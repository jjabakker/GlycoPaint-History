import os
import re
import shutil
from tkinter.filedialog import askdirectory

import pandas as pd

from src.Common.Support.DirectoriesAndLocations import (
    get_default_locations,
    save_default_locations)
from src.Common.Support.LoggerConfig import paint_logger

pd.options.mode.copy_on_write = True


def ask_user_for_paint_directory(title='Select Folder'):
    """
    Asks the user for the paint directory.
    Present the previous used value and then save the users choice.
    :param title:
    :return:
    """

    # Retrieve the default from file
    root_dir, paint_dir, images_dir, level = get_default_locations()

    # If that fails, select a reasonable default
    if not os.path.isdir(paint_dir):
        paint_dir = os.path.expanduser('~')

    # Ask the user
    image_directory = askdirectory(title=title, initialdir=paint_dir)

    # If the user returned something, save it to file
    if len(image_directory) != 0:
        save_default_locations(root_dir, paint_dir, images_dir, level)
    return image_directory


def save_experiment_to_file(df_experiment, experiment_file_path):
    df_experiment.to_csv(experiment_file_path, index=False)


def save_squares_to_file(df_squares, square_file_path):
    df_squares.to_csv(square_file_path, index=False)


def read_experiment_file(experiment_file_path: str, only_records_to_process: bool = True) -> pd.DataFrame:
    """
    Create the process table by looking for records that were marked for processing
    :return:
    """

    try:
        df_experiment = pd.read_csv(experiment_file_path, header=0, skiprows=[])
    except IOError:
        return None

    if only_records_to_process:
        df_experiment = df_experiment[df_experiment['Process'].str.lower().isin(['yes', 'y'])]

    df_experiment.set_index('Ext Recording Name', inplace=True, drop=False)
    df_experiment['Experiment Date'] = df_experiment['Experiment Date'].astype(str)

    return df_experiment


def read_experiment_tm_file(experiment_file_path, only_records_to_process=True):
    df_experiment = read_experiment_file(os.path.join(experiment_file_path, 'All Recordings.csv'),
                                         only_records_to_process=only_records_to_process)
    return df_experiment


def correct_all_images_column_types(df_experiment):
    """
    Set the column types for the experiment file
    :param df_experiment:
    :return:
    """

    try:
        df_experiment['Recording Sequence Nr'] = df_experiment['Recording Sequence Nr'].astype(int)
        df_experiment['Condition Nr'] = df_experiment['Condition Nr'].astype(int)
        df_experiment['Replicate Nr'] = df_experiment['Replicate Nr'].astype(int)
        df_experiment['Experiment Date'] = df_experiment['Experiment Date'].astype(str)
        df_experiment['Threshold'] = df_experiment['Threshold'].astype(int)
        df_experiment['Min Tracks for Tau'] = df_experiment['Min Tracks for Tau'].astype(int)
        df_experiment['Min R Squared'] = df_experiment['Min R Squared'].astype(float)
        df_experiment['Nr of Squares in Row'] = df_experiment['Nr of Squares in Row'].astype(int)
        df_experiment['Nr Visible Squares'] = df_experiment['Nr Visible Squares'].astype(int)
        df_experiment['Nr Invisible Squares'] = df_experiment['Nr Invisible Squares'].astype(int)
        df_experiment['Nr Total Squares'] = df_experiment['Nr Total Squares'].astype(int)
        df_experiment['Nr Defined Squares'] = df_experiment['Nr Defined Squares'].astype(int)
        df_experiment['Nr Rejected Squares'] = df_experiment['Nr Rejected Squares'].astype(int)

    except (ValueError, TypeError):
        return False
    return True


def read_squares_from_file(squares_file_path):
    try:
        df_squares = pd.read_csv(squares_file_path, header=0, skiprows=[])
    except IOError:
        paint_logger.error(f'Read_squares from_file: file {squares_file_path} could not be opened.')
        exit(-1)

    df_squares['Experiment Date'] = df_squares['Experiment Date'].astype(str)

    df_squares.set_index('Square Nr', inplace=True, drop=False)
    return df_squares


