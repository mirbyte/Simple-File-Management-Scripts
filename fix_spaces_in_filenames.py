import os
import re

def fix_misplaced_spaces(filename):
    """
    Fixes misplaced spaces in a filename:
    - Removes leading/trailing spaces.
    - Removes spaces before the file extension.
    - Replaces multiple spaces with a single space.
    """
    # Remove leading/trailing spaces
    filename = filename.strip()

    # Replace multiple spaces with one
    filename = re.sub(r'\s+', ' ', filename)

    # Split name and extension
    name, ext = os.path.splitext(filename)

    # Remove trailing spaces from the name part
    name = name.rstrip()

    # Rejoin name and extension
    new_name = name + ext

    return new_name

def rename_files_in_current_directory():
    files_renamed_count = 0
    errors_encountered = []

    print("Starting file rename process...")

    # Get the directory where the script is running
    current_directory = os.getcwd()
    script_name = os.path.basename(__file__) # Get the name of this script

    try:
        # List all items in the directory
        for item_name in os.listdir(current_directory):
            # Create the full path to the item
            item_path = os.path.join(current_directory, item_name)

            # Check if it's a file and not the script itself
            if os.path.isfile(item_path) and item_name != script_name:
                # Get the potentially corrected name
                corrected_name = fix_misplaced_spaces(item_name)

                # Rename only if the name actually changes
                if item_name != corrected_name:
                    try:
                        # Create the full path for the new name
                        new_item_path = os.path.join(current_directory, corrected_name)
                        # Perform the rename
                        os.rename(item_path, new_item_path)
                        files_renamed_count += 1
                    except OSError as e:
                        # Store errors to report later
                        errors_encountered.append(f"Could not rename '{item_name}': {e}")
                    except Exception as e: # Catch other potential errors
                         errors_encountered.append(f"Unexpected error renaming '{item_name}': {e}")

    except FileNotFoundError:
        print(f"ERROR: Directory not found: {current_directory}")
        errors_encountered.append(f"Directory not found: {current_directory}")
    except PermissionError:
         print(f"ERROR: Permission denied to access directory: {current_directory}")
         errors_encountered.append(f"Permission denied for directory: {current_directory}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        errors_encountered.append(f"General error: {e}")


    # --- Summary ---
    print(f"\n--- Process Summary ---")
    print(f"Renamed {files_renamed_count} files.")

    if errors_encountered:
        print(f"\nEncountered {len(errors_encountered)} error(s):")
        for error_msg in errors_encountered:
            print(f"- {error_msg}")
    else:
        print("No errors encountered.")

    print("")
    input("\nPress Enter to exit...")


if __name__ == '__main__':
    rename_files_in_current_directory()