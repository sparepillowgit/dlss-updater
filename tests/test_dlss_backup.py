from zipfile import ZipFile

from services.dlss_backup_service import delete_dlss_backups
from utils.dlss_backup import (
    create_backup_for_file,
    find_backup_files,
    restore_backup_file,
)


def test_create_backup_for_file_creates_zip_next_to_dll(tmp_path):
    dll_path = tmp_path / "nvngx_dlss.dll"
    dll_path.write_bytes(b"original dll content")

    result = create_backup_for_file(dll_path, "3.8.10")

    expected_backup = tmp_path / "nvngx_dlss.dll.3.8.10.dubackup.zip"

    assert result.success is True
    assert result.created is True
    assert result.skipped_existing is False
    assert expected_backup.exists()

    with ZipFile(expected_backup, "r") as zip_file:
        assert zip_file.namelist() == ["nvngx_dlss.dll"]
        assert zip_file.read("nvngx_dlss.dll") == b"original dll content"


def test_create_backup_for_file_skips_existing_backup(tmp_path):
    dll_path = tmp_path / "nvngx_dlss.dll"
    dll_path.write_bytes(b"original dll content")

    first_result = create_backup_for_file(dll_path, "3.8.10")
    second_result = create_backup_for_file(dll_path, "3.8.10")

    assert first_result.success is True
    assert first_result.created is True

    assert second_result.success is True
    assert second_result.created is False
    assert second_result.skipped_existing is True


def test_create_backup_for_file_overwrites_existing_backup_when_requested(tmp_path):
    dll_path = tmp_path / "nvngx_dlss.dll"
    dll_path.write_bytes(b"first dll content")

    first_result = create_backup_for_file(dll_path, "3.8.10")

    dll_path.write_bytes(b"second dll content")

    second_result = create_backup_for_file(
        dll_path,
        "3.8.10",
        overwrite_existing=True,
    )

    assert first_result.success is True
    assert second_result.success is True
    assert second_result.created is True
    assert second_result.skipped_existing is False

    with ZipFile(second_result.backup_path, "r") as zip_file:
        assert zip_file.read("nvngx_dlss.dll") == b"second dll content"


def test_create_backup_for_file_fails_for_missing_file(tmp_path):
    dll_path = tmp_path / "nvngx_dlss.dll"

    result = create_backup_for_file(dll_path, "3.8.10")

    assert result.success is False
    assert result.created is False
    assert result.skipped_existing is False
    assert result.reason is not None


def test_restore_backup_file_restores_dll_and_deletes_zip(tmp_path):
    dll_path = tmp_path / "nvngx_dlss.dll"
    dll_path.write_bytes(b"original dll content")

    backup_result = create_backup_for_file(dll_path, "3.8.10")
    backup_path = backup_result.backup_path

    dll_path.write_bytes(b"updated dll content")

    restore_result = restore_backup_file(backup_path)

    assert restore_result.success is True
    assert restore_result.deleted_backup is True
    assert dll_path.read_bytes() == b"original dll content"
    assert not backup_path.exists()


def test_find_backup_files_finds_dubackup_zips_recursively(tmp_path):
    nested = tmp_path / "Game" / "bin" / "x64"
    nested.mkdir(parents=True)

    backup_1 = tmp_path / "nvngx_dlss.dll.3.8.10.dubackup.zip"
    backup_2 = nested / "nvngx_dlssg.dll.3.8.10.dubackup.zip"
    normal_zip = nested / "something.zip"

    backup_1.write_bytes(b"fake")
    backup_2.write_bytes(b"fake")
    normal_zip.write_bytes(b"fake")

    results = find_backup_files(tmp_path)

    assert backup_1 in results
    assert backup_2 in results
    assert normal_zip not in results


def test_delete_dlss_backups_deletes_backup_files(tmp_path):
    backup_path = tmp_path / "nvngx_dlss.dll.3.8.10.dubackup.zip"
    backup_path.write_bytes(b"backup")

    result = delete_dlss_backups(tmp_path)

    assert not backup_path.exists()
    assert result.had_errors is False
    assert any(event.message == "All backups deleted" for event in result.events)


def test_delete_dlss_backups_deletes_backup_files_recursively(tmp_path):
    nested = tmp_path / "Game" / "bin" / "x64"
    nested.mkdir(parents=True)

    backup_1 = tmp_path / "nvngx_dlss.dll.3.8.10.dubackup.zip"
    backup_2 = nested / "nvngx_dlssg.dll.3.8.10.dubackup.zip"
    normal_zip = nested / "something.zip"

    backup_1.write_bytes(b"backup")
    backup_2.write_bytes(b"backup")
    normal_zip.write_bytes(b"not a backup")

    result = delete_dlss_backups(tmp_path)

    assert not backup_1.exists()
    assert not backup_2.exists()
    assert normal_zip.exists()
    assert result.had_errors is False
    assert any(event.message == "All backups deleted" for event in result.events)


def test_delete_dlss_backups_handles_no_backups(tmp_path):
    result = delete_dlss_backups(tmp_path)

    assert result.had_errors is False
    assert any(event.message == "No DLSS backup files found" for event in result.events)
