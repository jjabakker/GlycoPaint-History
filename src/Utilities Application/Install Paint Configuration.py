import os
import shutil

from fontTools.ttLib.tables.otTables import Paint


def install_paint_configuration():
    """
    The function installs the Paint configuration files in the user's home directory.
    The configuration files are used to store the user's preferences and settings.
    """

    # Create the directories of needed
    home_dir = os.path.expanduser('~')
    os.makedirs(os.path.join(home_dir, 'Paint', 'Logger'), exist_ok=True)
    os.makedirs(os.path.join(home_dir, 'Paint', 'Defaults'), exist_ok=True)

    # Copy the configuration file
    shutil.copyfile(os.path.join('..', 'Config', 'Paint.json'), os.path.join(home_dir, 'Paint', 'Defaults', 'Paint.json'))
    print("Paint configuration installed successfully.")



if __name__ == '__main__':
    install_paint_configuration()