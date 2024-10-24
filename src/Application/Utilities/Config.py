import os
import json
from src.Common.Support.LoggerConfig import paint_logger

class PaintConfiguration:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PaintConfiguration, cls).__new__(cls)
            cls.config = load_paint_config(os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json'))
        return cls._instance


# Load configuration from a JSON file
def load_paint_config(file_path):
    try:
        with open(file_path, 'r') as config_file:
            config = json.load(config_file)
        return config
    except FileNotFoundError:
        paint_logger.Error(f"Error: Configuration file {file_path} not found.")
        return None
    except json.JSONDecodeError:
        paint_logger.Error(f"Failed to parse JSON from {file_path}.")
        return None


if __name__ == '__main__':


    paint_config1 = PaintConfiguration()
    paint_config2 = PaintConfiguration()

    if paint_config2:
        config = paint_config1.config
        plot = config['Generate Squares']['Plot Files']
        print(f"App Name: {config['App Name']}")
        print(f"Plot Files: {config['App Name']}")


