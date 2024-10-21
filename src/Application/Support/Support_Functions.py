import csv
import os
import re
import shutil
from tkinter.filedialog import askdirectory

import numpy as np
import pandas as pd

from src.Common.Support.DirectoriesAndLocations import (
    get_default_locations,
    save_default_locations,
    get_paint_profile_directory)
from src.Common.Support.LoggerConfig import paint_logger

pd.options.mode.copy_on_write = True


def write_np_to_excel(matrix: np.ndarray, filename: str) -> None:
    df = pd.DataFrame(matrix)
    df.reset_index(inplace=True)
    df.to_excel(filename, index=False, index_label='None', header='False', float_format="%0.2f")


def calculate_density(nr_tracks: int, area: float, time: float, concentration: float, magnification: float) -> float:
    """
    The function implements a simple algorithm to calculate the density of tracks in a square.
    To calculate the density use the actual surface coordinates.
    Assume 2000 frames (100 sec) -  need to check - this is not always the case
    Multiply by 1000 to get an easier  number
    Area is calculated with Fiji info:
        Width:  82.0864 microns(512)
        Height: 82.0864 microns(512)
    The area of a square then is (82.0854/nr_of_squares_in_row)^2

    To normalise concentration we divide by the supplied concentration

    :param nr_tracks:
    :param area:
    :param time: Normally 100 sec (2000 frames)
    :param concentration:
    :param magnification: use 1000 to getr easier numbers
    :return: the density
    """

    density = nr_tracks / area
    density /= time
    density /= concentration
    density *= magnification
    density = round(density, 1)
    return density


def ask_user_for_paint_directory(title='Select Folder'):
    """
    Asks the user for the paint directory.
    Present the previous used value and then save the users choice.
    :param title:
    :return:
    """

    # Retrieve the default from file
    root_dir, paint_dir, images_dir, conf_file = get_default_locations()

    # If that fails, select a reasonable default
    if not os.path.isdir(paint_dir):
        paint_dir = os.path.expanduser('~')

    # Ask the user
    image_directory = askdirectory(title=title, initialdir=paint_dir)

    # If the user returned something, save it to file
    if len(image_directory) != 0:
        save_default_locations(root_dir, paint_dir, images_dir, conf_file)
    return image_directory


