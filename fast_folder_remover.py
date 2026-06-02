import os
import subprocess
import shutil
import tempfile
import sys
import time
import ctypes
import logging
import stat
from typing import Optional, List


MAX_RETRIES: int = 3
RETRY_DELAY: float = 1.0  # seconds
LOG_FILE_NAME: str = 'folder_remover.log'


def is_admin() -> bool:
    """Check if the script is running with administrator privileges on Windows."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except AttributeError:
        logging.warning("Could not determine admin status (ctypes/shell32 unavailable). Assuming not admin.")
        return False
    except Exception as e:
        logging.error(f"Error checking admin status: {e}")
        return False

def setup_logging() -> None:
    log_file_path = os.path.join(os.getcwd(), LOG_FILE_NAME)

    # 1. Configure the root logger to ONLY write to the file
    # By default, basicConfig will handle file routing without duplicating to stderr
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8')
        ]
    )

    # 2. Create a console handler that ONLY triggers for system errors/critical failures
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)  # Suppresses INFO and WARNING from the console
    
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # 3. Add the console handler to the root logger
    logging.getLogger().addHandler(console_handler)

def remove_readonly(func, path, excinfo) -> None:
    """Clear the read-only bit and retry the operation (used by shutil.rmtree)."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        logging.debug(f"Failed to clear read-only attribute for {path}: {e}")

