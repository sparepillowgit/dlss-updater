from pathlib import Path
from zipfile import ZipFile

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
