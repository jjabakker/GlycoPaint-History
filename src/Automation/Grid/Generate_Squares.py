import os
import sys
import time
from tkinter import *
from tkinter import ttk, filedialog

import numpy as np
import pandas as pd

from src.Automation.Support.Curvefit_and_Plot import (
    compile_duration,
    curve_fit_and_plot)
from src.Automation.Support.Generate_HeatMap import plot_heatmap
from src.Automation.Support.Support_Functions import (
    calc_variability,
    calculate_density,
    get_default_directories,
    get_df_from_file,
    get_grid_defaults_from_file,
    get_square_coordinates,
    read_batch_from_file,
    save_default_directories,
    save_grid_defaults_to_file,
    write_np_to_excel,
    save_squares_to_file,
    save_batch_to_file,
    check_batch_integrity,
    format_time_nicely,
    calc_average_track_count_of_lowest_squares,
    get_area_of_square
)
from src.Common.Support.CommonSupportFunctions import delete_files_in_directory
from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')


class GridDialog:

    def __init__(self, _root):

        # Retrieve the earlier saved parameters from disk, if nothing was saved provide reasonable defaults
        values = get_grid_defaults_from_file()
        nr_squares_in_row = values['nr_squares_in_row']
        min_tracks_for_tau = values['min_tracks_for_tau']
        min_r_squared = values['min_r_squared']
        min_density_ratio = values['min_density_ratio']
        max_variability = values['max_variability']
        max_square_coverage = values['max_square_coverage']
        self.root_directory, self.paint_directory, self.images_directory = get_default_directories()

        _root.title('Batch grid processing')

        content = ttk.Frame(_root)
        frame_parameters = ttk.Frame(
            content, borderwidth=5, relief='ridge', width=200, height=100, padding=(30, 30, 30, 30))
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        # Fill the parameter frame
        lbl_nr_squares = ttk.Label(frame_parameters, text='Nr of Squares in row/col', width=30, anchor=W)
        lbl_min_tracks_for_tau = ttk.Label(frame_parameters, text='Minimum tracks to calculate Tau', width=30, anchor=W)
        lbl_min_r2 = ttk.Label(frame_parameters, text='Min allowable R-squared', width=30, anchor=W)
        lbl_min_density_ratio = ttk.Label(frame_parameters, text='Min density ratio', width=30, anchor=W)
        lbl_max_variability = ttk.Label(frame_parameters, text='Max variability', width=30, anchor=W)
        lbl_max_square_coverage = ttk.Label(frame_parameters, text='Max squares coverage', width=30, anchor=W)

        self.nr_squares_in_row = IntVar(_root, nr_squares_in_row)
        en_nr_squares = ttk.Entry(frame_parameters, textvariable=self.nr_squares_in_row, width=10)

        self.min_tracks_for_tau = IntVar(_root, min_tracks_for_tau)
        en_min_tracks_for_tau = ttk.Entry(frame_parameters, textvariable=self.min_tracks_for_tau, width=10)

        self.min_r_squared = DoubleVar(_root, min_r_squared)
        en_min_r_squared = ttk.Entry(frame_parameters, textvariable=self.min_r_squared, width=10)

        self.min_density_ratio = DoubleVar(_root, min_density_ratio)
        en_min_density_ratio = ttk.Entry(frame_parameters, textvariable=self.min_density_ratio, width=10)

        self.max_variability = DoubleVar(_root, max_variability)
        en_max_variability = ttk.Entry(frame_parameters, textvariable=self.max_variability, width=10)

        self.max_square_coverage = DoubleVar(_root, max_square_coverage)
        en_max_square_coverage = ttk.Entry(frame_parameters, textvariable=self.max_square_coverage, width=10)

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_parameters.grid(column=0, row=0, columnspan=3, rowspan=2, padx=5, pady=5)
        frame_buttons.grid(column=0, row=4, padx=5, pady=5)
        frame_directory.grid(column=0, row=5, padx=5, pady=5)

        lbl_nr_squares.grid(column=0, row=1, padx=5, pady=5)
        lbl_min_tracks_for_tau.grid(column=0, row=2, padx=5, pady=5)
        lbl_min_r2.grid(column=0, row=3, padx=5, pady=5)
        lbl_min_density_ratio.grid(column=0, row=4, padx=5, pady=5)
        lbl_max_variability.grid(column=0, row=5, padx=5, pady=5)
        lbl_max_square_coverage.grid(column=0, row=6, padx=5, pady=5)

        en_nr_squares.grid(column=1, row=1)
        en_min_tracks_for_tau.grid(column=1, row=2)
        en_min_r_squared.grid(column=1, row=3)
        en_min_density_ratio.grid(column=1, row=4)
        en_max_variability.grid(column=1, row=5)
        en_max_square_coverage.grid(column=1, row=6)

        # Fill the button frame

        btn_process = ttk.Button(frame_buttons, text='Process', command=self.process_grid)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.exit_pressed)

        btn_process.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        # Fill the directory frame
        btn_change_dir = ttk.Button(frame_directory, text='Change Directory', width=15, command=self.change_dir)
        self.lbl_directory = ttk.Label(frame_directory, text=self.paint_directory, width=80)

        btn_change_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_directory.grid(column=1, row=0, padx=20, pady=5)

    def change_dir(self):
        paint_directory = filedialog.askdirectory(initialdir=self.paint_directory)
        if len(paint_directory) != 0:
            self.paint_directory = paint_directory
            self.lbl_directory.config(text=paint_directory)

    def exit_pressed(self):
        root.destroy()

    def process_grid(self):

        time_stamp = time.time()

        save_grid_defaults_to_file(
            self.nr_squares_in_row.get(), self.min_tracks_for_tau.get(), self.min_r_squared.get(),
            self.min_density_ratio.get(), self.max_variability.get(), self.max_square_coverage.get())
        save_default_directories(self.root_directory, self.paint_directory, self.images_directory)

        # See if this really is a paint directory or maybe a root directory containing paint directories

        if os.path.isfile(os.path.join(self.paint_directory, 'Batch.csv')):

            process_all_images_in_paint_directory(
                self.paint_directory, self.nr_squares_in_row.get(), self.min_r_squared.get(),
                self.min_tracks_for_tau.get(), self.min_density_ratio.get(), self.max_variability.get(),
                self.max_square_coverage.get(), verbose=False)
            run_time = time.time() - time_stamp

        elif os.path.isfile(os.path.join(self.paint_directory, 'root.txt')):  # Assume it is group directory

            process_all_images_in_root_directory(
                self.paint_directory, self.nr_squares_in_row.get(), self.min_r_squared.get(),
                self.min_tracks_for_tau.get(), self.min_density_ratio.get(), self.max_variability.get(),
                self.max_square_coverage.get(), verbose=False)
            run_time = time.time() - time_stamp
            paint_logger.info(f"Total processing time is {format_time_nicely(run_time)}")
        else:
            run_time = 0
            paint_logger.error('Not an paint directory and not a root directory')

        paint_logger.info(f"Total processing time is {run_time:.1f} seconds")

        # And then exit
        self.exit_pressed()


