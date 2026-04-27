import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from services.dlss_backup_service import delete_dlss_backups, restore_dlss_backups
from services.dlss_update_service import update_dlss_files
from ui.styles import BG_MAIN, BG_SURFACE, FG_PRIMARY, FONT_MONO
from utils.path_validation import is_invalid_directory


class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master, bg=BG_MAIN)
        self.pack(fill="both", expand=True, padx=10, pady=10)

        self.folder_path = tk.StringVar()
        self.found_dlss_files = {}
        self.log_queue = queue.Queue()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        top_frame = tk.Frame(self, bg=BG_MAIN)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=0)
        top_frame.grid_columnconfigure(2, weight=0)
        top_frame.grid_rowconfigure(0, weight=1)

        self.entry = ttk.Entry(
            top_frame,
            textvariable=self.folder_path,
            state="readonly",
            style="Dark.TEntry",
        )
        self.entry.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        self.button = ttk.Button(
            top_frame,
            text="Select Game Folder",
            command=self.browse_folder,
            style="Dark.TButton",
        )
        self.button.grid(row=0, column=1, padx=(0, 8), sticky="nsew")

        self.backups_button = ttk.Menubutton(
            top_frame,
            text="Backups   ▾",
            style="Toolbar.TMenubutton",
        )
        self.backups_button.grid(row=0, column=2, sticky="ns")
        self.backups_button.state(["disabled"])

        self.backups_menu = tk.Menu(self.backups_button, tearoff=False)
        self.backups_menu.add_command(
            label="Restore DLSS Backups",
            command=self.start_restore_backups,
        )
        self.backups_menu.add_command(
            label="Delete DLSS Backups",
            command=self.start_delete_backups,
        )
        self.backups_button["menu"] = self.backups_menu

        self.update_button = ttk.Button(
            self,
            text="Update DLSS Files",
            command=self.start_update_dlss,
            style="Success.TButton",
        )
        self.update_button.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 10),
        )
        self.update_button.state(["disabled"])

        self.log_text = tk.Text(
            self,
            bg=BG_SURFACE,
            fg=FG_PRIMARY,
            insertbackground=FG_PRIMARY,
            wrap="word",
            relief="flat",
            font=FONT_MONO,
            state="disabled",
            cursor="arrow",
        )
        self.log_text.grid(row=2, column=0, columnspan=2, sticky="nsew")

        self.log_text.tag_config("success", foreground="#4caf50")
        self.log_text.tag_config("error", foreground="#f44336")

        self.after(100, self.process_log_queue)

    def set_busy(self, busy: bool):
        if busy:
            self.button.state(["disabled"])
            self.backups_button.state(["disabled"])
            self.update_button.state(["disabled"])
        else:
            self.button.state(["!disabled"])

            if self.folder_path.get():
                self.backups_button.state(["!disabled"])
                self.update_button.state(["!disabled"])
            else:
                self.backups_button.state(["disabled"])
                self.update_button.state(["disabled"])

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select your game installation folder")

        if folder:
            if is_invalid_directory(folder):
                self.log("Invalid directory selected", "error")
                self.folder_path.set("")
                self.backups_button.state(["disabled"])
                self.update_button.state(["disabled"])
                return

            self.folder_path.set(folder)
            self.found_dlss_files = {}
            self.backups_button.state(["!disabled"])
            self.update_button.state(["!disabled"])

    def start_update_dlss(self):
        self.start_worker(self.update_dlss_worker)

    def start_restore_backups(self):
        self.start_worker(self.restore_backups_worker)

    def start_delete_backups(self):
        confirm = messagebox.askyesno(
            "Delete Backups",
            "Are you sure you want to delete all DLSS backups?",
        )

        if not confirm:
            return

        self.start_worker(self.delete_backups_worker)

    def start_worker(self, worker_target):
        folder = self.folder_path.get()

        if not folder:
            self.log("No folder selected", "error")
            return

        self.set_busy(True)

        worker = threading.Thread(
            target=worker_target,
            args=(folder,),
            daemon=True,
        )
        worker.start()

    def restore_backups_worker(self, folder: str):
        try:
            result = restore_dlss_backups(folder)
            self.queue_service_events(result.events)
        except Exception as e:
            self.queue_log(f"Unexpected error: {e}", "error")
        finally:
            self.after(0, lambda: self.set_busy(False))

    def delete_backups_worker(self, folder: str):
        try:
            result = delete_dlss_backups(folder)
            self.queue_service_events(result.events)
        except Exception as e:
            self.queue_log(f"Unexpected error: {e}", "error")
        finally:
            self.after(0, lambda: self.set_busy(False))

    def update_dlss_worker(self, folder: str):
        try:
            result = update_dlss_files(folder)
            self.queue_service_events(result.events)
            self.after(
                0,
                lambda: setattr(
                    self,
                    "found_dlss_files",
                    result.found_dlss_files,
                ),
            )
        except Exception as e:
            self.queue_log(f"Unexpected error: {e}", "error")
        finally:
            self.after(0, lambda: self.set_busy(False))

    def queue_service_events(self, events):
        for event in events:
            self.queue_log(event.message, event.tag)

    def queue_log(self, message: str, tag=None):
        self.log_queue.put((message, tag))

    def process_log_queue(self):
        while not self.log_queue.empty():
            message, tag = self.log_queue.get()
            self.log(message, tag)

        self.after(100, self.process_log_queue)

    def log(self, message, tag=None):
        self.log_text.configure(state="normal")

        if tag:
            self.log_text.insert("end", message + "\n", tag)
        else:
            self.log_text.insert("end", message + "\n")

        self.log_text.see("end")
        self.log_text.configure(state="disabled")
