import csv
import os
from tkinter.filedialog import askdirectory

import numpy as np
import pandas as pd

from src.Common.Support.CommonSupportFunctions import get_default_directories, save_default_directories
from src.Common.Support.LoggerConfig import paint_logger

pd.options.mode.copy_on_write = True


def write_np_to_excel(matrix: np.ndarray, filename: str) -> None:

    df = pd.DataFrame(matrix)
    df.reset_index(inplace=True)
    df.to_excel(filename, index=False, index_label='None', header='False', float_format="%0.2f")


def calculate_density(nr_tracks: int, area: float, time: float, concentration: float, magnification: float) -> float:
    """
    The function implements a simple algorithm to calculate the density
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
    root_dir, paint_dir, images_dir = get_default_directories()

    # If that fails, select a reasonable default
    if not os.path.isdir(paint_dir):
        paint_dir = os.path.expanduser('~')

    # Ask the user
    image_directory = askdirectory(title=title, initialdir=paint_dir)

    # If the user returned something, save it to file
    if len(image_directory) != 0:
        save_default_directories(root_dir, paint_dir, images_dir)
    return image_directory


# def get_list_of_images(image_directory):
#     """
#     The function returns a list of all directories (images) in the specified image directory
#     :param image_directory:
#     :return:
#     """
#     image_list = []
#     images_in_directory = os.listdir(image_directory)
#     images_in_directory.sort()
#
#     for image_name in images_in_directory:
#         if os.path.isfile(image_directory + os.sep + image_name):
#             continue
#         image_list.append(image_name)
#     return image_list


