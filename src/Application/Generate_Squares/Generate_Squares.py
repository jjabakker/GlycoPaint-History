import os
import sys
import time
from token import MINUS

import numpy as np
import pandas as pd

from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')

from src.Application.Generate_Squares.Utilities.Create_All_Tracks import create_all_tracks

from src.Application.Generate_Squares.Utilities.Curvefit_and_Plot import (
    compile_duration,
    curve_fit_and_plot,
)

from src.Application.Generate_Squares.Utilities.Generate_Squares_Support_Functions import (
    check_experiment_integrity,
    get_square_coordinates,
    calc_variability,
    calculate_density,
    write_np_to_excel,
    get_df_from_file,
    calc_area_of_square,
    calc_average_track_count_in_background_squares,
    label_visible_squares
)

from src.Application.Utilities.General_Support_Functions import (
    save_squares_to_file,
    save_experiment_to_file,
    format_time_nicely,
    read_experiment_tm_file)

from src.Common.Support.DirectoriesAndLocations import (
    delete_files_in_directory,
    get_tau_plots_dir_path,
    get_tracks_dir_path,
    get_squares_dir_path,
    get_squares_file_path,
    get_tracks_file_path)

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
        generate_all_tracks: bool = True,
        called_from_project: bool = True,
        verbose: bool = False) -> None:
    """
    This function processes all images in a root directory. It calls the function
    'process_all_images_in_paint_directory' for each directory in the root directory.
    """

    root_directory = paint_directory
    # --------------------------------------------------------------------------------------------
    # Start with compiling the All Tracks file if required
    # --------------------------------------------------------------------------------------------

    if generate_all_tracks:
        # Read all tracks files in the directory tree and concatenate them into a single All Tracks
        df_tracks = create_all_tracks(root_directory)
        if df_tracks is None:
            paint_logger.error('All Tracks not generated')
            return

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
        process_experiment_directory(
            os.path.join(root_directory, experiment_dir), nr_of_squares_in_row, min_r_squared, min_tracks_for_tau,
            min_required_density_ratio,
            max_allowable_variability,
            max_square_coverage,
            process_recording_tau=process_recording_tau,
            process_square_tau=process_square_tau,
            generate_all_tracks=generate_all_tracks,
            called_from_project=called_from_project,
            verbose=False)


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
        generate_all_tracks: bool = True,
        called_from_project: bool = True,
        verbose: bool = False) -> None:
    """
    This function processes all images in a paint directory. It reads the experiment file, to find out what
    images need processing
    """

    experiment_path = paint_directory

    # --------------------------------------------------------------------------------------------
    # Start with compiling the All Tracks file if required
    # --------------------------------------------------------------------------------------------

    if generate_all_tracks and not called_from_project:
        # Read all tracks files in the directory tree and concatenate them into a single All Tracks
        df_tracks = create_all_tracks(experiment_path)
        if df_tracks is None:
            paint_logger.error('All Tracks not generated')
            return

    # --------------------------------------------------------------------------------------------
    # Load from the paint configuration file
    # --------------------------------------------------------------------------------------------
    plot_to_file = get_paint_attribute('Generate Squares', 'Plot to File')

    time_stamp = time.time()

    # --------------------------------------------------------------------------------------------
    # Read the experiment file, check if it is in the correct format and add the required columns
    # --------------------------------------------------------------------------------------------

    df_experiment = read_experiment_tm_file(experiment_path)
    if df_experiment is None:
        paint_logger.error(
            f"Function 'process_all_images_in_paint_directory' failed: Likely, {experiment_path} is not a valid directory containing cell image information.")
        sys.exit(1)
    if len(df_experiment) == 0:
        paint_logger.error(
            f"Function 'process_all_images_in_paint_directory' failed: 'experiment_tm.csv' in {experiment_path} is empty")
        sys.exit(1)

    # Confirm the experiment file is in the correct format
    if not check_experiment_integrity(df_experiment):
        paint_logger.error(
            f"Function 'process_all_images_in_paint_directory' failed: The experiment file in {experiment_path} is not in the valid format.")
        sys.exit(1)

    df_experiment = add_columns_to_experiment_file(
        df_experiment, nr_of_squares_in_row, min_tracks_for_tau, min_r_squared, min_required_density_ratio, max_allowable_variability)

    # --------------------------------------------------------------------------------------------
    # Determine how many images need processing from the experiment file
    # --------------------------------------------------------------------------------------------

    nr_files = len(df_experiment)
    if nr_files <= 0:
        paint_logger.info("No files selected for processing")
        return

    # --------------------------------------------------------------------------------------------
    # Loop though selected images to produce the individual grid_results files
    # --------------------------------------------------------------------------------------------

    current_image_nr = 1
    processed = 0

    paint_logger.info(f"Processing {nr_files:2d} images in {experiment_path}")

    for index, row in df_experiment.iterrows():
        ext_recording_name = row['Recording Name'] + '-threshold-' + str(row["Threshold"])
        ext_image_path = os.path.join(experiment_path, row['Ext Recording Name'])
        concentration = row["Concentration"]

        process = True
        if process or image_needs_processing(ext_image_path, ext_recording_name):

            # --------------------------------------------------------------------------------------------
            # Process the image
            # --------------------------------------------------------------------------------------------

            if verbose:
                paint_logger.debug(
                    f"Processing file {current_image_nr} of {nr_files}: seq nr: {index} name: {ext_recording_name}")
            else:
                paint_logger.debug(ext_recording_name)

            df_squares, tau, r_squared, density = process_single_image_in_experiment_directory(
                experiment_path, ext_image_path, ext_recording_name, nr_of_squares_in_row,
                min_r_squared, min_tracks_for_tau, min_required_density_ratio, max_allowable_variability, concentration, row["Nr Spots"],
                row['Recording Sequence Nr'], row['Condition Nr'], row['Replicate Nr'], row['Experiment Date'],
                row['Experiment Name'], process_recording_tau, process_square_tau, plot_to_file, verbose)
            if df_squares is None:
                paint_logger.error("Aborted with error")
                return None

            # --------------------------------------------------------------------------------------------
            # Now update the experiment_squares file with the results
            # --------------------------------------------------------------------------------------------

            min_track_duration = 0         #ToDo Correct this
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
            nr_defined_squares = len(df_squares[df_squares['Valid Tau']])

            df_experiment.loc[index, 'Nr Total Squares'] = nr_total_squares
            df_experiment.loc[index, 'Nr Visible Squares'] = nr_invisible_squares
            df_experiment.loc[index, 'Nr Invisible Squares'] = nr_invisible_squares

            df_experiment.loc[index, 'Nr Defined Squares'] = nr_defined_squares
            df_experiment.loc[index, 'Nr Rejected Squares'] = nr_total_squares - nr_defined_squares

            df_experiment.loc[index, 'Squares Ratio'] = round(100 * nr_visible_squares / nr_total_squares)
            df_experiment.loc[index, 'Max Squares Ratio'] = max_square_coverage
            df_experiment.loc[index, 'Nr Rejected Squares'] = nr_total_squares - nr_defined_squares

            df_experiment.loc[index, 'Ext Recording Name'] = ext_recording_name
            df_experiment.loc[index, 'Tau'] = tau
            df_experiment.loc[index, 'Density'] = density
            df_experiment.loc[index, 'R Squared'] = round(r_squared, 3)

            df_experiment.loc[index, 'Exclude'] = df_experiment.loc[index, 'Squares Ratio'] >= max_square_coverage

            # Then assign the mean Diffusion Coefficient value to the experiment file    #ToDO - implement this
            name = row['Ext Recording Name']

            current_image_nr += 1
            processed += 1
        else:
            paint_logger.debug(f"Squares file already up to date: {ext_recording_name}")

    # --------------------------------------------------------------------------------------------
    # Save the experiment file
    # --------------------------------------------------------------------------------------------

    save_experiment_to_file(df_experiment, os.path.join(experiment_path, "experiment_squares.csv"))
    run_time = round(time.time() - time_stamp, 1)
    paint_logger.info(f"Processed  {nr_files:2d} images in {experiment_path} in {format_time_nicely(run_time)}")


