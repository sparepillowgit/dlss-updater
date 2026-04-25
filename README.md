# DLSS Updater

A simple open-source, on-demand desktop tool for finding and updating NVIDIA DLSS files in your game folders.

![CI](https://github.com/sparepillowgit/dlss-updater/actions/workflows/tests.yml/badge.svg)
![Release](https://img.shields.io/github/v/release/sparepillowgit/dlss-updater)
![Last commit](https://img.shields.io/github/last-commit/sparepillowgit/dlss-updater)
![License](https://img.shields.io/github/license/sparepillowgit/dlss-updater)
![Python](https://img.shields.io/badge/python-3.13-blue)

---

## Links

- Website: https://www.dlssupdater.com
- GitHub: https://github.com/sparepillowgit/dlss-updater
- Latest Release: https://github.com/sparepillowgit/dlss-updater/releases/latest

---

## Features

- Recursively scans a selected game folder
- Detects:
  - `nvngx_dlss.dll`
  - `nvngx_dlssg.dll`
  - `nvngx_dlssd.dll`
- Compares installed versions against the latest release
- Safely updates DLSS files with version compatibility checks:
  - 1.x versions are only updated within 1.x
  - 2.x and 3.x versions are treated as compatible
  - Blocks unsafe cross-version updates that can break older titles
- Automatically creates per-file backups before updating
- Restore original files from backups at any time

---

## Screenshot

![DLSS Updater Screenshot](assets/screenshot-v1.3.0.png)

---

## Download

Download the latest version:

https://github.com/sparepillowgit/dlss-updater/releases/latest

- ~10 MB download
- Portable (no installation required)

---

## Usage

1. Launch the application
2. Click **"Select Game Folder"**
3. Select your game installation directory
4. Click **"Update DLSS Files"**

---

## Notes

- You may need to run as **Administrator**
- The tool will skip downloading files if they are already cached
- Only files that need updating will be replaced
- Some games rely on specific DLSS versions. If issues occur, restore backups or verify your game files through your launcher

---

## FAQ

**What are DLSS files?**  
DLSS files are NVIDIA libraries used by supported games for features like AI upscaling, frame generation, and ray reconstruction. Files such as `nvngx_dlss.dll` are bundled with games and can sometimes be updated for better performance or image quality.

**How does DLSS Updater work?**  
It scans a selected game folder, detects DLSS files, and updates them when newer versions are available.

**Why choose this over DLSS Swapper?**  
DLSS Swapper offers more features, but DLSS Updater focuses on simplicity. It's a lightweight, no-setup tool that quickly scans your game folders and updates DLSS files without extra integrations or background processes.

**Does it require installation?**  
No. DLSS Updater is a portable tool and can be run directly from a folder or USB drive.

**How large is the download?**  
The download is around 10 MB. Additional space will be used when downloading updated DLSS files.

**Can updating DLSS files break my game?**  
Yes. Updating DLSS can cause issues in some games. Restore the original file or verify your game files through your launcher (Steam, etc.) if this happens.

**Why did my antivirus flag DLSS Updater?**  
This can happen because the tool downloads and replaces files, behaviour similar to some malware, which may trigger heuristic detection. The tool is open source and safe to use when downloaded from the official source.

---

## Development

### Build From Source

#### Requirements

- Python 3.13

#### Environment Setup (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip pyinstaller
rmdir /s /q build
rmdir /s /q dist
del /q *.spec
```

#### Build Command

```
pyinstaller --clean --noconfirm --onefile --windowed --name dlss-updater --icon=icon.ico --version-file=version_info.txt --add-data "icon.ico;." main.py
```

#### Output

The built application will be created in:

```
dist\
```

Run the executable from that folder:

```
dist\dlss-updater.exe
```