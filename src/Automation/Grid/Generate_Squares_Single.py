import os
import time
from tkinter import *
from tkinter import ttk, filedialog

import pandas as pd

from src.Automation.Support.Curvefit_and_Plot import (
    compile_duration,
    curve_fit_and_plot)
from src.Automation.Support.Logger_Config import paint_logger, change_file_handler, paint_logger_file_name_assigned
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
    save_squares_to_file,
    save_batch_to_file,
    check_batch_integrity,
    format_time_nicely
)
from src.Automation.Support.Grid_Support_Functions import (
    calc_average_track_count_of_lowest_squares
)

if not paint_logger_file_name_assigned:
    change_file_handler('Generate Squares Single.log')


class GridDialog:

    def __init__(self, root):

        # Retrieve the earlier saved parameters from disk, if nothing was saved provide reasonable defaults
        (nr_of_squares_in_row,
         min_tracks_for_tau,
         min_r_squared,
         min_density_ratio,
         max_variability,
         max_square_coverage) = get_grid_defaults_from_file()
        self.root_directory, self.paint_directory, self.images_directory = get_default_directories()

        root.title('Batch grid processing')

        content = ttk.Frame(root)
        frame_parameters = ttk.Frame(content, borderwidth=5, relief='ridge',
                                     width=200, height=100, padding=(30, 30, 30, 30))
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        # Fill the parameter frame
        lbl_nr_squares = ttk.Label(frame_parameters, text='Nr of Squares in row/col', width=30, anchor=W)
        lbl_min_tracks_for_tau = ttk.Label(frame_parameters, text='Minimum tracks to calculate Tau', width=30, anchor=W)
        lbl_min_r2 = ttk.Label(frame_parameters, text='Min allowable R-squared', width=30, anchor=W)
        lbl_max_variability = ttk.Label(frame_parameters, text='Max variability', width=30, anchor=W)
        lbl_max_square_coverage = ttk.Label(frame_parameters, text='Max squares coverage', width=30, anchor=W)

        self.nr_of_squares_in_row = IntVar(root, nr_of_squares_in_row)
        en_nr_squares = ttk.Entry(frame_parameters, textvariable=self.nr_of_squares_in_row, width=10)

        self.min_tracks_for_tau = IntVar(root, min_tracks_for_tau)
        en_min_tracks_for_tau = ttk.Entry(frame_parameters, textvariable=self.min_tracks_for_tau, width=10)

        self.min_r_squared = DoubleVar(root, min_r_squared)
        en_min_r_squared = ttk.Entry(frame_parameters, textvariable=self.min_r_squared, width=10)

        self.min_density_ratio = DoubleVar(root, min_density_ratio)

        self.max_variability = DoubleVar(root, max_variability)
        en_max_variability = ttk.Entry(frame_parameters, textvariable=self.max_variability, width=10)

        self.max_square_coverage = DoubleVar(root, max_square_coverage)
        en_max_square_coverage = ttk.Entry(frame_parameters, textvariable=self.max_square_coverage, width=10)

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_parameters.grid(column=0, row=0, columnspan=3, rowspan=2, padx=5, pady=5)
        frame_buttons.grid(column=0, row=4, padx=5, pady=5)
        frame_directory.grid(column=0, row=5, padx=5, pady=5)

        lbl_nr_squares.grid(column=0, row=1, padx=5, pady=5)
        lbl_min_tracks_for_tau.grid(column=0, row=2, padx=5, pady=5)
        lbl_min_r2.grid(column=0, row=3, padx=5, pady=5)
        lbl_max_variability.grid(column=0, row=5, padx=5, pady=5)
        lbl_max_square_coverage.grid(column=0, row=6, padx=5, pady=5)

        en_nr_squares.grid(column=1, row=1)
        en_min_tracks_for_tau.grid(column=1, row=2)
        en_min_r_squared.grid(column=1, row=3)
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

        save_grid_defaults_to_file(self.nr_of_squares_in_row.get(),
                                   self.min_tracks_for_tau.get(),
                                   self.min_r_squared.get(),
                                   self.min_density_ratio.get(),
                                   self.max_variability.get(),
                                   self.max_square_coverage.get())
        save_default_directories(self.root_directory, self.paint_directory, self.images_directory)

        # See if this really is a paint directory or maybe a root directory containing paint directories

        if os.path.isfile(os.path.join(self.paint_directory, 'Batch.csv')):

            process_images_in_paint_directory_single_mode(self.paint_directory,
                                                          self.nr_of_squares_in_row.get(),
                                                          self.min_r_squared.get(),
                                                          self.min_tracks_for_tau.get(),
                                                          self.max_variability.get(),
                                                          self.max_square_coverage.get(),
                                                          verbose=False)
            run_time = time.time() - time_stamp
            paint_logger.info(f"Total processing time is {format_time_nicely(run_time)}")
        elif os.path.isfile(os.path.join(self.paint_directory, 'root.txt')):  # Assume it is group directory

            process_images_in_root_directory_single_mode(self.paint_directory,
                                                         self.nr_of_squares_in_row.get(),
                                                         self.min_r_squared.get(),
                                                         self.min_tracks_for_tau.get(),
                                                         self.max_variability.get(),
                                                         self.max_square_coverage.get(),
                                                         verbose=False)
            run_time = time.time() - time_stamp
            paint_logger.info(f"Total processing time is {format_time_nicely(run_time)}")
        else:
            paint_logger.error('Not a paint directory and not a root directory')

        # And then exit
        self.exit_pressed()


