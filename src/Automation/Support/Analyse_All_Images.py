import os
import statistics

import pandas as pd

from src.Automation.Support.Support_Functions import ask_user_for_paint_directory
from src.Automation.Support.Support_Functions import get_df_from_file
from src.Automation.Support.Support_Functions import read_experiment_file


def analyse_all_images(paint_directory):
    """
    This function inspects a batch file and produces summary data
    :param paint_directory:
    :return:
    """

    # Read the batch  file. If the file is not there just return (a message will have been printed)
    df_batch = read_experiment_file(os.path.join(paint_directory, 'grid_batch.csv'), only_records_to_process=True)
    if df_batch is None:
        print(f"Function 'analyse_all_images' failed: No batch file: {os.path.join(paint_directory, 'grid_batch.csv')}")
        exit()

    # Now cycle through the images
    count = 0
    df_stats = pd.DataFrame()

    print("                                                                                     Mean     StDev     Nr")
    for index, row in df_batch.iterrows():
        image_name = row["Ext Image Name"]

        df_squares = get_df_from_file(os.path.join(paint_directory, image_name, "grid",
                                                   image_name + "-squares.csv"))
        if df_squares is None:
            print(f"Could not open: {df_squares}")
            pass

        cell_ids = df_squares["Cell Id"].unique().tolist()
        cell_ids.sort()

        for cell_id in cell_ids:
            df_cell = df_squares[df_squares['Cell Id'] == cell_id]
            df_cell_visible = df_cell[df_cell["Visible"]]
            if len(df_cell_visible) == 0:
                continue
            else:
                taus = df_cell_visible["Tau"].tolist()
                if len(taus) > 0:
                    probe = df_batch['Probe'].loc[index]
                    probe_type = df_batch['Probe Type'].loc[index]
                    cell_type = df_batch['Cell Type'].loc[index]
                    concentration = df_batch['Concentration'].loc[index]
                    threshold = df_batch['Threshold'].loc[index]
                    key = image_name + "-" + str(cell_id) + " - (" + probe + ") - (" + cell_type + ")"
                    tau_mean = round(statistics.mean(taus), 0)
                    if len(taus) >= 2:
                        tau_std = round(statistics.stdev(taus), 1)
                    else:
                        tau_std = 0
                    tau_nr = len(taus)
                    row = [image_name, cell_id, cell_type, probe_type, probe, concentration, threshold, key, tau_mean,
                           tau_std, tau_nr]
                    df_stats = pd.concat([df_stats, pd.DataFrame.from_records([row])])
                    count += 1
                    print(
                        f" {image_name:32s}-{cell_id:1d}  {cell_type:10} {probe_type:5s} {probe:6s} {concentration:2.1f} {threshold:3.1f}: {tau_mean:8.0f} {tau_std:8.0f} {tau_nr:8d}")
        print('\n')

    print(f"Count is {count}")

    print('Analysis of batch completed')

    df_stats.columns = ["Image Name", "Cell Id", "Cell Type", "Probe Type", "Probe", "Concentration", 'Threshold',
                        'Key', 'Mean', 'Std', 'Nr']
    df_stats.to_excel(os.path.join(paint_directory, 'Output', 'Statistics Summary Data.xlsx'))
    return df_stats


def create_summary_graphpad(image_directory, df_stats):
    df_for_graphpad = pd.DataFrame()
    cols_for_graphpad = []
    probes = df_stats['Probe'].unique().tolist()

    for probe in probes:
        df_probe = df_stats[df_stats['Probe'] == probe]
        cell_types = df_probe['Cell Type'].unique()
        for cell_type in cell_types:
            df_cell_type = df_probe[df_probe['Cell Type'] == cell_type]
            df_data = df_cell_type[['Mean', 'Std', 'Nr']]
            columns = [probe + "-" + cell_type + "-Mean",
                       probe + "-" + cell_type + "-Std",
                       probe + "-" + cell_type + "-Nr"]
            df_data.reset_index(inplace=True, drop=True)

            df_for_graphpad = pd.concat([df_for_graphpad, df_data], axis=1, ignore_index=True)
            cols_for_graphpad = cols_for_graphpad + columns

    df_for_graphpad.columns = cols_for_graphpad
    df_for_graphpad.to_excel(os.path.join(image_directory, 'Output', 'Graphpad - Tau - Summary Statistics.xlsx'))
    # print(df_for_graphpad.to_markdown())


if __name__ == "__main__":
    image_directory = ask_user_for_paint_directory()
    if image_directory == "":
        print("No image directory selected")
    else:
        df_stats = analyse_all_images(image_directory)
        create_summary_graphpad(image_directory, df_stats)
        print(df_stats.to_markdown())
