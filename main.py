import tkinter as tk

TARGET_RATIO = 16 / 9
GRID_SIZE = 64
NODE_START = 16
NODE_END = 48
FILL_COLOR = "#5b8fb9"

ZOOM_LEVELS = {
    "1x": (16, 48),
    "0.75x": (8, 56),
    "0.5x": (0, 64),
}

grids = {}
current_zoom = "0.75x"


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

    grid = grids.get(canvas, set())
    for col, row in grid:
        if view_start <= col < view_end and view_start <= row < view_end:
            x1 = offset_x + (col - view_start) * cell
            y1 = offset_y + (row - view_start) * cell
            canvas.create_rectangle(x1, y1, x1 + cell, y1 + cell, fill=FILL_COLOR, outline="")

    for i in range(view_start, view_end + 1):
        x = offset_x + (i - view_start) * cell
        y = offset_y + (i - view_start) * cell
        color = "#444444" if i % 8 == 0 else "#3a3a3a"
        canvas.create_line(x, offset_y, x, offset_y + size, fill=color)
        canvas.create_line(offset_x, y, offset_x + size, y, fill=color)


drag_mode = {}


def on_click(event, mode="fill"):
    canvas = event.widget
    col, row = pixel_to_cell(canvas, event.x, event.y)
    if col is None:
        return
    grid = grids.setdefault(canvas, set())
    if mode == "fill":
        grid.add((col, row))
    else:
        grid.discard((col, row))
    draw_grid(canvas)


def on_drag(event, mode="fill"):
    canvas = event.widget
    col, row = pixel_to_cell(canvas, event.x, event.y)
    if col is None:
        return
    grid = grids.setdefault(canvas, set())
    if mode == "fill":
        if (col, row) not in grid:
            grid.add((col, row))
            draw_grid(canvas)
    else:
        if (col, row) in grid:
            grid.discard((col, row))
            draw_grid(canvas)


def main():
    global current_zoom

    root = tk.Tk()
    root.title("Luanti Node Box Editor")
    root.geometry("1280x720")
    root.configure(bg="#000000")

    content = tk.Frame(root, bg="#000000")
    content.place(relx=0.5, rely=0.5, anchor="center")

    content.columnconfigure(0, weight=2, uniform="col")
    content.columnconfigure(1, weight=2, uniform="col")
    content.columnconfigure(2, weight=1, uniform="col")
    content.rowconfigure(0, weight=1, uniform="row")
    content.rowconfigure(1, weight=1, uniform="row")

    top_view = tk.Canvas(content, bg="#2a2a2a", highlightthickness=0)
    top_view.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

    front_view = tk.Canvas(content, bg="#2a2a2a", highlightthickness=0)
    front_view.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

    side_view = tk.Canvas(content, bg="#2a2a2a", highlightthickness=0)
    side_view.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)

    preview_3d = tk.Canvas(content, bg="#1a1a1a", highlightthickness=0)
    preview_3d.grid(row=1, column=1, sticky="nsew", padx=1, pady=1)

    right_panel = tk.Frame(content, bg="#333333")
    right_panel.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=1, pady=1)

    grid_views = [top_view, front_view, side_view]

    zoom_label = tk.Label(right_panel, text="Zoom", bg="#333333", fg="#cccccc")
    zoom_label.pack(pady=(10, 5))

    zoom_frame = tk.Frame(right_panel, bg="#333333")
    zoom_frame.pack(pady=5)

    def set_zoom(level):
        global current_zoom
        current_zoom = level
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

    root.mainloop()


if __name__ == "__main__":
    main()
