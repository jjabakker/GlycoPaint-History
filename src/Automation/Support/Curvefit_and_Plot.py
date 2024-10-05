import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import OptimizeWarning
from scipy.optimize import curve_fit
from src.Automation.Support.Logger_Config import logger


def ReadTrackMateData(csvfilename, istrack):
    """
    Function is not to be called externally, but by ReadTracksData or ReadSpotsData
    Read in the data file (it can be either 'tracks' or 'spots').
    Row 0 contains the header.
    Rows 1, 2 and 3 contain commentary, so skip those.
    :param csvfilename:
    :param istrack: A boolean value indicating whether it is tracks data (True) or spots data (False)
    :return: the dataframe with tracks
    """

    try:
        tmd = pd.read_csv(csvfilename, header=0, skiprows=[1, 2, 3])
    except FileNotFoundError:
        logger.error(f'Could not open {csvfilename}')
        sys.exit()
    except:
        logger.error(f'Problem parsing {csvfilename}')
        sys.exit()

    # Drop unused columns for 'tracks' data or 'plots' data
    try:
        if istrack:
            tmd.drop(['NUMBER_SPLITS', 'NUMBER_MERGES', 'TRACK_Z_LOCATION',
                      'NUMBER_COMPLEX'], axis=1, inplace=True)
        else:
            tmd.drop(['POSITION_Z', 'MANUAL_SPOT_COLOR'], axis=1, inplace=True)
        return tmd
    except KeyError:
        logger.error(f'Unexpected column names in {csvfilename}')
        sys.exit()


def ReadTracksData(csvfilename):
    """
    :param csvfilename:
    :return:
    """

    return ReadTrackMateData(csvfilename, istrack=True)


def monoExp(x, m, t, b):
    # Define the exponential decay function that will be used for fitting
    try:
        calc = m * np.exp(-t * x) + b
    except OverflowError:
        logger.error(f"Overflow error in monoExp: m = x = {x}, {m}, t = {t}, b = {b}")
        calc = 0
    return calc


def CompileDuration(tracks):
    """
    The function produces a histogram
    :param tracks: a dataframe containing the histogram data
    :return: a dataframe containing the histogram
    """

    duration_data = tracks.groupby('TRACK_DURATION')['TRACK_DURATION'].size()

    # histdata is returned as a Pandas Series, make histdata into a dataframe
    # The index values are the duration and the first (and only) column is 'Frequency'
    histdata = pd.DataFrame(duration_data)
    histdata.columns = ['Frequency']
    return histdata


def CurveFitAndPlot(plot_data, nr_tracks, plot_max_x, plot_title='Duration Histogram', file="", plot_to_screen=True,
                    verbose=True):
    """
    :param plot_data:
    :param nr_tracks
    :param plot_max_x: the maximum x value visible in the plot
    :param plot_title: optional title for histogram plot
    :param file:
    :param plot_to_screen:
    :param verbose:
    :return: nothing
    """

    # Convert the pd dataframe to Numpy arrays fur further curve fitting

    x = list(plot_data.index)
    x = np.asarray(x)

    y = list(plot_data["Frequency"])
    y = np.asarray(y)

    # Perform the fit
    p0 = (2000, 4, 10)  # this is more what we see

    try:
        params, cv = curve_fit(monoExp, x, y, p0)
        m, t, b = params
    except ValueError:
        if verbose:
            logger.error('CurveFitAndPlot: ydata or xdata contain NaNs, or incompatible options are used')
        return -2, 0
    except RuntimeError:
        if verbose:
            logger.warning('CurveFitAndPlot: The least-squares optimisation fails')
        return -2, 0
    except OptimizeWarning:
        if verbose:
            logger.warning('CurveFitAndPlot: Covariance of the parameters can not be estimated')
        return -2, 0

    tauSec = (1 / t)

    # Determine quality of the fit
    squaredDiffs = np.square(y - monoExp(x, m, t, b))
    squaredDiffsFromMean = np.square(y - np.mean(y))
    if np.sum(squaredDiffsFromMean) == 0:
        rSquared = 0
    else:
        try:
            rSquared = 1 - np.sum(squaredDiffs) / np.sum(squaredDiffsFromMean)
        except (OptimizeWarning, RuntimeError, RuntimeWarning):
            logger.warning('CurveFitAndPlot: OptimizeWarning, RuntimeError, RuntimeWarning')
            rSquared = 0

    fig, ax = plt.subplots()
    ax.plot(x, y, linewidth=1.0, label="Data")
    ax.plot(x, monoExp(x, m, t, b), linewidth=1.0, label="Fitted")

    x_middle = plot_max_x / 2 - plot_max_x * 0.1
    y_middle = y.max() / 2
    plt.text(x_middle, y_middle, f"Tau = {tauSec * 1e3:.0f} ms")
    plt.text(x_middle, 0.8 * y_middle, f"R2 = {rSquared:.4f} ms")
    plt.text(x_middle, 0.6 * y_middle, f"Number or tracks is {nr_tracks}")
    plt.text(x_middle, 0.4 * y_middle, f"Zoomed in from 0 to {plot_max_x:.0f} s")

    plt.xlim([0, plot_max_x])

    ax.set_xlabel('Duration [in s]')
    ax.set_ylabel('Number of tracks')
    ax.set_title(plot_title)
    ax.legend()

    # Plot to screen per default, but don't when it has been overriden
    # Plot to file when a filename has been specified

    if plot_to_screen:
        plt.show()
    if file != "":
        fig.savefig(file)
        if verbose:
            logger.debug("\nWriting plot file: " + file)

    # Inspect the parameters
    if verbose:
        print("")
        print(f'R² = {rSquared:.4f}')
        print(f'Y = {m:.3f} * e^(-{t:.3f} * x) + {b:.3f}')
        print(f'Tau = {tauSec * 1e3:.0f} ms')

    plt.close()
    tauSec *= 1000
    return tauSec, rSquared
