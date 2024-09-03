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


def inspect_batch_files(root_dir):

    # Create the dataframes to be filled
    df_all_batches   = pd.DataFrame()
    df_batch_summary = pd.DataFrame()

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

        print(f'\nInspecting directory: {paint_dir_path}')

        # Read the batch file in the directory to determine which images there are
        batch_file_name = os.path.join(paint_dir_path, 'batch.csv')
        df_batch = read_batch_from_file(batch_file_name, only_records_to_process=False)
        if df_batch is None:
            print(f"Function 'compile_squares_file' failed: Batch file {batch_file_name} does not exist")
            exit()

        df_all_batches   = pd.concat([df_all_batches, df_batch])



    # ------------------------------------
    # Save the files
    # -------------------------------------

    # Check if Output directory exists, create if necessary
    if not os.path.isdir(os.path.join(root_dir, "Output")):
        os.mkdir(os.path.join(root_dir, "Output"))

    # Save the files
    df_all_batches.to_excel(os.path.join(root_dir, 'Output', 'Batches to Run.xlsx'), index=False)
    df_batch_summary.to_excel(os.path.join(root_dir, "Output", "Batch Summary.xlsx"), index=False)

    print ("\nOutput generated in directory 'Output'")




class InspectDialog:

    def __init__(self, root):
        root.title('Inspect Batch Files')

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
        self.lbl_root_dir  = ttk.Label(frame_directory, text=self.root_directory, width=50)

        btn_root_dir.grid      (column=0, row=0, padx=10, pady=5)
        self.lbl_root_dir.grid (column=1, row=0, padx=20, pady=5)

    def change_root_dir(self):
        self.root_directory = filedialog.askdirectory(initialdir=self.root_directory)
        save_default_directories(self.root_directory, self.paint_directory, self.images_directory)
        if len(self.root_directory) != 0:
            self.lbl_root_dir.config(text=self.root_directory)

    def process(self):
        inspect_batch_files(root_dir=self.root_directory)
        root.destroy()

    def exit_dialog(self):
        root.destroy()


root = Tk()
root.eval('tk::PlaceWindow . center')
InspectDialog(root)
root.mainloop()
