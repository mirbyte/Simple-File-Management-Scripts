import os
import zipfile
import rarfile
import shutil
import logging
import tempfile
import time
import sys
import argparse
from pathlib import Path
from tqdm import tqdm


LOG_FILENAME = "archive_extraction.log"
PROGRESS_THRESHOLD_MB = 10 # Show progress bar for archives larger than 10 MB
RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 2

# --- Logging Setup ---
logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    # Use FileHandler to prevent issues if script is run multiple times quickly
    # handlers=[logging.FileHandler(LOG_FILENAME, mode='a')] # Optional: Explicit handler
)


def get_archive_opener(archive_path: Path):
    """Returns the appropriate archive opener based on file extension."""
    if archive_path.suffix.lower() == '.zip':
        return zipfile.ZipFile
    elif archive_path.suffix.lower() == '.rar':
        # NOTE: rarfile requires the 'unrar' executable or library.
        # On Windows, make sure unrar.exe or UnRAR.dll is in your PATH
        # or the same directory as the script.
        try:
            # Test if rarfile is functional (basic check)
            rarfile.is_rarfile(archive_path)
            return rarfile.RarFile
        except rarfile.NeedFirstVolume:
             logging.warning(f"Skipping multi-volume RAR (requires first volume): {archive_path.name}")
             return None
        except Exception as e:
            logging.error(f"rarfile library error for {archive_path.name}. Is unrar tool installed and accessible? Error: {e}")
            return None
    else:
        return None

def try_passwords(archive_path: Path, passwords: list[str] | None) -> str | None:
    """Tries multiple passwords on an archive, returns the working password or None."""
    if not passwords:
        return None

    ArchiveOpener = get_archive_opener(archive_path)
    if not ArchiveOpener:
        return None # Unsupported format

    for password in passwords:
        try:
            with ArchiveOpener(archive_path, 'r') as archive_ref:
                pwd_bytes = None
                if isinstance(archive_ref, zipfile.ZipFile):
                    pwd_bytes = password.encode()
                    archive_ref.setpassword(pwd_bytes)
                elif isinstance(archive_ref, rarfile.RarFile):
                    archive_ref.setpassword(password) # rarfile takes string

                # Test password by trying to access the first file's info or read it
                file_list = archive_ref.namelist()
                if file_list:
                    # Use testzip/testrar if available and reliable for password check
                    if hasattr(archive_ref, 'testzip'): # zipfile
                         archive_ref.testzip() # Will raise RuntimeError on bad password
                         logging.info(f"Password '{password}' accepted for {archive_path.name} via testzip.")
                         return password
                    elif hasattr(archive_ref, 'testrar'): # rarfile
                         # testrar might not reliably check password, try reading instead
                         try:
                              archive_ref.read(file_list[0])
                              logging.info(f"Password '{password}' accepted for {archive_path.name} via read test.")
                              return password
                         except rarfile.BadRarFile: # More specific for password errors in rarfile read
                              continue # Try next password
                         except Exception as read_err: # Catch other read errors
                              logging.debug(f"Read test failed for {archive_path.name} with password '{password}': {read_err}")
                              continue
                    else: # Fallback: try reading first file header/data
                         archive_ref.read(file_list[0])
                         logging.info(f"Password '{password}' accepted for {archive_path.name} via read test.")
                         return password
                else:
                    # Archive is empty, password might be correct but nothing to test
                    logging.warning(f"Archive {archive_path.name} is empty, assuming password '{password}' is correct.")
                    return password # Assume correct if empty

        except (RuntimeError, zipfile.BadZipFile) as zip_err: # Common zip password errors
            logging.debug(f"Password '{password}' failed for ZIP {archive_path.name}: {zip_err}")
            continue # Try next password
        except rarfile.BadRarFile as rar_err: # Common rar password/corruption error
             logging.debug(f"Password '{password}' failed for RAR {archive_path.name}: {rar_err}")
             continue # Try next password
        except rarfile.PasswordRequired:
             logging.debug(f"Password '{password}' failed for RAR {archive_path.name}: Password required but attempt failed.")
             continue # Try next password
        except Exception as e:
            logging.warning(f"Unexpected error testing password '{password}' on {archive_path.name}: {e}")
            continue # Try next password

    logging.warning(f"No working password found for {archive_path.name} from the provided list.")
    return None

