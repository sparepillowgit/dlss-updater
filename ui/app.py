import queue
import threading
import tkinter as tk
from collections import Counter
from tkinter import filedialog, ttk

from ui.styles import BG_MAIN, BG_SURFACE, FG_PRIMARY, FONT_MONO
from utils.dlss_finder import DLSS_DLL, DLSSG_DLL, find_dlss_files
from utils.dlss_manifest import fetch_manifest, get_manifest_entry
from utils.dlss_updater import download_dlss_files, replace_dlss_files
from utils.file_version import get_file_version
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
            text="Choose Game Folder",
            command=self.browse_folder,
            style="Dark.TButton",
        )
        self.button.grid(row=0, column=1, sticky="nsew")

        self.update_button = ttk.Button(
            self,
            text="Update DLSS Files",
            command=self.start_update_dlss,
            style="Success.TButton",
        )
        self.update_button.grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10)
        )
        self.update_button.state(["disabled"])

        # --- Read-only log ---
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
            self.update_button.state(["disabled"])
        else:
            self.button.state(["!disabled"])
            if self.folder_path.get():
                self.update_button.state(["!disabled"])

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select your game installation folder")
        if folder:
            if is_invalid_directory(folder):
                self.log("Invalid directory selected", "error")
                self.folder_path.set("")
                self.update_button.state(["disabled"])
                return

            self.folder_path.set(folder)
            self.found_dlss_files = {}
            self.update_button.state(["!disabled"])

    def start_update_dlss(self):
        folder = self.folder_path.get()

        if not folder:
            self.log("No folder selected", "error")
            return

        self.set_busy(True)

        worker = threading.Thread(
            target=self.update_dlss_worker, args=(folder,), daemon=True
        )
        worker.start()

    def update_dlss_worker(self, folder: str):
        try:
            self.queue_log("Searching for DLSS files...")

            found_files = find_dlss_files(folder)
            found_dlss_files = {
                name: paths for name, paths in found_files.items() if paths
            }

            dlss_count = len(found_files[DLSS_DLL])
            dlssg_count = len(found_files[DLSSG_DLL])

            if dlss_count > 0:
                self.queue_log(f"Found {dlss_count} instance(s) of {DLSS_DLL}")
            else:
                self.queue_log(f"Did not find {DLSS_DLL}")

            if dlssg_count > 0:
                self.queue_log(f"Found {dlssg_count} instance(s) of {DLSSG_DLL}")
            else:
                self.queue_log(f"Did not find {DLSSG_DLL}")

            if not found_dlss_files:
                self.queue_log("No DLSS files were found", "error")
                return

            self.queue_log("Checking installed versions...")

            manifest = fetch_manifest()

            download_targets = {}
            files_to_replace = {}
            version_details = {}

            for dll_name, file_paths in found_dlss_files.items():
                entry = get_manifest_entry(manifest, dll_name)

                if not entry:
                    self.queue_log(f"No manifest entry found for {dll_name}", "error")
                    continue

                latest_version = entry.get("version", "unknown")
                download_url = entry.get("url")

                if not download_url:
                    self.queue_log(
                        f"No download URL found in manifest for {dll_name}", "error"
                    )
                    continue

                local_versions = [
                    get_file_version(str(file_path)) or "unknown"
                    for file_path in file_paths
                ]

                unique_versions = sorted(set(local_versions))

                if len(unique_versions) == 1:
                    only_version = unique_versions[0]

                    if only_version == latest_version:
                        self.queue_log(
                            f"All {len(file_paths)} instance(s) of {dll_name} are already up to date ({only_version})",
                            "success",
                        )
                        continue

                    self.queue_log(
                        f"{dll_name} will update {len(file_paths)} instance(s) from {only_version} to {latest_version}"
                    )
                else:
                    version_summary = self.format_version_summary(local_versions)
                    self.queue_log(
                        f"{dll_name} has mixed installed versions: {version_summary}"
                    )
                    self.queue_log(
                        f"{dll_name} will update {len(file_paths)} instance(s) to {latest_version}"
                    )

                download_targets[dll_name] = {
                    "url": download_url,
                    "version": latest_version,
                }
                files_to_replace[dll_name] = file_paths
                version_details[dll_name] = {
                    "local_versions": local_versions,
                    "latest_version": latest_version,
                }

            if not download_targets:
                self.queue_log("All found DLSS files are already up to date", "success")
                return

            cache_hits = []
            seen_downloads = set()

            def report_progress(dll_name, value, version=None):
                if value == "cached":
                    cache_hits.append(dll_name)
                    self.queue_log(f"Using cached {dll_name} for version {version}")
                elif value is None:
                    if dll_name not in seen_downloads:
                        seen_downloads.add(dll_name)
                        self.queue_log(f"Downloading {dll_name}...")
                else:
                    self.queue_log(f"Downloading {dll_name}... {value}%")

            downloaded_files = download_dlss_files(
                download_targets, progress_callback=report_progress
            )

            if not downloaded_files:
                self.queue_log("Failed to download DLSS files", "error")
                return

            missing_downloads = [
                dll_name
                for dll_name in download_targets
                if dll_name not in downloaded_files
            ]
            for dll_name in missing_downloads:
                self.queue_log(f"Failed to download {dll_name}", "error")

            if len(cache_hits) != len(download_targets):
                self.queue_log("Download complete", "success")

            self.queue_log("Replacing files...")

            replace_targets = {
                dll_name: files_to_replace[dll_name] for dll_name in downloaded_files
            }

            update_results = replace_dlss_files(replace_targets, downloaded_files)

            had_errors = False

            for dll_name, (
                success,
                succeeded_paths,
                failed_paths,
            ) in update_results.items():
                latest_version = version_details[dll_name]["latest_version"]
                local_versions = version_details[dll_name]["local_versions"]
                old_version_summary = self.format_version_summary(local_versions)

                if succeeded_paths:
                    self.queue_log(
                        f"Updated {len(succeeded_paths)} instance(s) of {dll_name} from {old_version_summary} to {latest_version}"
                    )

                for failed_path, reason in failed_paths:
                    had_errors = True
                    self.queue_log(
                        f"Failed to update {dll_name}: {failed_path} ({reason})",
                        "error",
                    )

                if not success:
                    had_errors = True

            if update_results and not had_errors:
                self.queue_log("DLSS update complete", "success")
            else:
                self.queue_log("DLSS update finished with errors", "error")

            self.after(0, lambda: setattr(self, "found_dlss_files", found_dlss_files))

        except Exception as e:
            self.queue_log(f"Unexpected error: {e}", "error")
        finally:
            self.after(0, lambda: self.set_busy(False))

    def format_version_summary(self, versions: list[str]) -> str:
        counts = Counter(versions)
        parts = []

        for version in sorted(counts.keys()):
            count = counts[version]
            if count == 1:
                parts.append(version)
            else:
                parts.append(f"{version} x{count}")

        return ", ".join(parts)

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
