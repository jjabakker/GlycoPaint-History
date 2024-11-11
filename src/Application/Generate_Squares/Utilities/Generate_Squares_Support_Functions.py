import csv
import os

import numpy as np
import pandas as pd

from src.Common.Support.DirectoriesAndLocations import (
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


def calc_variability(df_tracks, square_nr, nr_of_squares_in_row, granularity):
    """
    The variability is calculated by creating a grid of granularity x granularity in the square for
    which tracks_fd specifies the tracks
    :param df_tracks: A dataframe that contains the tracks of the square for which the variability is calculated
    :param square_nr: The sequence number of the square for which the variability is calculated
    :param nr_of_squares_in_row: The number of rows and columns in the image
    :param granularity: Specifies how fine the grid is that is created
    :return:
    """

    # Create the matrix for the variability analysis
    matrix = np.zeros((granularity, granularity), dtype=int)

    # Loop over all the tracks in the square and determine where they sit in the grid
    for index, row in df_tracks.iterrows():
        # Retrieve the x and y values expressed in micrometers
        x = float(row["Track X Location"])
        y = float(row["Track Y Location"])

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


def get_grid_defaults_from_file() -> dict:
    parameter_file_path = os.path.join(get_paint_profile_directory(), "grid_parameters.csv")

    def_parameters = {'nr_of_squares_in_row': 20,
                      'min_tracks_for_tau': 30,
                      'min_r_squared': 0.9,
                      'min_density_ratio': 2,
                      'max_variability': 10,
                      'max_square_coverage': 100,
                      'process_recording_tau': True,
                      'process_square_tau': True}

    try:
        # Check if the file exists
        if not os.path.exists(parameter_file_path):
            return def_parameters

        # Open and read the CSV file
        with open(parameter_file_path, mode='r') as file:
            reader = csv.DictReader(file)  # Use DictReader to access columns by header names

            # Ensure required columns are present
            required_columns = ['nr_of_squares_in_row', 'min_tracks_for_tau', 'min_r_squared',
                                'min_required_density_ratio', 'max_allowable_variability', 'max_square_coverage',
                                'process_recording_tau', 'process_square_tau']
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
        min_required_density_ratio: float,
        max_allowable_variability: float,
        max_square_coverage: int,
        process_recording_tau: bool,
        process_square_tau: bool):
    grid_parameter_file_path = os.path.join(get_paint_profile_directory(), 'grid_parameters.csv')

    try:

        fieldnames = ['nr_of_squares_in_row', 'min_tracks_for_tau', 'min_r_squared', 'min_required_density_ratio',
                      'max_allowable_variability', 'max_square_coverage', 'process_recording_tau', 'process_square_tau']

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
                'min_required_density_ratio': min_required_density_ratio,
                'max_allowable_variability': max_allowable_variability,
                'max_square_coverage': max_square_coverage,
                'process_recording_tau': process_recording_tau,
                'process_square_tau': process_square_tau})

    except Exception as e:
        paint_logger.error(f"An error occurred while writing to the file: {e}")


def check_experiment_integrity(df_experiment):
    """
    Check if the experiment file has the expected columns and makes sure that the types are correct
    :param df_experiment:
    :return:
    """
    expected_columns = {
        'Recording Sequence Nr',
        'Recording Name',
        'Experiment Date',
        'Experiment Name',
        'Condition Nr',
        'Replicate Nr',
        'Probe',
        'Probe Type',
        'Cell Type',
        'Adjuvant',
        'Concentration',
        'Threshold',
        'Process',
        'Ext Recording Name',
        'Nr Spots',
        'Recording Size',
        'Run Time',
        'Time Stamp'}.issubset(df_experiment.columns)

    if expected_columns:
        # Make sure that there is a meaningful index           # TODO: Check if this is not causing problems
        df_experiment.set_index('Recording Sequence Nr', inplace=True, drop=False)
        return True
    else:
        return False


def calc_average_track_count_in_background_squares(df_squares, nr_of_average_count_squares):
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


def calc_area_of_square(nr_of_squares_in_row):
    micrometer_per_pixel = 0.1602804  # Referenced from Fiji
    pixel_per_image = 512  # Referenced from Fiji
    micrometer_per_image = micrometer_per_pixel * pixel_per_image
    micrometer_per_square = micrometer_per_image / nr_of_squares_in_row
    area = micrometer_per_square * micrometer_per_square
    return area


def create_unique_key_for_squares(df):
    df['String Square Nr'] = df['Square Nr'].astype(str)
    df['Unique Key'] = df['Ext Recording Name'] + ' - ' + df['String Square Nr']
    df.set_index('Unique Key', inplace=True, drop=False)
    df.drop('String Square Nr', axis=1, inplace=True)

    # Reorder the columns
    cols = list(df.columns)
    cols.insert(0, cols.pop(cols.index('Unique Key')))
    df = df[cols]
    return df


