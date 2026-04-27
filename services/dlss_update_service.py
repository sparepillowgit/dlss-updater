from pathlib import Path
from typing import Callable

from services.dlss_version_service import format_version_summary
from services.service_events import DlssUpdateResult, ServiceEvent
from utils.dlss_compat import can_update_between_versions, get_skip_reason
from utils.dlss_finder import find_dlss_files
from utils.dlss_manifest import fetch_manifest, get_manifest_entry
from utils.dlss_updater import download_dlss_files, replace_dlss_files
from utils.file_version import get_file_version

DLSS_DLL = "nvngx_dlss.dll"
DLSSG_DLL = "nvngx_dlssg.dll"
DLSSD_DLL = "nvngx_dlssd.dll"

ConfirmOverwriteBackup = Callable[[Path, Path], bool]
EmitEvent = Callable[[ServiceEvent], None]


def update_dlss_files(
    folder: str | Path,
    confirm_overwrite_backup: ConfirmOverwriteBackup | None = None,
    emit: EmitEvent | None = None,
) -> DlssUpdateResult:
    result = DlssUpdateResult()

    def add_event(message: str, tag: str | None = None) -> None:
        event = ServiceEvent(message, tag)
        result.events.append(event)

        if emit:
            emit(event)

    add_event("Searching for DLSS files...")

    found_files = find_dlss_files(str(folder))
    found_dlss_files = {name: paths for name, paths in found_files.items() if paths}
    result.found_dlss_files = found_dlss_files

    _add_found_counts(found_files, add_event)

    if not found_dlss_files:
        result.had_errors = True
        add_event("No DLSS files were found", "error")
        return result

    add_event("Checking installed versions...")

    manifest = fetch_manifest()
    download_targets = {}
    files_to_replace = {}
    version_details = {}

    for dll_name, file_paths in found_dlss_files.items():
        entry = get_manifest_entry(manifest, dll_name)

        if not entry:
            result.had_errors = True
            add_event(f"No manifest entry found for {dll_name}", "error")
            continue

        latest_version = entry.get("version", "unknown")
        download_url = entry.get("url")

        if not download_url:
            result.had_errors = True
            add_event(f"No download URL found in manifest for {dll_name}", "error")
            continue

        replace_paths, replace_versions = _collect_update_targets(
            dll_name=dll_name,
            file_paths=file_paths,
            latest_version=latest_version,
            add_event=add_event,
        )

        if not replace_paths:
            continue

        add_event(
            f"{dll_name} will update {len(replace_paths)} instance(s) "
            f"from {format_version_summary(replace_versions)} to {latest_version}"
        )

        download_targets[dll_name] = {
            "url": download_url,
            "version": latest_version,
        }
        files_to_replace[dll_name] = replace_paths
        version_details[dll_name] = {
            "local_versions": replace_versions,
            "latest_version": latest_version,
        }

    if not download_targets:
        add_event("No compatible DLSS files need updating", "success")
        return result

    downloaded_files = _download_required_files(download_targets, add_event)

    if not downloaded_files:
        result.had_errors = True
        add_event("Failed to download DLSS files", "error")
        return result

    for dll_name in download_targets:
        if dll_name not in downloaded_files:
            result.had_errors = True
            add_event(f"Failed to download {dll_name}", "error")

    add_event("Backing up and replacing files...")

    replace_targets = {
        dll_name: files_to_replace[dll_name] for dll_name in downloaded_files
    }

    update_results = replace_dlss_files(
        replace_targets,
        downloaded_files,
        confirm_overwrite_backup=confirm_overwrite_backup,
    )

    _add_update_results(
        result=result,
        update_results=update_results,
        version_details=version_details,
        add_event=add_event,
    )

    if update_results and not result.had_errors:
        add_event("DLSS update complete", "success")
    else:
        add_event("DLSS update finished with errors", "error")

    return result


def _add_found_counts(
    found_files: dict[str, list[Path]],
    add_event,
) -> None:
    for dll_name in (DLSS_DLL, DLSSG_DLL, DLSSD_DLL):
        count = len(found_files.get(dll_name, []))

        if count > 0:
            add_event(f"Found {count} instance(s) of {dll_name}")
        else:
            add_event(f"Did not find {dll_name}")


def _collect_update_targets(
    dll_name: str,
    file_paths: list[Path],
    latest_version: str,
    add_event,
) -> tuple[list[Path], list[str]]:
    up_to_date_paths = []
    up_to_date_versions = []
    replace_paths = []
    replace_versions = []

    for file_path in file_paths:
        installed_version = get_file_version(str(file_path)) or "unknown"

        if not can_update_between_versions(installed_version, latest_version):
            reason = get_skip_reason(dll_name, installed_version, latest_version)
            add_event(f"Skipping {dll_name}: {reason}")
            add_event(
                f"Skipped file: {file_path} "
                f"(installed: {installed_version}, latest: {latest_version})"
            )
            continue

        if installed_version == latest_version:
            up_to_date_paths.append(file_path)
            up_to_date_versions.append(installed_version)
        else:
            replace_paths.append(file_path)
            replace_versions.append(installed_version)

    if up_to_date_paths:
        add_event(
            f"{len(up_to_date_paths)} instance(s) of {dll_name} are already up to date "
            f"({format_version_summary(up_to_date_versions)})",
            "success",
        )

    return replace_paths, replace_versions


def _download_required_files(
    download_targets: dict[str, dict],
    add_event,
) -> dict[str, Path]:
    cache_hits = []
    seen_downloads = set()

    def report_progress(dll_name, value, version=None):
        if value == "cached":
            cache_hits.append(dll_name)
            add_event(f"Using cached {dll_name} for version {version}")
        elif value is None:
            if dll_name not in seen_downloads:
                seen_downloads.add(dll_name)
                add_event(f"Downloading {dll_name}...")
        else:
            add_event(f"Downloading {dll_name}... {value}%")

    downloaded_files = download_dlss_files(
        download_targets,
        progress_callback=report_progress,
    )

    if len(cache_hits) != len(download_targets):
        add_event("Download complete", "success")

    return downloaded_files


def _add_update_results(
    result: DlssUpdateResult,
    update_results: dict,
    version_details: dict,
    add_event,
) -> None:
    for dll_name, update_result in update_results.items():
        success = update_result[0]
        succeeded_paths = update_result[1]
        failed_paths = update_result[2]
        backup_results = update_result[3] if len(update_result) > 3 else []

        latest_version = version_details[dll_name]["latest_version"]
        local_versions = version_details[dll_name]["local_versions"]
        old_version_summary = format_version_summary(local_versions)

        for backup_result in backup_results:
            if backup_result.success and backup_result.created:
                add_event(f"Backed up {backup_result.file_path}")
            elif backup_result.success and backup_result.skipped_existing:
                add_event(f"Backup already exists for {backup_result.file_path}")

        if succeeded_paths:
            result.updated_count += len(succeeded_paths)
            add_event(
                f"Updated {len(succeeded_paths)} instance(s) of {dll_name} "
                f"from {old_version_summary} to {latest_version}"
            )

        for failed_path, reason in failed_paths:
            result.had_errors = True
            add_event(f"Failed to update {dll_name}: {failed_path} ({reason})", "error")

        if not success:
            result.had_errors = True
