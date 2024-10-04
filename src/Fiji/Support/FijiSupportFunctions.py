import os
import sys
import java.lang

from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate import Model
from javax.swing import JFileChooser
from java.lang.System import getProperty

paint_code__dir = os.path.join(getProperty('fiji.dir'), "scripts", "Plugins", "Paint")
sys.path.append(paint_code__dir)

from CommonSupportFunctions import get_default_directories
from CommonSupportFunctions import save_default_directories



def ask_user_for_image_directory(prompt='Select Folder', directory='Paint'):

    """
    Ask the user to specify the user image directory. Present the last used value as default.
    Save the user choice.
    :param prompt:
    :return:
    """
    root_dir, paint_dir, images_dir = get_default_directories()

    if (directory == 'Paint'):
        def_dir = paint_dir
    else:
        def_dir = images_dir

    file_chooser = JFileChooser(def_dir)
    file_chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)

    # Show the dialog and get the result
    result = file_chooser.showDialog(None, prompt)

    # Check if the user selected a directory
    if result == JFileChooser.APPROVE_OPTION:
        selected_directory = file_chooser.getSelectedFile()
        if (directory == 'Paint'):
            paint_dir = selected_directory
        else:
            images_dir = selected_directory
        save_default_directories(root_dir, paint_dir, images_dir)
        return selected_directory.getAbsolutePath()
    else:
        return ""


def ask_user_for_file(prompt='Select File'):

    """
    Ask the user to specify the user image directory. Present the last used value as default.
    Save the user choice.
    :param prompt:
    :return:
    """
    root_dir, paint_dir, images_dir = get_default_directories()

    file_chooser = JFileChooser('~')
    file_chooser.setFileSelectionMode(JFileChooser.FILES_ONLY)

    # Show the dialog and get the result
    result = file_chooser.showDialog(None, prompt)

    # Check if the user selected a directory
    if result == JFileChooser.APPROVE_OPTION:
        selected_file = file_chooser.getSelectedFile()
        return selected_file.getAbsolutePath()
    else:
        return ""


def fiji_get_file_open_write_attribute():

    """
    Returns a open write attribute that works both on MacOs and Windoes
    :return: A string containing the open write attribute
    """

    ver = java.lang.System.getProperty("os.name").lower()
    if ver.startswith("mac"):
        open_attribute = "w"
    else:
        open_attribute = "wb"

    return open_attribute




def fiji_get_file_open_append_attribute():

    """
    Returns an open append  attribute that works both on Mac OS and Windoes
    :return: A string containing the open append attribute
    """

    ver = java.lang.System.getProperty("os.name").lower()
    if ver.startswith("mac"):
        open_attribute = "a"
    else:
        open_attribute = "ab"

    return open_attribute