import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from nbx_format import save_nbx, load_nbx
from voxels import grids_to_faces, layers_to_faces, grids_to_lua_layers, grids_to_colored_faces, layers_to_colored_faces
from preview3d import render_preview

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

DEFAULT_SETTINGS = {
    "zoom": "0.75x",
}


def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            saved = json.load(f)
        return {**DEFAULT_SETTINGS, **saved}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

TARGET_RATIO = 16 / 9
GRID_SIZE = 64
NODE_START = 16
NODE_END = 48
PALETTE_STEPS = 8
PALETTE_CELL_SIZE = 3

BASE_COLORS = [
    (255, 0, 0),
    (255, 140, 0),
    (255, 220, 0),
    (0, 180, 0),
    (0, 200, 200),
    (0, 100, 255),
    (160, 0, 255),
]
GRAY_BASE = (160, 160, 160)


def lerp(a, b, t):
    return int(a + (b - a) * t)


def rgb_to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_palette_rows(base, steps=PALETTE_STEPS):
    r, g, b = base
    tints = []
    for i in range(steps):
        t = i / (steps - 1) * 0.9
        tints.append(rgb_to_hex(lerp(r, 255, t), lerp(g, 255, t), lerp(b, 255, t)))
    shades = []
    for i in range(steps):
        t = i / (steps - 1) * 0.85
        shades.append(rgb_to_hex(lerp(r, 30, t), lerp(g, 30, t), lerp(b, 30, t)))
    return tints, shades


def build_palette():
    rows = []
    for base in BASE_COLORS:
        tints, shades = generate_palette_rows(base)
        rows.append(tints)
        rows.append(shades)
    grays = []
    for i in range(PALETTE_STEPS):
        v = lerp(255, 20, i / (PALETTE_STEPS - 1))
        grays.append(rgb_to_hex(v, v, v))
    rows.append(grays)
    return rows


selected_color = "#0064ff"
color_indicator = None

ZOOM_LEVELS = {
    "1x": (16, 48),
    "0.75x": (8, 56),
    "0.5x": (0, 64),
}

grids = {"top": {}, "front": {}, "side": {}}
canvas_to_name = {}
dirty = False
last_saved_state = None
settings = load_settings()
current_zoom = settings.get("zoom", "0.75x")


def get_grid_params(canvas):
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    size = min(w, h)
    view_start, view_end = ZOOM_LEVELS[current_zoom]
    view_cells = view_end - view_start
    cell = size / view_cells
    offset_x = (w - size) // 2
    offset_y = (h - size) // 2
    return offset_x, offset_y, size, cell, view_start, view_end


def pixel_to_cell(canvas, px, py):
    offset_x, offset_y, size, cell, view_start, view_end = get_grid_params(canvas)
    if cell <= 0:
        return None, None
    col = int((px - offset_x) / cell) + view_start
    row = int((py - offset_y) / cell) + view_start
    if view_start <= col < view_end and view_start <= row < view_end:
        return col, row
    return None, None


