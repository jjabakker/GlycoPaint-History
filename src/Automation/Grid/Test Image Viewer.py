import os
import platform
import statistics
import subprocess
import sys
import tkinter as tk
from tkinter import *
from tkinter import filedialog
from tkinter import ttk

import matplotlib.pyplot as plt
from PIL import Image, ImageTk

from src.Automation.Support.Analyse_All_Images import (
    analyse_all_images,
    create_summary_graphpad)
from src.Common.Support.LoggerConfig import paint_logger, paint_logger_change_file_handler_name
from src.Automation.Support.Support_Functions import (
    eliminate_isolated_squares_relaxed,
    eliminate_isolated_squares_strict,
    test_if_square_is_in_rectangle,
    create_output_directories_for_graphpad,
    get_default_directories,
    save_default_directories,
    read_batch_from_file,
    read_squares_from_file,
    save_batch_to_file,
    save_squares_to_file)

# Log to an appropriately named file
paint_logger_change_file_handler_name('Image Viewer.log')


def save_as_png(canvas, file_name):
   pass

def save_square_info_to_batch(self):
    pass

def set_for_all_neighbour_state(self):
    self.df_batch['Neighbour Setting'] = self.neighbour_var.get()

def get_images(self, type_of_image):

    paint_directory = self.paint_directory
    df_batch = self.df_batch
    _mode = self.mode

    # Create an empty lst that will hold the images
    list_images = []

    # Cycle through the batch file
    count = 0
    for index in range(len(df_batch)):

        if df_batch.iloc[index]['Process'] == 'No' or df_batch.iloc[index]['Process'] == 'N':
            continue

        image_name = df_batch.iloc[index]['Ext Image Name']

        if _mode == 'Directory':
            image_path = os.path.join(paint_directory, image_name)
        else:
            image_path = os.path.join(paint_directory, str(df_batch.iloc[index]['Experiment Date']), image_name)

        # if os.path.isfile(image_path):
        #     continue

        # If there is no img directory below the image directory, skip it
        img_dir = os.path.join(image_path, "img")
        if not os.path.isdir(img_dir):
            continue

        if _mode == 'Directory':
            bf_dir = os.path.join(paint_directory, "Converted BF Images")
        else:
            bf_dir = os.path.join(paint_directory, str(df_batch.iloc[index]['Experiment Date']), "Converted BF Images")

        # Then get all the files in  the 'img' directory
        all_images_in_img_dir = os.listdir(img_dir)

        # Ignore any file that may have slipped in, such as '.Dstore'
        for img in all_images_in_img_dir:
            if image_name not in img:
                all_images_in_img_dir.remove(img)
        all_images_in_img_dir.sort()

        valid = False
        square_nrs = []

        for img in all_images_in_img_dir:
            if img.startswith('.'):
                continue
            if type_of_image == "ROI":  # Look for a file that has 'grid-roi' in the filename
                if img.find("grid-roi") == -1 and img.find("heat") == -1:

                    left_img = ImageTk.PhotoImage(Image.open(img_dir + os.sep + img))
                    count += 1

                    # Retrieve the square numbers for this image
                    self.squares_file_name = os.path.join(image_path, 'grid', image_name + '-squares.csv')
                    df_squares = read_squares_from_file(self.squares_file_name)
                    if df_squares is not None:
                        square_nrs = list(df_squares['Square Nr'])
                    else:
                        paint_logger.error("No square numbers found (?)")
                        square_nrs = []
                    valid = True
                else:
                    pass

            if type_of_image == "HEAT":  # Look for a file that has 'heat' in the filename
                if img.find("heat") != -1:
                    # Found the heatmap
                    left_img = Image.open(img_dir + os.sep + img)
                    left_img = left_img.resize((512, 512))
                    left_img = ImageTk.PhotoImage(left_img)
                    count += 1
                    square_nrs = []
                    valid = True
                    squares_file = ''
                else:
                    pass

        if not valid:  # Create an empty image with the correct background colour and insert that
            left_img = Image.new('RGB', (512, 512), "rgb(235,235,235)")
            left_img = left_img.resize((512, 512))
            left_img = ImageTk.PhotoImage(left_img)
            square_nrs = []

        # See if a Tau is defined in the grid_batch file.
        # If it is record it

        if 'Tau' in df_batch.columns:
            tau = df_batch.iloc[index]['Tau']
        else:
            tau = 0

        # Try to find the corresponding BF
        right_valid, right_img = get_corresponding_bf(bf_dir, image_name)

        record = {
            "Left Image Name": df_batch.iloc[index]['Ext Image Name'],
            "Left Image": left_img,
            "Cell Type": df_batch.iloc[index]['Cell Type'],
            "Adjuvant": df_batch.iloc[index]['Adjuvant'],
            "Probe": df_batch.iloc[index]['Probe'],
            "Probe Type": df_batch.iloc[index]['Probe Type'],
            "Nr Spots": int(df_batch.iloc[index]['Nr Spots']),
            "Square Nrs": square_nrs,
            "Squares File": self.squares_file_name,
            "Left Valid": valid,
            "Right Image Name": image_name,
            "Right Image": right_img,
            "Right Valid": right_valid,
            "Threshold": df_batch.iloc[index]['Threshold'],
            "Tau": tau
        }

        list_images.append(record)

    print("\n\n")

    if count != len(df_batch):
        f"There were {len(df_batch) - count} out of {len(df_batch)} images for which no picture was available"

    return list_images


