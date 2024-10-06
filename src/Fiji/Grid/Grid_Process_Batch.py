import csv
import os
import sys
import time

from ij import IJ
from java.lang.System import getProperty

paint_dir = getProperty('fiji.dir') + os.sep + "scripts" + os.sep + "Plugins" + os.sep + "Paint"
sys.path.append(paint_dir)

from Trackmate import paint_trackmate
from CommonSupportFunctions import create_directories
from FijiSupportFunctions import (
    fiji_get_file_open_write_attribute,
    fiji_get_file_open_append_attribute,
    ask_user_for_image_directory)

from LoggerConfigFiji import logger, change_file_handler

change_file_handler('Grid Process Batch.log')


def grid_analysis_batch(paint_directory, image_source_directory):

    # Open the batch file to determine the columns (which should be in the paint directory)

    batch_file_name = os.path.join(paint_directory, "batch.csv")
    old_batch_file_name = os.path.join(paint_directory, "previous_batch.csv")

    try:
        batch_file = open(batch_file_name, 'rt')
        csv_reader = csv.reader(batch_file)
        for batch_column_names in csv_reader:  # Read the first row into batch_column_names and then stop
            break
        batch_file.close()
    except IOError:
        logger.error("Could not open batch file:" + batch_file_name)
        sys.exit(-1)

    # -----------------------------------------------------------------------------
    # Then open the batch file for processing
    # -----------------------------------------------------------------------------

    try:
        batch_file = open(batch_file_name, 'rt')
        csv_reader = csv.DictReader(batch_file)
    except IOError:
        logger.errro("Could not open batch file:" + batch_file_name)
        sys.exit(-1)

    # -----------------------------------------------------------------------------
    # Open the results file for writing the colum headers only (in the paint directory)
    # -----------------------------------------------------------------------------

    temp_batch_file_name = os.path.join(paint_directory, "temp_batch.csv")
    try:
        temp_batch_file = open(temp_batch_file_name, fiji_get_file_open_write_attribute())
        temp_batch_writer = csv.DictWriter(temp_batch_file, batch_column_names)
        temp_batch_writer.writeheader()
        temp_batch_file.close()
    except IOError:
        logger.error("Could not open results file:" + temp_batch_file_name)
        sys.exit(-1)

    # ------------------------------------------
    # Count how many images need to be processed
    # ------------------------------------------

    count = 0
    nr_to_process = 0
    for row in csv_reader:
        if 'y' in row['Process'].lower():
            nr_to_process += 1
        count += 1

    if nr_to_process == 0:
        logger.warning("No images selected for processing")
        return -1

    logger.info("Number of images processed: " + str(nr_to_process) + " out of a total of " + str(
        count) + " images in the batch file.")

    # -----------------------------------------------------------------------------
    # Cycle through images and process where requested
    # -----------------------------------------------------------------------------

    message = "Processing " + str(nr_to_process) + " images in directory " + image_source_directory
    logger.info(message)

    nr_images_processed = 0
    nr_images_failed = 0
    nr_images_not_found = 0

    # Start at the beginning for the main processing
    batch_file.seek(0)
    next(csv_reader, None)  # Skip the header

    file_count = 1
    for row in csv_reader:  # Here we are reading the batch file
        try:
            adjuvant = row['Adjuvant']
            image_name = row['Image Name']
            threshold = float(row['Threshold'])
            process = row['Process']
            image_file = row['Ext Image Name']

        except (KeyError, IndexError):
            logger.error("Error in batch file format")
            sys.exit(-1)

        if adjuvant == 'None':
            row['Adjuvant'] = 'No'

        if 'Y' in process or 'y' in process:
            logger.info(image_file)

            image_file_name = os.path.join(image_source_directory, image_name + '.nd2')

            if not os.path.exists(image_file_name):
                logger.warning("\nProcessing: Failed to open image: " + image_file_name)
                row['Image Size'] = '-'
                nr_images_not_found += 1
            else:
                row['Image Size'] = os.path.getsize(image_file_name)
                imp = IJ.openImage(image_file_name)
                imp.show()
                IJ.run("Enhance Contrast", "saturated=0.35")
                IJ.run("Grays")
                ext_image_name = image_name + "-threshold-" + str(int(threshold))

                create_directories(os.path.join(paint_directory, ext_image_name), True)

                # ---------------------------------------
                # Run the full image (in RunTrackMate.py)
                # ---------------------------------------

                logger.info(
                    "Processing file nr " + str(file_count) + " of " + str(nr_to_process) + ": " + ext_image_name)
                time_stamp = time.time()
                tracks_filename = os.path.join(paint_directory, ext_image_name, "tracks",
                                               ext_image_name + "-full-tracks.csv")
                tiff_filename = os.path.join(paint_directory, ext_image_name, "img", ext_image_name + ".tiff")

                nr_spots, total_tracks, long_tracks = paint_trackmate(threshold, tracks_filename, tiff_filename)
                if nr_spots == -1:
                    logger.error("\n'Process single image' did not manage to run 'paint_trackmate'")
                    return -1
                else:
                    time.sleep(3)  # Display the image for 3 seconds
                run_time = round(time.time() - time_stamp, 1)

                logger.info('Nr of spots: ' + str(nr_spots) + " processed in " + str(run_time) + " seconds")
                if nr_spots == -1:
                    nr_images_failed += 1
                else:
                    nr_images_processed += 1
                imp.close()

                # Update the row
                row['Nr Spots'] = nr_spots
                row['Nr Tracks'] = long_tracks
                row['Run Time'] = run_time
                row['Ext Image Name'] = ext_image_name
                row['Time Stamp'] = time.asctime(time.localtime(time.time()))

                file_count += 1
        else:
            pass  # Do nothing, just write the unchanged row

        # And write the row (changed or not) to the output
        try:
            temp_batch_file = open(temp_batch_file_name, fiji_get_file_open_append_attribute())
            temp_batch_writer = csv.DictWriter(temp_batch_file, batch_column_names)
            temp_batch_writer.writerow(row)
            temp_batch_file.close()
        except IOError:
            exit()

    temp_batch_file.close()
    batch_file.close()

    logger.info("Number of images processed successfully:         " + str(nr_images_processed))
    logger.info("Number of images not found:                      " + str(nr_images_not_found))
    logger.info("Number of images not not successfully processed: " + str(nr_images_failed))

    if os.path.isfile(old_batch_file_name):
        os.remove(old_batch_file_name)
    try:
        os.rename(batch_file_name, old_batch_file_name)
    except OSError:
        logger.error("Could not rename batch file: " + old_batch_file_name)
        return -1

    if os.path.isfile(batch_file_name):
        os.remove(batch_file_name)
    try:
        os.rename(temp_batch_file_name, batch_file_name)
    except OSError:
        logger.error("Could not rename results file: " + temp_batch_file_name)
        return -1

    return 0


if __name__ == "__main__":

    paint_directory = ask_user_for_image_directory("Specify the Paint directory", 'Paint')
    if len(paint_directory) == 0:
        logger.warning("\nUser aborted the batch processing.")
        exit(0)

    # Get the directory where the images are located
    images_directory = ask_user_for_image_directory("Specify the Image Source directory", 'Images')
    if len(images_directory) == 0:
        logger.warning("\nUser aborted the batch processing.")
        exit(0)

    time_stamp = time.time()
    grid_analysis_batch(paint_directory, images_directory)
    run_time = time.time() - time_stamp
    run_time = round(run_time, 1)
    logger.info("\nProcessing completed in " + str(run_time) + " seconds")
