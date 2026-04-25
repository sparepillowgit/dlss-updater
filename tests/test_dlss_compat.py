from utils.dlss_compat import can_update_between_versions


def test_1x_to_1x_allowed():
    assert can_update_between_versions("1.0.0", "1.2.0") is True


def test_1x_to_2x_blocked():
    assert can_update_between_versions("1.9.9", "2.0.0") is False


def test_2x_to_3x_allowed():
    assert can_update_between_versions("2.5.0", "3.0.0") is True


def test_3x_to_2x_allowed():
    assert can_update_between_versions("3.1.0", "2.5.0") is True


def test_same_version_allowed():
    assert can_update_between_versions("3.8.10", "3.8.10") is True


def test_unknown_versions_handled():
    assert can_update_between_versions("unknown", "3.8.10") is False
    assert can_update_between_versions("3.8.10", "unknown") is False
