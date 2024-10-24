import csv
import os
import sys
import time

from ij import IJ
from java.lang.System import getProperty
from javax.swing import JOptionPane

paint_dir = os.path.join(getProperty('fiji.dir'), "scripts", "Plugins", "Paint")
sys.path.append(paint_dir)

from DirectoriesAndLocations import (
    get_tracks_file_path,
    get_experiment_info_file_path,
    get_experiment_tm_file_path,
    get_tracks_dir_path,
    get_image_file_path,
    create_directories)

from Trackmate import excute_trackmate_in_Fiji

from FijiSupportFunctions import (
    fiji_get_file_open_write_attribute,
    fiji_get_file_open_append_attribute,
    ask_user_for_image_directory,
    suppress_fiji_output,
    restore_fiji_output)

from LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name)

paint_logger_change_file_handler_name('Grid Process Batch.log')


def run_trackmate(experiment_directory, image_source_directory):
    # Open the experiment file to determine the columns (which should be in the paint directory)

    # experiment_info_path = os.path.join(experiment_directory, EXPERIMENT_INFO)
    experiment_info_path = get_experiment_info_file_path(experiment_directory)

    if not os.path.exists(experiment_info_path):
        msg = "Warning: The file '{}' does not exist.".format(experiment_info_path)
        paint_logger.error(msg)
        JOptionPane.showMessageDialog(None, msg, "Warning", JOptionPane.WARNING_MESSAGE)
        suppress_fiji_output
        sys.exit()

    with open(experiment_info_path, mode='r') as experiment_info_file:

        csv_reader = csv.DictReader(experiment_info_file)
        if not {'Recording Sequence Nr', 'Recording Name', 'Experiment Date', 'Experiment Name', 'Condition Nr',
                'Replicate Nr', 'Recording Condition Name', 'Probe', 'Probe Type', 'Cell Type', 'Adjuvant',
                'Concentration', 'Threshold', 'Process'} <= set(csv_reader.fieldnames):
            paint_logger.error("Error: Missing expected column headers ")
            suppress_fiji_output()
            sys.exit()

        try:
            # Count how many images need to be processed
            count = 0
            nr_to_process = 0
            for row in csv_reader:
                if 'y' in row['Process'].lower():
                    nr_to_process += 1
                count += 1
            if nr_to_process == 0:
                paint_logger.warning("No images selected for processing")
                return -1

            message = "Processing " + str(nr_to_process) + " images in directory " + image_source_directory
            paint_logger.info(message)

            # Initialise the experiment_tm file with the column headers
            col_names = csv_reader.fieldnames + ['Nr Spots', 'Nr Tracks', 'Run Time', 'Ext Recording Name', 'Recording Size', 'Time Stamp']
            experiment_tm_file_path = initialise_experiment_tm_file(experiment_directory, col_names)

            # And now cycle through the experiment file
            nr_images_processed = 0
            nr_images_failed = 0
            nr_images_not_found = 0

            experiment_info_file.seek(0)
            csv_reader = csv.DictReader(experiment_info_file)

            file_count = 0
            for row in csv_reader:  # Here we are reading the experiment file
                if 'y' in row['Process'].lower():
                    file_count += 1
                    paint_logger.info(
                        "Processing file nr " + str(file_count) + " of " + str(nr_to_process) + ": " + row['Recording Name'])

                    status, row = process_image(row, image_source_directory, experiment_directory)
                    if status == 'OK':
                        nr_images_processed += 1
                    elif status == 'NOT_FOUND':
                        nr_images_not_found += 1
                    elif status == 'FAILED':
                        nr_images_not_found += 1

                write_row_to_temp_file(row, experiment_tm_file_path, col_names)

            paint_logger.info("Number of images processed successfully:      " + str(nr_images_processed))
            paint_logger.info("Number of images not found:                   " + str(nr_images_not_found))
            paint_logger.info("Number of images not  successfully processed: " + str(nr_images_failed))

            if nr_images_processed == 0:
                msg = "No images processed successfully. Refer to Paint log for details."
                paint_logger.warning(msg)
                JOptionPane.showMessageDialog(None, msg, "Warning", JOptionPane.WARNING_MESSAGE)
            elif nr_images_not_found:
                msg = "Some images were not found. Refer to Paint log for details."
                paint_logger.warning(msg)
                JOptionPane.showMessageDialog(None, msg, "Warning", JOptionPane.WARNING_MESSAGE)

            return 0

        except KeyError as e:
            paint_logger.error("Run_Trackmate: Missing expected column in row: {e}")
            suppress_fiji_output()
            sys.exit(0)