def process_images_in_root_directory_single_mode(root_directory,
                                                 nr_of_squares_in_row,
                                                 min_r_squared,
                                                 min_tracks_for_tau,
                                                 max_variability,
                                                 max_square_coverage,
                                                 verbose):
    image_dirs = os.listdir(root_directory)
    image_dirs.sort()
    for image_dir in image_dirs:
        if not os.path.isdir(os.path.join(root_directory, image_dir)):
            continue
        if 'Output' in image_dir:
            continue
        process_images_in_paint_directory_single_mode(os.path.join(root_directory, image_dir),
                                                      nr_of_squares_in_row,
                                                      min_r_squared,
                                                      min_tracks_for_tau,
                                                      max_variability,
                                                      max_square_coverage,
                                                      verbose=False)





def process_single_image_in_paint_directory(image_path,
                                            image_name,
                                            nr_of_squares_in_row,
                                            min_r_squared,
                                            min_tracks_for_tau,
                                            min_density_ratio,
                                            max_variability,
                                            concentration,
                                            nr_spots,
                                            batch_seq_nr,
                                            experiment_nr,
                                            experiment_seq_nr,
                                            experiment_date,
                                            experiment_name,
                                            verbose=False):
    """

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

    # Read the full-track file from the 'tracks' directory (use special reading parameters!)
    tracks_file_name = os.path.join(image_path, "tracks", image_name + "-full-tracks.csv")
    df_tracks = get_df_from_file(tracks_file_name, header=0, skip_rows=[1, 2, 3])
    if df_tracks is None:
        paint_logger.debug(f"Process Single Image in Paint directory - Tracks file {tracks_file_name} cannot be opened")
        return

    # Here the actual calculation work is done: df_squares is generated
    df_squares = create_df_squares(df_tracks,
                                   image_name,
                                   nr_of_squares_in_row,
                                   concentration,
                                   nr_spots,
                                   batch_seq_nr,
                                   experiment_nr,
                                   experiment_seq_nr,
                                   experiment_date,
                                   experiment_name,
                                   verbose)

    # -------------------------------------------------------------------------------
    # Determine the density ratio
    # -------------------------------------------------------------------------------

    # Calculate the average of the lowest average_count_squares
    # TODO The hardcoded 0.1 should be changed

    background_tracks = calc_average_track_count_of_lowest_squares(df_squares,
                                                                   int(0.1 * nr_of_squares_in_row * nr_of_squares_in_row))

    # Write the Density Ratio
    if background_tracks == 0:
        df_squares['Density Ratio'] = 999  # Special code
    else:
        # The density RATIO can be calculated simply by dividing the tracks in the square by the average tracks
        # because everything else stays the same (no need to calculate the background density itself)
        df_squares['Density Ratio'] = round(df_squares['Nr Tracks'] / background_tracks, 1)

    label_nr = 1
    for idx, row in df_squares.iterrows():
        if row['Valid Tau']:
            df_squares.at[idx, 'Label Nr'] = label_nr
            label_nr += 1

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

    df_squares['Visible'] = (df_squares['Density Ratio Visible'] &
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

    # Identify the squares that contribute to the Tau calculation
    df_squares_for_tau = df_squares[df_squares['Visible']]
    df_tracks_for_tau = df_tracks[df_tracks['Square Nr'].isin(df_squares_for_tau['Square Nr'])]
    nr_tracks = df_tracks_for_tau.shape[0]

    # Calculate the Tau
    if nr_tracks < min_tracks_for_tau:
        tau = -1
        r_squared = 0
    else:
        duration_data = compile_duration(df_tracks_for_tau)
        plt_file = image_path + os.sep + "plt" + os.sep + image_name + ".png"
        tau, r_squared = curve_fit_and_plot(plot_data=duration_data,
                                            nr_tracks=nr_tracks,
                                            plot_max_x=5,
                                            plot_title=" ",
                                            file=plt_file, plot_to_screen=False, verbose=False)
        if tau == -2:  # Tau calculation failed
            r_squared = 0
        tau = int(tau)
        if r_squared < min_r_squared:  # Tau was calculated, but not reliable
            tau = -3

    if verbose:
        print(tau)
    return tau, r_squared, df_squares


def create_df_squares(df_tracks,
                      image_name,
                      nr_squares_in_row,
                      concentration,
                      nr_spots,
                      seq_nr,
                      experiment_nr,
                      experiment_seq_nr,
                      experiment_date,
                      experiment_name,
                      verbose):
    # Add a label and square column to the tracks dataframe, if it does not already exist, else reset it
    if 'Square Nr' in df_tracks.columns:
        df_tracks['Square Nr'] = 0
    else:
        df_tracks['Square Nr'] = 0

    if 'Label' in df_tracks.columns:
        df_tracks['Label Nr'] = 0
    else:
        df_tracks['Label Nr'] = 0

    # Create an empty squares dataframe, that will contain the data for each square
    df_squares = pd.DataFrame()

    nr_total_squares = int(nr_squares_in_row * nr_squares_in_row)

    for i in range(nr_total_squares):

        # Calculate the row and column number from the sequence number (all are 0-based)
        col_nr = i % nr_squares_in_row
        row_nr = i // nr_squares_in_row

        # Find the tracks that are within the square defined by boundaries x0, y0, x1, y1
        # Create a new dataframe that contains just those tracks
        x0, y0, x1, y1 = get_square_coordinates(nr_squares_in_row, i)
        mask = ((df_tracks['TRACK_X_LOCATION'] >= x0) &
                (df_tracks['TRACK_X_LOCATION'] < x1) &
                (df_tracks['TRACK_Y_LOCATION'] >= y0) &
                (df_tracks['TRACK_Y_LOCATION'] < y1))
        df_tracks_square = df_tracks[mask]
        df_tracks_square.reset_index(drop=True, inplace=True)
        nr_tracks = len(df_tracks_square)

        # Assign the tracks to the square.
        if nr_tracks > 0:
            df_tracks.loc[mask, 'Square Nr'] = i

        # --------------------------------------------
        # Calculate the sum of track durations
        # --------------------------------------------

        total_track_duration = sum(df_tracks_square['TRACK_DURATION'])

        # ----------------------------------------
        # Calculate the average of the long tracks
        # ----------------------------------------

        if nr_tracks > 0:
            df_tracks_square.sort_values(by=['TRACK_DURATION'], inplace=True)
        if nr_tracks == 0:
            average_long_track = 0
        elif nr_tracks < 10:
            average_long_track = df_tracks_square.iloc[nr_tracks - 1]['TRACK_DURATION']
        else:
            nr_tracks_to_average = round(0.10 * nr_tracks)
            average_long_track = df_tracks_square.tail(nr_tracks_to_average)['TRACK_DURATION'].mean()

        # ----------------------------------------------------------------------------------
        # To calculate the density use the actual surface coordinates.
        # Assume 2000 frames (100 sec) -  need to check - this is not always the case
        # Multiply by 1000 to get an easier  number
        # Area is calculated with Fiji info:
        #     Width:  82.0864 microns(512)
        #     Height: 82.0864 microns(512)
        # The area of a square then is (82.0854/nr_of_squares_in_row)^2
        #
        # To normalise concentration we divide by the supplied concentration
        # ----------------------------------------------------------------------------------

        area = (x1 - x0) * (y1 - y0)
        density = calculate_density(nr_tracks=nr_tracks,
                                    area=area,
                                    time=100,
                                    concentration=concentration,
                                    magnification=1000)

        # Enter the calculated values in the tau, density, and variability matrices
        variability = calc_variability(df_tracks_square, i, nr_squares_in_row, 10)

        # Create the new squares record to add
        row = {'Experiment Date': experiment_date,
               'Ext Image Name': image_name,
               'Experiment Name': experiment_name,
               'Experiment Nr': experiment_nr,
               'Experiment Seq Nr': experiment_seq_nr,
               'Batch Sequence Nr': int(seq_nr),
               'Label Nr': 0,
               'Square Nr': int(i),
               'Row Nr': int(row_nr + 1),
               'Col Nr': int(col_nr + 1),
               'X0': round(x0, 2),
               'X1': round(x1, 2),
               'Y0': round(y0, 2),
               'Y1': round(y1, 2),
               'Nr Spots': int(nr_spots),
               'Nr Tracks': int(nr_tracks),
               'Tau': 0,
               'Valid Tau': True,
               'Density': round(density, 1),
               'Average Long Track Duration': round(average_long_track, 1),
               'Total Track Duration': round(total_track_duration, 1),
               'Variability': round(variability, 2),
               'Density Ratio': 0.0,
               'Cell Id': 0,
               'Visible': True,
               'Neighbour Visible': True,
               'Variability Visible': True,
               'Density Ratio Visible': True
               }

        # And add it to the squares dataframe
        df_squares = pd.concat([df_squares, pd.DataFrame.from_records([row])])

    # Polish up the table and sort
    df_squares = df_squares.sort_values(by=['Nr Tracks'], ascending=False)

    df_squares.set_index('Square Nr', inplace=True, drop=False)
    # df_squares.index.names = ['index_sq_nr']
    return df_squares


def add_columns_to_batch_file(df_batch,
                              nr_of_squares_in_row,
                              min_tracks_for_tau,
                              min_r_squared,
                              max_variability):
    mask = ((df_batch['Process'] == 'Yes') |
            (df_batch['Process'] == 'yes') |
            (df_batch['Process'] == 'Y') |
            (df_batch['Process'] == 'y'))
    df_batch.loc[mask, 'Min Tracks for Tau'] = int(min_tracks_for_tau)
    df_batch.loc[mask, 'Min R Squared'] = min_r_squared
    df_batch.loc[mask, 'Nr Of Squares per Row'] = int(nr_of_squares_in_row)

    df_batch['Exclude'] = False
    df_batch['Neighbour Setting'] = 'Free'
    df_batch['Variability Setting'] = max_variability
    df_batch['Density Ratio Setting'] = df_batch['Min Density Ratio']
    df_batch['Nr Total Squares'] = 0  # Defined by the nr of squares per row
    df_batch['Nr Defined Squares'] = 0  # The number of squares for which a Tau was successfully calculated
    df_batch['Nr Visible Squares'] = 0  # The number of squares that also meet the density and variability hurdle
    df_batch['Nr Invisible Squares'] = 0
    df_batch['Nr Rejected Squares'] = 0  # The difference between Nr Defined and Visible squares
    df_batch['Max Squares Ratio'] = 0
    df_batch['Squares Ratio'] = 0.0
    df_batch['Nr Invisible Squares'] = 0

    return df_batch


def process_images_in_paint_directory_single_mode(paint_directory,
                                                  nr_of_squares_in_row,
                                                  min_r_squared,
                                                  min_tracks_for_tau,
                                                  max_variability,
                                                  max_square_coverage,
                                                  verbose=False):
    """
    :param paint_directory:
    :param nr_of_squares_in_row:
    :param min_r_squared:
    :param min_tracks_for_tau:
    :param max_variability:
    :param max_square_coverage:
    :param verbose:
    :return:
    """

    time_stamp = time.time()

    df_batch = read_batch_from_file(os.path.join(paint_directory, "batch.csv"))
    if df_batch is None:
        paint_logger.error(
            f"Function 'process_images_in_paint_directory' failed: Likely, {paint_directory} is not a valid directory containing cell image information.")
        exit(1)

    if not check_batch_integrity(df_batch):
        paint_logger.error(
            f"Function 'process_images_in_paint_directory' failed: The batch file in {paint_directory} is not in the valid format.")
        return

    # Needed in some cases, unclear why
    df_batch['Batch Sequence Nr'] = df_batch['Batch Sequence Nr'].astype(int)
    df_batch['Experiment Seq Nr'] = df_batch['Experiment Seq Nr'].astype(int)
    df_batch['Experiment Nr'] = df_batch['Experiment Nr'].astype(int)
    df_batch['Experiment Date'] = df_batch['Experiment Date'].astype(int)
    df_batch['Threshold'] = df_batch['Threshold'].astype(int)

    # Need to make sure that there is a meaningful index
    df_batch.set_index('Batch Sequence Nr', inplace=True, drop=False)

    df_batch = add_columns_to_batch_file(df_batch,
                                         nr_of_squares_in_row,
                                         min_tracks_for_tau,
                                         min_r_squared,
                                         max_variability)

    # Determine what images need processing from the batch.csv file
    nr_files = len(df_batch)
    if nr_files <= 0:
        paint_logger.info("\nNo files selected for processing")
        return

    # Loop though selected images to produce the individual grid_results files
    i = 1
    processed = 0

    paint_logger.info(f"Processing {nr_files:2d} images in {paint_directory}")

    for index, row in df_batch.iterrows():
        ext_image_name = row["Image Name"] + '-threshold-' + str(row["Threshold"])
        ext_image_path = os.path.join(paint_directory, ext_image_name)
        concentration = row["Concentration"]

        squares_file_name = os.path.join(ext_image_path, "grid", ext_image_name + "-squares.csv")
        tracks_file_name = os.path.join(ext_image_path, "tracks", ext_image_name + "-full-tracks.csv")

        process = False
        if not os.path.isfile(squares_file_name):
            process = True
        else:
            squares_file_timestamp = os.path.getmtime(squares_file_name)

        # Get the time stamp of the tracks_file
        if not os.path.isfile(tracks_file_name):
            paint_logger.error(f"process_single_image_in_paint_directory: tracks file {tracks_file_name} not found")
            continue
        else:
            tracks_file_timestamp = os.path.getmtime(tracks_file_name)

        # Force processing
        process = True
        if process or squares_file_timestamp < tracks_file_timestamp:

            if verbose:
                paint_logger.debug(f"Processing file {i} of {nr_files}: seq nr: {index} name: {ext_image_name}")
            else:
                paint_logger.debug(ext_image_name)

            tau, r_squared, df_squares = process_single_image_in_paint_directory(ext_image_path,
                                                                                 ext_image_name,
                                                                                 nr_of_squares_in_row,
                                                                                 min_r_squared,
                                                                                 min_tracks_for_tau,
                                                                                 row['Min Density Ratio'],
                                                                                 max_variability,
                                                                                 concentration,
                                                                                 row["Nr Spots"],
                                                                                 row['Batch Sequence Nr'],
                                                                                 row['Experiment Nr'],
                                                                                 row['Experiment Seq Nr'],
                                                                                 row['Experiment Date'],
                                                                                 row['Experiment Name'],
                                                                                 verbose)
            if df_squares is None:
                paint_logger.error("process_single_image_in_paint_directory: did not return correctly")
                continue

            # To calculate the density use the actual surface coordinates.
            # Assume 2000 frames (100 sec) -  need to check - this is not always the case
            # Multiply by 1000 to get an easier  number
            # Area is calculated with Fiji info:
            #     Width:  82.0864 microns(512)
            #     Height: 82.0864 microns(512)
            # The area of a square then is (82.0864/nr_of_squares_in_row)^2
            #
            # To normalise concentration we divide by the supplied concentration
            # ----------------------------------------------------------------------------------

            area = pow(82.0864 / nr_of_squares_in_row, 2) * len(df_squares)
            density = calculate_density(nr_tracks=sum(df_squares['Nr Tracks']),
                                        area=area,
                                        time=100,
                                        concentration=concentration,
                                        magnification=1000)

            nr_visible_squares = len(df_squares[df_squares['Visible']])
            nr_total_squares = int(nr_of_squares_in_row * nr_of_squares_in_row)
            nr_defined_squares = nr_total_squares
            df_batch.loc[index, 'Nr Total Squares'] = nr_total_squares
            df_batch.loc[index, 'Nr Defined Squares'] = nr_defined_squares
            df_batch.loc[index, 'Nr Visible Squares'] = nr_visible_squares
            df_batch.loc[index, 'Nr Invisible Squares'] = nr_defined_squares - nr_visible_squares
            df_batch.loc[index, 'Squares Ratio'] = round(100 * nr_visible_squares / nr_total_squares)
            df_batch.loc[index, 'Max Squares Ratio'] = max_square_coverage
            df_batch.loc[index, 'Nr Rejected Squares'] = 0
            df_batch.loc[index, 'Exclude'] = df_batch.loc[index, 'Squares Ratio'] >= max_square_coverage
            df_batch.loc[index, 'Ext Image Name'] = ext_image_name
            df_batch.loc[index, 'Tau'] = tau
            df_batch.loc[index, 'Density'] = density
            df_batch.loc[index, 'R Squared'] = round(r_squared, 3)

            i += 1
            processed += 1

        else:
            paint_logger.info(f"Squares file already up to date: {squares_file_name}")

    save_batch_to_file(df_batch, os.path.join(paint_directory, "grid_batch.csv"))
    run_time = round(time.time() - time_stamp, 1)

    paint_logger.info(f"Processed  {processed:2d} images in {paint_directory} in {format_time_nicely(run_time)}")


if __name__ == "__main__":
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    GridDialog(root)
    root.mainloop()
