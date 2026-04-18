from tkinter import ttk

# --- Theme constants ---
BG_MAIN = "#121212"
BG_SURFACE = "#1e1e1e"
BG_BUTTON = "#2d2d2d"
BG_BUTTON_ACTIVE = "#3a3a3a"
BG_BUTTON_PRESSED = "#1f1f1f"

FG_PRIMARY = "white"

FONT_UI = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 10)


def configure_styles():
    style = ttk.Style()

    style.theme_use("clam")

    # --- Entry ---
    style.configure(
        "Dark.TEntry",
        fieldbackground=BG_SURFACE,
        foreground=FG_PRIMARY,
        padding=6,
        font=FONT_UI,
    )

    style.map(
        "Dark.TEntry",
        fieldbackground=[("readonly", BG_SURFACE)],
        foreground=[("readonly", FG_PRIMARY)],
    )

    # --- Default button ---
    style.configure(
        "Dark.TButton",
        background=BG_BUTTON,
        foreground=FG_PRIMARY,
        padding=6,
        font=FONT_UI,
    )

    style.map(
        "Dark.TButton",
        background=[("active", BG_BUTTON_ACTIVE), ("pressed", BG_BUTTON_PRESSED)],
    )

    # --- NVIDIA themed primary button ---
    style.configure(
        "Success.TButton",
        background="#76B900",
        foreground="white",
        padding=6,
        font=FONT_UI,
    )

    style.map(
        "Success.TButton",
        background=[
            ("active", "#8fdc00"),
            ("pressed", "#5c8f00"),
            ("disabled", "#3a3a3a"),
        ],
        foreground=[("disabled", "#cccccc")],
    )
