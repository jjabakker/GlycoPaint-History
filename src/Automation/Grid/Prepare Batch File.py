import os
import re
from tkinter import *
from tkinter import messagebox
from tkinter import ttk, filedialog

import pandas as pd


def prepare_batch_file(image_source_directory, paint_directory):
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
    batch_df = pd.DataFrame()

    # Scan the files
    all_images = os.listdir(image_source_directory)
    all_images.sort()

    seq_nr = 1
    print("\n")

    for image_name in all_images:

        # Skip files starting with .
        if image_name.startswith('._'):
            continue

        if image_name.startswith('.DS'):
            continue

        # if not image_name.endswith(".nd2"):
        #     continue

        # Check the filename format of both the film and the BF
        regexp = re.compile(r'(?P<exp_date>\d{6})-Exp-(?P<exp_nr>\d{1,2})-[AB][1234]-(?P<exp_seq_nr>\d{1,2})(-BF)?')
        match = regexp.match(image_name)
        if match is None:
            format_problem = True
            print(f"Image name: {image_name} is not in the required format")
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

        print(f'Processing file: {image_name}')

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
               'Min Density Ratio': '10',
               'Process': 'Yes',
               'Ext Image Name': '-',
               'Nr Spots': 0,
               'Nr Tracks': 0,
               'Image Size': image_size,
               'Run Time': 0,
               'Time Stamp': '-'
               }
        batch_df = pd.concat([batch_df, pd.DataFrame.from_records([row])])
        seq_nr += 1

    # Now write the file, but only if there is data
    if len(batch_df) == 0:
        print('No images were found. You have probably selected an incorrect directory.')
        print('No batch file was written.')
    else:
        batch_df.to_csv(os.path.join(paint_directory, "Batch.csv"), index=False)
        if format_problem:
            print(f"\nThere were filenames not in the expected format (\\d{6})-Exp-\\d{1, 2}-[AB][1234]-(\\d{1, 2})")
            print(
                "Please supply values for Batche Sequence Nr, Experiment Date, Experiment Nr, Experiment Seq Nr yourself.")
        print(f"\nProcess finished normally with {seq_nr - 1} images processed.")

    print("\n\n")
    print(
        "Don't forget to edit the batch file to specify correct values for Probe, Probe type, Cell Type, Adjuvant and concentration.")
    print("Then choose the threshold values and select which images needs processing.")
    print("\n\n")


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
        btn_image_dir = ttk.Button(frame_directory, text='Image Directory', width=15, command=self.change_image_dir)
        self.lbl_image_dir = ttk.Label(frame_directory, text=self.image_directory, width=50)

        btn_paint_dir = ttk.Button(frame_directory, text='Paint Directory', width=15, command=self.change_paint_dir)
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
            message += 'The paint directory is where the batch.csv will be placed.'
            messagebox.showwarning(title='Warning', message=message)
        else:
            prepare_batch_file(self.image_directory, self.paint_directory)

    def exit_dialog(self):
        root.destroy()


root = Tk()
root.eval('tk::PlaceWindow . center')
BatchDialog(root)
root.mainloop()
