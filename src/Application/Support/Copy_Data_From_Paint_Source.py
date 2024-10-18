import os
import shutil

from src.Common.Support.LoggerConfig import paint_logger


def copy_data_from_paint_source_to_paint_data(source_root, dest_root, include_experiment_file=True):
    """
    Copies (Trackmate) data from the Paint Source root to the appropriate Paint Data root
    Only the images directories are copied, not the Output directory or the csv files

    :param source_root:
    :param dest_root:
    :return:
    """

    # Delete
    try:
        # Get all the directories in the destination root
        exp_dirs = [d for d in os.listdir(dest_root) if os.path.isdir(os.path.join(dest_root, d))]
        exp_dirs.sort()

        for exp in exp_dirs:
            if 'Output' in exp:
                continue

            # Create a path to the Experiment directories
            exp_path = os.path.join(dest_root, exp)

            # Find out which directories exist for each experiment
            image_dirs = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
            image_dirs.sort()

            # Delete each of these directories if they are not the Output or Converted
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

            if 'Output' in exp:
                continue

            src_dirs = [d for d in os.listdir(os.path.join(source_root, exp)) if
                        os.path.isdir(os.path.join(source_root, exp, d))]
            src_dirs.sort()

            for src_dir in src_dirs:
                # Do the actual copying
                dest_dir = os.path.join(dest_root, exp, src_dir)
                try:
                    shutil.copytree(os.path.join(source_root, exp, src_dir), dest_dir, dirs_exist_ok=True)
                    paint_logger.debug(f"Copied directory from {os.path.join(source_root, exp, src_dir)} to {dest_dir}")
                except Exception as e:
                    paint_logger.error(
                        f"copy_data_from_source: copy_directory: Failed to copy directory from {src_dir} to {dest_dir}. Error: {e}")

            if include_experiment_file:
                # And copy the expert files
                shutil.copy(os.path.join(source_root, exp, 'experiment_tm.csv'), os.path.join(dest_root, exp))
                shutil.copy(os.path.join(source_root, exp, 'experiment_info.csv'), os.path.join(dest_root, exp))

        return True

    except Exception as e:
        paint_logger.error(f"copy_data_from_source: Failed to process directories in {dest_root}. Error: {e}")
        return False


if __name__ == '__main__':
    # Example usage

    copy_data_from_paint_source_to_paint_data(
        source_root='/Users/hans/Paint Source/New Probes',
        dest_root='/Users/hans/Paint Data/New Probes/Single/Test - Paint New Probes - Single - 30 Squares - 10 DR'
    )
