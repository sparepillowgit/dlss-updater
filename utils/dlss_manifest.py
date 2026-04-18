import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

MANIFEST_URL = "https://github.com/sparepillowgit/dlss-updater-files/releases/latest/download/dlss_manifest.json"


def fetch_manifest() -> dict | None:
    try:
        with urlopen(MANIFEST_URL, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    except (HTTPError, URLError):
        return None
    except json.JSONDecodeError:
        return None


def get_manifest_entry(manifest: dict | None, dll_name: str) -> dict | None:
    if not manifest:
        return None

    entry = manifest.get(dll_name)
    return entry if isinstance(entry, dict) else None
