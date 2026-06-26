import tkinter as tk


def show_help(root, settings, save_settings, on_3d_options=None, show_3d_options_current=False, on_show_intro=None):
    win = tk.Toplevel(root)
    win.title("Help / About")
    w, h = 780, 700
    sx = root.winfo_x() + (root.winfo_width() - w) // 2
    sy = root.winfo_y() + (root.winfo_height() - h) // 2
    win.geometry(f"{w}x{h}+{sx}+{sy}")
    win.configure(bg="#2a2a2a")
    win.transient(root)
    win.grab_set()
    win.resizable(False, False)

    tk.Label(win, text="Luanti VHR Nodebox & Texture Editor", bg="#2a2a2a", fg="#cccccc",
             font=("TkDefaultFont", 13, "bold")).pack(pady=(18, 3))
    tk.Label(win, text="Visual Hull Reconstruction Nodebox & Texture Editor",
             bg="#2a2a2a", fg="#888888", font=("TkDefaultFont", 9)).pack()
    tk.Label(win, text="Version 0.6.0   -   © 2026 Zenon Seth - LGPL 2.1",
             bg="#2a2a2a", fg="#ccff00", font=("TkDefaultFont", 11)).pack(pady=(4, 14))

    def section(title, lines, title_color="#88bbff"):
        # Each entry in lines is either a plain string or a list of segments.
        # A segment is either a plain string or a (text, tag) tuple.
        # Tags: "kw" = bold green (tool/feature names), "mode" = bold teal (mode names)
        f = tk.Frame(win, bg="#2a2a2a")
        f.pack(fill=tk.X, padx=24, pady=(0, 10))
        tk.Label(f, text=title, bg="#2a2a2a", fg=title_color,
                 font=("TkDefaultFont", 12, "bold"), anchor="w").pack(fill=tk.X)
        t = tk.Text(f, bg="#2a2a2a", fg="#cccccc", font=("TkDefaultFont", 11),
                    relief=tk.FLAT, highlightthickness=0, bd=0,
                    wrap=tk.NONE, padx=8, pady=0, cursor="arrow",
                    height=len(lines))
        t.tag_configure("kw", font=("TkDefaultFont", 11, "bold"), foreground="#aaffaa")
        t.tag_configure("mode", font=("TkDefaultFont", 11, "bold"), foreground="#66ddbb")
        for i, line in enumerate(lines):
            if i > 0:
                t.insert(tk.END, "\n")
            if isinstance(line, str):
                t.insert(tk.END, line)
            else:
                for seg in line:
                    if isinstance(seg, tuple):
                        t.insert(tk.END, seg[0], seg[1])
                    else:
                        t.insert(tk.END, seg)
        t.configure(state=tk.DISABLED)
        t.pack(fill=tk.X)

    section("How it works", [
        [("Visual Hull Reconstruction", "kw"), " converts your 2D drawings (Top, Front, Left) into nodebox cuboids automatically."],
    ])

    section("● Primary views  (geometry + texture)", [
        [("Top", "kw"), ", ", ("Front", "kw"), " and ", ("Left", "kw"), " are the primary sides - only these three define the nodebox geometry."],
        "They are marked ● in blue when active.",
    ])

    section("Opposite sides  (texture only)", [
        ["Each view can be toggled to its opposite - ", ("Bottom", "kw"), ", ", ("Back", "kw"), ", or ", ("Right", "kw"), ". These are texture-only;"],
        "they let you paint a different texture for that face without affecting the shape.",
    ])

    section("Layers", [
        "Each layer has a visibility toggle. Only visible layers appear in the preview and export.",
        "Where layers overlap, the topmost visible layer's color takes priority.",
    ])

    section("Drawing tools", [
        [("Pencil", "kw"), " (Y): single-pixel drawing.   ", ("Fill", "kw"), " (F): flood-fills connected pixels of the same color."],
        [("Symmetry", "kw"), ": mirrors every stroke - ", ("Left/Right", "mode"), ", ", ("Top/Bottom", "mode"), ", or ", ("Radial", "mode"), " (both axes). Toggle with S."],
        [("Noise", "kw"), ": applies a random lightness jitter per pixel while drawing, for a natural grain effect."],
        "Enable via checkbox next to Symmetry; use the slider to set intensity.",
    ])

    section("Controls", [
        [("LMB", "kw"), " / drag: Draw  |  ", ("RMB", "kw"), " / drag: Erase  |  ", ("Alt+LMB", "kw"), ": Pick color"],
        [("Ctrl+Z", "kw"), ": Undo  |  ", ("Ctrl+Y", "kw"), ": Redo  |  ", ("Y", "kw"), ": Pencil  |  ", ("F", "kw"), ": Fill  |  ", ("S", "kw"), ": Cycle symmetry"],
    ])

    use_system_var = tk.BooleanVar(value=settings.get("use_system_colorpicker", False))

    def on_toggle_colorpicker():
        settings["use_system_colorpicker"] = use_system_var.get()
        save_settings(settings)

    cb_style = dict(bg="#2a2a2a", fg="#cccccc", selectcolor="#1a1a1a",
                    activebackground="#2a2a2a", activeforeground="#cccccc",
                    font=("TkDefaultFont", 11))

    tk.Checkbutton(win, text="Use system color picker",
                   variable=use_system_var, command=on_toggle_colorpicker,
                   **cb_style).pack(pady=(8, 0))

    if on_3d_options is not None:
        show_3d_var = tk.BooleanVar(value=show_3d_options_current)
        def on_toggle_3d_options():
            on_3d_options(show_3d_var.get())
        tk.Checkbutton(win, text="Show 3D View options",
                       variable=show_3d_var, command=on_toggle_3d_options,
                       **cb_style).pack(pady=(4, 0))

    tk.Button(win, text="Show intro again", width=14,
              command=lambda: [win.destroy(), on_show_intro()],
              bg="#2a2a2a", fg="#cccccc", relief="flat"
              ).pack(pady=(12, 0))

    tk.Button(win, text="Close", width=10, command=win.destroy).pack(pady=(8, 16))
