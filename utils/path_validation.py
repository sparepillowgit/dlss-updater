import os


def normalise_path(path: str) -> str:
    return os.path.abspath(path).lower()


def is_root_directory(path: str) -> bool:
    path = os.path.abspath(path)
    return os.path.dirname(path) == path


def is_system_directory(path: str) -> bool:
    path = normalise_path(path)

    system_paths = [
        os.environ.get("SystemRoot", "C:\\Windows"),
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
    ]

    for system_path in system_paths:
        if path == normalise_path(system_path):
            return True

    return False


def is_invalid_directory(path: str) -> bool:
    if not path:
        return True

    return is_root_directory(path) or is_system_directory(path)
