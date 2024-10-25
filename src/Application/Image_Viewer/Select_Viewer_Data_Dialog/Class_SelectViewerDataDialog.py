import os

import tkinter as tk
from tkinter import *
from tkinter import filedialog
from tkinter import ttk

from src.Application.Utilities.General_Support_Functions import (
    get_default_locations,
    save_default_locations)
from src.Common.Support.LoggerConfig import paint_logger

class SelectViewerDataDialog:

    def __init__(self, parent: tk.Tk) -> None:

        self.top = tk.Toplevel(parent)
        self.parent = parent
        self.parent.title('Select Viewer')

        self.proceed = False
        self.root_directory, self.experiment_directory, self.images_directory, self.level = get_default_locations()

        # Main content frame
        content = ttk.Frame(parent)
        content.grid(column=0, row=0)

        # Directory and Button frames
        frame_directory = self.create_frame(content, 0, 1)
        frame_buttons = self.create_frame(content, 0, 2)

        # Fill directory frame
        self.add_directory_widgets(frame_directory)

        # Fill button frame
        self.add_buttons(frame_buttons)

    def create_frame(self, parent, col, row, padding=(5, 5)) -> ttk.Frame:
        """Creates and returns a frame with grid layout."""
        frame = ttk.Frame(parent, borderwidth=5, relief='ridge')
        frame.grid(column=col, row=row, padx=padding[0], pady=padding[1])
        return frame

    def add_directory_widgets(self, frame) -> None:
        """Adds widgets to the directory frame."""
        # Directory and Configuration file buttons
        self.add_button(frame, 'Experiment Directory', 0, self.change_root_dir)
        self.add_button(frame, 'Project File', 1, self.change_level)

        # Labels and Radio buttons
        self.lbl_root_dir = self.add_label(frame, self.root_directory, 0)
        self.lbl_level = self.add_label(frame, self.level, 1)

        self.mode_dir_or_conf = StringVar(value="EXPERIMENT_LEVEL")
        self.add_radio_button(frame, "EXPERIMENT_LEVEL", 0)
        self.add_radio_button(frame, "PROJECT_LEVEL", 1)

    def add_buttons(self, frame) -> None:
        """Adds the Process and Exit buttons."""
        self.add_button(frame, 'Process', 0, self.process)
        self.add_button(frame, 'Exit', 1, self.exit_dialog)

    def add_button(self, parent, text, row, command) -> None:
        """Helper function to add a button to a frame."""
        ttk.Button(parent, text=text, command=command, width=15).grid(column=1, row=row, padx=2, pady=5)

    def add_label(self, parent, text, row) -> ttk.Label:
        """Helper function to add a label to a frame."""
        label = ttk.Label(parent, text=text, width=90)
        label.grid(column=2, row=row, padx=20, pady=5)
        return label

    def add_radio_button(self, parent, text, row) -> None:
        """Helper function to add a radio button to a frame."""
        ttk.Radiobutton(parent, text="", variable=self.mode_dir_or_conf, value=text, width=2).grid(column=0, row=row,
                                                                                                    padx=10, pady=5)

    def change_root_dir(self) -> None:
        self.root_directory = filedialog.askdirectory(initialdir=self.root_directory)
        if self.root_directory:
            self.mode_dir_or_conf.set('EXPERIMENT_LEVEL')
            self.lbl_root_dir.config(text=self.root_directory)
            save_default_locations(self.root_directory, self.experiment_directory, self.images_directory,
                                   self.level)

    def change_level(self) -> None:
        self.level = filedialog.askopenfilename(initialdir=self.experiment_directory,
                                                    title='Select a configuration file')
        if self.level:
            self.mode_dir_or_conf.set('PROJECT_LEVEL')
            self.lbl_level.config(text=self.level)
            save_default_locations(self.root_directory, self.experiment_directory, self.images_directory,
                                   self.level)

    def process(self) -> None:
        error = False

        if self.mode_dir_or_conf == "EXPERIMENT_LEVEL" and not os.path.isdir(self.root_directory):
            paint_logger.error('The root directory does not exist!')
            error = True
        elif self.mode_dir_or_conf == "PROJECT_LEVEL" and not os.path.isfile(self.level):
            paint_logger.error('No configuration file has been selected!')
            error = True

        if not error:
            self.proceed = True
            self.parent.destroy()

    def exit_dialog(self) -> None:
        self.proceed = False
        self.parent.destroy()

    def get_result(self):
        self.top.wait_window()
        return self.proceed, self.root_directory, self.level, self.mode_dir_or_conf.get()
