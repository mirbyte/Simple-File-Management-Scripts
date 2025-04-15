import os
import re
import sys


def replace_multiple_pluses(filename):
    # Split the file name into base name and extension
    base_name, extension = os.path.splitext(filename)
    # Replace one or more '+' characters with a single space
    new_base_name = re.sub(r'\++', ' ', base_name)
    new_base_name = new_base_name.strip()

    # Handle cases where the name becomes empty after stripping (e.g., "+++.txt")
    if not new_base_name:
        print(f"Warning: Renaming '{filename}' would result in an empty name. Skipping.")
        return filename
    return new_base_name + extension

def main():
    try:
        current_dir = os.getcwd()
        print(f"Scanning directory: {current_dir}")
    except OSError as e:
        print(f"Error accessing current directory: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    files_processed = 0
    files_renamed = 0
    files_skipped = 0
    errors_encountered = 0


    for filename in os.listdir(current_dir):
        old_file_path = os.path.join(current_dir, filename)
        # Check if it's a file
        if os.path.isfile(old_file_path):
            files_processed += 1

            # check for .py files to prevent self renaming
            if filename.lower().endswith('.py'):
                print(f"Skipped: '{filename}' is a Python script.")
                files_skipped += 1
                continue

            new_filename = replace_multiple_pluses(filename)

            # Only proceed if the name would actually change
            if new_filename != filename:
                # Create the full path for the potential new filename
                new_file_path = os.path.join(current_dir, new_filename)

                # Check if a file with the new name already exists
                if os.path.exists(new_file_path):
                    print(f"Skipped: Target '{new_filename}' already exists (from '{filename}')")
                    files_skipped += 1
                else:
                    # Try to rename the file, catching potential OS errors
                    try:
                        os.rename(old_file_path, new_file_path)
                        print(f"Renamed: '{filename}' -> '{new_filename}'")
                        files_renamed += 1
                    except OSError as e:
                        print(f"ERROR renaming '{filename}': {e}")
                        errors_encountered += 1


    print("\n--- Summary ---")
    print(f"Files renamed: {files_renamed}")
    print(f"Files skipped (target exists, empty name, or python script): {files_skipped}")
    print(f"Errors encountered: {errors_encountered}")


if __name__ == "__main__":
    main()
    print("")
    input("\nPress Enter to exit...")
