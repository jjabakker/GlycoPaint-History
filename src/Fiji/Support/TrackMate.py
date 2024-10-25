# -*- coding: utf-8 -*-

# --------------------------------------------------------
# Code adapted from
# https://imagej.net/plugins/trackmate/scripting/scripting
# --------------------------------------------------------

import csv
import os
import sys

import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
from fiji.plugin.trackmate import (
    Logger,
    Model,
    SelectionModel,
    Settings,
    TrackMate)

from fiji.plugin.trackmate.action import CaptureOverlayAction
from fiji.plugin.trackmate.detection import LogDetectorFactory
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui.displaysettings.DisplaySettings import TrackMateObject
from fiji.plugin.trackmate.tracking.jaqaman import SparseLAPTrackerFactory
from fiji.plugin.trackmate.util import LogRecorder
from ij import WindowManager
from ij.io import FileSaver
from java.lang.System import getProperty

paint_dir = getProperty('fiji.dir') + os.sep + "scripts" + os.sep + "Plugins" + os.sep + "Paint"
sys.path.append(paint_dir)

from FijiSupportFunctions import fiji_get_file_open_write_attribute
from LoggerConfig import paint_logger


def excute_trackmate_in_Fiji(recording_name, threshold, tracks_filename, image_filename):
    print("\nProcessing: " + tracks_filename)

    # We have to do the following to avoid errors with UTF8 chars generated in
    # TrackMate that will mess with our Fiji Jython.
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # ----------------------------
    # Create the model object now
    # ----------------------------

    # Some of the parameters we configure below need to have
    # a reference to the model at creation. So we create an
    # empty model now.

    model = Model()
    model.setLogger(Logger.IJ_LOGGER)

    # Get currently selected image
    imp = WindowManager.getCurrentImage()

    # Prepare settings object
    settings = Settings(imp)

    # Configure detector - all important parameters
    settings.detectorFactory = LogDetectorFactory()
    settings.detectorSettings = {
        'DO_SUBPIXEL_LOCALIZATION': False,
        'RADIUS': 0.5,
        'TARGET_CHANNEL': 1,
        'THRESHOLD': threshold,
        'DO_MEDIAN_FILTERING': False,
    }

    # Configure spot filters - Do not filter out any spots
    filter1 = FeatureFilter('QUALITY', 0, True)
    settings.addSpotFilter(filter1)

    # Configure tracker, first set the default, but then override parameters that we know are important
    settings.trackerFactory = SparseLAPTrackerFactory()
    settings.trackerSettings = settings.trackerFactory.getDefaultSettings()

    # These are the important parameters
    settings.trackerSettings['MAX_FRAME_GAP'] = 3
    settings.trackerSettings['LINKING_MAX_DISTANCE'] = 0.6
    settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = 1.2

    # These are default values made explicit
    settings.trackerSettings['ALTERNATIVE_LINKING_COST_FACTOR'] = 1.05
    settings.trackerSettings['SPLITTING_MAX_DISTANCE'] = 15.0
    settings.trackerSettings['ALLOW_GAP_CLOSING'] = True
    settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = False
    settings.trackerSettings['ALLOW_TRACK_MERGING'] = False
    settings.trackerSettings['MERGING_MAX_DISTANCE'] = 15.0
    settings.trackerSettings['CUTOFF_PERCENTILE'] = 0.9

    # Add ALL the feature analyzers known to TrackMate.
    # They will yield numerical features for the results, such as speed, mean intensity etc.
    settings.addAllAnalyzers()

    # Configure track filters - Only consider tracks of 3 and longer.
    filter2 = FeatureFilter('NUMBER_SPOTS', 3, True)
    settings.addTrackFilter(filter2)

    # Instantiate plugin
    trackmate = TrackMate(model, settings)

    # Process
    ok = trackmate.checkInput()
    if not ok:
        paint_logger.error('Routine paint_trackmate - checkInput failed')
        return -1, -1, -1

    ok = trackmate.process()
    if not ok:
        paint_logger.error('Routine paint_trackmate - process failed')
        return -1, -1, -1


    # Get spots data, iterate through each track to calculate the mean square displacement

    track_ids = model.getTrackModel().trackIDs(True)  # True means only return visible tracks
    diffusion_coefficient_list = []
    for track_id in track_ids:

        # Get the set of spots in this track
        track_spots = model.getTrackModel().trackSpots(track_id)

        first_spot = True
        cum_msd = 0
        # Iterate through the spots in this track, retrieve values for x and y (in micron)
        for spot in track_spots:
            if first_spot:
                x0 = spot.getFeature('POSITION_X')
                y0 = spot.getFeature('POSITION_Y')
                first_spot = False
            else:
                x = spot.getFeature('POSITION_X')
                y = spot.getFeature('POSITION_Y')
                cum_msd += (x - x0) ** 2 + (y - y0) ** 2
        msd = cum_msd/ (len(track_spots) - 1)
        diffusion_coefficient = msd / (2 * 2 * 0.05)

        nice_diffusion_coefficient = round(diffusion_coefficient * 1000000, 0)
        diffusion_coefficient_list.append(nice_diffusion_coefficient)

    # ----------------
    # Display results
    # ----------------

    # A selection.
    selection_model = SelectionModel(model)

    # Read the default display settings.
    ds = DisplaySettingsIO.readUserDefault()
    ds.setTrackColorBy(TrackMateObject.TRACKS, 'TRACK_DURATION')

    displayer = HyperStackDisplayer(model, selection_model, imp, ds)
    displayer.render()
    displayer.refresh()

    # ---------------------------------------------------
    # Save the image file with image with overlay as tiff
    # ---------------------------------------------------

    image = trackmate.getSettings().imp
    tm_logger = LogRecorder(Logger.VOID_LOGGER)
    capture = CaptureOverlayAction.capture(image, -1, 1, tm_logger)
    FileSaver(capture).saveAsTiff(image_filename)

    # The feature model, that stores edge and track features.
    feature_model = model.getFeatureModel()

    # ----------------
    # Write the Tracks file
    # ----------------

    fields = ["RECORDING NAME", "LABEL", "NUMBER_SPOTS", "TRACK_DURATION", 'TRACK_X_LOCATION', 'TRACK_Y_LOCATION', 'DIFFUSION_COEFFICIENT']

    # Determine write attributes
    open_attribute = fiji_get_file_open_write_attribute()

    # Iterate over all the tracks that are visible.
    with open(tracks_filename, open_attribute) as csvfile:

        # Need to write three empty line to maintain compatability with the Trackmate generated CSV file
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        csvwriter.writerow('         ')
        csvwriter.writerow('         ')
        csvwriter.writerow('         ')

        track_index = 0
        for track_id in model.getTrackModel().trackIDs(True):
            # Fetch the track feature from the feature model.
            label = 'Track_' + str(track_id )
            duration = round(feature_model.getTrackFeature(track_id, 'TRACK_DURATION'), 3)
            spots = feature_model.getTrackFeature(track_id, 'NUMBER_SPOTS')
            x = round(feature_model.getTrackFeature(track_id, 'TRACK_X_LOCATION'), 2)
            y = round(feature_model.getTrackFeature(track_id, 'TRACK_Y_LOCATION'), 2)

            # Write the record for each track
            csvwriter.writerow([recording_name, label, spots, duration, x, y, diffusion_coefficient_list[track_index]])
            track_index += 1

    model.getLogger().log('Found ' + str(model.getTrackModel().nTracks(True)) + ' tracks.')

    nr_spots = model.getSpots().getNSpots(True)  # Get visible spots only
    all_tracks = model.getTrackModel().nTracks(False)  # Get all tracks
    filtered_tracks = model.getTrackModel().nTracks(True)  # Get filtered tracks

    return nr_spots, all_tracks, filtered_tracks
