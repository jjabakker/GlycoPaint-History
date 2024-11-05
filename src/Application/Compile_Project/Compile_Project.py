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

from src.Application.Utilities.Compille_All_tracks import compile_all_tracks
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

def compile_project_output(project_dir: str, drop_empty: bool = True, verbose: bool = False):
    paint_logger.info("")
    paint_logger.info(f"Compiling 'All Recordings' and 'All Squares' for {project_dir}")
    time_stamp = time.time()

    # Create the dataframes to be filled
    df_all_recordings = pd.DataFrame()
    df_all_squares = pd.DataFrame()

    experiment_dirs = os.listdir(project_dir)
    experiment_dirs.sort()

    for experiment_name in experiment_dirs:

        experiment_dir_path = os.path.join(project_dir, experiment_name)
        if not os.path.isdir(experiment_dir_path) or 'Output' in experiment_name or experiment_name.startswith('-'):
            continue
        if False:
            paint_logger.debug(f'Processing experiment: {experiment_dir_path}')

        # Read the experiment file
        df_experiment = read_experiment_file(os.path.join(experiment_dir_path, 'All Recordings.csv'))
        if df_experiment is None:
            paint_logger.error(f"Error reading {os.path.join(experiment_dir_path, 'All Recordings.csv')}")
            sys.exit()
        df_all_recordings = pd.concat([df_all_recordings, df_experiment])

        df_squares = read_squares_from_file(os.path.join(experiment_dir_path, 'All Squares.csv'))
        df_all_squares = pd.concat([df_all_squares, df_squares])

        if df_squares is None:
            paint_logger.error(f"Error reading {os.path.join(experiment_dir_path, 'All Squares.csv')}")
            sys.exit()
        df_all_squares = pd.concat([df_all_squares, df_squares])


    # -----------------------------------------------------------------------------
    # At this point we have the df_all_recordings and  df_all_squares complete.
    # Some small tidying up
    # -----------------------------------------------------------------------------

    if len(df_all_squares) == 0:
        paint_logger.error(f"No 'All Squares' generated.")
        sys.exit()
    if len(df_all_recordings) == 0:
        paint_logger.error(f"No 'All Recordings' generated.")
        sys.exit()

    # Ensure column types are correct
    correct_all_images_column_types(df_all_recordings)

    # Optionally drop the squares that have no tracks
    if drop_empty:
        df_all_squares = df_all_squares[df_all_squares['Nr Tracks'] != 0]

    # ------------------------------------
    # Save the files
    # -------------------------------------

    # Save the files,
    df_all_squares.to_csv(os.path.join(project_dir, 'All Squares.csv'), index=False)
    df_all_recordings.to_csv(os.path.join(project_dir, 'All Recordings.csv'), index=False)

    run_time = time.time() - time_stamp
    paint_logger.info(f"Compiled  'All Recordings' and 'All Squares' for {project_dir} in {format_time_nicely(run_time)}")
    paint_logger.info("")

    # ------------------------------------
    # Then do the Tracks File
    # -------------------------------------

    compile_all_tracks(project_dir)


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

        dir_content = os.listdir(self.root_directory)

        if all(item in dir_content for item in ['TrackMate Images', 'Brightfield Images']):
            paint_logger.error("The selected directory does not seem to be a project directory")
            paint_messagebox(self.root, title='Warning',
                             message="The selected directory does not seem to be a project directory")
        else:
            compile_project_output(project_dir=self.root_directory, verbose=True)
            self.root.destroy()

    def on_exit_pressed(self) -> None:
        self.root.destroy()


if __name__ == "__main__":
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    CompileDialog(root)
    root.mainloop()
