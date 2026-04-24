import os
from dataclasses import dataclass
from pathlib import Path
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile

BACKUP_SUFFIX = ".dubackup.zip"


@dataclass
class BackupResult:
    file_path: Path
    backup_path: Path | None
    success: bool
    created: bool
    skipped_existing: bool
    reason: str | None = None


@dataclass
class RestoreResult:
    zip_path: Path
    restored_path: Path | None
    success: bool
    deleted_backup: bool
    reason: str | None = None


def safe_version_text(version: str | None) -> str:
    if not version:
        return "unknown"

    cleaned = str(version).strip()

    for char in '<>:"/\\|?*':
        cleaned = cleaned.replace(char, "_")

    return cleaned or "unknown"


def get_backup_path(file_path: str | Path, version: str | None) -> Path:
    file_path = Path(file_path)
    version_text = safe_version_text(version)
    return file_path.with_name(f"{file_path.name}.{version_text}{BACKUP_SUFFIX}")


def create_backup_for_file(file_path: str | Path, version: str | None) -> BackupResult:
    file_path = Path(file_path)
    backup_path = get_backup_path(file_path, version)

    if not file_path.exists():
        return BackupResult(
            file_path=file_path,
            backup_path=backup_path,
            success=False,
            created=False,
            skipped_existing=False,
            reason="Source file does not exist.",
        )

    if backup_path.exists():
        return BackupResult(
            file_path=file_path,
            backup_path=backup_path,
            success=True,
            created=False,
            skipped_existing=True,
        )

    try:
        with ZipFile(backup_path, "w", compression=ZIP_DEFLATED) as zip_file:
            zip_file.write(file_path, arcname=file_path.name)

        return BackupResult(
            file_path=file_path,
            backup_path=backup_path,
            success=True,
            created=True,
            skipped_existing=False,
        )

    except OSError as e:
        return BackupResult(
            file_path=file_path,
            backup_path=backup_path,
            success=False,
            created=False,
            skipped_existing=False,
            reason=str(e),
        )


def restore_backup_file(zip_path: str | Path) -> RestoreResult:
    zip_path = Path(zip_path)

    if not zip_path.name.endswith(BACKUP_SUFFIX):
        return RestoreResult(
            zip_path=zip_path,
            restored_path=None,
            success=False,
            deleted_backup=False,
            reason="Not a DLSS Updater backup file.",
        )

    if not zip_path.exists():
        return RestoreResult(
            zip_path=zip_path,
            restored_path=None,
            success=False,
            deleted_backup=False,
            reason="Backup file does not exist.",
        )

    try:
        with ZipFile(zip_path, "r") as zip_file:
            names = [
                name
                for name in zip_file.namelist()
                if not name.endswith("/") and Path(name).suffix.lower() == ".dll"
            ]

            if len(names) != 1:
                return RestoreResult(
                    zip_path=zip_path,
                    restored_path=None,
                    success=False,
                    deleted_backup=False,
                    reason="Backup must contain exactly one DLL file.",
                )

            dll_name = Path(names[0]).name
            restored_path = zip_path.parent / dll_name

            with zip_file.open(names[0]) as source, open(restored_path, "wb") as target:
                target.write(source.read())

        try:
            zip_path.unlink()
        except OSError as e:
            return RestoreResult(
                zip_path=zip_path,
                restored_path=restored_path,
                success=True,
                deleted_backup=False,
                reason=f"Restored, but could not delete backup: {e}",
            )

        return RestoreResult(
            zip_path=zip_path,
            restored_path=restored_path,
            success=True,
            deleted_backup=True,
        )

    except BadZipFile:
        return RestoreResult(
            zip_path=zip_path,
            restored_path=None,
            success=False,
            deleted_backup=False,
            reason="Backup file is not a valid zip file.",
        )

    except OSError as e:
        return RestoreResult(
            zip_path=zip_path,
            restored_path=None,
            success=False,
            deleted_backup=False,
            reason=str(e),
        )


def find_backup_files(root_folder: str | Path) -> list[Path]:
    root_folder = Path(root_folder)

    if not root_folder.exists() or not root_folder.is_dir():
        return []

    backup_files: list[Path] = []

    for folder_path, _, file_names in os.walk(root_folder):
        for file_name in file_names:
            if file_name.endswith(BACKUP_SUFFIX):
                backup_files.append(Path(folder_path) / file_name)

    return backup_files
