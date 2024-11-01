import json
import os
import sys
import time
import shutil

from datetime import datetime
from src.Application.Compile_Project_Output.Compile_Project_Output import compile_project_output
from src.Application.Process_Projects.Utilities.Copy_Data_From_Paint_Source import copy_data_from_paint_source_to_paint_data
from src.Application.Generate_Squares.Generate_Squares import process_project_directory
from src.Application.Utilities.Set_Directory_Tree_Timestamp import (
    set_directory_tree_timestamp,
    get_timestamp_from_string)
from src.Application.Utilities.General_Support_Functions import (
    copy_directory,
    format_time_nicely
)
from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_console_handle_set_level,
    get_paint_logger_directory,
    DEBUG as PAINT_DEBUG
)

from src.Application.Generate_Squares.Utilities.Create_All_Tracks import create_all_tracks
from src.Application.Generate_Squares.Utilities.Add_DC_to_Squares_Files import add_dc_to_squares_file

paint_logger_change_file_handler_name('Process All Projects.log')
paint_logger_console_handle_set_level(PAINT_DEBUG)

PAINT_FORCE = True

def process_json_configuration_block(paint_source_dir,
                                     project_directory: str,
                                     paint_data_dir: str,
                                     r_dest_dir: str,
                                     probe: str,
                                     nr_of_squares_in_row: int,
                                     nr_to_process: int,
                                     current_process: int,
                                     min_density_ratio: float,
                                     min_r_squared: float,
                                     min_tracks_for_tau: int,
                                     max_variability: float,
                                     max_square_coverage: float,
                                     process_recording_tau: bool,
                                     process_square_tau: bool,
                                     time_string: str,
                                     paint_force: bool,
                                     generate_all_tracks) -> bool:

    time_stamp = time.time()
    msg = f"{current_process} of {nr_to_process} - Processing {project_directory}"
    paint_logger.info("")
    paint_logger.info("")
    paint_logger.info("-" * 40)
    paint_logger.info(msg)
    paint_logger.info("")
    paint_logger.info(f"Probe Series                : {probe}")
    paint_logger.info(f"Process Square Tau          : {process_square_tau}")
    paint_logger.info(f"Process Recording Tau       : {process_recording_tau}")
    paint_logger.info(f"Number of squares           : {nr_of_squares_in_row}")
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

    # Copy the data from Paint Source to the appropriate directory in Paint Data
    if not copy_data_from_paint_source_to_paint_data(paint_source_dir, paint_data_dir):
        return False

    if not os.path.exists(r_dest_dir):
        os.makedirs(r_dest_dir)

    process_project_directory(
        root_directory=paint_data_dir,
        nr_of_squares_in_row=nr_of_squares_in_row,
        min_r_squared=min_r_squared,
        min_tracks_for_tau=min_tracks_for_tau,
        min_density_ratio=min_density_ratio,
        max_variability=max_variability,
        max_square_coverage=max_square_coverage,
        process_recording_tau=process_recording_tau,
        process_square_tau=process_square_tau,
        generate_all_tracks=False,
        verbose=False)

    # Compile the squares file
    compile_project_output(paint_data_dir, verbose=True)

    if generate_all_tracks:
        # Read all tracks files in the directory tree and concatenate them into a single All Tracks
        df_tracks = create_all_tracks(paint_data_dir)
        if df_tracks is None:
            paint_logger.error('All Tracks not generated')
            return

    # Now copy the data from the Paint Data directory to the R space (OK, to use a general copy routine)
    output_source = os.path.join(paint_data_dir, 'Output')
    output_destination = os.path.join(r_dest_dir, 'Output')
    os.makedirs(output_destination, exist_ok=True)
    copy_directory(output_source, output_destination)
    paint_logger.info(f"Copied output to {output_destination}")

    # Set the timestamp for the R data destination directory

    if time_string != '':
        specific_time = get_timestamp_from_string(time_string)
        if specific_time is None:
            paint_logger.error(f"Time string '{time_stamp}' is not a valid date string.")
    else:
        specific_time = None
    set_directory_tree_timestamp(r_dest_dir, specific_time)
    set_directory_tree_timestamp(paint_data_dir, specific_time)

    paint_logger.info("")
    paint_logger.info(
        f"Processed block in {format_time_nicely(time.time() - time_stamp)}")
    return True


