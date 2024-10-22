import os
import platform
import shutil
import pandas as pd
import statistics
import subprocess
import sys
import tempfile
import time
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import ttk

import matplotlib.pyplot as plt
from PIL import Image, ImageTk

from src.Application.Support.Class_HeatmapControlDialog import HeatMapControlDialog
from src.Application.Support.Class_SelectViewerDialog import SelectViewerDialog
from src.Application.Support.Class_SelectSquareDialog import SelectSquareDialog
from src.Application.Support.Heatmap_Support import get_colormap_colors, get_color_index, get_heatmap_data
from src.Application.Support.Support_Functions import (
    eliminate_isolated_squares_relaxed,
    eliminate_isolated_squares_strict,
    test_if_square_is_in_rectangle,
    read_experiment_file,
    read_squares_from_file,
    save_experiment_to_file,
    save_squares_to_file)
from src.Common.Support.DirectoriesAndLocations import (
    get_trackmate_image_dir_path,
    get_squares_file_path)
from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name)

# Log to an appropriately named file
paint_logger_change_file_handler_name('Image Viewer.log')


# ----------------------------------------------------------------------------------------
# ImageViewer Class
# ----------------------------------------------------------------------------------------

class ImageViewer:

    def __init__(self, parent, user_specified_directory, user_specified_conf_file, user_specified_mode):

        self.parent = tk.Toplevel(parent)

        self.user_specified_conf_file = user_specified_conf_file
        self.user_specified_directory = user_specified_directory
        self.user_specified_mode = user_specified_mode

        self.initialize_variables()

        self.setup_ui()
        self.load_images_and_config()
        self.setup_exclude_button()
        self.setup_exclude_button()
        self.setup_heatmap()

        # Bind keys for navigation
        parent.bind('<Right>', lambda event: self.go_forward_backward('FORWARD'))
        parent.bind('<Left>', lambda event: self.go_forward_backward('BACKWARD'))

        # Ensure the user can't close the window by clicking the X button
        self.parent.protocol("WM_DELETE_WINDOW", self.exit_viewer)

    def setup_heatmap(self):
        self.slider_value = tk.DoubleVar()
        self.rb_heatmap_parameter_value = tk.IntVar()
        self.rb_heatmap_parameter_value.set(1)  # Default selection is the first option
        # The update_heatmap_rb_value function is called when the radio button value is changed
        self.rb_heatmap_parameter_value.trace_add("write", self.update_heatmap_rb_value)

        self.checkbox_value = tk.BooleanVar()
        self.checkbox_value.set(False)  # Default is unchecked

    def initialize_variables(self):

        self.img_no = 0
        self.image_directory = None

        self.conf_file = conf_file
        self.mode_dir_or_conf = mode_dir_or_conf
        self.df_all_squares = None
        self.heatmap_active = False

        # UI state variables
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.squares_file_name = None
        self.show_squares_numbers = True
        self.show_squares = True
        self.square_changed = False
        self.experiments_changed = False
        self.neighbour_mode = ""
        self.select_mode = ""
        self.pop_square_info = None

        msg = f'Image Viewer - {self.user_specified_directory if self.mode_dir_or_conf == "DIRECTORY" else self.user_specified_conf_file}'
        msg += f'{" - NO SAVING" if self.user_specified_mode == "CONF_FILE" else ""}'
        self.parent.title(msg)


    def setup_ui(self):
        """
        Sets up the UI by defining the top level frames
        For each frame a setup function ios called
        """

        self.content = ttk.Frame(self.parent, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))

        self.frame_images = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_navigation_buttons = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_controls = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_filter = ttk.Frame(self.content, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_duration_mode = ttk.Frame(self.content, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))

        self.frame_images.grid(column=0, row=0, rowspan=2, padx=5, pady=5, sticky=tk.N)
        self.frame_navigation_buttons.grid(column=0, row=2, padx=5, pady=5, sticky=tk.N)
        self.frame_controls.grid(column=1, row=0, rowspan=2, padx=5, pady=5, sticky=N)
        # self.frame_filter.grid(column=2, row=0, padx=5, pady=5, sticky=N)
        self.frame_duration_mode.grid(column=2, row=1, padx=5, pady=5, sticky=N)

        self.setup_frame_images()
        self.setup_frame_navigation_buttons()
        self.setup_frame_controls()
        self.setup_frame_filter()

        self.content.grid(column=0, row=0)

    # ----------------------------------------------------------------------------------------
    # Setup functions for the frame_images content
    # ----------------------------------------------------------------------------------------

    def setup_frame_images(self):

        frame_width = 530
        frame_height = 670

        self.frame_picture_left = ttk.Frame(self.frame_images, borderwidth=2, relief='groove', width=frame_width,
                                            height=frame_height)
        self.frame_picture_right = ttk.Frame(self.frame_images, borderwidth=2, relief='groove', width=frame_width,
                                             height=frame_height)

        self.frame_picture_left.grid(column=0, row=0, padx=5, pady=5, sticky=N)
        self.frame_picture_right.grid(column=1, row=0, padx=5, pady=5, sticky=N)

        self.frame_picture_left.grid_propagate(False)
        self.frame_picture_right.grid_propagate(False)

        # Define the canvas widgets for the images
        self.cn_left_image = tk.Canvas(self.frame_picture_left, width=512, height=512)
        self.cn_right_image = tk.Canvas(self.frame_picture_right, width=512, height=512)

        self.cn_left_image.grid(column=0, row=0, padx=5, pady=5)
        self.cn_right_image.grid(column=0, row=0, padx=5, pady=5)

        self.parent.bind('<Key>', self.key_pressed)

        # Define the labels and combobox widgets for the images
        self.list_images = []
        self.list_of_image_names = []
        self.cb_image_names = ttk.Combobox(self.frame_picture_left, values=self.list_of_image_names, state='readonly',
                                           width=30)

        # Label for the right image name
        self.lbl_image_bf_name = StringVar(self.parent, "")
        lbl_image_bf_name = ttk.Label(self.frame_picture_right, textvariable=self.lbl_image_bf_name)

        # Labels for image info
        self.text_for_info1 = StringVar(self.parent, "")
        lbl_info1 = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info1)

        self.text_for_info2 = StringVar(self.parent, "")
        lbl_info2 = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info2)

        self.text_for_info3 = StringVar(self.parent, "")
        self.lbl_info3 = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info3)

        # Create a ttk style object
        self.style = ttk.Style()
        self.style.configure("Red.Label", foreground="red")
        self.style.configure("Black.Label", foreground="red")

        # Create a custom style for the label (set foreground to red)
        self.style.configure("Red.TLabel", foreground="red")

        # Bind combobox selection
        self.cb_image_names.bind("<<ComboboxSelected>>", self.image_selected)

        # Layout labels and combobox
        self.cb_image_names.grid(column=0, row=1, padx=5, pady=5)
        lbl_info1.grid(column=0, row=2, padx=5, pady=5)
        lbl_info2.grid(column=0, row=3, padx=5, pady=5)
        self.lbl_info3.grid(column=0, row=4, padx=5, pady=5)
        lbl_image_bf_name.grid(column=0, row=1, padx=0, pady=0)

    def setup_frame_navigation_buttons(self):
        # This frame is part of the content frame and contains the following buttons: bn_forward, bn_exclude, bn_backward, bn_exit

        self.bn_forward = ttk.Button(self.frame_navigation_buttons, text='Forward',
                                     command=lambda: self.go_forward_backward('FORWARD'))
        self.bn_exclude = ttk.Button(self.frame_navigation_buttons, text='Reject', command=lambda: self.exinclude())
        self.bn_backward = ttk.Button(self.frame_navigation_buttons, text='Backward',
                                      command=lambda: self.go_forward_backward('BACKWARD'))
        self.bn_exit = ttk.Button(self.frame_navigation_buttons, text='Exit', command=lambda: self.exit_viewer())

        # Layout the buttons
        self.bn_backward.grid(column=0, row=0, padx=5, pady=5)
        self.bn_exclude.grid(column=1, row=0, padx=5, pady=5)
        self.bn_forward.grid(column=2, row=0, padx=5, pady=5)
        self.bn_exit.grid(column=4, row=0, padx=30, pady=5)

        # Initially disable the back button
        self.bn_backward.configure(state=tk.DISABLED)

    def setup_frame_controls(self):
        # This frame is part of the content frame and contains the following frames: frame_neighbours, frame_cells, frame_commands

        frame_width = 30

        self.frame_neighbours = ttk.Frame(self.frame_controls, borderwidth=1, relief='groove', padding=(5, 5, 5, 5),
                                          width=frame_width)
        self.frame_cells = ttk.Frame(self.frame_controls, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_output_commands = ttk.Frame(self.frame_controls, borderwidth=2, relief='groove',
                                               padding=(5, 5, 5, 5))

        self.frame_neighbours.grid(column=0, row=1, padx=5, pady=5, sticky=tk.NSEW)
        self.frame_cells.grid(column=0, row=2, padx=5, pady=5)
        self.frame_output_commands.grid(column=0, row=3, padx=5, pady=5)

        self.setup_frame_neighbours()
        self.setup_frame_cells()
        self.setup_frame_output_commands()

    def setup_frame_neighbours(self):
        # This frame is part of frame_controls and contains the following radio buttons: rb_neighbour_free, rb_neighbour_strict, rb_neighbour_relaxed, bn_set_neighbours_all

        self.neighbour_var = StringVar(value="")
        self.rb_neighbour_free = Radiobutton(self.frame_neighbours, text="Free", variable=self.neighbour_var, width=12,
                                             value="Free", command=self.select_neighbour_button, anchor=tk.W)
        self.rb_neighbour_strict = Radiobutton(self.frame_neighbours, text="Strict", variable=self.neighbour_var,
                                               width=12, value="Strict", command=self.select_neighbour_button,
                                               anchor=tk.W)
        self.rb_neighbour_relaxed = Radiobutton(self.frame_neighbours, text="Relaxed", variable=self.neighbour_var,
                                                width=12, value="Relaxed", command=self.select_neighbour_button,
                                                anchor=tk.W)
        self.bn_set_neighbours_all = Button(self.frame_neighbours, text="Set for All",
                                            command=lambda: self.set_for_all_neighbour_state())

        # Place the radio buttons and button in the grid
        self.rb_neighbour_free.grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.rb_neighbour_relaxed.grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        self.rb_neighbour_strict.grid(column=0, row=2, padx=5, pady=5, sticky=tk.W)
        self.bn_set_neighbours_all.grid(column=0, row=3, padx=5, pady=5, sticky=tk.W)

        # Place the radio buttons and button in the grid
        self.rb_neighbour_free.grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.rb_neighbour_relaxed.grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        self.rb_neighbour_strict.grid(column=0, row=2, padx=5, pady=5, sticky=tk.W)
        self.bn_set_neighbours_all.grid(column=0, row=3, padx=5, pady=5, sticky=tk.W)

    def setup_frame_cells(self):
        """
        This frame is part of frame_controls and contains the cell selection radio buttons:

        :return:
        """

        width_rb = 12
        self.cell_var = StringVar(value=1)
        self.rb_cell0 = Radiobutton(self.frame_cells, text="Not on cell", width=width_rb, variable=self.cell_var,
                                    value=0)
        self.rb_cell1 = Radiobutton(self.frame_cells, text="On cell 1", width=width_rb, bg="red", fg="white",
                                    variable=self.cell_var, value=1)
        self.rb_cell2 = Radiobutton(self.frame_cells, text="On cell 2", width=width_rb, bg="yellow", fg="black",
                                    variable=self.cell_var, value=2)
        self.rb_cell3 = Radiobutton(self.frame_cells, text="On cell 3", width=width_rb, bg="green", fg="white",
                                    variable=self.cell_var, value=3)
        self.rb_cell4 = Radiobutton(self.frame_cells, text="On cell 4", width=width_rb, bg="magenta", fg="black",
                                    variable=self.cell_var, value=4)
        self.rb_cell5 = Radiobutton(self.frame_cells, text="On cell 5", width=width_rb, bg="cyan", fg="black",
                                    variable=self.cell_var, value=5)
        self.rb_cell6 = Radiobutton(self.frame_cells, text="On cell 6", width=width_rb, bg="black", fg="white",
                                    variable=self.cell_var, value=7)

        self.rb_cell0.grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.rb_cell1.grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        self.rb_cell2.grid(column=0, row=2, padx=5, pady=5, sticky=tk.W)
        self.rb_cell3.grid(column=0, row=3, padx=5, pady=5, sticky=tk.W)
        self.rb_cell4.grid(column=0, row=4, padx=5, pady=5, sticky=tk.W)
        self.rb_cell5.grid(column=0, row=5, padx=5, pady=5, sticky=tk.W)
        self.rb_cell6.grid(column=0, row=6, padx=5, pady=5, sticky=tk.W)

        # Bind the right mouse click
        self.rb_cell1.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 1))
        self.rb_cell2.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 2))
        self.rb_cell3.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 3))
        self.rb_cell4.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 4))
        self.rb_cell5.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 5))
        self.rb_cell6.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 6))
        self.rb_cell0.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 0))

    def setup_frame_output_commands(self):
        # This frame is part of frame_controls and contains the following buttons: bn_output, bn_reset, bn_excel, bn_histogram

        button_width = 12

        self.bn_histogram = ttk.Button(self.frame_output_commands, text='Histogram', command=lambda: self.histogram(),
                                       width=button_width)
        self.bn_excel = ttk.Button(self.frame_output_commands, text='Excel', command=lambda: self.show_excel(),
                                   width=button_width)
        self.bn_output = ttk.Button(self.frame_output_commands, text='Output', command=lambda: self.run_output(),
                                    width=button_width)
        self.bn_reset = ttk.Button(self.frame_output_commands, text='Reset', command=lambda: self.reset_image(),
                                   width=button_width)

        self.bn_output.grid(column=0, row=0, padx=5, pady=5)
        self.bn_reset.grid(column=0, row=1, padx=5, pady=5)
        self.bn_excel.grid(column=0, row=2, padx=5, pady=5)
        self.bn_histogram.grid(column=0, row=3, padx=5, pady=5)

    def setup_frame_filter(self):
        # This frame is part of the content frame and contains the following frames: frame_variability, frame_density_ratio

        self.frame_variability = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_density_ratio = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_duration = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))

        self.setup_frame_variability()
        self.setup_frame_density_ratio()
        self.setup_frame_duration()

        self.frame_variability.grid(column=0, row=0, padx=5, pady=5, sticky=tk.N)
        self.frame_density_ratio.grid(column=0, row=1, padx=5, pady=5, sticky=tk.N)
        self.frame_duration.grid(column=0, row=2, padx=5, pady=5, sticky=tk.N)

        # The set for all button ....
        self.bn_set_for_all_slider = ttk.Button(self.frame_filter, text='Set for All', command=self.set_for_all_slider)
        self.bn_set_for_all_slider.grid(column=0, row=3, padx=5, pady=5)

    def setup_frame_variability(self):
        # Define the Max Allowable Variability slider ....

        self.variability = DoubleVar()
        self.lbl_variability_text = ttk.Label(self.frame_variability, text='Max Allowable Variability', width=20)
        self.sc_variability = tk.Scale(self.frame_variability, from_=1.5, to=10, variable=self.variability,
                                       orient='vertical', resolution=0.5)
        self.sc_variability.bind("<ButtonRelease-1>", self.variability_changed)
        self.lbl_variability_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_variability.grid(column=0, row=1, padx=5, pady=5)

    def setup_frame_density_ratio(self):
        # Define the Min Required Density Ratio slider ...

        self.density_ratio = DoubleVar()
        self.lbl_density_ratio_text = ttk.Label(self.frame_density_ratio, text='Min Required Density Ratio', width=20)
        self.sc_density_ratio = tk.Scale(self.frame_density_ratio, from_=2, to=40, variable=self.density_ratio,
                                         orient='vertical', resolution=0.1)
        self.sc_density_ratio.bind("<ButtonRelease-1>", self.density_ratio_changed)
        self.lbl_density_ratio_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_density_ratio.grid(column=0, row=1, padx=5, pady=5)

    def setup_frame_duration(self):
        # Define the Track Duration sliders ...

        self.frame_max_duration = ttk.Frame(self.frame_duration, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_min_duration = ttk.Frame(self.frame_duration, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))

        self.setup_max_duration()
        self.setup_min_duration()

        self.lbl_track_duration_text = ttk.Label(self.frame_duration, text='Track Duration', width=10)

        self.frame_duration.columnconfigure(0, weight=1)  # First column
        self.frame_duration.columnconfigure(1, weight=1)  # Second column
        self.lbl_track_duration_text.grid(row=0, column=0, padx=5, pady=5, columnspan=2, sticky=tk.N)
        self.frame_max_duration.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)
        self.frame_min_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N)

    def setup_max_duration(self):
        # Define the max duration slider .....

        self.track_max_duration = DoubleVar(value=200)
        self.lbl_track_max_duration_text = ttk.Label(self.frame_max_duration, text='Max', width=10)
        self.sc_track_max_duration = tk.Scale(self.frame_max_duration, from_=0, to=200,
                                              variable=self.track_max_duration,
                                              orient='vertical', resolution=0.1)
        self.sc_track_max_duration.bind("<ButtonRelease-1>", self.track_duration_changed)

        self.lbl_track_max_duration_text.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W + tk.E)
        self.sc_track_max_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W + tk.E)

    def setup_min_duration(self):
        # Define the min duration slider .....

        self.track_min_duration = DoubleVar(value=0)
        self.lbl_track_min_duration_text = ttk.Label(self.frame_min_duration, text='Min', width=10)
        self.sc_track_min_duration = tk.Scale(self.frame_min_duration, from_=0, to=200,
                                              variable=self.track_min_duration,
                                              orient='vertical', resolution=0.1)
        self.sc_track_min_duration.bind("<ButtonRelease-1>", self.track_duration_changed)
        self.lbl_track_min_duration_text.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W + tk.E)
        self.sc_track_min_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W + tk.E)

    def load_images_and_config(self):

        if self.user_specified_mode == "DIRECTORY":
            self.experiment_directory_path = self.user_specified_directory
            self.experiment_bf_directory = os.path.join(self.experiment_directory_path, 'Converted BF Images')
            experiment_tm_file_path = os.path.join(self.experiment_directory_path, 'experiment_squares.csv')
        else:
            # self.experiment_directory_path is not set in this case    TODO: Check when it is set
            self.project_directory = os.path.split(self.user_specified_conf_file)[0]
            experiment_tm_file_path = self.user_specified_conf_file

        self.df_experiment = read_experiment_file(experiment_tm_file_path, True)
        if self.df_experiment is None:
            self.show_error_and_exit("No 'experiment_squares.csv.csv' file, Did you select an image directory?")

        self.nr_of_squares_in_row = int(self.df_experiment.iloc[0]['Nr of Squares in Row'])

        self.list_images = self.get_images()
        if not self.list_images:
            self.show_error_and_exit(f"No images were found in directory {self.experiment_directory_path}.")

        self.list_of_image_names = [image['Left Image Name'] for image in self.list_images]
        self.cb_image_names['values'] = self.list_of_image_names

        self.initialise_image_display()
        self.img_no = -1
        self.go_forward_backward('FORWARD')

    def setup_exclude_button(self):
        # Set up the exclude/include button state

        row_index = self.df_experiment.index[self.df_experiment['Ext Image Name'] == self.image_name].tolist()[0]
        if self.df_experiment.loc[row_index, 'Exclude']:
            self.bn_exclude.config(text='Include')
            self.text_for_info3.set('Excluded')
            self.lbl_info3.config(style="Red.Label")
        else:
            self.bn_exclude.config(text='Exclude')
            self.text_for_info3.set('')
            self.lbl_info3.config(style="Black.Label")

    def set_for_all_neighbour_state(self):
        # Set the neighbour state for all images as specified in the radio buttons

        self.experiments_changed = True
        self.df_experiment['Neighbour Setting'] = self.neighbour_var.get()

    def get_images(self):
        """
        Retrieve the images to be displayed (for the left and right frame) from disk and return them as a list
        :return:
        """

        # Create an empty lst that will hold the images
        list_images = []
        square_nrs = []
        self.df_all_squares = pd.DataFrame()

        # Cycle through the experiments file (it can be at experiment level or at project level)
        error_count = 0

        for index in range(len(self.df_experiment)):

            # Skip images that do not require processing
            if self.df_experiment.iloc[index]['Process'] in ['No', 'N']:
                continue

            image_name = self.df_experiment.iloc[index]['Ext Image Name']
            if self.user_specified_mode == "CONF_FILE":

                experiment = str(self.df_experiment.iloc[index]['Experiment Date'])
                exp_dir =  os.path.join(self.project_directory, experiment)
                bf_dir = os.path.join(exp_dir, 'Converted BF Images')
                squares_file_path = get_squares_file_path(exp_dir, image_name)
                trackmate_images_dir = get_trackmate_image_dir_path(exp_dir, image_name)
                # self.experiment_directory = exp_dir    # TODO: Check if this is correct
            else:
                exp_dir = self.experiment_directory_path
                bf_dir = self.experiment_bf_directory
                squares_file_path = get_squares_file_path(exp_dir, image_name)
                trackmate_images_dir = get_trackmate_image_dir_path(exp_dir, image_name)
            self.squares_file_name = squares_file_path

            # If there is no 'Trackmate Images' directory below the image directory, skip it
            if not os.path.isdir(trackmate_images_dir):
                paint_logger.error(
                    f"Function 'get_images' failed - The directory for trackmate images does not exist: {trackmate_images_dir}")
                continue

            # Then get all the files in  the 'img' directory
            all_images_in_img_dir = os.listdir(trackmate_images_dir)

            # Only consider images that contain the image_name
            # TODO Can there ever be different files and can there be more than one file?
            all_images_in_img_dir = [img for img in all_images_in_img_dir if image_name in img]
            all_images_in_img_dir.sort()

            valid = False

            for img in all_images_in_img_dir:

                try:
                    # Try reading the file
                    left_img = ImageTk.PhotoImage(Image.open(os.path.join(trackmate_images_dir, img)))

                    # Try Retrieve the square numbers for this image
                    df_squares = read_squares_from_file(squares_file_path)
                    square_nrs = list(df_squares['Square Nr'])
                    self.df_experiment.loc[index, 'Nr Spots'] = len(square_nrs)

                    # Check if self.df_all_squares is empty
                    if not self.df_all_squares.empty:  # Correct way to check for an empty DataFrame
                        self.df_all_squares = pd.concat([self.df_all_squares, df_squares], ignore_index=True)
                    else:
                        self.df_all_squares = df_squares

                except:
                    left_img = Image.new('RGB', (512, 512), "rgb(235,235,235)")
                    left_img = ImageTk.PhotoImage(left_img)
                    square_nrs = []
                    error_count += 1

            # Retrieve Tau from the experiments_squares file, if problem return 0
            tau = self.df_experiment['Tau'].iloc[index] if 'Tau' in self.df_experiment.columns else 0

            # Find the corresponding BF
            right_valid, right_img = self.get_corresponding_bf(bf_dir, image_name)

            record = {
                "Left Image Name": self.df_experiment.iloc[index]['Ext Image Name'],
                "Left Image": left_img,
                "Left Valid": valid,

                "Right Image Name": image_name,
                "Right Image": right_img,
                "Right Valid": right_valid,

                "Cell Type": self.df_experiment.iloc[index]['Cell Type'],
                "Adjuvant": self.df_experiment.iloc[index]['Adjuvant'],
                "Probe": self.df_experiment.iloc[index]['Probe'],
                "Probe Type": self.df_experiment.iloc[index]['Probe Type'],

                "Threshold": self.df_experiment.iloc[index]['Threshold'],
                "Nr Spots": int(self.df_experiment.iloc[index]['Nr Spots']),

                "Square Nrs": square_nrs,
                "Squares File": self.squares_file_name,

                "Tau": tau
            }

            list_images.append(record)

        print("\n\n")

        if error_count > 0:
            paint_logger.error(
                f"There were {error_count} out of {len(self.df_experiment)} images for which no picture was available")

        return list_images

    def get_corresponding_bf(self, bf_dir, image_name):
        """
        Retrieve the corresponding BF image for the given image name
        :param bf_dir:
        :param image_name:


        :return:
        """

        if not os.path.exists(bf_dir):
            paint_logger.error(
                "Function 'get_corresponding_bf' failed - The directory for jpg versions of BF images does not exist. Run 'Convert BF Images' first")
            sys.exit()

        # Peel off the 'threshold' and add -BF*.jpg
        image_name = "-".join(image_name.split("-")[:-2])

        # List of possible BF image names
        bf_images = [f"{image_name}-BF.jpg", f"{image_name}-BF1.jpg", f"{image_name}-BF2.jpg"]

        # Iterate through the list and check if the file exists
        image_name = None
        for img in bf_images:
            if os.path.isfile(os.path.join(bf_dir, img)):
                image_name = img
                break

        if image_name:
            img = ImageTk.PhotoImage(Image.open(os.path.join(bf_dir, image_name)))
            valid = True
        else:
            img = ImageTk.PhotoImage(Image.new('RGB', (512, 512), (235, 235, 235)))
            valid = False

        return valid, img

    def show_error_and_exit(self, message):
        paint_logger.error(message)
        sys.exit()

    def initialise_image_display(self):
        # Update the image display based on the current image number

        self.cn_left_image.create_image(0, 0, anchor=tk.NW, image=self.list_images[self.img_no]['Left Image'])
        self.cn_right_image.create_image(0, 0, anchor=tk.NW, image=self.list_images[self.img_no]['Right Image'])

        # Update labels for image information
        self.lbl_image_bf_name.set(self.list_images[self.img_no]['Right Image Name'])
        cell_info = f"({self.list_images[self.img_no]['Cell Type']}) - ({self.list_images[self.img_no]['Adjuvant']}) - ({self.list_images[self.img_no]['Probe Type']}) - ({self.list_images[self.img_no]['Probe']})"
        self.text_for_info1.set(cell_info)
        info2 = f"Spots: {self.list_images[self.img_no]['Nr Spots']:,} - Threshold: {self.list_images[self.img_no]['Threshold']}"
        self.text_for_info2.set(info2)

    def exinclude(self):
        """
        Toggle the state of the recording. Change the button text and the info text
        :return:
        """

        #row_index = self.df_experiment.index[self.df_experiment['Ext Image Name'] == self.image_name].tolist()[0]
        # This was complex code, but the index is already the image name

        row_index = self.image_name
        if not self.df_experiment.loc[row_index, 'Exclude']:
            self.df_experiment.loc[row_index, 'Exclude'] = True
            self.bn_exclude.config(text='Include')     # Change the button text
            self.text_for_info3.set('Excluded')        # Change the info text to 'Excluded'
        else:
            self.df_experiment.loc[row_index, 'Exclude'] = False
            self.bn_exclude.config(text='Exclude')      # Change the button text
            self.text_for_info3.set('')
        self.experiments_changed = True


    def key_pressed(self, event):
        """
        This function is triggered by pressing a key and will perform the required actions

        :return:
        """
        self.cn_left_image.focus_set()

        # Displaying squares is toggled by pressing 's'
        if event.keysym == 's':
            self.show_squares = not self.show_squares
            self.display_selected_squares()

        # Displaying square numbers is toggled by pressing 'n'
        if event.keysym == 'n':
            self.show_squares_numbers = not self.show_squares_numbers
            if self.show_squares:
                self.show_numbers = True
            self.display_selected_squares()

        # Pressing 'o' will generate a pdf file containing all the images
        if event.keysym == 'o':
            self.output_pictures()

    def output_pictures(self):
        """
        The function is triggered by pressing 'o' and will generate a pdf file containing all the images.
        :return:
        """

        # Create the squares directory if it does not exist
        squares_dir = os.path.join(self.experiment_directory_path, 'Output', 'Squares')
        os.makedirs(squares_dir, exist_ok=True)

        # Cycle through all images
        save_img_no = self.img_no
        self.img_no = -1
        for img_no in range(len(self.list_images)):
            self.go_forward_backward('FORWARD')

            image_name = self.list_images[self.img_no]['Left Image Name']
            paint_logger.debug(f"Writing {image_name} tp pdf")

            # Delete the squares and write the canvas with just the tracks
            self.cn_left_image.delete("all")
            self.cn_left_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])
            save_as_png(self.cn_left_image, os.path.join(squares_dir, image_name))

            # Add the squares and write the canvas complete with squares
            self.select_squares_for_display()
            self.display_selected_squares()
            image_name = image_name + '-squares'
            save_as_png(self.cn_left_image, os.path.join(squares_dir, image_name))

        # Find all the ps files and delete them
        ps_files = os.listdir(squares_dir)
        for item in ps_files:
            if item.endswith(".ps"):
                os.remove(os.path.join(squares_dir, item))

        # Find all the png files and sort them
        png_files = []
        files = os.listdir(squares_dir)
        for file in files:
            if file.endswith(".png"):
                png_files.append(os.path.join(squares_dir, file))
        png_files = sorted(png_files)

        # Create Image objects of all png files
        png_images = []
        for png_file in png_files:
            png_images.append(Image.open(png_file))
        pdf_path = os.path.join(squares_dir, 'images.pdf')

        # Create a pdf with a first images and all the other images to it
        png_images[0].save(pdf_path, "PDF", resolution=200.0, save_all=True, append_images=png_images[1:])

        # Go back to the image where we were
        self.img_no -= 1
        self.go_forward_backward('FORWARD')

    def save_experiment_file_if_requested(self):

        file = f"{self.experiment_directory_path if self.mode_dir_or_conf == "DIRECTORY" else self.conf_file}"
        file = os.path.split(file)[1]
        msg = f"Do you want to save changes to {'experiments' if self.mode_dir_or_conf == 'DIRECTORY' else 'configuration'} file: {file} ?"
        response = messagebox.askyesnocancel("Save Changes", message=msg)
        if response is True:
            self.save_density_ratio_slider_state_into_df_experiment()
            self.save_variability_slider_state_into_df_experiment()
            self.save_neighbour_state_into_df_experiment()

            # Write the Visible Squares visibility information into the squares file
            self.df_squares['Visible'] = (self.df_squares['Density Ratio Visible'] &
                                          self.df_squares['Variability Visible'] &
                                          self.df_squares['Duration Visible'])
            self.df_experiment.loc[self.image_name, 'Nr Visible Squares'] = len(
                self.df_squares[self.df_squares['Visible']])
            save_experiment_to_file(self.df_experiment, self.experiment_tm_file_path)     # TODO: Check if this is correct
        if response is not None:
            self.experiments_changed = False
        return response

    def save_squares_file_if_requested(self):

        file = f"{self.squares_file_name if self.mode_dir_or_conf == "DIRECTORY" else self.conf_file}"
        file = os.path.split(file)[1]
        msg = f"Do you want to save changes to tracks file: {file}"
        response = messagebox.askyesnocancel("Save Changes", message=msg)
        if response is True:
            self.update_squares_file()
            self.square_changed = False
        return response

    def exit_viewer(self):

        response_square = None
        response_experiment = None

        if self.experiments_changed:
            if self.mode_dir_or_conf == "DIRECTORY":
                response_experiment = self.save_experiment_file_if_requested()
            else:
                messagebox.showinfo("Save Warning", "No saving of experiment file is implemented in configuration mode")

        if self.square_changed:
            if self.mode_dir_or_conf == "DIRECTORY":
                response_square = self.save_squares_file_if_requested()
            else:
                messagebox.showinfo("Save Warning", "No saving of squares file is implemented in configuration mode")

        if self.mode_dir_or_conf == "DIRECTORY":
            if (self.experiments_changed and response_experiment == None) or (self.square_changed and response_square == None):
                return
            else:
                root.quit()
        else:
            root.quit()

    def image_selected(self, _):
        image_name = self.cb_image_names.get()
        paint_logger.debug(image_name)
        index = self.list_of_image_names.index(image_name)
        self.img_no = index - 1
        self.go_forward_backward('FORWARD')

    def set_variability_slider_state(self):
        max_allowed_variability = self.df_experiment.loc[self.image_name]['Variability Setting']
        self.sc_variability.set(max_allowed_variability)

    def set_density_ratio_slider_state(self):
        min_required_density = self.df_experiment.loc[self.image_name]['Density Ratio Setting']
        self.sc_density_ratio.set(min_required_density)

    def set_neighbour_state(self):
        neighbour_state = self.df_experiment.loc[self.image_name]['Neighbour Setting']
        self.neighbour_var.set(neighbour_state)

    def save_variability_slider_state_into_df_experiment(self):
        self.df_experiment.loc[self.image_name, 'Variability Setting'] = round(self.sc_variability.get(), 1)

    def save_density_ratio_slider_state_into_df_experiment(self):
        self.df_experiment.loc[self.image_name, 'Density Ratio Setting'] = round(self.sc_density_ratio.get(), 1)

    def save_neighbour_state_into_df_experiment(self):
        self.df_experiment.loc[self.image_name, 'Neighbour Setting'] = self.neighbour_var.get()

    def histogram(self):

        unique_cells = self.df_squares['Cell Id'].unique().tolist()
        for cell_id in unique_cells:
            self.provide_report_on_cell(self, cell_id)

            df_selection = self.df_squares[self.df_squares['Cell Id'] == cell_id]
            df_selection_visible = df_selection[df_selection['Visible']]
            tau_values_visible = df_selection_visible['Tau'].to_list()

            if len(tau_values_visible) > 0:
                tau_mean = round(statistics.mean(tau_values_visible), 0)
                tau_median = round(statistics.median(tau_values_visible), 0)
                tau_std = round(statistics.stdev(tau_values_visible), 1)

                print(
                    f"For Cell Id: {cell_id}, the tau mean is {tau_mean}, the tau median is {tau_median} and the tau std is {tau_std}\n")

    def show_excel(self):
        # Path to the Excel application
        if platform.system() == 'Darwin':
            # On macOS, we use the 'open' command to open applications
            excel_command = 'open'
            excel_args = ['-a', '/Applications/Microsoft Excel.app']
        else:
            # On Windows, we directly call the Excel executable
            excel_command = r'C:\Program Files\Microsoft Office\root\OfficeXX\Excel.exe'  # Update Excel path as needed
            excel_args = [excel_command]

        # Create a temporary directory manually, so we can control when it's deleted
        temp_dir = tempfile.mkdtemp()

        try:
            # Define the destination path inside the temporary directory
            temp_file = os.path.join(temp_dir, os.path.basename(self.squares_file_name))

            # Save squares data to the temporary file
            save_squares_to_file(self.df_squares, temp_file)

            # Make sure the file exists before continuing
            if not os.path.exists(temp_file):
                raise FileNotFoundError(f"Temporary file {temp_file} does not exist")

            # Print the file path for debugging purposes
            print(f"Opening Excel with file: {temp_file}")

            # Open Excel with the temp file
            if platform.system() == 'Darwin':
                subprocess.Popen([excel_command] + excel_args + [temp_file])
            else:
                subprocess.Popen(excel_args + [temp_file], shell=True)

            # Optionally, wait for Excel to open the file before continuing
            time.sleep(2)  # Pause to give Excel time to open the file

        finally:
            # Ensure that the temporary directory is deleted after use
            print(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)

        nr_total_squares = len(self.df_squares)
        tau_values = self.df_squares[self.df_squares['Visible']]['Tau'].tolist()
        nr_visible_squares = len(tau_values)
        if nr_visible_squares != 0:
            tau_min = min(tau_values)
            tau_max = max(tau_values)
            tau_mean = round(statistics.mean(tau_values), 0)
            tau_median = round(statistics.median(tau_values), 0)
            tau_std = round(statistics.stdev(tau_values), 1)
        else:
            tau_min = '-'
            tau_max = '-'
            tau_mean = '-'
            tau_median = '-'
            tau_std = '-'

        print('\n\n')
        print(f'The total number of squares:   {nr_total_squares}')
        print(f'The visible number of squares: {nr_visible_squares}')
        print(f'The maximum Tau value:         {tau_max}')
        print(f'The minimum Tau value:         {tau_min}')
        print(f'The mean Tau value:            {tau_mean}')
        print(f'The median Tau value:          {tau_median}')
        print(f'The Tau standard deviation:    {tau_std}')

    def reset_image(self):
        """
        Resets the current image. All squares are displayed, but the variability and density ratio sliders are applied
        :return:
        """

        SelectSquareDialog(self)


        self.experiments_changed = True

        self.df_squares['Visible'] = True
        self.df_squares['Neighbour Visible'] = True
        self.df_squares['Variability Visible'] = True
        self.df_squares['Duration Visible'] = True
        # self.df_squares['Density Ration Selected'] = True
        self.df_squares['Cell Id'] = 0

        self.select_squares_for_display()
        self.display_selected_squares()

    def run_output(self):
        """
        Prepares the output files.
        For specific sets up probes or cell types, specific functions are needed
        :return:
        """

        # If the heatmap is not already  active, then we need to run the heatmap dialog
        if not self.heatmap_active:
            self.heatmap_active = True
            HeatMapControlDialog(self)
            self.img_no -= 1
            self.go_forward_backward('FORWARD')
        return

        # Get the slider and neighbour state and save it
        self.save_density_ratio_slider_state_into_df_experiment()
        self.save_variability_slider_state_into_df_experiment()
        self.save_neighbour_state_into_df_experiment()

        # Generate the graphpad and pdf directories if needed
        # create_output_directories_for_graphpad(self.experiment_directory)

        # Generate the graphpad info for summary statistics
        # df_stats = analyse_all_images(self.experiment_directory)
        # create_summary_graphpad(self.experiment_directory, df_stats)

    def set_for_all_slider(self):
        self.experiments_changed = True

        self.df_experiment['Density Ratio Setting'] = self.sc_density_ratio.get()
        self.df_experiment['Variability Setting'] = self.sc_variability.get()

    def track_duration_changed(self, _):
        self.select_squares_for_display()
        self.display_selected_squares()

    def variability_changed(self, _):
        self.experiments_changed = True
        self.select_squares_for_display()
        self.display_selected_squares()

    def density_ratio_changed(self, _):
        self.experiments_changed = True
        self.select_squares_for_display()
        self.display_selected_squares()

    # def provide_report_on_all_squares(self, _):
    #
    #     cell_ids = self.df_squares['Cell Id'].unique()
    #     cell_ids.sort()
    #     nr_cells = len(cell_ids)
    #     nr_squares = len(self.df_squares)
    #
    #     print("All squares report")
    #     print('------------------')
    #     print("Number of squares: ", nr_squares)
    #     print("Number of cells: ", nr_cells)
    #
    #     print(f'Cell Id |----------Tau--------------|--------Density------------|-------Variability--------|')
    #     print(f'         Mean     Sd    Max    Min   Mean     Sd    Max   Min    Mean    Sd     Max    Min  ')
    #
    #     for cell_id in cell_ids:
    #         df_cells = self.df_squares[self.df_squares['Cell Id'] == cell_id]
    #         df_cells = df_cells[['Square Nr', 'Label Nr', 'Tau', 'Density', 'Variability', 'Density Ratio']]
    #
    #         mean_tau = round(df_cells['Tau'].mean(), 0)
    #         sd_tau = round(df_cells['Tau'].std(), 0)
    #         max_tau = round(df_cells['Tau'].max(), 0)
    #         min_tau = round(df_cells['Tau'].min(), 0)
    #
    #         mean_density = round(df_cells['Density'].mean(), 0)
    #         sd_density = round(df_cells['Density'].std(), 0)
    #         max_density = round(df_cells['Density'].max(), 0)
    #         min_density = round(df_cells['Density'].min(), 0)
    #
    #         mean_variability = round(df_cells['Variability'].mean(), 2)
    #         sd_variability = round(df_cells['Variability'].std(), 2)
    #         max_variability = round(df_cells['Variability'].max(), 2)
    #         min_variability = round(df_cells['Variability'].min(), 2)
    #
    #         print(
    #             f'{cell_id:6} {mean_tau:6} {sd_tau:6} {max_tau:6} {min_tau:6} {mean_density:6} {sd_density:6} {max_density:6} {min_density:6} {mean_variability:6} {sd_variability:6} {max_variability:6} {min_variability:6}')
    #
    #     print('\n\n')
    #
    #     for cell_id in cell_ids:
    #         df_cells = self.df_squares[self.df_squares['Cell Id'] == cell_id]
    #         df_cells = df_cells[['Square Nr', 'Label Nr', 'Tau', 'Density', 'Variability', 'Density Ratio']]
    #
    #         print(f'\n\nCell Id: {cell_id:6} \n')
    #         print(df_cells)
    #         print('\n')

    def provide_report_on_cell(self, _, cell_nr):
        """
        Invoked by right-clicking on a cell radio button. Only when there are actually squares defined for the cell,
        information will be shown, including a histogram of the Tau values

        :param _:
        :param cell_nr:
        :return:
        """

        # See if there are any squares defined for this cell
        df_selection = self.df_squares[self.df_squares['Cell Id'] == cell_nr]
        df_visible = df_selection[df_selection['Visible']]
        if len(df_visible) == 0:
            paint_logger.debug(
                f'There are {len(df_selection)} squares defined for cell {cell_nr}, but none are visible')
        else:
            # The labels and tau values for the visible squares of that cell are retrieved
            tau_values = list(df_visible['Tau'])
            labels = list(df_visible['Label Nr'])

            print(f'There are {len(df_visible)} squares visible for cell {cell_nr}: {labels}')
            print(f'The tau values for cell {cell_nr} are: {tau_values}')

            cell_ids = list(df_visible['Label Nr'])
            cell_str_ids = list(map(str, cell_ids))
            plt.figure(figsize=(5, 5))
            plt.bar(cell_str_ids, tau_values)
            plt.ylim(0, 500)

            # Plot the numerical values
            for i in range(len(tau_values)):
                plt.text(cell_str_ids[i],
                         tau_values[i] + 10,
                         str(tau_values[i]),
                         horizontalalignment='center',
                         verticalalignment='center')
            plt.title(self.image_name + ' - Cell ' + str(cell_nr))
            plt.show()
        return

    def select_squares_for_display(self):
        """
        Determine which squares are visible and set the 'Visible' column in the df_squares DataFrame
        :return:
        """

        # All squares are invisible, unless the variability is sufficiently small
        self.df_squares['Variability Visible'] = False
        self.df_squares.loc[
            self.df_squares['Variability'] <= round(self.sc_variability.get(), 1), 'Variability Visible'] = True

        # All squares are invisible, unless the density ratio is sufficiently large
        self.df_squares['Density Ratio Visible'] = False
        self.df_squares.loc[
            self.df_squares['Density Ratio'] >= round(self.density_ratio.get(), 1), 'Density Ratio Visible'] = True

        # All squares are invisible, unless the max track duration is within the min and max limits
        self.df_squares['Duration Visible'] = False
        mask = (self.df_squares['Max Track Duration'] > self.track_min_duration.get()) & \
               (self.df_squares['Max Track Duration'] < self.track_max_duration.get())
        self.df_squares.loc[mask, 'Duration Visible'] = True

        # All squares are visible, unless the Relaxed or Strict neighbour state is not satisfied
        self.df_squares['Neighbour Visible'] = True
        neighbour_state = self.neighbour_var.get()
        if neighbour_state == "Relaxed":
            eliminate_isolated_squares_relaxed(self.df_squares, self.nr_of_squares_in_row)
        elif neighbour_state == "Strict":
            eliminate_isolated_squares_strict(self.df_squares, self.nr_of_squares_in_row)

        # Squares are visible if they are visible based on the sliders and the neighbour state and if there is a valid Tau
        self.df_squares['Visible'] = (self.df_squares['Valid Tau'] &
                                      self.df_squares['Density Ratio Visible'] &
                                      self.df_squares['Variability Visible'] &
                                      self.df_squares['Neighbour Visible'] &
                                      self.df_squares['Duration Visible'])

    def display_selected_squares(self):
        """
        Display the squares on the left image canvas, that have the Visible flag set
        :return:
        """

        # Clear the screen and reshow the picture
        self.cn_left_image.delete("all")
        self.cn_left_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])

        # Bind left buttons for canvas
        self.cn_left_image.bind('<Button-1>', lambda e: self.start_rectangle(e))
        self.cn_left_image.bind('<ButtonRelease-1>', lambda e: self.define_rectangle(e))
        self.cn_left_image.bind('<B1-Motion>', lambda e: self.increase_rectangle_size(e))

        if self.show_squares:
            # If there are no squares you can stop here
            if len(self.df_squares) > 0:
                for index, squares_row in self.df_squares.iterrows():
                    if squares_row['Visible']:
                        self.draw_single_square(squares_row)

    def draw_single_square(self, squares_row, color='white'):

        colour_table = {1: ('red', 'white'),
                        2: ('yellow', 'white'),
                        3: ('green', 'white'),
                        4: ('magenta', 'white'),
                        5: ('cyan', 'white'),
                        6: ('black', 'white')}

        square_nr = squares_row['Square Nr']
        cell_id = squares_row['Cell Id']
        label_nr = squares_row['Label Nr']

        col_nr = square_nr % self.nr_of_squares_in_row
        row_nr = square_nr // self.nr_of_squares_in_row
        width = 512 / self.nr_of_squares_in_row
        height = 512 / self.nr_of_squares_in_row

        square_tag = f'square-{square_nr}'
        text_tag = f'text-{square_nr}'

        if cell_id == -1:  # The square is deleted (for good), stop processing
            return
        elif cell_id == 0:  # Square is removed from a cell
            # Draw the outline without filling the rectangle
            rect_item = self.cn_left_image.create_rectangle(
                col_nr * width, row_nr * width, col_nr * width + width, row_nr * height + height,
                outline="white", fill="", width=0.5, tags=square_tag)

            if self.show_squares_numbers:
                text_item = self.cn_left_image.create_text(
                    col_nr * width + 0.5 * width, row_nr * width + 0.5 * width, text=str(label_nr),
                    font=('Arial', -10), fill=color, tags=text_tag)
        else:  # A square is allocated to a cell
            # Draw the outline without filling the rectangle
            rect_item = self.cn_left_image.create_rectangle(
                col_nr * width, row_nr * width, col_nr * width + width, row_nr * height + height,
                outline=colour_table[self.df_squares.loc[square_nr]['Cell Id']][0], fill="", width=3, tags=square_tag)

            if self.show_squares_numbers:
                text_item = self.cn_left_image.create_text(
                    col_nr * width + 0.5 * width, row_nr * width + 0.5 * width,
                    text=str(self.df_squares.loc[square_nr]['Label Nr']), font=('Arial', -10),
                    fill=colour_table[self.df_squares.loc[square_nr]['Cell Id']][1], tags=text_tag)

        # Create a transparent rectangle (clickable area)
        invisible_rect = self.cn_left_image.create_rectangle(
            col_nr * width, row_nr * width, col_nr * width + width, row_nr * height + height,
            outline="", fill="", tags=f"invisible-{square_nr}")

        # Bind events to the invisible rectangle (transparent clickable area)
        self.cn_left_image.tag_bind(
            invisible_rect, '<Button-1>', lambda e: self.square_assigned_to_cell(square_nr))
        self.cn_left_image.tag_bind(
            invisible_rect, '<Button-2>', lambda e: self.provide_information_on_square(
                e, self.df_squares.loc[square_nr]['Label Nr'], square_nr))

    def square_assigned_to_cell(self, square_nr):

        # Retrieve the old and new cell id
        old_cell_id = self.df_squares.at[square_nr, 'Cell Id']
        new_cell_id = int(self.cell_var.get())
        if new_cell_id == old_cell_id:
            new_cell_id = 0

        # Delete the current square
        square_tag = f'square-{square_nr}'
        text_tag = f'text-{square_nr}'
        self.cn_left_image.delete(square_tag, text_tag)
        self.cn_left_image.delete(text_tag)

        # Draw the new one
        self.draw_single_square(self.df_squares.loc[square_nr])

        # Record the new cell id`
        self.df_squares.at[square_nr, 'Cell Id'] = int(new_cell_id)

    def provide_information_on_square(self, event, label_nr, square_nr):
        """
        After right-clicking on a square, provides information on the square and shows it as a popup

        :param event:
        :param label_nr:
        :param square_nr:
        :return:
        """

        # Define the popup
        if self.pop_square_info  is None:
            self.pop_square_info = Toplevel(root)
            self.pop_square_info.title("Square Info")
            self.pop_square_info.geometry("220x180")

            # Position the popup relative to the main window and the event
            x = root.winfo_x()
            y = root.winfo_y()
            self.pop_square_info.geometry(f"+{x + event.x + 15}+{y + event.y + 40}")

            # Get the data to display from the dataframe
            square_data = self.df_squares.loc[square_nr]

            # Define the fields to display
            fields = [
                ("Label Nr", label_nr),
                ("Square", square_data['Square Nr']),
                ("Tau", square_data['Tau']),
                ("Density", square_data['Density']),
                ("Number of Tracks", square_data['Nr Tracks']),
                ("Density Ratio", square_data['Density Ratio']),
                ("Variability", square_data['Variability']),
                ("Max Track Duration", square_data['Max Track Duration']),
            ]

            # Fill the popup with labels using a loop
            padx_value = 10
            pady_value = 1
            lbl_width = 15

            for idx, (label, value) in enumerate(fields, start=1):
                ttk.Label(self.pop_square_info, text=label, anchor=W, width=lbl_width).grid(row=idx, column=1, padx=padx_value,
                                                                           pady=pady_value)
                ttk.Label(self.pop_square_info, text=str(value), anchor=W).grid(row=idx, column=2, padx=padx_value, pady=pady_value)

            # Bring the focus back to the root window so the canvas can detect more clicks
            self.parent.focus_force()
        else:
            self.pop_square_info.destroy()
            self.pop_square_info = None

    def start_rectangle(self, event):
        self.square_changed = True
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.cn_left_image.create_rectangle(self.start_x,
                                                        self.start_y,
                                                        self.start_x + 1,
                                                        self.start_y + 1,
                                                        fill="", outline='white')

    def increase_rectangle_size(self, event):
        cur_x, cur_y = (event.x, event.y)

        # expand rectangle as you drag the mouse
        self.cn_left_image.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def define_rectangle(self, event):
        cur_x, cur_y = (event.x, event.y)

        # Record the new cell id`
        cell_id = int(self.cell_var.get())

        for i in range(len(self.df_squares)):
            square = self.df_squares.iloc[i]
            # if square_is_visible(self.df_squares, square['Square Nr']):
            if square['Visible']:
                if test_if_square_is_in_rectangle(
                        square['X0'], square['Y0'], square['X1'], square['Y1'], self.start_x, self.start_y,
                        cur_x, cur_y):
                    self.df_squares.at[square['Square Nr'], 'Cell Id'] = int(cell_id)

        self.display_selected_squares()

    def configure_widgets_state(self, state):
        self.rb_neighbour_free.configure(state=state)
        self.rb_neighbour_strict.configure(state=state)
        self.rb_neighbour_relaxed.configure(state=state)

        self.rb_cell0.configure(state=state)
        self.rb_cell1.configure(state=state)
        self.rb_cell2.configure(state=state)
        self.rb_cell3.configure(state=state)
        self.rb_cell4.configure(state=state)
        self.rb_cell5.configure(state=state)
        self.rb_cell6.configure(state=state)

        self.sc_variability.configure(state=state, takefocus=(state == NORMAL))
        self.sc_density_ratio.configure(state=state, takefocus=(state == NORMAL))

    def select_neighbour_button(self):

        self.experiments_changed = True

        self.cn_left_image.delete("all")
        self.cn_left_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])

        self.neighbour_mode = self.neighbour_var.get()

        self.df_squares['Neighbour Setting'] = self.neighbour_mode
        self.select_squares_for_display()
        self.display_selected_squares()

    def go_forward_backward(self, direction):
        # The function is called when we switch image

        experiment_warning = False
        square_warning = False

        if self.experiments_changed:
            if self.mode_dir_or_conf == "DIRECTORY":
                response_experiment = self.save_experiment_file_if_requested()
                if response_experiment is None:
                    return
            else:
                experiment_warning = True

        if self.square_changed:
            if self.mode_dir_or_conf == "DIRECTORY":
                response_square = self.save_squares_file_if_requested()
                if response_square is None:
                    return
            else:
                square_warning = True

        if self.mode_dir_or_conf == 'CONF_FILE':
            warnings = []
            if square_warning:
                warnings.append("squares file")
            if experiment_warning:
                warnings.append("experiment file")

            if warnings:
                message = "No saving of " + (" or ".join(warnings)) + " is implemented in configuration mode"
                messagebox.showinfo('Save Warning',message)

            self.square_changed = False
            self.experiments_changed = False

        # Determine what the next image is, depending on the direction
        # Be sure not move beyond the boundaries (could happen when the left and right keys are used)
        if direction == 'FORWARD':
            if self.img_no != len(self.list_images) - 1:
                self.img_no += 1
        elif direction == 'BACKWARD':
            if self.img_no != 0:
                self.img_no -= 1

        # Set the name of the image
        self.image_name = self.list_images[self.img_no]['Left Image Name']

        if self.heatmap_active:
            self.squares_file_name = self.list_images[self.img_no]['Squares File']
            self.df_squares = read_squares_from_file(self.squares_file_name)
            self.display_heatmap()
        else:
            # Place new image in the canvas and draw the squares
            self.cn_left_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])

            self.squares_file_name = self.list_images[self.img_no]['Squares File']
            self.df_squares = read_squares_from_file(self.squares_file_name)
            self.set_variability_slider_state()
            self.set_density_ratio_slider_state()
            # Duration? TODO
            self.set_neighbour_state()
            self.select_squares_for_display()
            self.display_selected_squares()

        # Place new image_bf
        self.cn_right_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Right Image'])
        self.lbl_image_bf_name.set(str(self.img_no + 1) + ":  " + self.list_images[self.img_no]['Right Image Name'])

        # Update information labels
        if self.list_images[self.img_no]['Adjuvant'] is None:
            adj_label = 'No'
        else:
            adj_label = self.list_images[self.img_no]['Adjuvant']
        cell_info = f"({self.list_images[self.img_no]['Cell Type']}) - ({adj_label}) - ({self.list_images[self.img_no]['Probe Type']}) - ({self.list_images[self.img_no]['Probe']})"
        self.text_for_info1.set(cell_info)

        info1 = f"Spots: {self.list_images[self.img_no]['Nr Spots']:,} - Threshold: {self.list_images[self.img_no]['Threshold']}"
        if self.list_images[self.img_no]['Tau'] != 0:
            info1 = f"{info1} - Tau: {int(self.list_images[self.img_no]['Tau'])}"
        self.text_for_info2.set(info1)

        # Set correct state of Forward and back buttons
        if self.img_no == len(self.list_images) - 1:
            self.bn_forward.configure(state=DISABLED)
        else:
            self.bn_forward.configure(state=NORMAL)

        if self.img_no == 0:
            self.bn_backward.configure(state=DISABLED)
        else:
            self.bn_backward.configure(state=NORMAL)

        image_name = self.list_images[self.img_no]['Left Image Name']
        self.cb_image_names.set(image_name)

        # Set the correct label for Exclude/Include button
        row_index = self.df_experiment.index[self.df_experiment['Ext Image Name'] == self.image_name].tolist()[0]
        if self.df_experiment.loc[row_index, 'Exclude']:
            self.bn_exclude.config(text='Include')
            self.text_for_info3.set("Excluded")
        else:
            self.bn_exclude.config(text='Exclude')
            self.text_for_info3.set("")

        # Reset user change
        self.square_changed = False

    def read_squares(self, image_name):
        self.squares_file_name = os.path.join(self.experiment_directory_path, image_name, 'grid',
                                              image_name + '-squares.csv')
        self.df_squares = read_squares_from_file(self.list_images[self.img_no]['Squares File'])
        if self.df_squares is None:
            paint_logger.error(f"Function 'read_squares' failed - Squares file {self.squares_file_name} was not found.")
            sys.exit()
        return self.df_squares

    def update_squares_file(self):
        # It is necessary to the squares file, because the user may have made changes
        if self.mode_dir_or_conf == 'DIRECTORY':
            squares_file_path = get_squares_file_path(self.experiment_directory_path, self.image_name)
            squares_file_name = os.path.join(self.experiment_directory_path, self.image_name, 'grid',
                                             self.image_name + '-squares.csv')
        else:
            squares_file_path = os.path.join(self.experiment_directory_path,
                                             str(self.df_experiment.iloc[self.img_no]['Experiment Date']),
                                             self.image_name,
                                             'grid',
                                             self.image_name + '-squares.csv')
        save_squares_to_file(self.df_squares, squares_file_path)  # TODO

    # ---------------------------------------------
    # ------------------ Heatmap ------------------
    # ---------------------------------------------

    def update_heatmap_rb_value(self, *args):

        selected_idx = self.rb_heatmap_parameter_value.get()
        if selected_idx == -1:
            self.heatmap_active = False
            self.select_squares_for_display()
            self.display_selected_squares()
        else:
            self.heatmap_active = True
            self.img_no -= 1
            self.go_forward_backward('FORWARD')

        # selected_name = self.option_names[selected_idx - 1]  # Subtract 1 to match the list index
        # self.lbl_radio_value.config(text=f"Selected Option: {selected_name}")

    def display_heatmap(self):

        # Clear the screen and reshow the picture
        self.cn_left_image.delete("all")

        colors = get_colormap_colors('Blues', 20)
        heatmap_mode = self.rb_heatmap_parameter_value.get()

        heatmapdata, min_val, max_val = get_heatmap_data(self.df_squares, self.df_all_squares, heatmap_mode)

        for square_number, value in enumerate(heatmapdata):
            self.draw_heatmap_square(square_number, value, min_val, max_val, colors)

        # if len(self.df_squares) > 0:
        #     for index, squares_row in self.df_squares.iterrows():
        #         if squares_row['Visible']:
        #             self.draw_single_square(squares_row, 'black')

    def draw_heatmap_square(self, square_nr, value, min_value, max_value, colors):

        col_nr = square_nr % self.nr_of_squares_in_row
        row_nr = square_nr // self.nr_of_squares_in_row
        width = 512 / self.nr_of_squares_in_row
        height = 512 / self.nr_of_squares_in_row

        color_index = get_color_index(value, max_value, min_value, 20)
        color = colors[color_index]

        self.cn_left_image.create_rectangle(
            col_nr * width, row_nr * width, col_nr * width + width, row_nr * height + height,
            fill=color, outline=color)