def process_all_images_in_root_directory(
        root_directory: str,
        nr_of_squares_in_row: int,
        min_r_squared: float,
        min_tracks_for_tau: int,
        min_density_ratio: float,
        max_variability: float,
        max_square_coverage: float,
        verbose: bool):
    """
    This function processes all images in a root directory. It calls the function
    'process_all_images_in_paint_directory' for each directory in the root directory.

    :param root_directory:
    :param nr_of_squares_in_row:
    :param min_r_squared:
    :param min_tracks_for_tau:
    :param min_density_ratio:
    :param max_variability:
    :param max_square_coverage:
    :param verbose:
    :return:
    """

    image_dirs = os.listdir(root_directory)
    image_dirs.sort()
    for image_dir in image_dirs:
        if not os.path.isdir(os.path.join(root_directory, image_dir)):
            continue
        if 'Output' in image_dir:
            continue
        process_all_images_in_paint_directory(
            os.path.join(root_directory, image_dir), nr_of_squares_in_row, min_r_squared, min_tracks_for_tau,
            min_density_ratio, max_variability, max_square_coverage, verbose=False)



def process_all_images_in_paint_directory(
        paint_directory: str,
        nr_of_squares_in_row: int,
        min_r_squared: float,
        min_tracks_for_tau: int,
        min_density_ratio: float,
        max_variability: float,
        max_square_coverage: float,
        verbose: bool = False):

    """
    This function processes all images in a paint directory. It reads the batch file, to find out what
    images need processing

    :param paint_directory:
    :param nr_of_squares_in_row:
    :param min_r_squared:
    :param min_tracks_for_tau:
    :param min_density_ratio:
    :param max_variability:
    :param max_square_coverage:
    :param verbose:
    :return:
    """

    time_stamp = time.time()

    # Read the batch file
    df_batch = read_batch_from_file(os.path.join(paint_directory, "batch.csv"))
    if df_batch is None:
        paint_logger.error(
            f"Function 'process_all_images_in_paint_directory' failed: Likely, {paint_directory} is not a valid directory containing cell image information.")
        sys.exit(1)

    # Confirm the batch file is in the correct format
    if not check_batch_integrity(df_batch):
        paint_logger.error(
            f"Function 'process_all_images_in_paint_directory' failed: The batch file in {paint_directory} is not in the valid format.")
        sys.exit(1)

    df_batch = add_columns_to_batch_file(
        df_batch, nr_of_squares_in_row, min_tracks_for_tau, min_r_squared, min_density_ratio, max_variability)

    # Determine how many images need processing from the batch.csv file
    nr_files = len(df_batch)
    if nr_files <= 0:
        paint_logger.info("No files selected for processing")
        return

    # Loop though selected images to produce the individual grid_results files
    current_image_nr = 1
    processed = 0

    paint_logger.info(f"Processing {nr_files:2d} images in {paint_directory}")

    for index, row in df_batch.iterrows():
        ext_image_name = row["Image Name"] + '-threshold-' + str(row["Threshold"])
        ext_image_path = os.path.join(paint_directory, ext_image_name)
        concentration = row["Concentration"]

        process = True
        if process or image_needs_processing(ext_image_path, ext_image_name):

            if verbose:
                paint_logger.debug(f"Processing file {current_image_nr} of {nr_files}: seq nr: {index} name: {ext_image_name}")
            else:
                paint_logger.debug(ext_image_name)

            df_squares, tau, r_squared = process_single_image_in_paint_directory(
                ext_image_path, ext_image_name, nr_of_squares_in_row, min_r_squared, min_tracks_for_tau,
                min_density_ratio, max_variability, concentration, row["Nr Spots"], row['Batch Sequence Nr'],
                row['Experiment Nr'], row['Experiment Seq Nr'], row['Experiment Date'], row['Experiment Name'], verbose)
            if df_squares is None:
                paint_logger.error("Aborted with error")
                return None

            area = get_area_of_square(nr_of_squares_in_row)
            density = calculate_density(
                nr_tracks=sum(df_squares['Nr Tracks']), area=area, time=100,
                concentration=concentration, magnification=1000)

            nr_defined_squares = len(df_squares[df_squares['Valid Tau']])
            nr_visible_squares = len(df_squares[df_squares['Visible']])
            nr_total_squares = int(nr_of_squares_in_row * nr_of_squares_in_row)
            df_batch.loc[index, 'Nr Total Squares'] = nr_total_squares
            df_batch.loc[index, 'Nr Defined Squares'] = nr_defined_squares
            df_batch.loc[index, 'Nr Visible Squares'] = nr_visible_squares
            df_batch.loc[index, 'Nr Invisible Squares'] = nr_defined_squares - nr_visible_squares
            df_batch.loc[index, 'Squares Ratio'] = round(100 * nr_defined_squares / nr_total_squares)
            df_batch.loc[index, 'Max Squares Ratio'] = max_square_coverage
            df_batch.loc[index, 'Nr Rejected Squares'] = nr_total_squares - nr_defined_squares
            df_batch.loc[index, 'Exclude'] = df_batch.loc[index, 'Squares Ratio'] >= max_square_coverage
            df_batch.loc[index, 'Ext Image Name'] = ext_image_name
            df_batch.loc[index, 'Tau'] = tau
            df_batch.loc[index, 'Density'] = density
            df_batch.loc[index, 'R Squared'] = round(r_squared, 3)

            current_image_nr += 1
            processed += 1

        else:
            paint_logger.debug(f"Squares file already up to date: {ext_image_name}")

    save_batch_to_file(df_batch, os.path.join(paint_directory, "grid_batch.csv"))
    run_time = round(time.time() - time_stamp, 1)
    paint_logger.info(f"Processed  {nr_files:2d} images in {paint_directory} in {format_time_nicely(run_time)}")


