import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


def plot_heatmap(tau_matrix, file_to_plot='', show=False):
    """

    :param tau_matrix: A square numpy matrix containing the data to be plotted
    :param file_to_plot: If a file name is specified the heatmap will be saved
    :param show: If True the heatmap will be shown
    :return:
    """

    x_min = 0
    y_min = 0
    x_max = tau_matrix.shape[0]
    y_max = tau_matrix.shape[1]

    if x_max != y_max:
        print('The Heatmap function expects a square matrix')
        return -1

    # Create the meshgrid
    x = np.arange(x_min, x_max + 1, 1)
    y = np.arange(y_min, y_max + 1, 1)

    x_values, y_values = np.meshgrid(x, y)
    z_values = tau_matrix

    # Now do the plotting

    cutoff = 1

    fig, ax = plt.subplots()
    ax.set_aspect('equal')

    colors = [(0, '#ffffff'),
              (1, '#ff0000')]

    cmap = LinearSegmentedColormap.from_list("colormap", colors=colors, N=256)

    cm = ax.pcolormesh(x_values, y_values, z_values, vmin=np.amin(z_values), vmax=np.amax(z_values) * cutoff, cmap=cmap)
    ax.invert_yaxis()
    plt.colorbar(cm)
    plt.axis('off')

    if show:
        plt.show()

    if file_to_plot != "":
        try:
            fig.savefig(file_to_plot, bbox_inches='tight')
        except IOError:
            print(f'Invalid file name to plot: {file_to_plot}')
    plt.close()
    return 0


if __name__ == '__main__':
    tau_file = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/heatmaptest-1.xlsx'
    tau_df = pd.read_excel(tau_file, index_col=0)

    # Sometimes these 2 columns have crept in for a not fully understood reason
    tau_df.drop(['Unnamed: 0', 'index'], inplace=True, axis=1, errors='ignore')
    tau_matrix = tau_df.to_numpy()
    plot_heatmap(tau_matrix, show=True)
