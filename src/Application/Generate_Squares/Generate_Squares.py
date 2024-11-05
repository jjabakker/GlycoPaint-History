import os
import sys
import time

import numpy as np
import pandas as pd

from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')

from src.Application.Generate_Squares.Utilities.Curvefit_and_Plot import (
    compile_duration,
    curve_fit_and_plot
)

from src.Application.Generate_Squares.Utilities.Generate_Squares_Support_Functions import (
    check_experiment_integrity,
    get_square_coordinates,
    calc_variability,
    calculate_density,
    write_np_to_excel,
    calc_area_of_square,
    calc_average_track_count_in_background_squares,
    label_visible_squares,
    create_unique_key_for_squares,
    select_tracks_for_tau_calculation
)

from src.Application.Utilities.General_Support_Functions import (
    save_experiment_to_file,
    format_time_nicely)

from src.Common.Support.DirectoriesAndLocations import (
    delete_files_in_directory,
    get_tau_plots_dir_path)

from src.Common.Support.PaintConfig import get_paint_attribute

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')


def process_project_directory(
        paint_directory: str,
        nr_of_squares_in_row: int,
        min_r_squared: float,
        min_tracks_for_tau: int,
        min_required_density_ratio: float,
        max_allowable_variability: float,
        max_square_coverage: float,
        process_recording_tau: bool = True,
        process_square_tau: bool = True,
        called_from_project: bool = True,
        paint_force: bool = False,
        verbose: bool = False) -> None:
    """
    This function processes all images in a root directory. It calls the function
    'process_all_images_in_paint_directory' for each directory in the root directory.
    """

    nr_experiments_processed = 0
    root_directory = paint_directory

    # --------------------------------------------------------------------------------------------
    # Process all experiments in the project directory
    # --------------------------------------------------------------------------------------------

    paint_logger.info(f"Starting generating squares for all images in {root_directory}")
    paint_logger.info('')
    experiment_dirs = os.listdir(root_directory)
    experiment_dirs.sort()
    for experiment_dir in experiment_dirs:
        if not os.path.isdir(os.path.join(root_directory, experiment_dir)):
            continue
        if 'Output' in experiment_dir:
            continue
        if (os.path.exists(os.path.join(root_directory, experiment_dir)) and
                os.path.exists(os.path.join(root_directory, experiment_dir, 'All Squares.csv')) and
                os.path.exists(os.path.join(root_directory, experiment_dir, 'All Recordings.csv')) and
                os.path.exists(os.path.join(root_directory, experiment_dir, 'All Tracks.csv')) and
                not paint_force):
            paint_logger.info('')
            paint_logger.info(f"Experiment output exists and skipped: {experiment_dir}")
            paint_logger.info('')
            continue
        process_experiment_directory(
            paint_directory=os.path.join(root_directory, experiment_dir),
            nr_of_squares_in_row=nr_of_squares_in_row,
            min_r_squared=min_r_squared,
            min_tracks_for_tau=min_tracks_for_tau,
            min_required_density_ratio=min_required_density_ratio,
            max_allowable_variability=max_allowable_variability,
            max_square_coverage=max_square_coverage,
            process_recording_tau=process_recording_tau,
            process_square_tau=process_square_tau,
            called_from_project=called_from_project,
            verbose=False)
        nr_experiments_processed += 1

    return nr_experiments_processed

