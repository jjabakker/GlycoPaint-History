import csv
import os
import sys
from inspect import currentframe, getframeinfo

from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate import Model
from ij import IJ
from ij.plugin.frame import RoiManager
from java.lang.System import getProperty

paint_dir = getProperty('fiji.dir') + os.sep + "scripts" + os.sep + "Plugins" + os.sep + "Paint"
sys.path.append(paint_dir)

from Trackmate import paint_trackmate

from CommonSupportFunctions import (
    create_directories,
    get_default_image_directory)

from FijiSupportFunctions import fiji_get_file_open_write_attribute

from fiji.util.gui import GenericDialogPlus

from LoggerConfig import paint_logger


def process_full_image(threshold, image_directory, image_name, cell_type, probe, probe_type, concentration_probe):
    """
    This function runs trackmate on the full image, i.e. without any ROI identified
    The results are written to:
        full_results.csv file
        full_tracks_csv
    The image is saved as tiff file
    :param threshold:
    :param image_directory:
    :param image_name:
    :param cell_type:
    :param probe:
    :param probe_type:
    :param concentration_probe:
    :return:
    """

    full_results_file = os.path.join(image_directory, image_name, image_name, "-full-results.csv")
    full_tracks_filename = os.path.join(image_directory, image_name, "tracks", image_name, "-full-tracks.csv")
    tiff_filename = os.path.join(image_directory, image_name, "img", image_name, ".tiff")

    nr_spots, total_tracks, long_tracks = paint_trackmate(threshold, full_tracks_filename, tiff_filename)
    if nr_spots == -1:
        paint_logger.error("\n'Process full image' did not manage to run 'paint_trackmate'")
        paint_logger.error(getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        return -1

    # ----------------------
    # Write the tracks file
    # ----------------------

    open_attribute = fiji_get_file_open_write_attribute()
    export_file = open(full_results_file, open_attribute)
    export_writer = csv.writer(export_file)

    fields = ["Image Name", "Cell Type", "Probe", "Probe Type", "Concentration", "Threshold", "F Spots",
              "F Total Tracks", "F Long Tracks", "F Area"]
    export_writer.writerow(fields)

    area = round(82.0864 * 82.0864, 0)

    fields = [image_name, cell_type, probe, probe_type, concentration_probe, threshold, nr_spots, total_tracks,
              long_tracks, area]
    export_writer.writerow(fields)

    export_file.close()

    return 0


def get_user_input(interactive):
    """
    :param interactive:
    :return:
    """

    model = Model()
    model.setLogger(Logger.IJ_LOGGER)

    threshold = 5.0
    probe = "1 Mono"
    probe_type = "Simple"
    concentration_probe = 1

    # See if there is a choices file. If there is, take the default values from there
    configuration_dir = os.path.expanduser('~') + os.sep + "Paint Profile"
    choices_file = configuration_dir + os.sep + "cell_user_choices.csv"

    try:
        f = open(choices_file, 'rt')
        reader = csv.DictReader(f)  # f will have a valid value
        for row in reader:
            threshold = float(row['threshold'])
            concentration_probe = float(row['concentration_probe'])
            probe = row['probe']
            probe_type = row['probe_type']
        f.close()
    except IOError:
        # This is not a real problem, we then use defaults
        threshold = 5.0
        concentration_probe = 1.0
        probe = "1 Mono"
        probe_type = "Simple"

    # In all cases show the dialog to allow the user to change
    if interactive:
        gui = GenericDialogPlus("PAINT input")
        gui.addNumericField("Quality Threshold", threshold, 0)
        gui.addNumericField("Concentration Probe", concentration_probe, 0)
        gui.addRadioButtonGroup("Probe", ["1 Mono", "2 Mono", "6 Mono",
                                          "1 Bi", "2 Bi", "6 Bi",
                                          "1 Tri", "2 Tri", "6 Tri"],
                                3, 3, probe)
        gui.addRadioButtonGroup("Type of Probe", ["Simple", "Peptide"], 1, 2, probe_type)

        gui.showDialog()

        if gui.wasOKed():
            threshold = gui.getNextNumber()
            concentration_probe = gui.getNextNumber()
            probe = gui.getNextRadioButton()
            probe_type = gui.getNextRadioButton()

            # Write the choices file
            open_attribute = fiji_get_file_open_write_attribute()
            export_file = open(choices_file, open_attribute)
            export_writer = csv.writer(export_file)
            fields = ["threshold", "concentration_probe", "probe", "probe_type"]
            export_writer.writerow(fields)
            fields = [threshold, concentration_probe, probe, probe_type]
            export_writer.writerow(fields)

        else:
            return 0, 0, 0, 0

    return probe, probe_type, threshold, concentration_probe


def square_analysis():
    """
    This routine needs to be run on every single image for which the square analysis needs to be performed.
    It simply runs Trackmate on the full image and stores the tracks and image file

    Later this information is used to determine which squares are the critical ones and for them the
    Taus are calculated.
    :return:
    """

    # Determine where the Trackmate Data root is
    image_directory = get_default_image_directory()

    # There should already be an image selected.....
    try:
        imp = IJ.getImage()
    except (RuntimeError, Exception):
        imp = None

    if imp is None:
        print("No image selected")
        model.getLogger().log("No image selected")
        return -1
    image_title = imp.getTitle().replace(".nd2", "")

    # Prepare the directory structure
    create_directories(image_directory + os.sep + image_title, True)

    # There should be no ROIs in this stage, so remove any that may be there
    rm = RoiManager.getInstance()
    if not rm:
        rm = RoiManager()
    rm.runCommand("Reset")
    rm.runCommand("Sort")  # A trick to update the window

    # Ask for probe information and threshold
    probe, probe_type, threshold, concentration_probe = get_user_input(interactive=True)
    if probe == 0:
        paint_logger.info("User aborted the operation")
        return 0
    cell_type = " "

    # Run the full image (in RunTrackMate.py)
    process_full_image(threshold, image_directory, image_title, cell_type, probe, probe_type, concentration_probe)

    return 0


if __name__ == "__main__":

    model = Model()
    model.setLogger(Logger.IJ_LOGGER)

    if square_analysis() != 0:
        print("\n\nRoutine aborted with error")
        model.getLogger().log("\n\nRoutine aborted with error")
    else:
        print("\n\nRoutine completed successfully")
        model.getLogger().log("\n\nRoutine completed successfully")