def select_tracks_for_tau_calculation(df_tracks_in_square, limit_DC):
    if limit_DC:
        df_tracks_in_square = df_tracks_in_square[df_tracks_in_square['Diffusion Coefficient'] > 0]

    return df_tracks_in_square


def create_unique_key_for_tracks(df):
    df['Unique Key'] = df['Recording Name'] + ' - ' + df['Track Label'].str.split('_').str[1]
    df.set_index('Unique Key', inplace=True, drop=False)

    # Reorder the columns
    cols = list(df.columns)
    cols.insert(0, cols.pop(cols.index('Unique Key')))
    df = df[cols]
    return df


def write_matrices(
        recording_path: str,
        recording_name: str,
        tau_matrix: np.ndarray,
        density_matrix: np.ndarray,
        count_matrix: np.ndarray,
        variability_matrix: np.ndarray,
        verbose: bool):
    """
    Simply utility function to write the matrices to disk.
    If the grid directory does not exist, exit.
    """

    # Check if the grid directory exists
    dir_name = os.path.join(recording_path, "grid")
    if not os.path.exists(dir_name):
        paint_logger.error(f"Function 'write_matrices' failed: Directory {dir_name} does not exists.")
        exit(-1)

    # Write the Tau matrix to file
    if verbose:
        print(f"\n\nThe Tau matrix for image : {recording_name}\n")
        print(tau_matrix)
    filename = recording_path + os.sep + "grid" + os.sep + recording_name + "-tau.xlsx"
    write_np_to_excel(tau_matrix, filename)

    # Write the Density matrix to file
    if verbose:
        print(f"\n\nThe Density matrix for image : {recording_name}\n")
        print(tau_matrix)
    filename = recording_path + os.sep + "grid" + os.sep + recording_name + "-density.xlsx"
    write_np_to_excel(density_matrix, filename)

    # Write the count matrix to file
    if verbose:
        print(f"\n\nThe Count matrix for image: {recording_name}\n")
        print(count_matrix)
    filename = recording_path + os.sep + "grid" + os.sep + recording_name + "-count.xlsx"
    write_np_to_excel(count_matrix, filename)

    # Write the percentage matrix to file
    percentage_matrix = count_matrix / count_matrix.sum() * 100
    percentage_matrix.round(1)
    if verbose:
        print(f"\n\nThe Percentage matrix for image: {recording_name}\n")
        with np.printoptions(precision=1, suppress=True):
            print(count_matrix)
    filename = recording_path + os.sep + "grid" + os.sep + recording_name + "-percentage.xlsx"
    write_np_to_excel(percentage_matrix, filename)

    # Write the variability matrix to file
    if verbose:
        print(f"\n\nThe Variability matrix for image: {recording_name}\n")
        print(variability_matrix)
    filename = recording_path + os.sep + "grid" + os.sep + recording_name + "-variability.xlsx"
    write_np_to_excel(variability_matrix, filename)

    return 0


def add_columns_to_experiment_file(
        df_experiment: pd.DataFrame,
        nr_of_squares_in_row: int,
        min_tracks_for_tau: int,
        min_r_squared: float,
        min_required_density_ratio: float,
        max_allowable_variability: float):
    """
    This function adds columns to the experiment file that are needed for the grid processing.
    Only images for which the 'Process' column is set to 'Yes' are processed.
    """

    mask = ((df_experiment['Process'] == 'Yes') |
            (df_experiment['Process'] == 'yes') |
            (df_experiment['Process'] == 'Y') |
            (df_experiment['Process'] == 'y'))

    # User specified parameters
    df_experiment.loc[mask, 'Min Tracks for Tau'] = int(min_tracks_for_tau)
    df_experiment.loc[mask, 'Min R Squared'] = min_r_squared
    df_experiment.loc[mask, 'Nr of Squares in Row'] = int(nr_of_squares_in_row)
    df_experiment.loc[mask, 'Max Allowable Variability'] = max_allowable_variability
    df_experiment.loc[mask, 'Min Required Density Ratio'] = min_required_density_ratio

    # Default values
    df_experiment.loc[mask, 'Exclude'] = False
    df_experiment.loc[mask, 'Neighbour Mode'] = 'Free'

    return df_experiment


def pack_select_parameters(
        min_required_density_ratio: float,
        max_allowable_variability: float,
        min_track_duration: int,
        max_track_duration: int,
        neighbour_mode: str):

    select_parameters = {
        'min_required_density_ratio': min_required_density_ratio,
        'max_allowable_variability': max_allowable_variability,
        'min_track_duration': min_track_duration,
        'max_track_duration': max_track_duration,
        'neighbour_mode': neighbour_mode
    }

    return select_parameters

