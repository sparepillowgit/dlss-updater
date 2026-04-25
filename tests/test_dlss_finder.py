from utils.dlss_finder import find_dlss_files


def test_find_dlss_files_finds_supported_dlls_recursively(tmp_path):
    game_folder = tmp_path / "Game"
    nested_folder = game_folder / "bin" / "x64"
    nested_folder.mkdir(parents=True)

    dlss_file = game_folder / "nvngx_dlss.dll"
    dlssg_file = nested_folder / "nvngx_dlssg.dll"
    dlssd_file = nested_folder / "nvngx_dlssd.dll"

    dlss_file.write_bytes(b"dlss")
    dlssg_file.write_bytes(b"dlssg")
    dlssd_file.write_bytes(b"dlssd")

    result = find_dlss_files(str(game_folder))

    assert dlss_file in result["nvngx_dlss.dll"]
    assert dlssg_file in result["nvngx_dlssg.dll"]
    assert dlssd_file in result["nvngx_dlssd.dll"]


def test_find_dlss_files_ignores_unrelated_files(tmp_path):
    game_folder = tmp_path / "Game"
    game_folder.mkdir()

    unrelated_file = game_folder / "not_dlss.dll"
    unrelated_file.write_bytes(b"not dlss")

    result = find_dlss_files(str(game_folder))

    assert result["nvngx_dlss.dll"] == []
    assert result["nvngx_dlssg.dll"] == []
    assert result["nvngx_dlssd.dll"] == []


def test_find_dlss_files_matches_case_insensitively(tmp_path):
    game_folder = tmp_path / "Game"
    game_folder.mkdir()

    mixed_case_file = game_folder / "NVNGX_DLSS.DLL"
    mixed_case_file.write_bytes(b"dlss")

    result = find_dlss_files(str(game_folder))

    assert mixed_case_file in result["nvngx_dlss.dll"]


def test_find_dlss_files_empty_folder(tmp_path):
    from utils.dlss_finder import find_dlss_files

    result = find_dlss_files(str(tmp_path))

    assert all(len(v) == 0 for v in result.values())
