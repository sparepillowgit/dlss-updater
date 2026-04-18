from pathlib import Path

DLSS_DLL = "nvngx_dlss.dll"
DLSSG_DLL = "nvngx_dlssg.dll"


def find_dlss_files(root_folder: str) -> dict[str, list[Path]]:
    root = Path(root_folder)

    found_files = {
        DLSS_DLL: [],
        DLSSG_DLL: [],
    }

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        name = path.name.lower()

        if name == DLSS_DLL:
            found_files[DLSS_DLL].append(path)
        elif name == DLSSG_DLL:
            found_files[DLSSG_DLL].append(path)

    return found_files
