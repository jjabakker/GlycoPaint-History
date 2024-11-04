import os
import sys
from tkinter import *

from PIL import Image, ImageTk

from src.Common.Support.LoggerConfig import paint_logger


def get_images(self, initial=False):
    """
    Retrieve the images to be displayed (for the left and right frame) from disk.
    A list with all necessary attributes for each image is created.
    """

    # Create an empty lst that will hold the images
    list_images = []
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
            trackmate_images_dir = get_trackmate_image_dir_path(exp_dir, image_name)
        else:
            exp_dir = self.experiment_directory_path
            bf_dir = self.experiment_bf_directory
            trackmate_images_dir = get_trackmate_image_dir_path(exp_dir, image_name)

        try:
            left_img = ImageTk.PhotoImage(Image.open(os.path.join(trackmate_images_dir, image_name + '.tiff')))
            valid = True
        except:
            valid = False
            left_img = Image.new('RGB', (512, 512), "rgb(235,235,235)")
            left_img = ImageTk.PhotoImage(left_img)
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
            "Concentration": str(self.df_experiment.iloc[index]['Concentration']),

            "Threshold": self.df_experiment.iloc[index]['Threshold'],
            "Nr Spots": int(self.df_experiment.iloc[index]['Nr Spots']),
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

    if initial:
        self.saved_list_images = list_images

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
