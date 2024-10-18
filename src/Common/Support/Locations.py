import os


# ----------------------------------------------------------------------------------------------------------------------
# Experiment
# ----------------------------------------------------------------------------------------------------------------------
EXPERIMENT_TM = "experiment_tm.csv"
EXPERIMENT_INFO = "experiment_info.csv"
EXPERIMENT_SQUARES = "experiment_squares.csv"

def get_experiment_info_file_path(experiment_directory):
    return os.path.join(experiment_directory, EXPERIMENT_INFO)

def get_experiment_tm_file_path(experiment_directory):
    return os.path.join(experiment_directory, EXPERIMENT_TM)

def get_experiment_squares_file_path(experiment_directory):
    return os.path.join(experiment_directory,  EXPERIMENT_SQUARES)

# ----------------------------------------------------------------------------------------------------------------------
# TrackMate Tracks
# ----------------------------------------------------------------------------------------------------------------------

TRACKMATE_TRACKS = "Trackmate Tracks"

def get_tracks_dir_path(experiment_directory, image_name):
    return os.path.join(experiment_directory, image_name, TRACKMATE_TRACKS)


def get_tracks_file_path(experiment_directory, image_name):
    return os.path.join(get_tracks_dir_path(experiment_directory, image_name), image_name + "-tracks.csv")


# ----------------------------------------------------------------------------------------------------------------------
# Trackmate Images
# ----------------------------------------------------------------------------------------------------------------------

TRACKMATE_IMAGES = "Trackmate Images"

def get_image_dir_path(experiment_directory, image_name):
    return os.path.join(experiment_directory, image_name, TRACKMATE_IMAGES)


def get_image_file_path(experiment_directory, image_name):
    return os.path.join(get_image_dir_path(experiment_directory, image_name), image_name + ".tiff")


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


def get_squares_file_path(experiment_directory, image_name):
    return os.path.join(get_squares_dir_path(experiment_directory, image_name), image_name + "-squares.csv")


# ----------------------------------------------------------------------------------------------------------------------
# Miscellanea
# ----------------------------------------------------------------------------------------------------------------------

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

    tracks_dir = os.path.join(image_directory, TRACKMATE_TRACKS)  # Where all cells track files will be stored
    plt_dir = os.path.join(image_directory, TAU_PLOTS)  # Where all cells plt files will be stored
    grid_dir = os.path.join(image_directory, SQUARES)  # Where th squares files will be stored
    img_dir = os.path.join(image_directory, TRACKMATE_IMAGES)  # Where all cells img files will be stored

    dirs_to_create = [tracks_dir, plt_dir, grid_dir, img_dir]

    for directory in dirs_to_create:
        if not os.path.isdir(directory):  # Create the roi directory if it does not exist
            os.makedirs(directory)
        else:
            if delete_existing:
                delete_files_in_directory(directory)

    return tracks_dir, plt_dir, img_dir


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
        print("Error occurred while deleting files.")     #TODO Add logging