def format_time_nicely(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)

    if hours == 0 and minutes == 0 and seconds == 0:
        return "0 seconds"
    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")

    return ' and '.join(parts)


def split_probe_valency(row):
    regexp = re.compile(r'(?P<valency>\d) +(?P<structure>[A-Za-z]+)')
    match = regexp.match(row['Probe'])
    if match is not None:
        valency = match.group('valency')
        return int(valency)
    else:
        return 0


def split_probe_structure(row):
    regexp = re.compile(r'(?P<valency>\d) +(?P<structure>[A-Za-z]+)')
    match = regexp.match(row['Probe'])
    if match is not None:
        structure = match.group('structure')
        return structure
    else:
        return ""


def copy_directory(src, dest):
    try:
        shutil.rmtree(dest, ignore_errors=True)
        paint_logger.debug(f"Removed {dest}")
    except FileNotFoundError as e:
        paint_logger.error(f"FileNotFoundError: {e}")
    except PermissionError as e:
        paint_logger.error(f"PermissionError: {e}")
    except OSError as e:
        paint_logger.error(f"OSError: {e}")
    except RecursionError as e:
        paint_logger.error(f"RecursionError: {e}")
    except Exception as e:
        paint_logger.error(f"An unexpected error occurred: {e}")

    try:
        shutil.copytree(src, dest)
        paint_logger.debug(f"Copied {src} to {dest}")
    except FileNotFoundError as e:
        paint_logger.error(f"FileNotFoundError: {e}")
    except FileExistsError as e:
        paint_logger.error(f"FileExistsError: {e}")
    except PermissionError as e:
        paint_logger.error(f"PermissionError: {e}")
    except OSError as e:
        paint_logger.error(f"OSError: {e}")
    except RecursionError as e:
        paint_logger.error(f"RecursionError: {e}")
    except Exception as e:
        paint_logger.error(f"An unexpected error occurred: {e}")


def _inspect_dirs(root_dir, required_files, required_dirs):  # Define the set of required files

    # Initialize counters
    complete_count = 0
    incomplete_count = 0

    # Loop through each immediate subdirectory in the root directory
    for subdir in os.listdir(root_dir):
        subdir_path = os.path.join(root_dir, subdir)

        # Check if it is a directory (ignore files in root_dir)
        if os.path.isdir(subdir_path):
            # Get the set of files and directories in the subdirectory
            items_in_subdir = set(os.listdir(subdir_path))

            # Check for required files and directories
            has_required_files = required_files.issubset(items_in_subdir)
            has_required_dirs = required_dirs.issubset(items_in_subdir)

            # Update counters based on the presence of required files and directories
            if has_required_files and has_required_dirs:
                complete_count += 1
            else:
                incomplete_count += 1

    # Return the counts of complete and incomplete subdirectories
    return complete_count, incomplete_count


def test_paint_directory_type_for_generate(directory):
    required_files = {'All Tracks.csv'}
    required_dirs = {'TrackMate Images', 'Brightfield Images'}

    complete_experiment_dirs, problem_experiment_dirs = _inspect_dirs(directory, required_files, required_dirs)
    if complete_experiment_dirs > 0:
        if problem_experiment_dirs == 0:
            return 'Project'
        else:
            return None
    else:
        dir_content = os.listdir(directory)
        if all(item in dir_content for item in required_dirs):
            return 'Experiment'
        else:
            return None


def test_paint_directory_type_for_compile(directory):
    required_files = {'All Squares.csv', 'All Tracks.csv', 'All Recordings.csv'}
    required_dirs = {'TrackMate Images', 'Brightfield Images'}

    complete_experiment_dirs, problem_experiment_dirs = _inspect_dirs(directory, required_files, required_dirs)
    if complete_experiment_dirs > 0:
        if problem_experiment_dirs == 0:
            return 'Project'
        else:
            return None
    else:
        dir_content = os.listdir(directory)
        if all(item in dir_content for item in required_dirs):
            return 'Experiment'
        else:
            return None