def get_corresponding_bf(bf_dir, image_name):
    """
    Get the brightfield images for the right canvas
    :param bf_dir:
    :param image_name:
    :return:
    """

    if not os.path.exists(bf_dir):
        paint_logger.error(
            "Function 'get_corresponding_bf' failed - The directory for jpg versions of BF images does not exist. Run 'Convert BF Images' first")
        sys.exit()

    # Peel off the threshold and add -BF*.jpg
    image_name = image_name[:image_name.rfind("-")]
    image_name = image_name[:image_name.rfind("-")]

    # The BF image may be called BF, BF1 or BF2, any one is ok
    try_image = image_name + "-BF.jpg"
    try_image1 = image_name + "-BF1.jpg"
    try_image2 = image_name + "-BF2.jpg"

    if os.path.isfile(bf_dir + os.sep + try_image):
        image_name = try_image
    elif os.path.isfile(bf_dir + os.sep + try_image1):
        image_name = try_image1
    elif os.path.isfile(bf_dir + os.sep + try_image2):
        image_name = try_image2
    else:
        image_name = ""

    if len(image_name) != 0:
        img = ImageTk.PhotoImage(Image.open(bf_dir + os.sep + image_name))
        valid = True
    else:
        no_img = Image.new('RGB', (512, 512), "rgb(235,235,235)")
        img = ImageTk.PhotoImage(no_img)
        valid = False

    return valid, img


# ----------------------------------------------------------------------------------------
# Dialog code starts here
# ----------------------------------------------------------------------------------------

