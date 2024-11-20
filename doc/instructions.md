# Installation Instructions

&nbsp;<br>
&nbsp;<br>

## Install PyCharm Environment

- Download PyCharm (either the professional or the free community edition) from <https://www.jetbrains.com/pycharm/>
- The version used is PyCharm 2024.2.4 (Professional Edition), but other versions or any other Python development
  environment can also be used

## Create PyCharm project PAINT code

- In PyCharm create a new project (‘Project from version control’) and clone it from the GitHub
  link: <https://github.com/jjabakker/PaintProcessingPipeline.git>

## Configure the PyCharm project

- Select a Python interpreter (used Python 3.13)
- Install the following libraries:
    - pandas (2.2.2)
    - matplotlib (3.9.0)
    - scipy (1.13.1)
    - openpyxl (3.1.5)

## Install Fiji

- Install Fiji from <https://imagej.net/software/fiji/downloads>
- Determine the location of the Fiji application, as 'fiji_app', e.g. /Users/Hans/Applications/Fiji.app
- Ensure that directories 'fiji_app'/scripts/plugins exist (they normally are present)
- You may have to edit the script Install Paint to specify the fiji_app variable (there are a few defaults listed)
- Run the ‘Install Paint.py’ script to copy the following files to the Fiji directory tree:
    - Process_Batch.py
    - Convert_BF_images.py
    - Single_Analysis.py
    - FijiSupportFunctions.py
    - Trackmate.py
    - CommonSupportFunctions.py

- Upon (re)starting Fiji, you should now see in the ‘Plugins’ directory, a ‘Paint’ directory, with Paint-related
  commands.

## Install RStudio

- Follow the instructions on <https://posit.co/download/rstudio-desktop/> to install R and R Studio if needed.

&nbsp;<br>
&nbsp;<br>
&nbsp;<br>
&nbsp;<br>

# Run Instructions

## Download images files

