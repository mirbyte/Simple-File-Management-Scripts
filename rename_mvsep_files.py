import os
import re
import argparse
from pathlib import Path


def clean_filename(filename):
    # lean up audio filenames by removing unwanted patterns from mvsep.com files.
    # Formats the name as 'Song Title (stem).mp3' or 'Song Title.mp3'.

    # Pattern for files with stem type (e.g., vocals, drums)
    pattern_with_stem = r'^\d{14}-[a-f0-9]{10}-(.*?)_(?:.*?_)?(?:mdx\w+_mt_\d+_)?([a-zA-Z0-9]{1,7})_\[mvsep\.com\](?:\.mp3)?$'

    # Pattern for files without a stem type but with an underscore before [mvsep.com]
    pattern_without_stem = r'^\d{14}-[a-f0-9]{10}-(.*?)_(?:.*?_)?(?:mdx\w+_mt_\d+_)?\[mvsep\.com\](?:\.mp3)?$'

    # Pattern for files without an underscore or stem type before [mvsep.com]
    pattern_no_underscore = r'^\d{14}-[a-f0-9]{10}-(.*?)\[mvsep\.com\](?:\.mp3)?$'

    cleaned_name = None
    stem_type = None
    title_part = None

    # Try matching with the first pattern (with stem)
    match = re.match(pattern_with_stem, filename)
    if match:
        title_part = match.group(1)
        stem_type = match.group(2)

    # If no match, try the second pattern (without stem, with underscore)
    if not match:
        match = re.match(pattern_without_stem, filename)
        if match:
            title_part = match.group(1)

    # If still no match, try the third pattern (no underscore)
    if not match:
        match = re.match(pattern_no_underscore, filename)
        if match:
            title_part = match.group(1)

    # If any pattern matched and we extracted a title part
    if title_part:
        # *** ADDED: Strip trailing dots, underscores, or spaces from the captured title part ***
        # This handles cases like 'title._[metadata]' by removing the trailing '.'
        title_part = title_part.rstrip('._ ')

        # Replace hyphens with spaces
        title_part = title_part.replace('-', ' ')
        # Capitalize the first letter of each word
        title_part = ' '.join(word.capitalize() for word in title_part.split())

        # Construct the final name
        if stem_type:
            cleaned_name = f"{title_part} ({stem_type}).mp3"
        else:
            cleaned_name = f"{title_part}.mp3"

        return cleaned_name

    # If none of the patterns matched, return the original filename
    return filename


def process_directory(directory_path, recursive=False, dry_run=False):
    directory = Path(directory_path)

    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist.")
        input("\nPress Enter to exit...")
        return

    # Get all MP3 files in the directory
    if recursive:
        files = list(directory.glob('**/*.mp3'))
    else:
        files = list(directory.glob('*.mp3'))

    if not files:
        print(f"No MP3 files found.")
        input("\nPress Enter to exit...")
        return

    renamed_count = 0

    for file_path in files:
        original_name = file_path.name
        cleaned_name = clean_filename(original_name)
        cleaned_name = re.sub(r'[<>:"/\\|?*]', '_', cleaned_name)

        if original_name != cleaned_name:
            new_path = file_path.parent / cleaned_name

            if dry_run:
                print(f"Would rename: '{original_name}' -> '{cleaned_name}'")
            else:
                try:
                    # Avoid overwriting existing files with the same cleaned name
                    if new_path.exists():
                         print(f"Skipping rename: Target file '{cleaned_name}' already exists.")
                         continue
                    file_path.rename(new_path)
                    print(f"Renamed: '{original_name}' -> '{cleaned_name}'")
                    renamed_count += 1
                except Exception as e:
                    print(f"Error renaming '{original_name}' to '{cleaned_name}': {e}")

    if dry_run:
        print(f"\nDry run completed. {len(files)} files processed.")
    else:
        print(f"\nRenamed {renamed_count} of {len(files)} files.")

    input("\nPress Enter to exit...")


def main():
    parser = argparse.ArgumentParser(description="Clean up mvsep.com audio filenames.")
    parser.add_argument("directory", nargs="?", default=".",
                        help="Directory containing audio files (default: current directory)")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="Process subdirectories recursively")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be renamed without actually renaming files")

    args = parser.parse_args()

    process_directory(args.directory, args.recursive, args.dry_run)


if __name__ == "__main__":
    main()
