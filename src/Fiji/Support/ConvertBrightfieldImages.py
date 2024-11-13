import logging
import os
import shutil
import sys

from ij import IJ
from java.lang.System import getProperty

paint_dir = getProperty('fiji.dir') + os.sep + "scripts" + os.sep + "Plugins" + os.sep + "Paint"
sys.path.append(paint_dir)

from LoggerConfig import paint_logger, paint_logger_change_file_handler_name

# Set up logging
paint_logger_change_file_handler_name('Convert BF Images.log')

# Import custom functions for asking the user for directories.
from FijiSupportFunctions import ask_user_for_image_directory


def convert_bf_images(image_source_directory, paint_directory, force=False):
    """
    Convert .nd2 BF images to JPEG and store them in a specified directory.

    Args:
        image_source_directory (str): Directory containing the .nd2 images.
        paint_directory (str): Directory to store the converted JPEGs.
        force (bool): Force overwrite of existing JPEG files, even if up to date.
    """
    # Create a 'Converted BF Images' directory if it doesn't exist
    bf_jpeg_dir = os.path.join(image_source_directory, "Converted BF Images")
    if not os.path.isdir(bf_jpeg_dir):
        os.mkdir(bf_jpeg_dir)

    paint_logger.info('')  # Start logging new run

    count = found = converted = 0
    all_images = sorted(os.listdir(image_source_directory))  # Sort images for predictable processing order

    for image_name in all_images:
        # Skip hidden files or system files
        if image_name.startswith('._'):
            continue

        # Check if the file is a .nd2 file
        if image_name.endswith('.nd2'):
            count += 1

            # Only process Bright Field (BF) images
            if 'BF' in image_name:
                found += 1
                display_name = image_name.ljust(30, ' ')  # Align name in log for readability
                input_file = os.path.join(image_source_directory, image_name)
                output_file = os.path.join(bf_jpeg_dir, image_name.replace('.nd2', '.jpg'))

                # Determine if the image needs to be converted (force flag or file modification check)
                convert = force or not os.path.isfile(output_file) or os.path.getmtime(output_file) < os.path.getmtime(
                    input_file)

                if convert:
                    try:
                        # Open the image using Bio-Formats and save as JPEG
                        nd2_arg = "open=[%s]" % input_file
                        IJ.run("Bio-Formats (Windowless)", nd2_arg)
                        IJ.saveAs("Jpeg", output_file)
                        IJ.getImage().close()  # Close the image after saving
                        paint_logger.info("Image %s was updated.", display_name)
                        converted += 1
                    except Exception as e:
                        paint_logger.error("Error converting %s: %s", display_name, str(e))
                else:
                    paint_logger.info("Image %s does not require updating.", display_name)

    # Log the conversion summary
    paint_logger.info("\nConverted %d BF images, out of %d BF images from %d total .nd2 images.", converted, found,
                      count)

    # Copy the entire 'Converted BF Images' directory to the paint directory
    dest_dir = os.path.join(paint_directory, "Brightfield Images")
    if os.path.exists(dest_dir):
        # If the destination directory already exists, remove it before copying
        shutil.rmtree(dest_dir)

    try:
        shutil.copytree(bf_jpeg_dir, dest_dir)
        paint_logger.info("Copied the entire 'Brightfield Images' directory to %s", dest_dir)
    except Exception as e:
        paint_logger.error("Error copying the directory %s to %s: %s", bf_jpeg_dir, dest_dir, str(e))


if __name__ == "__main__":
    # Ask user for Paint directory
    paint_directory = ask_user_for_image_directory("Specify the Paint directory", 'Paint')
    if not paint_directory:
        paint_logger.info("User aborted the batch processing.")
        sys.exit(0)

    # Ask user for the source directory of images
    images_source_directory = ask_user_for_image_directory("Specify the Image Source directory", 'Images')
    if not images_source_directory:
        logging.info("User aborted the batch processing.")
        sys.exit(0)

    # Run the conversion with user-specified directories
    convert_bf_images(images_source_directory, paint_directory, force=False)