import csv
import os
import sys


def get_default_directories():

    configuration_dir = os.path.expanduser('~') + os.sep + "Paint Profile"
    parameter_file = os.path.join(configuration_dir, "default_directories.csv")

    # Set the default directories so that you can return something in any case
    image_directory = os.path.expanduser('~')
    paint_directory = os.path.expanduser('~')
    root_directory = os.path.expanduser('~')

    try:
        # Check if the file exists
        if not os.path.exists(parameter_file):
            return root_directory, paint_directory, image_directory

        # Open and read the CSV file
        with open(parameter_file, mode='r', newline='') as file:
            reader = csv.DictReader(file)  # Use DictReader to access columns by header names

            # Ensure required columns are present
            required_columns = ['images_directory', 'paint_directory', 'root_directory']
            for col in required_columns:
                if col not in reader.fieldnames:
                    # raise KeyError(f"Required column '{col}' is missing from the CSV file.")
                    return root_directory, paint_directory, image_directory

            # Ensure file is not empty
            rows = list(reader)  # Read all rows into a list to check content
            if not rows:
                return root_directory, paint_directory, image_directory

            # Access the first row of data
            row = rows[0]
            return row['root_directory'], row['paint_directory'], row['images_directory']

    except FileNotFoundError as e:
        print(e)
    except KeyError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def save_default_directories(root_directory, paint_directory, images_directory):

    configuration_dir = os.path.join(os.path.expanduser('~'), "Paint Profile")
    parameter_file_path = os.path.join(configuration_dir, "default_directories.csv")

    os.makedirs(configuration_dir, exist_ok=True)
    try:

        fieldnames = ['images_directory', 'paint_directory', 'root_directory']

        # Open the file in write mode ('w') and overwrite any existing content
        with open(parameter_file_path, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write the data as a row
            writer.writerow({
                'images_directory': images_directory,
                'paint_directory': paint_directory,
                'root_directory': root_directory
            })

            print(f"Data successfully written to {csv_file_path}")

    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")


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
        print("Error occurred while deleting files.")


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
