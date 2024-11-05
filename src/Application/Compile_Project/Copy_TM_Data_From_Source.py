import os
import shutil


def copy_tm_data_from_paint_source(source_dir, destination_dir):

    # Ensure the destination directory exists
    os.makedirs(destination_dir, exist_ok=True)

    # Loop through only the first level of subdirectories in source_dir
    for subdir in os.listdir(source_dir):
        subdir_path = os.path.join(source_dir, subdir)

        # Check if it's a directory (to ignore files in the root)
        if os.path.isdir(subdir_path):
            # Create the corresponding directory in the destination
            dest_path = os.path.join(destination_dir, subdir)
            os.makedirs(dest_path, exist_ok=True)

            # Copy only the specified files if they exist
            for file in ['All Tracks.csv', 'Experiment TM.csv']:
                src_file_path = os.path.join(subdir_path, file)
                if os.path.exists(src_file_path):
                    dest_file_path = os.path.join(dest_path, file)
                    shutil.copy2(src_file_path, dest_file_path)  # copy2 preserves metadata
                    # print(f"Copied {src_file_path} to {dest_file_path}")


if __name__ == '__main__':
    source_dir = r'C:\Users\user\Documents\TM\TM Paint Source'
    destination_dir = r'C:\Users\user\Documents\TM\TM Data'
    copy_tm_data_from_paint_source(source_dir, destination_dir)