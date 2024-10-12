import json
import os
import sys
import time

from pandas.io.formats.info import INFO_DOCSTRING

from src.Automation.Grid.Compile_Results_Files import compile_squares_file
from src.Automation.Grid.Generate_Squares_Single import process_images_in_root_directory_single_mode
from src.Automation.Grid.Generate_Squares_Traditional import process_images_in_root_directory_traditional_mode
from src.Automation.Support.Copy_Data_From_Source import copy_data_from_paint_source_to_paint_data
from src.Automation.Support.Set_Directory_Tree_Timestamp import set_directory_tree_timestamp, get_timestamp_from_string
from src.Automation.Support.Support_Functions import copy_directory, format_time_nicely
from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_console_handle_set_level
)

import logging

paint_logger_change_file_handler_name('Process All.log')
paint_logger_console_handle_set_level(logging.DEBUG)

PAINT_DEBUG = True

if PAINT_DEBUG:
    CONF_FILE = '/Users/hans/Paint Source/paint data generation - test.json'
    PAINT_SOURCE = '/Users/hans/Paint Source'
    PAINT_DATA = '/Users/Hans/Paint Data Test'
    R_DATA_DEST = '/Users/hans/R Data'
    R_DATA_DEST = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/Python and R Code/Paint-R/Data New'
    TIME_STAMP = '2024-10-11 11:11:11'  # '%Y-%m-%d %H:%M:%S

else:
    CONF_FILE = '/Users/hans/Paint Source/paint data generation - production.json'
    PAINT_SOURCE = '/Users/hans/Paint Source'
    PAINT_DATA = '/Users/Hans/Paint Data'
    R_DATA_DEST = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/Python and R Code/Paint-R/Data New'
    TIME_STAMP = '2024-10-11 00:00:00'  # '%Y-%m-%d %H:%M:%S


def run_single(root_dir: str, nr_of_squares: int) -> None:
    try:
        process_images_in_root_directory_single_mode(
            root_dir,
            nr_of_squares_in_row=nr_of_squares,
            min_r_squared=0.9,
            min_tracks_for_tau=20,
            max_variability=10,
            max_square_coverage=100,
            verbose=False
        )
    except Exception as e:
        paint_logger.error(f"Failed to run single mode for {root_dir}. Error: {e}")


def run_traditional(root_dir: str,
                    nr_of_squares: int,
                    min_density_ratio: float) -> None:
    try:
        process_images_in_root_directory_traditional_mode(
            root_dir,
            nr_of_squares_in_row=nr_of_squares,
            min_r_squared=0.9,
            min_tracks_for_tau=20,
            min_density_ratio=min_density_ratio,
            max_variability=10,
            max_square_coverage=100,
            verbose=False
        )
    except Exception as e:
        paint_logger.error(f"Failed to run traditional mode for {root_dir}. Error: {e}")


