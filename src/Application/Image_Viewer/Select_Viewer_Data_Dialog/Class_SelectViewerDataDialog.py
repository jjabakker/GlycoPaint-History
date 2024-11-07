import os
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

from src.Application.Utilities.General_Support_Functions import (
    get_default_locations,
    save_default_locations,
    test_paint_directory_type_for_compile,
)
from src.Application.Utilities.Paint_Messagebox import paint_messagebox
from src.Application.Utilities.ToolTips import ToolTip
from src.Common.Support.LoggerConfig import paint_logger
from src.Application.Image_Viewer.Utilities.Image_Viewer_Support_Functions import only_one_nr_of_squares_in_row

class SelectViewerDataDialog:

    def __init__(self, parent: tk.Tk) -> None:

        self.top = tk.Toplevel(parent)
        self.parent = parent
        self.parent.title('Select Viewer')

        self.proceed = False
        self.experiment_directory, self.directory, self.images_directory, self.project_file = get_default_locations()
        self.mode = None

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

        btn_root_dir = ttk.Button(frame_directory, text='Paint Directory', width=15, command=self.on_change_dir)
        self.lbl_experiment_dir = ttk.Label(frame_directory, text=self.experiment_directory, width=80)

        tooltip = "Select the directory where the Paint project or experiment is located. This can be a Project or Experiment directory."
        ToolTip(btn_root_dir, tooltip, wraplength=400)

        btn_root_dir.grid(column=1, row=0, padx=(5, 5), pady=5)
        self.lbl_experiment_dir.grid(column=2, row=0, padx=5, pady=5)

    def on_change_dir(self) -> None:
        self.directory = filedialog.askdirectory(initialdir=self.directory)
        if self.directory:
            self.lbl_experiment_dir.config(text=self.directory)
            save_default_locations(self.directory, self.experiment_directory, self.images_directory,
                                   self.project_file)

    def on_view(self) -> None:

        self.directory = self.lbl_experiment_dir.cget('text')

        if not os.path.isdir(self.directory):
            paint_logger.error("The selected directory does not exist")
            paint_messagebox(self.parent, title='Warning', message="The selected directory does not exist")
            return

        type = test_paint_directory_type_for_compile(self.directory)
        if type is None:
            # Unlikely that this is Project or Experiment directory
            paint_logger.error("The selected directory does not seem to be a project or experiment directory")
            paint_messagebox(self.parent, title='Warning',
                             message="The selected directory does not seem to be a project or experiment directory")
        else:

            # Now do a quick check to see if all recordings have been processed with the same nr_of_square_in_row setting
            if not only_one_nr_of_squares_in_row(self.directory):
                paint_messagebox(self.parent, title='Warning',
                                 message="Not all recordings have been processed with the same nr_of_square_in_row setting. Please run Generate Squares with consistent parameters.")
                return

            # The dialog will simply exit and the main programs will pick up the return values
            self.mode = type
            self.proceed = True
            self.parent.destroy()

    def on_exit(self) -> None:
        self.proceed = False
        self.parent.destroy()

    def get_result(self):
        self.top.wait_window()
        return self.proceed, self.directory, self.mode

