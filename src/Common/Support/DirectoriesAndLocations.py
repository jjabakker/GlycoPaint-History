import csv
import os
import sys
from os import makedirs

# ----------------------------------------------------------------------------------------------------------------------
# Experiment
# ----------------------------------------------------------------------------------------------------------------------
EXPERIMENT_TM = "experiment_tm.csv"
EXPERIMENT_INFO = "Experiment Info.csv"


def get_experiment_info_file_path(experiment_directory):
    return os.path.join(experiment_directory, EXPERIMENT_INFO)


def get_experiment_tm_file_path(experiment_directory):
    return os.path.join(experiment_directory, EXPERIMENT_TM)


# ----------------------------------------------------------------------------------------------------------------------
# TrackMate Tracks
# ----------------------------------------------------------------------------------------------------------------------

def get_tracks_dir_path(experiment_directory, image_name):
    return os.path.join(experiment_directory)
    # return os.path.join(experiment_directory, image_name)


def get_tracks_file_path(experiment_directory, image_name):
    return os.path.join(get_tracks_dir_path(experiment_directory, image_name), image_name + "-tracks.csv")


# ----------------------------------------------------------------------------------------------------------------------
# Tau Plots
# ----------------------------------------------------------------------------------------------------------------------

TAU_PLOTS = "Tau Plots"


def get_tau_plots_dir_path(experiment_directory, image_name):
    return os.path.join(experiment_directory, image_name, TAU_PLOTS)


# ----------------------------------------------------------------------------------------------------------------------
# Squares
# ----------------------------------------------------------------------------------------------------------------------

SQUARES = "Squares"


def get_squares_dir_path(experiment_directory, image_name):
    return os.path.join(experiment_directory, image_name, SQUARES)


# ----------------------------------------------------------------------------------------------------------------------
# Miscellanea
# ----------------------------------------------------------------------------------------------------------------------

def create_directories(image_directory, delete_existing=True):
    """
    :param image_directory:
    :param delete_existing:
    :return:
    """

    if not os.path.isdir(image_directory):
        os.makedirs(image_directory)
    else:
        if delete_existing:
            delete_files_in_directory(image_directory)
    return


def _get_paint_configuration_directory(sub_dir):
    conf_dir = os.path.join(os.path.expanduser('~'), 'Paint')
    if not os.path.exists(conf_dir):
        makedirs(os.path.join(conf_dir, sub_dir))
    return conf_dir


def get_paint_profile_directory():
    sub_dir = 'Profile'
    return os.path.join(_get_paint_configuration_directory(sub_dir), sub_dir)


def get_paint_logger_directory():
    sub_dir = 'Logger'
    return os.path.join(_get_paint_configuration_directory(sub_dir), sub_dir)


# def get_paint_defaults_directory():
#     sub_dir = 'Defaults'
#     return os.path.join(_get_paint_configuration_directory(sub_dir), sub_dir)


def get_paint_defaults_file_path():
    sub_dir = 'Defaults'
    return os.path.join(_get_paint_configuration_directory(sub_dir), sub_dir, 'Paint.json')
    return path


def get_default_locations():
    default_locations_file_path = os.path.join(get_paint_profile_directory(), "default_locations.csv")

    # Set the default directories so that you can return something in any case
    image_directory = os.path.expanduser('~')
    paint_directory = os.path.expanduser('~')
    root_directory = os.path.expanduser('~')
    level = os.path.expanduser('~')

    try:
        # Check if the file exists
        if not os.path.exists(default_locations_file_path):
            return root_directory, paint_directory, image_directory, level

        # Open and read the CSV file
        with open(default_locations_file_path, mode='r') as file:
            reader = csv.DictReader(file)  # Use DictReader to access columns by header names

            # Ensure required columns are present
            required_columns = ['images_directory', 'paint_directory', 'root_directory', 'level']
            for col in required_columns:
                if col not in reader.fieldnames:
                    # raise KeyError(f"Required column '{col}' is missing from the CSV file.")
                    return root_directory, paint_directory, image_directory, level

            # Ensure file is not empty
            rows = list(reader)  # Read all rows into a list to check content
            if not rows:
                return root_directory, paint_directory, image_directory, level

            # Access the first row of data
            row = rows[0]
            return row['root_directory'], row['paint_directory'], row['images_directory'], row['level']

    except KeyError as e:
        print("Error: {}".format(e))
    except ValueError as e:
        print("Error: {}".format(e))
    except Exception as e:
        print("An unexpected error occurred: {}".format(e))
    return root_directory, paint_directory, image_directory, level


def save_default_locations(root_directory, paint_directory, images_directory, level):
    default_locations_file_path = os.path.join(get_paint_profile_directory(), "default_locations.csv")

    try:

        fieldnames = ['images_directory', 'paint_directory', 'root_directory', 'level']

        # Open the file in write mode ('w') and overwrite any existing content
        with open(default_locations_file_path, mode='w') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write the data as a row
            writer.writerow({
                'images_directory': images_directory,
                'paint_directory': paint_directory,
                'root_directory': root_directory,
                'level': level
            })

    except Exception as e:
        print("An error occurred while writing to the file: {}".format(e))  # TODO: Add logging


def delete_files_in_directory(directory_path):
    """
    Delete all files in the specified directory.
    Note that only files are deleted, directories are left.

    :param directory_path: The directory to be emptied
    :return:
    """
    try:
        if not os.path.exists(directory_path):
            return
        files = os.listdir(directory_path)
        for file in files:
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except OSError:
        print("Error occurred while deleting files.")  # TODO Add logging


def get_default_image_directory():
    """
    Determine where the root is. We are looking for something like /Users/xxxx/Trackmate Data
    The only thing that can vary is the username.
    If the directory does not exist just warn and abort
    :return:  the image root directory
    """

    image_directory = os.path.expanduser('~') + os.sep + "Trackmate Data"
    if not os.path.isdir(image_directory):
        print("\nPlease ensure that a directory /User/***/Trackmate Data exists (with xxx the user name)")
        sys.exit()
    else:
        return image_directory
