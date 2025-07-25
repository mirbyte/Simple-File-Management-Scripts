[![License](https://img.shields.io/github/license/mirbyte/Simple-File-Management-Scripts?color=ffcd42)](https://raw.githubusercontent.com/mirbyte/Simple-File-Management-Scripts/master/LICENSE)
![Size](https://img.shields.io/github/repo-size/mirbyte/Simple-File-Management-Scripts?label=size&color=ffcd42)
[![Updated](https://img.shields.io/github/last-commit/mirbyte/Simple-File-Management-Scripts?color=ffcd42&label=updated)](https://github.com/mirbyte/Simple-File-Management-Scripts/commits/main)

# Simple File Management Scripts
Please read this README file very carefully to avoid any data losses. The scripts may vary in quality. I've made these for my own use and cannot guarantee their functionality for others. By default all the scripts use current directory as source.


### Root Directory Scripts

- **Album_Art_Applier.py**: Tool for `mp3` & `flac` files. Buggy as for now.
- **universal_prefix-suffix_remover.py**: Interactively removes a user-specified prefix or suffix from filenames.
- **rename_mvsep_files.py**: Renames audio files downloaded from `mvsep.com` to a cleaner format like `Song Title (stem).mp3`. *Doesn't really work for now*
- **rename_mvsep_files_with_AI.py**: Renames audio files downloaded from `mvsep.com` to a cleaner format like `Song Title (stem).mp3` with the help of Gemini API.
- **bulk image resizer (50%).bat**: Resizes all images 50% of their original size in currentdir.
- **+_to_space_in_filenames.py**: Replaces one or more consecutive '+' characters in filenames with a single space. Ignores Python scripts.
- **fix_spaces_in_filenames.py**: Cleans filenames in the current directory by removing leading/trailing spaces, spaces before the file extension, and replacing multiple spaces with a single space.
- **unzip_all_in_currentdir.py**: Finds and extracts all ZIP/RAR files within currentdir. Verifies extracted files and manages filename collisions.
- **FastFolderRemover.exe**: Faster only if the target folder contains A LOT of small files. Very niche product. Asks for the full path of target folder.



### Adlist Converters

- **Adguardlist_to_windowsHOSTSlist.py**: Converts an AdGuard blocklist file (like `||domain.com^`) into a Windows HOSTS file format (like `127.0.0.1 domain.com`).
- **domainlist_to_Adguardblocklist.py**: Converts a text file containing a list of domains (one per row) into the AdGuard blocklist format (`||domain.com^`).
- **domainlist_to_windowsHOSTSlist.py**: Converts a text file containing a list of domains into the Windows HOSTS file format (`127.0.0.1 domain.com`).
- **windowsHOSTSlist_to_domainlist.py**: Extracts domain names from a Windows HOSTS file and saves them to a simple domain list file.


<br>
<br>


*If you found this project useful, please drop a ⭐- it means a lot!*
