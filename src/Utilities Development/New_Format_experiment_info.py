import os

import pandas as pd


def process_experiment_info_files(root_directory):
    # Traverse the directory tree
    for dirpath, dirnames, filenames in os.walk(root_directory):
        # Look for files named 'experiment_info.csv'
        if 'experiment_info.csv' in filenames:
            # Full path of the original file
            original_file_path = os.path.join(dirpath, 'experiment_info.csv')

            # Read the CSV file into a DataFrame
            df = pd.read_csv(original_file_path)

            # Create the new DataFrame with the required columns and mappings
            new_df = pd.DataFrame()

            # Mapping the columns
            new_df['Recording Sequence Nr'] = df['Batch Sequence Nr']
            new_df['Recording Name'] = df['Image Name']
            new_df['Experiment Date'] = df['Experiment Date']  # Copying to both Experiment Date and Experiment Name
            new_df['Experiment Name'] = df['Experiment Date']
            new_df['Condition Nr'] = df['Experiment Nr']
            new_df['Replicate Nr'] = df['Experiment Seq Nr']

            # Add remaining columns if they exist in the original dataframe, otherwise fill with NaN
            columns_to_copy = ['Probe', 'Probe Type', 'Cell Type', 'Adjuvant',
                               'Concentration', 'Threshold', 'Process']
            for col in columns_to_copy:
                if col in df.columns:
                    new_df[col] = df[col]
                else:
                    new_df[col] = pd.NA  # Or use None if you prefer

            # Rename the original 'experiment_info.csv' to 'old_experiment_info.csv'
            # old_file_path = os.path.join(dirpath, 'old_experiment_info.csv')
            # os.rename(original_file_path, old_file_path)
            # print(f"Renamed original file to: {old_file_path}")

            # Write the new DataFrame to 'experiment_info.csv' (overwriting the original filename)
            new_file_path = os.path.join(dirpath, 'experiment_tm.csv')
            new_df.to_csv(new_file_path, index=False)
            print(f"Processed and saved new file: {new_file_path}")


# Example usage: Provide the root directory where the traversal should start
root_dir = '/Users/hans/Paint Source'
process_experiment_info_files(root_dir)
