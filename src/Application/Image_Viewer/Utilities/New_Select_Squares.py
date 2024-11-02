import math

import pandas as pd


def select_squares1(self):
    condition1 = self.df_squares['Density Ratio'] >= self.min_required_density_ratio
    condition2 = self.df_squares['Variability'] <= self.max_allowable_variability
    condition3 = self.df_squares['Max Track Duration'] <= self.min_track_duration
    condition4 = self.df_squares['Max Track Duration'] >= self.max_track_duration

    self.df_squares['Visible'] = condition1 & condition2 & condition3 & condition4

    mode='STRICT'
    nr_of_squares_in_row = math.sqrt(len(self.df_squares))

    if mode == 'STRICT':
        eliminate_isolated_squares_strict1(self.df_squares, nr_of_squares_in_row)
    else:
        eliminate_isolated_squares_relaxed(self.df_squares, nr_of_squares_in_row)

def eliminate_isolated_squares_strict1(df_squares, nr_of_squares_in_row):
    """
    Identifies squares with visible neighbors and updates their visibility status.

    Parameters:
    - df_squares (pd.DataFrame): DataFrame containing squares data with a 'Visible' attribute.
    - nr_of_squares_in_row (int): Number of squares in a row (grid width).

    Returns:
    - list: List of square numbers that are not isolated.
    """

    list_of_squares = []  # Stores square numbers with visible neighbors

    for index, square in df_squares.iterrows():

        # Skip squares that are not initially marked as 'Visible'
        if not square['Visible']:
            continue

        row = square['Row Nr']
        col = square['Col Nr']
        square_nr = square['Square Nr']

        # Determine neighbors based on grid position
        left = (row, max(col - 1, 1))
        right = (row, min(col + 1, nr_of_squares_in_row))
        above = (max(row - 1, 1), col)
        below = (min(row + 1, nr_of_squares_in_row), col)

        # Determine which neighbors to inspect based on boundary conditions
        if row == 1:  # Top row
            neighbours = [right, below] if col == 1 else [left, below] if col == nr_of_squares_in_row else [left, right,
                                                                                                            below]
        elif row == nr_of_squares_in_row:  # Bottom row
            neighbours = [right, above] if col == 1 else [left, above] if col == nr_of_squares_in_row else [left, right,
                                                                                                            above]
        else:  # Middle rows
            neighbours = [right, below, above] if col == 1 else [left, below,
                                                                 above] if col == nr_of_squares_in_row else [left,
                                                                                                             right,
                                                                                                             below,
                                                                                                             above]

        # Check if there are visible neighbors
        has_visible_neighbors = any(
            df_squares.index.contains(int((nb[0] - 1) * nr_of_squares_in_row + (nb[1] - 1))) and
            df_squares.loc[int((nb[0] - 1) * nr_of_squares_in_row + (nb[1] - 1)), 'Visible']
            for nb in neighbours
        )

        # Keep square visible only if it was initially visible and has visible neighbors
        if has_visible_neighbors:
            df_squares.at[square_nr, 'Visible'] = True
            list_of_squares.append(square_nr)
        else:
            df_squares.at[square_nr, 'Visible'] = False

    return list_of_squares



def eliminate_isolated_squares_relaxed(df_squares, nr_of_squares_in_row):
    """
    Updates the 'Visible' status of squares in the DataFrame based on neighboring squares' visibility
    and an additional condition.

    Parameters:
    - df_squares (pd.DataFrame): DataFrame containing squares data with a 'Visible' attribute.
    - nr_of_squares_in_row (int): Number of squares in a row (grid width).

    Returns:
    - pd.DataFrame: Updated DataFrame with 'Visible' status, indicating whether each square has visible neighbors.
    - list: List of square numbers that are not isolated.
    """


    list_of_squares = []  # Stores square numbers with valid neighbors

    for index, square in df_squares.iterrows():

        if not df_squares['Visible']:
            continue

        # Identify the row and column position of the square
        row_nr, col_nr = square['Row Nr'], square['Col Nr']

        # Define potential neighbors in all eight possible directions (left, right, above, below, and diagonals)
        neighbors = [
            (row_nr, max(col_nr - 1, 1)),  # Left
            (row_nr, min(col_nr + 1, nr_of_squares_in_row)),  # Right
            (max(row_nr - 1, 1), col_nr),  # Above
            (min(row_nr + 1, nr_of_squares_in_row), col_nr),  # Below
            (min(row_nr + 1, nr_of_squares_in_row), max(col_nr - 1, 1)),  # Below Left
            (min(row_nr + 1, nr_of_squares_in_row), min(col_nr + 1, nr_of_squares_in_row)),  # Below Right
            (max(row_nr - 1, 1), max(col_nr - 1, 1)),  # Above Left
            (max(row_nr - 1, 1), min(col_nr + 1, nr_of_squares_in_row))  # Above Right
        ]

        # Filter neighbors based on the grid boundaries
        if row_nr == 1:  # Top row
            if col_nr == 1:  # Top-left corner
                neighbors = [neighbors[1], neighbors[3], neighbors[5]]
            elif col_nr == nr_of_squares_in_row:  # Top-right corner
                neighbors = [neighbors[0], neighbors[3], neighbors[4]]
            else:
                neighbors = [neighbors[0], neighbors[1], neighbors[3], neighbors[4], neighbors[5]]
        elif row_nr == nr_of_squares_in_row:  # Bottom row
            if col_nr == 1:  # Bottom-left corner
                neighbors = [neighbors[1], neighbors[2], neighbors[7]]
            elif col_nr == nr_of_squares_in_row:  # Bottom-right corner
                neighbors = [neighbors[0], neighbors[2], neighbors[6]]
            else:
                neighbors = [neighbors[0], neighbors[1], neighbors[2], neighbors[6], neighbors[7]]
        elif col_nr == 1:  # Leftmost column (excluding corners)
            neighbors = [neighbors[1], neighbors[2], neighbors[3], neighbors[5], neighbors[7]]
        elif col_nr == nr_of_squares_in_row:  # Rightmost column (excluding corners)
            neighbors = [neighbors[0], neighbors[2], neighbors[3], neighbors[4], neighbors[6]]

        # Count visible neighbors by checking if they exist in the DataFrame and meet the 'Visible' status
        visible_neighbors = sum(
            (df_squares.index.contains(int((nb[0] - 1) * nr_of_squares_in_row + (nb[1] - 1))) and
             df_squares.loc[int((nb[0] - 1) * nr_of_squares_in_row + (nb[1] - 1)), 'Visible'])
            for nb in neighbors
        )

        # Update 'Visible' status based on the number of visible neighbors and the additional test
        if visible_neighbors > 0 and square['Visible']:
            df_squares.at[square['Square Nr'], 'Visible'] = True
            list_of_squares.append(square['Square Nr'])
        else:
            df_squares.at[square['Square Nr'], 'Visible'] = False

    return df_squares, list_of_squares