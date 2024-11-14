import os
import sys
import time

import numpy as np
import pandas as pd

from src.Application.Recording_Viewer.Select_Squares import (
    select_squares_with_parameters,
    label_selected_squares_and_tracks)
from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')

from src.Application.Generate_Squares.Curvefit_and_Plot import (
    compile_duration,
    curve_fit_and_plot
)

from src.Application.Generate_Squares.Generate_Squares_Support_Functions import (
    check_experiment_integrity,
    get_square_coordinates,
    calc_variability,
    calculate_density,
    calc_area_of_square,
    calc_average_track_count_in_background_squares,
    create_unique_key_for_squares,
    create_unique_key_for_tracks,
    extra_constraints_on_tracksfor_tau_calculation,
    add_columns_to_experiment
)

from src.Application.Utilities.General_Support_Functions import (
    format_time_nicely)

from src.Common.Support.DirectoriesAndLocations import (
    delete_files_in_directory,
    get_tau_plots_dir_path)

from src.Common.Support.PaintConfig import get_paint_attribute

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')


def process_project(
        project_path: str,
        select_parameters: dict,
        nr_of_squares_in_row: int,
        min_r_squared: float,
        min_tracks_for_tau: int,
        process_recording_tau: bool = True,
        process_square_tau: bool = True,
        paint_force: bool = False,
        verbose: bool = False) -> None:
    """
    This function processes all images in a Project. It calls the function 'process_experiment' for each Experiment
    """

    nr_experiments_processed = 0

    # --------------------------------------------------------------------------------------------
    # Process all experiments in the project directory
    # --------------------------------------------------------------------------------------------

    paint_logger.info(f"Starting generating squares for all recordings in {project_path}")
    paint_logger.info('')
    experiment_dirs = os.listdir(project_path)
    experiment_dirs.sort()
    for experiment_dir in experiment_dirs:

        # Skip if not a directory or if it is the Output directory
        if not os.path.isdir(os.path.join(project_path, experiment_dir)):
            continue
        if 'Output' in experiment_dir:
            continue

        # Look at the time tags and decide if reprocessing is needed. Always process when the paint_force flag is set
        if (os.path.exists(os.path.join(project_path, experiment_dir)) and
                os.path.exists(os.path.join(project_path, experiment_dir, 'All Squares.csv')) and
                os.path.exists(os.path.join(project_path, experiment_dir, 'All Recordings.csv')) and
                os.path.exists(os.path.join(project_path, experiment_dir, 'All Tracks.csv')) and
                not paint_force):
            paint_logger.info('')
            paint_logger.info(f"Experiment output exists and skipped: {experiment_dir}")
            paint_logger.info('')
            continue

        # Process the experiment
        process_experiment(
            os.path.join(project_path, experiment_dir),
            select_parameters=select_parameters,
            nr_of_squares_in_row=nr_of_squares_in_row,
            min_r_squared=min_r_squared,
            min_tracks_for_tau=min_tracks_for_tau,
            process_recording_tau=process_recording_tau,
            process_square_tau=process_square_tau,
            verbose=False)
        nr_experiments_processed += 1

    return nr_experiments_processed


