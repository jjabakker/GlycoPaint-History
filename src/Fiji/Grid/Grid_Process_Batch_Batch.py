import csv
import os
import sys
import time

from java.lang.System import getProperty

# This is necessary to import the FijiSupport and LoggerConfig module
paint_dir = os.path.join(getProperty('fiji.dir'), "scripts", "Plugins", "Paint")
sys.path.append(paint_dir)
from LoggerConfig import paint_logger, change_file_handler
from FijiSupportFunctions import (
    ask_user_for_file,
    format_time_nicely)

# This is necessary to import the Grid_Process_Batch module
paint_dir = os.path.join(getProperty('fiji.dir'), "scripts", "Plugins", "Paint", "Grid")
sys.path.append(paint_dir)
from Grid_Process_Batch import grid_analysis_batch

# Set an appropriate name for the log file
change_file_handler('Grid Process Batch Batch.log')

if __name__ == "__main__":

    batch_file_name = ask_user_for_file("Specify the batch file")
    if not batch_file_name:
        paint_logger.info("User aborted the batch processing.")
        sys.exit(0)

    try:
        # Use `with` to open the file and ensure it is closed after reading
        with open(batch_file_name, mode='r') as file:
            # Create a DictReader object
            csv_reader = csv.DictReader(file)

            # Check if the required columns are present
            required_columns = ['Source', 'Destination', 'Process']
            if not all(col in csv_reader.fieldnames for col in required_columns):
                paint_logger.error("Error: Missing one or more required columns: {}".format(required_columns))
                sys.exit()

            # Read and print each row
            time_stamp = time.time()
            for row in csv_reader:
                if 'y' in row['Process'].lower():
                    message = "Processing image '{}'".format(row['Image'])
                    paint_logger.info("")
                    paint_logger.info("-" * len(message))
                    paint_logger.info(message)
                    paint_logger.info("-" * len(message))
                    grid_analysis_batch(paint_directory=os.path.join(row['Source'], row['Image']),
                                        image_source_directory=os.path.join(row['Destination'], row['Image']))
                    paint_logger.info("")
                    paint_logger.info("")
            run_time = round(time.time() - time_stamp, 1)
            paint_logger.info("Processing completed in {} seconds".format(format_time_nicely(run_time)))

    except csv.Error as e:
        paint_logger.error("grid_process_batc_batch: Error reading CSV file: {}".format(e))
    except Exception as e:
        paint_logger.error("grid_process_batc_batch: An unexpected error occurred: {}".format(e))