- Request access to example data at <j.j.a.bakker.2@umail.leidenuniv.nl>
- Download
  the [example images](https://leidenuniv1-my.sharepoint.com/:f:/g/personal/bakkerjja1_vuw_leidenuniv_nl/ElwN30klq2JMukmqwy84B-MBJ8hTRBj1Ckg0bUJLCMAfoA?e=9rDTdZ)
  to a local image directory, e.g. ~/PaintExample/Images/240402

## Create the batch file

The batch file contains information about the images to be analysed. For each experiment, the images are stored in
separate directories.

- Create a Paint directory, e.g. ~/ PaintExample/Paint/240242
- From PyCharm, run ‘src/Automation/Grid/Prepare Batch File’
    - Specify as image directory: ~/ PaintExample/Images/240402 (this directory contains the files to be analysed).
    - Specify as paint directory: ~/ PaintExample/Paint/240242 (in this directory the batch.csv file will be created).
- A batch file ‘batch.csv’ is created in the paint directory
- Provide the missing details (Probe, Probe Type, Adjuvant, Cell Type). An example of a batch file is provided. Note
  that the name batch.csv is mandatory.

## Run Trackmate

The Fiji plugin Trackmate detects spots on each frame and connects spots on subsequent frames to form tracks. Data is
written in the paint directory.

- Start Fiji
- Run Plugins – Paint – Grid – Grid Process Batch
- Specify as Paint directory: ~/ PaintExample/Paint/240402
- Specify as Image directory: ~/ PaintExample/Images/240402

## Transform Brightfield images

The image viewer can not handle the original Nikon nd2 format, so with the use of Fiji the nd2 brightfield images are
converted to jpg format.

- Start Fiji
- Run Plugins – Paint – Grid – Convert BF Images
- Specify as Paint directory: ~/ PaintExample/Paint/240402
- Specify as Image directory: ~/ PaintExample/Images/240402

## Process All Images

With the tracks information available, the square processing can now take place. The image is divided into 20x20 squares
and after quality control of individual squares, the Tau of the tracks in the square are calculated by curve fitting of
the track duration histogram.

The following default parameters are used (which can be overridden in the Image Viewer:

- Connectivity: Free
- Min Density Ratio: 2
- Max Variability: 10

The procedure to run 'Process All Images':

- Start PyCharm
- Run ‘src/Automation/Grid/Process All Images’
- Specify as Paint directory: ~/ PaintExample/Paint/240402
- Select parameters. Reasonable defaults are
    - Nr of Squares in row/col: 20
    - Minimum tracks to calculate Tau: 30
    - Min allowable R-squared: 0.9
    - Min density ratio: 2
    - Max variability: 10
    - Max squares coverage: 20

## Run Image Viewer

The Image Viewer allows the user to inspect how squares have been generated on the images. Values for connectivity, min
density rati and maximum variability can be adjusted.

- Start PyCharm
- Run ‘src/Automation/Grid/Image Viewer’
- Specify as Paint directory: ~/PaintExample/Paint/240402

## Run Compile Results

In this step the square data of the various experiments are compiled in an 'All Squares' file. This file contains all
the information to generate graphical output with R-Studio.

- Start PyCharm
- Run ‘src/Automation/Grid/Compile Results’
- Specify as Paint directory: ~/PaintExample/Paint/

## Process numerical output with scripts in R Studio

Several scripts are provided to analyse the numerical output. The lines where the data files are read in will need to be
edited to properly reflect the source location.

&nbsp;<br>
&nbsp;<br>
&nbsp;<br>
&nbsp;<br>

# Detailed Information

## Image file formats

The pipeline assume that files are in Nikon's .nd2 format and will check for the .nd2 file extension. Fiji and Trackmate
however process files in the more generic tiff format also and the software can be easily adjusted.

## File naming convention

The convention for experiment filenames used in this version of the software is described by the following regular
expression: '\d{6}-Exp-d{1,2}-[AB][1234]-\d{1,2}'

In plain words:

- 6 digits (representing a date): indicating the experiment date
- A text string '-Exp-' (for Experiment)
- A number of 1 or 2 digits: indicating the experiment number
- An 'A' or a 'B': indicating the row of the microscope tray
- A number 1, 2, 3 or 4: indicating the column of the microscope tray
- A text string '-'
- A number of 1 or 2 digits: indicating the Experiment Seq Nr

If the filenames comply with this format, part of the batch file information is filled in automatically; if not, more
manual data entry is required.

## Batch file format

Using example file name: 240623-Exp-1-A1-3

- Recording Sequence Nr:    A simple sequential number
- Experiment Date:        '240623' (Retrieved from the image name or specified)
- Experiment Name:        '240623-Exp-1' (Retrieved from the image name or specified)
- Condition Nr:            '1' (Retrieved from the image name or specified)
- Replicate Nr:            '3' (Retrieved from the image name or specified)
- Recording Name:            '240623-Exp-1-A1-3' (The image name as found in the directory)
- Probe:                    A user specified text string
- Probe Type:                A user specified text string. In this experiment ‘simple’ or ‘epitope’
- Cell Type:                A user specified text string
- Adjuvant:                    A user specified text string
- Concentration:        A user specified number

## Directory structure

In the example directory structure there is one experiment shown (240402), which contains four images (
240402-Exp-6-B2-4-threshold-10, ...).
For each image four directories are (automatically) created:

- the 'tracks' directory contains the numerical information generated by Trackmate
- the 'img' directory contains the graphical tracks information
- the 'grid' directory contains information about the squares in the images
- the 'plots' directory contains the curve fitting information

Under each image directory an 'Output directory' is created in which the 'All Batches', 'All Squares' and 'Batch
Summary' files are written.

Paint Directory &nbsp; <br>
&nbsp;&nbsp; 240402 &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 240402-Exp-6-B2-4-threshold-10 &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; tracks &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; img &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; grid &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; plt &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 240402-Exp-3-A3-1-threshold-10 &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; tracks &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; img &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; grid &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; plt &nbsp; <br>&nbsp;&nbsp;&nbsp; 240402-Exp-1-A1-3-threshold-10
&nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; tracks &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; img &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; grid &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; plt &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 240402-Exp-1-A1-1-threshold-10 &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; tracks &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; img &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; grid &nbsp; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; plt &nbsp; <br>
&nbsp;&nbsp; Output &nbsp; <br>