import tkinter as tk
from tutorial_images import (
    intro_1_1, intro_1_2,
    intro_2_1, intro_2_2, intro_2_3,
    intro_3_1,
)

PAGES = [
    [intro_1_1, intro_1_2],
    [intro_2_1, intro_2_2, intro_2_3],
    [intro_3_1],
]

CYCLE_MS = [4000, 2000, 2000]


def show_tutorial(root, settings, save_settings):
    if settings.get("hide_tutorial", False):
        return
    _open_dialog(root, settings, save_settings)


def open_tutorial(root, settings, save_settings):
    _open_dialog(root, settings, save_settings)


def _open_dialog(root, settings, save_settings):
    win = tk.Toplevel(root)
    win.title("Welcome")
    win.configure(bg="#1a1a1a")
    win.resizable(False, False)
    win.transient(root)
    win.grab_set()

    page_images = []
    for page_data in PAGES:
        page_images.append([tk.PhotoImage(data=d) for d in page_data])

    img_w = page_images[0][0].width()
    img_h = page_images[0][0].height()

    w = img_w
    h = img_h + 48
    win.update_idletasks()
    sx = root.winfo_x() + (root.winfo_width() - w) // 2
    sy = root.winfo_y() + (root.winfo_height() - h) // 2
    win.geometry(f"{w}x{h}+{sx}+{sy}")

    canvas = tk.Canvas(win, width=img_w, height=img_h, bg="#1a1a1a", highlightthickness=0)
    canvas.pack()
    img_item = canvas.create_image(0, 0, anchor="nw")

    state = {"page": 0, "frame": 0, "after_id": None}

    def cancel_cycle():
        if state["after_id"] is not None:
            win.after_cancel(state["after_id"])
            state["after_id"] = None

    def start_cycle():
        cancel_cycle()
        page = state["page"]
        frames = page_images[page]
        canvas.itemconfig(img_item, image=frames[state["frame"]])
        if len(frames) <= 1:
            return
        def cycle():
            if not win.winfo_exists():
                return
            state["frame"] = (state["frame"] + 1) % len(page_images[state["page"]])
            canvas.itemconfig(img_item, image=page_images[state["page"]][state["frame"]])
            state["after_id"] = win.after(CYCLE_MS[state["page"]], cycle)
        state["after_id"] = win.after(CYCLE_MS[state["page"]], cycle)

    def go_to_page(p):
        cancel_cycle()
        state["page"] = p
        state["frame"] = 0
        start_cycle()
        prev_btn.config(state="normal" if p > 0 else "disabled")
        next_btn.config(state="normal" if p < len(PAGES) - 1 else "disabled")
        page_label.config(text=f"{p + 1} / {len(PAGES)}")

    btn_style = dict(bg="#2a2a2a", fg="#cccccc", relief="flat",
                     activebackground="#3a3a3a", activeforeground="#ffffff",
                     padx=10, pady=3, cursor="hand2")

    ctrl = tk.Frame(win, bg="#1a1a1a")
    ctrl.pack(fill=tk.X, padx=8, pady=(6, 8))

    prev_btn = tk.Button(ctrl, text="◀ Prev", command=lambda: go_to_page(state["page"] - 1), **btn_style)
    prev_btn.pack(side=tk.LEFT)

    page_label = tk.Label(ctrl, text="", bg="#1a1a1a", fg="#666666", font=("TkDefaultFont", 9))
    page_label.pack(side=tk.LEFT, padx=8)

    next_btn = tk.Button(ctrl, text="Next ▶", command=lambda: go_to_page(state["page"] + 1), **btn_style)
    next_btn.pack(side=tk.LEFT)

    close_btn = tk.Button(ctrl, text="Close", command=win.destroy, **btn_style)
    close_btn.pack(side=tk.RIGHT)

    hide_var = tk.BooleanVar(value=settings.get("hide_tutorial", False))
    def on_hide_toggle():
        settings["hide_tutorial"] = hide_var.get()
        save_settings(settings)

    tk.Checkbutton(ctrl, text="Don't show again", variable=hide_var, command=on_hide_toggle,
                   bg="#1a1a1a", fg="#888888", selectcolor="#0a0a0a",
                   activebackground="#1a1a1a", activeforeground="#aaaaaa",
                   font=("TkDefaultFont", 9)).pack(side=tk.RIGHT, padx=(0, 12))

    win.protocol("WM_DELETE_WINDOW", lambda: [cancel_cycle(), win.destroy()])

    go_to_page(0)
