import logging
import os

# Create a custom logger
logger = logging.getLogger('paint')

# Set the global logging level (this applies to all handlers unless overridden)
logger.setLevel(logging.DEBUG)  # Logs everything from DEBUG level and above

# Create and set the log format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# Create console handler
console_handler = logging.StreamHandler()  # Logs to the console (standard output)
console_handler.setLevel(logging.DEBUG)  # All logs at DEBUG level or higher go to the console
console_handler.setFormatter(formatter)

# Create file handler

def create_file_handler(file_name):
    file_handler    = logging.FileHandler(os.path.join(os.path.expanduser('~'), file_name), mode='w')  # Logs to a file
    file_handler.setLevel(logging.INFO)  # Only logs at INFO level or higher go to the file
    file_handler.setFormatter(formatter)
    return file_handler


file_handler = create_file_handler('paint.log')

# Step 6: Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def change_file_handler(file_name):
    global file_handler

    logger.removeHandler(file_handler)
    file_handler = create_file_handler(file_name)
    logger.addHandler(file_handler)