def process_experiment(
        experiment_path: str,
        select_parameters: dict,
        nr_of_squares_in_row: int,
        min_r_squared: float,
        min_tracks_for_tau: int,
        process_recording_tau: bool = True,
        process_square_tau: bool = True,
        paint_force: bool = False,
        verbose: bool = False) -> None:
    """
    This function processes all Recordings in an Experiment. It reads the experiment file to find out what
    Recordings need processing
    """

    df_all_squares = pd.DataFrame()

    # Load from the paint configuration file the parameters that are needed
    plot_to_file = get_paint_attribute('Generate Squares', 'Plot to File') or ""
    plot_max = get_paint_attribute('Generate Squares', 'Plot Max') or 5

    time_stamp = time.time()

    # --------------------------------------------------------------------------------------------
    # Read the All Tracks file and add (or reinitialise two columns for the square and label numbers
    # --------------------------------------------------------------------------------------------

    df_all_tracks = pd.read_csv(os.path.join(experiment_path, 'All Tracks.csv'))
    if df_all_tracks is None:
        paint_logger.error(f"Could not read the 'All Tracks.csv' file in {experiment_path}")
        sys.exit(1)
    df_all_tracks = create_unique_key_for_tracks(df_all_tracks)
    if df_all_tracks is None:
        paint_logger.error(f"Could not read the 'All Tracks.csv' file in {experiment_path}")
        sys.exit(1)
    df_all_tracks['Square Nr'] = None
    df_all_tracks['Label Nr'] = None

    # --------------------------------------------------------------------------------------------
    # Read the All Recordings file, check if it is in the correct format and add the required columns
    # --------------------------------------------------------------------------------------------

    df_experiment = pd.read_csv(os.path.join(experiment_path, 'All Recordings.csv'))
    if df_experiment is None:
        paint_logger.error(
            f"Function 'process_experiment' failed: Likely, {experiment_path} is not a valid  \
            directory containing cell image information.")
        sys.exit(1)
    if len(df_experiment) == 0:
        paint_logger.error(
            f"Function 'process_experiment' failed: 'All Recordings.csv' in {experiment_path} \
            is empty")
        sys.exit(1)

    # Confirm the experiment is in the correct format
    if not check_experiment_integrity(df_experiment):
        paint_logger.error(
            f"Function 'process_experiment' failed: The experiment file in {experiment_path} is \
            not in the valid format.")
        sys.exit(1)

    # Add some parameters that the user just specified to the experiment
    df_experiment = add_columns_to_experiment(
        df_experiment,
        nr_of_squares_in_row,
        min_tracks_for_tau,
        min_r_squared,
        select_parameters['min_required_density_ratio'],
        select_parameters['max_allowable_variability'])

    # Determine how many Recordings are in the files
    nr_files = df_all_tracks['Ext Recording Name'].nunique()
    nr_files1 = len(df_experiment)
    if nr_files1 != nr_files:
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

    nr_of_recordings_to_process = len(df_experiment[df_experiment['Process'].isin(['Yes', 'y', 'Y'])])
    paint_logger.info(f"Processing {nr_of_recordings_to_process:2d} images in {experiment_path}")

    for index, experiment_row in df_experiment.iterrows():

        # Skip if not selected for processing
        if experiment_row['Process'] not in ['Yes', 'yes', 'y', 'Y']:
            continue

        recording_name = experiment_row['Ext Recording Name']
        recording_path = os.path.join(experiment_path, experiment_row['Ext Recording Name'])

        process = True
        if process:

            # --------------------------------------------------------------------------------------------
            # Process the Recording
            # --------------------------------------------------------------------------------------------

            paint_logger.debug(f"Processing file {current_image_nr} of {nr_of_recordings_to_process}: {recording_name}")

            df_squares, tau, r_squared, density = process_recording(
                df_all_tracks,
                select_parameters,
                experiment_row,
                experiment_path,
                recording_path,
                recording_name,
                nr_of_squares_in_row,
                min_r_squared,
                min_tracks_for_tau,
                process_recording_tau,
                process_square_tau,
                plot_to_file,
                plot_max,
                verbose)

            if df_squares is None:
                paint_logger.error("Aborted with error")
                return None

            # --------------------------------------------------------------------------------------------
            # Now update the Experiment with the results
            # --------------------------------------------------------------------------------------------

            df_experiment.at[index, 'Ext Recording Name'] = recording_name
            df_experiment.at[index, 'Tau'] = tau
            df_experiment.at[index, 'Density'] = density
            df_experiment.at[index, 'R Squared'] = round(r_squared, 3)

            current_image_nr += 1
            processed += 1
        else:
            paint_logger.debug(f"Squares file already up to date: {recording_name}")

        df_all_squares = pd.concat([df_all_squares, df_squares], ignore_index=True)

    # --------------------------------------------------------------------------------------------
    # Save to the All Tracks file (the square and label columns have been updated)
    # --------------------------------------------------------------------------------------------

    df_all_tracks.to_csv(os.path.join(experiment_path, 'All Tracks.csv'), index=False)

    # --------------------------------------------------------------------------------------------
    # Save the Experiment file
    # --------------------------------------------------------------------------------------------

    df_experiment.to_csv(os.path.join(experiment_path, "All Recordings.csv"))
    run_time = round(time.time() - time_stamp, 1)
    paint_logger.info(f"Processed  {nr_files:2d} images in {experiment_path} in {format_time_nicely(run_time)}")

    # --------------------------------------------------------------------------------------------
    # Make a unique index and then save the All Squares  file
    # --------------------------------------------------------------------------------------------
    df_all_squares = create_unique_key_for_squares(df_all_squares)
    df_all_squares.to_csv(os.path.join(experiment_path, "All Squares.csv"), index=False)


