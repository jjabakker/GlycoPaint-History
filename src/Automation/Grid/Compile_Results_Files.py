"""
This function takes as input the directory under which the various experiments are held.
It will create an Output directory with three files: all squares, all batches, and batches summary.
"""

import os
import re
import pandas as pd

from tkinter import *
from tkinter import ttk, filedialog

from src.Automation.Support.Support_Functions import get_default_directories
from src.Automation.Support.Support_Functions import save_default_directories
from src.Automation.Support.Support_Functions import read_batch_from_file
from src.Automation.Support.Support_Functions import read_squares_from_file

# -------------------------------------------------------------------------------------
# Define the default parameters
# -------------------------------------------------------------------------------------

max_squares_with_tau  = 20
max_variability       = 10
min_density_ratio     = 2


def compile_squares_file(root_dir, verbose):

    # Create the dataframes to be filled
    df_all_images    = pd.DataFrame()
    df_all_squares   = pd.DataFrame()
    df_image_summary = pd.DataFrame()

    paint_dirs = os.listdir(root_dir)
    paint_dirs.sort()
    for paint_dir in paint_dirs:

        paint_dir_path = os.path.join(root_dir, paint_dir)

        if not os.path.isdir(paint_dir_path):  # If it is not a directory, skip it
            continue
        if 'Output' in paint_dir:              # If it is the output directory, skip it
            continue
        if paint_dir.startswith('-'):          # If the image directory name starts with '-' it was marked to be ignored
            continue

        if verbose:
            print(f'\nProcessing directory: {paint_dir_path}')

        # Read the batch file in the directory to determine which images there are
        batch_file_name = os.path.join(paint_dir_path, 'grid_batch.csv')
        df_batch = read_batch_from_file(batch_file_name, only_records_to_process=True)
        if df_batch is None:
            print(f"Function 'compile_squares_file' failed: Batch file {batch_file_name} does not exist")
            exit()

        for index, row in df_batch.iterrows():

            ext_image_name = row['Ext Image Name']

            if row['Exclude']:     # Skip over images that are Excluded
                continue

            squares_file_name = os.path.join(root_dir, paint_dir, ext_image_name, 'grid', ext_image_name + '-squares.csv')

            df_squares = read_squares_from_file(squares_file_name)
            if df_squares is None:
                print(f'Compile Squares: No squares file found for image {ext_image_name} in the directory {paint_dir}')
                continue
            if len(df_squares) == 0:  # Ignore it when it is empty
                continue

            # df_all_squares = pd.concat([df_all_squares, df_squares[df_squares['Visible']]])
            df_all_squares = pd.concat([df_all_squares, df_squares])

        nr_cell_types    = len(df_batch['Cell Type'].unique().tolist())
        nr_probe_types   = len(df_batch['Probe Type'].unique().tolist())
        nr_probes        = len(df_batch['Probe'].unique().tolist())
        nr_adjuvants     = len(df_batch['Adjuvant'].unique().tolist())
        row              = [paint_dir, nr_cell_types, nr_probe_types, nr_adjuvants, nr_probes]

        # Add the data to the all_dataframes
        df_image_summary = pd.concat([df_image_summary, pd.DataFrame([row])])
        df_all_images    = pd.concat([df_all_images, df_batch])

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
        probe             = df_all_images.loc[image]['Probe']
        probe_type        = df_all_images.loc[image]['Probe Type']
        adjuvant          = df_all_images.loc[image]['Adjuvant']
        cell_type         = df_all_images.loc[image]['Cell Type']
        concentration     = df_all_images.loc[image]['Concentration']
        threshold         = df_all_images.loc[image]['Threshold']
        image_size        = df_all_images.loc[image]['Image Size']
        experiment_nr     = df_all_images.loc[image]['Experiment Nr']
        seq_nr            = df_all_images.loc[image]['Batch Sequence Nr']
        neighbour_setting = df_all_images.loc[image]['Neighbour Setting']

        # Add the data that was obtained from df_all_images
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Probe']             = probe
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Probe Type']        = probe_type
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Adjuvant']          = adjuvant
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Cell Type']         = cell_type
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Concentration']     = concentration
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Threshold']         = threshold
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Image Size']        = image_size
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Experiment Nr']     = int(experiment_nr)
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Batch Sequence Nr'] = int(seq_nr)
        df_all_squares.loc[df_all_squares['Ext Image Name'] == image, 'Neighbour Setting'] = neighbour_setting

    # Drop irrelevant columns in df_all_squares
    df_all_squares = df_all_squares.drop(['Neighbour Visible', 'Variability Visible', 'Density Ratio Visible'], axis=1)

    # Drop the info on squares that have no tracks
    df_all_squares = df_all_squares[df_all_squares['Nr Tracks'] != 0]

    # Change ext_image_name to image_name
    df_all_squares.rename(columns={'Ext Image Name': 'Image Name'}, inplace=True)

    # Set the columns for df_image_summary
    df_image_summary.columns = ['Image', 'Nr Cell Types', 'Nr Probe Types', 'Adjuvants', 'Nr Probes']

    # Only keep Visible squares
    # df_all_squares = df_all_squares[df_all_squares['Visible'] == True]

    # --------------------------------------------------------------
    # Add probe valency and structure information when thesis is set
    # --------------------------------------------------------------

    thesis = True
    if thesis:
        df_all_squares['Valency']   = df_all_squares.apply(split_probe_valency, axis=1)
        df_all_squares['Structure'] = df_all_squares.apply(split_probe_structure, axis=1)

    # ------------------------------------
    # Save the files
    # -------------------------------------

    # Check if Output directory exists, create if necessary
    if not os.path.isdir(os.path.join(root_dir, "Output")):
        os.mkdir(os.path.join(root_dir, "Output"))

    # Save the files, use csv for the really big file size
    df_all_squares.to_csv(os.path.join(root_dir, 'Output', 'All Squares.csv'), index=False)
    df_all_images.to_csv(os.path.join(root_dir, 'Output', 'All Images.csv'), index=False)
    df_image_summary.to_csv(os.path.join(root_dir, "Output", "Image Summary.csv"), index=False)

    df_all_images.to_csv(os.path.join(root_dir, 'All Images.csv'), index=False)

    print ("\nOutput generated in directory 'Output'")