def save_as_png(canvas, file_name):
    # First save as a postscript file
    canvas.postscript(file=file_name + '.ps', colormode='color')

    # Then let PIL convert to a png file
    img = Image.open(file_name + '.ps')
    img.save(f"{file_name}.png", 'png')


def save_square_info_to_batch(self):  # TODO
    for index, row in self.df_experiment.iterrows():
        self.squares_file_name = self.list_images[self.img_no]['Squares File']
        df_squares = read_squares_from_file(self.squares_file_name)
        if df_squares is None:
            paint_logger.error("Function 'save_square_info_to_batch' failed: - Square file does not exist")
            sys.exit()
        if len(df_squares) > 0:
            nr_visible_squares = len(df_squares[df_squares['Visible']])
            nr_total_squares = len(df_squares)
            squares_ratio = round(nr_visible_squares / nr_total_squares, 2)
        else:
            nr_visible_squares = 0
            nr_total_squares = 0
            squares_ratio = 0.0

        self.df_experiment.loc[index, 'Nr Visible Squares'] = nr_visible_squares
        self.df_experiment.loc[index, 'Nr Total Squares'] = nr_total_squares
        self.df_experiment.loc[index, 'Squares Ratio'] = squares_ratio


if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    root.eval('tk::PlaceWindow . center')
    dialog_result = SelectViewerDialog(root)
    proceed, root_directory, conf_file, mode_dir_or_conf = dialog_result.get_result()

    if proceed:
        root = tk.Tk()
        root.withdraw()
        root.eval('tk::PlaceWindow . center')
        paint_logger.debug(f'Mode: {mode_dir_or_conf}')
        if mode_dir_or_conf == 'DIRECTORY':
            paint_logger.info(f'Root directory: {root_directory}')
        else:
            paint_logger.debug(f'Project file: {conf_file}')

        image_viewer = ImageViewer(root, root_directory, conf_file, mode_dir_or_conf)

    root.mainloop()
