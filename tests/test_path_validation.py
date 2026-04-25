from utils.path_validation import is_invalid_directory


def test_invalid_directory_empty_string():
    assert is_invalid_directory("") is True


def test_invalid_directory_none():
    assert is_invalid_directory(None) is True


def test_valid_directory(tmp_path):
    assert is_invalid_directory(str(tmp_path)) is False


def test_normal_path_is_not_invalid(tmp_path):
    subdir = tmp_path / "Game"
    subdir.mkdir()

    assert is_invalid_directory(str(subdir)) is False
