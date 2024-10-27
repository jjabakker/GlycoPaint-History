import os

import pandas as pd

from src.Application.Generate_Squares.Utilities.Generate_Squares_Support_Functions import (
    get_square_coordinates)
from src.Common.Support.LoggerConfig import (
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')


def add_dc_to_squares_file(df_tracks: pd.DataFrame, nr_of_squares_in_row: int, project_directory: str):
    """
    Add the diffusion coefficient to the squares file. The squares file is assumed to be in the project directory.
    """
    nr_squares = nr_of_squares_in_row ** 2

    # Find out which unique Recordings there are
    recording_names = df_tracks['RECORDING NAME'].unique().tolist()

    for recording_name in recording_names:

        # For each recording get the tracks
        df_tracks_in_recording = df_tracks[df_tracks['RECORDING NAME'] == recording_name]

        # Find the squares file associated with this recording
        path = find_squares_file(project_directory, recording_name + '-squares.csv')
        if path:
            df_squares = pd.read_csv(path)

        df_squares = df_squares.sort_values(by='Square Nr', ascending=True)

        # Add the new DC column or just initialise it. Get the column numbetr
        df_squares['DC'] = 0
        dc_col_index = df_squares.columns.get_loc('DC')
        square_nr_col_index = df_squares.columns.get_loc('Square Nr')

        # Now determine for each square which tracks fit in, start
        count = 0
        for i in range(nr_squares):
            square_nr = df_squares.iloc(i, square_nr_col_index)
            x0, y0, x1, y1 = get_square_coordinates(nr_of_squares_in_row, i)
            df_tracks_in_square = df_tracks_in_recording[
                (df_tracks_in_recording['TRACK_X_LOCATION'] >= x0) & (
                            df_tracks_in_recording['TRACK_X_LOCATION'] <= x1) &
                (df_tracks_in_recording['TRACK_Y_LOCATION'] >= y0) & (df_tracks_in_recording['TRACK_Y_LOCATION'] <= y1)]
            if len(df_tracks_in_square) > 0:
                dc_mean = df_tracks_in_square['DIFFUSION_COEFFICIENT'].mean()
                count += 1
            else:
                dc_mean = -1

            df_squares.iloc[square_nr, dc_col_index] = int(dc_mean)

        df_squares = df_squares.sort_values(by='Nr Tracks', ascending=False)
        df_squares.to_csv(path, index=False)

        print(f"File {recording_name} has {count} squares with a valid DC")


def find_squares_file(root_directory, target_filename):
    for dirpath, dirnames, filenames in os.walk(root_directory):
        if target_filename in filenames:
            # Join the directory path with the filename to get the full path
            return os.path.join(dirpath, target_filename)
    return None  # Return None if the file is not found


if __name__ == '__main__':
    df_tracks = pd.read_csv('/Users/hans/Paint Work/New Probes/Output/All Tracks.csv')
    add_dc_to_squares_file(df_tracks, 20, '/Users/hans/Paint Work/New Probes')

    df_tracks = pd.read_csv('/Users/hans/Paint Work/Regular Probes/Output/All Tracks.csv')
    add_dc_to_squares_file(df_tracks, 20, '/Users/hans/Paint Work/Regular Probes')
