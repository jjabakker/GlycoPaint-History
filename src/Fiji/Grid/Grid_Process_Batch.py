import csv
import os
import sys
import time

from ij import IJ
from java.lang.System import getProperty

paint_dir = os.path.join(getProperty('fiji.dir'), "scripts", "Plugins", "Paint")
sys.path.append(paint_dir)


# paint_dir = os.path.join(getProperty('fiji.dir'), "scripts", "Plugins", "Paint", "Grid")
# sys.path.append(paint_dir)

from Trackmate import paint_trackmate
from CommonSupportFunctions import create_directories
from FijiSupportFunctions import (
    fiji_get_file_open_write_attribute,
    fiji_get_file_open_append_attribute,
    ask_user_for_image_directory)

from LoggerConfig import paint_logger, change_file_handler

change_file_handler('Grid Process Batch.log')


def grid_analysis_batch(paint_directory, image_source_directory):
    # Open the batch file to determine the columns (which should be in the paint directory)

    batch_file_name = os.path.join(paint_directory, "batch.csv")
    old_batch_file_name = os.path.join(paint_directory, "previous_batch.csv")

    if not os.path.exists(batch_file_name):
        paint_logger.error("Error: The file '{}' does not exist.".format(batch_file_name))
        sys.exit()

    with open(batch_file_name, mode='r') as batch_file:

        csv_reader = csv.DictReader(batch_file)
        if not {'Batch Sequence Nr','Experiment Date', 'Experiment Name', 'Experiment Nr',	'Experiment Seq Nr', 'Image Name',
                'Probe', 'Probe Type', 'Cell Type', 'Adjuvant',	'Concentration', 'Threshold', 'Process'} <= set(csv_reader.fieldnames):
            paint_logger.error("Error: Missing expected column headers ")
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

            # Initialise the temp_batch_file with the column headers
            temp_batch_file_name = initialise_temp_batch(paint_directory, csv_reader.fieldnames)

            # And now cycle through the batch file

            nr_images_processed = 0
            nr_images_failed = 0
            nr_images_not_found = 0

            batch_file.seek(0)
            csv_reader = csv.DictReader(batch_file)

            file_count = 0
            for row in csv_reader:  # Here we are reading the batch file
                if 'y' in row['Process'].lower():
                    file_count += 1
                    paint_logger.info("Processing file nr " + str(file_count) + " of " + str(nr_to_process) + ": " + row['Ext Image Name'])
                    status, row = process_row(row, image_source_directory, paint_directory)
                    if status == 'OK':
                        nr_images_processed += 1
                    elif status == 'NOT_FOUND':
                        nr_images_not_found += 1
                    elif status == 'FAILED':
                        nr_images_not_found += 1

                write_row_to_temp_batch(row, temp_batch_file_name, csv_reader.fieldnames)

            paint_logger.info("Number of images processed successfully:      " + str(nr_images_processed))
            paint_logger.info("Number of images not found:                   " + str(nr_images_not_found))
            paint_logger.info("Number of images not  successfully processed: " + str(nr_images_failed))

            if os.path.isfile(old_batch_file_name):
                os.remove(old_batch_file_name)
            try:
                os.rename(batch_file_name, old_batch_file_name)
            except OSError:
                paint_logger.error("Could not rename batch file: " + old_batch_file_name)
                return -1

            if os.path.isfile(batch_file_name):
                os.remove(batch_file_name)
            try:
                os.rename(temp_batch_file_name, batch_file_name)
            except OSError:
                paint_logger.error("Could not rename results file: " + temp_batch_file_name)
                return -1

            return 0

        except KeyError as e:
            paint_logger.error("Missing expected column in row: {e}")
            return


def process_row(row, image_source_directory, paint_directory):

    status = 'OK'
    adjuvant = row['Adjuvant']
    image_name = row['Image Name']
    threshold = float(row['Threshold'])

    if adjuvant == 'None':
        row['Adjuvant'] = 'No'

    image_file_name = os.path.join(image_source_directory, image_name + '.nd2')

    if not os.path.exists(image_file_name):
        paint_logger.warning("\nProcessing: Failed to open image: " + image_file_name)
        row['Image Size'] = '-'
        status = 'NOT_FOUND'
    else:
        row['Image Size'] = os.path.getsize(image_file_name)
        imp = IJ.openImage(image_file_name)
        imp.show()
        IJ.run("Enhance Contrast", "saturated=0.35")
        IJ.run("Grays")
        ext_image_name = image_name + "-threshold-" + str(int(threshold))

        create_directories(os.path.join(paint_directory, ext_image_name), True)

        time_stamp = time.time()
        tracks_filename = os.path.join(paint_directory, ext_image_name, "tracks",
                                       ext_image_name + "-full-tracks.csv")
        tiff_filename = os.path.join(paint_directory, ext_image_name, "img", ext_image_name + ".tiff")

        nr_spots, total_tracks, long_tracks = paint_trackmate(threshold, tracks_filename, tiff_filename)
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
        row['Ext Image Name'] = ext_image_name
        row['Time Stamp'] = time.asctime(time.localtime(time.time()))

        return status, row


def initialise_temp_batch(paint_directory, column_names):
    temp_batch_file_name = os.path.join(paint_directory, "temp_batch.csv")
    try:
        temp_batch_file = open(temp_batch_file_name, fiji_get_file_open_write_attribute())
        temp_batch_writer = csv.DictWriter(temp_batch_file, column_names)
        temp_batch_writer.writeheader()
        temp_batch_file.close()
        return temp_batch_file_name
    except IOError:
        paint_logger.error("Could not open results file:" + temp_batch_file_name)
        sys.exit(-1)


def write_row_to_temp_batch(row, temp_batch_file_name, column_names):
    try:
        temp_batch_file = open(temp_batch_file_name, fiji_get_file_open_append_attribute())
        temp_batch_writer = csv.DictWriter(temp_batch_file, column_names)
        temp_batch_writer.writerow(row)
        temp_batch_file.close()
    except IOError:
        exit()

if __name__ == "__main__":

    paint_directory = ask_user_for_image_directory("Specify the Paint directory", 'Paint')
    if len(paint_directory) == 0:
        paint_logger.warning("\nUser aborted the batch processing.")
        exit(0)

    # Get the directory where the images are located
    images_directory = ask_user_for_image_directory("Specify the Image Source directory", 'Images')
    if len(images_directory) == 0:
        paint_logger.warning("\nUser aborted the batch processing.")
        exit(0)

    time_stamp = time.time()
    grid_analysis_batch(paint_directory, images_directory)
    run_time = time.time() - time_stamp
    run_time = round(run_time, 1)
    paint_logger.info("\nProcessing completed in " + str(run_time) + " seconds")
