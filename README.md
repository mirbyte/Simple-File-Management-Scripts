# Simple-File-Management-Scripts IN PROGRESS
Please read this README file very carefully to avoid any data losses. The scripts may vary in quality. I have made these for my own use and cannot guarantee their functionality for others. Please use with caution. By default all the scripts use current directory as source.


### Root Directory Scripts

- **universal_prefix-suffix_remover.py**: Interactively removes a user-specified prefix or suffix from filenames.
- **rename_mvsep_files.py**: Renames audio files downloaded from `mvsep.com` to a cleaner format like `Song Title (stem).mp3`.
- **bulk image resizer (50%).bat**: Resizes all images 50% of their original size in currentdir.
- **+_to_space_in_filenames.py**: Replaces one or more consecutive '+' characters in filenames with a single space. Ignores Python scripts.
- **fix_spaces_in_filenames.py**: Cleans filenames in the current directory by removing leading/trailing spaces, spaces before the file extension, and replacing multiple spaces with a single space.
- **unzip_all_in_currentdir.py**: Finds and extracts all ZIP/RAR files within currentdir. Verifies extracted files and manages filename collisions.
- **FastFolderRemover.exe**: Faster only if the target folder contains A LOT of small files. Very niche product. Asks for the full path of target folder.



### Adlist Converters

- **Adguardlist_to_windowsHOSTSlist.py**: Converts an AdGuard blocklist file (like `||domain.com^`) into a Windows HOSTS file format (like `127.0.0.1 domain.com`).
- **domainlist_to_Adguardblocklist.py**: Converts a text file containing a list of domains (one per line) into the AdGuard blocklist format (`||domain.com^`).
- **domainlist_to_windowsHOSTSlist.py**: Converts a text file containing a list of domains into the Windows HOSTS file format (`127.0.0.1 domain.com`).
- **windowsHOSTSlist_to_domainlist.py**: Extracts domain names from a Windows HOSTS file and saves them to a simple domain list file.