def process_single_image_in_paint_directory(
        image_path: str,
        image_name: str,
        nr_of_squares_in_row: int,
        min_r_squared: float,
        min_tracks_for_tau: int,
        min_density_ratio: float,
        max_variability: float,
        concentration: float,
        nr_spots: int,
        batch_seq_nr: int,
        experiment_nr: int,
        experiment_seq_nr: int,
        experiment_date: str,
        experiment_name: str,
        verbose: bool = False) -> tuple:
    """
    This function processes a single image in a paint directory. It reads the full-track file from the 'tracks' directory

    :param image_path:
    :param image_name:
    :param nr_of_squares_in_row:
    :param min_r_squared:
    :param min_tracks_for_tau:
    :param min_density_ratio:
    :param max_variability:
    :param concentration:
    :param nr_spots:
    :param batch_seq_nr:
    :param experiment_nr:
    :param experiment_seq_nr:
    :param experiment_date:
    :param experiment_name:
    :param verbose:
    :return:
    """

    # Empty the plt directory
    delete_files_in_directory(os.path.join(image_path, "plt"))

    # Read the full-track file from the 'tracks' directory
    tracks_file_name = os.path.join(image_path, "tracks", image_name + "-full-tracks.csv")
    df_tracks = get_df_from_file(tracks_file_name, header=0, skip_rows=[1, 2, 3])
    if df_tracks is None:
        paint_logger.error(f"Process Single Image in Paint directory - Tracks file {tracks_file_name} cannot be opened")
        return None

    # A df_squares dataframe is generated and for every square the Tau and Density ratio is calculated
    df_squares, tau_matrix = create_df_squares(
        df_tracks, image_path, image_name, nr_of_squares_in_row, concentration, nr_spots,
        min_r_squared, min_tracks_for_tau, batch_seq_nr, experiment_nr, experiment_seq_nr,
        experiment_date, experiment_name, verbose)

    # Do the filtering, eliminate all squares for which no valid Tau exists
    df_squares = identify_invalid_squares(
        df_squares, min_r_squared, min_tracks_for_tau, verbose)

    # Assign the label numbers to the squares
    df_with_label = df_tracks.copy()
    df_temp = df_squares[df_squares['Label Nr'] != 0]
    for index, row in df_temp.iterrows():
        square = row['Square Nr']
        label = row['Label Nr']
        df_with_label.loc[df_with_label['Square Nr'] == square, 'Label Nr'] = label

    # The tracks dataframe has been changed, so write a copy to file
    new_tracks_file_name = tracks_file_name[:tracks_file_name.find('.csv')] + '_label.csv'
    df_with_label.drop(['NUMBER_SPLITS', 'NUMBER_MERGES', 'TRACK_Z_LOCATION', 'NUMBER_COMPLEX'], axis=1,
                       inplace=True)
    df_with_label.to_csv(new_tracks_file_name, index=False)

    # -------------------------------------------------------------------------------
    # Set the visibility in the df_squares
    # -------------------------------------------------------------------------------

    df_squares['Variability Visible'] = False
    df_squares.loc[df_squares['Variability'] <= round(max_variability, 1), 'Variability Visible'] = True

    df_squares['Density Ratio Visible'] = False
    df_squares.loc[df_squares['Density Ratio'] >= round(min_density_ratio, 1), 'Density Ratio Visible'] = True

    # df_squares, list_of_squares = eliminate_isolated_squares_relaxed(df_squares, nr_of_squares_in_row)

    df_squares['Visible'] = (df_squares['Valid Tau'] &
                             df_squares['Density Ratio Visible'] &
                             df_squares['Variability Visible'] &
                             df_squares['Neighbour Visible'])

    label_nr = 1
    for idx, row in df_squares.iterrows():
        if row['Valid Tau']:
            df_squares.at[idx, 'Label Nr'] = label_nr
            label_nr += 1

    # Write the filtered squares results
    squares_file_name = os.path.join(image_path, "grid", image_name + "-squares.csv")
    save_squares_to_file(df_squares, squares_file_name)

    # Generate the Tau heatmap, but only if there are squares selected
    if len(df_squares) > 0:
        plt_file = os.path.join(image_path, "img", image_name + "-heatmap.png")
        plot_heatmap(tau_matrix, plt_file)

    # Now do the single mode processing: determine a single Tau and Density per image, i.e. for all squares
    tau, r_squared = calc_single_tau_and_density_for_image(
        df_squares, df_tracks, min_tracks_for_tau, min_r_squared, image_path, image_name)

    return df_squares, tau, r_squared