def get_folder_path() -> Optional[str]:
    """Prompt user for folder path, validate it against blacklists, and handle exit."""
    # Define a safety blacklist of critical system paths
    forbidden_paths = {
        os.path.abspath(os.environ.get("SystemRoot", "C:\\Windows")),
        os.path.abspath(os.environ.get("ProgramFiles", "C:\\Program Files")),
        os.path.abspath(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")),
        os.path.abspath(os.path.expanduser("~")),  # Entire user profile directory
    }

    while True:
        print("\n" + "="*65)
        path_input = input("Enter the full path of the folder to delete (or 'exit' to quit): ").strip()

        if path_input.lower() == 'exit':
            logging.info("User entered 'exit'.")
            return None

        if len(path_input) > 1 and path_input.startswith('"') and path_input.endswith('"'):
            path_input = path_input[1:-1]
        elif len(path_input) > 1 and path_input.startswith("'") and path_input.endswith("'"):
            path_input = path_input[1:-1]

        try:
            abs_path = os.path.abspath(path_input)
            
            # Guardrail checks
            if abs_path in forbidden_paths or abs_path == os.path.abspath("/"):
                print(f"[!] Error: Deleting system, user profile, or root directories is strictly forbidden: {abs_path}")
                logging.warning(f"User blocked from deleting protected path: {abs_path}")
                continue
                
            if not os.path.exists(abs_path):
                print(f"[!] Error: Path does not exist: {abs_path}")
                logging.warning(f"User provided non-existent path: {abs_path} (Original input: '{path_input}')")
                continue
            if not os.path.isdir(abs_path):
                print(f"[!] Error: Path is not a directory: {abs_path}")
                logging.warning(f"User provided path that is not a directory: {abs_path} (Original input: '{path_input}')")
                continue
                
            logging.info(f"Validated folder path: {abs_path}")
            return abs_path
        except OSError as e:
            print(f"[!] Invalid path or OS error: {e}")
            logging.error(f"Error processing path '{path_input}': {e}")
        except Exception as e:
            print(f"[!] An unexpected error occurred: {e}")
            logging.error(f"Unexpected error validating path '{path_input}': {e}")

def confirm_deletion(folder_path: str) -> bool:
    """Ask for user confirmation before proceeding with deletion."""
    print("\n" + "!"*50)
    print(f"WARNING: You are about to PERMANENTLY delete:")
    print(f"  {folder_path}")
    print("And ALL its contents (files and subfolders)!")
    print("This action cannot be undone.")
    print("!"*50 + "\n")

    while True:
        response = input("Are you absolutely sure? (yes/no): ").strip().lower()
        if response in ('yes', 'y'):
            logging.info(f"User confirmed deletion for: {folder_path}")
            return True
        elif response in ('no', 'n'):
            logging.info("User cancelled deletion during confirmation.")
            return False
        else:
            print("Please enter 'yes' or 'no'.")

def fast_delete(target_folder: str) -> bool:
    """Attempt to delete the specified folder quickly using robocopy and fallback methods."""
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting to delete folder: {target_folder}")

    try:
        with tempfile.TemporaryDirectory() as empty_folder:
            logger.info(f"Using temporary empty folder for robocopy: {empty_folder}")

            # --- Robocopy Phase ---
            # Removed /LOG:NUL because capture_output handles it natively.
            # Added /MT:16 flag for multi-threaded file adjustments.
            robocopy_cmd: List[str] = [
                'robocopy',
                empty_folder,    
                target_folder,   
                '/MIR',          
                '/NFL',          
                '/NDL',          
                '/NJH',          
                '/NJS',          
                '/NP',           
                '/R:1',          
                '/W:1',          
                '/MT:16'         
            ]

            logger.info(f"Running robocopy command: {' '.join(robocopy_cmd)}")
            try:
                process = subprocess.run(robocopy_cmd, check=False, capture_output=True, text=True, encoding='utf-8', errors='ignore')

                if process.returncode >= 8:
                    logger.warning(f"Robocopy potentially failed (return code {process.returncode}). Output: STDOUT='{process.stdout.strip()}' STDERR='{process.stderr.strip()}'")
                else:
                    logger.info(f"Robocopy completed (return code {process.returncode}). Proceeding with final folder removal.")

            except FileNotFoundError:
                logger.error("Robocopy command not found. Ensure it's in your system's PATH. Falling back to shutil.rmtree.")
            except Exception as e:
                logger.error(f"Error running robocopy: {e}. Falling back to shutil.rmtree.")

            # --- shutil.rmtree Phase ---
            for attempt in range(1, MAX_RETRIES + 1):
                logger.info(f"Attempt {attempt}/{MAX_RETRIES}: Removing folder structure with shutil.rmtree: {target_folder}")
                try:
                    if not os.path.exists(target_folder):
                        logger.info("Folder no longer exists (possibly removed by robocopy). Deletion successful.")
                        return True 

                    # Added on_exc error callback handler to automatically clear read-only attributes
                    shutil.rmtree(target_folder, on_exc=remove_readonly)
                    
                    if not os.path.exists(target_folder):
                        logger.info("Folder successfully deleted after shutil.rmtree.")
                        return True
                    else:
                        logger.warning("Folder still exists immediately after shutil.rmtree reported success. Retrying...")
                        time.sleep(RETRY_DELAY)

                except PermissionError as e:
                    logger.warning(f"shutil.rmtree Attempt {attempt} failed (PermissionError): {e}")
                except OSError as e:
                    logger.warning(f"shutil.rmtree Attempt {attempt} failed (OSError): {e}")
                except Exception as e:
                    logger.warning(f"shutil.rmtree Attempt {attempt} failed (Unexpected Error): {e}")

                if attempt < MAX_RETRIES:
                    logger.info(f"Waiting {RETRY_DELAY}s before next attempt.")
                    time.sleep(RETRY_DELAY)

            # --- 'rd' Command Phase (Last Resort) ---
            logger.warning(f"shutil.rmtree failed after {MAX_RETRIES} attempts. Trying 'rd /s /q' as a final resort...")
            try:
                rd_cmd = f'rd /s /q "{target_folder}"'
                logger.info(f"Running final attempt command: {rd_cmd}")
                rd_process = subprocess.run(rd_cmd, check=True, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')

                if not os.path.exists(target_folder):
                    logger.info("Final deletion attempt with 'rd' succeeded.")
                    return True
                else:
                    logger.error(f"Folder still exists after 'rd' command. Deletion failed. 'rd' Output: STDOUT='{rd_process.stdout.strip()}' STDERR='{rd_process.stderr.strip()}'")
                    return False
            except subprocess.CalledProcessError as e:
                logger.error(f"Final deletion attempt with 'rd' failed. Return code: {e.returncode}, Output: STDOUT='{e.stdout.strip()}' STDERR='{e.stderr.strip()}'")
                return False
            except Exception as e:
                logger.error(f"Unexpected error during final 'rd' deletion attempt: {e}")
                return False

    except Exception as e:
        logger.error(f"Failed during temporary directory handling or outer try block: {e}")
        return False

    logger.error(f"Failed to delete folder '{target_folder}' after all attempts and phases.")
    return False


def main() -> int:
    """Main function to orchestrate the folder deletion process."""
    setup_logging() 
    logger = logging.getLogger(__name__) 

    print("=== Fast Folder Removal Tool ===")
    print("This tool PERMANENTLY deletes folders and all their contents!")
    print("Use with extreme caution. There is NO UNDO.")

    if not is_admin():
        warning_message = "Not running as administrator. Deletion might fail for some protected folders or files."
        print(f"\nWarning: {warning_message}")
        logger.warning(warning_message) 
    else:
        logger.info("Script is running with administrator privileges.") 

    target_folder = get_folder_path()
    if not target_folder:
        print("Operation cancelled by user during path input.")
        return 0

    if not confirm_deletion(target_folder):
        print("Deletion cancelled by user during confirmation.")
        return 0

    logger.info(f"Starting deletion process for: {target_folder}") 
    start_time = time.time()
    success = fast_delete(target_folder)
    end_time = time.time()
    duration = end_time - start_time

    if success:
        success_message = f"Successfully deleted: {target_folder} (Duration: {duration:.2f} seconds)"
        print(f"\n[✓] {success_message}")
        logger.info(success_message) 
        input("\nPress Enter to exit...")
        return 0
    else:
        fail_message = f"Failed to delete: {target_folder}"
        log_file_location = os.path.join(os.getcwd(), LOG_FILE_NAME)
        print(f"\n[X] {fail_message}")
        print(f"    Check the log file for details: {log_file_location}")
        logger.error(f"{fail_message}. Please review log file '{log_file_location}' for detailed errors.")
        return 1 

if __name__ == "__main__":
    sys.exit(main())