def main():
    # Load the configuration file

    conf_file = '../Config/Process Project.json'
    try:
        with open(conf_file, 'r') as file:
            process_project_params_list = json.load(file)
    except FileNotFoundError:
        paint_logger.error(f"The configuration file {conf_file} was not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        paint_logger.error(f"Failed to decode JSON from the configuration file {conf_file}.")
        sys.exit(1)

    process_project_params = process_project_params_list[0]

    conf_file ='../Config/Paint Data Generation.json'
    try:
        with open(conf_file, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        paint_logger.error(f"The configuration file {conf_file} was not found.")
        config = []
        sys.exit(1)
    except json.JSONDecodeError:
        paint_logger.error(f"Failed to decode JSON from the configuration file {conf_file}.")
        config = []
        sys.exit(1)

    conf_file = process_project_params['Config File']
    paint_data = process_project_params['Paint Data']
    paint_source = process_project_params['Paint Source']
    data_version = process_project_params['Version']
    r_dest = process_project_params['R Destination']
    time_string = process_project_params['Time String']
    generate_all_tracks = process_project_params['Generate All Tracks']

    paint_data = paint_data + ' - v' + data_version
    r_dest = r_dest + ' - v' + data_version

    if time_string == '':
        current_time = datetime.now()
        time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")

    # Main loop to process each configuration based on flags

    nr_to_process = sum(1 for entry in config if entry['flag'])
    main_stamp = time.time()

    paint_logger.info("")
    paint_logger.info("")
    paint_logger.info(f"New Run - {'Debug' if PAINT_DEBUG else 'Production'} mode")
    paint_logger.info("")
    paint_logger.info(f"The configuration file is               : {conf_file}")
    paint_logger.info(f"The Paint Source directory is           : {paint_source}")
    paint_logger.info(f"The Paint Data directory is             : {paint_data}")
    paint_logger.info(f"The Version is                          : {data_version}")
    paint_logger.info(f"The R Output directory is               : {r_dest}")
    paint_logger.info(f"The number of directories to process is : {nr_to_process}")
    paint_logger.info(f"All Tracks will {'' if generate_all_tracks else 'not'} be generated")

    nr_to_process = sum(1 for entry in config if entry['flag'])

    current_process_seq_nr = 0
    error_count = 0
    for entry in config:
        if entry['flag']:
            paint_source_dir = os.path.join(paint_source, entry['probe'])
            paint_data_dir = os.path.join(paint_data, entry['probe'], entry['project_directory'])
            r_dest_dir = os.path.join(r_dest, entry['project_directory'])
            current_process_seq_nr += 1
            if not process_json_configuration_block(
                    paint_source_dir=paint_source_dir,
                    project_directory=entry['project_directory'],
                    paint_data_dir=paint_data_dir,
                    r_dest_dir=r_dest_dir,
                    probe=entry['probe'],
                    nr_of_squares_in_row=entry['nr_of_squares'],
                    nr_to_process=nr_to_process,
                    current_process=current_process_seq_nr,
                    min_density_ratio=entry['min_density_ratio'],
                    min_r_squared=entry['min_r_squared'],
                    min_tracks_for_tau=entry['min_tracks_for_tau'],
                    max_variability=entry['max_variability'],
                    max_square_coverage=entry['max_square_coverage'],
                    process_recording_tau=entry['process_recording_tau'],
                    process_square_tau=entry['process_square_tau'],
                    time_string=time_string,
                    paint_force=PAINT_FORCE,
                    generate_all_tracks=generate_all_tracks):
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

    logger_dir = get_paint_logger_directory()
    shutil.copyfile(os.path.join(logger_dir, 'Process All Projects.log'),
                    os.path.join(logger_dir, f'Process All Projects - v{data_version}.log'))

if __name__ == '__main__':
    main()
