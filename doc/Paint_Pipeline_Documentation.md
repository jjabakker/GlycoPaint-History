<div style="text-align: center;"> 
<span style="font-size: 72px;">GlycoPaint Pipeline</span>

<span style="font-size: 36px;">Functional description</span>

</div>



<figure style="text-align: center;">
  <img src="Images/paint_logo.png" alt="Image Description" width="500">
</figure>


<br>
<br>

<div style="text-align: center;"> 
November 2024
</div>

<br>
<br>

# Overview - The Dataflow in the GlycoPaint pipeline

Cells are observed under a microscope for 100 seconds capturing 2000 images during this interval. Bright spots, which  represent fluorophores, are visible in these images. These spots may move and often disappear after a short period. Their appearance signifies that a fluorophore has remained stationary long enough to be detected by the camera. In the GlycoPaint method, such events are interpreted as glycans (attached to fluorophores) binding to lectins on the cell surface. A key challenge is distinguishing these biologically relevant events from non-specific fluorophore sticking.

With the Fiji plugin TrackMate, spots are detected in each frame, and their positions registered. Tracks are then created by connecting spots across consecutive frames. Each track is characterised by features such as its duration, average x and y positions, and distance travelled. If a lectin-glycan pair were completely stationary, the resulting track would consist of a series of spots in the same location, with no movement. However, lectin-glycan pairs typically move slightly within the cell membrane, resulting in tracks that resemble small 'wriggles'. These tracks  are not evenly distributed across the image but are typically concentrated on the cell surface and show heterogeneous patterns within a cell.

An average recording may contain around 800,000 spots, from which approximately 50,000 tracks are constructed. A grid is then overlaid on the recording, commonly using a 20x20 or 30x30 grid, dividing the image into 400 or 900 squares. Each track, based on its x and y coordinates, is assigned to a square. Diving the image into squares allows for the investigation of differences between cells or between regions within a cell.

In the GlycoPaint pipeline, the primary unit of analysis is not an individual recording but a set of recordings grouped into an Experiment. Data processing generates two main datasets:

- **All Squares**: A table containing summarised information on all tracks across all recordings in the experiment.

- **All Tracks**: A table containing detailed information on every track in the experiment.

Both datasets serve as the foundation for further analysis.

A lot of data is generated. For an experiment with 14 recordings and a 20x20 grid, the All Squares table would contain 5600 rows (or 12,600 rows for a 30x30 grid) and the All Tracks table might contain between 100,000 and 400,000 rows.

The scope of the GlycoPaint pipeline is to extract information from the Recordings and to extract the maximum amount of meaningful summary information from the images for subsequent processing.

Important features of the pipeline are that the results are fully reproducible, require minimal user intervention and  are efficient in terms of processing time and

# Pipeline Concepts

The Paint Pipeline was developed to analyse (bulk) data from Glyco-PAINT experiments. The interaction of weak-binding ligands to receptors on live cells is studied on varying cell types, ligands and adjuvants. Binding events show up as bright spots under a fluorescent microscope. Analysis of the location and duration of spots reveal information about  single binding events.

**Recording**

The central concept in PAINT is the recording of binding events. A recording  consists of a brightfield image to identify the position of cells and a multi-frame image in which the spots, indicative of binding events, are recorded. In our experiments, we observe cells for 100 seconds, with 2000 frames at 50 milli-second intervals.

**Experiment**

A set of recordings is referred to as an experiment. Typically, an experiment is conducted in one day, with up to 100 individual recordings. Normally, several conditions are studied in an experiment
and several replicates are recorded for each condition.

**Project**

A project is a set of experiments, that together are analysed.  Experiments in a project may be replicates of earlier conducted experiments or introduce new combinations of cell types, probes or adjuvants.

For example, a hierarchy is shown of a project consisting of two experiments, with 4 recordings each.

**Metadata**

For recordings metadata needs to be provided for the Paint pipeline to work. On top of that, a simple convention for naming the recordings is used. For example, from the name '240116-Ex1-1-A1-1', the following can be derived:

- <u>240116</u>-Exp-1-A1-1: Part of experiment 240116
- 240116-Exp-<u>1</u>-A1-1: Operating condition 1
- 240116-Exp-1-<u>A1</u>-1: Microscopic plate well A1
- 240116-Exp-1-A1-<u>1</u>: Replicate 1

# Process Flow

## Overview

<figure style="text-align: center;">
  <img src="Images/process_flow.png" alt="Paint Process" width="300">

</figure>

The GlycoPaint process starts with a **microscopy experiment**, in which binding events are observed under a fluorescent microscope. Such an experiment leads to a set of recordings,
each consisting of a bright field image and a multi-frame image.

The user subsequently prepares the **Experiment Info** by providing metadata for the recordings. The metadata specifies properties such as Cell Type, Probe Type, Concentration and Adjuvant and provides some necessary processing parameters.

The experiment data is analysed in **TrackMate** which detects spots in each frame of the multi-frame set and connects these spots into tracks where appropriate. A track represents a binding event with the length of the track indicating the duration of the binding event.

With the tracks available, the **Generate Squares** step overlays a fine grid of squares over each recording, establishing the properties of each of the squares, for example, whether the square covers an area of interest or likely background.

**Compile Project** combines all available data into large data tables containing all information of interest.

These tables are used in the **R Analysis** phase where the data is selected, processed and presented in line with research objectives.

**Visual Inspection** of the results is possible at any time after the squares have been generated, both recordings in an experiment or allrecordings in a project.

## Prepare Experiment Info

The metadata of the experiment is information about the conditions under which each recording is made and recorded in an 'Experiment Info' file. The Paint processing pipeline contains a 'Prepare Experiments Info' utility to prepare this file. The user provides two parameters: the directory that contains the recordings and the location of the Paint Experiment directory where the Experiment Info file (and all subsequent data) will be written.

<figure style="text-align: center;">
  <img src="Images/prepare_experiments_info_dialog.png"  width="500">
</figure>

After this has been done for both demo experiments, two directories have been created each with an 'Experiment Info' file.

<figure style="text-align: center;">
  <img src="Images/demo_after_prepare_exepriment.png"  width="350">
</figure>

If the Paint file naming convention is used, columns such as Experiment Date, Experiment Name, Condition Nr and Replicate Nr will be filled in automatically, if not the user has to provide this information manually.

<figure style="text-align: center;">
  <img src="Images/empty_experiments_info.png"  width="800">
</figure>

An example of a fully specified Experiment Info file, with values for Probe, Probe Type, Cell Type, Adjuvant and Concentration provided is shown below. The Threshold parameter is necessary for TrackMate processing (refer to next section). The 'Process' flag indicates whether a recording is processed or ignored.

<figure style="text-align: center;">
  <img src="Images/experiments_info_with_metadata.png"  width="800">
</figure>

The 'Brightfield Images' directory holds JPG versions of the Brightfield images, converted from the original Nikon '.nd2' format. These files  will be needed later in the Visual Inspection phase.

## Run TrackMate

The Trackmate plugin in the Fiji environment is used to analyse the recordings, detect spots and connect spots to tracks where possible.

The Experiment info 'Threshold' parameter determines the spot detection sensitivity. With a low threshold value, even not very well-defined  spots are detected. With a high threshold value, poorly defined spots are ignored. Experience indicates that with 1,000,000 plus spots, processing becomes very lengthy and does not lead to usable results. The user chooses for each recording a threshold value in an iterative process. The threshold should be set so that the number of spots preferably is in the 300,000 to 800,000 range. A good starting value for the Threshold is 20.

The 'Run Trackmate' procedure is started from Fiji by selecting from the 'Plugins' menu the Paint group and in there 'Run Trackmate'. A dialog box to select the Recordings Directory and Experiment Directory is displayed.

<figure style="text-align: center;">
  <img src="Images/run_trackmate_dialog.png"  width="500">
</figure>



Upon successful processing, the system generates for each recording an image. A representative example of an image is shown below.

