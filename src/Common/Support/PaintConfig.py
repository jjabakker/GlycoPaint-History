import os
import json

from src.Common.Support.DirectoriesAndLocations import get_paint_defaults_file_path

paint_configuration = None

# Load configuration from a JSON file
def load_paint_config(file_path):

    global paint_configuration

    if paint_configuration is not None:
        return paint_configuration

    if file_path is None:
        file_path = os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json')
    try:
        with open(file_path, 'r') as config_file:
            paint_configuration = json.load(config_file)
        return paint_configuration
    except FileNotFoundError:
        print("Error: Configuration file {} not found.".format(file_path))
        #paint_logger.error("Error: Configuration file {} not found.".format(file_path))
        return None
    except json.JSONDecodeError:
        #paint_logger.error("Failed to parse JSON from {}.".format(file_path))
        print("Failed to parse JSON from {}.".format(file_path))
        return None


def get_paint_attribute(application,  attribute_name):
    config = load_paint_config(get_paint_defaults_file_path())
    if config is None:
        return None
    else:
        application = config.get(application)
        value = application.get(attribute_name, None)
        return value

if __name__ == '__main__':


    config = load_paint_config(os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json'))
    trackmate_config = config['TrackMate']
    max_gap1 = trackmate_config['MAX_FRAME_GAP']

    config = load_paint_config(os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json'))
    trackmate_config = config['TrackMate']
    max_gap1 = trackmate_config['MAX_FRAME_GAP']

    i = 1