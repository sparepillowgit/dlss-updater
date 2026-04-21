from pathlib import Path

TARGET_FILES = {
    "nvngx_dlss.dll",
    "nvngx_dlssg.dll",
    "nvngx_dlssd.dll",
}


def find_dlss_files(root_folder: str) -> dict[str, list[Path]]:
    root = Path(root_folder)

    found_files = {name: [] for name in TARGET_FILES}

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        name = path.name.lower()

        if name in TARGET_FILES:
            found_files[name].append(path)

    return found_files