def process_experiment_directory(
        paint_directory: str,
        nr_of_squares_in_row: int,
        min_r_squared: float,
        min_tracks_for_tau: int,
        min_required_density_ratio: float,
        max_allowable_variability: float,
        max_square_coverage: float,
        process_recording_tau: bool = True,
        process_square_tau: bool = True,
        called_from_project: bool = True,
        paint_force: bool = False,
        verbose: bool = False) -> None:
    """
    This function processes all images in a paint directory. It reads the experiment file, to find out what
    images need processing
    """

    df_all_squares = pd.DataFrame()
    experiment_path = paint_directory

    # Load from the paint configuration file the parameters that are needed
    plot_to_file = get_paint_attribute('Generate Squares', 'Plot to File')

    time_stamp = time.time()

    # --------------------------------------------------------------------------------------------
    # Read the All Tracks file and add two columns for the square and label numbers
    # --------------------------------------------------------------------------------------------

    df_all_tracks = pd.read_csv(os.path.join(paint_directory, 'All Tracks.csv'))
    if df_all_tracks is None:
        paint_logger.error(f"Could not read the 'All Tracks.csv' file in {paint_directory}")
        sys.exit(1)
    df_all_tracks.set_index('Recording Name', drop=False, inplace=True)
    df_all_tracks['Square Nr'] = 0
    df_all_tracks['Label Nr'] = 0

    # --------------------------------------------------------------------------------------------
    # Read the experiment file, check if it is in the correct format and add the required columns
    # --------------------------------------------------------------------------------------------

    df_experiment = pd.read_csv(os.path.join(paint_directory, 'Experiment TM.csv'))
    if df_experiment is None:
        paint_logger.error(
            f"Function 'process_all_images_in_paint_directory' failed: Likely, {experiment_path} is not a valid directory containing cell image information.")
        sys.exit(1)
    if len(df_experiment) == 0:
        paint_logger.error(
            f"Function 'process_all_images_in_paint_directory' failed: 'Experiment TM.csv' in {experiment_path} is empty")
        sys.exit(1)

    # Confirm the experiment file is in the correct format
    if not check_experiment_integrity(df_experiment):
        paint_logger.error(
            f"Function 'process_all_images_in_paint_directory' failed: The experiment file in {experiment_path} is not in the valid format.")
        sys.exit(1)

    df_experiment = add_columns_to_experiment_file(
        df_experiment, nr_of_squares_in_row, min_tracks_for_tau, min_r_squared, min_required_density_ratio,
        max_allowable_variability)

    # --------------------------------------------------------------------------------------------
    # Determine how many images need processing from the experiment file
    # --------------------------------------------------------------------------------------------

    nr_files = df_all_tracks['Recording Name'].nunique()
    nr_files1 = len(df_experiment)
    if (nr_files1 != nr_files):
        paint_logger.info("All Squares file is not consistent with All Recordings")
    if nr_files <= 0:
        paint_logger.info("No files selected for processing")
        return

    # --------------------------------------------------------------------------------------------
    # Loop though selected images to produce the individual grid_results files
    # --------------------------------------------------------------------------------------------

    current_image_nr = 1
    processed = 0
    df_squares = pd.DataFrame()

    paint_logger.info(f"Processing {nr_files:2d} images in {experiment_path}")

    for index, experiment_row in df_experiment.iterrows():
        recording_name = experiment_row['Ext Recording Name']
        ext_image_path = os.path.join(experiment_path, experiment_row['Ext Recording Name'])

        process = True
        if process:
            # --------------------------------------------------------------------------------------------
            # Process the image
            # --------------------------------------------------------------------------------------------

            if True:
                paint_logger.debug(
                    f"Processing file {current_image_nr} of {nr_files}: {recording_name}")
            else:
                paint_logger.debug(recording_name)

            df_squares, tau, r_squared, density = process_single_image_in_experiment_directory(
                df_all_tracks,
                experiment_row,
                experiment_path,
                ext_image_path,
                recording_name,
                nr_of_squares_in_row,
                min_r_squared,
                min_tracks_for_tau,
                min_required_density_ratio,
                max_allowable_variability,
                process_recording_tau,
                process_square_tau,
                plot_to_file, verbose)

            if df_squares is None:
                paint_logger.error("Aborted with error")
                return None

            # --------------------------------------------------------------------------------------------
            # Now update the experiment_squares file with the results
            # --------------------------------------------------------------------------------------------

            min_track_duration = 0  # ToDo Correct this
            max_track_duration = 10000

            df_squares['Visible'] = (
                    (df_squares['Density Ratio'] >= min_required_density_ratio) &
                    (df_squares['Variability'] <= max_allowable_variability) &
                    (df_squares['Max Track Duration'] >= min_track_duration) &
                    (df_squares['Max Track Duration'] <= max_track_duration)
            )

            nr_total_squares = int(nr_of_squares_in_row * nr_of_squares_in_row)
            nr_visible_squares = len(df_squares[df_squares['Visible']])
            nr_invisible_squares = nr_total_squares - nr_visible_squares
            nr_valid_tau_squares = len(df_squares[df_squares['Tau'] > 0])

            df_experiment.loc[index, 'Nr Total Squares'] = nr_total_squares
            df_experiment.loc[index, 'Nr Visible Squares'] = nr_invisible_squares
            df_experiment.loc[index, 'Nr Invisible Squares'] = nr_invisible_squares

            df_experiment.loc[index, 'Nr Defined Squares'] = nr_valid_tau_squares
            df_experiment.loc[index, 'Nr Rejected Squares'] = nr_total_squares - nr_valid_tau_squares

            df_experiment.loc[index, 'Squares Ratio'] = round(100 * nr_visible_squares / nr_total_squares)
            df_experiment.loc[index, 'Max Squares Ratio'] = max_square_coverage
            df_experiment.loc[index, 'Nr Rejected Squares'] = nr_total_squares - nr_valid_tau_squares

            df_experiment.loc[index, 'Ext Recording Name'] = recording_name
            df_experiment.loc[index, 'Tau'] = tau
            df_experiment.loc[index, 'Density'] = density
            df_experiment.loc[index, 'R Squared'] = round(r_squared, 3)

            df_experiment.loc[index, 'Exclude'] = df_experiment.loc[index, 'Squares Ratio'] >= max_square_coverage

            # Then assign the mean Diffusion Coefficient value to the experiment file    #ToDo - implement this

            df_squares = pd.concat([df_squares, df_squares], ignore_index=True)
            current_image_nr += 1
            processed += 1
        else:
            paint_logger.debug(f"Squares file already up to date: {recording_name}")

        df_all_squares = pd.concat([df_all_squares, df_squares], ignore_index=True)

    # --------------------------------------------------------------------------------------------
    # Save to the tracks file
    # --------------------------------------------------------------------------------------------

    df_all_tracks.to_csv(os.path.join(paint_directory, 'All Tracks.csv'), index=False)

    # --------------------------------------------------------------------------------------------
    # Save the experiment file
    # --------------------------------------------------------------------------------------------

    save_experiment_to_file(df_experiment, os.path.join(experiment_path, "All Recordings.csv"))
    run_time = round(time.time() - time_stamp, 1)
    paint_logger.info(f"Processed  {nr_files:2d} images in {experiment_path} in {format_time_nicely(run_time)}")

    # --------------------------------------------------------------------------------------------
    # Make a unique index and then save the All Squares  file
    # --------------------------------------------------------------------------------------------
    df_all_squares = create_unique_key_for_squares(df_all_squares)
    df_all_squares.to_csv(os.path.join(experiment_path, "All Squares.csv"), index=False)


