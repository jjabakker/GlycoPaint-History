import os
import re
import platform
import statistics

import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
import subprocess

from tkinter import *

from tkinter import ttk

from PIL import Image, ImageTk

from src.Automation.Support.Support_Functions import eliminate_isolated_squares_relaxed
from src.Automation.Support.Support_Functions import eliminate_isolated_squares_strict
from src.Automation.Support.Support_Functions import test_if_square_is_in_rectangle
from src.Automation.Support.Support_Functions import create_output_directories_for_graphpad
from src.Automation.Support.Support_Functions import get_default_directories
from src.Automation.Support.Support_Functions import save_default_directories
from src.Automation.Support.Support_Functions import read_batch_from_file
from src.Automation.Support.Support_Functions import read_squares_from_file
# from src.Automation.Support.Support_Functions import save_squares_to_file
from src.Automation.Support.Support_Functions import save_batch_to_file

from src.Automation.Support.Analyse_All_Images import analyse_all_images
from src.Automation.Support.Analyse_All_Images import create_summary_graphpad


def save_as_png(canvas, file_name, image_name):
    # canvas.create_text(60, 40, fill='white', text=image_name, font='Helvetica 15 bold')
    canvas.create_text(60, 40)
    canvas.postscript(file=file_name + '.eps')
    img = Image.open(file_name + '.eps')
    img.save(file_name + '.png', 'png')


def save_square_info_to_batch(self):
    for index, row in self.df_batch.iterrows():
        # image_name = row['Ext Image Name']
        # squares_file_path = os.path.join(self.paint_directory, image_name, 'grid', image_name + '-squares.csv')
        self.squares_file_name = self.list_images[self.img_no]['Squares File']
        df_squares             = read_squares_from_file(self.squares_file_name)
        if df_squares is None:
            print(" Function 'save_square_info_to_batch' failed: - Square file {squares_file_path} does not exist")
            exit()
        if len(df_squares) > 0:
            nr_visible_squares    = len(df_squares[df_squares['Visible']])
            nr_total_squares      = len(df_squares)
            squares_ratio         = round(nr_visible_squares / nr_total_squares, 2)
        else:
            nr_visible_squares    = 0
            nr_total_squares      = 0
            squares_ratio         = 0.0

        self.df_batch.loc[index, 'Nr Visible Squares']    = nr_visible_squares
        self.df_batch.loc[index, 'Nr Total Squares']      = nr_total_squares
        self.df_batch.loc[index, 'Squares Ratio']         = squares_ratio


def set_for_all_neighbour_state(self):
    self.df_batch['Neighbour Setting'] = self.neighbour_var.get()


def get_images(self, type_of_image):
    """
    Get the images for the left canvas. Either an image with squares or a heatmap.
    The data is all in the Combined Filtered Results spreadsheet (which is a compilation of the individual
    squares files, but for some reason the individual files are used here (maybe a bit safer in terms of
    corruption risk),

    :param paint_directory:
    :param df_batch:
    :param mode:
    :param type_of_image:
    :return:
    """

    paint_directory = self.paint_directory
    df_batch        = self.df_batch
    mode            = self.mode

    # Create an empty lst that will hold the images
    list_images = []

    # Cycle through the batch file
    count = 0
    for index in range(len(df_batch)):

        if df_batch.iloc[index]['Process'] == 'No' or df_batch.iloc[index]['Process'] == 'N':
            continue

        image_name = df_batch.iloc[index]['Ext Image Name']

        if mode == 'Directory':
            image_path = os.path.join(paint_directory, image_name)
        else:
            image_path = os.path.join(paint_directory, str(df_batch.iloc[index]['Experiment Date']), image_name)

        # if os.path.isfile(image_path):
        #     continue

        # If there is no img directory below the image directory, skip it
        img_dir = os.path.join(image_path, "img")
        if not os.path.isdir(img_dir):
            continue

        if mode == 'Directory':
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

        valid      = False
        square_nrs = []

        for img in all_images_in_img_dir:
            if type_of_image == "ROI":  # Look for a file that has 'grid-roi' in the filename
                if img.find("grid-roi") == -1 and img.find("heat") == -1:

                    # Retrieve image
                    left_img = ImageTk.PhotoImage(Image.open(img_dir + os.sep + img))
                    count += 1

                    # Retrieve the square numbers for this image
                    self.squares_file_name = os.path.join(image_path, 'grid', image_name + '-squares.csv')
                    df_squares             = read_squares_from_file(self.squares_file_name)
                    if df_squares is not None:
                        square_nrs = list(df_squares['Square Nr'])
                    else:
                        print("No square numbers found (?)")
                        square_nrs = []
                    valid = True
                else:
                    pass

            if type_of_image == "HEAT":  # Look for a file that has 'heat' in the filename
                if img.find("heat") != -1:
                    # Found the heatmap
                    left_img     = Image.open(img_dir + os.sep + img)
                    left_img     = left_img.resize((512, 512))
                    left_img     = ImageTk.PhotoImage(left_img)
                    count        += 1
                    square_nrs   = []
                    valid        = True
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
            "Left Image Name"  : df_batch.iloc[index]['Ext Image Name'],
            "Left Image"       : left_img,
            "Cell Type"        : df_batch.iloc[index]['Cell Type'],
            "Adjuvant"         : df_batch.iloc[index]['Adjuvant'],
            "Probe"            : df_batch.iloc[index]['Probe'],
            "Probe Type"       : df_batch.iloc[index]['Probe Type'],
            "Nr Spots"         : int(df_batch.iloc[index]['Nr Spots']),
            "Square Nrs"       : square_nrs,
            "Squares File"     : self.squares_file_name,
            "Left Valid"       : valid,
            "Right Image Name" : image_name,
            "Right Image"      : right_img,
            "Right Valid"      : right_valid,
            "Threshold"        : df_batch.iloc[index]['Threshold'],
            "Tau"              : tau
        }

        list_images.append(record)

    print("\n\n")

    if count != len(df_batch):
        print(f"There were {len(df_batch) - count} out of {len(df_batch)} images for which no picture was available")

    return list_images