def draw_grid(canvas):
    canvas.delete("all")
    offset_x, offset_y, size, cell, view_start, view_end = get_grid_params(canvas)

    canvas.create_rectangle(
        offset_x, offset_y, offset_x + size, offset_y + size,
        fill="#2a2a2a", outline=""
    )

    node_x1 = offset_x + max(0, NODE_START - view_start) * cell
    node_y1 = offset_y + max(0, NODE_START - view_start) * cell
    node_x2 = offset_x + min(view_end - view_start, NODE_END - view_start) * cell
    node_y2 = offset_y + min(view_end - view_start, NODE_END - view_start) * cell
    canvas.create_rectangle(node_x1, node_y1, node_x2, node_y2, fill="#323232", outline="")

    grid = grids[canvas_to_name[canvas]]
    for (col, row), color in grid.items():
        if view_start <= col < view_end and view_start <= row < view_end:
            x1 = offset_x + (col - view_start) * cell
            y1 = offset_y + (row - view_start) * cell
            canvas.create_rectangle(x1, y1, x1 + cell, y1 + cell, fill=color, outline="")

    for i in range(view_start, view_end + 1):
        x = offset_x + (i - view_start) * cell
        y = offset_y + (i - view_start) * cell
        color = "#444444" if i % 8 == 0 else "#3a3a3a"
        canvas.create_line(x, offset_y, x, offset_y + size, fill=color)
        canvas.create_line(offset_x, y, offset_x + size, y, fill=color)

    VIEW_LABELS = {
        "top":   ("-X", "+X", "-Z", "+Z"),
        "front": ("-X", "+X", "+Y", "-Y"),
        "side":  ("-Z", "+Z", "+Y", "-Y"),
    }
    name = canvas_to_name.get(canvas)
    if name and name in VIEW_LABELS:
        lbl_left, lbl_right, lbl_top, lbl_bottom = VIEW_LABELS[name]
        mid = offset_x + size / 2
        midy = offset_y + size / 2
        margin = 4
        canvas.create_text(offset_x + margin, midy, text=lbl_left,
                           fill="#999999", font=("TkDefaultFont", 9), anchor="w")
        canvas.create_text(offset_x + size - margin, midy, text=lbl_right,
                           fill="#999999", font=("TkDefaultFont", 9), anchor="e")
        canvas.create_text(mid, offset_y + margin + 14, text=lbl_top,
                           fill="#999999", font=("TkDefaultFont", 9), anchor="n")
        canvas.create_text(mid, offset_y + size - margin, text=lbl_bottom,
                           fill="#999999", font=("TkDefaultFont", 9), anchor="s")


preview_canvas = None
preview_azimuth = 35
preview_elevation = 25
cached_faces = []
_layers = None
_active_layer_idx = 0


def _visible_layers():
    if not _layers:
        return []
    return [l for l in _layers if l.get("visible", True)]


def rebuild_faces():
    global cached_faces
    vis = _visible_layers()
    if vis:
        cached_faces = layers_to_colored_faces(vis)
    else:
        cached_faces = []
    redraw_preview()


def redraw_preview():
    if preview_canvas is None:
        return
    render_preview(preview_canvas, cached_faces, preview_azimuth, preview_elevation)


def update_preview():
    rebuild_faces()


def mark_dirty():
    global dirty
    dirty = True


def _resolve_fill_color(view_name, col, row):
    if _active_layer_idx != 0 and _layers:
        top_layer_grid = _layers[0][view_name]
        if (col, row) in top_layer_grid:
            return top_layer_grid[(col, row)]
    return selected_color


def on_pick_color(event):
    canvas = event.widget
    col, row = pixel_to_cell(canvas, event.x, event.y)
    if col is None:
        return
    view_name = canvas_to_name[canvas]
    grid = grids[view_name]
    color = grid.get((col, row))
    if color:
        global selected_color
        selected_color = color
        color_indicator.configure(bg=selected_color)


def on_click(event, mode="fill"):
    canvas = event.widget
    col, row = pixel_to_cell(canvas, event.x, event.y)
    if col is None:
        return
    view_name = canvas_to_name[canvas]
    grid = grids[view_name]
    if mode == "fill":
        grid[(col, row)] = _resolve_fill_color(view_name, col, row)
    else:
        grid.pop((col, row), None)
    mark_dirty()
    draw_grid(canvas)
    update_preview()


def on_drag(event, mode="fill"):
    canvas = event.widget
    col, row = pixel_to_cell(canvas, event.x, event.y)
    if col is None:
        return
    view_name = canvas_to_name[canvas]
    grid = grids[view_name]
    if mode == "fill":
        color = _resolve_fill_color(view_name, col, row)
        if (col, row) not in grid or grid[(col, row)] != color:
            grid[(col, row)] = color
            mark_dirty()
            draw_grid(canvas)
            update_preview()
    else:
        if (col, row) in grid:
            grid.pop((col, row))
            mark_dirty()
            draw_grid(canvas)
            update_preview()