def process_recording(
        df_all_tracks: pd.DataFrame,
        select_parameters: dict,
        experiment_row: pd.Series,
        experiment_path: str,
        recording_path: str,
        recording_name: str,
        nr_of_squares_in_row: int,
        min_r_squared: float,
        min_tracks_for_tau: int,
        process_recording_tau: bool,
        process_square_tau: bool,
        plot_to_file: False,
        plot_max: int = 5,
        verbose: bool = False) -> tuple:
    """
    This function processes a single Recording in an Experiment. It reads the full-track file from the 'tracks'
    directory and creates a grid of squares. For each square, the Tau and Density ratio is calculated. The squares
    are then filtered on visibility.
    """

    # Create the Plot directory if needed
    if plot_to_file:
        plot_dir = os.path.join(experiment_path, 'Plot')
        if not os.path.exists(plot_dir):
            os.makedirs(plot_dir)
        else:
            delete_files_in_directory(plot_dir)

    # Look at squares for the recording, note that at this time Label Nr and Square Nr are not assigned, but not needed
    df_recording_tracks = df_all_tracks[df_all_tracks['Ext Recording Name'] == recording_name]

    # -----------------------------------------------------------------------------------------------------
    # A df_squares dataframe is generated and, if the process_square_tau flag is set, for every square the
    # Tau and Density are calculated. The results are stored in 'All Squares'.
    # -----------------------------------------------------------------------------------------------------

    df_squares, tau_matrix = process_squares(
        experiment_row,
        experiment_path,
        recording_path,
        df_all_tracks,
        df_recording_tracks,
        recording_name,
        nr_of_squares_in_row,
        float(experiment_row['Concentration']),
        min_r_squared,
        min_tracks_for_tau,
        process_square_tau,
        plot_to_file,
        plot_max,
        verbose)

    # ----------------------------------------------------------------------------------------------------
    # Assign labels in All Squares, so that selected tracks are assigned to squares.
    # This is a slow process - see if it can be done more efficiently
    # ----------------------------------------------------------------------------------------------------

    generate_labels_but_very_slow = True
    if generate_labels_but_very_slow:

        # Label just the squares that have a valid Tau
        select_squares_with_parameters(
            df_squares=df_squares,
            select_parameters=select_parameters,
            nr_of_squares_in_row=nr_of_squares_in_row,
            only_valid_tau=True)
        label_selected_squares_and_tracks(df_squares, df_all_tracks)

        # Refresh df_recording_tracks now to pick up Label and Square Nrs
        df_recording_tracks = df_all_tracks[df_all_tracks['Ext Recording Name'] == recording_name]

    # ----------------------------------------------------------------------------------------------------
    # Now do the single mode processing: determine a single Tau and Density per image, i.e., for all squares and return
    # those values
    # ----------------------------------------------------------------------------------------------------

    if process_recording_tau:
        tau, r_squared, density = calculate_tau_and_density_for_recording(
            recording_path,
            df_recording_tracks,
            min_tracks_for_tau,
            min_r_squared,
            recording_name,
            nr_of_squares_in_row,
            float(experiment_row['Concentration']),
            df_squares,
            select_parameters,
            plot_to_file=plot_to_file,
            plot_max=plot_max)
    else:
        tau = r_squared = density = 0

    return df_squares, tau, r_squared, density


