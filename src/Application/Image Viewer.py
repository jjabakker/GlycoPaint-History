import os
import platform
import shutil
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
import pandas as pd
from PIL import Image

from src.Application.Image_Viewer.Define_Cell_Dialog.Class_DefineCellDialog import DefineCellDialog
from src.Application.Image_Viewer.Define_Select_Square_Dialog.Class_SelectSquareDialog import SelectSquareDialog
from src.Application.Image_Viewer.Heatmap_Dialog.Class_HeatmapDialog import HeatMapDialog
from src.Application.Image_Viewer.Heatmap_Dialog.Heatmap_Support import (
    get_colormap_colors, get_color_index,
    get_heatmap_data)
from src.Application.Image_Viewer.Select_Recording_Dialog.Class_Select_Recording_Dialog import SelectRecordingDialog
from src.Application.Image_Viewer.Select_Viewer_Data_Dialog.Class_SelectViewerDataDialog import SelectViewerDataDialog
from src.Application.Image_Viewer.Utilities.Display_Selected_Squares import (
    display_selected_squares_do_the_work,
    mark_selected_squares_do_the_work)
from src.Application.Image_Viewer.Utilities.Get_Images import get_images
from src.Application.Image_Viewer.Utilities.Image_Viewer_Support_Functions import (
    test_if_square_is_in_rectangle,
    save_as_png)
from src.Application.Image_Viewer.Utilities.Select_Squares_For_Display import select_squares_for_display_do_the_work
from src.Application.Utilities.General_Support_Functions import (
    read_squares_from_file,
    save_experiment_to_file,
    save_squares_to_file)
from src.Application.Utilities.Paint_Messagebox import paint_messagebox
from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name)

# Log to an appropriately named file
paint_logger_change_file_handler_name('Image Viewer.log')


# ----------------------------------------------------------------------------------------
# ImageViewer Class
# ----------------------------------------------------------------------------------------

