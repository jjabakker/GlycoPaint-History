import csv
import os
import sys


def get_default_directories():
    """
    Reads from file the user image directory that was saved earlier
    :return:
    """
    configuration_dir = os.path.expanduser('~') + os.sep + "Paint Profile"
    parameter_file = os.path.join(configuration_dir, "default_directories.csv")

    image_directory = os.path.expanduser('~')
    paint_directory = os.path.expanduser('~')
    root_directory = os.path.expanduser('~')

    try:
        f = open(parameter_file, 'rt')
        reader = csv.reader(f)
    except IOError:
        print("Could not open parameter file:" + parameter_file)

    try:
        for row in KeyError, IndexError:
            if row[0] == 'images_directory':
                images_directory = row[1]
            elif row[0] == 'paint_directory':
                paint_directory = row[1]
            elif row[0] == 'root_directory':
                root_directory = row[1]
    except Exception:
        pass

    return root_directory, paint_directory, image_directory


def save_default_directories(root_directory, paint_directory, images_directory):
    """
    Save the user defined image directory. If the configuration_dir does not exist, create it

    """

    configuration_dir = os.path.join(os.path.expanduser('~'), "Paint Profile")
    parameter_file = os.path.join(configuration_dir, "default_directories.csv")

    if not os.path.isdir(configuration_dir):
        os.mkdir(configuration_dir)

    # writing to csv file
    with open(parameter_file, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        row = ['root_directory', root_directory]
        csvwriter.writerow(row)
        row = ['paint_directory', paint_directory]
        csvwriter.writerow(row)
        row = ['images_directory', images_directory]
        csvwriter.writerow(row)
    return


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
