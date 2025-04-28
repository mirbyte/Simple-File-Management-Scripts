import os
import re
import argparse
from pathlib import Path


def clean_filename(filename):
    # Clean up audio filenames by removing unwanted patterns
    # Handles both formats with and without MVSEP prefix
    # Properly converts contractions (don-t -> don't)
    
    # Patterns with MVSEP prefix (original format)
    patterns = [
        # New format with MVSEP prefix: ...melroformer_mt_4_vocals.mp3
        r'^\d{14}-[a-f0-9]{10}-(.*?)\._(?:.*?_)?(?:mdx\w+|melroformer)_mt_\d+_([a-zA-Z0-9]{1,7})\.mp3$',
        # Original format with stem: ...vocals_[mvsep.com].mp3
        r'^\d{14}-[a-f0-9]{10}-(.*?)_(?:.*?_)?(?:mdx\w+_mt_\d+_)?([a-zA-Z0-9]{1,7})_\[mvsep\.com\]\.mp3$',
        # Original format without stem: ..._[mvsep.com].mp3
        r'^\d{14}-[a-f0-9]{10}-(.*?)_(?:.*?_)?(?:mdx\w+_mt_\d+_)?\[mvsep\.com\]\.mp3$',
        # Simple format: ...[mvsep.com].mp3
        r'^\d{14}-[a-f0-9]{10}-(.*?)\[mvsep\.com\]\.mp3$',
        
        # Patterns WITHOUT MVSEP prefix (new simpler format)
        # New format without prefix: ...melroformer_mt_4_vocals.mp3
        r'^(.*?)\._(?:.*?_)?(?:mdx\w+|melroformer)_mt_\d+_([a-zA-Z0-9]{1,7})\.mp3$',
        # Stem format without prefix: ..._vocals.mp3
        r'^(.*?)_([a-zA-Z0-9]{1,7})\.mp3$'
    ]

    for pattern in patterns:
        match = re.match(pattern, filename)
        if match:
            title_part = match.group(1).rstrip('._ ')
            stem_type = match.group(2) if len(match.groups()) > 1 else None
            
            # First fix contractions (don-t -> don't)
            title_part = re.sub(r'(\w+)-([tT])\b', r"\1'\2", title_part)
            # Then replace remaining hyphens with spaces
            title_part = title_part.replace('-', ' ')
            # Capitalize the first letter of each word
            title_part = ' '.join(word.capitalize() for word in title_part.split())
            
            return f"{title_part} ({stem_type}).mp3" if stem_type else f"{title_part}.mp3"
    
    return filename


def process_directory(directory_path, recursive=False):
    directory = Path(directory_path)

    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist.")
        input("\nPress Enter to exit...")
        return

    files = list(directory.glob('**/*.mp3')) if recursive else list(directory.glob('*.mp3'))
    
    if not files:
        print("No MP3 files found.")
        input("\nPress Enter to exit...")
        return

    renamed_count = 0

    for file_path in files:
        original_name = file_path.name
        cleaned_name = clean_filename(original_name)
        cleaned_name = re.sub(r'[<>:"/\\|?*]', '_', cleaned_name)

        if original_name != cleaned_name:
            new_path = file_path.parent / cleaned_name
            try:
                if new_path.exists():
                    print(f"Skipping: '{cleaned_name}' already exists")
                    continue
                file_path.rename(new_path)
                print(f"Renamed: '{original_name}' -> '{cleaned_name}'")
                renamed_count += 1
            except Exception as e:
                print(f"Error renaming '{original_name}': {e}")

    print(f"\nRenamed {renamed_count} of {len(files)} files.")
    input("\nPress Enter to exit...")


def main():
    parser = argparse.ArgumentParser(description="Clean up mvsep.com audio filenames.")
    parser.add_argument("directory", nargs="?", default=".",
                      help="Directory containing audio files (default: current directory)")
    parser.add_argument("-r", "--recursive", action="store_true",
                      help="Process subdirectories recursively")
    
    args = parser.parse_args()
    try:
        process_directory(args.directory, args.recursive)
    except Exception as e:
        print(f"An error occurred: {e}")
        input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
