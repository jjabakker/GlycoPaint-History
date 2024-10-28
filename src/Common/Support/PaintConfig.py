import os
import json

class PaintConfiguration:
    _instance = None
    paint_conf_data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PaintConfiguration, cls).__new__(cls)
            cls.paint_conf_data = load_paint_config(os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json'))
        return cls._instance


# Load configuration from a JSON file
def load_paint_config(file_path):
    try:
        with open(file_path, 'r') as config_file:
            config = json.load(config_file)
        return config
    except FileNotFoundError:
        print("Error: Configuration file {} not found.".format(file_path))
        #paint_logger.error("Error: Configuration file {} not found.".format(file_path))
        return None
    except json.JSONDecodeError:
        #paint_logger.error("Failed to parse JSON from {}.".format(file_path))
        print("Failed to parse JSON from {}.".format(file_path))
        return None


if __name__ == '__main__':


    paint_config1 = PaintConfiguration().paint_conf_data
    paint_config2 = PaintConfiguration().paint_conf_data
    paint_config3 = PaintConfiguration().paint_conf_data

    print(paint_config3)

    if paint_config2:

        trackmate_defaults1 = paint_config1['TrackMate']
        trackmate_defaults2 = paint_config2['TrackMate']
        trackmate_defaults3 = paint_config3['TrackMate']

        max_gap1 = trackmate_defaults1['MAX_FRAME_GAP']
        max_gap2 = trackmate_defaults1['MAX_FRAME_GAP']


        config = load_paint_config(os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json'))
        plot = config['Generate Squares']['Plot to File']

        max_gap1 = config['TrackMate']['MAX_FRAME_GAP']

        i = 1