class ImageViewer:

    def __init__(self, root, directory, conf_file, mode):
        self.initialize_variables(root, directory, conf_file, mode)
        self.setup_ui()
        self.load_images_and_config()
        # self.setup_sliders_and_neighbours()
        self.setup_exclude_button()

        # Bind keys for navigation
        root.bind('<Right>', lambda event: self.go_forward_backward('Forward'))
        root.bind('<Left>', lambda event: self.go_forward_backward('Backward'))

    def initialize_variables(self, root, directory, conf_file, mode):

        self.root = root
        self.paint_directory = directory
        self.conf_file = conf_file
        self.mode = mode
        self.img_no = 0
        self.mode_var = None

        # UI state variables
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.squares_file_name = None
        self.show_squares_numbers = True
        self.show_squares = True
        self.user_change = False
        self.neighbour_mode = ""

        root.title('Image Viewer')

    def setup_ui(self):

        self.content = ttk.Frame(self.root, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.setup_frames()
        self.setup_frame_images()
        self.setup_frame_buttons()
        self.setup_frame_canvas()
        self.setup_labels_and_combobox()

        self.content.grid(column=0, row=0)

    def setup_frames(self):
        self.frame_images = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_buttons = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_controls = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_filter = ttk.Frame(self.content, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))

        self.frame_images.grid(column=0, row=0, padx=5, pady=5, sticky=tk.N)
        self.frame_buttons.grid(column=0, row=1, padx=5, pady=5, sticky=tk.N)
        self.frame_controls.grid(column=1, row=0, padx=5, pady=5, sticky=N)
        self.frame_filter.grid(column=2, row=0, padx=5, pady=5, sticky=N)

    def setup_frame_images(self):
        self.frame_picture_left = ttk.Frame(self.frame_images, borderwidth=2, relief='groove', width=516, height=670)
        self.frame_picture_right = ttk.Frame(self.frame_images, borderwidth=2, relief='groove', width=514, height=670)

        self.frame_picture_left.grid(column=0, row=0, padx=5, pady=5, sticky=N)
        self.frame_picture_right.grid(column=1, row=0, padx=5, pady=5, sticky=N)

    def setup_frame_buttons(self):
        self.bn_forward = ttk.Button(self.frame_buttons, text='Forward', command=lambda: self.go_forward_backward('Forward'))
        self.bn_exclude = ttk.Button(self.frame_buttons, text='Reject', command=lambda: self.exinclude())
        self.bn_backward = ttk.Button(self.frame_buttons, text='Backward', command=lambda: self.go_forward_backward('Backward'))
        self.bn_exit = ttk.Button(self.frame_buttons, text='Exit', command=lambda: self.exit_viewer())

        # Initially disable the back button
        self.bn_backward.configure(state=tk.DISABLED)

        # Layout the buttons
        self.bn_backward.grid(column=0, row=0, padx=5, pady=5)
        self.bn_exclude.grid(column=1, row=0, padx=5, pady=5)
        self.bn_forward.grid(column=2, row=0, padx=5, pady=5)
        self.bn_exit.grid(column=4, row=0, padx=30, pady=5)

    def setup_frame_controls(self):
        self.frame_mode = ttk.Frame(self.frame_controls, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_neighbours = ttk.Frame(self.frame_controls, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_cells = ttk.Frame(self.frame_controls, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_commands = ttk.Frame(self.frame_controls, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))

        self.frame_mode.grid(column=0, row=0, padx=5, pady=5)
        self.frame_neighbours.grid(column=0, row=1, padx=5, pady=5, sticky=tk.N)
        self.frame_cells.grid(column=0, row=2, padx=5, pady=5)
        self.frame_commands.grid(column=0, row=3, padx=5, pady=5)

    def setup_frame_cell(self):
        WIDTH_RB = 12
        self.cell_var = StringVar(value=1)
        self.rb_cell0 = Radiobutton(self.frame_cells, text="Not on cell", width=WIDTH_RB, variable=self.cell_var, value=0)
        self.rb_cell1 = Radiobutton(self.frame_cells, text="On cell 1", width=WIDTH_RB, bg="red", fg="white", variable=self.cell_var, value=1)
        self.rb_cell2 = Radiobutton(self.frame_cells, text="On cell 2", width=WIDTH_RB, bg="yellow", fg="black", variable=self.cell_var, value=2)
        self.rb_cell3 = Radiobutton(self.frame_cells, text="On cell 3", width=WIDTH_RB, bg="green", fg="white", variable=self.cell_var, value=3)
        self.rb_cell4 = Radiobutton(self.frame_cells, text="On cell 4", width=WIDTH_RB, bg="magenta", fg="black",  variable=self.cell_var, value=4)
        self.rb_cell5 = Radiobutton(self.frame_cells, text="On cell 5", width=WIDTH_RB, bg="cyan", fg="black", variable=self.cell_var, value=5)
        self.rb_cell6 = Radiobutton(self.frame_cells, text="On cell 6", width=WIDTH_RB, bg="black", fg="white", variable=self.cell_var, value=7)

        # Bind the right mouse click
        self.rb_cell1.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 1))
        self.rb_cell2.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 2))
        self.rb_cell3.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 3))
        self.rb_cell4.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 4))
        self.rb_cell5.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 5))
        self.rb_cell6.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 6))
        self.rb_cell0.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 0))

    def setup_frame_neighbours(self):
        self.neighbour_var = StringVar(value="")
        self.rb_neighbour_free = Radiobutton(self.frame_neighbours, text="Free", variable=self.neighbour_var, width=12, value="Free", command=self.select_neighbour_button)
        self.rb_neighbour_strict = Radiobutton(self.frame_neighbours, text="Strict", variable=self.neighbour_var, width=12, value="Strict", command=self.select_neighbour_button)
        self.rb_neighbour_relaxed = Radiobutton(self.frame_neighbours, text="Relaxed", variable=self.neighbour_var, width=12, value="Relaxed", command=self.select_neighbour_button)
        self.bn_set_neighbours_all = Button(self.frame_neighbours, text="Set for All", command=lambda: self.set_for_all_neighbour_state())

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

    def setup_frame_filter(self):
        self.frame_variability = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_density_ratio = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))

        self.variability = DoubleVar()
        self.lbl_variability_text = ttk.Label(self.frame_variability, text='Max Allowable Variability', width=20)
        self.sc_variability = tk.Scale(self.frame_variability, from_=1.5, to=10, variable=self.variability,
                                       orient='vertical', resolution=0.5, command=self.variability_changing)
        self.sc_variability.bind("<ButtonRelease-1>", self.variability_changed)

        # Set initial state for the variability slider
        self.variability.set(3.0)  # Default value, adjust as needed

        # Place the variability slider and label in the grid
        self.lbl_variability_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_variability.grid(column=0, row=1, padx=5, pady=5)

        # ---------------------------------
        # Define the slider for density ratio
        # ---------------------------------
        self.density_ratio = DoubleVar()
        self.lbl_density_ratio_text = ttk.Label(self.frame_density_ratio, text='Min Required Density Ratio', width=20)
        self.sc_density_ratio = tk.Scale(self.frame_density_ratio, from_=2, to=40, variable=self.density_ratio,
                                         orient='vertical', resolution=0.1, command=self.density_ratio_changing)
        self.sc_density_ratio.bind("<ButtonRelease-1>", self.density_ratio_changed)

        # Set initial state for the density ratio slider
        self.density_ratio.set(10)  # Default value, adjust as needed

        # Place the density ratio slider and label in the grid
        self.lbl_density_ratio_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_density_ratio.grid(column=0, row=1, padx=5, pady=5)

    def setup_frame_canvas(self):
        self.cn_left_image = tk.Canvas(self.frame_picture_left, width=512, height=512)
        self.cn_right_image = tk.Canvas(self.frame_picture_right, width=512, height=512)

        self.cn_left_image.grid(column=0, row=0, padx=2, pady=2)
        self.cn_right_image.grid(column=0, row=0, padx=2, pady=2)

    def setup_labels_and_combobox(self):
        self.list_images = []
        self.list_of_image_names = []
        self.cb_image_names = ttk.Combobox(self.frame_picture_left, values=self.list_of_image_names, state='readonly',
                                           width=30)

        # Label for the right image name
        self.lbl_image_bf_name = StringVar(self.root, "")
        lbl_image_bf_name = ttk.Label(self.frame_picture_right, textvariable=self.lbl_image_bf_name)

        # Labels for image info
        self.text_for_info1 = StringVar(self.root, "")
        lbl_info1 = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info1)

        self.text_for_info2 = StringVar(self.root, "")
        lbl_info2 = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info2)

        self.text_for_info3 = StringVar(self.root, "")
        lbl_info3 = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info3)

        # Bind combobox selection
        self.cb_image_names.bind("<<ComboboxSelected>>", self.image_selected)

        # Layout labels and combobox
        self.cb_image_names.grid(column=0, row=1, padx=5, pady=5)
        lbl_info1.grid(column=0, row=2, padx=5, pady=5)
        lbl_info2.grid(column=0, row=3, padx=5, pady=5)
        lbl_info3.grid(column=0, row=4, padx=5, pady=5)
        lbl_image_bf_name.grid(column=0, row=1, padx=0, pady=0)

    def load_images_and_config(self):
        """Load images and configurations."""
        if self.mode == 'Directory':
            self.batchfile_path = os.path.join(self.paint_directory, 'grid_batch.csv')
        else:
            self.paint_directory = os.path.split(self.conf_file)[0]
            self.batchfile_path = os.path.join(self.paint_directory, self.conf_file)

        self.df_batch = read_batch_from_file(self.batchfile_path, False)
        if self.df_batch is None:
            self.show_error_and_exit("No 'grid_batch.csv' file, Did you select an image directory?")

        self.image_name = self.df_batch.iloc[self.img_no]['Ext Image Name']
        self.list_images = get_images(self, 'ROI')
        if not self.list_images:
            self.show_error_and_exit(f"No images were found below directory {self.paint_directory}.")

        self.list_of_image_names = [image['Left Image Name'] for image in self.list_images]
        self.cb_image_names['values'] = self.list_of_image_names

        self.update_image_display()

        # def setup_sliders_and_neighbours(self):
        # -----------------------------
        # Define the slider for variability
        # -----------------------------
        # self.variability = DoubleVar()
        # lbl_variability_text = ttk.Label(self.frame_variability, text='Max Allowable Variability', width=20)
        # self.sc_variability = tk.Scale(self.frame_variability, from_=1.5, to=10, variable=self.variability,
        #                                orient='vertical', resolution=0.5, command=self.variability_changing)
        # self.sc_variability.bind("<ButtonRelease-1>", self.variability_changed)
        #
        # # Set initial state for the variability slider
        # self.variability.set(3.0)  # Default value, adjust as needed
        #
        # # Place the variability slider and label in the grid
        # lbl_variability_text.grid(column=0, row=0, padx=5, pady=5)
        # self.sc_variability.grid(column=0, row=1, padx=5, pady=5)
        #
        # # ---------------------------------
        # # Define the slider for density ratio
        # # ---------------------------------
        # self.density_ratio = DoubleVar()
        # lbl_density_ratio_text = ttk.Label(self.frame_density_ratio, text='Min Required Density Ratio', width=20)
        # self.sc_density_ratio = tk.Scale(self.frame_density_ratio, from_=2, to=40, variable=self.density_ratio,
        #                                  orient='vertical', resolution=0.1, command=self.density_ratio_changing)
        # self.sc_density_ratio.bind("<ButtonRelease-1>", self.density_ratio_changed)
        #
        # # Set initial state for the density ratio slider
        # self.density_ratio.set(10)  # Default value, adjust as needed
        #
        # # Place the density ratio slider and label in the grid
        # lbl_density_ratio_text.grid(column=0, row=0, padx=5, pady=5)
        # self.sc_density_ratio.grid(column=0, row=1, padx=5, pady=5)

        # -------------------------------
        # Define the frame for neighbours
        # -------------------------------

        # Define radio buttons for neighbour control
        # self.neighbour_var = StringVar(value="")
        # self.rb_neighbour_free = Radiobutton(self.frame_neighbours, text="Free", variable=self.neighbour_var,
        #                                      width=12, value="Free", command=self.select_neighbour_button)
        # self.rb_neighbour_strict = Radiobutton(self.frame_neighbours, text="Strict", variable=self.neighbour_var,
        #                                        width=12, value="Strict", command=self.select_neighbour_button)
        # self.rb_neighbour_relaxed = Radiobutton(self.frame_neighbours, text="Relaxed", variable=self.neighbour_var,
        #                                         width=12, value="Relaxed", command=self.select_neighbour_button)
        #
        # # Add the "Set for All" button
        # self.bn_set_neighbours_all = Button(self.frame_neighbours, text="Set for All",
        #                                     command=lambda: self.set_for_all_neighbour_state())
        #
        # # Place the radio buttons and button in the grid
        # self.rb_neighbour_free.grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        # self.rb_neighbour_relaxed.grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        # self.rb_neighbour_strict.grid(column=0, row=2, padx=5, pady=5, sticky=tk.W)
        # self.bn_set_neighbours_all.grid(column=0, row=3, padx=5, pady=5, sticky=tk.W)

    def setup_exclude_button(self):
        """Setup the exclude/include button state."""
        if 'Exclude' not in self.df_batch:
            self.bn_exclude.config(text='Exclude')
        else:
            row_index = self.df_batch.index[self.df_batch['Ext Image Name'] == self.image_name].tolist()[0]
            if self.df_batch.loc[row_index, 'Exclude']:
                self.bn_exclude.config(text='Include')
                self.text_for_info3.set('Excluded')
            else:
                self.bn_exclude.config(text='Exclude')
                self.text_for_info3.set('')

    def show_error_and_exit(self, message):
        """Display an error message and exit."""
        # Assuming paint_logger is defined elsewhere
        paint_logger.error(message)
        sys.exit()

    def update_image_display(self):
        """Update the image display based on the current image number."""
        self.cn_left_image.create_image(0, 0, anchor=tk.NW, image=self.list_images[self.img_no]['Left Image'])
        self.cn_right_image.create_image(0, 0, anchor=tk.NW, image=self.list_images[self.img_no]['Right Image'])

        # Update labels for image information
        self.lbl_image_bf_name.set(self.list_images[self.img_no]['Right Image Name'])
        cell_info = f"({self.list_images[self.img_no]['Cell Type']}) - ({self.list_images[self.img_no]['Adjuvant']}) - ({self.list_images[self.img_no]['Probe Type']}) - ({self.list_images[self.img_no]['Probe']})"
        self.text_for_info1.set(cell_info)
        info2 = f"Spots: {self.list_images[self.img_no]['Nr Spots']:,} - Threshold: {self.list_images[self.img_no]['Threshold']}"
        self.text_for_info2.set(info2)

    def image_selected(self, event):
        """Handle image selection from combobox."""
        # Logic for when an image is selected
        pass

    def go_forward_backward(self, direction):
        """Navigate through images."""
        if direction == 'Forward':
            self.img_no += 1
        elif direction == 'Backward':
            self.img_no -= 1

        # Ensure we stay within bounds
        self.img_no = max(0, min(self.img_no, len(self.list_images) - 1))

        self.update_image_display()

    def exinclude(self):
        pass

    def key_pressed(self, event):
        pass

    def output_pictures(self):
        pass

    def exit_viewer(self):
        pass

    def image_selected(self, _):
        pass

    def set_variability_slider_state(self):
        pass

    def set_density_ratio_slider_state(self):
        pass

    def set_neighbour_state(self):
      pass

    def save_variability_slider_state(self):
        pass

    def save_density_ratio_slider_state(self):
        pass

    def save_neighbour_state(self):
        pass

    def histogram(self):
        pass

    def show_excel(self):
        pass

    def reset_image(self):
        pass

    def run_output(self):
        pass

    def set_for_all_slider(self):
        pass

    def variability_changing(self, event):
        pass

    def density_ratio_changing(self, event):
        pass

    def variability_changed(self, _):
        pass

    def density_ratio_changed(self, _):
        pass

    def provide_report_on_all_squares(self, _):
        pass

    def provide_report_on_cell(self, _, cell_nr):
        pass

    def select_squares_for_display(self):

        self.df_squares['Variability Visible'] = False
        self.df_squares.loc[
            self.df_squares['Variability'] <= round(self.sc_variability.get(), 1), 'Variability Visible'] = True
        self.df_squares.loc[
            self.df_squares['Variability'] > round(self.sc_variability.get(), 1), 'Variability Visible'] = False

        self.df_squares['Density Ratio Visible'] = False
        self.df_squares.loc[
            self.df_squares['Density Ratio'] >= round(self.density_ratio.get(), 1), 'Density Ratio Visible'] = True
        self.df_squares.loc[
            self.df_squares['Density Ratio'] < round(self.density_ratio.get(), 1), 'Density Ratio Visible'] = False

        self.df_squares['Visible'] = self.df_squares['Density Ratio Visible'] & self.df_squares['Variability Visible']

        # Select which isolation mode to be applied
        neighbour_state = self.neighbour_var.get()
        if neighbour_state == "Relaxed":
            eliminate_isolated_squares_relaxed(self.df_squares, self.nr_of_squares_in_row)
        elif neighbour_state == "Strict":
            eliminate_isolated_squares_strict(self.df_squares, self.nr_of_squares_in_row)
        elif neighbour_state == "Free":
            self.df_squares['Neighbour Visible'] = True

        self.df_squares['Visible'] = (self.df_squares['Valid Tau'] &
                                      self.df_squares['Density Ratio Visible'] &
                                      self.df_squares['Variability Visible'] &
                                      self.df_squares['Neighbour Visible'])

    def display_selected_squares(self):

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
                for index, row in self.df_squares.iterrows():
                    if row['Visible']:
                        self.draw_single_square(row)
        return self.df_squares

    def draw_single_square(self, squares_row):

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
            self.cn_left_image.create_rectangle(col_nr * width,
                                                row_nr * width,
                                                col_nr * width + width,
                                                row_nr * height + height,
                                                outline="white",
                                                # outline="red",
                                                width=0.5,
                                                tags=square_tag)
            if self.show_squares_numbers:
                text_item = self.cn_left_image.create_text(col_nr * width + 0.5 * width,
                                                           row_nr * width + 0.5 * width,
                                                           text=str(label_nr),
                                                           font=('Arial', -10),
                                                           fill="white",
                                                           tags=text_tag)
        else:  # A square is allocated to a cell
            self.cn_left_image.create_rectangle(col_nr * width,
                                                row_nr * width,
                                                col_nr * width + width,
                                                row_nr * height + height,
                                                outline=colour_table[self.df_squares.loc[square_nr]['Cell Id']][0],
                                                width=3,
                                                tags=square_tag)
            if self.show_squares_numbers:
                text_item = self.cn_left_image.create_text(col_nr * width + 0.5 * width,
                                                           row_nr * width + 0.5 * width,
                                                           text=str(self.df_squares.loc[square_nr]['Label Nr']),
                                                           font=('Arial', -10),
                                                           fill=colour_table[self.df_squares.loc[square_nr]['Cell Id']][1],
                                                           tags=text_tag)

        # The new square is made clickable -  for now use the text item
        if self.show_squares_numbers:
            self.cn_left_image.tag_bind(text_item, '<Button-1>', lambda e: self.square_assigned_to_cell(square_nr))

    def square_assigned_to_cell(self, square_nr):

        if self.mode_var.get() == 'HEAT':
            return

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
       pass

    def start_rectangle(self, event):
        pass

    def increase_rectangle_size(self, event):
        pass

    def define_rectangle(self, event):
        pass

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

    def select_mode_button(self):
        if self.mode_var.get() == "HEAT":
            self.configure_widgets_state(DISABLED)
        elif self.mode_var.get() == "ROI":
            self.configure_widgets_state(NORMAL)
        else:
            paint_logger.error('Big trouble!')

        self.list_images = get_images(self, self.mode_var.get())
        self.img_no = self.img_no - 1
        self.go_forward_backward('Forward')

    def select_neighbour_button(self):

        self.user_change = True

        self.cn_left_image.delete("all")
        self.cn_left_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])

        self.neighbour_mode = self.neighbour_var.get()

        self.df_squares['Neighbour Setting'] = self.neighbour_mode
        self.select_squares_for_display()
        self.display_selected_squares()

    def go_forward_backward(self, direction):
        """
        The function is called when we switch image
        :param direction:
        :return:
        """

        if self.user_change:
            self.save_image_state()
            self.user_change = False

        # Determine what the next image is, depending on the direction
        # Be sure not move beyond the boundaries (could happen when the left and right keys are used)
        if direction == 'Forward':
            if self.img_no != len(self.list_images) - 1:
                self.img_no += 1
        elif direction == 'Backward':
            if self.img_no != 0:
                self.img_no -= 1

        # Set the name of the image
        self.image_name = self.list_images[self.img_no]['Left Image Name']

        # Place new image in the canvas and draw the squares
        self.cn_left_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])

        # If the mode is 'ROI' draw the squares:
        if self.mode_var.get() == 'ROI':
            self.squares_file_name = self.list_images[self.img_no]['Squares File']
            self.df_squares = read_squares_from_file(self.squares_file_name)
            self.set_variability_slider_state()
            self.set_density_ratio_slider_state()
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
        row_index = self.df_batch.index[self.df_batch['Ext Image Name'] == self.image_name].tolist()[0]
        if self.df_batch.loc[row_index, 'Exclude']:
            self.bn_exclude.config(text='Include')
            self.text_for_info3.set("Excluded")
        else:
            self.bn_exclude.config(text='Exclude')
            self.text_for_info3.set("")

        # Reset user change
        self.user_change = False

    def read_squares(self, image_name):
        self.squares_file_name = os.path.join(self.paint_directory, image_name, 'grid', image_name + '-squares.csv')
        self.df_squares = read_squares_from_file(self.list_images[self.img_no]['Squares File'])
        if self.df_squares is None:
            paint_logger.error(f"Function 'read_squares' failed - Squares file {self.squares_file_name} was not found.")
            sys.exit()
        return self.df_squares

    def read_batch(self):
        batch_file_path = os.path.join(self.paint_directory, self.image_name, 'grid_batch.csv')
        self.df_batch = read_batch_from_file(batch_file_path)
        if self.df_batch is None:
            paint_logger.error(f"Function 'read_batch' failed - Squares file {batch_file_path} was not found.")
            sys.exit()
        return self.df_batch

    def write_squares(self):
        # It is necessary to the squares file, because the user may have made changes
        if self.mode == 'Directory':
            squares_file_name = os.path.join(self.paint_directory, self.image_name, 'grid', self.image_name + '-squares.csv')
        else:
            squares_file_name = os.path.join(self.paint_directory, str(self.df_batch.iloc[self.img_no]['Experiment Date']),  self.image_name, 'grid',
                                             self.image_name + '-squares.csv')
        save_squares_to_file(self.df_squares, squares_file_name)

    def write_grid_batch(self):
        save_batch_to_file(self.df_batch, self.batchfile_path)

    def save_image_state(self):

        # Get the slider and neighbour state and save it into df_batch
        self.save_density_ratio_slider_state()
        self.save_variability_slider_state()
        self.save_neighbour_state()

        # Write the Nr Visible Squares visibility information into the batch file
        self.df_squares['Visible'] = (self.df_squares['Density Ratio Visible'] &
                                      self.df_squares['Variability Visible'] &
                                      self.df_squares['Variability Visible'])
        self.df_batch.loc[self.image_name, 'Nr Visible Squares'] = len(self.df_squares[self.df_squares['Visible']])

        # Save the batch and squares
        self.select_squares_for_display()
        self.write_squares()
        self.write_grid_batch()


