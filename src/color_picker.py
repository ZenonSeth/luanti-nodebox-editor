import tkinter as tk
import colorsys


def _hex_to_hsv(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    hue, sat, val = colorsys.rgb_to_hsv(r, g, b)
    return int(hue * 360), int(sat * 100), int(val * 100)


def _hsv_to_hex(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h / 360, s / 100, v / 100)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def ask_color(parent, initial_color="#ffffff", title="Pick Color"):
    result = [None]

    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg="#2a2a2a")
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    w, h = 320, 280
    sx = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
    sy = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    win.geometry(f"{w}x{h}+{sx}+{sy}")

    try:
        hue, sat, val = _hex_to_hsv(initial_color)
    except Exception:
        hue, sat, val = 0, 0, 100

    h_var = tk.IntVar(value=hue)
    s_var = tk.IntVar(value=sat)
    v_var = tk.IntVar(value=val)
    hex_var = tk.StringVar(value=initial_color)

    updating = [False]

    def on_slider_change(*_):
        if updating[0]:
            return
        updating[0] = True
        color = _hsv_to_hex(h_var.get(), s_var.get(), v_var.get())
        hex_var.set(color)
        preview.configure(bg=color)
        updating[0] = False

    def on_hex_change(*_):
        if updating[0]:
            return
        raw = hex_var.get().strip()
        if not raw.startswith("#"):
            raw = "#" + raw
        if len(raw) == 7:
            try:
                int(raw[1:], 16)
            except ValueError:
                return
            updating[0] = True
            h2, s2, v2 = _hex_to_hsv(raw)
            h_var.set(h2)
            s_var.set(s2)
            v_var.set(v2)
            preview.configure(bg=raw)
            updating[0] = False

    # Preview swatch
    preview_frame = tk.Frame(win, bg="#2a2a2a")
    preview_frame.pack(pady=(16, 8))
    preview = tk.Label(preview_frame, width=12, height=2, bg=initial_color,
                       relief=tk.FLAT, bd=2)
    preview.pack()

    # Sliders
    slider_frame = tk.Frame(win, bg="#2a2a2a")
    slider_frame.pack(fill=tk.X, padx=20)

    SLIDER_OPTS = dict(orient=tk.HORIZONTAL, length=240, bg="#2a2a2a",
                       fg="#cccccc", troughcolor="#1a1a1a", highlightthickness=0,
                       activebackground="#88bbff", bd=0)

    for label, var, from_, to in (
        ("H", h_var, 0, 360),
        ("S", s_var, 0, 100),
        ("V", v_var, 0, 100),
    ):
        row = tk.Frame(slider_frame, bg="#2a2a2a")
        row.pack(fill=tk.X, pady=3)
        tk.Label(row, text=label, bg="#2a2a2a", fg="#888888",
                 font=("TkDefaultFont", 9), width=2, anchor="e").pack(side=tk.LEFT)
        sl = tk.Scale(row, variable=var, from_=from_, to=to,
                      command=on_slider_change, **SLIDER_OPTS)
        sl.pack(side=tk.LEFT, padx=(6, 0))

    # Hex input
    hex_frame = tk.Frame(win, bg="#2a2a2a")
    hex_frame.pack(pady=(10, 0))
    tk.Label(hex_frame, text="Hex", bg="#2a2a2a", fg="#888888",
             font=("TkDefaultFont", 9)).pack(side=tk.LEFT, padx=(0, 6))
    hex_entry = tk.Entry(hex_frame, textvariable=hex_var, width=9,
                         bg="#1a1a1a", fg="#cccccc", insertbackground="#cccccc",
                         relief=tk.FLAT, font=("Consolas", 10))
    hex_entry.pack(side=tk.LEFT)
    hex_var.trace_add("write", on_hex_change)

    # Buttons
    btn_frame = tk.Frame(win, bg="#2a2a2a")
    btn_frame.pack(pady=(12, 0))

    def do_ok():
        raw = hex_var.get().strip()
        if not raw.startswith("#"):
            raw = "#" + raw
        result[0] = raw
        win.destroy()

    tk.Button(btn_frame, text="OK", width=8, command=do_ok).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Cancel", width=8, command=win.destroy).pack(side=tk.LEFT, padx=5)

    win.bind("<Return>", lambda e: do_ok())
    win.bind("<Escape>", lambda e: win.destroy())

    win.wait_window()
    return result[0]