def process_image(row, image_source_directory, experiment_directory):
    status = 'OK'
    adjuvant = row['Adjuvant']
    image_name = row['Recording Name']
    threshold = float(row['Threshold'])

    if adjuvant == 'None':
        row['Adjuvant'] = 'No'

    image_file_name = os.path.join(image_source_directory, image_name + '.nd2')

    if not os.path.exists(image_file_name):
        paint_logger.warning("Processing: Failed to open image: " + image_file_name)
        row['Recording Size'] = 0
        status = 'NOT_FOUND'
    else:
        row['Recording Size'] = os.path.getsize(image_file_name)
        imp = IJ.openImage(image_file_name)
        imp.show()
        IJ.run("Enhance Contrast", "saturated=0.35")
        IJ.run("Grays")

        # Set the scale
        # IJ.run("Set Scale...", "distance=6.2373 known=1 unit=micron")
        # IJ.run("Scale Bar...", "width=10 height=5 thickness=3 bold overlay")

        ext_image_name = image_name + "-threshold-" + str(int(threshold))

        create_directories(os.path.join(experiment_directory, ext_image_name), True)

        time_stamp = time.time()
        tracks_file_path = get_tracks_file_path(experiment_directory, ext_image_name)
        image_file_path = get_image_file_path(experiment_directory, ext_image_name)

        # suppress_fiji_output()
        nr_spots, total_tracks, long_tracks = excute_trackmate_in_Fiji(threshold, tracks_file_path, image_file_path)
        # restore_fiji_output()

        # IJ.run("Set Scale...", "distance=6.2373 known=1 unit=micron")
        # IJ.run("Scale Bar...", "width=10 height=5 thickness=3 bold overlay")

        if nr_spots == -1:
            paint_logger.error("\n'Process single image' did not manage to run 'paint_trackmate'")
            status = 'FAILED'
        else:
            time.sleep(3)  # Display the image for 3 seconds
        run_time = round(time.time() - time_stamp, 1)

        paint_logger.debug('Nr of spots: ' + str(nr_spots) + " processed in " + str(run_time) + " seconds")
        imp.close()

        # Update the row
        row['Nr Spots'] = nr_spots
        row['Nr Tracks'] = long_tracks
        row['Run Time'] = run_time
        row['Ext Recording Name'] = ext_image_name
        row['Time Stamp'] = time.asctime(time.localtime(time.time()))

    return status, row


def initialise_experiment_tm_file(experiment_directory, column_names):
    temp_file_path = get_experiment_tm_file_path(experiment_directory)
    try:
        temp_file = open(temp_file_path, fiji_get_file_open_write_attribute())
        temp_writer = csv.DictWriter(temp_file, column_names)
        temp_writer.writeheader()
        temp_file.close()
        return temp_file_path
    except IOError:
        paint_logger.error("Could not open results file:" + temp_file_path)
        suppress_fiji_output()
        sys.exit(-1)


def write_row_to_temp_file(row, temp_file_path, column_names):
    try:
        temp_file = open(temp_file_path, fiji_get_file_open_append_attribute())
        temp_writer = csv.DictWriter(temp_file, column_names)
        temp_writer.writerow(row)
        temp_file.close()
    except IOError:
        paint_logger.error("Could not write results file:" + temp_file_path)
        suppress_fiji_output()
        sys.exit()


if __name__ == "__main__":

    experiment_directory = ask_user_for_image_directory("Specify the Experiment directory", 'Paint')
    if len(experiment_directory) == 0:
        paint_logger.warning("User aborted the batch processing.")
        suppress_fiji_output()
        exit(0)

    # Get the directory where the images are located
    images_directory = ask_user_for_image_directory("Specify the Image Source directory", 'Images')
    if len(images_directory) == 0:
        paint_logger.warning("User aborted the batch processing.")
        suppress_fiji_output()
        exit(0)

    time_stamp = time.time()
    run_trackmate(experiment_directory, images_directory)
    run_time = time.time() - time_stamp
    run_time = round(run_time, 1)
    paint_logger.info("\nProcessing completed in " + str(run_time) + " seconds")