class ImageViewer(tk.Tk):

    def __init__(self, parent, user_specified_directory, user_specified_mode):

        super().__init__()
        self.parent = tk.Toplevel(parent)
        self.parent.resizable(False, False)

        # Save the parameters
        self.user_specified_directory = user_specified_directory
        self.user_specified_mode = user_specified_mode

        self.initialize_variables()

        self.setup_ui()
        self.load_images_and_config()
        self.setup_exclude_button()
        self.setup_heatmap()

        # Bind keys for navigation
        parent.bind('<Right>', lambda event: self.on_forward_backward('FORWARD'))
        parent.bind('<Left>', lambda event: self.on_forward_backward('BACKWARD'))

        # Ensure the user can't close the window by clicking the X button
        self.parent.protocol("WM_DELETE_WINDOW", self.on_exit_viewer)

    def setup_heatmap(self):
        self.slider_value = tk.DoubleVar()

        self.heatmap_option = tk.IntVar()
        self.heatmap_option.set(1)  # Default selection is the first option

        self.heatmap_global_min_max = tk.IntVar()
        self.heatmap_global_min_max.set(1)  # Default selection is the first option

        # The heatmap_type_selection_changed function is called by the UI when a radio button is clicked
        self.heatmap_option.trace_add("write", self.heatmap_type_selection_changed)

        self.checkbox_value = tk.BooleanVar()
        self.checkbox_value.set(False)  # Default is unchecked

    def initialize_variables(self):

        self.img_no = 0
        self.image_directory = None

        self.df_all_squares = None
        self.squares_file_name = None

        # UI state variables
        self.start_x = None
        self.start_y = None
        self.rect = None

        # Variables to keep track if the user changed something
        self.squares_changed = False
        self.experiment_changed = False

        # Variables indicating whether to show squares and square numbers in the left pane
        self.show_squares_numbers = True
        self.show_squares = True

        # Variables to hold the information on the current image
        self.max_allowable_variability = None
        self.min_required_density_ratio = None
        self.min_track_duration = None
        self.max_track_duration = None
        self.neighbour_state = None

        # Variables to hold references to the Dialogs, initially all empty
        self.select_square_dialog = None
        self.heatmap_control_dialog = None
        self.define_cells_dialog = None
        self.square_info_popup = None
        self.select_recording_dialog = None

        self.squares_in_rectangle = []

        self.saved_list_images = []
        self.df_all_squares = None

        self.parent.title(f'Image Viewer - {self.user_specified_directory}')

    def setup_ui(self):
        """
        Sets up the UI by defining the top level frames
        For each frame a setup function is called
        """

        self.content = ttk.Frame(self.parent, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))

        self.frame_images = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_navigation_buttons = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_controls = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))

        self.frame_images.grid(column=0, row=0, rowspan=2, padx=5, pady=5, sticky=tk.N)
        self.frame_navigation_buttons.grid(column=0, row=2, padx=5, pady=5, sticky=tk.N)
        self.frame_controls.grid(column=1, row=0, rowspan=2, padx=5, pady=5, sticky=N)

        self.setup_frame_images()
        self.setup_frame_navigation_buttons()
        self.setup_frame_controls()

        self.content.grid(column=0, row=0)

    # ----------------------------------------------------------------------------------------
    # Setup functions for the frame_images content
    # ----------------------------------------------------------------------------------------

    def setup_frame_images(self):

        frame_width = 530
        frame_height = 690

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

        self.parent.bind('<Key>', self.on_key_pressed)

        # Define the labels and combobox widgets for the images
        self.list_images = []
        self.list_of_image_names = []
        self.cb_image_names = ttk.Combobox(
            self.frame_picture_left, values=self.list_of_image_names, state='readonly', width=30)

        # Label for the right image name
        self.lbl_image_bf_name = StringVar(self.parent, "")
        lbl_image_bf_name = ttk.Label(self.frame_picture_right, textvariable=self.lbl_image_bf_name)

        # Labels for image info
        self.text_for_info1 = StringVar(self.parent, "")
        self.lbl_info1 = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info1)

        self.text_for_info2 = StringVar(self.parent, "")
        self.lbl_info2 = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info2)

        self.text_for_info3 = StringVar(self.parent, "")
        self.lbl_info3 = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info3)

        self.text_for_info4 = StringVar(self.parent, "")
        self.lbl_info4 = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info4)

        # Create a ttk style object
        self.style = ttk.Style()
        self.style.configure("Red.Label", foreground="red")
        self.style.configure("Black.Label", foreground="red")

        # Bind combobox selection
        self.cb_image_names.bind("<<ComboboxSelected>>", self.image_selected)

        # Layout labels and combobox
        self.cb_image_names.grid(column=0, row=1, padx=5, pady=5)
        self.lbl_info1.grid(column=0, row=2, padx=5, pady=5)
        self.lbl_info2.grid(column=0, row=3, padx=5, pady=5)
        self.lbl_info3.grid(column=0, row=4, padx=5, pady=5)
        self.lbl_info4.grid(column=0, row=5, padx=5, pady=5)
        lbl_image_bf_name.grid(column=0, row=1, padx=0, pady=0)

    def setup_frame_navigation_buttons(self):
        # This frame is part of the content frame and contains the following buttons: bn_forward, bn_exclude, bn_backward, bn_exit

        self.bn_end = ttk.Button(
            self.frame_navigation_buttons, text='>>', command=lambda: self.on_forward_backward('END'))
        self.bn_forward = ttk.Button(
            self.frame_navigation_buttons, text='>', command=lambda: self.on_forward_backward('FORWARD'))
        self.bn_exclude = ttk.Button(self.frame_navigation_buttons, text='Reject', command=lambda: self.on_exinclude())
        self.bn_backward = ttk.Button(
            self.frame_navigation_buttons, text='<', command=lambda: self.on_forward_backward('BACKWARD'))
        self.bn_start = ttk.Button(
            self.frame_navigation_buttons, text='<<', command=lambda: self.on_forward_backward('START'))
        self.bn_exit = ttk.Button(self.frame_navigation_buttons, text='Exit', command=lambda: self.on_exit_viewer())

        # Layout the buttons
        self.bn_start.grid(column=0, row=0, padx=5, pady=5)
        self.bn_backward.grid(column=1, row=0, padx=5, pady=5)
        self.bn_exclude.grid(column=2, row=0, padx=5, pady=5)
        self.bn_forward.grid(column=3, row=0, padx=5, pady=5)
        self.bn_end.grid(column=4, row=0, padx=5, pady=5)
        self.bn_exit.grid(column=5, row=0, padx=30, pady=5)

        # Initially disable the back button
        self.bn_backward.configure(state=tk.DISABLED)

    def setup_frame_controls(self):
        # This frame is part of the content frame and contains the following frames: frame_commands

        self.frame_commands = ttk.Frame(self.frame_controls, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_save_commands = ttk.Frame(self.frame_controls, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.setup_frame_commands()
        self.setup_frame_save_commands()
        self.frame_commands.grid(column=0, row=3, padx=5, pady=5)
        self.frame_save_commands.grid(column=0, row=6, padx=5, pady=5)

    def setup_frame_commands(self):
        # This frame is part of frame_controls and contains the following buttons: bn_output, bn_reset, bn_excel, bn_histogram

        button_width = 13

        self.bn_select_recording = ttk.Button(
            self.frame_commands, text='Select Recordings', command=lambda: self.on_select_recording(),
            width=button_width)
        self.bn_show_heatmap = ttk.Button(
            self.frame_commands, text='Heatmap', command=lambda: self.on_show_heatmap(), width=button_width)
        self.bn_show_select_squares = ttk.Button(
            self.frame_commands, text='Select Squares', command=lambda: self.on_show_select_squares(),
            width=button_width)
        self.bn_show_define_cells = ttk.Button(
            self.frame_commands, text='Define Cells', command=lambda: self.on_show_define_cells(), width=button_width)
        self.bn_histogram = ttk.Button(
            self.frame_commands, text='Histogram', command=lambda: self.on_histogram(), width=button_width)
        self.bn_excel = ttk.Button(
            self.frame_commands, text='Excel', command=lambda: self.on_how_excel(), width=button_width)
        self.bn_output = ttk.Button(
            self.frame_commands, text='Output', command=lambda: self.on_run_output(), width=button_width)
        self.bn_reset = ttk.Button(
            self.frame_commands, text='Reset', command=lambda: self.on_reset_image(), width=button_width)

        self.bn_select_recording.grid(column=0, row=0, padx=5, pady=5)
        self.bn_show_heatmap.grid(column=0, row=1, padx=5, pady=5)
        self.bn_show_select_squares.grid(column=0, row=2, padx=5, pady=5)
        self.bn_show_define_cells.grid(column=0, row=3, padx=5, pady=5)
        self.bn_output.grid(column=0, row=4, padx=5, pady=5)
        self.bn_reset.grid(column=0, row=5, padx=5, pady=5)
        self.bn_excel.grid(column=0, row=6, padx=5, pady=5)

    def setup_frame_save_commands(self):

        # Create three radio buttons for the neighbour mode
        self.save_state_var = tk.StringVar(value="Ask")
        self.rb_always_save = tk.Radiobutton(
            self.frame_save_commands, text="Always Save", variable=self.save_state_var, width=12, value="Always",
            anchor=tk.W)
        self.rb_never_save = tk.Radiobutton(
            self.frame_save_commands, text="Never Save", variable=self.save_state_var, width=12, value="Never",
            anchor=tk.W)
        self.rb_ask_toSave = tk.Radiobutton(
            self.frame_save_commands, text="Ask to Save", variable=self.save_state_var, width=12, value="Ask",
            anchor=tk.W)

        # Place the radio buttons and button in the grid

        self.rb_always_save.grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.rb_never_save.grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        self.rb_ask_toSave.grid(column=0, row=2, padx=5, pady=5, sticky=tk.W)

    def load_images_and_config(self):

        # Read the All Squares file
        self.df_all_squares = read_squares_from_file(
            os.path.join(self.user_specified_directory, 'All Squares.csv'))
        if self.df_all_squares is None:
            self.show_error_and_exit("No 'All Squares.csv.csv' file, Did you select an image directory?")

        # Read the All Experiments file
        self.df_experiment = pd.read_csv(os.path.join(self.user_specified_directory, 'All Recordings.csv'))
        if self.df_experiment is None:
            self.show_error_and_exit("No 'experiment_squares.csv' file, Did you select an image directory?")
        self.df_experiment.set_index('Ext Recording Name', drop=False, inplace=True)

        # Check that the two align
        if set(self.df_all_squares['Ext Recording Name']) != set(self.df_experiment['Ext Recording Name']):
            self.show_error_and_exit(
                "The recordings in the 'All Squares' file do not align with the 'All Experiments' file")

        self.nr_of_squares_in_row = int(self.df_experiment.iloc[0]['Nr of Squares in Row'])

        # Load the images
        self.list_images = get_images(self, initial=True)
        if not self.list_images:
            self.show_error_and_exit(f"No images were found in directory {self.user_specified_directory}.")

        # Load the combobox with the image names
        self.list_of_image_names = [image['Left Image Name'] for image in self.list_images]
        self.cb_image_names['values'] = self.list_of_image_names

        self.initialise_image_display()
        self.img_no = -1
        self.on_forward_backward('FORWARD')

    def on_select_recording(self):
        if any(dialog is not None for dialog in
               [self.select_square_dialog, self.define_cells_dialog, self.heatmap_control_dialog,
                self.select_recording_dialog]):
            return
        else:
            self.select_recording_dialog = SelectRecordingDialog(self, self.df_experiment, self.on_recording_selection)

    def on_show_heatmap(self):
        # If the heatmap is not already  active, then we need to run the heatmap dialog

        if any(dialog is not None for dialog in
               [self.select_square_dialog, self.define_cells_dialog, self.heatmap_control_dialog,
                self.select_recording_dialog]):
            return
        else:
            self.set_dialog_buttons(tk.DISABLED)
            self.heatmap_control_dialog = HeatMapDialog(self)
            # self.heatmap_control_dialog.on_heatmap_variable_change()
            self.img_no -= 1
            self.on_forward_backward('FORWARD')

    def set_dialog_buttons(self, state):
        self.bn_show_heatmap.configure(state=state)
        self.bn_show_define_cells.configure(state=state)
        self.bn_show_select_squares.configure(state=state)

    def on_show_select_squares(self):
        # If the select square dialog is not already active, then we need to run the select square dialog

        if any(dialog is not None for dialog in
               [self.select_square_dialog, self.define_cells_dialog, self.heatmap_control_dialog,
                self.select_recording_dialog]):
            return
        else:
            self.set_dialog_buttons(tk.DISABLED)

            self.min_required_density_ratio = self.list_images[self.img_no]['Min Required Density Ratio']
            self.max_allowable_variability = self.list_images[self.img_no]['Max Allowable Variability']
            self.neighbour_state = self.list_images[self.img_no]['Neighbour Mode']

            self.min_track_duration = 1
            self.max_track_duration = 199

            if self.select_square_dialog is None:
                self.select_square_dialog = SelectSquareDialog(
                    self, self.update_select_squares, self.min_required_density_ratio, self.max_allowable_variability,
                    self.min_track_duration, self.max_track_duration, self.neighbour_state)

    def on_show_define_cells(self):

        if any(dialog is not None for dialog in
               [self.select_square_dialog, self.define_cells_dialog, self.heatmap_control_dialog,
                self.select_recording_dialog]):
            return
        else:
            self.set_dialog_buttons(tk.DISABLED)
            self.define_cells_dialog = DefineCellDialog(
                self, self.callback_to_assign_squares_to_cell_id, self.callback_to_reset_square_selection,
                self.callback_to_close_define_cells)

    def callback_to_close_define_cells(self):
        self.define_cells_dialog = None

    def callback_to_reset_square_selection(self):
        """
        This function is called by the DefineCellsDialog
        It will empty the list og squares that are currently selected and update the display
        """

        self.squares_in_rectangle = []
        self.display_selected_squares()

    def callback_to_assign_squares_to_cell_id(self, cell_id):
        """
        This function is called by the DefineCellsDialog when a cell id has been selected to is assigned to a square
        See if there are any squares selected and if so update the cell id, then update the display
        """

        for square_nr in self.squares_in_rectangle:
            self.df_squares.at[square_nr, 'Cell Id'] = int(cell_id)

        self.squares_changed = True
        self.squares_in_rectangle = []
        self.display_selected_squares()

    def setup_exclude_button(self):
        # Set up the exclude/include button state

        row_index = self.df_experiment.index[self.df_experiment['Ext Recording Name'] == self.image_name].tolist()[0]
        if self.df_experiment.loc[row_index, 'Exclude']:
            self.bn_exclude.config(text='Include')
            self.text_for_info4.set('Excluded')
            self.lbl_info4.config(style="Red.Label")
        else:
            self.bn_exclude.config(text='Exclude')
            self.text_for_info4.set('')
            self.lbl_info4.config(style="Black.Label")

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
        info3 = f"Min Required Density Ratio: {self.list_images[self.img_no]['Min Required Density Ratio']:,} - Max Allowable Variability: {self.list_images[self.img_no]['Max Allowable Variability']}"
        self.text_for_info3.set(info3)

    def on_exinclude(self):
        """
        Toggle the state of the recording. Change the button text and the info text
        :return:
        """

        # row_index = self.df_experiment.index[self.df_experiment['Ext Recording Name'] == self.image_name].tolist()[0]
        # This was complex code, but the index is already the image name

        row_index = self.image_name
        if not self.df_experiment.loc[row_index, 'Exclude']:
            self.df_experiment.loc[row_index, 'Exclude'] = True
            self.bn_exclude.config(text='Include')  # Change the button text
            self.text_for_info4.set('Excluded')  # Change the info text to 'Excluded'
            self.lbl_info4.config(style="Red.Label")
            self.lbl_info4.configure(foreground='red')
        else:
            self.df_experiment.loc[row_index, 'Exclude'] = False
            self.bn_exclude.config(text='Exclude')  # Change the button text
            self.text_for_info4.set('')
            self.lbl_info4.config(style="Black.Label")
        self.experiment_changed = True

    def on_key_pressed(self, event):
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
        elif event.keysym == 'n':
            self.show_squares_numbers = not self.show_squares_numbers
            if self.show_squares:
                self.show_numbers = True
            self.display_selected_squares()

        # Pressing 'o' will generate a pdf file containing all the images
        elif event.keysym == 'o':
            self.output_pictures_to_pdf()

        elif event.keysym == 't':
            self.show_squares = not self.show_squares
            self.display_selected_squares()

        elif event.keysym == 'h':
            self.on_histogram()

        elif event.keysym == 'Right':
            if event.state & 0x0001:  # 0x0001 is the bit mask for Shift
                self.on_forward_backward('END')
            else:
                self.on_forward_backward('FORWARD')

        elif event.keysym == 'Left':
            if event.state & 0x0001:  # 0x0001 is the bit mask for Shift
                self.on_forward_backward('START')
            else:
                self.on_forward_backward('BACKWARD')

    def output_pictures_to_pdf(self):
        """
        The function is triggered by pressing 'o' and will generate a pdf file containing all the images.
        :return:
        """

        # Create the squares directory if it does not exist
        squares_dir = os.path.join(self.user_specified_directory, 'Output', 'Squares')
        os.makedirs(squares_dir, exist_ok=True)

        # Cycle through all images
        save_img_no = self.img_no
        self.img_no = -1
        for img_no in range(len(self.list_images)):
            self.on_forward_backward('FORWARD')

            image_name = self.list_images[self.img_no]['Left Image Name']
            paint_logger.debug(f"Writing {image_name} to pdf file {os.path.join(squares_dir, image_name)}")

            # Delete the squares and write the canvas with just the tracks
            self.cn_left_image.delete("all")
            self.cn_left_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])
            save_as_png(self.cn_left_image, os.path.join(squares_dir, image_name))

            # Add the squares and write the canvas complete with squares
            self.select_squares_for_display()
            self.display_selected_squares()
            image_name = image_name + '-squares'
            save_as_png(self.cn_left_image, os.path.join(squares_dir, image_name))

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
        if platform.system() == "Darwin":
            png_images[0].save(pdf_path, "PDF", resolution=200.0, save_all=True, append_images=png_images[1:])


        # Go back to the image where we were
        self.img_no -= 1
        self.on_forward_backward('FORWARD')

    def on_exit_viewer(self):

        status = False
        if self.experiment_changed or self.squares_changed:
            status = self.save_changes()

        if status == False or status == True:
            root.quit()
        else:
            return

    def image_selected(self, _):
        image_name = self.cb_image_names.get()
        paint_logger.debug(image_name)
        index = self.list_of_image_names.index(image_name)
        self.img_no = index - 1
        self.on_forward_backward('FORWARD')

    def on_histogram(self):

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

    def on_how_excel(self):
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
            temp_file = os.path.join(temp_dir, 'Temporary All Squares.csv')

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

    def on_reset_image(self):
        """
        Resets the current image. All squares are displayed, but the variability and density ratio sliders are applied
        :return:
        """

        self.df_squares['Visible'] = True  # ToDo is this ok?
        self.df_squares['Cell Id'] = 0

        self.select_squares_for_display()
        self.display_selected_squares()

    def update_select_squares(self,
                              setting_type: str,
                              density_ratio: float,
                              variability: float,
                              min_duration: float,
                              max_duration: float,
                              neighbour_mode: str) -> None:
        """
        This function is called from the SelectSquareDialog when a control has changed or when the control exists. This
        give an opportunity to update the settings for the current image
        :param setting_type:
        :param density_ratio:
        :param variability:
        :param min_duration:
        :param max_duration:
        :param neighbour_mode:
        :return:
        """
        if setting_type == "Min Required Density Ratio":
            self.min_required_density_ratio = density_ratio
            self.list_images[self.img_no]['Min Required Density Ratio'] = density_ratio
            self.experiment_changed = True
        elif setting_type == "Max Allowable Variability":
            self.max_allowed_variability = variability
            self.list_images[self.img_no]['Max Allowable Variability'] = variability
            self.experiment_changed = True
        elif setting_type == "Neighbour Mode":
            self.neighbour_state = neighbour_mode
            self.list_images[self.img_no]['Neighbour Mode'] = neighbour_mode
            self.experiment_changed = True
        elif setting_type == "Min Track Duration":
            self.min_track_duration = min_duration
        elif setting_type == "Max Track Duration":
            self.max_track_duration = max_duration
        elif setting_type == "Set for All":
            # Set the same settings for all recordings
            self.min_required_density_ratio = density_ratio
            self.max_allowed_variability = variability
            self.min_track_duration = min_duration
            self.max_track_duration = max_duration
            self.neighbour_state = neighbour_mode

            for image in self.list_images:
                image['Min Required Density Ratio'] = density_ratio
                image['Max Allowable Variability'] = variability
                image['Neighbour Mode'] = neighbour_mode

            self.experiment_changed = True
        elif setting_type == "Exit":
            self.select_square_dialog = None
        else:
            paint_logger.error(f"Unknown setting type: {setting_type}")

        self.select_squares_for_display()
        self.display_selected_squares()

        # Update the info line
        info3 = f"Min Required Density Ratio: {density_ratio:,} - Max Allowable Variability: {variability}"
        self.text_for_info3.set(info3)

    def on_run_output(self):
        """
        Prepares the output files.
        For specific sets up probes or cell types, specific functions are needed
        :return:
        """

        # Generate the graphpad and pdf directories if needed
        # create_output_directories_for_graphpad(self.experiment_directory)

        # Generate the graphpad info for summary statistics
        # df_stats = analyse_all_images(self.experiment_directory)
        # create_summary_graphpad(self.experiment_directory, df_stats)

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
        select_squares_for_display_do_the_work(self)

    def display_selected_squares(self):
        display_selected_squares_do_the_work(self)

    def square_assigned_to_cell(self, square_nr):

        if square_nr in self.squares_in_rectangle:
            self.squares_in_rectangle.remove(square_nr)
        else:
            self.squares_in_rectangle.append(int(square_nr))

        self.mark_selected_squares(self.squares_in_rectangle)

    def provide_information_on_square(self, event, label_nr, square_nr):
        """
        After right-clicking on a square, provides information on the square and shows it as a popup
        """

        # Define the popup
        if self.square_info_popup is None:
            self.square_info_popup = Toplevel(root)
            self.square_info_popup.title("Square Info")
            self.square_info_popup.geometry("280x200")

            # Position the popup relative to the main window and the event
            x = root.winfo_x()
            y = root.winfo_y()
            self.square_info_popup.geometry(f"+{x + event.x + 15}+{y + event.y + 40}")

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
                ("Mean Diffusion Coefficient", square_data['Diffusion Coefficient'])
            ]
            # Fill the popup with labels using a loop
            padx_value = 10
            pady_value = 1
            lbl_width = 20

            for idx, (label, value) in enumerate(fields, start=1):
                ttk.Label(self.square_info_popup, text=label, anchor=W, width=lbl_width).grid(row=idx, column=1,
                                                                                              padx=padx_value,
                                                                                              pady=pady_value)
                ttk.Label(self.square_info_popup, text=str(value), anchor=W).grid(row=idx, column=2, padx=padx_value,
                                                                                  pady=pady_value)

            # Bring the focus back to the root window so the canvas can detect more clicks
            self.parent.focus_force()
        else:
            self.square_info_popup.destroy()
            self.square_info_popup = None

    # --------------------------------------------------------------------------------------
    # Rectangle functions
    # --------------------------------------------------------------------------------------

    def start_rectangle(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.cn_left_image.create_rectangle(
            self.start_x, self.start_y, self.start_x + 1, self.start_y + 1, fill="", outline='white')

    def expand_rectangle_size(self, event):
        # Expand rectangle as you drag the mouse
        self.cn_left_image.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def close_rectangle(self, event):

        # Remove the rectangle
        self.cn_left_image.delete(self.rect)

        if self.define_cells_dialog is None:
            pass  # ToDo Maybe open the dialog here

        for i in range(len(self.df_squares)):
            square = self.df_squares.iloc[i]
            if square['Visible']:
                if test_if_square_is_in_rectangle(
                        square['X0'], square['Y0'], square['X1'], square['Y1'], self.start_x, self.start_y,
                        event.x, event.y):
                    self.squares_in_rectangle.append(int(square['Square Nr']))

        # self.mark_selected_squares(self.squares_in_rectangle)
        self.display_selected_squares()

    def mark_selected_squares(self, list_of_squares):

        mark_selected_squares_do_the_work(list_of_squares, self.nr_of_squares_in_row, self.cn_left_image)

    def on_forward_backward(self, direction):
        """
        The function is called when we switch image
        """

        # ----------------------------------------------------------------------------
        # Check if the user has changed the Cell assignments and if so, ask if they want to save
        # ----------------------------------------------------------------------------

        if self.squares_changed:
            self.save_changes()

        # ----------------------------------------------------------------------------
        # Determine what the next image is, depending on the direction
        # Be sure not move beyond the boundaries (could happen when the left and right keys are used)
        # Disable the forward and backward buttons when the boundaries are reached
        # ----------------------------------------------------------------------------

        # Determine the next image number
        if direction == 'START':
            self.img_no = 0
        elif direction == 'END':
            self.img_no = len(self.list_images) - 1
        elif direction == 'FORWARD':
            if self.img_no != len(self.list_images) - 1:
                self.img_no += 1
        elif direction == 'BACKWARD':
            if self.img_no != 0:
                self.img_no -= 1

        # Set the name of the image
        self.image_name = self.list_images[self.img_no]['Left Image Name']

        # Set correct state of Forward and back buttons
        if self.img_no == len(self.list_images) - 1:
            self.bn_forward.configure(state=DISABLED)
            self.bn_end.configure(state=DISABLED)
        else:
            self.bn_forward.configure(state=NORMAL)
            self.bn_end.configure(state=NORMAL)

        if self.img_no == 0:
            self.bn_backward.configure(state=DISABLED)
            self.bn_start.configure(state=DISABLED)
        else:
            self.bn_backward.configure(state=NORMAL)
            self.bn_start.configure(state=NORMAL)

        # image_name = self.list_images[self.img_no]['Left Image Name']
        self.cb_image_names.set(self.image_name)

        # ----------------------------------------------------------------------------
        # Irrespective up heatmap or normal image update the BF image, the bright field
        # and the labels can be updated
        # ----------------------------------------------------------------------------

        # Place new image_bf
        self.cn_right_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Right Image'])
        self.lbl_image_bf_name.set(str(self.img_no + 1) + ":  " + self.list_images[self.img_no]['Right Image Name'])

        # The information labels are updated
        if self.list_images[self.img_no]['Adjuvant'] is None:
            adj_label = 'No'
        else:
            adj_label = self.list_images[self.img_no]['Adjuvant']
        cell_info = f"({self.list_images[self.img_no]['Cell Type']}) - ({adj_label}) - ({self.list_images[self.img_no]['Probe Type']}) - ({self.list_images[self.img_no]['Probe']})"
        self.text_for_info1.set(cell_info)

        info2 = f"Spots: {self.list_images[self.img_no]['Nr Spots']:,} - Threshold: {self.list_images[self.img_no]['Threshold']}"
        if self.list_images[self.img_no]['Tau'] != 0:
            info2 = f"{info2} - Tau: {int(self.list_images[self.img_no]['Tau'])}"
        self.text_for_info2.set(info2)
        # TODO: If saved, the Tau value should be displayed
        info3 = f"Min Required Density Ratio: {self.list_images[self.img_no]['Min Required Density Ratio']:,} - Max Allowable Variability: {self.list_images[self.img_no]['Max Allowable Variability']}"
        self.text_for_info3.set(info3)

        # Set the correct label for Exclude/Include button
        if self.heatmap_control_dialog is None:
            row_index = self.df_experiment.index[self.df_experiment['Ext Recording Name'] == self.image_name].tolist()[
                0]
            if self.df_experiment.loc[row_index, 'Exclude']:
                self.bn_exclude.config(text='Include')
                self.text_for_info4.set("Excluded")
            else:
                self.bn_exclude.config(text='Exclude')
                self.text_for_info4.set("")

        # ----------------------------------------------------------------------------
        # Now it depends what control dialog is up
        # ----------------------------------------------------------------------------

        # If the heatmap control dialog is up just display the heatmap
        if self.heatmap_control_dialog:
            self.df_squares = self.df_all_squares[self.df_all_squares['Ext Recording Name'] == self.image_name]
            self.display_heatmap()
            return

        else:  # update the regular image

            self.cn_left_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])
            self.df_squares = self.df_all_squares[self.df_all_squares['Ext Recording Name'] == self.image_name]

            # Set the filter parameters with values retrieved from the experiment file
            self.min_track_duration = 0  # self.df_experiment.loc[self.image_name]['Min Duration']
            self.max_track_duration = 200  # self.df_experiment.loc[self.image_name]['Max Duration']

            self.min_required_density_ratio = self.list_images[self.img_no]['Min Required Density Ratio']
            self.max_allowable_variability = self.list_images[self.img_no]['Max Allowable Variability']
            self.neighbour_state = self.list_images[self.img_no]['Neighbour Mode']

            if self.select_square_dialog:
                self.select_square_dialog.initialise_controls(
                    self.min_required_density_ratio, self.max_allowable_variability, self.min_track_duration,
                    self.max_track_duration, self.neighbour_state)

        # ----------------------------------------------------------------------------
        # Then display
        # ----------------------------------------------------------------------------

        if self.heatmap_control_dialog:
            self.display_heatmap()
        else:
            self.select_squares_for_display()
            self.display_selected_squares()

        # Reset user change
        self.squares_changed = False

        # Make sure that there is no user square selection left
        self.squares_in_rectangle = []
        self.mark_selected_squares(self.squares_in_rectangle)

    def save_changes(self):

        # See if there is anything to save
        if not (self.experiment_changed or self.squares_changed):
            return False

        # There is something to save but the Never option is selected
        if self.save_state_var.get() == 'Never':
            paint_logger.debug("Changes were not saved, because the 'Never' option was selected.")
            return False

        # There is experiments data to save.
        if self.experiment_changed:
            if self.save_state_var.get() == 'Ask':
                save = self.user_confirms_save('Experiment')
            else:  # Then must be 'Always'
                save = True
            if save:
                for i in range(len(self.list_images)):
                    image_name = self.list_images[i]['Left Image Name']
                    self.df_experiment.loc[image_name, 'Min Required Density Ratio'] = self.list_images[i][
                        'Min Required Density Ratio']
                    self.df_experiment.loc[image_name, 'Max Allowable Variability'] = self.list_images[i][
                        'Max Allowable Variability']
                    self.df_experiment.loc[image_name, 'Neighbour Mode'] = self.list_images[i]['Neighbour Mode']
                save_experiment_to_file(self.df_experiment,
                                        os.path.join(self.user_specified_directory, 'All Recordings.csv'))
                paint_logger.debug(
                    f"Experiment file {os.path.join(self.user_specified_directory, 'All Recordings.csv')} was saved.")
            self.experiment_changed = False

        # There is squares data to save.
        if self.squares_changed:
            if self.save_state_var.get() == 'Ask':
                save = self.user_confirms_save('Squares')
            else:  # Then must be 'Always'
                save = True
            if save:
                self.df_all_squares.set_index(['Unique Key'], inplace=True, drop=False)
                self.df_squares.set_index(['Unique Key'], inplace=True, drop=False)
                self.df_all_squares.update(self.df_squares)
                save_squares_to_file(self.df_all_squares,
                                     os.path.join(self.user_specified_directory, 'All Squares.csv'))
                paint_logger.debug(
                    f"Squares file {os.path.join(self.user_specified_directory, 'All Squares.csv')} was saved.")
            self.squares_changed = False
        return save

    def user_confirms_save(self, mode):
        """
        Ask the user if they want to save the changes
        :return: True if the user wants to save, False if not
        """
        answer = messagebox.askyesno("Save Changes", f"Do you want to save the {mode} changes?")
        return answer

    # ---------------------------------------------------------------------------------------
    # Heatmap Dialog Interaction
    # ---------------------------------------------------------------------------------------

    def heatmap_type_selection_changed(self, *args):

        selected_idx = self.heatmap_option.get()
        if selected_idx == -1:
            self.heatmap_control_dialog = None
            self.display_selected_squares()
        else:

            self.img_no -= 1
            self.on_forward_backward('FORWARD')

        # selected_name = self.option_names[selected_idx - 1]  # Subtract 1 to match the list index
        # self.lbl_radio_value.config(text=f"Selected Option: {selected_name}")

    def display_heatmap(self):

        # Clear the screen and reshow the picture
        self.cn_left_image.delete("all")

        colors = get_colormap_colors('Blues', 20)
        heatmap_mode = self.heatmap_option.get()
        heatmap_global_min_max = self.heatmap_global_min_max.get()

        df_heatmap_data, min_val, max_val = get_heatmap_data(self.df_squares, self.df_all_squares, heatmap_mode,
                                                             heatmap_global_min_max)
        if df_heatmap_data is None:
            paint_messagebox(self.parent, "No data for heatmap", "There is no data for the heatmap")
            return

        for index, row in df_heatmap_data.iterrows():
            draw_heatmap_square(self.cn_left_image, index, self.nr_of_squares_in_row, row['Value'],
                                min_val, max_val, colors)

    # ---------------------------------------------------------------------------------------
    # Recording Selection Dialog Interaction
    # ---------------------------------------------------------------------------------------

    def on_recording_selection(self, selection, selected):
        # Callback to receive the filtered data from the dialog
        # Update the label with the selected filter criteria

        self.select_recording_dialog = None

        if selected == False:
            return

        # If nothing has been selected, do nothing
        if len(selection) == 0:
            return

        # Otherwise, build up the list of images from the saved list of images
        self.list_images = []

        for image in self.saved_list_images:
            choose = True
            for key, value in selection.items():
                if str(image[key]) not in value:
                    choose = False
                    break
            if choose:
                # print(f"Key: {key}, Value: {value}")
                self.list_images.append(image)

        # Update the combobox with the new list of images
        self.list_of_image_names = [image['Left Image Name'] for image in self.list_images]
        self.cb_image_names['values'] = self.list_of_image_names
        self.cb_image_names.set(self.cb_image_names['values'][0])  # @@@

        # Start at 0
        self.on_forward_backward('START')


def draw_heatmap_square(canvas_to_draw_on, square_nr, nr_of_squares_in_row, value, min_value, max_value, colors):
    col_nr = square_nr % nr_of_squares_in_row
    row_nr = square_nr // nr_of_squares_in_row
    width = 512 / nr_of_squares_in_row
    height = 512 / nr_of_squares_in_row

    color_index = get_color_index(value, max_value, min_value, 20)

    color = colors[color_index]

    canvas_to_draw_on.create_rectangle(
        col_nr * width, row_nr * width, col_nr * width + width, row_nr * height + height,
        fill=color, outline=color)


# ---------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    root.eval('tk::PlaceWindow . center')
    dialog_result = SelectViewerDataDialog(root)
    proceed, directory, mode = dialog_result.get_result()

    if proceed:
        root = tk.Tk()
        root.withdraw()
        root.eval('tk::PlaceWindow . center')
        paint_logger.debug(f'Mode: {mode}')
        paint_logger.info(f'Mode is: {mode} - Directory: {directory}')
        image_viewer = ImageViewer(root, directory, mode)

    root.mainloop()
