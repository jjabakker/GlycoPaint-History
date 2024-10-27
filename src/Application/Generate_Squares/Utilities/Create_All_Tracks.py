import os

import pandas as pd

from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Create All Tracks.log')


def create_all_tracks(root_dir):
    # Initialize an empty list to collect file paths
    csv_files = []

    # Traverse the directory tree, to find all the files
    for root, dirs, files in os.walk(root_dir):
        if os.path.basename(root) == 'TrackMate Tracks':
            for file in files:
                # Check if it's a CSV file and does not contain 'label' in the name
                if any(keyword in file for keyword in ['tracks', 'threshold']) and file.endswith(
                        '.csv') and 'label' not in file:
                    csv_files.append(os.path.join(root, file))
                    paint_logger.debug(f"Read Tracks file: {file}")


    # Read and concatenate all CSV files found
    df_tracks = pd.concat((pd.read_csv(f, header=0, skiprows=[1, 2, 3]) for f in csv_files), ignore_index=True)
    if df_tracks.empty:
        paint_logger.error("No tracks files found.")
        return None
    else:
        df_tracks.to_csv('All Tracks.csv', index=False)
        paint_logger.info(f"Combined {len(csv_files)} tracks files.")
    return df_tracks