def split_probe_valency (row):
    regexp = re.compile(r'(?P<valency>\d{1}) +(?P<structure>[A-Za-z]+)')
    match = regexp.match(row['Probe'])
    if match is not None:
        valency   = match.group('valency')
        return int(valency)
    else:
        return 0


def split_probe_structure (row):
    regexp = re.compile(r'(?P<valency>\d{1}) +(?P<structure>[A-Za-z]+)')
    match = regexp.match(row['Probe'])
    if match is not None:
        structure = match.group('structure')
        return structure
    else:
        return ""


class CompileDialog:

    def __init__(self, root):
        root.title('Compile Squara Data')

        self.root_directory, self.paint_directory, self.images_directory = get_default_directories()

        content                       = ttk.Frame(root)
        frame_buttons                 = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory               = ttk.Frame(content, borderwidth=5, relief='ridge')

        #  Do the lay-out
        content.grid          (column=0, row=0)
        frame_directory.grid  (column=0, row=1, padx=5, pady=5)
        frame_buttons.grid    (column=0, row=2, padx=5, pady=5)

        # Fill the button frame
        btn_process = ttk.Button(frame_buttons, text='Process', command=self.process)
        btn_exit    = ttk.Button(frame_buttons, text='Exit', command=self.exit_dialog)
        btn_process.grid (column=0, row=1)
        btn_exit.grid    (column=0, row=2)

        # Fill the directory frame
        btn_root_dir       = ttk.Button(frame_directory, text='Root Directory', width=15, command=self.change_root_dir)
        self.lbl_root_dir  = ttk.Label(frame_directory, text=self.root_directory, width=80)

        btn_root_dir.grid      (column=0, row=0, padx=10, pady=5)
        self.lbl_root_dir.grid (column=1, row=0, padx=20, pady=5)

    def change_root_dir(self):
        self.root_directory = filedialog.askdirectory(initialdir=self.root_directory)
        save_default_directories(self.root_directory, self.paint_directory, self.images_directory)
        if len(self.root_directory) != 0:
            self.lbl_root_dir.config(text=self.root_directory)

    def process(self):
        compile_squares_file(root_dir=self.root_directory, verbose=True)
        root.destroy()

    def exit_dialog(self):
        root.destroy()

if __name__ == "__main__":
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    CompileDialog(root)
    root.mainloop()
