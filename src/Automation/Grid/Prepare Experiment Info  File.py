import os
import re
from tkinter import *
from tkinter import messagebox
from tkinter import ttk, filedialog

import pandas as pd

from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name)


def prepare_experiment_info_file(image_source_directory, experiment_directory):
    """
    This function creates a batch file in the image directory
    :return:
    """

    all_images = os.listdir(image_source_directory)
    all_images.sort()
    format_problem = False

    # Check if this is a likely correct directory. There should be lots of nd2 files
    count = 0
    count_bf = 0
    for image_name in all_images:
        if image_name.endswith(".nd2"):
            if image_name.find("BF") == -1:
                count += 1
            else:
                count_bf += 1

    # If there are less than 10 files ask the user
    if count < 10:
        txt = f"There were {count + count_bf} nd2 files found, of which {count_bf} are brightfield.\n"
        txt += "\nDo you want to continue?"
        proceed = messagebox.askyesno(title=txt, message=txt)
        if not proceed:
            return

    # Prepare the df to receive the date
    df_experiment = pd.DataFrame()

    # Scan the files
    all_images = os.listdir(image_source_directory)
    all_images.sort()

    seq_nr = 1
    paint_logger.info("")

    for image_name in all_images:

        # Skip files starting with .
        if image_name.startswith(('._', '.DS')) or not image_name.endswith(".nd2"):
            continue

        # Check the filename format of both the film and the BF
        regexp = re.compile(
            r'(?P<exp_date>\d{6})-Exp-(?P<exp_nr>\d{1,2})-[AB][1234]-(?P<exp_seq_nr>\d{1,2})(-BF[1-2])?$')
        match = regexp.match(os.path.splitext(image_name)[0])
        if match is None:
            format_problem = True
            paint_logger.info(f"Image name: {image_name} is not in the expected format")
            exp_nr = ""
            exp_seq_nr = ""
            exp_date = ""
            exp_name = ""
        else:
            exp_nr = match.group('exp_nr')
            exp_seq_nr = match.group('exp_seq_nr')
            exp_date = match.group('exp_date')
            exp_name = f'{exp_date}-Exp-{exp_nr}'

        # For further processing skip the BF file
        if image_name.find("BF") != -1:
            continue

        paint_logger.info(f'Processing file: {image_name}')

        # Get the image size
        image_size = os.path.getsize(os.path.join(image_source_directory, image_name))

        image_name = image_name.replace(".nd2", "")
        row = {'Batch Sequence Nr': seq_nr,
               'Experiment Date': exp_date,
               'Experiment Name': exp_name,
               'Experiment Nr': exp_nr,
               'Experiment Seq Nr': exp_seq_nr,
               'Image Name': image_name,
               'Probe': '',
               'Probe Type': '',
               'Cell Type': '',
               'Adjuvant': '',
               'Concentration': '',
               'Threshold': '',
               'Process': 'Yes',
               }
        df_experiment = pd.concat([df_experiment, pd.DataFrame.from_records([row])])
        seq_nr += 1

    # Now write the file, but only if there is data
    if len(df_experiment) == 0:
        paint_logger.info('No images were found. You have probably selected an incorrect directory.')
        paint_logger.info('No batch file was written.')
    else:
        df_experiment.to_csv(os.path.join(experiment_directory, "experiment_info.csv"), index=False)
        if format_problem:
            paint_logger.info('')
            paint_logger.info(
                f"There were filenames not in the expected format (\\d{6})-Exp-\\d{1, 2}-[AB][1234]-(\\d{1, 2})")
            paint_logger.info(
                "Please supply values for Batch Sequence Nr, Experiment Date, Experiment Nr, Experiment Seq Nr yourself.")
        paint_logger.info('')
        paint_logger.info(f"Process finished normally with {seq_nr - 1} images processed.")

    paint_logger.info('')
    paint_logger.info(
        "Don't forget to edit the experiment file to specify correct values for Probe, Probe type, Cell Type, Adjuvant and concentration.")
    paint_logger.info("Then choose the threshold values and select which images needs processing.")


class BatchDialog:

    def __init__(self, _root):
        _root.title('Prepare batch file')

        self.image_directory = ""
        self.paint_directory = ""

        content = ttk.Frame(_root)
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
        btn_image_dir = ttk.Button(frame_directory, text='Image Source Directory', width=20,
                                   command=self.change_image_dir)
        self.lbl_image_dir = ttk.Label(frame_directory, text=self.image_directory, width=50)

        btn_paint_dir = ttk.Button(frame_directory, text='Experiment Directory', width=20,
                                   command=self.change_paint_dir)
        self.lbl_paint_dir = ttk.Label(frame_directory, text=self.paint_directory, width=50)

        btn_image_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_image_dir.grid(column=1, row=0, padx=20, pady=5)

        btn_paint_dir.grid(column=0, row=1, padx=10, pady=5)
        self.lbl_paint_dir.grid(column=1, row=1, padx=20, pady=5)

    def change_image_dir(self):
        self.image_directory = filedialog.askdirectory(initialdir=self.image_directory)
        if len(self.image_directory) != 0:
            self.lbl_image_dir.config(text=self.image_directory)

    def change_paint_dir(self):
        self.paint_directory = filedialog.askdirectory(initialdir=self.paint_directory)
        if len(self.paint_directory) != 0:
            self.lbl_paint_dir.config(text=self.paint_directory)

    def process(self):
        if self.image_directory == "" or self.paint_directory == "":
            message = 'The image directory needs to point to where the images are.\n\n'
            message += 'The experimen directory is where the experiment_info.csv will be placed.'
            messagebox.showwarning(title='Warning', message=message)
        else:
            prepare_experiment_info_file(self.image_directory, self.paint_directory)
            self.exit_dialog()

    def exit_dialog(self):
        root.destroy()


paint_logger_change_file_handler_name('Prepare Experiment Info File.log')

root = Tk()
root.eval('tk::PlaceWindow . center')
BatchDialog(root)
root.mainloop()
