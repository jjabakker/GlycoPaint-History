import tkinter as tk
import matplotlib.pyplot as plt
import math
from matplotlib.pyplot import minorticks_off
from pyparsing import make_xml_tags


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
    index = math.floor(var * nr_levels / (var_max - var_min))
    if index == nr_levels:
        index -= 1
    return index



if __name__ == "__main__":

    # Tkinter setup
    root = tk.Tk()
    canvas = tk.Canvas(root, width=400, height=600)
    canvas.pack()

    # Generate 10 shades of a color using a colormap (e.g., 'Blues')
    colors = get_colormap_colors('Blues', 20)

    # Draw rectangles with different shades of blue
    for i, color in enumerate(colors):
        canvas.create_rectangle(50, 50 + i*20, 350, 80 + i*20, fill=color, outline='black')

    root.mainloop()