def calc_single_tau_and_density_for_image(
        df_squares: pd.DataFrame,
        df_tracks: pd.DataFrame,
        min_tracks_for_tau: int,
        min_r_squared: float,
        image_path: str,
        image_name: str) -> tuple:

    # Identify the squares that contribute to the Tau calculation
    df_squares_for_single_tau = df_squares[df_squares['Visible']]
    df_tracks_for_tau = df_tracks[df_tracks['Square Nr'].isin(df_squares_for_single_tau['Square Nr'])]
    nr_tracks = df_tracks_for_tau.shape[0]

    # Calculate the Tau
    if nr_tracks < min_tracks_for_tau:
        tau = -1
        r_squared = 0
    else:
        duration_data = compile_duration(df_tracks_for_tau)
        plt_file = image_path + os.sep + "plt" + os.sep + image_name + ".png"
        tau, r_squared = curve_fit_and_plot(
            plot_data=duration_data, nr_tracks=nr_tracks, plot_max_x=5, plot_title=" ",
            file=plt_file, plot_to_screen=False, verbose=False)
        if tau == -2:  # Tau calculation failed
            r_squared = 0
        tau = int(tau)
        if r_squared < min_r_squared:  # Tau was calculated, but not reliable
            tau = -3
    return tau, r_squared


