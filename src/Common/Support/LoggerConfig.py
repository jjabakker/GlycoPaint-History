import logging
from os import path
import os


# Create a custom logger
paint_logger = logging.getLogger('paint')

# Set the global logging level (this applies to all handlers unless overridden)
paint_logger.setLevel(logging.DEBUG)  # Logs everything from DEBUG level and above

# Create and set the log format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# Create console handler
console_handler = logging.StreamHandler()  # Logs to the console (standard output)
console_handler.setLevel(logging.DEBUG)  # All logs at DEBUG level or higher go to the console
console_handler.setFormatter(formatter)

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL  = logging.CRITICAL

# Create file handler

def _get_paint_configuration_directory(sub_dir):
    conf_dir = os.path.join(os.path.expanduser('~'), 'Paint')
    if not os.path.exists(conf_dir):
        os.makedirs(os.path.join(conf_dir, sub_dir))
    return conf_dir

def get_paint_logger_directory():
    sub_dir = 'Paint Logger'
    return os.path.join(_get_paint_configuration_directory(sub_dir), sub_dir)

def create_file_handler(file_name):
    file_handler_dir = get_paint_logger_directory()

    file_handler = logging.FileHandler(path.join(file_handler_dir, file_name), mode='w')  # Logs to a file
    file_handler.setLevel(logging.INFO)  # Only logs at INFO level or higher go to the file
    file_handler.setFormatter(formatter)
    return file_handler

file_handler = create_file_handler('paint.log')

def paint_logger_file_handle_set_level(level):
    global file_handler

    if level not in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
        raise ValueError("Invalid level: {}".format(level))
    else:
        file_handler.setLevel(level)

def paint_logger_console_handle_set_level(level):
    global console_handler

    if level not in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
        raise ValueError("Invalid level: {}.format(level)")
    else:
        console_handler.setLevel(level)



# Add handlers to the logger
paint_logger.addHandler(console_handler)
paint_logger.addHandler(file_handler)


def paint_logger_change_file_handler_name(file_name):
    global file_handler
    global paint_logger_file_name_assigned

    paint_logger.removeHandler(file_handler)
    file_handler = create_file_handler(file_name)
    paint_logger.addHandler(file_handler)
    paint_logger_file_name_assigned = True


paint_logger_file_name_assigned = False
