import os
import time
from colorama import init, Fore, Style

init()

# github/mirbyte

def print_log(message, status="INFO"):
    if status == "INFO":
        return

    timestamp = time.strftime("%H:%M:%S")
    status_colors = {
        "INFO": Fore.BLUE,
        "SUCCESS": Fore.GREEN,
        "ERROR": Fore.RED,
        "WARNING": Fore.YELLOW
    }
    print(f"{status_colors[status]}[{status}][{timestamp}] {message}{Style.RESET_ALL}")

def rename_files():
    print("Choose what to remove:")
    print("1. Prefix (from start of filename)")
    print("2. Suffix (after filename)")
    choice = input("Enter 1 or 2: ").strip()

    if choice not in ['1', '2']:
        print_log("Invalid choice. Exiting.", "ERROR")
        input("\nPress Enter to exit...")
        return

    # Ask user for string to remove
    prompt = "Enter the prefix to remove (e.g., 'demo - '):" if choice == '1' else \
             "Enter the suffix to remove (e.g., '- Copy' or a single space):"
    print(f"\n{prompt}")

    # Use rstrip() for prefixes to keep leading spaces, strip() for suffixes but handle single space case
    if choice == '1':
        remove_str = input("> ").rstrip()
    else:
        raw_input = input("> ")
        # Check if input is a single space
        if raw_input == " ":
            remove_str = " "
        else:
            remove_str = raw_input.strip()

    if not remove_str:
        print_log("No string provided. Exiting.", "ERROR")
        input("\nPress Enter to exit...")
        return

    # Ask user for case sensitivity
    print("\nShould the removal be case-sensitive? (y/n)")
    case_sensitive = input("> ").strip().lower() == 'y'

    # Ask user for dry-run mode
    print("\nDo you want to do a dry-run first? (y/n)")
    dry_run = input("> ").strip().lower() == 'y'

    files_processed = 0
    files_renamed = 0
    duplicates_found = 0
    skipped_non_files = 0

    print_log(f"Starting {'dry-run ' if dry_run else ''}file rename process...")

    # If not dry run, ask for confirmation
    if not dry_run:
        print_log("About to rename files. This cannot be undone easily.", "WARNING")
        confirm = input("Are you sure you want to proceed? (y/n): ").strip().lower()
        if confirm != 'y':
            print_log("Operation cancelled by user.", "INFO")
            input("\nPress Enter to exit...")
            return

    for filename in os.listdir():
        # Skip directories and other non-file items
        if not os.path.isfile(filename):
            skipped_non_files += 1
            continue

        target = None
        if choice == '1':
            # Prefix removal with case sensitivity check
            starts_with = filename.startswith(remove_str) if case_sensitive else \
                         filename.lower().startswith(remove_str.lower())
            if starts_with:
                target = filename[len(remove_str):]
                # Ensure filename doesn't start with space after prefix removal
                if target.startswith(' '):
                    # This INFO message will not be printed
                    print_log(f"Fixing leading space in: {target}", "INFO")
                    target = target.lstrip()
        elif choice == '2':
            # Suffix removal with case sensitivity check
            name, ext = os.path.splitext(filename)
            ends_with = name.endswith(remove_str) if case_sensitive else \
                       name.lower().endswith(remove_str.lower())
            if ends_with:
                target = name[:-len(remove_str)] + ext

        # Ensure no space is left between filename and extension
        if target:
            name, ext = os.path.splitext(target)
            if name.endswith(' '):
                print_log(f"Fixing space before extension in: {target}", "INFO")
                target = name.rstrip() + ext

            files_processed += 1
            if os.path.exists(target):
                print_log(f"Skipping {filename} → {target} (target exists)", "ERROR")
                duplicates_found += 1
            else:
                try:
                    if not dry_run:
                        os.rename(filename, target)
                    print_log(f"{'Would rename' if dry_run else 'Renamed'}: {filename} → {target}",
                              "SUCCESS" if not dry_run else "INFO")
                    files_renamed += 1
                except OSError as e:
                    print_log(f"Failed to rename {filename}: {e}", "ERROR")

    print_log(f"Process complete. Processed {files_processed} files, renamed {files_renamed} files, found {duplicates_found} duplicates.")
    if skipped_non_files > 0:
        print_log(f"Skipped {skipped_non_files} non-file items (directories, etc.)", "INFO")
    input("\nPress Enter to exit...")

if __name__ == '__main__':
    try:
        rename_files()
    except Exception as e:
        print_log(f"Unexpected error: {e}", "ERROR")
        input("\nPress Enter to exit...")