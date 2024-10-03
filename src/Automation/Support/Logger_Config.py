import logging
import os

# Setup logging

# Step 1: Create a custom logger
logger = logging.getLogger('my_logger')

# Step 2: Set the global logging level (this applies to all handlers unless overridden)
logger.setLevel(logging.DEBUG)  # Logs everything from DEBUG level and above

# Step 3: Create handlers
console_handler = logging.StreamHandler()  # Logs to the console (standard output)
file_handler = logging.FileHandler(os.path.join(os.path.expanduser('~'), 'app.log'), mode ='w')  # Logs to a file

# Step 4: Set logging levels for the handlers
console_handler.setLevel(logging.DEBUG)  # All logs at DEBUG level or higher go to the console
file_handler.setLevel(logging.INFO)  # Only logs at INFO level or higher go to the file

# Step 5: Create and set the log format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Step 6: Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