def process_single_image_in_experiment_directory(
        df_all_tracks: pd.DataFrame,
        experiment_row: pd.Series,
        experiment_path: str,
        recording_path: str,
        recording_name: str,
        nr_of_squares_in_row: int,
        min_r_squared: float,
        min_tracks_for_tau: int,
        min_required_density_ratio: float,
        max_allowable_variability: float,
        process_recording_tau: bool,
        process_square_tau: bool,
        plot_to_file: False,
        verbose: bool = False) -> tuple:
    """
    This function processes a single image in a paint directory. It reads the full-track file from the 'tracks'
    directory and creates a grid of squares. For each square the Tau and Density ratio is calculated. The squares
    are then filtered on visibility. For each square a squares.csv id written to the 'grid' directory.
    """

    tau = 0
    r_squared = 0
    density = 0

    # Empty the plt directory
    delete_files_in_directory(get_tau_plots_dir_path(experiment_path, recording_name))  # TODO - Check this

    df_tracks = df_all_tracks[df_all_tracks['Recording Name'] == recording_name]

    # -----------------------------------------------------------------------------------------------------
    # A df_squares dataframe is generated and, if the process_square_tau flag is set, for every square the
    # Tau and Density are calculated. The results are written to a squares file.
    # -----------------------------------------------------------------------------------------------------

    df_squares, tau_matrix = create_df_squares(
        experiment_row, experiment_path, df_tracks, recording_path, recording_name, nr_of_squares_in_row,
        float(experiment_row['Concentration']), min_r_squared, min_tracks_for_tau, process_square_tau, verbose)

    # ----------------------------------------------------------------------------------------------------
    # Assign labels to the tracks file, so that tracks are assigned to squares
    # ----------------------------------------------------------------------------------------------------

    label_visible_squares(df_squares)

    df_temp = df_squares[df_squares['Label Nr'] != 0]
    for index, experiment_row in df_temp.iterrows():
        square = experiment_row['Square Nr']
        label = experiment_row['Label Nr']
        df_all_tracks.loc[
            (df_all_tracks['Square Nr'] == square) & (
                    df_all_tracks['Recording Name'] == recording_name), 'Label Nr'] = label
        df_all_tracks.loc[
            (df_all_tracks['Square Nr'] == square) & (
                    df_all_tracks['Recording Name'] == recording_name), 'Square Nr'] = square

    # ----------------------------------------------------------------------------------------------------
    # Now do the single mode processing: determine a single Tau and Density per image, i.e. for all squares and return
    # those values
    # ----------------------------------------------------------------------------------------------------

    min_track_duration = 0
    max_track_duration = 10000  # ToDo - Really should come from the user interface
    if process_recording_tau:
        tau, r_squared, density = calc_single_tau_and_density_for_image(
            experiment_path, df_squares, df_tracks, min_tracks_for_tau, min_r_squared, min_required_density_ratio,
            max_allowable_variability, min_track_duration, max_track_duration, recording_name, nr_of_squares_in_row,
            float(experiment_row['Concentration']), plot_to_file=plot_to_file)
    else:
        tau = r_squared = density = 0

    return df_squares, tau, r_squared, density


