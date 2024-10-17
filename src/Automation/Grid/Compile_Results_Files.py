"""
This function takes as input the directory under which the various experiments are held.
It will create an Output directory with three files: all squares, all batches, and batches summary.
"""
import os
import time
from tkinter import *
from tkinter import ttk, filedialog

import pandas as pd

from src.Automation.Support.Support_Functions import (
    get_default_locations,
    save_default_locations,
    read_experiment_file,
    read_squares_from_file,
    format_time_nicely,
    correct_all_images_column_types)

from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Compile Squares.log')


# -----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------
# The routine that does the work
# -----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------

def compile_squares_file(root_dir: str, verbose: bool):
    paint_logger.info(f"Compiling output for {root_dir}")
    time_stamp = time.time()

    # Create the dataframes to be filled
    df_all_images = pd.DataFrame()
    df_all_squares = pd.DataFrame()
    df_image_summary = pd.DataFrame()

    paint_dirs = os.listdir(root_dir)
    paint_dirs.sort()
    for paint_dir in paint_dirs:

        paint_dir_path = os.path.join(root_dir, paint_dir)

        if not os.path.isdir(paint_dir_path) or 'Output' in paint_dir or paint_dir.startswith('-'):
            continue

        if verbose:
            paint_logger.debug(f'Adding directory: {paint_dir_path}')

        # Read the batch file in the directory to determine which images there are
        batch_file_name = os.path.join(paint_dir_path, 'grid_batch.csv')
        df_batch = read_experiment_file(batch_file_name, only_records_to_process=True)
        if df_batch is None:
            paint_logger.error(f"Function 'compile_squares_file' failed: Batch file {batch_file_name} does not exist")
            exit()

        for index, row in df_batch.iterrows():

            ext_image_name = row['Ext Image Name']
            if row['Exclude']:  # Skip over images that are Excluded
                continue

            df_squares = read_squares_from_file(os.path.join(root_dir, paint_dir, ext_image_name, 'grid',
                                                             ext_image_name + '-squares.csv'))
            if df_squares is None:
                paint_logger.error(
                    f'Compile Squares: No squares file found for image {ext_image_name} in the directory {paint_dir}')
                continue
            if len(df_squares) == 0:  # Ignore it when it is empty
                continue

            df_all_squares = pd.concat([df_all_squares, df_squares])

        # Determine how many unique for cell type, probe type, adjuvant, and probe there are in the batch
        row = [
            paint_dir,
            df_batch['Cell Type'].nunique(),
            df_batch['Probe Type'].nunique(),
            df_batch['Adjuvant'].nunique(),
            df_batch['Probe'].nunique()]

        # Add the data to the all_dataframes
        df_image_summary = pd.concat([df_image_summary, pd.DataFrame([row])])
        df_all_images = pd.concat([df_all_images, df_batch])

    # -----------------------------------------------------------------------------
    # At this point we have the df_all_images, df_all_squares and df_image_summary complete.
    # It is a matter of fine tuning now
    # -----------------------------------------------------------------------------

    # ----------------------------------------
    # Add data from df_all_images to df_all_squares
    # ----------------------------------------

    list_of_images = df_all_squares['Ext Image Name'].unique().tolist()
    for image in list_of_images:

        # Get data from df_batch to add to df_all_squares
        probe = df_all_images.loc[image]['Probe']
        probe_type = df_all_images.loc[image]['Probe Type']
        adjuvant = df_all_images.loc[image]['Adjuvant']
        cell_type = df_all_images.loc[image]['Cell Type']
        concentration = df_all_images.loc[image]['Concentration']
        threshold = df_all_images.loc[image]['Threshold']
        image_size = df_all_images.loc[image]['Image Size']
        experiment_nr = df_all_images.loc[image]['Experiment Nr']
        seq_nr = df_all_images.loc[image]['Batch Sequence Nr']
        neighbour_setting = df_all_images.loc[image]['Neighbour Setting']

        # It can happen that image size is not filled in, handle that event
        try:
            image_size = int(image_size)
        except (ValueError, TypeError):
            # If the specified images size was not valid (not a number), set it to 0
            df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Image Size'] = 0
            paint_logger.error(f"Invalid image size in {image}")

        # Add the data that was obtained from df_all_images
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Probe'] = probe
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Probe Type'] = probe_type
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Adjuvant'] = adjuvant
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Cell Type'] = cell_type
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Concentration'] = concentration
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Threshold'] = threshold
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Experiment Nr'] = int(experiment_nr)
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Batch Sequence Nr'] = int(seq_nr)
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Neighbour Setting'] = neighbour_setting

    # Ensure column types are correct
    correct_all_images_column_types(df_all_images)

    # Drop irrelevant columns in df_all_squares
    df_all_squares = df_all_squares.drop(['Neighbour Visible', 'Variability Visible', 'Density Ratio Visible'], axis=1)

    # Drop the squares that have no tracks
    df_all_squares = df_all_squares[df_all_squares['Nr Tracks'] != 0]

    # Change ext_image_name to image_name
    df_all_squares.rename(columns={'Ext Image Name': 'Image Name'}, inplace=True)

    # Set the columns for df_image_summary
    df_image_summary.columns = ['Image', 'Nr Cell Types', 'Nr Probe Types', 'Adjuvants', 'Nr Probes']

    # ------------------------------------
    # Save the files
    # -------------------------------------

    # Check if Output directory exists, create if necessary
    os.makedirs(os.path.join(root_dir, "Output"), exist_ok=True)

    # Save the files,
    df_all_squares.to_csv(os.path.join(root_dir, 'Output', 'All Squares.csv'), index=False)
    df_all_images.to_csv(os.path.join(root_dir, 'Output', 'All Images.csv'), index=False)
    df_image_summary.to_csv(os.path.join(root_dir, "Output", "Image Summary.csv"), index=False)

    # Save a copy for easy Imager Viewer access
    df_all_images.to_csv(os.path.join(root_dir, 'All Images.csv'), index=False)

    run_time = time.time() - time_stamp
    paint_logger.info(f"Compiled  output for {root_dir} in {format_time_nicely(run_time)}")



class CompileDialog:

    def __init__(self, _root):
        root.title('Compile Square Data')

        self.root_directory, self.paint_directory, self.images_directory, self_conf_file = get_default_locations()

        content = ttk.Frame(root)
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

        # Fill the button frame
        btn_process = ttk.Button(frame_buttons, text='Process', command=self.process)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.exit_dialog)
        btn_process.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        # Fill the directory frame
        btn_root_dir = ttk.Button(frame_directory, text='Root Directory', width=15, command=self.change_root_dir)
        self.lbl_root_dir = ttk.Label(frame_directory, text=self.root_directory, width=80)

        btn_root_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_root_dir.grid(column=1, row=0, padx=20, pady=5)

    def change_root_dir(self) -> None:
        self.root_directory = filedialog.askdirectory(initialdir=self.root_directory)
        save_default_locations(self.root_directory, self.paint_directory, self.images_directory, self.conf_file)
        if len(self.root_directory) != 0:
            self.lbl_root_dir.config(text=self.root_directory)

    def process(self)-> None:
        compile_squares_file(root_dir=self.root_directory, verbose=True)
        root.destroy()

    def exit_dialog(self)-> None:
        root.destroy()


if __name__ == "__main__":
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    CompileDialog(root)
    root.mainloop()