<figure style="text-align: center;">
  <img src="Images/sample_recording.png"  width="500">
</figure>


For the set of recordings in the experiment, the system generates one 'All Tracks' and one 'All Recordings' file with attributes such as Nr Spots, Nr Tracks, Run Time and a Time Stamp. The 'All Tracks' file contains, for every track, the average x and y position, and the number of spots and track duration. In addition, the diffusion coefficient (a measure of the displacement from the origin) has been calculated. An example is shown below.

<figure style="text-align: center;">
  <img src="Images/experiments_info_after_generate_squares.png"  width="800">
</figure>

The Project directory contents just after TrackMate has been run for the 241116 experiment is shown below.

<figure style="text-align: center;">
  <img src="Images/demo_project_after_trackmate.png"  width="350">
</figure>

## Generate Squares

With the tracks for the experiment available in the 'All Tracks' file, the recordings in the Exepriment folder (or for all experiments in a Project folder) are analysed by superimposing a grid over the image and determining the characteristics of each square. The user interface to invoke this function is shown below.

<figure style="text-align: center;">
  <img src="Images/generate_squares.png"  width="700">
</figure>

The Number of Squares in a Row (and Column) determines the size of the squares in the grid (typical values are 20 or  30). The number of tracks is determined for each square. The 10% least dense squares determin a 'background' density. All square densities are compared to this background density. If the ratio exceeds the 'Minimum Required Density  Ratio', squares are interpreted to be sufficiently distinct from the background to be of interest. 

The homogeneity of squares is also determined and, if requested, the lack of homogeneity, i.e., the variability, can be limited.

A histogram of track durations is generated for each square that meets the specified density and variability criteria. Tau is then calculated through curve fitting. To ensure accurate curve fitting, a minimum number of data points (tracks) is required. The user can define this threshold with the 'Minimum Tracks to Calculate Tau' parameter.

The quality of curve fitting is expressed in an R<sup>2</sup> parameter. An R<sup>2</sup> value of 1 indicates a perfect fit, values lower than 0.5 that a fit was difficult. The user-specified 'Min allowable R-squared' parameter sets a limit to how the required quality of fit.

For all squares in each recording, several attributes are calculated:

- The number of tracks
- The duration of the longest track
- The average duration of the longest 10 tracks
- The total track duration
- The Tau (provided that the squares meet the selection criteria
- The R<sup>2</sup> indicating the quality of the Tau curve fitting

With the 'Generate Squares' function run, the directory structure is
shown below.

<figure style="text-align: center;">
  <img src="Images/demo_project_after_generate_squares.png"  width="350">
</figure>

## Compile Project

Typically, data to be analysed comes from more than one experiment. With the Compile project option (Figure 11), the data from the experiments in the project are compiled and an 'All Recordings', 'All Squares' and 'All Tracks' file is generated (Figure 12).

<figure style="text-align: center;">
  <img src="Images/compile_project_dialog.png"  width="700">
</figure>

<figure style="text-align: center;">
  <img src="Images/demo_project_after_compile.png"  width="350">
</figure>

## Visual Inspection

Once the squares are generated, the results can be reviewed in the Image Viewer. A straightforward dialogue enables the selection of the Project or Experiment directory.

<figure style="text-align: center;">
  <img src="Images/select_viewer_dialog.png"  width="700">
</figure>

The Viewer dialogue appears, showing on the left the image with tracks and squares, and on the right the corresponding bright field image. Through scroll buttons at the bottom (or the combo box immediately under the 'Squares' window, different recordings can be selected. Information on the recording in view is displayed below the 'Squares' window.

Metadata of the recording in view is displayed below the Squares image. To better view the underlying cells and tracks, keyboard options allow toggling between showing squares or not(key 't') or showing numbers or not (key 'n').

<figure style="text-align: center;">
  <img src="Images/recording_viewer.png"  width="900">
</figure>

### Select Recordings

The 'Select Recordings' dialogue allows users to narrow down the recordings being viewed. In the example provided, recordings are available for two Cell Types and Probes. If the user is only interested in CHO-MR recordings, they can select 'CHO-MR,' then click 'Filter' followed by 'Apply All Filters' to display only the relevant recordings. 'Reset All' undoes any selections previously made.

<figure style="text-align: center;">
  <img src="Images/select_recordings.png"  width="900">
</figure>

### Select Squares

The selection of squares of interest for each recording can be adjusted using the Select Squares dialogue. Sliders enable you to set the values for Max Allowable Variability, Min Required Density, and Min and Max Track Duration. Squares that no longer meet the selection criteria will disappear, while those that meet them will appear.

The 'Neighbour' mode defines limitations in the spatial distribution of squares. There are no restrictions in 'Free' mode; in 'Relaxed' mode, squares must touch at least at the corners; and in 'Restricted' mode, they must be adjacent along the edges. The 'Set All' button applies the current selection criteria to all recordings in the set.

Changes made are reflected in the 'All Recordings' date. The Recording Viewer dialogue has three options 'Always Save', 'Never Save' and 'Ask to Save' that determine if the changes are saved or not when the user closes the Recording Viewer.

<figure style="text-align: center;">
  <img src="Images/select_squares_dialog.png"  width="900">
</figure>

### Define Cells

In the Define Cells dialogue it is possible to assign squares to cells. The user selects squares by drawing a rectangle with the mouse, selecting a cell (colour) and pressing 'Assign'. The 'Toggle' function, which can also be invoked by pressing 't', switches between the heatmap and regular display.

Any changes made will be saved in the 'All Squares' file, depending on the selected save options.

<figure style="text-align: center;">
  <img src="Images/define_cells_dialog.png"  width="900">
</figure>

### Show Heatmap

The Heatmap dialogue allows properties of squares to be viewed relative to each other. Five properties are available: Tau, Density, Average Diffusion Coefficient, Max Track Duration and Cumulative Track Duration. A colour range of 20 steps is used to display values. The minimum and maximum value is limited to the current recording unless the 'global' option is checked and the minimum and maximum are determined for the current set of recordings.

Whilst the Heatmap dialogue is displayed, the user can scroll through images.

<figure style="text-align: center;">
  <img src="Images/heatmap_dialog.png"  width="800">
</figure>

The 'Toggle' function, which can also be invoked by pressing 't', switches between the heatmap and regular display.

# Data formats

## All Recordings Format

Holding information on an experiment
<figure style="text-align: center;">
  <img src="Images/all_recordings_format.png" >
</figure>

## All Squares format

Holding information on a single square

<figure style="text-align: center;">
  <img src="Images/all_squares_format.png" >
</figure>

## All Tracks

Holding information on all tracks in a recording


<figure style="text-align: center;">
  <img src="Images/all_tracks_format.png" >
</figure>

# Algorithms

## Tau

Tau is a measure used to characterise the distribution of track durations. To calculate Tau, a frequency distribution is created from the track durations, which, since track durations are multiples of the sample time. The track durations are ordered and fitted with an exponential curve to determine the decay and obtain the Tau value.

All tracks in that square are included in the Tau calculation, but the calculation is performed only if a minimum number of tracks is present. Furthermore, the Tau calculation is only valid if the R<sup>2</sup> value meets or exceeds a specified threshold.

To calculate one Tau for the recording, all tracks within squares that meet the specified selection criteria - such as the minimum required density ratio, maximum allowable variability, minimum and maximum track durations, and neighbour state - are considered.

<figure style="text-align: center;">
  <img src="Images/curve_fitting.png" width="300">
</figure>

## Variability

The variability of a square calculation starts with overlaying a grid over the square and determining the number of tracks in each grid element. The variability is then calculated as the quotient of the standard deviation and the mean of the grid track numbers. In the igure below the variability for four fictional squares is shown.

<figure style="text-align: center;">
  <img src="Images/variability.png" width="1200">
</figure>  

## Square Density

The Square Density is normalised to duration and concentration and is calculated with the following formula:

$$Square\ Density = \frac{Track\ Count}{Area*Duration*Concentration}$$

The area of a square is calculated with the following data: 0.1602804 µm per pixel, 512 pixels in a row (or column).

$$Square\ Area = \left(\frac{0.1602804*512}{Nr\ of\ Squares\ in\ Row} \right)^{2}$$

The Density reported is multiplied by 1000 to make it easier to handle numbers.

## Background Density and Density Ratio

The background 'density' represents the average track count of the lowest 10% of squares with a track count greater than zero. This measure helps distinguish squares with high track counts, likely on the cell surface, from those on the glass. The 'Min Required Density Ratio' - calculated by dividing the track count in a square by the background track count per square - determines which squares are considered of interest.

## Diffusion Coefficient

The diffusion coefficient is calculated for each track in the recording that contains three or more spots, using the following formula. Here, *n* represents the dimensionality (2), and *t* is the time interval over which displacement is measured (0.05 s). The Diffusion coefficient reported is multiplied by 1000 to make it easier to handle numbers.

$$MSD = \sum_{i = 1}^{nr\ spots}{{(x_{i} - x_{0})}^{2} + \ {(y_{i} - y_{0})}^{2}}$$

$$Diffusion\ Coefficient = \frac{MSD}{(2\ *n*t)}$$

# Parameters

The operation of the Paint Pipeline can be tuned with parameters that are kept in 'Paint.json' file.

<figure style="text-align: center;">
  <img src="Images/paint_json.png" width="1200">
</figure>

# Paint directories

The Paint pipeline creates a 'Paint' directory in the user's home directory, with two subdirectories: 'Defaults' and 'Logger'.

In the 'Defaults' directory, a 'Paint.json' holds the parameters that are used by the various components of the Paint pipeline. For regular use, parameters do not need to be changed, but the option to change is provided (but requires detailed insight into the pipeline's operation). The parameters are explained in the next section.

In the 'Logger' directory, the system writes log files, that provide information about the progress of operations in the pipeline and if any difficulties encountered. The log files can be statically viewed with a regular text editor or dynamically with the MacOS Console application.

# Logging
The pipeline provides detailed output on the progress of operations in the pipeline. The log files are written to the 'Logger' directory in the 'Paint' directory. The log files can be viewed with a regular text editor or dynamically with the macOS Console application.

# Structure of Generate Squares

**Generate Squares**

    For all the Experiments in the Project (Process Project)
        For all the Recordings in the Experiment (Process Experiment)
            For all the Squares in the Recording (Process Recording)
                Calculate Square properties (Process Square)

<br>

**Process Project**

1. Start project processing and log the project path.
2. List and sort all experiment directories.
3. For each experiment directory:
    - Skip if it is not a directory or if it's an "Output" directory.
    - Skip if already processed, unless forced by a paint_force flag.
    - Call process_experiment for unprocessed experiments.
4. Return the number of experiments processed.

<br>

**Process Experiment**

1. Initialize variables for tracking and logging.
2. Load tracks and recordings into DataFrames.
3. Validate consistency between tracks and recordings.
4. Log the number of recordings to process.
5. For each recording
    - Retrieve recording details.
    - Call process_recording to process data.
    - Update experiment-level metrics with results from recording.
6. Save updated tracks, recordings, and squares data to files.
7. Log total processing time for the experiment.

<br>

**Process Recording**

1. Initialize processing variables.
2. Loop through all squares in the grid:
    - Calculate square coordinates.
    - Filter tracks within square boundaries.
    - Compute metrics (Tau, Density, Variability, etc.).
    - Append square data to the main DataFrame.
3. Compute the density ratio for the squares.
4. Apply selection filters using select_squares_with_parameters.
5. Label selected squares and propagate labels to tracks.
6. Return processed squares, tracks, and recording-level metrics.

<br>

**Process Square**

1. Calculate square boundaries based on grid coordinates.
2. Filter tracks within the square.
3. If no tracks:
    - Assign default values for metrics (e.g., Tau, Density = 0).
4. If tracks exist:
    - Compute metrics (Tau, R-squared, Density, Variability, etc.).
5. Return a dictionary containing square-level data.
