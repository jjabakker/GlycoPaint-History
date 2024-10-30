import os
import sys
from tkinter import *

import pandas as pd
from PIL import Image, ImageTk

from src.Application.Utilities.General_Support_Functions import read_squares_from_file
from src.Common.Support.DirectoriesAndLocations import (
    get_trackmate_image_dir_path,
    get_squares_file_path)
from src.Common.Support.LoggerConfig import paint_logger


def get_images(self):
    """
    Retrieve the images to be displayed (for the left and right frame) from disk.
    A list with all necessary attributes for each image is created.
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

        image_name = self.df_experiment.iloc[index]['Ext Recording Name']
        if self.user_specified_mode == "PROJECT_LEVEL":

            experiment = str(self.df_experiment.iloc[index]['Experiment Date'])
            exp_dir = os.path.join(self.project_directory, experiment)
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

        # If there is no 'TrackMate Images' directory below the image directory, skip it
        if not os.path.isdir(trackmate_images_dir):
            paint_logger.error(
                f"Function 'get_images' failed - The directory for TrackMate images does not exist: {trackmate_images_dir}")
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

                # Retrieve the square numbers for this image
                df_squares = read_squares_from_file(squares_file_path)
                square_nrs = list(df_squares['Square Nr'])
                # self.df_experiment.loc[image_name, 'Nr Spots'] = len(square_nrs)    # ToDo what were we tryuing to do here?

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
        right_valid, right_img = get_corresponding_bf(bf_dir, image_name)

        record = {
            "Left Image Name": self.df_experiment.iloc[index]['Ext Recording Name'],
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

            "Min Required Density Ratio": self.df_experiment.iloc[index]['Min Required Density Ratio'],
            "Max Allowable Variability": self.df_experiment.iloc[index]['Max Allowable Variability'],
            "Neighbour Mode": self.df_experiment.iloc[index]['Neighbour Mode'],

            "Tau": tau
        }

        list_images.append(record)

    print("\n\n")

    if error_count > 0:
        paint_logger.error(
            f"There were {error_count} out of {len(self.df_experiment)} images for which no picture was available")

    return list_images


def get_corresponding_bf(bf_dir, recording_name):
    """
    Retrieve the corresponding BF image for the given image name
    """

    if not os.path.exists(bf_dir):
        paint_logger.error(
            "Function 'get_corresponding_bf' failed - The directory for jpg versions of BF images does not exist. Run 'Convert BF Images' first")
        sys.exit()

    # Peel off the 'threshold' and add -BF*.jpg
    recording_name = "-".join(recording_name.split("-")[:-2])

    # List of possible BF image names
    bf_images = [f"{recording_name}-BF.jpg", f"{recording_name}-BF1.jpg", f"{recording_name}-BF2.jpg"]

    # Iterate through the list and check if the file exists
    recording_name = None
    for img in bf_images:
        if os.path.isfile(os.path.join(bf_dir, img)):
            recording_name = img
            break

    if recording_name:
        img = ImageTk.PhotoImage(Image.open(os.path.join(bf_dir, recording_name)))
        valid = True
    else:
        img = ImageTk.PhotoImage(Image.new('RGB', (512, 512), (235, 235, 235)))
        valid = False

    return valid, img
