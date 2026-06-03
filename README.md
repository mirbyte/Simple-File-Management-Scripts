[![License](https://img.shields.io/github/license/mirbyte/Simple-File-Management-Scripts?color=ffcd42)](https://raw.githubusercontent.com/mirbyte/Simple-File-Management-Scripts/master/LICENSE)
![Size](https://img.shields.io/github/repo-size/mirbyte/Simple-File-Management-Scripts?label=size&color=ffcd42)
[![Updated](https://img.shields.io/github/last-commit/mirbyte/Simple-File-Management-Scripts?color=ffcd42&label=updated)](https://github.com/mirbyte/Simple-File-Management-Scripts/commits/main)

# Simple File Management Scripts

Please read this README carefully to avoid any data loss.  
The scripts may vary in quality – I made them for my own use and cannot guarantee their functionality for everyone.

> **Platform notes**  
> - `fast_folder_remover.py` and `bulk image resizer (50%).bat` are designed for **Windows** (they use `robocopy`, `rd`, and PowerShell).  
> - All other Python scripts should work on any OS where Python 3 is available.  

By default, most scripts use the **current working directory** as the source.  
*Exceptions*: `fast_folder_remover.py` asks for a full folder path, and the Adlist converters open a file selection dialog.

## Root Directory Scripts

- **`universal_prefix-suffix_remover.py`** – Interactively removes a user‑specified prefix or suffix from filenames. Supports dry‑run, case‑sensitive toggle, and cleans up stray spaces.

- **`bulk image resizer (50%).bat`** – Resizes all `.jpg`, `.jpeg`, `.png` images in the current folder to 50% of their original size. Saves resized copies with a `_resized` suffix (originals are kept).

- **`+_to_space_in_filenames.py`** – Replaces one or more consecutive `+` characters in filenames with a single space. Ignores `.py` scripts.

- **`fix_spaces_in_filenames.py`** – Cleans filenames by removing leading/trailing spaces, spaces before the file extension, and replacing multiple spaces with a single space.

- **`fast_folder_remover.py`** – **Windows only**. Deletes a folder and all its contents quickly, especially when it contains many small files. Uses `robocopy /MIR` with an empty temporary folder, then falls back to `shutil.rmtree` and `rd /s /q`. Includes safety blacklists for critical system paths.

- **`txt_file_splitter.py`** – Splits a text file into 2‑20 parts. Smart splitting tries to cut at paragraph or line breaks for even distribution. Shows detailed statistics (size per part, variance).

## Adlist Converters

All converter scripts open a file dialog, transform the selected file, and save the result in the same folder with a descriptive suffix.

- **`Adguardlist_to_windowsHOSTSlist.py`** – Converts an AdGuard blocklist (`||domain.com^`) into Windows HOSTS format (`127.0.0.1 domain.com`).

- **`domainlist_to_Adguardblocklist.py`** – Converts a simple list of domains (one per line) into AdGuard rules (`||domain.com^`).

- **`domainlist_to_windowsHOSTSlist.py`** – Converts a domain list into Windows HOSTS file entries.

- **`windowsHOSTSlist_to_domainlist.py`** – Extracts domain names from a Windows HOSTS file and saves them as a plain domain list.

---

*If you found this project useful, please drop a ⭐ – it means a lot!*
