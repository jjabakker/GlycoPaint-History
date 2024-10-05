import os
import shutil
import time

from src.Automation.Grid.Generate_Squares_Single import process_images_in_root_directory_single_mode

from src.Automation.Grid.Generate_Squares_Traditional import process_images_in_root_directory_traditional_mode

from src.Automation.Grid.Compile_Results_Files import compile_squares_file
from src.Automation.Support.Copy_Data_From_Source import copy_data_from_source
from src.Automation.Support.Directory_Timestamp import set_directory_timestamp
from src.Automation.Support.Logger_Config import logger
from src.Automation.Support.Support_Functions import format_time_nicely

SOURCE_NEW_DIR     = '/Users/hans/Paint Source/New Probes'
SOURCE_REGULAR_DIR = '/Users/hans/Paint Source/Regular Probes'

paint_source_dirs = {
    'new':      SOURCE_NEW_DIR,
    'regular':  SOURCE_REGULAR_DIR
}

logger.debug("\n\n\n\nNew Run\n\n\n")


def copy_directory(src, dest):
    try:
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        logger.debug(f"Copied {src} to {dest}")
    except Exception as e:
        logger.error(f"process_all_chatgtp - copy directories: Failed to copy {src} to {dest}. Error: {e}")


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
        logger.error(f"Failed to run single mode for {root_dir}. Error: {e}")


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
        logger.error(f"Failed to run traditional mode for {root_dir}. Error: {e}")


def process_directory(directory, root_dir, dest_dir, mode, probe, nr_of_squares, min_density_ratio=None):

    time_stamp = time.time()
    msg = f"Processing mode: {mode} - probe {probe} - directory: {directory}"
    logger.info("")
    logger.info("")
    logger.info("-" * len(msg))
    logger.info(f"Processing mode: {mode} - probe {probe} - directory: {directory}")
    logger.info("-" * len(msg))
    logger.info("")
    copy_data_from_source(paint_source_dirs[probe], root_dir)

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    if mode == 'single':

        run_single(root_dir, nr_of_squares)
    elif mode == 'traditional':
        run_traditional(root_dir, nr_of_squares, min_density_ratio)

    compile_squares_file(root_dir, verbose=True)
    copy_directory(os.path.join(root_dir, 'Output'), os.path.join(dest_dir, 'Output'))
    logger.info(f"Copied output to {os.path.join(dest_dir, 'Output')}")
    set_directory_timestamp(root_dir)
    set_directory_timestamp(dest_dir)
    logger.info(f"Processed mode: {mode} - probe {probe} - directory: {directory} in {format_time_nicely(time.time() - time_stamp)} seconds")


# Define the configuration for different processing modes
config = [
    # Single modes
    {'flag': True,
     'mode': 'single',
     'probe': 'new',
     'directory': 'Paint New Probes - Single - 30 Squares - 10 DR',
     'source_dir': '/Users/hans/Paint Data/New Probes/Single/',
     'nr_of_squares': 30},

    {'flag': True,
     'mode': 'single',
     'probe': 'new',
     'directory': 'Paint New Probes - Single - 30 Squares - 30 DR',
     'source_dir': '/Users/hans/Paint Data/New Probes/Single/',
     'nr_of_squares': 30},

    {'flag': True,
     'mode': 'single',
     'probe': 'new',
     'directory': 'Paint New Probes - Single - 30 Squares - 5 DR',
     'source_dir': '/Users/hans/Paint Data/New Probes/Single/',
     'nr_of_squares': 30},

    {'flag': True,
     'mode': 'single',
     'probe': 'regular',
     'directory': 'Paint Regular Probes - Single - 30 Squares - 10 DR',
     'source_dir': '/Users/hans/Paint Data/Regular Probes/Single/',
     'nr_of_squares': 30},

    {'flag': True,
     'mode': 'single',
     'probe': 'regular',
     'directory': 'Paint Regular Probes - Single - 30 Squares - 30 DR',
     'source_dir': '/Users/hans/Paint Data/Regular Probes/Single/',
     'nr_of_squares': 30},

    # Traditional modes
    {'flag': True,
     'mode': 'traditional',
     'probe': 'new',
     'directory': 'Paint New Probes - Traditional - 20 Squares - 2 DR',
     'source_dir': '/Users/hans/Paint Data/New Probes/Traditional/',
     'nr_of_squares': 20,
     'min_density_ratio': 2},

    {'flag': True,
     'mode': 'traditional',
     'probe': 'new',
     'directory': 'Paint New Probes - Traditional - 30 Squares - 2 DR',
     'source_dir': '/Users/hans/Paint Data/New Probes/Traditional/',
     'nr_of_squares': 30,
     'min_density_ratio': 2},

    {'flag': True,
     'mode': 'traditional',
     'probe': 'regular',
     'directory': 'Paint Regular Probes - Traditional - 20 Squares - 2 DR',
     'source_dir': '/Users/hans/Paint Data/Regular Probes/Traditional/',
     'nr_of_squares': 20,
     'min_density_ratio': 2}
]

# Destination directory
root_dest_dir = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/Code/Paint-R/Data/'

# Main loop to process each configuration based on flags

main_stamp = time.time()

logger.info("")
logger.info('Starting the full processing')
logger.info("")

for entry in config:
    if entry['flag']:
        root_dir = os.path.join(entry['source_dir'], entry['directory'])
        dest_dir = os.path.join(root_dest_dir, entry['directory'])
        process_directory(
            directory=entry['directory'],
            root_dir=root_dir,
            dest_dir=dest_dir,
            mode=entry['mode'],
            probe=entry['probe'],
            nr_of_squares=entry['nr_of_squares'],
            min_density_ratio=entry.get('min_density_ratio')
        )

# Report the time it took in hours minutes seconds
run_time = time.time() - main_stamp
format_time_nicely(run_time)

logger.info("")
logger.info(f'Finished the full processing in  {format_time_nicely(run_time)}')
logger.info("")

