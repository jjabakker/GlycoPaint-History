import os
import platform
import shutil
import logging
import colorlog
from tkinter.filedialog import askdirectory

# Set up color logging with black text
log_format = "%(log_color)s%(asctime)s - %(levelname)s - %(message)s"
colorlog.basicConfig(
    level=logging.INFO,
    format=log_format,
    log_colors={'DEBUG': 'black', 'INFO': 'black', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red'},
)


def copy_code_directory(source_dir, destination_dir):
    """
    Copy all Python files from the source directory to the destination directory, preserving the directory structure.

    :param source_dir: The source directory from which to copy files.
    :param destination_dir: The destination directory where files will be copied.
    """
    for root, _, files in os.walk(source_dir):
        copied = False
        for filename in files:
            # Skip hidden files and special files
            if filename.startswith(('.', '__')):
                continue

            # Check if the file is a Python file
            if filename.endswith('.py'):
                index = root.find("src/")
                destination = os.path.join(destination_dir, root[index:])  # Build destination path

                try:
                    if not os.path.exists(destination):
                        os.makedirs(destination)  # Create directory if it does not exist

                    shutil.copy(os.path.join(root, filename), destination)  # Copy file
                    copied = True
                    logging.info(f"Copied {filename} from {root} to {destination}")
                except Exception as e:
                    logging.error(f"Failed to copy {filename} from {root} to {destination}: {e}")

        if copied:
            logging.info(" ")


def copy_files():
    """
    Main function to handle file copying process.
    """
    if platform.system() != 'Darwin':
        logging.error("Unsupported operating system. This script is intended for macOS.")
        return

    # Ask user for the destination directory
    destination_dir = askdirectory(title='Specify destination directory', initialdir=os.path.expanduser('~'))
    if not destination_dir:
        logging.error("No directory selected.")
        return

    # Define source directories
    source_root             = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/Code/'
    fiji_source_root        = os.path.join(source_root, 'Paint-v8', 'src', 'Fiji')
    common_source_root      = os.path.join(source_root, 'Paint-v8', 'src', 'Common')
    automation_source_root  = os.path.join(source_root, 'Paint-v8', 'src', 'Automation')

    # Copy code directories
    copy_code_directory(fiji_source_root, destination_dir)
    copy_code_directory(common_source_root, destination_dir)
    copy_code_directory(automation_source_root, destination_dir)


if __name__ == "__main__":
    copy_files()