def get_corresponding_bf(bf_dir, image_name):
    """
    Get the brightfield images for the right canvas
    :param bf_dir:
    :param image_name:
    :return:
    """

    if not os.path.exists(bf_dir):
        print(
            "Function 'get_corresponding_bf' failed - The directory for jpg versions of BF images does not exist. Run 'Convert BF Images' first")
        exit()

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

        # Remember the root, because you need it later to close
        self.image_viewer_root = root
        root.title('Image Viewer')

        self.neighbour_mode    = ""   # We can't know for sure what mode is displayed, so leave it ambiguous
        self.img_no            = 0
        self.show_squares      = True
        self.user_change       = False

        self.mode              = mode
        self.conf_file         = conf_file
        self.paint_directory   = directory

        if self.mode == 'Directory':
            self.paint_directory = directory
            self.batchfile_path  = os.path.join(self.paint_directory, 'grid_batch.csv')
        else:
            self.paint_directory = os.path.split(self.conf_file)[0]
            self.batchfile_path  = os.path.join(self.paint_directory, conf_file)

        # Read the batch file. If the file is not there just return (a message will have been printed)
        self.df_batch = read_batch_from_file(self.batchfile_path, FALSE)
        if self.df_batch is None:
            print("No 'grid_batch.csv' file, Did you run 'Process All Images.py'?")
            return

        # Retrieve some info from the batch file
        self.image_name = self.df_batch.iloc[self.img_no]['Ext Image Name']
        self.nr_of_squares_in_row = int(self.df_batch.iloc[0]['Nr Of Squares per Row'])

        # ---------------------------------
        # Fill the list with images to view
        # ---------------------------------

        self.list_images = get_images(self, 'ROI')
        if len(self.list_images) == 0:
            print(f"Function 'ImageViewer Init' failed - No images were found below directory {self.paint_directory}.")
            exit()

        self.list_of_image_names = []
        for image in self.list_images:
            self.list_of_image_names.append(image['Left Image Name'])

        # --------------------------
        # Define the dialog elements
        # --------------------------

        # Define the frames
        content                  = ttk.Frame(root,           borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        frame_images             = ttk.Frame(content,        borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_picture_left  = ttk.Frame(frame_images,   borderwidth=2, relief='groove', width=516, height=670, padding=(0, 0, 0, 0))
        self.frame_picture_right = ttk.Frame(frame_images,   borderwidth=2, relief='groove', width=514, height=670, padding=(0, 0, 0, 0))

        frame_buttons            = ttk.Frame(content,        borderwidth=2, relief='groove', padding=(5, 5, 5, 5))

        frame_controls           = ttk.Frame(content,        borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        frame_mode               = ttk.Frame(frame_controls, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        frame_neighbours         = ttk.Frame(frame_controls, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        frame_cells              = ttk.Frame(frame_controls, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        frame_commands           = ttk.Frame(frame_controls, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))

        frame_filter             = ttk.Frame(content,        borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        frame_variability        = ttk.Frame(frame_filter,   borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        frame_density_ratio      = ttk.Frame(frame_filter,   borderwidth=1, relief='groove', padding=(5, 5, 5, 5))

        # Define the canvas for the left image and fill with picture
        self.cn_left_image = tk.Canvas(self.frame_picture_left, width=512, height=512)
        self.cn_left_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])
        root.bind('<Key>', self.key_pressed)

        # Define the canvas for the right image (bf) and fill with picture
        self.cn_right_image = tk.Canvas(self.frame_picture_right, width=512, height=512)
        self.cn_right_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Right Image'])

        # Define combo box for the left image name
        self.cb_image_names = ttk.Combobox(self.frame_picture_left, values=self.list_of_image_names, state='readonly',
                                           width=30)
        self.cb_image_names.bind("<<ComboboxSelected>>", self.image_selected)
        self.cb_image_names.bind('<Button-2>', lambda e: self.provide_report_on_all_squares(e))
        self.cb_image_names.set(self.list_images[self.img_no]['Left Image Name'])

        # Define the label for the right image name (bf)
        self.lbl_image_bf_name = StringVar(root, "1:  " + self.list_images[self.img_no]['Right Image Name'])
        lbl_image_bf_name = ttk.Label(self.frame_picture_right, textvariable=self.lbl_image_bf_name)

        # Define the label for info1
        cell_info = f"({self.list_images[self.img_no]['Cell Type']}) - ({self.list_images[self.img_no]['Adjuvant']}) - ({self.list_images[self.img_no]['Probe Type']}) - ({self.list_images[self.img_no]['Probe']})"

        self.text_for_info1 = StringVar(root, cell_info)
        lbl_info1           = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info1)

        # Define the label  for info2
        info1 = f"Spots: {self.list_images[self.img_no]['Nr Spots']:,} - Threshold: {self.list_images[self.img_no]['Threshold']}"
        if self.list_images[self.img_no]['Tau'] != 0:
            info1 = f"{info1} - Tau: {int(self.list_images[self.img_no]['Tau'])}"
        self.text_for_info2 = StringVar(root, info1)
        lbl_info2           = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info2)

        # Define the label  for info3
        style = ttk.Style()
        style.configure("RW.TLabel", foreground="red", background="white")
        self.text_for_info3 = StringVar()
        lbl_info3           = ttk.Label(self.frame_picture_left, textvariable=self.text_for_info3, style='RW.TLabel')

        # Define the Buttons for back, forward and exit
        self.bn_forward     = ttk.Button(frame_buttons, text='Forward',
                                         command=lambda: self.go_forward_backward('Forward'))
        self.bn_exclude     = ttk.Button(frame_buttons, text='Reject',
                                         command=lambda: self.exinclude())
        self.bn_backward    = ttk.Button(frame_buttons, text='Backward',
                                         command=lambda: self.go_forward_backward('Backward'))
        bn_exit             = ttk.Button(frame_buttons, text='Exit',
                                         command=lambda: self.exit_viewer())

        # We start at 0, so disable the back button
        self.bn_backward.configure(state=DISABLED)

        # Define the Radio buttons for the type of plot
        width_rb      = 12
        self.mode_var = StringVar(value="ROI")
        rb_mode_roi   = Radiobutton(frame_mode, text="ROI", variable=self.mode_var, width=width_rb, value="ROI",
                                    command=self.select_mode_button)
        rb_mode_heat  = Radiobutton(frame_mode, text="Heat map", variable=self.mode_var, width=width_rb, value="HEAT",
                                    command=self.select_mode_button)

        # Define the radio buttons for the neighbour control. Default state is unspecified.
        self.neighbour_var         = StringVar(value="")
        self.rb_neighbour_free     = Radiobutton(frame_neighbours, text="Free", variable=self.neighbour_var,
                                                 width=width_rb, value="Free", command=self.select_neighbour_button)
        self.rb_neighbour_strict   = Radiobutton(frame_neighbours, text="Strict", variable=self.neighbour_var,
                                                 width=width_rb, value="Strict", command=self.select_neighbour_button)
        self.rb_neighbour_relaxed  = Radiobutton(frame_neighbours, text="Relaxed", variable=self.neighbour_var,
                                                 width=width_rb, value="Relaxed", command=self.select_neighbour_button)
        self.bn_set_neighbours_all = Button(frame_neighbours, text="Set for All",
                                            command=lambda: set_for_all_neighbour_state(self))

        # Define the cell selection color panel
        self.cell_var = StringVar(value=1)
        self.rb_cell0 = Radiobutton(frame_cells, text="Not on cell", width=width_rb,
                                    variable=self.cell_var, value=0)
        self.rb_cell1 = Radiobutton(frame_cells, text="On cell 1", width=width_rb, bg="blue", fg="white",
                                    variable=self.cell_var, value=1)
        self.rb_cell2 = Radiobutton(frame_cells, text="On cell 2", width=width_rb, bg="yellow", fg="black",
                                    variable=self.cell_var, value=2)
        self.rb_cell3 = Radiobutton(frame_cells, text="On cell 3", width=width_rb, bg="green", fg="white",
                                    variable=self.cell_var, value=3)
        self.rb_cell4 = Radiobutton(frame_cells, text="On cell 4", width=width_rb, bg="magenta", fg="black",
                                    variable=self.cell_var, value=4)
        self.rb_cell5 = Radiobutton(frame_cells, text="On cell 5", width=width_rb, bg="cyan", fg="black",
                                    variable=self.cell_var, value=5)
        self.rb_cell6 = Radiobutton(frame_cells, text="On cell 6", width=width_rb, bg="black", fg="white",
                                    variable=self.cell_var, value=7)

        # Bind the right mouse click
        self.rb_cell1.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 1))
        self.rb_cell2.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 2))
        self.rb_cell3.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 3))
        self.rb_cell4.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 4))
        self.rb_cell5.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 5))
        self.rb_cell6.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 6))
        self.rb_cell0.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 0))

        # Define the slider for variability
        self.variability     = DoubleVar()
        lbl_variability_text = ttk.Label(frame_variability, text='Max Allowable Variability', width=20)
        self.sc_variability  = tk.Scale(frame_variability, from_=1.5, to=10, variable=self.variability,
                                        orient='vertical', command=self.variability_changing, resolution=0.5)
        self.sc_variability.bind("<ButtonRelease-1>", self.variability_changed)
        self.set_variability_slider_state()

        # Define the slider for density ratio
        self.density_ratio     = DoubleVar()
        lbl_density_ratio_text = ttk.Label(frame_density_ratio, text='Min Required Density Ratio', width=20)
        self.sc_density_ratio  = tk.Scale(frame_density_ratio, from_=2, to=40, variable=self.density_ratio,
                                          orient='vertical', command=self.density_ratio_changing, resolution=1)
        self.sc_density_ratio.bind("<ButtonRelease-1>", self.density_ratio_changed)
        self.set_density_ratio_slider_state()

        bn_set_for_all_slider = ttk.Button(frame_filter, text='Set for All', command=self.set_for_all_slider)

        # Define the commands
        button_width = 12
        bn_output      = ttk.Button(frame_commands, text='Output All Images', width=button_width, command=lambda: self.run_output())
        bn_reset_image = ttk.Button(frame_commands, text='Reset Image',       width=button_width, command=lambda: self.reset_image())
        bn_excel       = ttk.Button(frame_commands, text='Excel',             width=button_width, command=lambda: self.show_excel())
        bn_histogram   = ttk.Button(frame_commands, text='Histogram',         width=button_width, command=lambda: self.histogram())

        # --------------
        # Do the lay-out
        # --------------

        # The frames
        content.grid(column=0, row=0)

        # The frame with the images
        frame_images.grid       (column=0, row=0, padx=5, pady=5, sticky=N)
        frame_buttons.grid      (column=0, row=1, padx=5, pady=5, sticky=N)
        frame_controls.grid     (column=1, row=0, padx=5, pady=5, sticky=N)

        # The frame with the sliders
        frame_filter.grid       (column=2, row=0, padx=5, pady=5, sticky=N)
        frame_variability.grid  (column=2, row=0, padx=5, pady=5, sticky=N)
        frame_density_ratio.grid(column=2, row=0, padx=5, pady=5, sticky=N)

        # The two image frames fit in frame_images
        self.frame_picture_left.grid (column=0, row=0, padx=5, pady=5)
        self.frame_picture_right.grid(column=1, row=0, padx=5, pady=5)

        self.frame_picture_right.grid_propagate(False)
        self.frame_picture_left.grid_propagate(False)

        # Fill the left image frame
        self.cn_left_image.grid  (column=0, row=0, padx=2, pady=2)
        self.cb_image_names.grid (column=0, row=1, padx=5, pady=5)
        lbl_info1.grid           (column=0, row=2, padx=5, pady=5)
        lbl_info2.grid           (column=0, row=3, padx=5, pady=5)
        lbl_info3.grid           (column=0, row=4, padx=5, pady=5)

        # Fill the right image frame
        self.cn_right_image.grid(column=0, row=0, padx=2, pady=2)
        lbl_image_bf_name.grid  (column=0, row=1, padx=0, pady=0)

        # Fill the button window
        self.bn_backward.grid(column=0, row=0, padx=5,  pady=5)
        self.bn_exclude.grid (column=1, row=0, padx=5,  pady=5)
        self.bn_forward.grid (column=2, row=0, padx=5,  pady=5)
        bn_exit.grid         (column=4, row=0, padx=30, pady=5)

        # Fill the frame_controls window
        frame_mode.grid      (column=0, row=0, padx=5, pady=5)
        frame_neighbours.grid(column=0, row=1, padx=5, pady=5)
        frame_cells.grid     (column=0, row=2, padx=5, pady=5)
        frame_commands.grid  (column=0, row=3, padx=5, pady=5)

        # Fill the control window
        rb_mode_roi.grid (column=0, row=0, padx=5, pady=5, sticky=W)
        rb_mode_heat.grid(column=0, row=1, padx=5, pady=5, sticky=W)

        # Fill the neighbours window
        self.rb_neighbour_free.grid      (column=0, row=0, padx=5, pady=5, sticky=W)
        self.rb_neighbour_relaxed.grid   (column=0, row=1, padx=5, pady=5, sticky=W)
        self.rb_neighbour_strict.grid    (column=0, row=2, padx=5, pady=5, sticky=W)
        self.bn_set_neighbours_all.grid  (column=0, row=3, padx=5, pady=5, sticky=W)

        # Fill the cells window
        self.rb_cell0.grid(column=0, row=5,  padx=5, pady=5)
        self.rb_cell1.grid(column=0, row=6,  padx=5, pady=5)
        self.rb_cell2.grid(column=0, row=7,  padx=5, pady=5)
        self.rb_cell3.grid(column=0, row=8,  padx=5, pady=5)
        self.rb_cell4.grid(column=0, row=9,  padx=5, pady=5)
        self.rb_cell5.grid(column=0, row=10, padx=5, pady=5)

        # The two filter frames fit in frame_images
        frame_variability.grid    (column=0, row=0, padx=5, pady=5)
        frame_density_ratio.grid  (column=0, row=1, padx=5, pady=5)
        bn_set_for_all_slider.grid(column=0, row=2, padx=5, pady=5)

        # Fill the variability frame
        lbl_variability_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_variability.grid (column=0, row=1, padx=5, pady=5)

        # Fill the density ratio  frame
        lbl_density_ratio_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_density_ratio.grid (column=0, row=1,  padx=5, pady=5)

        # Fill the command frame
        bn_output.grid      (column=0, row=0,  padx=5, pady=5)
        bn_reset_image.grid (column=0, row=1,  padx=5, pady=5)
        bn_excel.grid       (column=0, row=2,  padx=5, pady=5)
        bn_histogram.grid   (column=0, row=3, padx=5, pady=5)

        root.bind('<Right>', lambda event: self.go_forward_backward('Forward'))
        root.bind('<Left>', lambda event: self.go_forward_backward('Backward'))

        # self.select_squares_for_display()

        image_name      = self.list_images[self.img_no]['Left Image Name']
        self.df_squares = self.read_squares(image_name)

        # Set the sliders and neighbour state for the first image
        self.set_density_ratio_slider_state()
        self.set_variability_slider_state()
        self.set_neighbour_state()
        self.select_squares_for_display()
        self.display_selected_squares()

        # Set the Exclude / Include button
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

    def exinclude(self):

        image_name = self.image_name
        if 'Exclude' not in self.df_batch.columns.values:
            self.df_batch['Exclude'] = False
        row_index = self.df_batch.index[self.df_batch['Ext Image Name'] == image_name].tolist()[0]
        if not self.df_batch.loc[row_index, 'Exclude']:
            self.df_batch.loc[row_index, 'Exclude'] = True
            self.bn_exclude.config(text='Include')
            self.text_for_info3.set('Excluded')
        else:
            self.df_batch.loc[row_index, 'Exclude'] = False
            self.bn_exclude.config(text='Exclude')
            self.text_for_info3.set('')
        self.df_batch.to_csv(self.batchfile_path)

    def key_pressed(self, event):
        self.cn_left_image.focus_set()
        print(f'Key pressed {event.keysym}')

        if event.keysym == 't':
            if self.show_squares:
                self.cn_left_image.delete("all")
                self.cn_left_image.create_image(0, 0, anchor=NW,
                                                image=self.list_images[self.img_no]['Left Image'])
                self.show_squares = False
            else:
                self.display_selected_squares()
                self.show_squares = True

        if event.keysym == 'o':
            self.output_pictures()

    def output_pictures(self):

        """
        Function is triggered bt pressing 'o' and will generate a pdf file containing all the images.
        :return:
        """

        save_img_no = self.img_no
        self.img_no = -1

        # Create the squares directory if it does not exist
        squares_dir = os.path.join(self.paint_directory, 'Output', 'Squares')
        if not os.path.isdir(squares_dir):
            os.makedirs(squares_dir)

        # Cycle through all images
        for img_no in range(len(self.list_images)):
            self.go_forward_backward('Forward')

            image_name   = self.list_images[self.img_no]['Left Image Name']
            print(image_name)

            # Delete the squares and write the canvas as an eps file
            self.cn_left_image.delete("all")
            self.cn_left_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])
            save_as_png(self.cn_left_image, os.path.join(squares_dir, image_name), image_name)

            # Add the squares and write the canvas as an eps file
            self.select_squares_for_display()
            self.display_selected_squares()
            image_name = image_name + '-squares'
            save_as_png(self.cn_left_image, os.path.join(squares_dir, image_name), image_name)

        # Find all the eps files and delete them
        eps_files = os.listdir(squares_dir)
        for item in eps_files:
            if item.endswith(".eps"):
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
        png_images[0].save(
            pdf_path, "PDF", resolution=200.0, save_all=True, append_images=png_images[1:])

        # Go back to the image where we were
        self.img_no = save_img_no - 1
        self.go_forward_backward('Forward')

    def exit_viewer(self):

        if self.user_change:
            self.save_image_state()
        exit()

    def image_selected(self, event):

        image_name = self.cb_image_names.get()
        print(image_name)
        index       = self.list_of_image_names.index(image_name)
        self.img_no = index - 1
        self.go_forward_backward('Forward')

    def set_variability_slider_state(self):

        max_allowed_variability = self.df_batch.loc[self.image_name]['Variability Setting']
        self.sc_variability.set(max_allowed_variability)

    def set_density_ratio_slider_state(self):

        min_required_density = self.df_batch.loc[self.image_name]['Density Ratio Setting']
        self.sc_density_ratio.set(min_required_density)

    def set_neighbour_state(self):

        neighbour_state = self.df_batch.loc[self.image_name]['Neighbour Setting']
        self.neighbour_var.set(neighbour_state)

    def save_variability_slider_state(self):

        self.df_batch.loc[self.image_name, 'Variability Setting'] = round(self.sc_variability.get(), 1)

    def save_density_ratio_slider_state(self):

        self.df_batch.loc[self.image_name, 'Density Ratio Setting'] = round(self.sc_density_ratio.get(), 1)

    def save_neighbour_state(self):

        self.df_batch.loc[self.image_name, 'Neighbour Setting'] = self.neighbour_var.get()

    def histogram(self):

        unique_cells = self.df_squares['Cell Id'].unique().tolist()
        for cell_id in unique_cells:
            self.provide_report_on_cell(self, cell_id)

            df_selection         = self.df_squares[self.df_squares['Cell Id'] == cell_id]
            df_selection_visible = df_selection[df_selection['Visible']]
            tau_values_visible   = df_selection_visible['Tau'].to_list()

            if len(tau_values_visible) > 0:
                tau_mean   = round(statistics.mean(tau_values_visible), 0)
                tau_median = round(statistics.median(tau_values_visible), 0)
                tau_std    = round(statistics.stdev(tau_values_visible), 1)

                print(f"For Cell Id: {cell_id}, the tau mean is {tau_mean}, the tau median is {tau_median} and the tau std is {tau_std}\n")

    def show_excel(self):

        # Path to the Excel application
        if platform.system() == 'Darwin':
            excel_path = '/Applications/Microsoft Excel.app'  # Adjust the path if necessary
        else:
            excel_path = 'C:\\Program Files\\Microsoft Office\\root\\OfficeXX\\Excel.exe'

        # Write the current df_squares before opening it
        self.write_squares()

        # Open Excel
        subprocess.Popen(['open', excel_path, self.squares_file_name])

        # And then write some miscellaneous data on the image

        nr_total_squares   = len(self.df_squares)
        tau_values         = self.df_squares[self.df_squares['Visible']]['Tau'].tolist()
        nr_visible_squares = len(tau_values)
        if nr_visible_squares != 0:
            tau_min            = min(tau_values)
            tau_max            = max(tau_values)
            tau_mean           = round(statistics.mean(tau_values), 0)
            tau_median         = round(statistics.median(tau_values), 0)
            tau_std            = round(statistics.stdev(tau_values), 1)
        else:
            tau_min            = '-'
            tau_max            = '-'
            tau_mean           = '-'
            tau_median         = '-'
            tau_std            = '-'

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

        self.user_change = True

        self.df_squares['Visible']                 = True
        self.df_squares['Neighbour Visible']       = True
        self.df_squares['Variability Visible']     = True
        self.df_squares['Density Ration Selected'] = True
        self.df_squares['Cell Id']                 = 0

        self.select_squares_for_display()
        self.display_selected_squares()

    def run_output(self):
        """
        Prepares the output files.
        For specific sets up probes or cell types, specific functions are needed
        :return:
        """

        # Get the slider and neighbour state and save it
        self.save_density_ratio_slider_state()
        self.save_variability_slider_state()
        self.save_neighbour_state()

        # Generate the graphpad and pdf directories if needed
        create_output_directories_for_graphpad(self.paint_directory)

        # Generate the graphpad info for summary statistics
        df_stats = analyse_all_images(self.paint_directory)
        create_summary_graphpad(self.paint_directory, df_stats)

    def set_for_all_slider(self):
        self.user_change = True

        self.df_batch['Density Ratio Setting'] = self.sc_density_ratio.get()
        self.df_batch['Variability Setting']  = self.sc_variability.get()

    def variability_changing(self, event):
        # Updating the numerical value of the slider is not needed with tk widget
        pass

    def density_ratio_changing(self, event):
        # Updating the numerical value of the slider is not needed with tk widget
        pass

    def variability_changed(self, event):
        self.user_change = True

        if self.mode_var.get() == 'HEAT':   # Should not happen,as the slider is disabled, but still....
            return

        self.select_squares_for_display()
        self.display_selected_squares()

    def density_ratio_changed(self, event):
        self.user_change = True

        if self.mode_var.get() == 'HEAT':
            return

        self.select_squares_for_display()
        self.display_selected_squares()

    def provide_report_on_all_squares(self, event):

        cell_ids   = self.df_squares['Cell Id'].unique()
        cell_ids.sort()
        nr_cells   = len(cell_ids)
        nr_squares = len(self.df_squares)

        print("All squares report")
        print('------------------')
        print("Number of squares: ", nr_squares)
        print("Number of cells: ", nr_cells)

        print(f'Cell Id |----------Tau--------------|--------Density------------|-------Variability--------|')
        print(f'         Mean     Sd    Max    Min   Mean     Sd    Max   Min    Mean    Sd     Max    Min  ')

        for cell_id in cell_ids:
            df_cells = self.df_squares[self.df_squares['Cell Id'] == cell_id]
            df_cells = df_cells[['Square Nr', 'Label Nr', 'Tau', 'Density', 'Variability', 'Density Ratio']]

            mean_tau = round(df_cells['Tau'].mean(), 0)
            sd_tau   = round(df_cells['Tau'].std(), 0)
            max_tau  = round(df_cells['Tau'].max(), 0)
            min_tau  = round(df_cells['Tau'].min(), 0)

            mean_density = round(df_cells['Density'].mean(), 0)
            sd_density   = round(df_cells['Density'].std(), 0)
            max_density  = round(df_cells['Density'].max(), 0)
            min_density  = round(df_cells['Density'].min(), 0)

            mean_variability = round(df_cells['Variability'].mean(), 2)
            sd_variability   = round(df_cells['Variability'].std(), 2)
            max_variability  = round(df_cells['Variability'].max(), 2)
            min_variability  = round(df_cells['Variability'].min(), 2)

            print(f'{cell_id:6} {mean_tau:6} {sd_tau:6} {max_tau:6} {min_tau:6} {mean_density:6} {sd_density:6} {max_density:6} {min_density:6} {mean_variability:6} {sd_variability:6} {max_variability:6} {min_variability:6}')

        print('\n\n')

        for cell_id in cell_ids:
            df_cells = self.df_squares[self.df_squares['Cell Id'] == cell_id]
            df_cells = df_cells[['Square Nr', 'Label Nr', 'Tau', 'Density', 'Variability', 'Density Ratio']]

            print(f'\n\nCell Id: {cell_id:6} \n')
            print(df_cells)
            print('\n')

    def provide_report_on_cell(self, event, cell_nr):
        """
        Display a bar chart plot for the selected cell
        :param event:
        :param cell_nr:
        :return:
        """

        # Retrieve the squares for the selected cell
        df_selection = self.df_squares[self.df_squares['Cell Id'] == cell_nr]
        df_visible = df_selection[df_selection['Visible']]
        if len(df_visible) == 0:
            print(f'There are {len(df_selection)} squares defined for cell {cell_nr}, but none are visible')
        else:
            tau_values = list(df_visible['Tau'])
            labels     = list(df_visible['Label Nr'])

            print(f'There are {len(df_visible)} squares visible for cell {cell_nr}: {labels}')
            print(f'The tau values for cell {cell_nr} are: {tau_values}')

            cell_ids = list(df_visible['Label Nr'])
            cell_str_ids = list(map(str, cell_ids))
            plt.figure(figsize=(5, 5))
            plt.bar(cell_str_ids, tau_values)
            plt.ylim(0, 400)

            # Print the numerical values
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

        self.df_squares['Variability Visible'] = False
        self.df_squares.loc[self.df_squares['Variability'] <= round(self.sc_variability.get(), 1), 'Variability Visible'] = True
        self.df_squares.loc[self.df_squares['Variability'] > round(self.sc_variability.get(), 1), 'Variability Visible'] = False

        self.df_squares['Density Ratio Visible'] = False
        self.df_squares.loc[self.df_squares['Density Ratio'] >= round(self.density_ratio.get(), 1), 'Density Ratio Visible'] = True
        self.df_squares.loc[self.df_squares['Density Ratio'] < round(self.density_ratio.get(), 1), 'Density Ratio Visible'] = False

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

        # If there are no squares you can stop here
        if len(self.df_squares) > 0:
            for index, row in self.df_squares.iterrows():
                if row['Visible']:
                    self.draw_single_square(row)
        return self.df_squares

    def draw_single_square(self, squares_row):

        colour_table = {1: ('blue', 'white'),
                        2: ('yellow', 'white'),
                        3: ('green', 'white'),
                        4: ('magenta', 'white'),
                        5: ('cyan', 'white'),
                        6: ('black', 'white')}

        square_nr = squares_row['Square Nr']
        cell_id   = squares_row['Cell Id']
        label_nr  = squares_row['Label Nr']

        col_nr = square_nr % self.nr_of_squares_in_row
        row_nr = square_nr // self.nr_of_squares_in_row
        width  = 512 / self.nr_of_squares_in_row
        height = 512 / self.nr_of_squares_in_row

        square_tag = f'square-{square_nr}'
        text_tag = f'text-{square_nr}'

        if cell_id == -1:        # The square is deleted (for good), stop processing
            return
        elif cell_id == 0:       # Square is removed from a cell
            self.cn_left_image.create_rectangle(col_nr * width,
                                                row_nr * width,
                                                col_nr * width + width,
                                                row_nr * height + height,
                                                outline="white",
                                                tags=square_tag)
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
            text_item = self.cn_left_image.create_text(col_nr * width + 0.5 * width,
                                                       row_nr * width + 0.5 * width,
                                                       text=str(self.df_squares.loc[square_nr]['Label Nr']),
                                                       font=('Arial', -10),
                                                       fill=colour_table[self.df_squares.loc[square_nr]['Cell Id']][1],
                                                       tags=text_tag)

        # The new square is made clickable -  for now use the text item
        self.cn_left_image.tag_bind(text_item, '<Button-1>', lambda e: self.square_assigned_to_cell(square_nr))
        self.cn_left_image.tag_bind(text_item, '<Button-2>', lambda e: self.provide_information_on_square(e, self.df_squares.loc[square_nr]['Label Nr'], square_nr))

    def square_assigned_to_cell(self, square_nr):

        if self.mode_var.get() == 'HEAT':
            return

        # Delete the current square
        square_tag = f'square-{square_nr}'
        text_tag = f'text-{square_nr}'
        self.cn_left_image.delete(square_tag, text_tag)
        self.cn_left_image.delete(text_tag)

        # Draw the new one
        self.draw_single_square(self.df_squares.loc[square_nr])

        # Record the new cell id`
        cell_id = int(self.cell_var.get())
        self.df_squares.at[square_nr, 'Cell Id'] = int(cell_id)

    def provide_information_on_square(self, event, label_nr, square_nr):

        if self.mode_var.get() == 'HEAT':
            return

        # Define the popup
        pop = Toplevel(root)
        pop.title("Square Info")
        pop.geometry("220x180")

        # Position the popup
        x = root.winfo_x()
        y = root.winfo_y()
        pop.geometry("+%d+%d" % (x + event.x + 15, y + event.y + 40))

        # Get the data to display
        square_nr     = self.df_squares.loc[square_nr]['Square Nr']
        variability   = self.df_squares.loc[square_nr]['Variability']
        density_ratio = self.df_squares.loc[square_nr]['Density Ratio']
        density       = self.df_squares.loc[square_nr]['Density']
        tau           = self.df_squares.loc[square_nr]['Tau']
        nr_tracks     = self.df_squares.loc[square_nr]['Nr Tracks']

        # Fill the popup
        padx_value = 10
        pady_value = 1
        lbl_width = 15

        ttk.Label(pop, text=f"Label Nr", anchor=W, width=lbl_width).grid(row=1, column=1, padx=padx_value,
                                                                         pady=pady_value)
        ttk.Label(pop, text=f"Square", anchor=W, width=lbl_width).grid(row=2, column=1, padx=padx_value,
                                                                       pady=pady_value)
        ttk.Label(pop, text=f"Tau", anchor=W, width=lbl_width).grid(row=3, column=1,
                                                                    padx=padx_value, pady=pady_value)
        ttk.Label(pop, text=f"Density", anchor=W, width=lbl_width).grid(row=4, column=1,
                                                                        padx=padx_value, pady=pady_value)
        ttk.Label(pop, text=f"Number of Tracks", anchor=W, width=lbl_width).grid(row=5, column=1,
                                                                                 padx=padx_value, pady=pady_value)
        ttk.Label(pop, text=f"Density Ratio", anchor=W, width=lbl_width).grid(row=6, column=1,
                                                                              padx=padx_value, pady=pady_value)
        ttk.Label(pop, text=f"Variability", anchor=W, width=lbl_width).grid(row=7, column=1,
                                                                            padx=padx_value, pady=pady_value)

        ttk.Label(pop, text=f"{label_nr}", anchor=W).grid(row=1, column=2, padx=padx_value, pady=pady_value)
        ttk.Label(pop, text=f"{square_nr}", anchor=W).grid(row=2, column=2, padx=padx_value, pady=pady_value)
        ttk.Label(pop, text=f"{tau}", anchor=W).grid(row=3, column=2, padx=padx_value, pady=pady_value)
        ttk.Label(pop, text=f"{density}", anchor=W).grid(row=4, column=2, padx=padx_value, pady=pady_value)
        ttk.Label(pop, text=f"{nr_tracks}", anchor=W).grid(row=5, column=2, padx=padx_value, pady=pady_value)
        ttk.Label(pop, text=f"{density_ratio}", anchor=W).grid(row=6, column=2, padx=padx_value, pady=pady_value)
        ttk.Label(pop, text=f"{variability}", anchor=W).grid(row=7, column=2, padx=padx_value, pady=pady_value)

    def start_rectangle(self, event):
        self.user_change = True
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
                if test_if_square_is_in_rectangle(square['X0'], square['Y0'], square['X1'], square['Y1'],
                                                  self.start_x, self.start_y, cur_x, cur_y):
                    self.df_squares.at[square['Square Nr'], 'Cell Id'] = int(cell_id)

        self.display_selected_squares()

    def select_mode_button(self):

        if self.mode_var.get() == "HEAT":
            self.rb_neighbour_free.configure(state=DISABLED)
            self.rb_neighbour_strict.configure(state=DISABLED)
            self.rb_neighbour_relaxed.configure(state=DISABLED)

            self.rb_cell0.configure(state=DISABLED)
            self.rb_cell1.configure(state=DISABLED)
            self.rb_cell2.configure(state=DISABLED)
            self.rb_cell3.configure(state=DISABLED)
            self.rb_cell4.configure(state=DISABLED)
            self.rb_cell5.configure(state=DISABLED)
            self.rb_cell6.configure(state=DISABLED)

            self.sc_variability.configure(state=DISABLED, takefocus=False)
            self.sc_density_ratio.configure(state=DISABLED, takefocus=False)

        elif self.mode_var.get() == "ROI":
            self.rb_neighbour_free.configure(state=NORMAL)
            self.rb_neighbour_strict.configure(state=NORMAL)
            self.rb_neighbour_relaxed.configure(state=NORMAL)

            self.rb_cell0.configure(state=NORMAL)
            self.rb_cell1.configure(state=NORMAL)
            self.rb_cell2.configure(state=NORMAL)
            self.rb_cell3.configure(state=NORMAL)
            self.rb_cell4.configure(state=NORMAL)
            self.rb_cell5.configure(state=NORMAL)
            self.rb_cell6.configure(state=NORMAL)

            self.sc_variability.configure(state=NORMAL)
            self.sc_density_ratio.configure(state=NORMAL)
        else:
            print('Big trouble!')

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
        if self.list_images[self.img_no]['Adjuvant'] is  None:
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
            print(f"Function 'read_squares' failed - Squares file {self.squares_file_name} was not found.")
            exit()
        return self.df_squares

    def read_batch(self):
        batch_file_path = os.path.join(self.paint_directory, self.image_name, 'grid_batch.csv')
        self.df_batch = read_batch_from_file(batch_file_path)
        if self.df_batch is None:
            print(f"Function 'read_batch' failed - Squares file {batch_file_path} was not found.")
            exit()
        return self.df_batch

    def write_squares(self):

        pass

        # It is in fact not necessary to write the squares file. It is reinterpreted every time it is loaded which square are visible
        # if self.mode == 'Directory':
        #     squares_file_name = os.path.join(self.paint_directory, self.image_name, 'grid', self.image_name + '-squares.csv')
        # else:
        #     squares_file_name = os.path.join(self.paint_directory, str(self.df_batch.iloc[self.img_no]['Experiment Date']),  self.image_name, 'grid',
        #                                      self.image_name + '-squares.csv')
        # save_squares_to_file(self.df_squares, squares_file_name)

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