def calc_single_tau_and_density_for_image(
        experiment_directory: str,
        df_squares: pd.DataFrame,
        df_tracks: pd.DataFrame,
        min_tracks_for_tau: int,
        min_r_squared: float,
        min_required_density_ratio: float,
        max_allowable_variability: float,
        min_track_duration: int,
        max_track_duration: int,
        recording_name: str,
        nr_of_squares_in_row: int,
        concentration: float,
        plot_to_file: bool
) -> tuple:
    """
    This function calculates a single Tau and Density for an image. It does this by considering only the tracks
    in the image
    """

    # Identify the squares that contribute to the Tau calculation

    df_squares_for_single_tau = df_squares[
        (df_squares['Density Ratio'] >= min_required_density_ratio) &
        (df_squares['Variability'] <= max_allowable_variability) &
        (df_squares['Max Track Duration'] >= min_track_duration) &
        (df_squares['Max Track Duration'] <= max_track_duration)
        ]

    # For these squares select from the tracks only those that fall within the squares
    # The following line of code filter the `df_tracks` DataFrame to include only the rows where the
    # `Square Nr` column values are present in the `Square Nr` column of the `df_squares_for_single_tau` DataFrame.

    df_tracks_for_tau = df_tracks[df_tracks['Square Nr'].isin(df_squares_for_single_tau['Square Nr'])]
    nr_of_tracks_for_single_tau = len(df_tracks_for_tau)

    # --------------------------------------------------------------------------------------------
    # Calculate the Tau
    # --------------------------------------------------------------------------------------------

    if nr_of_tracks_for_single_tau < min_tracks_for_tau:
        tau = -1
        r_squared = 0
    else:
        duration_data = compile_duration(df_tracks_for_tau)
        plt_file = os.path.join(get_tau_plots_dir_path(experiment_directory, recording_name), recording_name + ".png")
        tau, r_squared = curve_fit_and_plot(
            plot_data=duration_data, nr_tracks=nr_of_tracks_for_single_tau, plot_max_x=5, plot_title=" ",
            file=plt_file, plot_to_screen=False, plot_to_file=plot_to_file, verbose=False)
        if tau == -2:  # Tau calculation failed
            r_squared = 0
        tau = int(tau)
        if r_squared < min_r_squared:  # Tau was calculated, but not reliable
            tau = -3

    # --------------------------------------------------------------------------------------------
    # Calculate the Density
    # --------------------------------------------------------------------------------------------

    area = calc_area_of_square(nr_of_squares_in_row)
    density = calculate_density(
        nr_tracks=nr_of_tracks_for_single_tau, area=area, time=100, concentration=concentration, magnification=1000)

    return tau, r_squared, density