def is_valid_archive(archive_path: Path, password: str | None = None) -> bool:
    """Checks if an archive file is valid (structure/CRC), optionally with a password."""
    ArchiveOpener = get_archive_opener(archive_path)
    if not ArchiveOpener:
        logging.error(f"Unsupported archive format: {archive_path.name}")
        return False

    try:
        with ArchiveOpener(archive_path, 'r') as archive_ref:
            pwd_bytes = None
            if password:
                 if isinstance(archive_ref, zipfile.ZipFile):
                      pwd_bytes = password.encode()
                      archive_ref.setpassword(pwd_bytes)
                 elif isinstance(archive_ref, rarfile.RarFile):
                      archive_ref.setpassword(password)

            # Use testzip/testrar for integrity check
            if hasattr(archive_ref, 'testzip'):
                result = archive_ref.testzip()
                if result is not None:
                    logging.error(f"Archive {archive_path.name} failed integrity check (testzip) on file: {result}")
                    return False
                return True
            elif hasattr(archive_ref, 'testrar'):
                 # rarfile's testrar() might raise exceptions on error rather than return value
                 try:
                      archive_ref.testrar()
                      return True
                 except rarfile.BadRarFile as e:
                      logging.error(f"Archive {archive_path.name} failed integrity check (testrar): {e}")
                      return False
            else:
                 # Should not happen if get_archive_opener worked
                 logging.error(f"Cannot determine test method for {archive_path.name}")
                 return False

    except (zipfile.BadZipFile, rarfile.BadRarFile, rarfile.NotRarFile, rarfile.PasswordRequired) as e:
        # PasswordRequired here means it needs a password but none (or wrong one) was provided for validation
        if isinstance(e, rarfile.PasswordRequired):
             logging.warning(f"Validation check indicates archive {archive_path.name} is password protected.")
             # We return True here, assuming password will be handled later.
             # If a password *was* provided and failed, it's an error.
             return not password # True if no password given, False if password was given and failed
        logging.error(f"Invalid or corrupted archive file {archive_path.name}: {e}")
        return False
    except FileNotFoundError:
         logging.error(f"Archive file not found during validation: {archive_path}")
         return False
    except Exception as e:
        logging.error(f"Unexpected error validating {archive_path.name}: {e}")
        return False

def verify_extracted_files(extract_to_path: Path, archive_ref) -> bool:
    """Verifies extracted files against archive contents (existence and size)."""
    try:
        logging.info(f"Verifying extracted files in {extract_to_path}...")
        all_verified = True
        for item_info in archive_ref.infolist():
            # Adjust path separators for consistency if needed (usually pathlib handles this)
            relative_path_str = item_info.filename.replace('\\', '/')
            extracted_path = extract_to_path / relative_path_str

            if not extracted_path.exists():
                logging.error(f"Verification failed: Missing file/dir '{relative_path_str}'")
                all_verified = False
                continue # Check others

            # rarfile infolist might not have is_dir(), zipfile does
            is_dir = getattr(item_info, 'is_dir', lambda: extracted_path.is_dir())()

            if not is_dir:
                try:
                    extracted_size = extracted_path.stat().st_size
                    archive_size = item_info.file_size
                    if extracted_size != archive_size:
                        logging.error(f"Verification failed: Size mismatch for '{relative_path_str}' (Expected: {archive_size}, Got: {extracted_size})")
                        all_verified = False
                except FileNotFoundError:
                     # Should have been caught by exists() check, but good to be safe
                     logging.error(f"Verification failed: File disappeared '{relative_path_str}'")
                     all_verified = False
                except Exception as stat_err:
                     logging.error(f"Verification error getting size for '{relative_path_str}': {stat_err}")
                     all_verified = False

        if all_verified:
             logging.info(f"Verification successful for files from {getattr(archive_ref, 'filename', 'archive')}")
        else:
             logging.error(f"Verification failed for one or more files from {getattr(archive_ref, 'filename', 'archive')}")
        return all_verified
    except Exception as e:
        logging.error(f"Unexpected error during verification process: {e}")
        return False


