import os
import pandas as pd
import logging
from tkinter import *
from tkinter import ttk, filedialog

from src.Automation.Support.Support_Functions import (
    get_default_directories,
    save_default_directories,
    read_batch_from_file,
)

# -------------------------------------------------------------------------------------
# Configure logging
# -------------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -------------------------------------------------------------------------------------
# Define the default parameters
# -------------------------------------------------------------------------------------
MAX_SQUARES_WITH_TAU = 20
MAX_VARIABILITY = 10
MIN_DENSITY_RATIO = 2


def inspect_batch_files(root_dir):
    """
    Inspects batch files in the given root directory and generates an output summary.

    :param root_dir: Directory containing experiment subdirectories
    """
    df_all_images = pd.DataFrame()  # Create an empty DataFrame to store results

    # Check if the root directory exists
    if not os.path.isdir(root_dir):
        logging.error(f"Root directory '{root_dir}' does not exist.")
        return

    # Get the list of experiment directories
    paint_dirs = sorted(os.listdir(root_dir))

    for paint_dir in paint_dirs:
        paint_dir_path = os.path.join(root_dir, paint_dir)

        if not os.path.isdir(paint_dir_path):  # If it's not a directory, skip it
            continue
        if 'Output' in paint_dir:             # Skip the output directory
            continue
        if paint_dir.startswith('-'):         # Skip directories marked with '-'
            continue

        logging.info(f'Inspecting directory: {paint_dir_path}')

        # Read the batch file in the directory
        batch_file_name = os.path.join(paint_dir_path, 'batch.csv')
        df_batch = read_batch_from_file(batch_file_name, only_records_to_process=False)

        if df_batch is None:
            logging.error(f"Batch file '{batch_file_name}' does not exist. Skipping directory.")
            continue

        # Concatenate the batch DataFrame with the main DataFrame
        df_all_images = pd.concat([df_all_images, df_batch])

    # ------------------------------------
    # Save the output file
    # ------------------------------------
    output_dir = os.path.join(root_dir, "Output")

    # Ensure Output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Save the concatenated DataFrame to Excel
    output_file = os.path.join(output_dir, 'Images to Process.xlsx')
    try:
        df_all_images.to_excel(output_file, index=False)
        logging.info(f"Output file saved at: {output_file}")
    except Exception as e:
        logging.error(f"Failed to save output file '{output_file}': {e}")


class InspectDialog:
    """
    A class for handling the user interface to inspect batch files.
    """

    def __init__(self, root):
        root.title('Inspect Batch Files')
        self.root_directory, self.paint_directory, self.images_directory = get_default_directories()

        # Set up the UI layout
        content = ttk.Frame(root)
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

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
        """
        Allows the user to select a new root directory.
        """
        self.root_directory = filedialog.askdirectory(initialdir=self.root_directory)
        if self.root_directory:
            save_default_directories(self.root_directory, self.paint_directory, self.images_directory)
            self.lbl_root_dir.config(text=self.root_directory)

    def process(self):
        """
        Starts the batch file inspection process.
        """
        if self.root_directory:
            inspect_batch_files(root_dir=self.root_directory)
        else:
            logging.error("No root directory selected.")
        root.destroy()

    def exit_dialog(self):
        """
        Closes the application.
        """
        root.destroy()


if __name__ == '__main__':
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    InspectDialog(root)
    root.mainloop()