proceed = False
root_directory = ''
conf_file = ''
mode = ''


class SelectViewerDialog:

    def __init__(self, _root: tk.Tk)  ->  None:

        _root.title('Image Viewer')

        self.root_directory, self.paint_directory, self.images_directory = get_default_directories()
        self.conf_file = ''

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
        btn_root_dir = ttk.Button(frame_directory, text='Paint Directory', width=15, command=self.change_root_dir)
        btn_conf_file = ttk.Button(frame_directory, text='Configuration file', width=15, command=self.change_conf_file)

        self.lbl_root_dir = ttk.Label(frame_directory, text=self.root_directory, width=80)
        self.lbl_conf_file = ttk.Label(frame_directory, text=self.conf_file, width=80)

        self.mode_var = StringVar(value="Directory")
        self.rb_mode_directory = ttk.Radiobutton(frame_directory, text="", variable=self.mode_var, width=10,
                                                 value="Directory")
        self.rb_mode_conf_file = ttk.Radiobutton(frame_directory, text="", variable=self.mode_var, width=10,
                                                 value="Conf File")

        btn_root_dir.grid(column=0, row=0, padx=10, pady=5)
        btn_conf_file.grid(column=0, row=1, padx=10, pady=5)

        self.lbl_root_dir.grid(column=1, row=0, padx=20, pady=5)
        self.lbl_conf_file.grid(column=1, row=1, padx=20, pady=5)

        self.rb_mode_directory.grid(column=2, row=0, padx=10, pady=5)
        self.rb_mode_conf_file.grid(column=2, row=1, padx=10, pady=5)

    def change_root_dir(self) -> None:

        global root_directory
        global conf_file
        global mode

        self.root_directory = filedialog.askdirectory(initialdir=self.root_directory)
        save_default_directories(self.root_directory, self.paint_directory, self.images_directory)
        if len(self.root_directory) != 0:
            self.mode_var.set('Directory')
            self.rb_mode_directory.focus()
            self.lbl_root_dir.config(text=self.root_directory)

    def change_conf_file(self) -> None:
        global root_directory
        global conf_file
        global mode

        self.conf_file = filedialog.askopenfilename(initialdir=self.paint_directory,
                                                    title='Select a configuration file')

        if len(self.conf_file) != 0:
            self.mode_var.set('Conf File')
            self.rb_mode_conf_file.focus()
            self.lbl_conf_file.config(text=self.conf_file)
            # save_default_directories(self.root_directory, self.paint_directory, self.images_directory)

    def process(self) -> None:
        global proceed
        global root_directory
        global conf_file
        global mode

        error = False

        mode = self.mode_var.get()
        if mode == "Directory":
            root_directory = self.root_directory
            if not os.path.isdir(root_directory):
                paint_logger.error('Whoops')
                error = True

        else:
            conf_file = self.conf_file
            if not os.path.isfile(conf_file):
                paint_logger.error('Whoops')
                error = True

        if not error:
            proceed = True
            root.destroy()

    @staticmethod
    def exit_dialog() -> None:

        global proceed

        proceed = False
        root.destroy()


root = Tk()
root.eval('tk::PlaceWindow . center')
SelectViewerDialog(root)
root.mainloop()

if proceed:
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    paint_logger.debug(f'Mode: {mode}')
    if mode == 'Directory':
        paint_logger.info(f'Root directory: {root_directory}')
    else:
        paint_logger.debug(f'Configuration file: {conf_file}')

    image_viewer = ImageViewer(root, root_directory, conf_file, mode)
    root.mainloop()