def process_directory(paint_source_dir,
                      process_directory: str,
                      paint_data_dir: str,
                      r_dest_dir: str,
                      mode: str,
                      probe: str,
                      nr_of_squares: int,
                      nr_to_process: int,
                      current_process: int,
                      min_density_ratio: float = None) -> bool:
    time_stamp = time.time()
    msg = f"{current_process} of {nr_to_process} --- Processing mode: {mode} - Probe: {probe} - Directory: {process_directory}"
    paint_logger.info("")
    paint_logger.info("")
    paint_logger.info("-" * len(msg))
    paint_logger.info(msg)
    paint_logger.info("-" * len(msg))
    paint_logger.info("")

    # Check if the Paint Source directory exists
    if not os.path.exists(paint_source_dir):
        paint_logger.error(f"Paint Source directory {paint_source_dir} does not exist.")
        return False

    # Check if the Paint Data directory exists
    if not os.path.exists(paint_data_dir):
        paint_logger.error(f"Paint Data directory {paint_data_dir} does not exist.")
        return False

    # Copy the data from Paint Source to the appropriate directory in Paint Data
    if not copy_data_from_paint_source_to_paint_data(paint_source_dir, paint_data_dir):
        return False

    if not os.path.exists(r_dest_dir):
        os.makedirs(r_dest_dir)

    # Do the grid processing
    if mode == 'Single':
        run_single(paint_data_dir, nr_of_squares)
    elif mode == 'Traditional':
        run_traditional(paint_data_dir, nr_of_squares, min_density_ratio)
    else:
        paint_logger.error(f"Invalid mode '{mode}' for {process_directory}.")
        return False

    # Compile the squares file
    compile_squares_file(paint_data_dir, verbose=True)

    # Now copy the data from the Paint Data directory to the R space (OK, to use a general copy routine)
    output_source = os.path.join(paint_data_dir, 'Output')
    output_destination = os.path.join(r_dest_dir, 'Output')
    copy_directory(output_source, output_destination)
    paint_logger.info(f"Copied output to {output_destination}")

    # Set the timestamp for the R data destination directory
    specific_time = get_timestamp_from_string(TIME_STAMP)
    if specific_time:
        set_directory_tree_timestamp(r_dest_dir, specific_time)
    else:
        paint_logger.error(f"Time string '{TIME_STAMP}' is not a valid date string.")

    paint_logger.info("")
    paint_logger.info(
        f"Processed Mode: {mode} - Probe: {probe} - Directory: {process_directory} in {format_time_nicely(time.time() - time_stamp)} seconds")
    return True

def main():

    # paint_logger_change_file_handler_name('Process All.log')

    # Load the configuration file
    try:
        with open(CONF_FILE, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        paint_logger.error(f"The configuration file {CONF_FILE} was not found.")
        config = []
        sys.exit(1)
    except json.JSONDecodeError:
        paint_logger.error(f"Failed to decode JSON from the configuration file {CONF_FILE}.")
        config = []
        sys.exit(1)

    # Main loop to process each configuration based on flags

    nr_to_process = sum(1 for entry in config if entry['flag'])
    main_stamp = time.time()

    paint_logger.info("")
    paint_logger.info("")
    paint_logger.info(f"New Run - {'Debug' if PAINT_DEBUG else 'Production'} mode")
    paint_logger.info("")
    paint_logger.info(f'The configuration file is: {CONF_FILE}')
    paint_logger.info(f'The Paint Source directory is: {PAINT_SOURCE}')
    paint_logger.info(f'The Paint Data directory is: {PAINT_DATA}')
    paint_logger.info(f'The R Output directory is: {R_DATA_DEST}')
    paint_logger.info(f'The number of directories to process is: {nr_to_process}')

    nr_to_process = sum(1 for entry in config if entry['flag'])

    current_process_seq_nr = 0
    error_count = 0
    for entry in config:
        if entry['flag']:
            paint_source_dir = os.path.join(PAINT_SOURCE, entry['probe'])
            paint_data_dir = os.path.join(PAINT_DATA, entry['probe'], entry['mode'], entry['directory'])
            r_dest_dir = os.path.join(R_DATA_DEST, entry['directory'])
            current_process_seq_nr += 1
            if not process_directory(
                    paint_source_dir=paint_source_dir,
                    process_directory=entry['directory'],
                    paint_data_dir=paint_data_dir,
                    r_dest_dir=r_dest_dir,
                    mode=entry['mode'],
                    probe=entry['probe'],
                    nr_of_squares=entry['nr_of_squares'],
                    nr_to_process=nr_to_process,
                    current_process=current_process_seq_nr,
                    min_density_ratio=entry.get('min_density_ratio')):
                error_count += 1

    # Report the time it took in hours minutes seconds
    run_time = time.time() - main_stamp
    format_time_nicely(run_time)

    paint_logger.info("")
    paint_logger.info(f"Finished the whole process in:  {format_time_nicely(run_time)}")
    paint_logger.info("")

    if error_count > 0:
        paint_logger.error('-' * 80)
        paint_logger.error('-' * 80)
        paint_logger.error(f"Errors occurred in {error_count} of {nr_to_process} directories.")
        paint_logger.error('-' * 80)
        paint_logger.error('-' * 80)

if __name__ == '__main__':
    main()
