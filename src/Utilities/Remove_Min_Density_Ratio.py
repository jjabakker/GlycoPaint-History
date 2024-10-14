import os
from tkinter import *
from tkinter import ttk, filedialog

import pandas as pd


def remove_min_density(root_directory):
    image_dirs = os.listdir(root_directory)
    image_dirs.sort()
    for image_dir in image_dirs:
        if 'Output' in image_dir:
            continue
        if os.path.isdir(os.path.join(root_directory, image_dir)):

            df_batch = pd.read_csv(os.path.join(root_directory, image_dir, 'batch.csv'), index_col=False)
            if {'Min Density Ratio'}.issubset(df_batch.columns):
                df_batch.drop(['Min Density Ratio'], axis=1, inplace=True)
                df_batch.to_csv(os.path.join(root_directory, image_dir, 'batch.csv'), index=False)
                print(f'Deleted column in batch file: {os.path.join(root_directory, image_dir, 'batch.csv')}')

            if os.path.isfile(os.path.join(root_directory, image_dir, 'grid_batch.csv')):
                df_batch = pd.read_csv(os.path.join(root_directory, image_dir, 'grid_batch.csv'), index_col=False)
                if {'Min Density Ratio'}.issubset(df_batch.columns):
                    df_batch.drop(['Min Density Ratio'], axis=1, inplace=True)
                    df_batch.to_csv(os.path.join(root_directory, image_dir, 'grid_batch.csv'), index=False)
                    print(f'Deleted column in batch file: {os.path.join(root_directory, image_dir, 'grid_batch.csv')}')


class Dialog:

    def __init__(self, root):
        root.title('Remove Min Density Ratio')

        self.root_dir = ""

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
        btn_root_dir = ttk.Button(frame_directory, text='Root Directory', width=15, command=self.select_dir)
        self.lbl_root_dir = ttk.Label(frame_directory, text=self.root_dir, width=50)

        btn_root_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_root_dir.grid(column=1, row=0, padx=20, pady=5)

    def select_dir(self):
        self.root_dir = filedialog.askdirectory()
        if len(self.root_dir) != 0:
            self.lbl_root_dir.config(text=self.root_dir)

    def process(self):
        remove_min_density(self.root_dir)

    def exit_dialog(self):
        root.destroy()


root = Tk()
root.eval('tk::PlaceWindow . center')
Dialog(root)
root.mainloop()