def get_indices(x1: float, y1: float, width: float, height: float, square_seq_nr: int, nr_of_squares_in_row: int,
                granularity: int) -> tuple[int, int]:
    """
    Given coordinates (x1, y1) of the track, calculate the indices of the grid

    :param x1: The x coordinate of the track
    :param y1: The y coordinate of the track
    :param width: The width of a grid in the square
    :param height: The height of a grid in the square
    :param square_seq_nr: The number of the square for which the variability is calculated
    :param nr_of_squares_in_row: The numbers of rows and columns in the full image
    :param granularity: Specifies how fine the grid is that is overlaid on the square
    :return: The indices (xi, yi) of the grid
    """

    # Calculate the top-left corner (x0, y0) of the square
    x0 = (square_seq_nr % nr_of_squares_in_row) * width
    y0 = (square_seq_nr // nr_of_squares_in_row) * height

    # Calculate the grid indices (xi, yi) for the track
    xi = int(((x1 - x0) / width) * granularity)
    yi = int(((y1 - y0) / height) * granularity)

    return xi, yi


def get_square_coordinates(nr_of_squares_in_row, sequence_number):
    """

    :param nr_of_squares_in_row:
    :param sequence_number: The sequence number of the square for which the coordinates are needed
    :return: The coordinates of the upper left (x0, y0) and lower right corner (x1, y1)
    """
    width = 82.0864 / nr_of_squares_in_row
    height = 82.0864 / nr_of_squares_in_row

    i = sequence_number % nr_of_squares_in_row
    j = sequence_number // nr_of_squares_in_row

    x0 = i * width
    x1 = (i + 1) * width
    y0 = j * height
    y1 = (j + 1) * width
    return x0, y0, x1, y1


def calc_variability(tracks_df, square_nr, nr_of_squares_in_row, granularity):
    """
    The variability is calculated by creating a grid of granularity x granularity in the square for
    which tracks_fd specifies the tracks
    :param tracks_df: A dataframe that contains the tracks of the square for which the variability is calculated
    :param square_nr: The sequence number of the square for which the variability is calculated
    :param nr_of_squares_in_row: The number of rows and columns in the image
    :param granularity: Specifies how fine the grid is that is created
    :return:
    """

    # Create the matrix for the variability analysis
    matrix = np.zeros((granularity, granularity), dtype=int)

    # Loop over all the tracks in the square and determine where they sit in the grid
    for i in range(len(tracks_df)):
        # Retrieve the x and y values expressed in micrometers
        x = float(tracks_df.at[i, "TRACK_X_LOCATION"])
        y = float(tracks_df.at[i, "TRACK_Y_LOCATION"])

        # The width of the image is 82.0864 micrometer. The width and height of a square can be calculated
        width = 82.0864 / nr_of_squares_in_row
        height = width

        # Get the grid indices for this track and update the matrix
        xi, yi = get_indices(x, y, width, height, square_nr, nr_of_squares_in_row, 10)
        matrix[yi, xi] += 1

    # Calculate the variability by dividing the standard deviation by the average
    std = np.std(matrix)
    mean = np.mean(matrix)
    if mean != 0:
        variability = std / mean
    else:
        variability = 0
    return variability


def get_df_from_file(file, header=0, skip_rows=[]):
    try:
        df = pd.read_csv(file, header=header, skiprows=skip_rows)
    except FileNotFoundError:
        df = None
        paint_logger.error("File not found: " + file)
    except IOError:
        df = None
        paint_logger.error("IoError: " + file)

    return df


def eliminate_isolated_squares_strict(df_squares, nr_of_squares_in_row):
    list_of_squares = []
    neighbours = []

    for index, square in df_squares.iterrows():

        # If the square itself is not visible you do not need to look for neighbours
        if not (square['Valid Tau'] and
                square['Variability Visible'] and
                square['Density Ratio Visible']):
            df_squares.loc[index, 'Neighbour Visible'] = False
            continue

        row = square['Row Nr']
        col = square['Col Nr']
        square_nr = square['Square Nr']

        # Determine the neighbours to inspect
        left = (row, max(col - 1, 1))
        right = (row, min(col + 1, nr_of_squares_in_row))
        above = (max(row - 1, 1), col)
        below = (min(row + 1, nr_of_squares_in_row), col)

        if row == 1:
            if col == 1:
                neighbours = [right, below]
            elif col == nr_of_squares_in_row:
                neighbours = [left, below]
            else:
                neighbours = [left, right, below]
        elif row == nr_of_squares_in_row:
            if col == 1:
                neighbours = [right, above]
            elif col == nr_of_squares_in_row:
                neighbours = [left, above]
            else:
                neighbours = [left, right, above]
        elif 1 < row < nr_of_squares_in_row:
            if col == 1:
                neighbours = [right, below, above]
            elif col == nr_of_squares_in_row:
                neighbours = [left, below, above]
            else:
                neighbours = [left, right, below, above]

        # Do the inspection of neighbours
        nr_of_neighbours = 0
        for nb in neighbours:
            neighbour_square_nr = int((nb[0] - 1) * nr_of_squares_in_row + (nb[1] - 1))
            if neighbour_square_nr in df_squares.index:
                if (df_squares.loc[neighbour_square_nr, 'Variability Visible'] and
                        df_squares.loc[neighbour_square_nr, 'Density Ratio Visible'] and
                        df_squares.loc[neighbour_square_nr, 'Valid Tau']):
                    nr_of_neighbours += 1

        # Record the results
        if nr_of_neighbours > 0:
            df_squares.at[square['Square Nr'], 'Neighbour Visible'] = True
            list_of_squares.append(square_nr)
        else:
            df_squares.at[square['Square Nr'], 'Neighbour Visible'] = False

        df_squares['Visible'] = (df_squares['Density Ratio Visible'] &
                                 df_squares['Neighbour Visible'] &
                                 df_squares['Variability Visible'] &
                                 df_squares['Valid Tau'])

    return list_of_squares


def eliminate_isolated_squares_relaxed(df_squares, nr_of_squares_in_row):
    list_of_squares = []
    neighbours = []

    for index, square in df_squares.iterrows():

        # If the square itself is not valid you do not need to look for neighbours
        if not (square['Valid Tau'] and
                square['Variability Visible'] and
                square['Density Ratio Visible']):
            df_squares.loc[index, 'Neighbour Visible'] = False
            continue

        # Determine the neighbours to inspect
        row_nr = square['Row Nr']
        col_nr = square['Col Nr']
        square_nr = square['Square Nr']

        left = (row_nr, max(col_nr - 1, 1))
        right = (row_nr, min(col_nr + 1, nr_of_squares_in_row))
        above = (max(row_nr - 1, 1), col_nr)
        below = (min(row_nr + 1, nr_of_squares_in_row), col_nr)

        below_left = (min(row_nr + 1, nr_of_squares_in_row), max(col_nr - 1, 1))
        below_right = (min(row_nr + 1, nr_of_squares_in_row), min(col_nr + 1, nr_of_squares_in_row))
        above_left = (max(row_nr - 1, 1), max(col_nr - 1, 1))
        above_right = (max(row_nr - 1, 1), min(col_nr + 1, nr_of_squares_in_row))

        if row_nr == 1:
            if col_nr == 1:
                neighbours = [right, below, below_right, ]
            elif col_nr == nr_of_squares_in_row:
                neighbours = [left, below, below_left]
            else:
                neighbours = [left, right, below, below_left, below_right]
        elif row_nr == nr_of_squares_in_row:
            if col_nr == 1:
                neighbours = [right, above, above_right]
            elif col_nr == nr_of_squares_in_row:
                neighbours = [left, above, above_left]
            else:
                neighbours = [left, right, above, above_left, above_right]
        elif 1 < row_nr < nr_of_squares_in_row:
            if col_nr == 1:
                neighbours = [right, below, above, above_right, below_right]
            elif col_nr == nr_of_squares_in_row:
                neighbours = [left, below, above, below_right, below_left]
            else:
                neighbours = [left, right, below, above, above_right, below_right, above_left, below_left]

        # Do the inspection of neighbours
        nr_of_neighbours = 0
        for nb in neighbours:
            neighbour_seqnr = int((nb[0] - 1) * nr_of_squares_in_row + (nb[1] - 1))
            if neighbour_seqnr in df_squares.index:
                if (df_squares.loc[neighbour_seqnr, 'Variability Visible'] and
                        df_squares.loc[neighbour_seqnr, 'Density Ratio Visible'] and
                        df_squares.loc[neighbour_seqnr, 'Valid Tau']):
                    # df_squares.loc[neighbour_seqnr, 'Neighbour Visible'] = True
                    nr_of_neighbours += 1

        # Record the results
        if nr_of_neighbours > 0:
            df_squares.at[square['Square Nr'], 'Neighbour Visible'] = True
            list_of_squares.append(square_nr)
        else:
            df_squares.at[square['Square Nr'], 'Neighbour Visible'] = False

    df_squares['Visible'] = (df_squares['Density Ratio Visible'] &
                             df_squares['Neighbour Visible'] &
                             df_squares['Density Ratio Visible'])

    return df_squares, list_of_squares


def get_grid_defaults_from_file() -> dict:
    parameter_file_path = os.path.join(get_paint_profile_directory(), "grid_parameters.csv")

    def_parameters = {'nr_of_squares_in_row': 20,
                      'min_tracks_for_tau': 30,
                      'min_r_squared': 0.9,
                      'min_density_ratio': 2,
                      'max_variability': 10,
                      'max_square_coverage': 100,
                      'process_single': True,
                      'process_traditional': True}

    try:
        # Check if the file exists
        if not os.path.exists(parameter_file_path):
            return def_parameters

        # Open and read the CSV file
        with open(parameter_file_path, mode='r') as file:
            reader = csv.DictReader(file)  # Use DictReader to access columns by header names

            # Ensure required columns are present
            required_columns = ['nr_of_squares_in_row', 'min_tracks_for_tau', 'min_r_squared', 'min_density_ratio',
                                'max_variability', 'max_square_coverage', 'process_single', 'process_traditional']
            for col in required_columns:
                if col not in reader.fieldnames:
                    # raise KeyError(f"Required column '{col}' is missing from the CSV file.")
                    return def_parameters

            # Ensure file is not empty
            rows = list(reader)  # Read all rows into a list to check content
            if not rows:
                return def_parameters

            # Access the first row of data
            return rows[0]

    except FileNotFoundError as e:
        paint_logger.error(e)
    except KeyError as e:
        paint_logger.error(f"Error: {e}")
    except ValueError as e:
        paint_logger.error(f"Error: {e}")
    except Exception as e:
        paint_logger.error(f"An unexpected error occurred: {e}")
    return def_parameters


def save_grid_defaults_to_file(
        nr_of_squares_in_row: int,
        min_tracks_for_tau: int,
        min_r_squared: float,
        min_density_ratio: float,
        max_variability: float,
        max_square_coverage: int,
        process_single: bool,
        process_traditional: bool):
    grid_parameter_file_path = os.path.join(get_paint_profile_directory(), 'grid_parameters.csv')

    try:

        fieldnames = ['nr_of_squares_in_row', 'min_tracks_for_tau', 'min_r_squared', 'min_density_ratio',
                      'max_variability', 'max_square_coverage', 'process_single', 'process_traditional']

        # Open the file in write mode ('w') and overwrite any existing content
        with open(grid_parameter_file_path, mode='w') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write the data as a row
            writer.writerow({
                'nr_of_squares_in_row': nr_of_squares_in_row,
                'min_tracks_for_tau': min_tracks_for_tau,
                'min_r_squared': min_r_squared,
                'min_density_ratio': min_density_ratio,
                'max_variability': max_variability,
                'max_square_coverage': max_square_coverage,
                'process_single': process_single,
                'process_traditional': process_traditional})

    except Exception as e:
        paint_logger.error(f"An error occurred while writing to the file: {e}")


def test_if_square_is_in_rectangle(x0, y0, x1, y1, xr0, yr0, xr1, yr1):
    """
    Test if the square is in the rectangle specified by the user.
    Note these are different unit systems
    The coordinates from the squares are in micrometers
    The coordinates from the rectangle are in pixels
    One or the other needs to be converted before you can compare
    :param x0:
    :param y0:
    :param x1:
    :param y1:
    :param xr0:
    :param yr0:
    :param xr1:
    :param yr1:
    :return:
    """

    # Convert square coordinates from micrometers to pixels
    x0, y0, x1, y1 = [coord / 82.0864 * 512 for coord in [x0, y0, x1, y1]]

    # Determine if the square is within the rectangle
    if xr0 < xr1 and yr0 < yr1:
        return x0 >= xr0 and x1 <= xr1 and y0 >= yr0 and y1 <= yr1
    elif xr0 < xr1 and yr0 > yr1:
        return x0 >= xr0 and x1 <= xr1 and y0 >= yr1 and y1 <= yr0
    elif xr0 > xr1 and yr0 > yr1:
        return x0 >= xr1 and x1 <= xr0 and y0 >= yr1 and y1 <= yr0
    elif xr0 > xr1 and yr0 < yr1:
        return x0 >= xr1 and x1 <= xr0 and y0 >= yr0 and y1 <= yr1

    return False


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

    df_experiment.set_index('Ext Image Name', inplace=True, drop=False)
    # correct_all_images_column_types(df_experiment)

    return df_experiment


def read_experiment_tm_file(experiment_file_path, only_records_to_process=True):
    df_experiment = read_experiment_file(os.path.join(experiment_file_path, 'experiment_tm.csv'),
                                         only_records_to_process=only_records_to_process)
    return df_experiment


def check_experiment_integrity(df_experiment):
    """
    Check if the experiment file has the expected columns and makes sure that the types are correct
    :param df_experiment:
    :return:
    """
    expected_columns = {
        'Batch Sequence Nr',
        'Experiment Date',
        'Experiment Name',
        'Experiment Nr',
        'Experiment Seq Nr',
        'Image Name',
        'Probe',
        'Probe Type',
        'Cell Type',
        'Adjuvant',
        'Concentration',
        'Threshold',
        'Process',
        'Ext Image Name',
        'Nr Spots',
        'Image Size',
        'Run Time',
        'Time Stamp'}.issubset(df_experiment.columns)

    if expected_columns:
        # Make sure that there is a meaningful index           # TODO: Check if this is not causing problems
        df_experiment.set_index('Batch Sequence Nr', inplace=True, drop=False)
        return True
    else:
        return False


def correct_all_images_column_types(df_experiment):
    """
    Set the column types for the experiment file
    :param df_experiment:
    :return:
    """

    try:
        df_experiment['Batch Sequence Nr'] = df_experiment['Batch Sequence Nr'].astype(int)
        df_experiment['Experiment Seq Nr'] = df_experiment['Experiment Seq Nr'].astype(int)
        df_experiment['Experiment Nr'] = df_experiment['Experiment Nr'].astype(int)
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

    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")

    return ' and '.join(parts)


def calc_average_track_count_of_lowest_squares(df_squares, nr_of_average_count_squares):
    """
    The function calculates the average track count of the lowest average_count_squares squares with a track count > 0.
    The df_squares df is already sorted on track number.
    All we have to do is access backwards, ignore 0 values and only then start counting.

    :param df_squares:
    :param nr_of_average_count_squares:
    :return:
    """

    count_values = list(df_squares['Nr Tracks'])
    count_values.sort(reverse=True)

    total = 0
    n = 0
    for i in range(len(count_values) - 1, -1, -1):
        if count_values[i] > 0:
            total += count_values[i]
            n += 1
            if n >= nr_of_average_count_squares:
                break
    if n == 0:
        average = 0
    else:
        average = total / n
    return average


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


def get_area_of_square(nr_of_squares_in_row):
    MICROMETER_PER_PIXEL = 0.1602804  # Referenced from Fiji
    PIXEL_PER_IMAGE = 512  # Referenced from Fiji

    MICROMETER_PER_IMAGE = MICROMETER_PER_PIXEL * PIXEL_PER_IMAGE

    micrometer_per_square = MICROMETER_PER_IMAGE / nr_of_squares_in_row
    area = micrometer_per_square * micrometer_per_square

    return area
