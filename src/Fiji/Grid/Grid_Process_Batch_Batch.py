import csv
import os
import sys
import time

from java.lang.System import getProperty

paint_dir = os.path.join(getProperty('fiji.dir'), "scripts", "Plugins", "Paint")
sys.path.append(paint_dir)

paint_dir = os.path.join(getProperty('fiji.dir'), "scripts", "Plugins", "Paint", "Grid")
sys.path.append(paint_dir)

from FijiSupportFunctions import (
    ask_user_for_file,
    format_time_nicely)
from Grid_Process_Batch import grid_analysis_batch

from LoggerConfigFiji import logger, change_file_handler

change_file_handler('Grid Process Batch Batch.log')

if __name__ == "__main__":

    batch_file_name = ask_user_for_file("Specify the batch file")
    if not batch_file_name:
        logger.info("User aborted the batch processing.")
        sys.exit(0)

    try:
        batch_file = open(batch_file_name, 'rt')
        csv_reader = csv.reader(batch_file)
        for batch_column_names in csv_reader:  # Read the first row into batch_column_names and then stop
            break
        batch_file.close()
    except IOError:
        logger.error("Could not open batch file:" + batch_file_name)
        sys.exit(-1)

    try:
        batch_file = open(batch_file_name, 'rt')
        csv_reader = csv.DictReader(batch_file)
    except IOError:
        logger.errro("Could not open batch file:" + batch_file_name)
        sys.exit(-1)

    time_stamp = time.time()
    for row in csv_reader:
        if 'y' in row['Process'].lower():
            grid_analysis_batch(paint_directory=os.path.join(row['Source'], row['Image']),
                                image_source_directory=os.path.join(row['Destination'], row['Image']))

    run_time = round(time.time() - time_stamp, 1)
    logger.info("Processing completed in {} seconds".format(format_time_nicely(run_time)))
