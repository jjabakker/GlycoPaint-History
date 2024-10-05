import os
import platform
import shutil
import subprocess

# import winreg
from src.Common.Support.CommonSupportFunctions import delete_files_in_directory


# def find_app_path_windows():
#     reg_paths = [
#         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
#         r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
#     ]
#
#     for reg_path in reg_paths:
#         try:
#             reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
#             for i in range(0, winreg.QueryInfoKey(reg_key)[0]):
#                 sub_key_name = winreg.EnumKey(reg_key, i)
#                 sub_key = winreg.OpenKey(reg_key, sub_key_name)
#                 try:
#                     display_name = winreg.QueryValueEx(sub_key, "DisplayName")[0]
#                     if "Fiji".lower() in display_name.lower():
#                         install_location = winreg.QueryValueEx(sub_key, "InstallLocation")[0]
#                         return install_location
#                 except FileNotFoundError:
#                     continue
#         except FileNotFoundError:
#             continue
#     return None


def find_app_path_macos():
    """
    Function obtained from ChatGTP to locate the path of an application in macOS

    :return:
    """

    # Common directories to search
    common_paths = [
        '/Applications',
        os.path.expanduser('~/Applications'),
        '/System/Applications'
    ]

    # Check common directories
    for directory in common_paths:
        app_path = os.path.join(directory, "Fiji.app")
        if os.path.exists(app_path):
            return app_path

    # If not found, use mdfind (Spotlight search)
    try:
        result = subprocess.run(
            ['mdfind', f'kMDItemFSName == "Fiji.app"'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        paths = result.stdout.strip().split('\n')
        for path in paths:
            if path.endswith("Fiji.app"):
                return path
    except Exception as e:
        print(f"Error using mdfind: {e}")

    return None


def find_fiji_path():
    if platform.system() == "Darwin":
        fiji_app = find_app_path_macos()
    else:
        # fiji_app = find_app_path_windows()
        fiji_app = 'c:\\Fiji.app'
        if os.path.exists(fiji_app):
            pass
        else:
            fiji_app = 'd:\\Fiji.app'
            if os.path.exists(fiji_app):
                pass
            else:
                fiji_app = 'C:\\Program Files\\WindowsApps\\Fiji.app'
                if os.path.exists(fiji_app):
                    pass
                else:
                    fiji_app = 'C:\\Program Files\\Fiji.app'
                    if os.path.exists(fiji_app):
                        pass
                    else:
                        fiji_app = None

    return fiji_app


def copy_file_from_source_to_dest(source_dir, dest_dir, filename):
    """
    Utility function to copies a file from a source to destination directory
    :param source_dir:
    :param dest_dir:
    :param filename:
    :return:
    """

    source_file = source_dir + os.sep + filename
    dest_file = dest_dir + os.sep + filename
    if not os.path.isfile(source_file):
        print(f"File {source_file} does not exist")
    elif not os.path.isdir(dest_dir):
        print(f"Destination directory {dest_dir} does not exist")
    else:
        shutil.copyfile(source_file, dest_file)
        print(f"\t{filename}")


def install():
    fiji_app = find_fiji_path()
    if fiji_app is None:
        print('Fiji app not found. Please specify a path for Fiji directly')
        exit(1)

    dest_root = os.path.join(fiji_app, 'scripts', 'Plugins')

    # Determine the source_root from the current path
    head_tail = os.path.split(os.getcwd())
    source_root = os.path.split(head_tail[0])[0]

    # Define the source directories
    fiji_grid_source = os.path.join(source_root, 'Fiji', 'Grid')
    fiji_single_source = os.path.join(source_root, 'Fiji', 'Single')
    fiji_support_source = os.path.join(source_root, 'Fiji', 'Support')

    common_support_source = os.path.join(source_root, 'Common', 'Support')

    # Define the destination directories
    fiji_grid_dest = os.path.join(dest_root, 'Paint', 'Grid')
    fiji_single_dest = os.path.join(dest_root, 'Paint', 'Single')
    library_dest = os.path.join(dest_root, 'Paint')

    # Create and empty the directories
    fiji_directories = [library_dest, fiji_grid_dest, fiji_single_dest]
    for directory in fiji_directories:
        if os.path.exists(directory):
            delete_files_in_directory(directory)
        else:
            os.mkdir(directory)

    # Then do the actual copying

    print(f"\n\nCopy from {fiji_grid_source} to {fiji_grid_dest}: ")
    plugin_files = ["Grid_Process_Batch.py", "Convert_BF_images.py", "Grid_Process_Batch_Batch.py"]
    for file in plugin_files:
        copy_file_from_source_to_dest(fiji_grid_source, fiji_grid_dest, file)

    print(f"\n\nCopy from {fiji_single_source} to {fiji_single_dest}: ")
    plugin_files = ["Single_Analysis.py"]
    for file in plugin_files:
        copy_file_from_source_to_dest(fiji_single_source, fiji_single_dest, file)

    print(f"\n\nCopy from {fiji_support_source} to {library_dest}: ")
    fiji_files = ["FijiSupportFunctions.py", "Trackmate.py", "LoggerConfigFiji.py"]
    for file in fiji_files:
        copy_file_from_source_to_dest(fiji_support_source, library_dest, file)

    print(f"\n\nCopy from {common_support_source} to {library_dest}: ")
    fiji_files = ["CommonSupportFunctions.py"]
    for file in fiji_files:
        copy_file_from_source_to_dest(common_support_source, library_dest, file)

    # Create the Trackmate Data and Paint profile directories
    profile_dir = os.path.join(os.path.expanduser('~'), "Paint Profile")
    trackmate_dir = os.path.join(os.path.expanduser('~'), "Trackmate Data")

    dirs_to_create = [profile_dir, trackmate_dir]
    for directory in dirs_to_create:
        if not os.path.isdir(directory):
            print("\nCreated directory {dir}")
            os.makedirs(directory)


if __name__ == '__main__':
    install()
