import csv
import os
import sys
import time

from ij import IJ
from java.lang.System import getProperty

paint_dir = os.path.join(getProperty('fiji.dir'), "scripts", "Plugins",  "Paint")
sys.path.append(paint_dir)

from Trackmate import paint_trackmate
from CommonSupportFunctions import create_directories
from FijiSupportFunctions import fiji_get_file_open_write_attribute
from FijiSupportFunctions import fiji_get_file_open_append_attribute
from FijiSupportFunctions import fiji_log
from FijiSupportFunctions import fiji_header
from FijiSupportFunctions import ask_user_for_file


def grid_analysis_batch(paint_directory, image_source_directory):

    # Clear the log file
    # fiji_log("", True)

    # -----------------------------------------------------------------------------
    # Open the batch file to determine the columns (which should be in the paint directory)
    # -----------------------------------------------------------------------------

    batch_file_name     = os.path.join(paint_directory, "batch.csv")
    old_batch_file_name = os.path.join(paint_directory, "previous_batch.csv")

    try:
        batch_file = open(batch_file_name, 'rt')
        csv_reader = csv.reader(batch_file)
        for batch_column_names in csv_reader:     # Read the first row into batch_column_names and then stop
            break
        batch_file.close()
    except IOError:
        fiji_log("Could not open batch file:" + batch_file_name)
        print("Could not open batch file:" + batch_file_name)
        exit(-1)

    # -----------------------------------------------------------------------------
    # Then open the batch file for processing
    # -----------------------------------------------------------------------------

    try:
        batch_file = open(batch_file_name, 'rt')
        csv_reader = csv.DictReader(batch_file)
    except IOError:
        fiji_log("Could not open batch file:" + batch_file_name)
        print("Could not open batch file:" + batch_file_name)
        exit(-1)

    # -----------------------------------------------------------------------------
    # Open the results file for writing the colum headers only (in the paint directory)
    # -----------------------------------------------------------------------------

    temp_batch_file_name = os.path.join(paint_directory, "temp_batch.csv")
    try:
        temp_batch_file   = open(temp_batch_file_name, fiji_get_file_open_write_attribute())
        temp_batch_writer = csv.DictWriter(temp_batch_file, batch_column_names)
        temp_batch_writer.writeheader()
        temp_batch_file.close()
    except IOError:
        fiji_log("Could not open results file:" + temp_batch_file_name)
        print("Could not open results file:" + temp_batch_file_name)
        exit(-1)

    # ------------------------------------------
    # Count how many images need to be processed
    # ------------------------------------------

    count         = 0
    nr_to_process = 0
    for row in csv_reader:
        if 'Y' in row['Process'] or 'y' in row['Process']:
            nr_to_process += 1
        count += 1

    if nr_to_process == 0:
        fiji_log("\nNo images selected for processing")
        return -1

    print("Number of images processed: " + str(nr_to_process) + " out of a total of " + str(count) + " images in the batch file.")

    # -----------------------------------------------------------------------------
    # Cycle through images and process where requested
    # -----------------------------------------------------------------------------

    message = "Processing " + str(nr_to_process) + " images in directory " + image_source_directory
    fiji_log("\n\n")
    fiji_log("-" * len(message))
    fiji_log("-" * len(message))
    fiji_log(message)
    fiji_log("-" * len(message))
    fiji_log("-" * len(message))

    nr_images_processed = 0
    nr_images_failed    = 0
    nr_images_not_found = 0

    # Start at the beginning for the main processing
    batch_file.seek(0)
    next(csv_reader, None)  # Skip the header

    file_count = 1
    for row in csv_reader:  # Here we are reading the batch file
        try:
            cell_type     = row['Cell Type']
            adjuvant      = row['Adjuvant']
            image_name    = row['Image Name']
            probe         = row['Probe']
            probe_type    = row['Probe Type']
            concentration = float(row['Concentration'])
            threshold     = float(row['Threshold'])
            process       = row['Process']
            image_file    = row['Ext Image Name']

        except Exception:
            print("Error in batch file format")
            exit(-1)

        if adjuvant == 'None':
            row['Adjuvant'] = 'No'

        if 'Y' in process or 'y' in process:
            print(image_file)

            image_file_name = os.path.join(image_source_directory, image_name + '.nd2')

            if not os.path.exists(image_file_name):
                fiji_log("\nProcessing: Failed to open image: " + image_file_name)
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

                fiji_header("Processing file nr " + str(file_count) + " of " + str(nr_to_process) + ": " + ext_image_name)
                time_stamp = time.time()
                tracks_filename = os.path.join(paint_directory, ext_image_name, "tracks",
                                               ext_image_name + "-full-tracks.csv")
                tiff_filename   = os.path.join(paint_directory, ext_image_name, "img", ext_image_name + ".tiff")

                nr_spots, total_tracks, long_tracks = paint_trackmate(threshold, tracks_filename, tiff_filename)
                if nr_spots == -1:
                    fiji_log("\n'Process single image' did not manage to run 'paint_trackmate'")
                    return -1
                else:
                    time.sleep(3)  # Display the image for 3 seconds
                run_time = round(time.time() - time_stamp, 1)

                fiji_log('Nr of spots: ' + str(nr_spots) + " processed in " + str(run_time) + " seconds")
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
        else:
            pass # Do nothing, just write the unchanged row

        # And write the row (changed or not) to the output
        try:
            temp_batch_file   = open(temp_batch_file_name, fiji_get_file_open_append_attribute())
            temp_batch_writer = csv.DictWriter(temp_batch_file, batch_column_names)
            temp_batch_writer.writerow(row)
            temp_batch_file.close()
        except IOError:
            exit()

    temp_batch_file.close()
    batch_file.close()

    fiji_log("\n\n")
    fiji_log("Number of images processed successfully:         " + str(nr_images_processed))
    fiji_log("Number of images not found:                      " + str(nr_images_not_found))
    fiji_log("Number of images not not successfully processed: " + str(nr_images_failed))

    if os.path.isfile(old_batch_file_name):
        os.remove(old_batch_file_name)
    try:
        os.rename(batch_file_name, old_batch_file_name)
    except OSError as e:
        print("Could not rename batch file: " + old_batch_file_name)
        return -1

    if os.path.isfile(batch_file_name):
        os.remove(batch_file_name)
    try:
        os.rename(temp_batch_file_name, batch_file_name)
    except OSError as e:
        print("Could not rename results file: " + temp_batch_file_name)
        return -1

    return 0


if __name__ == "__main__":

    batch_file_name = ask_user_for_file("Specify the batch file")
    if len(batch_file_name) == 0:
        fiji_log("\nUser aborted the batch processing.")
        exit(0)

    try:
        batch_file = open(batch_file_name, 'rt')
        csv_reader = csv.reader(batch_file)
    except IOError:
        fiji_log("Could not open batch file:" + batch_file_name)
        print("Could not open batch file:" + batch_file_name)
        exit(-1)


    # Clear the log file
    fiji_log("", True)

    time_stamp = time.time()
    for row in csv_reader:

        if 'Y' in row[3] or 'y' in row[3]:
            print(row[0])
            print(row[1])
            grid_analysis_batch(os.path.join(row[0], row[2]),
                                os.path.join(row[1], row[2]))


    run_time = time.time() - time_stamp
    run_time = round(run_time, 1)
    fiji_log("\nProcessing completed in " + str(run_time) + " seconds")
