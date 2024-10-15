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
from src.Common.Support.LoggerConfig import paint_logger, paint_logger_change_file_handler_name

def save_as_png(canvas, file_name):
    # First save as a postscript file
    canvas.postscript(file=file_name + '.ps', colormode='color')

    # Then let PIL convert to a png file
    img = Image.open(file_name + '.ps')
    img.save(f"{file_name}.png", 'png')


def save_square_info_to_batch(self):
    for index, row in self.df_batch.iterrows():
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

        self.df_batch.loc[index, 'Nr Visible Squares'] = nr_visible_squares
        self.df_batch.loc[index, 'Nr Total Squares'] = nr_total_squares
        self.df_batch.loc[index, 'Squares Ratio'] = squares_ratio


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

