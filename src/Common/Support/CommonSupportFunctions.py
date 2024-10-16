import csv
import os
import sys
from os import makedirs


def _get_paint_configuration_directory(sub_dir):
    conf_dir = os.path.join(os.path.expanduser('~'), 'Paint')
    makedirs(os.path.join(conf_dir, sub_dir), exist_ok=True)
    return conf_dir

def get_paint_profile_directory():
    sub_dir = 'Paint Profile'
    return os.path.join(_get_paint_configuration_directory(sub_dir), sub_dir)

def get_paint_logger_directory():
    sub_dir = 'Paint Logger'
    return os.path.join(_get_paint_configuration_directory(sub_dir), sub_dir)

def get_default_locations():

    default_locations_file_path = os.path.join(get_paint_profile_directory(), "default_locations.csv")

    # Set the default directories so that you can return something in any case
    image_directory = os.path.expanduser('~')
    paint_directory = os.path.expanduser('~')
    root_directory = os.path.expanduser('~')
    conf_file = ""

    try:
        # Check if the file exists
        if not os.path.exists(default_locations_file_path):
            return root_directory, paint_directory, image_directory, conf_file

        # Open and read the CSV file
        with open(default_locations_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)  # Use DictReader to access columns by header names

            # Ensure required columns are present
            required_columns = ['images_directory', 'paint_directory', 'root_directory', 'conf_file']
            for col in required_columns:
                if col not in reader.fieldnames:
                    # raise KeyError(f"Required column '{col}' is missing from the CSV file.")
                    return root_directory, paint_directory, image_directory, conf_file

            # Ensure file is not empty
            rows = list(reader)  # Read all rows into a list to check content
            if not rows:
                return root_directory, paint_directory, image_directory, conf_file

            # Access the first row of data
            row = rows[0]
            return row['root_directory'], row['paint_directory'], row['images_directory'], row['conf_file']

    except FileNotFoundError as e:
        print(e)
    except KeyError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def save_default_locations(root_directory, paint_directory, images_directory, conf_file):

    default_locations_file_path = os.path.join(get_paint_profile_directory(), "default_locations.csv")

    try:

        fieldnames = ['images_directory', 'paint_directory', 'root_directory', 'conf_file']

        # Open the file in write mode ('w') and overwrite any existing content
        with open(default_locations_file_path, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write the data as a row
            writer.writerow({
                'images_directory': images_directory,
                'paint_directory': paint_directory,
                'root_directory': root_directory,
                'conf_file': conf_file
            })

    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")   #TODO: Add logging


def delete_files_in_directory(directory_path):
    """
    Delete all files in the specified directory.
    Note that only files are deleted, directories are left.

    :param directory_path: The directory to be emptied
    :return:
    """
    try:
        files = os.listdir(directory_path)
        for file in files:
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except OSError:
        print("Error occurred while deleting files.")     #TODO Add logging


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


def create_directories(image_directory, delete_existing=True):
    """
    The function creates a bunch of directories under the specified directory.
    If there were already files in the specified directory they will be deleted
    :param image_directory:
    :param delete_existing:
    :return:
    """

    if not os.path.isdir(image_directory):
        os.makedirs(image_directory)
    else:
        if delete_existing:
            delete_files_in_directory(image_directory)

    tracks_dir = os.path.join(image_directory, "tracks")  # Where all cells track files will be stored
    plt_dir = os.path.join(image_directory, "plt")  # Where all cells plt files will be stored
    grid_dir = os.path.join(image_directory, "grid")  # Where all grid files will be stored
    img_dir = os.path.join(image_directory, "img")  # Where all cells img files will be stored

    dirs_to_create = [tracks_dir, plt_dir, grid_dir, img_dir]

    for directory in dirs_to_create:
        if not os.path.isdir(directory):  # Create the roi directory if it does not exist
            os.makedirs(directory)
        else:
            if delete_existing:
                delete_files_in_directory(directory)

    return tracks_dir, plt_dir, img_dir
