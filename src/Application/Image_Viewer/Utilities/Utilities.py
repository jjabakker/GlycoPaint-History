import sys
from tkinter import *

from PIL import Image, ImageTk

from src.Application.Support.Support_Functions import (
    read_squares_from_file)

from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name)


def save_as_png(canvas, file_name):
    # First save as a postscript file
    canvas.postscript(file=file_name + '.ps', colormode='color')

    # Then let PIL convert to a png file
    img = Image.open(file_name + '.ps')
    img.save(f"{file_name}.png", 'png')


def save_square_info_to_batch(self):  # TODO
    for index, row in self.df_experiment.iterrows():
        self.squares_file_name = self.list_images[self.img_no]['Squares File']
        df_squares = read_squares_from_file(self.squares_file_name)
        if df_squares is None:
            paint_logger.error("Function 'save_square_info_to_batch' failed: - Square file does not exist")
            sys.exit()
        if len(df_squares) > 0:
            nr_visible_squares = len(df_squares[df_squares['Visible']])
            nr_total_squares = len(df_squares)
            squares_ratio = round(nr_visible_squares / nr_total_squares, 2)
        else:
            nr_visible_squares = 0
            nr_total_squares = 0
            squares_ratio = 0.0

        self.df_experiment.loc[index, 'Nr Visible Squares'] = nr_visible_squares
        self.df_experiment.loc[index, 'Nr Total Squares'] = nr_total_squares
        self.df_experiment.loc[index, 'Squares Ratio'] = squares_ratio