def main():
    global current_zoom, selected_color

    root = tk.Tk()
    root.title("Luanti VHR Node Box Editor")
    geom = settings.get("geometry", "1280x720")
    root.geometry(geom)
    if settings.get("maximized", False):
        root.state("zoomed")
    root.configure(bg="#000000")

    content = tk.Frame(root, bg="#000000")
    content.place(relx=0.5, rely=0.5, anchor="center")

    content.columnconfigure(0, weight=2, uniform="col")
    content.columnconfigure(1, weight=2, uniform="col")
    content.columnconfigure(2, weight=1, uniform="col")
    content.rowconfigure(0, weight=1, uniform="row")
    content.rowconfigure(1, weight=1, uniform="row")

    top_frame = tk.Frame(content, bg="#2a2a2a")
    top_frame.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
    tk.Label(top_frame, text="Top", bg="#2a2a2a", fg="#999999",
             font=("TkDefaultFont", 11, "bold")).place(x=4, y=4, anchor="nw")
    top_view = tk.Canvas(top_frame, bg="#2a2a2a", highlightthickness=0)
    top_view.place(relx=0.5, rely=0.5, anchor="center")

    preview_3d = tk.Canvas(content, bg="#1a1a1a", highlightthickness=0)
    preview_3d.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

    front_frame = tk.Frame(content, bg="#2a2a2a")
    front_frame.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)
    tk.Label(front_frame, text="Front", bg="#2a2a2a", fg="#999999",
             font=("TkDefaultFont", 11, "bold")).place(x=4, y=4, anchor="nw")
    front_view = tk.Canvas(front_frame, bg="#2a2a2a", highlightthickness=0)
    front_view.place(relx=0.5, rely=0.5, anchor="center")

    side_frame = tk.Frame(content, bg="#2a2a2a")
    side_frame.grid(row=1, column=1, sticky="nsew", padx=1, pady=1)
    tk.Label(side_frame, text="Side", bg="#2a2a2a", fg="#999999",
             font=("TkDefaultFont", 11, "bold")).place(x=4, y=4, anchor="nw")
    side_view = tk.Canvas(side_frame, bg="#2a2a2a", highlightthickness=0)
    side_view.place(relx=0.5, rely=0.5, anchor="center")

    def on_view_frame_resize(event):
        frame = event.widget
        size = min(event.width, event.height)
        for child in frame.winfo_children():
            if isinstance(child, tk.Canvas):
                child.place_configure(width=size, height=size)

    top_frame.bind("<Configure>", on_view_frame_resize)
    front_frame.bind("<Configure>", on_view_frame_resize)
    side_frame.bind("<Configure>", on_view_frame_resize)

    global preview_canvas
    preview_canvas = preview_3d

    drag_start = [None, None]

    def on_preview_press(event):
        drag_start[0] = event.x
        drag_start[1] = event.y

    def on_preview_drag(event):
        global preview_azimuth, preview_elevation
        if drag_start[0] is None:
            return
        dx = event.x - drag_start[0]
        dy = event.y - drag_start[1]
        preview_azimuth -= dx * 0.5
        preview_elevation = max(-89, min(89, preview_elevation + dy * 0.5))
        drag_start[0] = event.x
        drag_start[1] = event.y
        redraw_preview()

    preview_3d.bind("<Button-1>", on_preview_press)
    preview_3d.bind("<B1-Motion>", on_preview_drag)
    preview_3d.bind("<Configure>", lambda e: redraw_preview())

    right_panel = tk.Frame(content, bg="#333333")
    right_panel.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=1, pady=1)

    canvas_to_name[top_view] = "top"
    canvas_to_name[front_view] = "front"
    canvas_to_name[side_view] = "side"

    grid_views = [top_view, front_view, side_view]

    # Zoom controls
    zoom_label = tk.Label(right_panel, text="Zoom", bg="#333333", fg="#cccccc")
    zoom_label.pack(pady=(10, 5))

    zoom_frame = tk.Frame(right_panel, bg="#333333")
    zoom_frame.pack(pady=5)

    def set_zoom(level):
        global current_zoom
        current_zoom = level
        settings["zoom"] = level
        save_settings(settings)
        for btn in zoom_buttons.values():
            btn.configure(relief=tk.RAISED)
        zoom_buttons[level].configure(relief=tk.SUNKEN)
        for view in grid_views:
            draw_grid(view)

    zoom_buttons = {}
    for level in ZOOM_LEVELS:
        btn = tk.Button(zoom_frame, text=level, width=5,
                        command=lambda l=level: set_zoom(l))
        btn.pack(side=tk.LEFT, padx=2)
        zoom_buttons[level] = btn

    zoom_buttons[current_zoom].configure(relief=tk.SUNKEN)

    # Palette
    palette_label = tk.Label(right_panel, text="Color", bg="#333333", fg="#cccccc")
    palette_label.pack(pady=(15, 5))

    global color_indicator
    color_indicator = tk.Canvas(right_panel, width=30, height=30,
                                bg=selected_color, highlightthickness=1,
                                highlightbackground="#666666")
    color_indicator.pack(pady=(0, 5))

    palette_area = tk.Frame(right_panel, bg="#333333")
    palette_area.pack(padx=5, fill=tk.X)

    palette_canvas = tk.Canvas(palette_area, bg="#333333", highlightthickness=0)
    palette_canvas.pack(side=tk.LEFT, fill=tk.Y)

    palette_rows = build_palette()

    def draw_palette(event=None):
        palette_canvas.delete("all")
        w = palette_area.winfo_width()
        if w <= 1:
            return
        cell_w = (w * 0.375) / PALETTE_STEPS
        cell_h = cell_w
        for row_idx, row in enumerate(palette_rows):
            for col_idx, color in enumerate(row):
                x1 = col_idx * cell_w
                y1 = row_idx * cell_h
                palette_canvas.create_rectangle(
                    x1, y1, x1 + cell_w, y1 + cell_h,
                    fill=color, outline="#222222"
                )
        total_width = PALETTE_STEPS * cell_w
        total_height = len(palette_rows) * cell_h
        palette_canvas.configure(width=int(total_width), height=int(total_height))

    def on_palette_click(event):
        global selected_color
        w = palette_area.winfo_width()
        if w <= 1:
            return
        cell_w = (w * 0.375) / PALETTE_STEPS
        cell_h = cell_w
        col = int(event.x / cell_w)
        row = int(event.y / cell_h)
        if 0 <= row < len(palette_rows) and 0 <= col < len(palette_rows[row]):
            selected_color = palette_rows[row][col]
            color_indicator.configure(bg=selected_color)

    palette_area.bind("<Configure>", draw_palette)
    palette_canvas.bind("<Button-1>", on_palette_click)

    # Custom color palette
    CUSTOM_SLOTS = 16
    saved_custom = settings.get("custom_colors", None)
    custom_colors = list(saved_custom) if saved_custom and len(saved_custom) == CUSTOM_SLOTS else ["#ffffff"] * CUSTOM_SLOTS
    custom_swatches = []

    custom_frame = tk.Frame(palette_area, bg="#333333")
    custom_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

    def pick_custom_color(idx):
        from tkinter import colorchooser
        result = colorchooser.askcolor(initialcolor=custom_colors[idx], title="Pick Color")
        if result[1]:
            custom_colors[idx] = result[1]
            custom_swatches[idx].configure(bg=custom_colors[idx])
            settings["custom_colors"] = list(custom_colors)
            save_settings(settings)

    def select_custom_color(idx):
        global selected_color
        selected_color = custom_colors[idx]
        color_indicator.configure(bg=selected_color)

    for i in range(CUSTOM_SLOTS):
        row_idx = i // 2
        col_idx = i % 2
        slot_frame = tk.Frame(custom_frame, bg="#333333")
        slot_frame.grid(row=row_idx, column=col_idx * 2, columnspan=2, sticky="w", padx=1, pady=1)

        swatch = tk.Button(slot_frame, bg=custom_colors[i], width=2, height=1,
                           relief=tk.RAISED, borderwidth=1,
                           command=lambda idx=i: select_custom_color(idx))
        swatch.pack(side=tk.LEFT)
        custom_swatches.append(swatch)

        pick_btn = tk.Button(slot_frame, text="●", width=1, font=("TkDefaultFont", 6),
                             command=lambda idx=i: pick_custom_color(idx))
        pick_btn.pack(side=tk.LEFT, padx=(1, 0))

    # Layers
    layers_label = tk.Label(right_panel, text="Layers", bg="#333333", fg="#cccccc")
    layers_label.pack(pady=(15, 5))

    layers_frame = tk.Frame(right_panel, bg="#333333")
    layers_frame.pack(padx=5, fill=tk.X)

    layer_list_frame = tk.Frame(layers_frame, bg="#1a1a1a", height=160,
                               relief=tk.SUNKEN, borderwidth=1)
    layer_list_frame.pack(fill=tk.X)
    layer_list_frame.pack_propagate(False)

    layer_inner = tk.Frame(layer_list_frame, bg="#1a1a1a")
    layer_inner.pack(fill=tk.BOTH, expand=True)

    layer_btn_frame = tk.Frame(layers_frame, bg="#333333")
    layer_btn_frame.pack(pady=(5, 0))

    global _layers, _active_layer_idx
    layers = [{"name": "Top Layer", "visible": True,
               "top": grids["top"], "front": grids["front"], "side": grids["side"]}]
    _layers = layers
    _active_layer_idx = 0
    layer_widgets = []

    def refresh_layer_list():
        for w in layer_widgets:
            w.destroy()
        layer_widgets.clear()
        for i, layer in enumerate(layers):
            row = tk.Frame(layer_inner, bg="#4a6a8a" if i == _active_layer_idx else "#1a1a1a")
            row.pack(fill=tk.X)
            layer_widgets.append(row)

            var = tk.BooleanVar(value=layer.get("visible", True))
            cb = tk.Checkbutton(row, variable=var, bg=row["bg"],
                                activebackground=row["bg"],
                                command=lambda idx=i, v=var: toggle_visibility(idx, v))
            cb.pack(side=tk.LEFT)

            lbl = tk.Label(row, text=layer["name"], bg=row["bg"], fg="#ffffff",
                           font=("TkDefaultFont", 9), anchor="w")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            lbl.bind("<Button-1>", lambda e, idx=i: select_layer(idx))

    def toggle_visibility(idx, var):
        layers[idx]["visible"] = var.get()
        mark_dirty()
        update_preview()

    def select_layer(idx):
        global _active_layer_idx
        if idx < 0 or idx >= len(layers):
            return
        _active_layer_idx = idx
        grids["top"] = layers[idx]["top"]
        grids["front"] = layers[idx]["front"]
        grids["side"] = layers[idx]["side"]
        refresh_layer_list()
        for view in grid_views:
            draw_grid(view)
        update_preview()

    def do_new_layer():
        idx = len(layers) + 1
        layers.append({"name": f"Layer {idx}", "visible": True, "top": {}, "front": {}, "side": {}})
        select_layer(len(layers) - 1)
        mark_dirty()

    def do_clone_layer():
        src = layers[_active_layer_idx]
        layers.append({
            "name": f"{src['name']} copy",
            "visible": True,
            "top": dict(src["top"]),
            "front": dict(src["front"]),
            "side": dict(src["side"]),
        })
        select_layer(len(layers) - 1)
        mark_dirty()

    def do_del_layer():
        if len(layers) <= 1:
            return
        if _active_layer_idx == 0:
            return
        del layers[_active_layer_idx]
        select_layer(min(_active_layer_idx, len(layers) - 1))
        mark_dirty()

    new_layer_btn = tk.Button(layer_btn_frame, text="New", width=5, command=do_new_layer)
    new_layer_btn.pack(side=tk.LEFT, padx=2)

    clone_layer_btn = tk.Button(layer_btn_frame, text="Clone", width=5, command=do_clone_layer)
    clone_layer_btn.pack(side=tk.LEFT, padx=2)

    del_layer_btn = tk.Button(layer_btn_frame, text="Del", width=5, command=do_del_layer)
    del_layer_btn.pack(side=tk.LEFT, padx=2)

    def do_rename_layer():
        from tkinter import simpledialog
        current_name = layers[_active_layer_idx]["name"]
        new_name = simpledialog.askstring("Rename Layer", "New name:", initialvalue=current_name, parent=root)
        if new_name and new_name.strip():
            layers[_active_layer_idx]["name"] = new_name.strip()
            refresh_layer_list()
            mark_dirty()

    rename_layer_btn = tk.Button(layer_btn_frame, text="Rename", width=5, command=do_rename_layer)
    rename_layer_btn.pack(side=tk.LEFT, padx=2)

    refresh_layer_list()

    # Save/Load buttons at bottom
    button_frame = tk.Frame(right_panel, bg="#333333")
    button_frame.pack(side=tk.BOTTOM, pady=10)

    def check_unsaved():
        if not dirty:
            return True
        return messagebox.askyesno(
            "Unsaved Changes",
            "You have unsaved changes. Continue without saving?"
        )

    def do_new():
        if not check_unsaved():
            return
        global dirty
        layers.clear()
        layers.append({"name": "Top Layer", "top": {}, "front": {}, "side": {}})
        select_layer(0)
        dirty = False

    def do_save():
        global dirty
        path = filedialog.asksaveasfilename(
            defaultextension=".nbx",
            filetypes=[("NodeBox files", "*.nbx")],
        )
        if path:
            json_str = save_nbx(layers)
            with open(path, "w") as f:
                f.write(json_str)
            dirty = False

    def do_load():
        if not check_unsaved():
            return
        global dirty
        path = filedialog.askopenfilename(
            filetypes=[("NodeBox files", "*.nbx")],
        )
        if path:
            with open(path, "r") as f:
                json_str = f.read()
            loaded = load_nbx(json_str)
            loaded[0]["name"] = "Top Layer"
            layers.clear()
            layers.extend(loaded)
            select_layer(0)
            dirty = False

    def do_export():
        lua_code, method, count = grids_to_lua_layers(_visible_layers())
        win = tk.Toplevel(root)
        win.title("Export Lua")
        win.geometry("500x340")
        win.configure(bg="#2a2a2a")
        win.transient(root)
        win.grab_set()

        btn_bar = tk.Frame(win, bg="#2a2a2a", height=40)
        btn_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 10))
        btn_bar.pack_propagate(False)

        if method:
            info = f"{count} cuboid{'s' if count != 1 else ''} (method: {method})"
            info_label = tk.Label(win, text=info, bg="#2a2a2a", fg="#888888",
                                  font=("TkDefaultFont", 9))
            info_label.pack(side=tk.BOTTOM, pady=(0, 2))

        text = tk.Text(win, bg="#1a1a1a", fg="#cccccc", insertbackground="#cccccc",
                       font=("Consolas", 10), wrap=tk.NONE, padx=8, pady=8)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
        text.insert("1.0", lua_code)
        text.configure(state=tk.DISABLED)

        def copy_to_clipboard():
            root.clipboard_clear()
            root.clipboard_append(lua_code)
            copy_btn.configure(text="Copied!")
            win.after(1500, lambda: copy_btn.configure(text="Copy"))

        copy_btn = tk.Button(btn_bar, text="Copy", width=10, command=copy_to_clipboard)
        copy_btn.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(btn_bar, text="Close", width=10, command=win.destroy)
        close_btn.pack(side=tk.LEFT, padx=5)

    new_btn = tk.Button(button_frame, text="New", width=8, command=do_new)
    new_btn.pack(side=tk.LEFT, padx=5)

    save_btn = tk.Button(button_frame, text="Save", width=8, command=do_save)
    save_btn.pack(side=tk.LEFT, padx=5)

    load_btn = tk.Button(button_frame, text="Load", width=8, command=do_load)
    load_btn.pack(side=tk.LEFT, padx=5)

    export_frame = tk.Frame(right_panel, bg="#333333")
    export_frame.pack(side=tk.BOTTOM, pady=(0, 10))

    def do_about():
        win = tk.Toplevel(root)
        win.title("Help / About")
        w, h = 400, 340
        sx = root.winfo_x() + (root.winfo_width() - w) // 2
        sy = root.winfo_y() + (root.winfo_height() - h) // 2
        win.geometry(f"{w}x{h}+{sx}+{sy}")
        win.configure(bg="#2a2a2a")
        win.transient(root)
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win, text="Luanti VHR Node Box Editor", bg="#2a2a2a", fg="#cccccc",
                 font=("TkDefaultFont", 12, "bold")).pack(pady=(15, 4))
        tk.Label(win, text="Version 0.5.0",
                 bg="#2a2a2a", fg="#999999", font=("TkDefaultFont", 9)).pack(pady=(0, 4))
        tk.Label(win, text="Visual Hull Reconstruction Node Box Editor",
                 bg="#2a2a2a", fg="#cccccc", font=("TkDefaultFont", 9)).pack(pady=(0, 4))
        tk.Label(win, text="by Zenon Seth", bg="#2a2a2a", fg="#ccff00",
                 font=("TkDefaultFont", 10)).pack(pady=(0, 10))

        help_text = (
            "Controls:\n"
            "  Left-click / drag    Draw with selected color\n"
            "  Right-click / drag   Erase\n"
            "  Alt + Left-click     Pick color from cell\n"
            "\n"
            "Layers:\n"
            "  Each layer has a visibility checkbox.\n"
            "  Only visible layers are shown in the preview\n"
            "  and included in export. The top layer's color\n"
            "  takes priority where layers overlap."
        )
        tk.Label(win, text=help_text, bg="#2a2a2a", fg="#cccccc",
                 font=("TkDefaultFont", 9), justify=tk.LEFT, anchor="w").pack(
                     padx=20, pady=(0, 10), fill=tk.X)

        tk.Button(win, text="Close", width=8, command=win.destroy).pack()

    export_btn = tk.Button(export_frame, text="Export", width=8, command=do_export)
    export_btn.pack(side=tk.LEFT, padx=5)

    about_btn = tk.Button(export_frame, text="Help/About", width=8, command=do_about)
    about_btn.pack(side=tk.LEFT, padx=5)

    def on_resize(event):
        if event.widget is not root:
            return
        w, h = event.width, event.height
        ratio = w / h if h > 0 else TARGET_RATIO
        if ratio > TARGET_RATIO:
            new_h = h
            new_w = int(h * TARGET_RATIO)
        else:
            new_w = w
            new_h = int(w / TARGET_RATIO)
        content.place_configure(width=new_w, height=new_h)

    def on_canvas_resize(event):
        draw_grid(event.widget)

    root.bind("<Configure>", on_resize)
    for view in grid_views:
        view.bind("<Configure>", on_canvas_resize)
        view.bind("<Button-1>", lambda e: on_click(e, "fill"))
        view.bind("<B1-Motion>", lambda e: on_drag(e, "fill"))
        view.bind("<Button-3>", lambda e: on_click(e, "erase"))
        view.bind("<B3-Motion>", lambda e: on_drag(e, "erase"))
        view.bind("<Alt-Button-1>", on_pick_color)

    def on_close():
        if dirty:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Quit without saving?"
            ):
                return
        maximized = root.state() == "zoomed"
        settings["maximized"] = maximized
        if not maximized:
            settings["geometry"] = root.geometry()
        save_settings(settings)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
