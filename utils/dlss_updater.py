import shutil
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from utils.app_paths import get_download_cache_dir


def download_dlss_files(
    download_targets: dict[str, dict], progress_callback=None
) -> dict[str, Path]:
    downloaded_files = {}

    for dll_name, target_info in download_targets.items():
        url = target_info["url"]
        version = target_info["version"]

        cache_dir = get_download_cache_dir(version)
        cache_dir.mkdir(parents=True, exist_ok=True)

        cached_file = cache_dir / dll_name

        # --- CACHE HIT ---
        if cached_file.exists():
            if progress_callback:
                progress_callback(dll_name, "cached", version)
            downloaded_files[dll_name] = cached_file
            continue

        try:
            with urlopen(url) as response:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0

                last_log_time = 0.0
                last_logged_percent = -1

                with open(cached_file, "wb") as file_handle:
                    while True:
                        chunk = response.read(64 * 1024)
                        if not chunk:
                            break

                        file_handle.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            now = time.time()
                            percent_jump = percent - last_logged_percent

                            should_log = percent != last_logged_percent and (
                                (now - last_log_time) >= 2
                                or percent == 100
                                or percent_jump >= 10
                            )

                            if should_log:
                                progress_callback(dll_name, percent)
                                last_log_time = now
                                last_logged_percent = percent

                if progress_callback and total_size <= 0:
                    progress_callback(dll_name, None)

                downloaded_files[dll_name] = cached_file

        except (HTTPError, URLError):
            if cached_file.exists():
                try:
                    cached_file.unlink()
                except OSError:
                    pass
            continue
        except OSError:
            if cached_file.exists():
                try:
                    cached_file.unlink()
                except OSError:
                    pass
            continue

    return downloaded_files


def replace_dlss_files(
    found_files: dict[str, list[Path]], downloaded_files: dict[str, Path]
) -> dict[str, tuple[bool, list[Path], list[tuple[Path, str]]]]:
    results = {}

    for dll_name, target_paths in found_files.items():
        source_path = downloaded_files.get(dll_name)

        if not source_path:
            results[dll_name] = (
                False,
                [],
                [(Path(""), f"Download missing for {dll_name}")],
            )
            continue

        succeeded = []
        failed = []

        for target_path in target_paths:
            try:
                shutil.copy2(source_path, target_path)
                succeeded.append(target_path)
            except PermissionError:
                failed.append(
                    (
                        target_path,
                        "Permission denied. Try running the app as administrator.",
                    )
                )
            except OSError as e:
                failed.append((target_path, str(e)))

        results[dll_name] = (len(failed) == 0, succeeded, failed)

    return results
