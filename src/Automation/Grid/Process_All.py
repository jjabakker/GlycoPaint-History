import os
import sys
import shutil
import time
import json

from src.Automation.Grid.Compile_Results_Files import compile_squares_file
from src.Automation.Grid.Generate_Squares_Single import process_images_in_root_directory_single_mode
from src.Automation.Grid.Generate_Squares_Traditional import process_images_in_root_directory_traditional_mode
from src.Automation.Support.Copy_Data_From_Source import copy_data_from_paint_source_to_paint_data
from src.Automation.Support.Directory_Timestamp import set_directory_timestamp
from src.Common.Support.LoggerConfig import paint_logger, change_file_handler
from src.Automation.Support.Support_Functions import format_time_nicely

SOURCE_NEW_DIR     = '/Users/hans/Paint Source/New Probes'
SOURCE_REGULAR_DIR = '/Users/hans/Paint Source/Regular Probes'
ROOT_DEST_DIR      = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/Code/Paint-R/Data/'
CONF_FILE          = '/Users/hans/Paint Source/paint data generation.json'




def copy_directory(src, dest):
    try:
        shutil.rmtree(dest, ignore_errors=True)
        shutil.copytree(src, dest)
        paint_logger.debug(f"Copied {src} to {dest}")
    except Exception as e:
        paint_logger.error(f"process_all - copy directories: Failed to copy {src} to {dest}. Error: {e}")


def run_single(root_dir, nr_of_squares):
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


def run_traditional(root_dir, nr_of_squares, min_density_ratio):
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


def process_directory(directory, root_dir, dest_dir, mode, probe, nr_of_squares, nr_to_process, current_process,
                      min_density_ratio=None):
    time_stamp = time.time()
    msg = f"{current_process} of {nr_to_process} --- Processing mode: {mode} - Probe: {probe} - Directory: {directory}"
    paint_logger.info("")
    paint_logger.info("")
    paint_logger.info("-" * len(msg))
    paint_logger.info(msg)
    paint_logger.info("-" * len(msg))
    paint_logger.info("")

    if not copy_data_from_paint_source_to_paint_data(paint_source_dirs[probe], root_dir):
        return

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    if mode == 'single':
        run_single(root_dir, nr_of_squares)
    elif mode == 'traditional':
        run_traditional(root_dir, nr_of_squares, min_density_ratio)

    compile_squares_file(root_dir, verbose=True)
    copy_directory(os.path.join(root_dir, 'Output'), os.path.join(dest_dir, 'Output'))
    paint_logger.info(f"Copied output to {os.path.join(dest_dir, 'Output')}")
    set_directory_timestamp(root_dir)
    set_directory_timestamp(dest_dir)
    paint_logger.info(
        f"Processed Mode: {mode} - Probe: {probe} - Directory: {directory} in {format_time_nicely(time.time() - time_stamp)} seconds")


def main():

    change_file_handler('Process All.log')

    paint_source_dirs = {
        'new': SOURCE_NEW_DIR,
        'regular': SOURCE_REGULAR_DIR
    }

    paint_logger.debug("\n\n\n\nNew Run\n\n\n")

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

    main_stamp = time.time()

    paint_logger.info("")
    paint_logger.info('Starting the full processing')
    paint_logger.info("")

    nr_to_process = sum(1 for entry in config if entry['flag'])

    current_process = 0
    for entry in config:
        if entry['flag']:
            root_dir = os.path.join(entry['source_dir'], entry['directory'])
            dest_dir = os.path.join(ROOT_DEST_DIR, entry['directory'])
            current_process += 1
            process_directory(
                directory=entry['directory'],
                root_dir=root_dir,
                dest_dir=dest_dir,
                mode=entry['mode'],
                probe=entry['probe'],
                nr_of_squares=entry['nr_of_squares'],
                nr_to_process=nr_to_process,
                current_process=current_process,
                min_density_ratio=entry.get('min_density_ratio')  # If the key does not exist, it returns ''
            )

    # Report the time it took in hours minutes seconds
    run_time = time.time() - main_stamp
    format_time_nicely(run_time)

    paint_logger.info("")
    paint_logger.info(f'Finished the full processing in  {format_time_nicely(run_time)}')
    paint_logger.info("")


if __name__ == '__main__':
    main()