def get_indices(x1: float, y1: float, width: float, height: float, square_seq_nr: int, nr_squares_in_row: int, granularity: int) -> tuple[int, int]:
    """
    Given coordinates (x1, y1) of the track, calculate the indices of the grid

    :param x1: The x coordinate of the track
    :param y1: The y coordinate of the track
    :param width: The width of a grid in the square
    :param height: The height of a grid in the square
    :param square_seq_nr: The number of the square for which the variability is calculated
    :param nr_squares_in_row: The numbers of rows and columns in the full image
    :param granularity: Specifies how fine the grid is that is overlaid on the square
    :return: The indices (xi, yi) of the grid
    """

    # Calculate the top-left corner (x0, y0) of the square
    x0 = (square_seq_nr % nr_squares_in_row) * width
    y0 = (square_seq_nr // nr_squares_in_row) * height

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


def calc_variability(tracks_df, square_nr, nr_squares_in_row, granularity):
    """
    The variability is calculated by creating a grid of granularity x granularity in the square for
    which tracks_fd specifies the tracks
    :param tracks_df: A dataframe that contains the tracks of the square for which the variability is calculated
    :param square_nr: The sequence number of the square for which the variability is calculated
    :param nr_squares_in_row: The number of rows and columns in the image
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
        width = 82.0864 / nr_squares_in_row
        height = width

        # Get the grid indices for this track and update the matrix
        xi, yi = get_indices(x, y, width, height, square_nr, nr_squares_in_row, 10)
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
    except IOError:
        df = None
        print("\nFile not found: " + file)

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


def eliminate_isolated_squares_relaxed(df_squares, nr_squares_in_row):
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
        right = (row_nr, min(col_nr + 1, nr_squares_in_row))
        above = (max(row_nr - 1, 1), col_nr)
        below = (min(row_nr + 1, nr_squares_in_row), col_nr)

        below_left = (min(row_nr + 1, nr_squares_in_row), max(col_nr - 1, 1))
        below_right = (min(row_nr + 1, nr_squares_in_row), min(col_nr + 1, nr_squares_in_row))
        above_left = (max(row_nr - 1, 1), max(col_nr - 1, 1))
        above_right = (max(row_nr - 1, 1), min(col_nr + 1, nr_squares_in_row))

        if row_nr == 1:
            if col_nr == 1:
                neighbours = [right, below, below_right, ]
            elif col_nr == nr_squares_in_row:
                neighbours = [left, below, below_left]
            else:
                neighbours = [left, right, below, below_left, below_right]
        elif row_nr == nr_squares_in_row:
            if col_nr == 1:
                neighbours = [right, above, above_right]
            elif col_nr == nr_squares_in_row:
                neighbours = [left, above, above_left]
            else:
                neighbours = [left, right, above, above_left, above_right]
        elif 1 < row_nr < nr_squares_in_row:
            if col_nr == 1:
                neighbours = [right, below, above, above_right, below_right]
            elif col_nr == nr_squares_in_row:
                neighbours = [left, below, above, below_right, below_left]
            else:
                neighbours = [left, right, below, above, above_right, below_right, above_left, below_left]

        # Do the inspection of neighbours
        nr_of_neighbours = 0
        for nb in neighbours:
            neighbour_seqnr = int((nb[0] - 1) * nr_squares_in_row + (nb[1] - 1))
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

    configuration_dir = os.path.expanduser('~') + os.sep + "Paint Profile"
    parameter_file_path = os.path.join(configuration_dir, "grid_parameters.csv")

    def_parameters = {'nr_squares_in_row': 20,
                      'min_tracks_for_tau': 30,
                      'min_r_squared': 0.9,
                      'min_density_ratio': 2,
                      'max_variability': 10,
                      'max_square_coverage': 100}

    try:
        # Check if the file exists
        if not os.path.exists(parameter_file_path):
            return def_parameters

        # Open and read the CSV file
        with open(parameter_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)  # Use DictReader to access columns by header names

            # Ensure required columns are present
            required_columns = ['nr_squares_in_row', 'min_tracks_for_tau', 'min_r_squared', 'min_density_ratio', 'max_variability', 'max_square_coverage']
            for col in required_columns:
                if col not in reader.fieldnames:
                    # raise KeyError(f"Required column '{col}' is missing from the CSV file.")
                    return def_parameters

            # Ensure file is not empty
            rows = list(reader)  # Read all rows into a list to check content
            if not rows:
                return def_parameters

            # Access the first row of data
            row = rows[0]
            return rows[0]
            return {'nr_squares_in_row': row['nr_squares_in_row'],
                    'min_tracks_for_tau': row['min_tracks_for_tau'],
                    'min_r_squared': row['min_r_squared'],
                    'min_density_ratio': row['min_density_ratio'],
                    'max_variability': row['max_variability'],
                    'max_square_coverage': row['max_square_coverage']}


    except FileNotFoundError as e:
        print(e)
    except KeyError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return def_parameters

def save_grid_defaults_to_file(nr_squares_in_row,
                               min_tracks_for_tau,
                               min_r_squared,
                               min_density_ratio,
                               max_variability,
                               max_square_coverage):

    configuration_dir = os.path.join(os.path.expanduser('~'), "Paint Profile")
    parameter_file_path = os.path.join(configuration_dir, "grid_parameters.csv")

    os.makedirs(configuration_dir, exist_ok=True)

    try:

        fieldnames = ['nr_squares_in_row', 'min_tracks_for_tau', 'min_r_squared', 'min_density_ratio', 'max_variability',  'max_square_coverage']

        # Open the file in write mode ('w') and overwrite any existing content
        with open(parameter_file_path, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write the data as a row
            writer.writerow({
                'nr_squares_in_row': nr_squares_in_row,
                'min_tracks_for_tau': min_tracks_for_tau,
                'min_r_squared': min_r_squared,
                'min_density_ratio': min_density_ratio,
                'max_variability': max_variability,
                'max_square_coverage': max_square_coverage})

            print(f"Data successfully written to {parameter_file_path}")

    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")



def save_grid_defaults_to_file1(nr_squares_in_row,
                               min_tracks_for_tau,
                               min_r_squared,
                               min_density_ratio,
                               max_variability,
                               max_square_coverage):
    configuration_dir = os.path.join(os.path.expanduser('~'), "Paint profile")
    parameter_file = os.path.join(configuration_dir, "grid_parameters.csv")
    os.makedirs(configuration_dir, exist_ok=True)

    df = pd.DataFrame.from_dict({'Parameter': ['nr_squares_in_row',
                                               'min_tracks_for_tau',
                                               'min_r_squared',
                                               'min_density_ratio',
                                               'max_variability',
                                               'max_square_coverage'
                                               ],
                                 'Value': [round(nr_squares_in_row, 0),
                                           round(min_tracks_for_tau, 0),
                                           round(min_r_squared, 1),
                                           round(min_density_ratio, 1),
                                           round(max_variability, 1),
                                           round(max_square_coverage, 1)
                                           ]
                                 })

    try:
        df.to_excel(parameter_file, index=False)
    except IOError:
        pass

    return


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

    # x0 = x0 / 82.0864 * 512
    # y0 = y0 / 82.0864 * 512
    # x1 = x1 / 82.0864 * 512
    # y1 = y1 / 82.0864 * 512
    #
    # c1 = c2 = c3 = c4 = False
    #
    # if xr0 < xr1 and yr0 < yr1:
    #     c1 = x0 >= xr0
    #     c2 = x1 <= xr1
    #     c3 = y0 >= yr0
    #     c4 = y1 <= yr1
    #
    # if xr0 < xr1 and yr0 > yr1:
    #     c1 = x0 >= xr0
    #     c2 = x1 <= xr1
    #     c3 = y0 >= yr1
    #     c4 = y1 <= yr0
    #
    # if xr0 > xr1 and yr0 > yr1:
    #     c1 = x0 >= xr1
    #     c2 = x1 <= xr0
    #     c3 = y0 >= yr1
    #     c4 = y1 <= yr0
    #
    # if xr0 > xr1 and yr0 < yr1:
    #     c1 = x0 >= xr1
    #     c2 = x1 <= xr0
    #     c3 = y0 >= yr0
    #     c4 = y1 <= yr1
    #
    # return c1 and c2 and c3 and c4


def save_batch_to_file(df_batch, batch_file_path):
    df_batch.to_csv(batch_file_path, index=False)


def save_squares_to_file(df_squares, square_file_path):
    df_squares.to_csv(square_file_path, index=False)


def read_batch_from_file(batch_file_path, only_records_to_process=True):
    """
    Create the process table by looking for records that were marked for processing
    :return:
    """

    try:
        df_batch = pd.read_csv(batch_file_path, header=0, skiprows=[])
    except IOError:
        return None

    # Only process the records the user has indicated to be of interest
    if only_records_to_process:
        # df_batch = df_batch[(df_batch['Process'] == 'Yes') |
        #                     (df_batch['Process'] == 'yes') |
        #                     (df_batch['Process'] == 'Y') |
        #                     (df_batch['Process'] == 'y')]
        df_batch = df_batch[df_batch['Process'].str.lower().isin(['yes', 'y'])]

    df_batch.set_index('Ext Image Name', inplace=True, drop=False)

    return df_batch


def check_grid_batch_integrity(df_batch):
    return {'Batch Sequence Nr',
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
            'Time Stamp',
            'Min Tracks for Tau',
            'Min R Squared',
            'Nr Of Squares per Row',
            'Neighbour Setting',
            'Variability Setting',
            'Density Ratio Setting',
            'Nr Visible Squares',
            'Nr Total Squares',
            'Squares Ratio',
            'Exclude',
            'Nr Defined Squares',
            'Nr Rejected Squares',
            'Max Squares Ratio'}.issubset(df_batch.columns)


def check_batch_integrity(df_batch):
    return {'Batch Sequence Nr',
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
            'Time Stamp'}.issubset(df_batch.columns)


def read_squares_from_file(squares_file_path):
    try:
        df_squares = pd.read_csv(squares_file_path, header=0, skiprows=[])
    except IOError:
        print(f'Read_squares from_file: file {squares_file_path} could not be opened.')
        exit(-1)

    df_squares.set_index('Square Nr', inplace=True, drop=False)
    return df_squares


def create_output_directories_for_graphpad(paint_directory):
    directories = [
        os.path.join(paint_directory, 'Output', 'pdf', 'Tau'),
        os.path.join(paint_directory, 'Output', 'pdf', 'Density'),
        os.path.join(paint_directory, 'Output', 'graphpad', 'Tau'),
        os.path.join(paint_directory, 'Output', 'graphpad', 'Density')
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


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

    total = 0
    n = 0
    for i in range(len(count_values) - 1, 0, -1):
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