def move_files_with_collision_handling(temp_dir_path: Path, extract_to_path: Path, collision_strategy: str):
    """Moves files from temp dir to destination, handling collisions."""
    logging.info(f"Moving extracted files from {temp_dir_path} to {extract_to_path}...")
    all_moved = True
    try:
        # Walk the temporary directory
        for src_path in temp_dir_path.rglob('*'): # rglob gets all files/dirs recursively
            rel_path = src_path.relative_to(temp_dir_path)
            dest_path = extract_to_path / rel_path

            # Ensure parent directory exists in destination
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Handle potential collisions at the destination
            if dest_path.exists():
                if dest_path.is_dir() and src_path.is_dir():
                    # If both are directories, we don't need to move the source dir itself,
                    # its contents will be handled by rglob.
                    continue
                elif collision_strategy == 'skip':
                    logging.warning(f"Collision: '{rel_path}' already exists in destination. Skipping.")
                    continue # Skip moving this item
                elif collision_strategy == 'overwrite':
                    logging.warning(f"Collision: '{rel_path}' already exists. Overwriting.")
                    try:
                        if dest_path.is_dir():
                            shutil.rmtree(dest_path)
                        else:
                            dest_path.unlink() # Remove file
                    except Exception as rm_err:
                        logging.error(f"Failed to remove existing item for overwrite '{dest_path}': {rm_err}")
                        all_moved = False
                        continue # Skip this item if removal failed
                elif collision_strategy == 'rename':
                    counter = 1
                    # Use stem and suffix for renaming
                    base_name = dest_path.stem
                    extension = dest_path.suffix
                    # Handle potential multiple dots in filename correctly
                    if dest_path.name.count('.') > 1:
                         parts = dest_path.name.split('.')
                         base_name = '.'.join(parts[:-1])
                         extension = '.' + parts[-1] if len(parts) > 1 else ''


                    while True:
                        new_name = f"{base_name}_{counter}{extension}"
                        new_dest_path = dest_path.with_name(new_name)
                        if not new_dest_path.exists():
                            logging.warning(f"Collision: '{rel_path}' already exists. Renaming to '{new_name}'.")
                            dest_path = new_dest_path
                            break
                        counter += 1
                        if counter > 999: # Safety break
                             logging.error(f"Could not find unique name for '{rel_path}' after 999 attempts. Skipping.")
                             all_moved = False
                             break # Break inner while
                    if not all_moved and counter > 999: continue # Continue outer loop if rename failed

            # --- Perform the move ---
            try:
                shutil.move(str(src_path), str(dest_path)) # shutil.move needs strings
            except Exception as move_err:
                logging.error(f"Failed to move '{rel_path}' to '{dest_path}': {move_err}")
                all_moved = False
                # Decide if one failure should stop everything (could return False here)

        logging.info(f"Finished moving files to {extract_to_path}.")
        return all_moved

    except Exception as e:
        logging.error(f"Error during file moving process: {e}")
        return False


