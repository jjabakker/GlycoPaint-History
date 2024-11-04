"""
This function takes as input the directory under which the various experiments are held.
It will create an Output directory with three files: All Squares, All Images, and Images Summary.
"""
import os
import sys
import time
from tkinter import *
from tkinter import ttk, filedialog

import pandas as pd

from src.Application.Generate_Squares.Utilities.Generate_Squares_Support_Functions import is_likely_root_directory
from src.Application.Utilities.General_Support_Functions import (
    get_default_locations,
    save_default_locations,
    read_experiment_file,
    read_squares_from_file,
    format_time_nicely,
    correct_all_images_column_types)
from src.Application.Utilities.Paint_Messagebox import paint_messagebox

from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Compile Output.log')


# -----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------
# The routine that does the work
# -----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------

def compile_project_output(project_dir: str, verbose: bool):
    paint_logger.info("")
    paint_logger.info(f"Compiling output for {project_dir}")
    time_stamp = time.time()

    # Create the dataframes to be filled
    df_all_images = pd.DataFrame()
    df_all_squares = pd.DataFrame()
    df_image_summary = pd.DataFrame()

    experiment_dirs = os.listdir(project_dir)
    experiment_dirs.sort()

    for experiment_name in experiment_dirs:

        experiment_dir_path = os.path.join(project_dir, experiment_name)
        if not os.path.isdir(experiment_dir_path) or 'Output' in experiment_name or experiment_name.startswith('-'):
            continue
        if verbose:
            paint_logger.debug(f'Adding directory: {experiment_dir_path}')

        # Read the experiment file

        experiment_file_path = os.path.join(experiment_dir_path, 'experiment_squares.csv')
        df_experiment = read_experiment_file(experiment_file_path)

        squares_file_path = os.path.join(experiment_dir_path, 'all_squares_in_experiment.csv')
        df_squares = read_squares_from_file(squares_file_path)


        # Determine how many unique for cell type, probe type, adjuvant, and probe there are in the batch
        row = [
            experiment_name,
            df_squares['Cell Type'].nunique(),
            df_squares['Probe Type'].nunique(),
            df_squares['Adjuvant'].nunique(),
            df_squares['Probe'].nunique()]

        # Add the data to the all_dataframes
        df_image_summary = pd.concat([df_image_summary, pd.DataFrame([row])])
        df_all_images = pd.concat([df_all_images, df_experiment])
        df_all_squares = pd.concat([df_all_squares, df_squares])

    # -----------------------------------------------------------------------------
    # At this point we have the df_all_images, df_all_squares and df_image_summary complete.
    # Some small tidying up
    # -----------------------------------------------------------------------------

    if len(df_all_squares) == 0:
        paint_logger.error(f"No squares found in {experiment_dir_path}")
        sys.exit()
    if len(df_all_images) == 0:
        paint_logger.error(f"No images found in {experiment_dir_path}")
        sys.exit()
    if len(df_image_summary) == 0:
        paint_logger.error(f"No image summary found in {experiment_dir_path}")
        sys.exit()

    # Ensure column types are correct
    correct_all_images_column_types(df_all_images)

    # Drop the squares that have no tracks
    # df_all_squares = df_all_squares[df_all_squares['Nr Tracks'] != 0]

    # Change recording_name to recording_name
    df_all_squares.rename(columns={'Ext Recording Name': 'Recording Name'}, inplace=True)
    #df_all_squares.insert(2, 'Recording Namne', df_all_squares['Ext Recording Name']0

    # Set the columns for df_image_summary
    df_image_summary.columns = ['Recording', 'Nr Cell Types', 'Nr Probe Types', 'Adjuvants', 'Nr Probes']

    # ------------------------------------
    # Save the files
    # -------------------------------------

    # Check if Output directory exists, create if necessary
    os.makedirs(os.path.join(project_dir, "Output"), exist_ok=True)

    # Save the files,
    df_all_squares.to_csv(os.path.join(project_dir, 'Output', 'All Squares.csv'), index=False)
    df_all_images.to_csv(os.path.join(project_dir, 'Output', 'All Images.csv'), index=False)
    df_image_summary.to_csv(os.path.join(project_dir, "Output", "Image Summary.csv"), index=False)

    # Save a copy for easy Imager Viewer access
    df_all_images.to_csv(os.path.join(project_dir, 'All Images.csv'), index=False)

    run_time = time.time() - time_stamp
    paint_logger.info(f"Compiled  output for {project_dir} in {format_time_nicely(run_time)}")
    paint_logger.info("")


class CompileDialog:

    def __init__(self, _root):
        self.root = _root

        self.root.title('Compile Square Data')

        self.root_directory, self.paint_directory, self.images_directory, self.level = get_default_locations()

        content = ttk.Frame(self.root)
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

        # Fill the button frame
        btn_compile = ttk.Button(frame_buttons, text='Compile', command=self.on_compile_pressed)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.on_exit_pressed)
        btn_compile.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        # Fill the directory frame
        btn_root_dir = ttk.Button(frame_directory, text='Project Directory', width=15, command=self.change_root_dir)
        self.lbl_root_dir = ttk.Label(frame_directory, text=self.root_directory, width=80)

        btn_root_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_root_dir.grid(column=1, row=0, padx=20, pady=5)

    def change_root_dir(self) -> None:
        self.root_directory = filedialog.askdirectory(initialdir=self.root_directory)
        save_default_locations(self.root_directory, self.paint_directory, self.images_directory, self.level)
        if len(self.root_directory) != 0:
            self.lbl_root_dir.config(text=self.root_directory)

    def on_compile_pressed(self) -> None:
        # Check if the directory is a likely project directory
        if is_likely_root_directory(self.root_directory):
            compile_project_output(project_dir=self.root_directory, verbose=True)
            self.root.destroy()
        else:
            paint_logger.error("The selected directory does not seem to be a project directory")
            paint_messagebox(self.root, title='Warning',
                             message="The selected directory does not seem to be a project directory")

    def on_exit_pressed(self) -> None:
        self.root.destroy()


if __name__ == "__main__":
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    CompileDialog(root)
    root.mainloop()
