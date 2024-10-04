import csv
import os
import sys
import time
import logging
from ij import IJ
from java.lang.System import getProperty


paint_dir = getProperty('fiji.dir') + os.sep + "scripts" + os.sep + "Plugins" + os.sep + "Paint"
sys.path.append(paint_dir)

from Trackmate import paint_trackmate
from CommonSupportFunctions import create_directories
from FijiSupportFunctions import fiji_get_file_open_write_attribute
from FijiSupportFunctions import fiji_get_file_open_append_attribute
from FijiSupportFunctions import ask_user_for_image_directory
from LoggerConfigFiji import logger, change_file_handler

# Configure logging
change_file_handler('Grid Process Batch.log')

def grid_analysis_batch(paint_directory, image_source_directory):
    """
    Batch process images based on a CSV configuration file.

    Args:
        paint_directory (str): Directory containing the Paint configuration and output files.
        image_source_directory (str): Directory containing the source images to be processed.
    """
    # Clear the log file (if needed) - In this case, we will log to a file as well
    logger.info("Starting grid analysis batch processing.")

    batch_file_name      = os.path.join(paint_directory, "batch.csv")
    temp_batch_file_name = os.path.join(paint_directory, "temp_batch.csv")

    # Load batch file to determine columns
    try:
        with open(batch_file_name, 'rt') as batch_file:
            batch_column_names = next(csv.reader(batch_file))  # Read the first row for column names
    except IOError:
        logger.error("Could not open batch file: %s", batch_file_name)
        sys.exit(-1)

    # Prepare to write results to a temporary CSV
    try:
        with open(temp_batch_file_name, fiji_get_file_open_write_attribute()) as temp_batch_file:
            temp_batch_writer = csv.DictWriter(temp_batch_file, batch_column_names)
            temp_batch_writer.writeheader()
    except IOError:
        logger.error("Could not open results file: %s", temp_batch_file_name)
        sys.exit(-1)

    # Count images to process
    nr_to_process = sum(1 for row in csv.DictReader(open(batch_file_name)) if 'Y' in row.get('Process', '').upper())
    if nr_to_process == 0:
        logger.info("No images selected for processing.")
        return -1

    logger.info("Number of images to process: %d", nr_to_process)

    # Cycle through images and process where requested
    logger.info("Processing %d images in directory: %s", nr_to_process, image_source_directory)

    nr_images_processed = 0
    nr_images_failed    = 0
    nr_images_not_found = 0

    with open(batch_file_name, 'rt') as batch_file:
        csv_reader = csv.DictReader(batch_file)
        for file_count, row in enumerate(csv_reader, start=1):
            if 'Y' in row.get('Process', '').upper():
                image_file_name = os.path.join(image_source_directory, row['Image Name'] + '.nd2')

                if not os.path.exists(image_file_name):
                    logger.warning("Failed to open image: %s", image_file_name)
                    row['Image Size'] = '-'
                    nr_images_not_found += 1
                else:
                    row['Image Size'] = os.path.getsize(image_file_name)
                    imp = IJ.openImage(image_file_name)
                    imp.show()
                    IJ.run("Enhance Contrast", "saturated=0.35")
                    IJ.run("Grays")

                    ext_image_name = "{}-threshold-{}".format(row['Image Name'], int(row['Threshold']))
                    create_directories(os.path.join(paint_directory, ext_image_name), True)

                    logger.info("Processing file nr %d: %s", file_count, ext_image_name)
                    time_stamp = time.time()
                    tracks_filename = os.path.join(paint_directory, ext_image_name, "tracks",
                                                   "{}-full-tracks.csv".format(ext_image_name))
                    tiff_filename = os.path.join(paint_directory, ext_image_name, "img",
                                                 "{}.tiff".format(ext_image_name))

                    nr_spots, total_tracks, long_tracks = paint_trackmate(float(row['Threshold']),
                                                                          tracks_filename,
                                                                          tiff_filename)
                    if nr_spots == -1:
                        logger.error("'paint_trackmate' did not manage to run.")
                        nr_images_failed += 1
                    else:
                        run_time = round(time.time() - time_stamp, 1)
                        logger.info("Processed %d spots in %.1f seconds", nr_spots, run_time)
                        row.update({
                            'Nr Spots': nr_spots,
                            'Nr Tracks': long_tracks,
                            'Run Time': run_time,
                            'Ext Image Name': ext_image_name,
                            'Time Stamp': time.asctime(time.localtime(time.time()))
                        })
                        nr_images_processed += 1
                    imp.close()

                # Write the updated row to the temporary file
                with open(temp_batch_file_name, fiji_get_file_open_append_attribute()) as temp_batch_file:
                    temp_batch_writer = csv.DictWriter(temp_batch_file, batch_column_names)
                    temp_batch_writer.writerow(row)

    logger.info("Number of images processed successfully: %d", nr_images_processed)
    logger.info("Number of images not found: %d", nr_images_not_found)
    logger.info("Number of images failed: %d", nr_images_failed)

    # Rename files as needed
    old_batch_file_name = os.path.join(paint_directory, "previous_batch.csv")
    if os.path.isfile(old_batch_file_name):
        os.remove(old_batch_file_name)
    os.rename(batch_file_name, old_batch_file_name)

    os.remove(batch_file_name)
    os.rename(temp_batch_file_name, batch_file_name)

    return 0


if __name__ == "__main__":
    paint_directory = ask_user_for_image_directory("Specify the Paint directory", 'Paint')
    if not paint_directory:
        logger.info("User aborted the batch processing.")
        sys.exit(0)

    images_directory = ask_user_for_image_directory("Specify the Image Source directory", 'Images')
    if not images_directory:
        logger.info("User aborted the batch processing.")
        sys.exit(0)

    start_time = time.time()
    grid_analysis_batch(paint_directory, images_directory)
    elapsed_time = round(time.time() - start_time, 1)
    logger.info("Processing completed in %.1f seconds", elapsed_time)