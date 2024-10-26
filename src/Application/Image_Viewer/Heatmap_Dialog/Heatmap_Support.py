import sys
import matplotlib.pyplot as plt
import math

from src.Common.Support.LoggerConfig import paint_logger

heatmap_modes = {
    1: 'Tau',
    2: 'Density',
    3: 'Mean DC',
    4: 'Max Track Duration',
    5: 'Total Track Duration'
}

# Function to convert RGB to HEX format
def _rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

# Generate colors from a colormap
def get_colormap_colors(cmap_name, num_colors):
    cmap = plt.get_cmap(cmap_name)
    return [_rgb_to_hex(cmap(i / num_colors)) for i in range(num_colors)]


def get_color_index(var, var_max, var_min, nr_levels):
    if var < 0:
        var = 0
    if var_max == var_min:
        return 0
    index = math.floor(var * nr_levels / (var_max - var_min))
    if index == nr_levels:
        index -= 1
    return index


def get_heatmap_data(df_squares, df_all_squares, heatmap_mode, experiment_min_max=True):

    heatmap_modes = {
        1: 'Tau',
        2: 'Density',
        3: 'Mean DC',
        4: 'Max Track Duration',
        5: 'Total Track Duration'
    }

    if df_all_squares.empty or df_squares.empty:
        paint_logger.error("Function 'display_heatmap' failed - No data available")
        sys.exit()

    if heatmap_mode in heatmap_modes:
        column_name = heatmap_modes[heatmap_mode]

        if experiment_min_max:
            heatmap_data = df_all_squares[column_name]
            min_val = df_all_squares[column_name].min()
            max_val = df_all_squares[column_name].max()
        else:
            heatmap_data = df_squares[column_name]
            min_val = df_squares[column_name].min()
            max_val = df_squares[column_name].max()
        min_val = max(min_val, 0)

        # There can be Nan values in the data, so we need to replace them
        heatmap_data = heatmap_data.fillna(0)

        # Sort on square number
        heatmap_data = heatmap_data.sort_index()

        # if heatmap_mode == 3:
        #     min_val = round(min_val/1000, 1)
        #     max_val = round(max_val/1000, 1)
        #     heatmap_data /= 1000
        #   heatmap_data.loc[heatmap_data['Mean DC'] < 0, 'Mean DC'] = -1

    else:
        paint_logger.error("Function 'display_heatmap' failed - Unknown heatmap mode")
        sys.exit()

    return heatmap_data, min_val, max_val
