import math
import os
import sys
import json
import pandas as pd
from  src.Common.Support.LoggerConfig import paint_logger, change_file_handler

CONF_FILE = '/Users/hans/Paint Source/paint data generation - production.json'
PAINT_SOURCE = '/Users/hans/Paint Source'
PAINT_DATA = '/Users/Hans/Paint Data'
R_DATA_DEST = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/Python and R Code/Paint-R/Data New'
TIME_STAMP = '2024-10-11 00:00:00'  # '%Y-%m-%d %H:%M:%S

change_file_handler('Inspect All Image File.log')


def inspect_all_images_file(image_file_path: str, short_file_name: str) -> None:

    df_images = pd.read_csv(image_file_path, low_memory=False)

    paint_logger.info("-" * 80)
    paint_logger.info(f"Inspecting file: {image_file_path}")
    paint_logger.info(f"Short file name: {short_file_name}")
    paint_logger.info("-" * 80)
    paint_logger.info("")

    # -------------------------------------------------------------------------------------------
    # See if the columns are as expected
    # -------------------------------------------------------------------------------------------

    expected_traditional_columns =  {
        'Batch Sequence Nr', 'Experiment Date', 'Experiment Name', 'Experiment Nr',
        'Experiment Seq Nr', 'Image Name', 'Probe', 'Probe Type', 'Cell Type', 'Adjuvant',
        'Concentration', 'Threshold', 'Density Ratio Setting', 'Process', 'Ext Image Name',
        'Nr Spots', 'Nr Tracks', 'Image Size', 'Run Time','Time Stamp', 'Min Tracks for Tau',
        'Min R Squared', 'Nr Of Squares per Row', 'Exclude', 'Neighbour Setting', 'Variability Setting',
        'Nr Total Squares', 'Nr Defined Squares', 'Nr Visible Squares',
        'Nr Invisible Squares', 'Nr Rejected Squares', 'Max Squares Ratio', 'Squares Ratio',
    }

    expected_single_columns = {'Tau', 'Density', 'R Squared', 'Min Density Ratio'}

    actual_columns = set(df_images.columns)

    if expected_single_columns <= set(actual_columns):
        process_mode = 'Single'
        paint_logger.info('Images file format is Single')
        expected_columns = expected_single_columns | expected_traditional_columns
    else:
        process_mode = 'Traditional'
        paint_logger.info('Images file format is Traditional')
        expected_columns = expected_traditional_columns

    missing_cols = set(expected_columns) - set(actual_columns)
    extra_cols = set(actual_columns) - set(expected_columns)

    if missing_cols:
        paint_logger.error(f"Missing columns: {missing_cols}")
    if extra_cols:
        paint_logger.error(f"Extra columns: {extra_cols}")
    if not (missing_cols or extra_cols):
        paint_logger.info("Columns are as expected")


    # -------------------------------------------------------------------------------------------
    # Display values
    # -------------------------------------------------------------------------------------------

    # Count the number of unique values for the following columns
    nr_of_squares = int(math.sqrt(df_images.loc[0, 'Nr Total Squares']))
    paint_logger.info(f"Number of squares per row is          : {nr_of_squares}")

    # If the processing name mentions a number of squares, check if it is correct
    if f"{nr_of_squares} Squares" not in image_file_path:
        paint_logger.error(f"Number of squares per row is not in the file name: {image_file_path}")

    paint_logger.info(f"Number of Density Ratio Settings is   : {df_images['Density Ratio Setting'].nunique()} - {', '.join(df_images['Density Ratio Setting'].unique().astype(str).tolist())}")
    if process_mode == 'Single':
        paint_logger.info(f"Number of Min Density Ratios is       : {df_images['Min Density Ratio'].nunique()} - {', '.join(df_images['Min Density Ratio'].unique().astype(str).tolist())}")
        if df_images['Min Density Ratio'].nunique() != 1:
            paint_logger.error(f"Multiple Min Density Ratios in the file: {', '.join(df_images['Min Density Ratio'].unique().astype(str).tolist())}")
        else:
            if f"{nr_of_squares} Squares" not in image_file_path:
                density_ratio_setting = df_images.loc[0, 'Density Ratio Setting']
                if f"{density_ratio_setting} DR" not in image_file_path:
                    paint_logger.error(f"Density Ratio Setting of {density_ratio_setting} is not in the file name: {image_file_path}")

    paint_logger.info(f"Number of Cell Types is               : {df_images['Cell Type'].nunique()} - {', '.join(df_images['Cell Type'].unique())}")
    paint_logger.info(f"Number of Probes Types is             : {df_images['Probe Type'].nunique()} - {', '.join(df_images['Probe Type'].unique())}")
    paint_logger.info(f"Number of Probes is                   : {df_images['Probe'].nunique()} - {', '.join(df_images['Probe'].unique())}")
    paint_logger.info(f"Number of Adjuvants is                : {df_images['Adjuvant'].nunique()} - {', '.join(df_images['Adjuvant'].unique())}")

    paint_logger.info('\n\n')


def main():

    change_file_handler('Inspect All Images.log')

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

    current_process_seq_nr = 0
    for entry in config:
        if entry['flag']:

            short_file_name = entry['directory']
            r_dest_dir = os.path.join(R_DATA_DEST, entry['directory'])
            file_to_inspect_name = os.path.join(r_dest_dir, 'Output', 'All Images.csv')
            current_process_seq_nr += 1
            inspect_all_images_file(file_to_inspect_name, short_file_name)


if __name__ == '__main__':

    main()

    # file = '/Users/hans/Paint Data/New Probes/Single/Paint New Probes - Single - 30 Squares - 5 DR/Output/All Images.csv'
    # inspect_all_images_file(file)
    #
    # file = '/Users/hans/Downloads/Paint New Probes - Traditional - 21 Squares - 2 DR/Output/All Images.csv'
    # inspect_all_images_file(file)
    #
    # file = '/Users/hans/Paint Data/New Probes/Traditional/Paint New Probes - Traditional - 20 Squares - 2 DR/Output/All Images.csv'
    # inspect_all_images_file(file)
    #
    # file = '/Users/hans/Paint Data/Regular Probes/Single/Paint Regular Probes - Single - 30 Squares - 5 DR/Output/All Images.csv'
    # inspect_all_images_file(file)
    #
    # file = '/Users/hans/Paint Data/Regular Probes/Traditional/Paint Regular Probes - Traditional - 20 Squares - 2 DR/Output/All Images.csv'
    # inspect_all_images_file(file)