def create_df_squares(
        df_tracks: pd.DataFrame,
        image_path: str,
        image_name: str,
        nr_squares_in_row: int,
        concentration: float,
        nr_spots: int,
        min_r_squared: float,
        min_tracks_for_tau: int,
        seq_nr: int,
        experiment_nr: int,
        experiment_seq_nr: int,
        experiment_date: str,
        experiment_name: str,
        verbose: bool) -> pd.DataFrame:

    # Create the tau_matrix (and other matrices if verbose is True)
    tau_matrix = np.zeros((nr_squares_in_row, nr_squares_in_row), dtype=int)
    if verbose:
        count_matrix = np.zeros((nr_squares_in_row, nr_squares_in_row), dtype=int)
        density_matrix = np.zeros((nr_squares_in_row, nr_squares_in_row), dtype=int)
        variability_matrix = np.zeros((nr_squares_in_row, nr_squares_in_row), dtype=int)

    # Add a label and square column to the tracks dataframe, if it does not already exist, else reset it
    df_tracks['Square Nr'] = 0
    df_tracks['Label Nr'] = 0

    # Create an empty squares dataframe, that will contain the data for each square
    df_squares = pd.DataFrame()

    nr_total_squares = int(nr_squares_in_row * nr_squares_in_row)

    for square_seq_nr in range(nr_total_squares):

        # Calculate the row and column number from the sequence number (all are 0-based)
        col_nr = square_seq_nr % nr_squares_in_row
        row_nr = square_seq_nr // nr_squares_in_row

        # Find the tracks that are within the square defined by boundaries x0, y0, x1, y1
        # Create a new dataframe df_tracks_square that contains just those tracks
        x0, y0, x1, y1 = get_square_coordinates(nr_squares_in_row, square_seq_nr)
        mask = ((df_tracks['TRACK_X_LOCATION'] >= x0) &
                (df_tracks['TRACK_X_LOCATION'] < x1) &
                (df_tracks['TRACK_Y_LOCATION'] >= y0) &
                (df_tracks['TRACK_Y_LOCATION'] < y1))
        df_tracks_square = df_tracks[mask]
        df_tracks_square.reset_index(drop=True, inplace=True)
        nr_tracks = len(df_tracks_square)

        # Assign the tracks to the square.
        if nr_tracks > 0:
            df_tracks.loc[mask, 'Square Nr'] = square_seq_nr

        # Calculate the sum of track durations for the square
        total_track_duration = sum(df_tracks_square['TRACK_DURATION'])

        # Calculate the average of the long tracks for the square
        # The long tracks are defined as the longest 10% of the tracks
        # If the number of tracks is less than 10, the average long track is set on the full set
        if nr_tracks > 0:
            df_tracks_square.sort_values(by=['TRACK_DURATION'], inplace=True)

        if nr_tracks == 0:
            average_long_track = 0
        elif nr_tracks < 10:
            average_long_track = df_tracks_square.iloc[nr_tracks - 1]['TRACK_DURATION']
        else:
            nr_tracks_to_average = round(0.10 * nr_tracks)       # TODO 0.10 is a magic number
            average_long_track = df_tracks_square.tail(nr_tracks_to_average)['TRACK_DURATION'].mean()

        # Calculate the Tau for the square
        if nr_tracks < min_tracks_for_tau:  # Too few points to curve fit
            tau = -1
            r_squared = 0
        else:
            duration_data = compile_duration(df_tracks_square)
            plt_file = os.path.join(image_path, "plt", image_name + "-square-" + str(square_seq_nr) + ".png")
            tau, r_squared = curve_fit_and_plot(
                plot_data=duration_data,  nr_tracks=nr_tracks,  plot_max_x=5, plot_title=" ",
                file=plt_file, plot_to_screen=False, verbose=False)
            if tau == -2:  # Tau calculation failed
                r_squared = 0
            if r_squared < min_r_squared:  # Tau was calculated, but not reliable
                tau = -3
            tau = int(tau)

        area = get_area_of_square(nr_squares_in_row)
        density = calculate_density(
            nr_tracks=nr_tracks, area=area, time=100, concentration=concentration, magnification=1000)

        variability = calc_variability(df_tracks_square, square_seq_nr, nr_squares_in_row, 10)

        # Enter the calculated values in the tau, density, and variability matrices
        tau_matrix[row_nr, col_nr] = int(tau)
        if verbose:
            density_matrix[row_nr, col_nr] = int(density)
            variability_matrix[row_nr, col_nr] = int(variability * 100)
            count_matrix[row_nr, col_nr] = nr_tracks

        # Create the new squares record to add all the data for this square
        row = {'Experiment Date': experiment_date,
               'Ext Image Name': image_name,
               'Experiment Name': experiment_name,
               'Experiment Nr': experiment_nr,
               'Experiment Seq Nr': experiment_seq_nr,
               'Batch Sequence Nr': int(seq_nr),
               'Label Nr': 0,
               'Square Nr': int(square_seq_nr),
               'Row Nr': int(row_nr + 1),
               'Col Nr': int(col_nr + 1),
               'X0': round(x0, 2),
               'X1': round(x1, 2),
               'Y0': round(y0, 2),
               'Y1': round(y1, 2),
               'Nr Spots': int(nr_spots),
               'Nr Tracks': int(nr_tracks),
               'Tau': round(tau, 0),
               'Valid Tau': True,
               'Density': round(density, 1),
               'Average Long Track Duration': round(average_long_track, 1),
               'Total Track Duration': round(total_track_duration, 1),
               'Variability': round(variability, 2),
               'R2': round(r_squared, 2),
               'Density Ratio': 0.0,
               'Cell Id': 0,
               'Visible': True,
               'Neighbour Visible': True,
               'Variability Visible': True,
               'Density Ratio Visible': True
               }

        # And add it to the squares dataframe
        df_squares = pd.concat([df_squares, pd.DataFrame.from_records([row])])

    background_tracks = calc_average_track_count_of_lowest_squares(df_squares,
                                                                   int(0.1 * nr_squares_in_row * nr_squares_in_row))

    # Write the Density Ratio
    if background_tracks == 0:
        df_squares['Density Ratio'] = 999  # Special code
    else:
        # The density RATIO can be calculated simply by dividing the tracks in the square by the average tracks
        # because everything else stays the same (no need to calculate the background density itself)
        df_squares['Density Ratio'] = round(df_squares['Nr Tracks'] / background_tracks, 1)

    # # Number the labels that are visible
    # label_nr = 1
    # for idx, row in df_squares.iterrows():
    #     if row['Valid Tau']:
    #         df_squares.at[idx, 'Label Nr'] = label_nr
    #         label_nr += 1

    # Polish up the table and sort
    df_squares = df_squares.sort_values(by=['Nr Tracks'], ascending=False)

    if verbose:
        write_matrices(image_path, image_name, tau_matrix, density_matrix, count_matrix, variability_matrix, verbose)

    df_squares.set_index('Square Nr', inplace=True, drop=False)
    return df_squares, tau_matrix


