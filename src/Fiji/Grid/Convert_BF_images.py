import os
import sys
import shutil

from ij import IJ
from java.lang.System import getProperty

paint_dir = getProperty('fiji.dir') + os.sep + "scripts" + os.sep + "Plugins" + os.sep + "Paint"
sys.path.append(paint_dir)

from FijiSupportFunctions import ask_user_for_image_directory
from FijiSupportFunctions import fiji_log
from FijiSupportFunctions import fiji_header


def convert_BF_images(image_source_directory, paint_directory, force=False):

    # Create a 'Converted BF Images' directory if it not already exists
    bf_jpeg_dir = image_source_directory + os.sep + "Converted BF Images"
    if not os.path.isdir(bf_jpeg_dir):
        os.mkdir(bf_jpeg_dir)

    fiji_log('\n\n')
    count      = 0
    found      = 0
    converted  = 0
    all_images = os.listdir(image_source_directory)
    all_images.sort()
    for image_name in all_images:
        if not image_name.startswith('._'):      # Ignore everything starting with ._
            if image_name.endswith('.nd2'):      # It is an nd2 file
                count += 1
                if image_name.find('BF') != -1:  # It is a BF file
                    # So, we have BF image of type .nd2
                    found += 1
                    display_name = image_name.ljust(30, ' ')
                    input_file   = image_source_directory + os.sep + image_name
                    output_file  = bf_jpeg_dir + os.sep + image_name
                    output_file  = output_file.replace('nd2', 'jpg')
                    convert      = force
                    if not os.path.isfile(output_file):
                        convert = True
                    elif os.path.getmtime(output_file) < os.path.getmtime(input_file):
                        convert = True
                    if convert:
                        nd2_arg = "open=[" + input_file + "]"
                        IJ.run("Bio-Formats (Windowless)", nd2_arg)
                        # IJ.run("Enhance Contrast", "saturated=0.35")
                        IJ.saveAs("Jpeg", output_file)
                        IJ.getImage().close()
                        fiji_log("Image " + display_name + " was updated.")
                        converted += 1
                    else:
                        fiji_log("Image " + display_name + " does not require updating.")
                        pass
    fiji_header("\nConverted " + str(converted) + " BF images, out of " + str(found) + " BF images out of " + str(count) + " nd2 images")
    # fiji_log("\n\n")

    # Copy the directory to the specified paint_directory
    dest_dir = os.path.join(paint_directory, 'Converted BF Images')
    if not os.path.isdir(dest_dir):
        os.mkdir(dest_dir)
    file_list = os.listdir(bf_jpeg_dir)

    count = 0
    for file in file_list:
        shutil.copy(os.path.join(bf_jpeg_dir, file), os.path.join(dest_dir, file))
        count += 1

    fiji_header("Copied " + str(found) + " BF images, to destination paint directory: " + dest_dir)
    fiji_log("\n\n")


if __name__ == "__main__":
    # image_source_directory = ask_user_for_image_directory("Please enter the directory containing the nd2 BF files", 'Images')

    paint_directory = ask_user_for_image_directory("Specify the Paint directory", 'Paint')
    if len(paint_directory) == 0:
        fiji_log("\nUser aborted the batch processing.")
        exit(0)

    # Get the directory where the images are located
    images_source_directory = ask_user_for_image_directory("Specify the Image Source directory", 'Images')
    if len(images_source_directory) == 0:
        fiji_log("\nUser aborted the batch processing.")
        exit(0)

    convert_BF_images(images_source_directory, paint_directory, force=False)
