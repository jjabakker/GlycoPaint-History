import logging
import os
from os import mkdir

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


# Create file handler
def create_file_handler(file_name):
    file_handler_dir = os.path.join(os.path.expanduser('~'), 'Paint Logger')
    if not os.path.exists(file_handler_dir):
        mkdir(file_handler_dir)
    file_handler = logging.FileHandler(os.path.join(file_handler_dir, file_name), mode='w')  # Logs to a file
    file_handler.setLevel(logging.INFO)  # Only logs at INFO level or higher go to the file
    file_handler.setFormatter(formatter)
    return file_handler


file_handler = create_file_handler('paint.log')

# Add handlers to the logger
paint_logger.addHandler(console_handler)
paint_logger.addHandler(file_handler)


def change_file_handler(file_name):
    global file_handler
    global logger_file_name_assigned

    paint_logger.removeHandler(file_handler)
    file_handler = create_file_handler(file_name)
    paint_logger.addHandler(file_handler)
    paint_logger_file_name_assigned = True


paint_logger_file_name_assigned = False
