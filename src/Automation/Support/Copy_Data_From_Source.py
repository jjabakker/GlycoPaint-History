import os
import shutil

from src.Common.Support.LoggerConfig import paint_logger


def copy_directory(src, dest):
    try:
        # Check if the destination directory exists
        # if os.path.exists(dest):
        #     # If it exists, remove it to allow overwriting
        #     shutil.rmtree(dest)

        # Now, copy the directory
        shutil.copytree(src, dest, dirs_exist_ok=True)
        paint_logger.debug(f"Copied directory from {src} to {dest}")

    except Exception as e:
        paint_logger.error(
            f"copy_data_from_source: copy_directory: Failed to copy directory from {src} to {dest}. Error: {e}")


def copy_data_from_source(source_root, dest_root):
    try:

        # Delete the image directories

        exp_dirs = [d for d in os.listdir(dest_root) if os.path.isdir(os.path.join(dest_root, d))]
        exp_dirs.sort()

        for exp in exp_dirs:
            if 'Output' in exp:
                continue

            exp_path = os.path.join(dest_root, exp)

            image_dirs = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
            image_dirs.sort()

            for image_dir in image_dirs:
                if 'Output' in image_dir or 'Converted' in image_dir:
                    continue

                if os.path.isfile(os.path.join(exp_path, image_dir)):
                    continue

                dest_path = os.path.join(exp_path, image_dir)
                shutil.rmtree(dest_path)

        # And fill it op again
        exp_dirs = [d for d in os.listdir(os.path.join(source_root)) if os.path.isdir(os.path.join(source_root, d))]
        exp_dirs.sort()

        for exp in exp_dirs:
            src_dirs = [d for d in os.listdir(os.path.join(source_root, exp)) if
                        os.path.isdir(os.path.join(source_root, exp, d))]
            src_dirs.sort()

            for src_dir in src_dirs:
                dest_dir = os.path.join(dest_root, exp, src_dir)
                copy_directory(os.path.join(source_root, exp, src_dir), dest_dir)

    except Exception as e:
        paint_logger.error(f"copy_data_from_source: Failed to process directories in {dest_root}. Error: {e}")


if __name__ == '__main__':
    # Example usage

    copy_data_from_source(
        source_root='/Users/hans/Paint Source/New Probes',
        dest_root='/Users/hans/Paint Data/New Probes/Single/Test - Paint New Probes - Single - 30 Squares - 10 DR'
    )
