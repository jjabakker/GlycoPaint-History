import os
import sys
import time

import numpy as np
import pandas as pd

from src.Application.Generate_Squares.Utilities.Curvefit_and_Plot import (
    compile_duration,
    curve_fit_and_plot)

from src.Application.Generate_Squares.Utilities.Generate_Squares_Support_Functions import (
    check_experiment_integrity,
    get_square_coordinates,
    calc_variability,
    calculate_density,
    write_np_to_excel,
    get_df_from_file,
    get_area_of_square,
    calc_average_track_count_of_lowest_squares)

from src.Application.Utilities.General_Support_Functions import (
    save_squares_to_file,
    save_experiment_to_file,
    format_time_nicely,
    read_experiment_tm_file)

from src.Common.Support.DirectoriesAndLocations import (
    delete_files_in_directory,
    get_tau_plots_dir_path,
    get_tracks_dir_path,
    get_squares_dir_path,
    get_squares_file_path,
    get_tracks_file_path)

from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')


def analyse_tracks(df_tracks, nr_of_squares_in_row, project_directory):

    nr_squares = nr_of_squares_in_row ** 2
    recording_names = df_tracks['RECORDING NAME'].unique().tolist()
    for recording_name in recording_names:
        df_tracks_in_recording = df_tracks[df_tracks['RECORDING NAME'] == recording_name]

        path = find_file(project_directory, recording_name + '-squares.csv')
        if path:
            df_squares = pd.read_csv(path)

        count = 0
        for i in range(nr_squares):
            x0, y0, x1, y1 = get_square_coordinates(nr_of_squares_in_row, i)
            df_tracks_in_square = df_tracks_in_recording[
                (df_tracks_in_recording['TRACK_X_LOCATION'] >= x0) & (df_tracks_in_recording['TRACK_X_LOCATION'] <= x1) &
                (df_tracks_in_recording['TRACK_Y_LOCATION'] >= y0) & (df_tracks_in_recording['TRACK_Y_LOCATION'] <= y1)]
            if len(df_tracks_in_square) > 0:
                dc_mean = df_tracks_in_square['DIFFUSION_COEFFICIENT'].mean()
                count += 1
            else:
                dc_mean = -1

            df_squares.loc[i, 'Mean DC'] = int(dc_mean)

        df_squares.to_csv(path, index=False)


        print(f"File {recording_name} has {count} squares with a valid DC")


def find_file(root_directory, target_filename):
    for dirpath, dirnames, filenames in os.walk(root_directory):
        if target_filename in filenames:
            # Join the directory path with the filename to get the full path
            return os.path.join(dirpath, target_filename)
    return None  # Return None if the file is not found

if __name__ == '__main__':
    df_tracks = pd.read_csv('/Users/hans/Paint Work/New Probes/Output/All Tracks.csv')
    analyse_tracks(df_tracks, 20, '/Users/hans/Paint Work/New Probes')

    df_tracks = pd.read_csv('/Users/hans/Paint Work/Regular Probes/Output/All Tracks.csv')
    analyse_tracks(df_tracks, 20, '/Users/hans/Paint Work/Regular Probes')