def process_squares(
        experiment_row: pd.Series,
        experiment_path: str,
        recording_path: str,
        df_all_tracks: pd.DataFrame,
        df_recording_tracks: pd.DataFrame,
        recording_name: str,
        nr_of_squares_in_row: int,
        concentration: float,
        min_r_squared: float,
        min_tracks_for_tau: int,
        process_square_tau: bool,
        plot_to_file: bool,
        plot_max: int,
        verbose: bool) -> pd.DataFrame:

    # --------------------------------------------------------------------------------------------
    # Set up for processing
    # --------------------------------------------------------------------------------------------

    # # Look at squares for the recording
    # df_recording_tracks = df_all_tracks[df_all_tracks['Recording Name'] == recording_name]

    # Create the tau_matrix (and other matrices if verbose is True)
    tau_matrix = np.zeros((nr_of_squares_in_row, nr_of_squares_in_row), dtype=int)

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

        squares_row, tau = process_square(
            experiment_row,
            experiment_path,
            recording_path,
            df_all_tracks,
            df_recording_tracks,
            recording_name,
            nr_of_squares_in_row,
            concentration,
            min_r_squared,
            min_tracks_for_tau,
            process_square_tau,
            square_area,
            square_seq_nr,
            row_nr,
            col_nr,
            plot_to_file,
            plot_max,
            verbose)

        # And add it to the squares dataframe and the tau to the tau_matrix
        df_squares = pd.concat([df_squares, pd.DataFrame.from_records([squares_row])])
        tau_matrix[row_nr, col_nr] = int(tau)

    # --------------------------------------------------------------------------------------------
    # At this point, the full df_square dataframe exists. Now some post-processing is done
    # Determine the background tracks count and calculate the density ratio calculation
    # The density ratio can be calculated simply by dividing the tracks in the square by the average tracks
    # because everything else stays the same (no need to calculate the background density itself)
    # --------------------------------------------------------------------------------------------

    nr_tracks_in_background = calc_average_track_count_in_background_squares(df_squares, int(0.1 * nr_total_squares))

    if nr_tracks_in_background == 0:
        df_squares['Density Ratio'] = 999.9  # Special code
    else:
        df_squares['Density Ratio'] = round(df_squares['Nr Tracks'] / nr_tracks_in_background, 1)

    return df_squares, tau_matrix


