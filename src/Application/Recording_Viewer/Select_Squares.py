
def select_squares_with_parameters (df_squares, select_parameters, nr_of_squares_in_row, only_valid_tau):

    select_squares_actual(
        df_squares,
        select_parameters['min_required_density_ratio'],
        select_parameters['max_allowable_variability'],
        select_parameters['min_track_duration'],
        select_parameters['max_track_duration'],
        select_parameters['neighbour_mode'],
        nr_of_squares_in_row,
        only_valid_tau= only_valid_tau)

def select_squares(self, only_valid_tau=True):
    """
    Wrapper function to select squares based on defined conditions for density, variability, and track duration,
    No need to pass on individual parameters.
    """

    select_squares_actual(
        self.df_squares,
        self.min_required_density_ratio,
        self.max_allowable_variability,
        self.min_track_duration,
        self.max_track_duration,
        self.neighbour_mode,
        self.nr_of_squares_in_row,
        only_valid_tau=only_valid_tau)

def select_squares_actual(
    df_squares,
    min_required_density_ratio,
    max_allowable_variability,
    min_track_duration,
    max_track_duration,
    neighbour_mode,
    nr_of_squares_in_row,
    only_valid_tau=True):

    """
    Select squares based on defined conditions for density, variability, and track duration,
    and apply visibility rules based on neighborhood states.
    """

    # Define the conditions for squares to be visible
    df_squares['Selected'] = (
            (df_squares['Density Ratio'] >= min_required_density_ratio) &
            (df_squares['Variability'] <= max_allowable_variability) &
            (df_squares['Max Track Duration'] >= min_track_duration) &
            (df_squares['Max Track Duration'] <= max_track_duration)
    )

    if only_valid_tau:
        df_squares['Selected'] = (
                (df_squares['Selected']) &
                (df_squares['Tau'] > 0)
        )

    # Eliminate isolated squares based on neighborhood rules
    if neighbour_mode == 'Free':
        pass
    elif neighbour_mode == 'Strict':
        select_squares_strict(df_squares, nr_of_squares_in_row)
    elif neighbour_mode == 'Relaxed':
        select_squares_relaxed(df_squares, nr_of_squares_in_row)
    else:
        raise ValueError(f"Neighbour mode '{neighbour_mode}' not recognized.")

    # Label visible squares, so that there is always a range from 1 to nr_selected squares
    label_visible_squares(df_squares)


def select_squares_strict(df_squares, nr_of_squares_in_row):
    """
    Identifies squares with visible neighbors in strict mode and updates their Selected status.
    """
    list_of_squares = []

    for index, square in df_squares.iterrows():
        if not square['Selected']:
            continue

        row, col = square['Row Nr'], square['Col Nr']
        square_nr = square['Square Nr']

        # Define neighboring squares based on position
        neighbours = get_strict_neighbours(row, col, nr_of_squares_in_row)

        # Check if there are visible neighbors
        has_visible_neighbors = False
        for nb in neighbours:
            # Calculate the neighbor index
            neighbor_index = int((nb[0] - 1) * nr_of_squares_in_row + (nb[1] - 1))

            # Check if the neighbor exists and is visible
            if neighbor_index in df_squares.index and df_squares.loc[neighbor_index, 'Selected']:
                has_visible_neighbors = True
                break  # Exit early if any visible neighbor is found

        # Update visibility based on visible neighbors
        df_squares.at[square_nr, 'Selected'] = has_visible_neighbors
        if has_visible_neighbors:
            list_of_squares.append(square_nr)

    return df_squares, list_of_squares


def select_squares_relaxed(df_squares, nr_of_squares_in_row):
    """
    Updates visibility of squares based on relaxed neighborhood conditions.
    """
    list_of_squares = []

    for index, square in df_squares.iterrows():
        if not square['Selected']:
            continue

        row, col = square['Row Nr'], square['Col Nr']
        square_nr = square['Square Nr']

        # Define neighboring squares in all eight directions for relaxed conditions
        neighbours = get_relaxed_neighbours(row, col, nr_of_squares_in_row)

        # Count visible neighbors
        visible_neighbors = 0
        for nb in neighbours:
            # Calculate the neighbor index
            neighbor_index = int((nb[0] - 1) * nr_of_squares_in_row + (nb[1] - 1))

            # Check if the neighbor exists and is visible
            if neighbor_index in df_squares.index and df_squares.loc[neighbor_index, 'Selected']:
                visible_neighbors += 1

        # Update 'Selected' based on initial visibility and neighbors' visibility
        df_squares.at[square_nr, 'Selected'] = visible_neighbors > 0 and square['Selected']
        if visible_neighbors > 0:
            list_of_squares.append(square_nr)

    return df_squares, list_of_squares


def get_strict_neighbours(row, col, nr_of_squares_in_row):
    """
    Returns neighboring positions for strict neighborhood rule.
    """
    left = (row, max(col - 1, 1))
    right = (row, min(col + 1, nr_of_squares_in_row))
    above = (max(row - 1, 1), col)
    below = (min(row + 1, nr_of_squares_in_row), col)

    if row == 1:
        return [right, below] if col == 1 else \
            [left, below] if col == nr_of_squares_in_row else \
                [left, right, below]
    elif row == nr_of_squares_in_row:
        return [right, above] if col == 1 else \
            [left, above] if col == nr_of_squares_in_row else \
                [left, right, above]
    else:
        return [right, below, above] if col == 1 else \
            [left, below, above] if col == nr_of_squares_in_row else \
                [left, right, below, above]


def get_relaxed_neighbours(row, col, nr_of_squares_in_row):
    """
    Returns all eight possible neighboring positions for relaxed neighborhood rule.
    """
    return [
        (row, max(col - 1, 1)),  # Left
        (row, min(col + 1, nr_of_squares_in_row)),  # Right
        (max(row - 1, 1), col),  # Above
        (min(row + 1, nr_of_squares_in_row), col),  # Below
        (min(row + 1, nr_of_squares_in_row), max(col - 1, 1)),  # Below Left
        (min(row + 1, nr_of_squares_in_row), min(col + 1, nr_of_squares_in_row)),  # Below Right
        (max(row - 1, 1), max(col - 1, 1)),  # Above Left
        (max(row - 1, 1), min(col + 1, nr_of_squares_in_row))  # Above Right
    ]


def label_visible_squares(df_squares):
    # Sort by 'Nr Tracks' in descending order
    df_squares.sort_values(by=['Nr Tracks'], inplace=True, ascending=False)
    df_squares.set_index('Square Nr', drop=False, inplace=True)

    # Initialize label number
    label_nr = 1

    # Iterate through rows and label selected ones
    for idx, row in df_squares.iterrows():
        if row['Selected']:
            df_squares.at[idx, 'Label Nr'] = label_nr
            label_nr += 1
        else:
            df_squares.at[idx, 'Label Nr'] = None  # Clear label for unselected rows

    # Restore original order
    df_squares.sort_index(inplace=True)

