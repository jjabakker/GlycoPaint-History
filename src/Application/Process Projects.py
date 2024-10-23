import json
import os
import sys
import time

from src.Application.Compile_Project_Output.Compile_Project_Output import compile_project_output
from src.Application.Process_Projects.Utilities.Copy_Data_From_Paint_Source import copy_data_from_paint_source_to_paint_data
from src.Application.Generate_Squares.Generate_Squares import process_all_images_in_root_directory
from src.Application.Utilities.Set_Directory_Tree_Timestamp import set_directory_tree_timestamp, get_timestamp_from_string
from src.Application.Utilities.General_Support_Functions import copy_directory, format_time_nicely
from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_console_handle_set_level,
    DEBUG as PAINT_DEBUG
)

paint_logger_change_file_handler_name('Process All Projects.log')
paint_logger_console_handle_set_level(PAINT_DEBUG)

PAINT_DEBUG = False
PAINT_FORCE = True

if PAINT_DEBUG:
    CONF_FILE = '/Users/hans/Paint Source/Generation Files/paint data generation.json'
    PAINT_SOURCE = '/Users/hans/Paint Source'
    PAINT_DATA = '/Users/Hans/Paint Data'
    R_DATA_DEST = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/Python and R Code/Paint-R/Data - v2'
    TIME_STAMP = '2024-10-11 00:00:00'  # '%Y-%m-%d %H:%M:%S

else:
    CONF_FILE = '/Users/hans/Paint Source/Generation Files/paint data generation.json'
    PAINT_SOURCE = '/Users/hans/Paint Source'
    PAINT_DATA = '/Users/Hans/Paint Data - v4'
    R_DATA_DEST = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/Python and R Code/Paint-R/Data - v4'
    TIME_STAMP = '2024-10-11 00:00:00'  # '%Y-%m-%d %H:%M:%S


def process_directory(paint_source_dir,
                      process_directory: str,
                      paint_data_dir: str,
                      r_dest_dir: str,
                      probe: str,
                      nr_of_squares: int,
                      nr_to_process: int,
                      current_process: int,
                      min_density_ratio: float,
                      min_r_squared: float,
                      min_tracks_for_tau: int,
                      max_variability: float,
                      max_square_coverage: float,
                      process_single: bool,
                      process_traditional: bool,
                      paint_force: bool) -> bool:
    time_stamp = time.time()
    msg = f"{current_process} of {nr_to_process} - Processing {process_directory}"
    paint_logger.info("")
    paint_logger.info("")
    paint_logger.info("-" * 40)
    paint_logger.info(msg)
    paint_logger.info("")
    paint_logger.info(f"Probe Series                : {probe}")
    paint_logger.info(f"Traditional mode            : {process_traditional}")
    paint_logger.info(f"Single                      : {process_single}")
    paint_logger.info(f"Number of squares           : {nr_of_squares}")
    paint_logger.info(f"Min Required Density Ratio  : {min_density_ratio}")
    paint_logger.info(f"Min R squared               : {min_r_squared}")
    paint_logger.info(f"Min tracks for tau          : {min_tracks_for_tau}")
    paint_logger.info(f"Max Allowable Variability   : {max_variability}")
    paint_logger.info(f"Max square coverage         : {max_square_coverage}")
    paint_logger.info(f"Paint Force                 : {paint_force}")

    paint_logger.info("")
    paint_logger.info("-" * 40)
    paint_logger.info("")

    # Check if the Paint Source directory exists
    if not os.path.exists(paint_source_dir):
        paint_logger.error(f"Paint Source directory {paint_source_dir} does not exist.")
        return False

    # Check if the Paint Data directory exists
    if not os.path.exists(paint_data_dir):
        paint_logger.info(f"Paint Data directory {paint_data_dir} does not exist, directory created.")
        os.makedirs(paint_data_dir)

    # Do the grid processing if the output files do not exist
    output_dir = os.path.join(paint_data_dir, 'Output')
    if (os.path.isfile(os.path.join(output_dir, 'All Squares.csv')) or
        os.path.isfile(os.path.join(output_dir, 'All Images.csv')) or
        os.path.isfile(os.path.join(output_dir, 'Image Summary.csv'))) and not paint_force:
        paint_logger.info("Output files exist, skipping grid processing.")
        return True

    # Copy the data from Paint Source to the appropriate directory in Paint Data
    if not copy_data_from_paint_source_to_paint_data(paint_source_dir, paint_data_dir):
        return False

    if not os.path.exists(r_dest_dir):
        os.makedirs(r_dest_dir)

    process_all_images_in_root_directory(
        paint_data_dir,
        nr_of_squares_in_row=nr_of_squares,
        min_r_squared=min_r_squared,
        min_tracks_for_tau=min_tracks_for_tau,
        min_density_ratio=min_density_ratio,
        max_variability=max_variability,
        max_square_coverage=max_square_coverage,
        process_single=process_single,
        process_traditional=process_traditional,
        verbose=False)

    # Compile the squares file
    compile_project_output(paint_data_dir, verbose=True)

    # Now copy the data from the Paint Data directory to the R space (OK, to use a general copy routine)
    output_source = os.path.join(paint_data_dir, 'Output')
    output_destination = os.path.join(r_dest_dir, 'Output')
    if not os.path.exists(output_destination):
        os.makedirs(output_destination)
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
        f"Processed Mode: Probe: {probe} - Directory: {process_directory} in {format_time_nicely(time.time() - time_stamp)} seconds")
    return True


def main():
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
            paint_data_dir = os.path.join(PAINT_DATA, entry['probe'], entry['directory'])
            r_dest_dir = os.path.join(R_DATA_DEST, entry['directory'])
            current_process_seq_nr += 1
            if not process_directory(
                    paint_source_dir=paint_source_dir,
                    process_directory=entry['directory'],
                    paint_data_dir=paint_data_dir,
                    r_dest_dir=r_dest_dir,
                    probe=entry['probe'],
                    nr_of_squares=entry['nr_of_squares'],
                    nr_to_process=nr_to_process,
                    current_process=current_process_seq_nr,
                    min_density_ratio=entry['min_density_ratio'],
                    min_r_squared=entry['min_r_squared'],
                    min_tracks_for_tau=entry['min_tracks_for_tau'],
                    max_variability=entry['max_variability'],
                    max_square_coverage=entry['max_square_coverage'],
                    process_single=entry['process_single'],
                    process_traditional=entry['process_traditional'],
                    paint_force=PAINT_FORCE):
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