def process_single_image_in_experiment_directory(
        experiment_path: str,
        recording_path: str,
        recording_name: str,
        nr_of_squares_in_row: int,
        min_r_squared: float,
        min_tracks_for_tau: int,
        min_required_density_ratio: float,
        max_allwable_variability: float,
        concentration: float,
        nr_spots: int,
        recording_seq_nr: int,
        condition_nr: int,
        replicate_nr: int,
        experiment_date: str,
        experiment_name: str,
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
    delete_files_in_directory(get_tau_plots_dir_path(experiment_path, recording_name))

    # Read the full-track file from the 'tracks' directory
    tracks_file_path = get_tracks_file_path(experiment_path, recording_name)
    df_tracks = get_df_from_file(tracks_file_path, header=0, skip_rows=[1, 2, 3])
    if df_tracks is None:
        paint_logger.error(f"Process Single Image in Paint directory - Tracks file {tracks_file_path} cannot be opened")
        return None, tau, r_squared, density

    # -----------------------------------------------------------------------------------------------------
    # A df_squares dataframe is generated and, if the process_square_tau flag is set, for every square the
    # Tau and Density are calculated. The results are written to a squares file.
    # -----------------------------------------------------------------------------------------------------

    df_squares, tau_matrix = create_df_squares(
        experiment_path, df_tracks, recording_path, recording_name, nr_of_squares_in_row, concentration, nr_spots,
        min_r_squared, min_tracks_for_tau, recording_seq_nr, condition_nr, replicate_nr, experiment_date,
        experiment_name, process_square_tau, verbose)

    # Mark all squares for which no valid Tau exists: every Tau < 0 is invalid
    df_squares.loc[df_squares['Tau'] < 0, 'Valid Tau'] = False

    # ----------------------------------------------------------------------------------------------------
    # Set the visibility in the df_squares and label the squares that visible (starting with the highest
    # density squares
    # ----------------------------------------------------------------------------------------------------

    # df_squares['Variability Visible'] = False
    # df_squares.loc[df_squares['Variability'] <= round(max_variability, 1), 'Variability Visible'] = True
    #
    # df_squares['Density Ratio Visible'] = False
    # df_squares.loc[df_squares['Density Ratio'] >= round(min_density_ratio, 1), 'Density Ratio Visible'] = True
    #
    # df_squares['Visible'] = (df_squares['Valid Tau'] &
    #                          df_squares['Density Ratio Visible'] &
    #                          df_squares['Variability Visible'] &
    #                          df_squares['Neighbour Visible'])

    # ----------------------------------------------------------------------------------------------------
    # Label the squares and assign labels to fnr_trthe tracks file
    # ----------------------------------------------------------------------------------------------------

    label_visible_squares(df_squares)

    df_with_label = df_tracks.copy()
    df_temp = df_squares[df_squares['Label Nr'] != 0]
    for index, row in df_temp.iterrows():
        square = row['Square Nr']
        label = row['Label Nr']
        df_with_label.loc[df_with_label['Square Nr'] == square, 'Label Nr'] = label

    # The tracks dataframe has been updated with label info, so write a copy to file
    new_tracks_file_name = tracks_file_path[:tracks_file_path.find('.csv')] + '-label.csv'
    df_with_label.to_csv(new_tracks_file_name, index=False)

    # ----------------------------------------------------------------------------------------------------
    # Save the squares file
    # ----------------------------------------------------------------------------------------------------

    squares_file_name = get_squares_file_path(experiment_path, recording_name)
    save_squares_to_file(df_squares, squares_file_name)

    # ----------------------------------------------------------------------------------------------------
    # Now do the single mode processing: determine a single Tau and Density per image, i.e. for all squares and return
    # those values
    # ----------------------------------------------------------------------------------------------------

    min_track_duration = 0
    max_track_duration = 10000
    if process_recording_tau:
        tau, r_squared, density = calc_single_tau_and_density_for_image(
            experiment_path, df_squares, df_tracks, min_tracks_for_tau, min_r_squared, min_required_density_ratio,
            max_allwable_variability, min_track_duration, max_track_duration,recording_name, nr_of_squares_in_row,
            concentration, plot_to_file=plot_to_file)
    else:
        tau = r_squared = density = 0

    return df_squares, tau, r_squared, density


def calc_single_tau_and_density_for_image(
        experiment_directory: str,
        df_squares: pd.DataFrame,
        df_tracks: pd.DataFrame,
        min_tracks_for_tau: int,
        min_r_squared: float,
        min_required_density_ratio,
        max_allowable_variability,
        min_track_duration,
        max_track_duration,
        recording_name: str,
        nr_of_squares_in_row: int,
        concentration: float,
        plot_to_file: bool) -> tuple:
    """
    This function calculates a single Tau and Density for an image. It does this by considering only the tracks
    in the image
    """

    # Identify the squares that contribute to the Tau calculation

    # df_squares_for_single_tau = df_squares[
    #     (df_squares['Nr Tracks'] > 0) &
    #     (df_squares['Neighbour Visible']) &
    #     (df_squares['Duration Visible']) &
    #     (df_squares['Density Ratio Visible'])]

    df_squares_for_single_tau = df_squares[
        (df_squares['Density Ratio'] >= min_required_density_ratio) &
        (df_squares['Variability'] <= max_allowable_variability) &
        (df_squares['Max Track Duration'] >= min_track_duration) &
        (df_squares['Max Track Duration'] <= max_track_duration)
    ]


    # self.min_required_density_ratio, self.max_allowable_variability, self.min_track_duration, self.min_track_duration,
    # self. max_track_duration
    #
    # min_required_density_ratio,
    # max_allowable_variability,
    # min_track_duration,
    # min_track_duration,
    # max_track_duration,

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


def create_df_squares(experiment_directory: str,
                      df_tracks: pd.DataFrame,
                      recording_path: str,
                      recording_name: str,
                      nr_of_squares_in_row: int,
                      concentration: float,
                      nr_spots: int,
                      min_r_squared: float,
                      min_tracks_for_tau: int,
                      seq_nr: int,
                      experiment_nr: int,
                      experiment_seq_nr: int,
                      experiment_date: str,
                      experiment_name: str,
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
            #   -2: curve fitttng tries, but failed
            #   -3: curve fitting succeeded, but R2 is too low
            # --------------------------------------------------------------------------------------------

            if process_square_tau:
                if nr_of_tracks_in_square < min_tracks_for_tau:  # Too few points to curve fit
                    tau = -1
                    r_squared = 0
                else:
                    duration_data = compile_duration(df_tracks_in_square)
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

        squares_row = {'Recording Sequence Nr': int(seq_nr),
                       'Ext Recording Name': recording_name,
                       'Experiment Name': experiment_name,
                       'Experiment Date': experiment_date,
                       'Condition Nr': experiment_nr,
                       'Replicate Nr': experiment_seq_nr,
                       'Square Nr': int(square_seq_nr),
                       'Row Nr': int(row_nr + 1),
                       'Col Nr': int(col_nr + 1),
                       'Label Nr': 0,
                       'Cell Id': 0,
                       'Nr Spots': int(nr_spots),
                       'Nr Tracks': int(nr_of_tracks_in_square),
                       'X0': round(x0, 2),
                       'Y0': round(y0, 2),
                       'X1': round(x1, 2),
                       'Y1': round(y1, 2),
                       'Visible': True,
                       'Variability': round(variability, 2),
                       'Density': round(density, 1),
                       'Density Ratio': 0.0,
                       'Valid Tau': True,
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


# def mark_squares_with_invalid_tau(
#         df_squares: pd.DataFrame,
#         min_r_squared: float,
#         min_tracks_for_tau: int,
#         verbose: bool) -> pd.DataFrame:
#     """
#
#     :param df_squares:
#     :param min_r_squared:
#     :param min_tracks_for_tau:
#     :param verbose:
#     :return:
#
#     """
#
#     just_do_it_simply = True
#     if just_do_it_simply:
#         df_squares.loc[df_squares['Tau'] < 0, 'Valid Tau'] = False
#         return df_squares
#
#     # Eliminate the squares for which no Tau was calculated, because there were insufficient tracks (tau code as -1)
#     original_count = len(df_squares)
#     if original_count != 0:
#         df_squares.loc[df_squares['Tau'] == -1, 'Valid Tau'] = False
#         updated_count = len(df_squares[df_squares['Valid Tau']])
#         if verbose:
#             paint_logger.debug(f"Started with {original_count} squares")
#             paint_logger.debug(
#                 f"Eliminated {original_count - updated_count} squares with track count was lower than {min_tracks_for_tau} (no Tau calculated): left {updated_count}")
#     else:
#         updated_count = 0
#
#
#     # Then eliminate the squares for which Tau was calculated but where it failed
#     original_count = updated_count
#     if original_count != 0:
#         df_squares.loc[df_squares['Tau'] == -2, 'Valid Tau'] = False
#         updated_count = len(df_squares[df_squares['Valid Tau']])
#         if verbose:
#             paint_logger.debug(
#                 f"Eliminated {original_count - updated_count} squares for which Tau was calculated but failed: left {updated_count}")
#     else:
#         updated_count = 0
#
#     # Then eliminate the squares for which Tau was calculated but the R2 was too low (tau coded as -3)
#     original_count = updated_count
#     if original_count != 0:
#         df_squares.loc[df_squares['Tau'] == -3, 'Valid Tau'] = False
#         updated_count = len(df_squares[df_squares['Valid Tau']])
#         if verbose:
#             paint_logger.debug(
#                 f"Eliminated {original_count - updated_count} squares for which the R2 was lower than {min_r_squared}: left {updated_count}")
#     else:
#         updated_count = 0
#
#     # Polish up the squares table by filling in the Label Nr
#     # The Label Nr corresponds to the squares visualised on the image (1-based)
#     # The Square number is the original sequence number of the squares (0-based)
#
#     label_nr = 1
#     for idx, row in df_squares.iterrows():
#         if row['Valid Tau']:
#             df_squares.at[idx, 'Label Nr'] = label_nr
#             label_nr += 1
#
#     df_squares.set_index('Square Nr', inplace=True)
#     df_squares['Square Nr'] = df_squares.index
#     df_squares = df_squares.drop(['index'], axis=1, errors='ignore')
#
#     return df_squares


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


def image_needs_processing(
        experiment_path: str,
        recording_name: str) -> bool:
    """
    This function checks if the squares file needs to be updated. It does this by comparing the timestamps of the
    tracks and squares files
    :param experiment_path:
    :param recording_name:
    :return:
    """

    squares_file_name = os.path.join(get_squares_dir_path(experiment_path, recording_name),
                                     recording_name + "-squares.csv")
    tracks_file_name = os.path.join(get_tracks_dir_path(experiment_path, recording_name),
                                    recording_name + "-tracks.csv")

    if not os.path.isfile(squares_file_name):  # If the squares file does not exist, force processing
        return True

    squares_file_timestamp = os.path.getmtime(squares_file_name)
    tracks_file_timestamp = os.path.getmtime(tracks_file_name)

    if squares_file_timestamp < tracks_file_timestamp:
        return True

    return False