def extract_archive(
    archive_path: Path,
    extract_to_path: Path,
    password: str | None = None,
    collision_strategy: str = 'skip'
) -> bool:
    """Extracts an archive to a temporary location, then moves files handling collisions."""
    ArchiveOpener = get_archive_opener(archive_path)
    if not ArchiveOpener:
        logging.warning(f"Skipping unsupported file: {archive_path.name}")
        return False

    # Check disk space before proceeding
    try:
        total_size = sum(m.file_size for m in ArchiveOpener(archive_path, 'r').infolist()
                        if hasattr(m, 'file_size') and m.file_size is not None)
        # Add 10% buffer to required space
        required_size = int(total_size * 1.1)
        disk_usage = shutil.disk_usage(extract_to_path)
        if required_size > disk_usage.free:
            logging.error(f"Insufficient disk space to extract {archive_path.name}. Required: {required_size} (with 10% buffer), Available: {disk_usage.free}")
            return False
    except Exception as e:
        logging.warning(f"Could not verify disk space: {e}. Proceeding anyway.")

    # Use a context manager for the temporary directory
    with tempfile.TemporaryDirectory(prefix=f"{archive_path.stem}_") as temp_dir:
        temp_dir_path = Path(temp_dir)
        logging.info(f"Created temporary directory: {temp_dir_path}")

        try:
            with ArchiveOpener(archive_path, 'r') as archive_ref:
                # Set password if provided
                if password:
                    try:
                        if isinstance(archive_ref, zipfile.ZipFile):
                            archive_ref.setpassword(password.encode())
                        elif isinstance(archive_ref, rarfile.RarFile):
                            archive_ref.setpassword(password)
                    except Exception as pwd_err:
                         # Should have been caught by try_passwords, but belt-and-suspenders
                         logging.error(f"Error setting password during extraction for {archive_path.name}: {pwd_err}")
                         return False # Password error during actual extraction

                # --- Perform extraction to temporary directory ---
                # print(f"Extracting {archive_path.name}...")
                members = archive_ref.infolist()
                total_size = sum(m.file_size for m in members if hasattr(m, 'file_size') and m.file_size is not None) # Sum file sizes

                if total_size > (PROGRESS_THRESHOLD_MB * 1024 * 1024):
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Extracting {archive_path.name}") as pbar:
                        for member in members:
                            try:
                                archive_ref.extract(member, path=str(temp_dir_path))
                                pbar.update(member.file_size if hasattr(member, 'file_size') and member.file_size is not None else 0)
                            except Exception as extract_err:
                                 logging.error(f"Error extracting member '{getattr(member, 'filename', 'unknown')}' from {archive_path.name}: {extract_err}")
                                 # Decide whether to continue or fail the whole archive
                                 # return False # Option: Fail on first error
                else:
                    try:
                        archive_ref.extractall(path=str(temp_dir_path))
                    except Exception as extract_err:
                         logging.error(f"Error during extractall for {archive_path.name}: {extract_err}")
                         return False # Fail if extractall fails

                logging.info(f"Successfully extracted {archive_path.name} to temporary directory.")

                # --- Move files from temp to final destination with collision handling ---
                if not move_files_with_collision_handling(temp_dir_path, extract_to_path, collision_strategy):
                     logging.error(f"Failed to move one or more files for {archive_path.name}. Check logs.")
                     # Decide if move failure means overall failure
                     # return False # Option: Fail if move fails

                # --- Final Verification Step ---
                # Re-open archive for verification if needed (or pass archive_ref if context allows)
                # Note: Re-opening ensures verification happens on the final state
                with ArchiveOpener(archive_path, 'r') as verify_ref:
                     if password:
                          if isinstance(verify_ref, zipfile.ZipFile):
                               verify_ref.setpassword(password.encode())
                          elif isinstance(verify_ref, rarfile.RarFile):
                               verify_ref.setpassword(password)

                     if not verify_extracted_files(extract_to_path, verify_ref):
                         logging.error(f"Post-extraction verification failed for {archive_path.name}.")
                         # Consider what to do if verification fails (e.g., clean up extract_to_path?)
                         return False

            # If we reach here, extraction, move, and verification were successful
            logging.info(f"Successfully extracted, moved, and verified: {archive_path.name} -> {extract_to_path}")
            return True

        except (zipfile.BadZipFile, rarfile.BadRarFile, rarfile.PasswordRequired) as e:
             # PasswordRequired here likely means the password check passed but extraction failed
             logging.error(f"Extraction failed for {archive_path.name}: {e}")
             return False
        except PermissionError as e:
             logging.error(f"Permission error during extraction/move for {archive_path.name}: {e}")
             return False
        except Exception as e:
            logging.error(f"Unexpected error extracting/processing {archive_path.name}: {e}")
            return False
        # No finally block needed for temp dir cleanup due to 'with tempfile.TemporaryDirectory'

# --- Main Processing Logic ---

