import csv
import os
import sys
import time
from ij import IJ
from java.lang.System import getProperty

paint_dir = os.path.join(getProperty('fiji.dir'), "scripts", "Plugins", "Paint")
sys.path.append(paint_dir)

from Trackmate import paint_trackmate
from CommonSupportFunctions import create_directories
from FijiSupportFunctions import (
    ask_user_for_file,
    fiji_get_file_open_write_attribute,
    fiji_get_file_open_append_attribute,
    format_time_nicely,
    set_directory_timestamp)

from LoggerConfigFiji import logger, change_file_handler

change_file_handler('Grid Process Batch Batch.log')

def grid_analysis_batch(paint_directory, image_source_directory):

    batch_file_name = os.path.join(paint_directory, "batch.csv")
    old_batch_file_name = os.path.join(paint_directory, "previous_batch.csv")

    try:
        with open(batch_file_name, 'rt') as batch_file:
            csv_reader = csv.reader(batch_file)
            for batch_column_names in csv_reader:
                break
    except IOError:
        logger.error("Could not open batch file: {}".format(batch_file_name))
        sys.exit(-1)

    try:
        batch_file = open(batch_file_name, 'rt')
        csv_reader = csv.DictReader(batch_file)
    except IOError:
        logger.error("Could not open batch file: {}".format(batch_file_name))
        sys.exit(-1)

    temp_batch_file_name = os.path.join(paint_directory, "temp_batch.csv")
    try:
        with open(temp_batch_file_name, fiji_get_file_open_write_attribute()) as temp_batch_file:
            temp_batch_writer = csv.DictWriter(temp_batch_file, batch_column_names)
            temp_batch_writer.writeheader()
    except IOError:
        logger.error("Could not open results file: {}".format(temp_batch_file_name))
        sys.exit(-1)

    nr_to_process = sum(1 for row in csv_reader if 'Y' in row['Process'] or 'y' in row['Process'])
    if nr_to_process == 0:
        logger.info("No images selected for processing")
        return -1

    # logger.info("Number of images to be processed: {} out of a total of {} images.".format(nr_to_process, csv_reader.line_num-1))

    main_time = time.time()
    message = "Processing {} images in directory {}".format(nr_to_process, image_source_directory)
    logger.info("\n\n")
    logger.info("-" * len(message))
    logger.info(message)
    logger.info("-" * len(message))

    nr_images_processed = 0
    nr_images_failed    = 0
    nr_images_not_found = 0

    batch_file.seek(0)
    next(csv_reader, None)  # Skip the header

    file_count = 1
    for row in csv_reader:
        try:
            image_name = row['Image Name']
            threshold  = float(row['Threshold'])
            process    = row['Process']
            image_file = row['Ext Image Name']
        except Exception:
            logger.error("Error in batch file format")
            sys.exit(-1)

        if 'Y' in process or 'y' in process:

            image_file_name = os.path.join(image_source_directory, image_name + '.nd2')

            if not os.path.exists(image_file_name):
                logger.error("Failed to open image: {}".format(image_file_name))
                row['Image Size'] = '-'
                nr_images_not_found += 1
            else:
                row['Image Size'] = os.path.getsize(image_file_name)
                imp = IJ.openImage(image_file_name)
                imp.show()
                IJ.run("Enhance Contrast", "saturated=0.35")
                IJ.run("Grays")
                ext_image_name = "{}-threshold-{}".format(image_name, int(threshold))

                create_directories(os.path.join(paint_directory, ext_image_name), True)

                logger.info("Processing file {} of {}: {}".format(file_count, nr_to_process, ext_image_name))
                time_stamp = time.time()
                tracks_filename = os.path.join(paint_directory, ext_image_name, "tracks", "{}-full-tracks.csv".format(ext_image_name))
                tiff_filename = os.path.join(paint_directory, ext_image_name, "img", "{}.tiff".format(ext_image_name))

                nr_spots, total_tracks, long_tracks = paint_trackmate(threshold, tracks_filename, tiff_filename)
                if nr_spots == -1:
                    logger.error("Failed to run 'paint_trackmate'")
                    return -1
                time.sleep(3)
                run_time = round(time.time() - time_stamp, 1)

                logger.info('Nr of spots: {} processed in {} seconds'.format(nr_spots, run_time))
                if nr_spots == -1:
                    nr_images_failed += 1
                else:
                    nr_images_processed += 1
                imp.close()

                # Update the row
                row['Nr Spots']       = nr_spots
                row['Nr Tracks']      = long_tracks
                row['Run Time']       = run_time
                row['Ext Image Name'] = ext_image_name
                row['Time Stamp']     = time.asctime(time.localtime(time.time()))

                file_count += 1

        try:
            with open(temp_batch_file_name, fiji_get_file_open_append_attribute()) as temp_batch_file:
                temp_batch_writer = csv.DictWriter(temp_batch_file, batch_column_names)
                temp_batch_writer.writerow(row)
        except IOError:
            sys.exit()

    logger.info("Number of images processed: {}".format(nr_images_processed))
    logger.info("Number of images not found: {}".format(nr_images_not_found))
    logger.info("Number of images failed: {}".format(nr_images_failed))

    if os.path.isfile(old_batch_file_name):
        os.remove(old_batch_file_name)
    try:
        os.rename(batch_file_name, old_batch_file_name)
    except OSError as e:
        logger.error("Could not rename batch file: {}".format(old_batch_file_name))
        return -1

    if os.path.isfile(batch_file_name):
        os.remove(batch_file_name)
    try:
        os.rename(temp_batch_file_name, batch_file_name)
    except OSError as e:
        logger.error("Could not rename results file: {}".format(temp_batch_file_name))
        return -1

    run_time = time.time() - main_time
    logger.info("Processed {} images in {}".format(nr_images_processed, format_time_nicely(run_time), ))
    return 0


if __name__ == "__main__":

    batch_file_name = ask_user_for_file("Specify the batch file")
    if not batch_file_name:
        logger.info("User aborted the batch processing.")
        sys.exit(0)

    try:
        # Open the batch file without using 'with' to keep it open while reading rows
        batch_file = open(batch_file_name, 'rt')
        csv_reader = csv.reader(batch_file)
    except IOError:
        logger.error("Could not open batch file: {}".format(batch_file_name))
        sys.exit(-1)

    time_stamp = time.time()
    for row in csv_reader:
        if 'Y' in row[3] or 'y' in row[3]:
            grid_analysis_batch(os.path.join(row[0], row[2]), os.path.join(row[1], row[2]))

    run_time = round(time.time() - time_stamp, 1)
    logger.info("Processing completed in {} seconds".format_time_nicely(run_time))