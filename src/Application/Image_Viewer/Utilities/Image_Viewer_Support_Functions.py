from tkinter import *

import pandas as pd
from PIL import Image

pd.options.mode.copy_on_write = True


def save_as_png(canvas, file_name):
    # First save as a postscript file
    canvas.postscript(file=file_name + '.ps', colormode='color')

    # Then let PIL convert to a png file
    img = Image.open(file_name + '.ps')
    img.save(f"{file_name}.png", 'png')


# def save_square_info_to_batch(self):  # TODO
#     for index, row in self.df_experiment.iterrows():
#         self.squares_file_name = self.list_images[self.img_no]['Squares File']
#         df_squares = read_squares_from_file(self.squares_file_name)
#         if df_squares is None:
#             paint_logger.error("Function 'save_square_info_to_batch' failed: - Square file does not exist")
#             sys.exit()
#         if len(df_squares) > 0:
#             nr_visible_squares = len(df_squares[df_squares['Visible']])
#             nr_total_squares = len(df_squares)
#             squares_ratio = round(nr_visible_squares / nr_total_squares, 2)
#         else:
#             nr_visible_squares = 0
#             nr_total_squares = 0
#             squares_ratio = 0.0
#
#         self.df_experiment.loc[index, 'Nr Visible Squares'] = nr_visible_squares
#         self.df_experiment.loc[index, 'Nr Total Squares'] = nr_total_squares
#         self.df_experiment.loc[index, 'Squares Ratio'] = squares_ratio


def eliminate_isolated_squares_strict(df_squares, nr_of_squares_in_row):
    list_of_squares = []
    neighbours = []

    for index, square in df_squares.iterrows():

        # If the square itself is not visible you do not need to look for neighbours
        if not (square['Tau'] >= 0 and
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
                        df_squares.loc[neighbour_square_nr, 'Tau'] >= 0):
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
                                 df_squares['Tau'] >= 0)

    return list_of_squares


def eliminate_isolated_squares_relaxed(df_squares, nr_of_squares_in_row):
    list_of_squares = []
    neighbours = []

    for index, square in df_squares.iterrows():

        # If the square itself is not valid you do not need to look for neighbours
        if not (square['Tau'] >= 0 and
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
                        df_squares.loc[neighbour_seqnr, 'Tau'] > 0):
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