def process_directory(
    directory: Path,
    passwords: list[str] | None = None,
    keep_original: bool = False,
    collision_strategy: str = 'skip'
):
    if not directory.is_dir():
        print(f"❌ Error: Directory not found or is not a directory: {directory}")
        logging.error(f"Target directory not found or invalid: {directory}")
        return

    print(f"Scanning directory: {directory}")
    found_archives = False
    processed_count = 0
    failed_count = 0

    for item_path in directory.iterdir():
        if item_path.is_file() and get_archive_opener(item_path): # Check if it's a supported archive file
            found_archives = True
            archive_path = item_path
            # Create destination folder based on archive name (without extension)
            extract_to_path = directory / archive_path.stem
            # Create the directory - collision handling for the *folder* itself isn't explicitly handled here
            # but extract_archive handles file collisions *within* it.
            extract_to_path.mkdir(exist_ok=True)

            logging.info(f"Processing archive: {archive_path.name}")

            working_password = None
            # Check if archive is valid without password first (quicker)
            # If it needs a password, is_valid_archive might return True (for RAR) or False (for ZIP needing pwd)
            # or raise PasswordRequired. Let's try extracting directly and handle password need there.

            # Try extracting without password first
            needs_password = False
            try:
                 # Attempt a quick check that might trigger password error early
                 with get_archive_opener(archive_path)('r') as quick_check_ref:
                      quick_check_ref.infolist() # Accessing infolist often requires password if needed
            except (RuntimeError, rarfile.PasswordRequired):
                 needs_password = True
                 logging.info(f"Archive {archive_path.name} requires a password.")
            except (zipfile.BadZipFile, rarfile.BadRarFile):
                 logging.error(f"Archive {archive_path.name} appears corrupt. Skipping.")
                 failed_count += 1
                 continue # Skip corrupt archive
            except Exception as quick_check_err:
                 logging.warning(f"Could not perform quick check on {archive_path.name}: {quick_check_err}")
                 # Proceed assuming it might work or might need password

            if needs_password:
                working_password = try_passwords(archive_path, passwords)
                if not working_password and passwords: # Only log if passwords were provided but none worked
                    logging.error(f"No working password found for {archive_path.name}. Skipping.")
                    failed_count += 1
                    continue # Skip password-protected archive if no password works
                elif not passwords:
                     logging.warning(f"Archive {archive_path.name} requires a password, but none were provided. Skipping.")
                     failed_count += 1
                     continue # Skip if password needed but none given

            # --- Retry Mechanism for Extraction ---
            success = False
            for attempt in range(RETRY_COUNT):
                try:
                    if extract_archive(archive_path, extract_to_path, working_password, collision_strategy):
                        logging.info(f"Successfully processed archive: {archive_path.name}")
                        success = True
                        processed_count += 1
                        # Delete original if requested and successful
                        if not keep_original:
                            try:
                                archive_path.unlink() # Use unlink for files
                                logging.info(f"Deleted original archive: {archive_path.name}")
                            except Exception as e:
                                logging.error(f"Failed to delete original archive {archive_path.name}: {e}")
                        break # Exit retry loop on success
                    else:
                        # extract_archive logs the specific error
                        logging.warning(f"Extraction attempt {attempt + 1} failed for {archive_path.name}.")
                        # No need to break here, let retry loop continue unless it was final attempt

                except PermissionError as e:
                    logging.warning(f"Permission error on attempt {attempt + 1} for {archive_path.name}: {e}")
                except Exception as e:
                    # Catch other unexpected errors during the call to extract_archive
                    logging.error(f"Unexpected error during extraction call (attempt {attempt + 1}) for {archive_path.name}: {e}")
                    # Break here as retrying might not help for unexpected errors
                    break

                # Wait before retrying if not the last attempt
                if attempt < RETRY_COUNT - 1:
                    logging.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                     logging.error(f"Failed to process {archive_path.name} after {RETRY_COUNT} attempts.")
                     failed_count += 1 # Count as failed only after all retries

            # Cleanup empty extraction folder if extraction ultimately failed? Optional.
            # if not success and extract_to_path.exists() and not any(extract_to_path.iterdir()):
            #     logging.info(f"Removing empty destination folder due to failed extraction: {extract_to_path}")
            #     try:
            #         extract_to_path.rmdir()
            #     except OSError as rmdir_err:
            #         logging.warning(f"Could not remove empty folder {extract_to_path}: {rmdir_err}")


    if not found_archives:
        print("ℹ️ No supported archive files (.zip, .rar) found in the directory.")
    else:
        print(f"✅ Processing complete. Processed: {processed_count}, Failed/Skipped: {failed_count}.")
        print(f"Check '{LOG_FILENAME}' for detailed logs.")


def wait_for_exit():
    """Waits for the user to press Enter before exiting."""
    input("\nPress Enter to exit...")

# --- Main Execution ---
if __name__ == "__main__":
    print("===== Archive Extractor Utility =====")
    print(f"Logging to: {LOG_FILENAME}\n")

    parser = argparse.ArgumentParser(
        description="Extract ZIP and RAR archives found in a specified directory.",
        epilog=f"Logs are saved to {LOG_FILENAME}. Requires 'unrar' tool for RAR files on Windows."
    )
    parser.add_argument(
        'directory',
        nargs='?',
        type=Path,
        default=Path.cwd(), # Use pathlib here too
        help='Directory containing archives to process (default: current directory)'
    )
    parser.add_argument(
        '-p', '--password',
        help='Single password for protected archives'
    )
    parser.add_argument(
        '--keep',
        action='store_true',
        help='Keep original archive files after successful extraction'
    )
    parser.add_argument(
        '--collision',
        choices=['skip', 'overwrite', 'rename'],
        default='skip',
        help='Strategy for handling existing files during extraction (default: skip)'
    )
    args = parser.parse_args()

    # --- Load Password ---
    passwords_to_try = []
    if args.password:
        passwords_to_try.append(args.password)

    # --- Execute Main Logic ---
    try:
        process_directory(
            args.directory,
            passwords=passwords_to_try if passwords_to_try else None,
            keep_original=args.keep,
            collision_strategy=args.collision
        )
    except Exception as e:
        logging.exception("Fatal error during script execution.") # Log traceback
        print(f"❌ An unexpected error occurred: {e}. Check '{LOG_FILENAME}' for details.")
    finally:
        # Keep console open only if run directly (e.g., double-clicked)
        # Check if stdin is interactive - won't pause if piped or run non-interactively
        if sys.stdin is not None and sys.stdin.isatty():
             wait_for_exit()
