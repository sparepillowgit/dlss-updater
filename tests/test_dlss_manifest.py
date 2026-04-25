from utils.dlss_manifest import get_manifest_entry


def test_get_manifest_entry_returns_matching_dll_entry():
    manifest = {
        "nvngx_dlss.dll": {
            "version": "3.8.10",
            "url": "https://example.com/nvngx_dlss.dll",
        },
        "nvngx_dlssg.dll": {
            "version": "3.8.10",
            "url": "https://example.com/nvngx_dlssg.dll",
        },
    }

    result = get_manifest_entry(manifest, "nvngx_dlss.dll")

    assert result is not None
    assert result["version"] == "3.8.10"
    assert result["url"] == "https://example.com/nvngx_dlss.dll"


def test_get_manifest_entry_returns_none_for_missing_dll():
    manifest = {
        "nvngx_dlss.dll": {
            "version": "3.8.10",
            "url": "https://example.com/nvngx_dlss.dll",
        }
    }

    result = get_manifest_entry(manifest, "nvngx_dlssd.dll")

    assert result is None


def test_get_manifest_entry_handles_empty_manifest():
    result = get_manifest_entry({}, "nvngx_dlss.dll")

    assert result is None


def test_get_manifest_entry_handles_none_manifest():
    result = get_manifest_entry(None, "nvngx_dlss.dll")

    assert result is None


def test_get_manifest_entry_ignores_non_dict_entry():
    manifest = {
        "nvngx_dlss.dll": "bad data",
    }

    result = get_manifest_entry(manifest, "nvngx_dlss.dll")

    assert result is None