def create_df_squares(row: pd.Series,
                      experiment_directory: str,
                      df_tracks: pd.DataFrame,
                      recording_path: str,
                      recording_name: str,
                      nr_of_squares_in_row: int,
                      concentration: float,
                      min_r_squared: float,
                      min_tracks_for_tau: int,
                      process_square_tau: bool,
                      verbose: bool) -> pd.DataFrame:
    # --------------------------------------------------------------------------------------------
    # Set up for processing
    # --------------------------------------------------------------------------------------------

    # Create the tau_matrix (and other matrices if verbose is True)
    tau_matrix = np.zeros((nr_of_squares_in_row, nr_of_squares_in_row), dtype=int)
    if verbose:
        count_matrix = np.zeros((nr_of_squares_in_row, nr_of_squares_in_row), dtype=int)
        density_matrix = np.zeros((nr_of_squares_in_row, nr_of_squares_in_row), dtype=int)
        variability_matrix = np.zeros((nr_of_squares_in_row, nr_of_squares_in_row), dtype=int)

    # Reset all label and square numbers in the tracks dataframe
    df_tracks['Square Nr'] = 0
    df_tracks['Label Nr'] = 0

    # Create an empty squares dataframe, that will contain the data for each square
    df_squares = pd.DataFrame()
    nr_total_squares = int(nr_of_squares_in_row * nr_of_squares_in_row)
    square_area = calc_area_of_square(nr_of_squares_in_row)

    # --------------------------------------------------------------------------------------------
    # Generate the data for a square in a row and append it to the squares dataframe
    # --------------------------------------------------------------------------------------------

    for square_seq_nr in range(nr_total_squares):

        # Calculate the squares_row and column number from the sequence number (all are 0-based)
        col_nr = square_seq_nr % nr_of_squares_in_row
        row_nr = square_seq_nr // nr_of_squares_in_row

        # --------------------------------------------------------------------------------------------
        # Determine which tracks fall within the square defined by boundaries x0, y0, x1, y1
        # Create a new dataframe df_tracks_in_square that contains just those tracks
        # --------------------------------------------------------------------------------------------

        x0, y0, x1, y1 = get_square_coordinates(nr_of_squares_in_row, square_seq_nr)
        mask = ((df_tracks['Track X Location'] >= x0) &
                (df_tracks['Track X Location'] < x1) &
                (df_tracks['Track Y Location'] >= y0) &
                (df_tracks['Track Y Location'] < y1))
        df_tracks_in_square = df_tracks[mask]
        df_tracks_in_square.reset_index(drop=True, inplace=True)
        nr_of_tracks_in_square = len(df_tracks_in_square)

        if nr_of_tracks_in_square == 0:

            total_track_duration = 0
            average_long_track = 0
            max_track_duration = 0
            if process_square_tau:
                tau = -1
                r_squared = 0
            else:
                tau = 0
                r_squared = 0
            density = 0
            variability = 0

        else:

            # Assign the tracks to the square.
            df_tracks.loc[mask, 'Square Nr'] = square_seq_nr

            # --------------------------------------------------------------------------------------------
            # Calculate the sum of track durations for the square
            # --------------------------------------------------------------------------------------------

            total_track_duration = sum(df_tracks_in_square['Track Duration'])

            # --------------------------------------------------------------------------------------------
            # Calculate the average of the long tracks for the square
            # The long tracks are defined as the longest 10% of the tracks
            # If the number of tracks is less than 10, the average long track is set on the full set
            # --------------------------------------------------------------------------------------------

            df_tracks_in_square.sort_values(by=['Track Duration'], inplace=True)

            if nr_of_tracks_in_square < 10:
                average_long_track = df_tracks_in_square.iloc[nr_of_tracks_in_square - 1]['Track Duration']
            else:
                percentage = get_paint_attribute('Generate Squares',
                                                 'Fraction of Squares to Determine Background')
                nr_tracks_to_average = round(percentage * nr_of_tracks_in_square)
                average_long_track = df_tracks_in_square.tail(nr_tracks_to_average)['Track Duration'].mean()

            # --------------------------------------------------------------------------------------------
            # Find the maximum track duration. If there are no tracks then set the value to 0
            # --------------------------------------------------------------------------------------------

            max_track_duration = df_tracks_in_square['Track Duration'].max()

            # --------------------------------------------------------------------------------------------
            # Calculate the Tau for the square if requested. Use error codes:
            #   -1: too few points to try to fit
            #   -2: curve fitting tries, but failed
            #   -3: curve fitting succeeded, but R2 is too low
            # --------------------------------------------------------------------------------------------

            if process_square_tau:

                # First decide what tracks to consider for the Tau calculation
                limit_dc = get_paint_attribute('Generate Squares',
                                               'Exclude zero DC tracks from Tau Calculation')
                df_tracks_for_tau = select_tracks_for_tau_calculation(df_tracks_in_square, limit_dc)

                if len(df_tracks_for_tau) < min_tracks_for_tau:  # Too few points to curve fit
                    tau = -1
                    r_squared = 0
                else:
                    duration_data = compile_duration(df_tracks_for_tau)
                    plt_file = os.path.join(get_tau_plots_dir_path(experiment_directory, recording_name),
                                            recording_name + "-square-" + str(square_seq_nr) + ".png")
                    tau, r_squared = curve_fit_and_plot(
                        plot_data=duration_data, nr_tracks=nr_of_tracks_in_square, plot_max_x=5, plot_title=" ",
                        file=plt_file, plot_to_screen=False, plot_to_file=False, verbose=False)
                    if tau == -2:  # Tau calculation failed
                        r_squared = 0
                    if r_squared < min_r_squared:  # Tau was calculated, but not reliable
                        tau = -3
                    tau = int(tau)
            else:
                tau = 0
                r_squared = 0

            # --------------------------------------------------------------------------------------------
            # Calculate the density for the square
            # Note: magnification is hard coded to 1000, just to get an easier to read number
            # --------------------------------------------------------------------------------------------

            density = calculate_density(
                nr_tracks=nr_of_tracks_in_square, area=square_area, time=100, concentration=concentration,
                magnification=1000)

            variability = calc_variability(df_tracks_in_square, square_seq_nr, nr_of_squares_in_row, 10)

        # --------------------------------------------------------------------------------------------
        # Enter the calculated values in the tau, density, and variability matrices
        # --------------------------------------------------------------------------------------------

        tau_matrix[row_nr, col_nr] = int(tau)
        if verbose:
            density_matrix[row_nr, col_nr] = int(density)
            variability_matrix[row_nr, col_nr] = int(variability * 100)
            count_matrix[row_nr, col_nr] = nr_of_tracks_in_square

        # --------------------------------------------------------------------------------------------
        # Create the new squares record to add all the data for this square
        # --------------------------------------------------------------------------------------------

        squares_row = {'Recording Sequence Nr': row['Recording Sequence Nr'],
                       'Ext Recording Name': row['Ext Recording Name'],
                       'Experiment Name': row['Experiment Name'],
                       'Experiment Date': row['Experiment Date'],
                       'Condition Nr': row['Condition Nr'],
                       'Replicate Nr': row['Replicate Nr'],
                       'Square Nr': int(square_seq_nr),
                       'Probe': row['Probe'],
                       'Probe Type': row['Probe Type'],
                       'Cell Type': row['Cell Type'],
                       'Adjuvant': row['Adjuvant'],
                       'Concentration': row['Concentration'],
                       'Row Nr': int(row_nr + 1),
                       'Col Nr': int(col_nr + 1),
                       'Label Nr': 0,
                       'Cell Id': 0,
                       'Nr Spots': row['Nr Spots'],
                       'Nr Tracks': int(nr_of_tracks_in_square),
                       'X0': round(x0, 2),
                       'Y0': round(y0, 2),
                       'X1': round(x1, 2),
                       'Y1': round(y1, 2),
                       'Visible': True,
                       'Variability': round(variability, 2),
                       'Density': round(density, 1),
                       'Density Ratio': 0.0,
                       'Tau': round(tau, 0),
                       'R2': round(r_squared, 2),
                       'Diffusion Coefficient': 0,
                       'Average Long Track Duration': round(average_long_track, 1),
                       'Max Track Duration': round(max_track_duration, 1),
                       'Total Track Duration': round(total_track_duration, 1),
                       }
        # And add it to the squares dataframe
        df_squares = pd.concat([df_squares, pd.DataFrame.from_records([squares_row])])

    # --------------------------------------------------------------------------------------------
    # At this point, the full df_square dataframe exists. Now sone post processing is done
    # --------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------
    # Determine the background tracks count and calculate the density ratio calculation
    # The density ratio can be calculated simply by dividing the tracks in the square by the average tracks
    # because everything else stays the same (no need to calculate the background density itself)
    # --------------------------------------------------------------------------------------------

    background_tracks = calc_average_track_count_in_background_squares(df_squares, int(0.1 * nr_total_squares))

    if background_tracks == 0:
        df_squares['Density Ratio'] = 999.9  # Special code
    else:
        df_squares['Density Ratio'] = round(df_squares['Nr Tracks'] / background_tracks, 1)

    # --------------------------------------------------------------------------------------------
    # Then add the diffusion coefficient to the squares file
    # --------------------------------------------------------------------------------------------

    df_squares.set_index('Square Nr', drop=False, inplace=True)

    df_squares['Diffusion Coefficient'] = 0
    for index, row in df_squares.iterrows():
        square_nr = row['Square Nr']
        x0, y0, x1, y1 = get_square_coordinates(nr_of_squares_in_row, square_nr)
        df_tracks_in_square = df_tracks[
            (df_tracks['Track X Location'] >= x0) &
            (df_tracks['Track X Location'] <= x1) &
            (df_tracks['Track Y Location'] >= y0) &
            (df_tracks['Track Y Location'] <= y1)]
        if len(df_tracks_in_square) > 0:
            dc_mean = df_tracks_in_square['Diffusion Coefficient'].mean()
        else:
            dc_mean = -1
        df_squares.loc[index, 'Diffusion Coefficient'] = int(dc_mean)

    # --------------------------------------------------------------------------------------------
    # Important! Set Square Nr as index, but leave the column
    # --------------------------------------------------------------------------------------------
    df_squares.set_index('Square Nr', inplace=True, drop=False)

    if verbose:
        write_matrices(recording_path, recording_name, tau_matrix, density_matrix, count_matrix, variability_matrix,
                       verbose)

    return df_squares, tau_matrix


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

    # Check if the grid directory exist
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

    :param df_experiment:
    :param nr_of_squares_in_row:
    :param min_tracks_for_tau:
    :param min_r_squared:
    :param min_required_density_ratio:
    :param max_allowable_variability:
    :return:
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