def process_square(
    experiment_row: pd.Series,
    experiment_path: str,
    recording_path: str,
    df_all_tracks: pd.DataFrame,
    df_recording_tracks: pd.DataFrame,
    recording_name: str,
    nr_of_squares_in_row: int,
    concentration: float,
    min_r_squared: float,
    min_tracks_for_tau: int,
    process_square_tau: bool,
    square_area: float,
    square_seq_nr: int,
    row_nr: int,
    col_nr: int,
    plot_to_file: bool,
    plot_max: int,
    verbose: bool) -> pd.Series:


    # Determine which tracks fall within the square defined by boundaries x0, y0, x1, y1
    x0, y0, x1, y1 = get_square_coordinates(nr_of_squares_in_row, square_seq_nr)
    mask = ((df_recording_tracks['Track X Location'] >= x0) &
            (df_recording_tracks['Track X Location'] < x1) &
            (df_recording_tracks['Track Y Location'] >= y0) &
            (df_recording_tracks['Track Y Location'] < y1))
    df_tracks_in_square = df_recording_tracks[mask]
    df_all_tracks.loc[df_tracks_in_square['Unique Key'], 'Square Nr'] = int(square_seq_nr)

    # Provide reasonable values for squares not containing any tracks
    nr_of_tracks_in_square = len(df_tracks_in_square)
    if nr_of_tracks_in_square == 0:
        total_track_duration = 0
        average_long_track = 0
        max_track_duration = 0
        r_squared = 0
        tau = -1 if process_square_tau else 0
        density = 0
        variability = 0
        dc_mean = 0

    else:

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
            fraction = get_paint_attribute('Generate Squares',
                                             'Fraction of Squares to Determine Background') or 0.1
            nr_tracks_to_average = round(fraction * nr_of_tracks_in_square)
            average_long_track = df_tracks_in_square.tail(nr_tracks_to_average)['Track Duration'].mean()

        # --------------------------------------------------------------------------------------------
        # Find the maximum track duration
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

            df_tracks_for_tau = extra_constraints_on_tracksfor_tau_calculation(df_tracks_in_square)

            if len(df_tracks_for_tau) < min_tracks_for_tau:  # Too few points to curve fit
                tau = -1
                r_squared = 0
            else:
                duration_data = compile_duration(df_tracks_for_tau)
                plt_file = os.path.join(experiment_path, 'Plot', recording_name + '-' + str(square_seq_nr) + "-curve-fit.png")
                tau, r_squared = curve_fit_and_plot(
                    plot_data=duration_data,
                    nr_tracks=nr_of_tracks_in_square,
                    plot_max_x=plot_max,
                    plot_title=" ",
                    file=plt_file,
                    plot_to_screen=False,
                    plot_to_file=plot_to_file,
                    verbose=False)
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

        # --------------------------------------------------------------------------------------------
        # Calculate the variability for the square
        # --------------------------------------------------------------------------------------------

        variability = calc_variability(df_tracks_in_square, square_seq_nr, nr_of_squares_in_row, 10)

        # --------------------------------------------------------------------------------------------
        # Calculate the diffusion coefficient for the square
        # --------------------------------------------------------------------------------------------

        dc_mean = df_tracks_in_square['Diffusion Coefficient'].mean()


    # Create the new squares record to add all the data for this square
    squares_row = {'Recording Sequence Nr': experiment_row['Recording Sequence Nr'],
                   'Ext Recording Name': experiment_row['Ext Recording Name'],
                   'Experiment Name': experiment_row['Experiment Name'],
                   'Experiment Date': experiment_row['Experiment Date'],
                   'Condition Nr': experiment_row['Condition Nr'],
                   'Replicate Nr': experiment_row['Replicate Nr'],
                   'Square Nr': int(square_seq_nr),
                   'Probe': experiment_row['Probe'],
                   'Probe Type': experiment_row['Probe Type'],
                   'Cell Type': experiment_row['Cell Type'],
                   'Adjuvant': experiment_row['Adjuvant'],
                   'Concentration': experiment_row['Concentration'],
                   'Threshold': experiment_row['Threshold'],
                   'Row Nr': int(row_nr + 1),
                   'Col Nr': int(col_nr + 1),
                   'Label Nr': 0,
                   'Cell Id': 0,
                   'Nr Spots': experiment_row['Nr Spots'],
                   'Nr Tracks': int(nr_of_tracks_in_square),
                   'X0': round(x0, 2),
                   'Y0': round(y0, 2),
                   'X1': round(x1, 2),
                   'Y1': round(y1, 2),
                   'Selected': True,
                   'Variability': round(variability, 2),
                   'Density': round(density, 1),
                   'Density Ratio': 0.0,
                   'Tau': round(tau, 0),
                   'R2': round(r_squared, 2),
                   'Diffusion Coefficient': round(dc_mean, 0),
                   'Average Long Track Duration': round(average_long_track, 1),
                   'Max Track Duration': round(max_track_duration, 1),
                   'Total Track Duration': round(total_track_duration, 1),
                   }

    return squares_row, tau


def calculate_tau_and_density_for_recording(
        experiment_directory: str,
        df_recording_tracks: pd.DataFrame,
        min_tracks_for_tau: int,
        min_r_squared: float,
        recording_name: str,
        nr_of_squares_in_row: int,
        concentration: float,
        df_squares: pd.DataFrame,
        select_parameters: dict,
        plot_to_file: bool,
        plot_max: int = 5
) -> tuple:
    """
    This function calculates a single Tau and Density for a Recording. It does this by considering all the tracks
    in the image that meet the selection criteria.
    Note that also squares are included for which no square Tau could be calculated (provided they meet the selection
    criteria). The Tau and Density are calculated for the entire image, not for individual squares.
    """

    # Within that recording use all the selected squares. Note: no need to filter out squares with Ta < 0
    select_squares_with_parameters(
        df_squares=df_squares,
        select_parameters=select_parameters,
        nr_of_squares_in_row=nr_of_squares_in_row,
        only_valid_tau=False)
    df_squares_for_single_tau = df_squares[df_squares['Selected']]

    # Select only the tracks that fall within these squares.
    # The following code filters df_tracks to include rows where Square Nr values match those
    # in df_squares_for_single_tau

    df_tracks_for_tau = df_recording_tracks[
        df_recording_tracks['Square Nr'].isin(df_squares_for_single_tau['Square Nr'])]
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
            plot_data=duration_data,
            nr_tracks=nr_of_tracks_for_single_tau,
            plot_max_x=5,
            plot_title=" ",
            file=plt_file,
            plot_to_screen=False,
            plot_to_file=plot_to_file,
            verbose=False)
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