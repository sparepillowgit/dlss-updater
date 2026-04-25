from pathlib import Path

from utils.dlss_updater import replace_dlss_files


def test_replace_dlss_files_replaces_file_when_backup_succeeds(tmp_path):
    target = tmp_path / "nvngx_dlss.dll"
    target.write_bytes(b"old")

    source = tmp_path / "new.dll"
    source.write_bytes(b"new")

    found_files = {"nvngx_dlss.dll": [target]}
    downloaded_files = {"nvngx_dlss.dll": source}

    result = replace_dlss_files(found_files, downloaded_files)

    success, succeeded, failed, backup_results = result["nvngx_dlss.dll"]

    assert success is True
    assert target.read_bytes() == b"new"
    assert len(succeeded) == 1
    assert len(failed) == 0


def test_replace_dlss_files_skips_when_backup_fails(tmp_path, monkeypatch):
    target = tmp_path / "nvngx_dlss.dll"
    target.write_bytes(b"old")

    source = tmp_path / "new.dll"
    source.write_bytes(b"new")

    def mock_backup(*args, **kwargs):
        class Result:
            success = False
            created = False
            skipped_existing = False
            reason = "fail"

        return Result()

    monkeypatch.setattr(
        "utils.dlss_updater.create_backup_for_file",
        mock_backup,
    )

    found_files = {"nvngx_dlss.dll": [target]}
    downloaded_files = {"nvngx_dlss.dll": source}

    result = replace_dlss_files(found_files, downloaded_files)

    success, succeeded, failed, backup_results = result["nvngx_dlss.dll"]

    assert success is False
    assert target.read_bytes() == b"old"
    assert len(succeeded) == 0
    assert len(failed) == 1


def test_replace_dlss_files_continues_when_one_file_fails(tmp_path, monkeypatch):
    target1 = tmp_path / "a.dll"
    target2 = tmp_path / "b.dll"

    target1.write_bytes(b"old1")
    target2.write_bytes(b"old2")

    source = tmp_path / "new.dll"
    source.write_bytes(b"new")

    def mock_backup(path, *args, **kwargs):
        class Result:
            def __init__(self, success):
                self.success = success
                self.created = success
                self.skipped_existing = False
                self.reason = None

        if path == target1:
            return Result(False)
        return Result(True)

    monkeypatch.setattr(
        "utils.dlss_updater.create_backup_for_file",
        mock_backup,
    )

    found_files = {"nvngx_dlss.dll": [target1, target2]}
    downloaded_files = {"nvngx_dlss.dll": source}

    result = replace_dlss_files(found_files, downloaded_files)

    success, succeeded, failed, _ = result["nvngx_dlss.dll"]

    assert target1.read_bytes() == b"old1"
    assert target2.read_bytes() == b"new"

    assert len(succeeded) == 1
    assert len(failed) == 1
