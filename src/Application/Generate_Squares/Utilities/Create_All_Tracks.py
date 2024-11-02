import os
import time

import pandas as pd

from src.Application.Utilities.General_Support_Functions import (
    format_time_nicely)
from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Create All Tracks.log')


def create_and_save_all_tracks(root_dir):
    """
    Read all tracks files in the directory tree and concatenate them into a single DataFrame.
    The file is then saved as 'All Tracks.csv' in the root directory.
    """

    time_stamp = time.time()

    csv_files = []

    # Traverse the directory tree, to find all the files
    for root, dirs, files in os.walk(root_dir):
        if os.path.basename(root).lower() == 'trackmate tracks':
            for file in files:
                # Check if it's a CSV file that contains 'tracks', threshold, but not 'label' in the name
                if (any(keyword in file for keyword in ['tracks', 'threshold']) and
                        file.endswith('.csv') and 'label' not in file):
                    csv_files.append(os.path.join(root, file))
                    # paint_logger.debug(f"Read Tracks file: {os.path.join(root, file)}")
    paint_logger.info(f"Located {len(csv_files)} tracks files in {root_dir}")

    csv_files.sort()
    for file in csv_files:
        paint_logger.debug(f"Found Tracks file: {file}")

    # Read and concatenate all CSV files found
    df_tracks = pd.concat((pd.read_csv(f, header=0, skiprows=[1, 2, 3]) for f in csv_files), ignore_index=True)
    if df_tracks.empty:
        paint_logger.error("No tracks files found.")
        return None
    else:
        # Save the file in the Output directory

        os.makedirs(os.path.join(root_dir, 'Output'), exist_ok=True)
        all_tracks_file_path = os.path.join(root_dir, 'Output', 'All Tracks.csv')
        df_tracks.to_csv(all_tracks_file_path, index=False)
        run_time = time.time() - time_stamp
        paint_logger.info(f"Combined {len(csv_files)} tracks files and saved as {all_tracks_file_path} in {format_time_nicely(run_time)}.")
        paint_logger.info("")

    return df_tracks
