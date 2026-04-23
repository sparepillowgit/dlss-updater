from __future__ import annotations


def get_major(version: str) -> int:
    try:
        return int(version.split(".")[0])
    except Exception:
        return -1


def get_version_family(version: str) -> str:
    major = get_major(version)

    if major == -1:
        return "unknown"

    # DLSS 1.x
    if major == 1:
        return "legacy"

    # DLSS 2.x, 3.x, and compact formats like 310.x
    if major >= 2:
        return "modern"

    return "unknown"


def can_update_between_versions(installed_version: str, latest_version: str) -> bool:
    installed_family = get_version_family(installed_version)
    latest_family = get_version_family(latest_version)

    if installed_family == "unknown" or latest_family == "unknown":
        return False

    return installed_family == latest_family


def get_skip_reason(filename: str, installed_version: str, latest_version: str) -> str:
    installed_family = get_version_family(installed_version)
    latest_family = get_version_family(latest_version)

    if installed_family == "unknown":
        return f"Installed {filename} version is unknown, cannot safely update"

    if latest_family == "unknown":
        return f"Latest {filename} version is unknown, cannot safely update"

    if installed_family == "legacy" and latest_family == "modern":
        return f"{filename} 1.x is not interchangeable with 2.x/3.x"

    if installed_family == "modern" and latest_family == "legacy":
        return f"{filename} 2.x/3.x is not interchangeable with 1.x"

    return f"{filename} cannot be safely updated across major version families"