def write_matrices(
        image_path: str,
        image_name: str,
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
    dir_name = os.path.join(image_path, "grid")
    if not os.path.exists(dir_name):
        paint_logger.error(f"Function 'write_matrices' failed: Directory {dir_name} does not exists.")
        exit(-1)

    # Write the Tau matrix to file
    if verbose:
        print(f"\n\nThe Tau matrix for image : {image_name}\n")
        print(tau_matrix)
    filename = image_path + os.sep + "grid" + os.sep + image_name + "-tau.xlsx"
    write_np_to_excel(tau_matrix, filename)

    # Write the Density matrix to file
    if verbose:
        print(f"\n\nThe Density matrix for image : {image_name}\n")
        print(tau_matrix)
    filename = image_path + os.sep + "grid" + os.sep + image_name + "-density.xlsx"
    write_np_to_excel(density_matrix, filename)

    # Write the count matrix to file
    if verbose:
        print(f"\n\nThe Count matrix for image: {image_name}\n")
        print(count_matrix)
    filename = image_path + os.sep + "grid" + os.sep + image_name + "-count.xlsx"
    write_np_to_excel(count_matrix, filename)

    # Write the percentage matrix to file
    percentage_matrix = count_matrix / count_matrix.sum() * 100
    percentage_matrix.round(1)
    if verbose:
        print(f"\n\nThe Percentage matrix for image: {image_name}\n")
        with np.printoptions(precision=1, suppress=True):
            print(count_matrix)
    filename = image_path + os.sep + "grid" + os.sep + image_name + "-percentage.xlsx"
    write_np_to_excel(percentage_matrix, filename)

    # Write the variability matrix to file
    if verbose:
        print(f"\n\nThe Variability matrix for image: {image_name}\n")
        print(variability_matrix)
    filename = image_path + os.sep + "grid" + os.sep + image_name + "-variability.xlsx"
    write_np_to_excel(variability_matrix, filename)

    return 0


def identify_invalid_squares(
        df_squares: pd.DataFrame,
        min_r_squared: float,
        min_tracks_for_tau: int,
        verbose: bool) -> pd.DataFrame:

    """

    :param df_squares:
    :param min_r_squared:
    :param min_tracks_for_tau:
    :param verbose:
    :return:
    """


    # Eliminate the squares for which no Tau was calculated, because there were insufficient tracks (tau code as -1)
    original_count = len(df_squares)
    if original_count != 0:
        df_squares.loc[df_squares['Tau'] == -1, 'Valid Tau'] = False
        updated_count = len(df_squares[df_squares['Valid Tau']])
        if verbose:
            paint_logger.debug(f"Started with {original_count} squares")
            paint_logger.debug(
                f"Eliminated {original_count - updated_count} squares with track count was lower than {min_tracks_for_tau} (no Tau calculated): left {updated_count}")
    else:
        updated_count = 0

    # Then eliminate the squares for which Tau was calculated but where it failed
    original_count = updated_count
    if original_count != 0:
        df_squares.loc[df_squares['Tau'] == -2, 'Valid Tau'] = False
        updated_count = len(df_squares[df_squares['Valid Tau']])
        if verbose:
            paint_logger.debug(
                f"Eliminated {original_count - updated_count} squares for which Tau was calculated but failed: left {updated_count}")
    else:
        updated_count = 0


    # Then eliminate the squares for which Tau was calculated but the R2 was too low (tau coded as -3)
    original_count = updated_count
    if original_count != 0:
        df_squares.loc[df_squares['Tau'] == -3, 'Valid Tau'] = False
        updated_count = len(df_squares[df_squares['Valid Tau']])
        if verbose:
            paint_logger.debug(
                f"Eliminated {original_count - updated_count} squares for which the R2 was lower than {min_r_squared}: left {updated_count}")
    else:
        updated_count = 0

    # Polish up the squares table by filling in the Label Nr
    # The Label Nr corresponds to the squares visualised on the image (1-based)
    # The Square number is the original sequence number of the squares (0-based)

    label_nr = 1
    for idx, row in df_squares.iterrows():
        if row['Valid Tau']:
            df_squares.at[idx, 'Label Nr'] = label_nr
            label_nr += 1

    df_squares.set_index('Square Nr', inplace=True)
    df_squares['Square Nr'] = df_squares.index
    df_squares = df_squares.drop(['index'], axis=1, errors='ignore')

    return df_squares


def add_columns_to_batch_file(
        df_batch: pd.DataFrame,
        nr_of_squares_in_row: int,
        min_tracks_for_tau: int,
        min_r_squared: float,
        min_density_ratio: float,
        max_variability: float):

    """
    This function adds columns to the batch file that are needed for the grid processing.
    Only images for which the 'Process' column is set to 'Yes' are processed.

    :param df_batch:
    :param nr_of_squares_in_row:
    :param min_tracks_for_tau:
    :param min_r_squared:
    :param min_density_ratio:
    :param max_variability:
    :return:
    """

    mask = ((df_batch['Process'] == 'Yes') |
            (df_batch['Process'] == 'yes') |
            (df_batch['Process'] == 'Y') |
            (df_batch['Process'] == 'y'))

    df_batch.loc[mask, 'Min Tracks for Tau'] = int(min_tracks_for_tau)
    df_batch.loc[mask, 'Min R Squared'] = min_r_squared
    df_batch.loc[mask, 'Nr Of Squares per Row'] = int(nr_of_squares_in_row)

    df_batch.loc[mask, 'Exclude'] = False
    df_batch.loc[mask, 'Neighbour Setting'] = 'Free'
    df_batch.loc[mask, 'Variability Setting'] = max_variability
    df_batch.loc[mask, 'Density Ratio Setting'] = min_density_ratio

    df_batch.loc[mask, 'Nr Total Squares'] = 0  # Equal to the square of the nr of squares per row
    df_batch.loc[mask, 'Nr Defined Squares'] = 0  # The number of squares for which a Tau was successfully calculated
    df_batch.loc[mask, 'Nr Visible Squares'] = 0  # The number of squares that also meet the density and variability hurdle
    df_batch.loc[mask, 'Nr Invisible Squares'] = 0 # The number of squares that do not meet the density and variability hurdle
    df_batch.loc[mask, 'Nr Rejected Squares'] = 0  # The difference between Nr Defined and Visible squares
    df_batch.loc[mask, 'Max Squares Ratio'] = 0
    df_batch.loc[mask, 'Squares Ratio'] = 0.0
    df_batch.loc[mask, 'Nr Invisible Squares'] = 0

    return df_batch


def image_needs_processing(
        ext_image_path: str,
        ext_image_name: str) -> bool:
    """
    This function checks if the squares file needs to be updated. It does this by comparing the timestamps of the
    tracks and squares files
    :param ext_image_path:
    :param ext_image_name:
    :return:
    """

    squares_file_name = os.path.join(ext_image_path, "grid", ext_image_name + "-squares.csv")
    tracks_file_name = os.path.join(ext_image_path, "tracks", ext_image_name + "-full-tracks.csv")

    if not os.path.isfile(squares_file_name):  # If the squares file does not exist, force processing
        return True

    squares_file_timestamp = os.path.getmtime(squares_file_name)
    tracks_file_timestamp = os.path.getmtime(tracks_file_name)

    if squares_file_timestamp < tracks_file_timestamp:
        return True

    return False



if __name__ == "__main__":
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    GridDialog(root)
    root.mainloop()
