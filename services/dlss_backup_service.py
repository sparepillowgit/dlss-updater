from pathlib import Path

from services.service_events import BackupRestoreResult, ServiceEvent
from utils.dlss_backup import find_backup_files, restore_backup_file


def restore_dlss_backups(folder: str | Path) -> BackupRestoreResult:
    result = BackupRestoreResult()

    result.events.append(ServiceEvent("Searching for DLSS backups..."))

    backup_files = find_backup_files(folder)

    if not backup_files:
        result.had_errors = True
        result.events.append(ServiceEvent("No DLSS backup files were found", "error"))
        return result

    result.events.append(ServiceEvent(f"Found {len(backup_files)} DLSS backup file(s)"))
    result.events.append(ServiceEvent("Restoring backups..."))

    for backup_file in backup_files:
        restore_result = restore_backup_file(backup_file)

        if restore_result.success:
            result.restored_count += 1

            if restore_result.deleted_backup:
                result.events.append(
                    ServiceEvent(f"Restored {restore_result.restored_path}", "success")
                )
            else:
                result.had_errors = True
                result.events.append(
                    ServiceEvent(
                        f"Restored {restore_result.restored_path}, "
                        f"but backup was not deleted: {restore_result.reason}",
                        "error",
                    )
                )
        else:
            result.had_errors = True
            result.events.append(
                ServiceEvent(
                    f"Failed to restore {restore_result.zip_path}: {restore_result.reason}",
                    "error",
                )
            )

    if result.restored_count and not result.had_errors:
        result.events.append(ServiceEvent("DLSS backup restore complete", "success"))
    elif result.restored_count:
        result.events.append(
            ServiceEvent("DLSS backup restore finished with errors", "error")
        )
    else:
        result.events.append(ServiceEvent("No DLSS backups were restored", "error"))

    return result


def delete_dlss_backups(folder: str | Path) -> BackupRestoreResult:
    result = BackupRestoreResult()

    result.events.append(ServiceEvent("Searching for DLSS backups..."))

    backup_files = find_backup_files(folder)

    if not backup_files:
        result.events.append(ServiceEvent("No DLSS backup files found", "error"))
        return result

    result.events.append(ServiceEvent(f"Found {len(backup_files)} backup file(s)"))
    result.events.append(ServiceEvent("Deleting backups..."))

    deleted_count = 0

    for backup_file in backup_files:
        try:
            Path(backup_file).unlink()
            deleted_count += 1
            result.events.append(ServiceEvent(f"Deleted {backup_file}", "success"))
        except Exception as e:
            result.had_errors = True
            result.events.append(
                ServiceEvent(f"Failed to delete {backup_file}: {e}", "error")
            )

    if deleted_count and not result.had_errors:
        result.events.append(ServiceEvent("All backups deleted", "success"))
    elif deleted_count:
        result.events.append(ServiceEvent("Some backups deleted with errors", "error"))
    else:
        result.events.append(ServiceEvent("No backups were deleted", "error"))

    return result