proceed        = False
root_directory = ''
conf_file      = ''
mode           = ''


class SelectViewerDialog:

    def __init__(self, root):

        root.title('Image Viewer')

        self.root_directory, self.paint_directory, self.images_directory = get_default_directories()
        self.conf_file = ''

        content                       = ttk.Frame(root)
        frame_buttons                 = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory               = ttk.Frame(content, borderwidth=5, relief='ridge')

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
        btn_root_dir       = ttk.Button(frame_directory, text='Paint Directory', width=15, command=self.change_root_dir)
        btn_conf_file      = ttk.Button(frame_directory, text='Configuration file', width=15, command=self.change_conf_file)

        self.lbl_root_dir  = ttk.Label(frame_directory, text=self.root_directory, width=80)
        self.lbl_conf_file = ttk.Label(frame_directory, text=self.conf_file, width=80)

        self.mode_var = StringVar(value="Directory")
        self.rb_mode_directory  = ttk.Radiobutton(frame_directory, text="", variable=self.mode_var, width=10, value="Directory")
        self.rb_mode_conf_file  = ttk.Radiobutton(frame_directory, text="", variable=self.mode_var, width=10, value="Conf File")

        btn_root_dir.grid           (column=0, row=0, padx=10, pady=5)
        btn_conf_file.grid          (column=0, row=1, padx=10, pady=5)

        self.lbl_root_dir.grid      (column=1, row=0, padx=20, pady=5)
        self.lbl_conf_file.grid     (column=1, row=1, padx=20, pady=5)

        self.rb_mode_directory.grid (column=2, row=0, padx=10, pady=5)
        self.rb_mode_conf_file.grid (column=2, row=1, padx=10, pady=5)

    def change_root_dir(self):

        global root_directory
        global conf_file
        global mode

        self.root_directory = filedialog.askdirectory(initialdir=self.root_directory)
        save_default_directories(self.root_directory, self.paint_directory, self.images_directory)
        if len(self.root_directory) != 0:
            self.mode_var.set('Directory')
            self.rb_mode_directory.focus()
            self.lbl_root_dir.config(text=self.root_directory)

    def change_conf_file(self):
        global root_directory
        global conf_file
        global mode

        self.conf_file = filedialog.askopenfilename(initialdir=self.paint_directory, title='Select a configuration file')

        if len(self.conf_file) != 0:
            self.mode_var.set('Conf File')
            self.rb_mode_conf_file.focus()
            self.lbl_conf_file.config(text=self.conf_file)
            # save_default_directories(self.root_directory, self.paint_directory, self.images_directory)

    def process(self):
        global proceed
        global root_directory
        global conf_file
        global mode

        error = False

        mode = self.mode_var.get()
        if mode == "Directory":
            root_directory = self.root_directory
            if not os.path.isdir(root_directory):
                print('Whoops')
                error = True

        else:
            conf_file = self.conf_file
            if not os.path.isfile(conf_file):
                print('Whoops')
                error = True

        if not error:
            proceed = True
            root.destroy()

    def exit_dialog(self):

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
    image_viewer = ImageViewer(root, root_directory, conf_file, mode)
    root.mainloop()
