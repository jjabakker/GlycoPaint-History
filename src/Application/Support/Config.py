import json

# Load configuration from a JSON file
def load_paint_config(file_path):
    try:
        with open(file_path, 'r') as config_file:
            config = json.load(config_file)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON from {file_path}.")
        return None

if __name__ == '__main__':

    # Example usage
    paint_config = load_paint_config('/Users/hans/Paint Code Local/src/Config/Paint.json')

     if paint_config:
        plot = paint_config['Generate Squares']['plotfiles']
        print(f"App Name: {paint_config['app_name']}")
        print(f"Logging Level: {paint_config['settings']['logging']['level']}")
        print(f"Feature X Enabled: {paint_config['features']['enable_feature_x']}")
''