import os
import time

from src.Common.Support.LoggerConfig import paint_logger


def set_directory_timestamp(dir_path, timestamp=None):
    """
    Set the access and modification timestamps of a directory.

    :param dir_path: Path to the directory.
    :param timestamp: Unix timestamp (seconds since epoch) to set for access and modification times.
                      If None, the current time will be used.
    """
    # Check if the provided path is a valid directory
    if not os.path.isdir(dir_path):
        paint_logger.error(f"Error: '{dir_path}' is not a valid directory.")
        return

    # If no timestamp is provided, use the current time
    if timestamp is None:
        timestamp = time.time()

    try:
        # Update the directory's access and modification times
        os.utime(dir_path, (timestamp, timestamp))
        paint_logger.debug(f"Updated timestamps for directory '{dir_path}' successfully.")

    except PermissionError:
        paint_logger.error(f"Error: Permission denied while setting timestamps for '{dir_path}'.")

    except FileNotFoundError:
        paint_logger.error(f"Error: Directory '{dir_path}' not found.")

    except Exception as e:
        paint_logger.error(f"An unexpected error occurred: {e}")


# Example Usage: Set timestamps to a specific date
def get_timestamp_from_string(date_str, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Convert a date string into a Unix timestamp.

    :param date_str: The date in string format (e.g., '2023-01-01 12:00:00').
    :param format_str: Format of the input date string (default: '%Y-%m-%d %H:%M:%S').
    :return: Unix timestamp (seconds since epoch).
    """
    try:
        return time.mktime(time.strptime(date_str, format_str))
    except ValueError as e:
        print(f"Error: Invalid date format. {e}")
        return None


if __name__ == '__main__':
    # Example of using current time for timestamp
    set_directory_timestamp(
        '/Users/hans/Paint Data/Regular Probes/Single/Paint Regular Probes - Single - 30 Squares - 5 DR')

    # Example of using a specific timestamp
    specific_time = get_timestamp_from_string('2023-01-01 12:00:00')
    if specific_time:
        set_directory_timestamp('/path/to/directory', specific_time)
