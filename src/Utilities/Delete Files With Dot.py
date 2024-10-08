import os

def delete_dot_files(directory):
    # Traverse the directory tree
    for root, dirs, files in os.walk(directory):
        # Set to keep track of filenames without the leading dot
        non_dot_files = set()

        # First pass: record all non-dot files
        for file in files:
            if not file.startswith('.'):
                # Store the name of the non-dot file
                non_dot_files.add(file)

        # Second pass: delete dot-files if corresponding non-dot file exists
        for file in files:
            if file.startswith('.'):
                # The corresponding non-dot filename
                corresponding_file = file[1:]  # Remove the leading dot

                if corresponding_file in non_dot_files:
                    # Full path of the dot file to be deleted
                    dot_file_path = os.path.join(root, file)

                    try:
                        os.remove(dot_file_path)
                        print(f"Deleted: {dot_file_path}")
                    except OSError as e:
                        print(f"Error deleting {dot_file_path}: {e}")

# Specify the directory you want to process
directory_path = "/Users/hans/Downloads"

# Call the function
delete_dot_files(directory_path)