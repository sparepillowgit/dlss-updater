import sys
from pathlib import Path


def get_app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def get_download_cache_dir(version: str) -> Path:
    return get_app_base_dir() / "download" / version
