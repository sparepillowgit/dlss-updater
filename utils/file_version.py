import ctypes
from ctypes import wintypes


class VS_FIXEDFILEINFO(ctypes.Structure):
    _fields_ = [
        ("dwSignature", wintypes.DWORD),
        ("dwStrucVersion", wintypes.DWORD),
        ("dwFileVersionMS", wintypes.DWORD),
        ("dwFileVersionLS", wintypes.DWORD),
        ("dwProductVersionMS", wintypes.DWORD),
        ("dwProductVersionLS", wintypes.DWORD),
        ("dwFileFlagsMask", wintypes.DWORD),
        ("dwFileFlags", wintypes.DWORD),
        ("dwFileOS", wintypes.DWORD),
        ("dwFileType", wintypes.DWORD),
        ("dwFileSubtype", wintypes.DWORD),
        ("dwFileDateMS", wintypes.DWORD),
        ("dwFileDateLS", wintypes.DWORD),
    ]


def get_file_version(path: str) -> str | None:
    size = ctypes.windll.version.GetFileVersionInfoSizeW(path, None)
    if not size:
        return None

    buffer = ctypes.create_string_buffer(size)

    success = ctypes.windll.version.GetFileVersionInfoW(path, 0, size, buffer)
    if not success:
        return None

    value_ptr = ctypes.c_void_p()
    value_len = wintypes.UINT()

    success = ctypes.windll.version.VerQueryValueW(
        buffer, "\\", ctypes.byref(value_ptr), ctypes.byref(value_len)
    )
    if not success:
        return None

    file_info = ctypes.cast(value_ptr, ctypes.POINTER(VS_FIXEDFILEINFO)).contents

    major = file_info.dwFileVersionMS >> 16
    minor = file_info.dwFileVersionMS & 0xFFFF
    build = file_info.dwFileVersionLS >> 16
    revision = file_info.dwFileVersionLS & 0xFFFF

    return f"{major}.{minor}.{build}.{revision}"
