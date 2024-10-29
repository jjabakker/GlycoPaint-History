import os
import sys

import tkinter as tk
from tkinter import *
from tkinter import filedialog
from tkinter import ttk

from src.Application.Utilities.General_Support_Functions import (
    get_default_locations,
    save_default_locations)
from src.Application.Utilities.Paint_Messagebox import paint_messagebox
from src.Common.Support.LoggerConfig import paint_logger

class SelectViewerDataDialog:

    def __init__(self, parent: tk.Tk) -> None:

        self.top = tk.Toplevel(parent)
        self.parent = parent
        self.parent.title('Select Viewer')

        self.proceed = False
        self.experiment_directory, self.project_directory, self.images_directory, self.project_file = get_default_locations()

        # Main content frame
        content = ttk.Frame(parent)
        content.grid(column=0, row=0)

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        self.setup_frame_directory(frame_directory)
        self.setup_frame_buttons(frame_buttons)

        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

    def setup_frame_buttons(self, frame_buttons):

        btn_process = ttk.Button(frame_buttons, text='View', command=self.on_view)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.on_exit)

        btn_process.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

    def setup_frame_directory(self, frame_directory):

        btn_root_dir = ttk.Button(
            frame_directory, text='Experiment Directory', width=15, command=self.on_change_project_dir)
        btn_conf_file = ttk.Button(frame_directory, text='Project file', width=15, command=self.on_change_project_file)

        self.lbl_experiment_dir = ttk.Label(frame_directory, text=self.experiment_directory, width=80)
        self.lbl_project_file = ttk.Label(frame_directory, text=self.project_file, width=80)

        self.mode_var = StringVar(value="EXPERIMENT_LEVEL")
        self.rb_mode_directory = ttk.Radiobutton(
            frame_directory, text="", variable=self.mode_var, width=3, value="EXPERIMENT_LEVEL")
        self.rb_mode_conf_file = ttk.Radiobutton(
            frame_directory, text="", variable=self.mode_var, width=3, value="PROJECT_LEVEL")

        self.rb_mode_directory.grid(column=0, row=0, padx=(5, 2), pady=5)
        self.rb_mode_conf_file.grid(column=0, row=1, padx=(5, 2), pady=5)

        btn_root_dir.grid(column=1, row=0, padx=(0, 5), pady=5)
        btn_conf_file.grid(column=1, row=1, padx=(0, 5), pady=5)

        self.lbl_experiment_dir.grid(column=2, row=0, padx=5, pady=5)
        self.lbl_project_file.grid(column=2, row=1, padx=5, pady=5)

    def on_change_project_dir(self) -> None:
        self.project_directory = filedialog.askdirectory(initialdir=self.project_directory)
        if self.project_directory:
            self.mode_var.set('EXPERIMENT_LEVEL')
            self.lbl_experiment_dir.config(text=self.project_directory)
            save_default_locations(self.project_directory, self.experiment_directory, self.images_directory,
                                   self.project_file)

    def on_change_project_file(self) -> None:
        self.level = filedialog.askopenfilename(initialdir=self.experiment_directory,
                                                filetypes=[('CSV files', '*.csv')],
                                                title='Select a configuration file')
        if self.level:
            self.mode_var.set('PROJECT_LEVEL')
            self.lbl_project_file.config(text=self.level)
            save_default_locations(self.project_directory, self.experiment_directory, self.images_directory,
                                   self.level)

    def on_view(self) -> None:
        error = False

        if self.mode_var.get() == "EXPERIMENT_LEVEL":
            if not os.path.exists(os.path.join(self.experiment_directory, 'experiment_squares.csv')):
                msg = "The Experiment directory does not exist or does not contain the required 'experiment squares.csv' file (and is likely not a valid Experiment directory)"
                paint_logger.error(msg)
                paint_logger.error(f"Experiment directory: {self.experiment_directory}")
                paint_messagebox(self.parent, title='Warning', message=msg)
                error = True
        elif self.mode_var.get() == "PROJECT_LEVEL":
            if not os.path.isfile(self.project_file):
                msg = "The project file does not exist!"
                paint_logger.error(msg)
                paint_messagebox(self.parent, title='Warning', message=msg)
                error = True
        else:
            paint_logger.error("Invalid mode=")
            sys.exit()

        if not error:
            self.experiment_directory = self.lbl_experiment_dir.cget('text')
            self.project_file = self.lbl_project_file.cget('text')
            self.proceed = True
            self.parent.destroy()

    def on_exit(self) -> None:
        self.proceed = False
        self.parent.destroy()

    def get_result(self):
        self.top.wait_window()
        return self.proceed, self.experiment_directory, self.project_file, self.mode_var.get()
