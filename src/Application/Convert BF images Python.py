from nd2reader import ND2Reader
from PIL import Image
import numpy as np
import os
import shutil

from src.Common.Support.LoggerConfig import paint_logger

def convert_nd2_to_jpg(nd2_file_path, output_file):

    # Open the .nd2 file
    with ND2Reader(nd2_file_path) as images:

        frame = images[0]
        # Check if the frame is in 16-bit format
        if frame.dtype == np.uint16:
            # Normalize the 16-bit frame to the range 0-255 (8-bit)
            min_val = np.min(frame)
            max_val = np.max(frame)

            # Avoid division by zero in case the image is uniform
            if max_val > min_val:
                frame = ((frame - min_val) / (max_val - min_val) * 255).astype(np.uint8)
            else:
                frame = np.zeros_like(frame, dtype=np.uint8)  # Handle uniform image case

        # Convert frame to PIL Image
        img = Image.fromarray(frame)

        # Save the image as .jpg
        img.save(output_file, 'JPEG')



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
                        convert_nd2_to_jpg(input_file, output_file)
                        paint_logger.info("Image %s was updated.", display_name)
                        converted += 1
                    except Exception as e:
                        paint_logger.error("Error converting %s: %s", display_name, str(e))
                else:
                    paint_logger.info("Image %s does not require updating.", display_name)

    # Log the conversion summary
    paint_logger.info("\nConverted %d BF images, out of %d BF images from %d total .nd2 images.", converted, found, count)

    # Copy the entire 'Converted BF Images' directory to the paint directory
    dest_dir = os.path.join(paint_directory, "Converted BF Images")
    if os.path.exists(dest_dir):
        # If the destination directory already exists, remove it before copying
        shutil.rmtree(dest_dir)

    try:
        shutil.copytree(bf_jpeg_dir, dest_dir)
        paint_logger.info("Copied the entire 'Converted BF Images' directory to %s", dest_dir)
    except Exception as e:
        paint_logger.error("Error copying the directory %s to %s: %s", bf_jpeg_dir, dest_dir, str(e))


if __name__ == "__main__":
    # Ask user for Paint directory
    # paint_directory = ask_user_for_image_directory("Specify the Paint directory", 'Paint')
    # if not paint_directory:
    #     paint_logger.info("User aborted the batch processing.")
    #     sys.exit(0)
    #
    # # Ask user for the source directory of images
    # images_source_directory = ask_user_for_image_directory("Specify the Image Source directory", 'Images')
    # if not images_source_directory:
    #     paint_logger.info("User aborted the batch processing.")
    #     sys.exit(0)
    #
    # # Run the conversion with user-specified directories
    # convert_bf_images(images_source_directory, paint_directory, force=False)
    convert_bf_images('/Volumes/Extreme Pro/Omero/221101', '/Users/hans/Downloads/Test', force=True)

