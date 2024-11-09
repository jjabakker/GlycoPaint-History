from src.Application.Generate_Squares.Utilities.Generate_Squares_Support_Functions import label_visible_squares


def select_squares_for_display_do_the_work(self):
    """
    Select squares based on defined conditions for density, variability, and track duration,
    and apply visibility rules based on neighborhood states.
    """

    # Define the conditions for squares to be visible
    self.df_squares['Selected'] = (
            (self.df_squares['Density Ratio'] >= self.min_required_density_ratio) &
            (self.df_squares['Variability'] <= self.max_allowable_variability) &
            (self.df_squares['Max Track Duration'] >= self.min_track_duration) &
            (self.df_squares['Max Track Duration'] <= self.max_track_duration)
    )

    self.df_squares['Selected'] = (
            (self.df_squares['Selected']) &
            (self.df_squares['Tau'] > 0)
    )

    # Eliminate isolated squares based on neighborhood rules
    if self.neighbour_mode == 'Strict':
        select_squares_strict(self.df_squares, self.nr_of_squares_in_row)
    elif self.neighbour_mode == 'Relaxed':
        select_squares_relaxed(self.df_squares, self.nr_of_squares_in_row)

    # Label visible squares, so that it is always a range starting from 1
    label_visible_squares(self.df_squares)


def select_squares_strict(df_squares, nr_of_squares_in_row):
    """
    Identifies squares with visible neighbors in a strict manner and updates their visibility status.
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
