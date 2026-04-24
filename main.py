import os
import sys
import tkinter as tk

from ui.app import App
from ui.styles import configure_styles, BG_MAIN
from utils.window import centre_window

# --- App version ---
APP_VERSION = "1.3.0"


def resource_path(relative_path: str) -> str:
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def main():
    root = tk.Tk()
    root.title(f"DLSS Updater v{APP_VERSION}")
    root.resizable(False, False)
    root.configure(bg=BG_MAIN)

    try:
        root.iconbitmap(resource_path("icon.ico"))
    except Exception:
        pass

    centre_window(root, 500, 400)
    configure_styles()

    app = App(master=root)
    app.mainloop()


if __name__ == "__main__":
    main()
