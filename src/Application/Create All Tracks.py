import logging
from tkinter import *
from tkinter import ttk, filedialog

from src.Application.Create_All_Tracks.Create_All_Tracks import create_all_tracks
from src.Common.Support.DirectoriesAndLocations import (
    get_default_locations,
    save_default_locations)
from src.Common.Support.LoggerConfig import (
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Create All Tracks.log')


class CreateAllTracksDialog:

    def __init__(self, _root):
        _root.title('Create All Tracks')
        self.root_directory, self.paint_directory, self.images_directory, self.level = get_default_locations()

        # Set up the UI layout
        content = ttk.Frame(_root)
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

        # Fill the button frame
        btn_process = ttk.Button(frame_buttons, text='Process', command=self.process)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.exit_dialog)
        btn_process.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        # Fill the directory frame
        btn_root_dir = ttk.Button(frame_directory, text='Project Directory', width=15, command=self.change_root_dir)
        self.lbl_root_dir = ttk.Label(frame_directory, text=self.root_directory, width=50)

        btn_root_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_root_dir.grid(column=1, row=0, padx=20, pady=5)

    def change_root_dir(self):
        self.root_directory = filedialog.askdirectory(initialdir=self.root_directory)
        if self.root_directory:
            save_default_locations(self.root_directory, self.paint_directory, self.images_directory, self.level)
            self.lbl_root_dir.config(text=self.root_directory)

    def process(self):
        if self.root_directory:
            create_all_tracks(root_dir=self.root_directory)
        else:
            logging.error("No root directory selected.")
        root.destroy()

    def exit_dialog(self):
        root.destroy()


if __name__ == '__main__':
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    CreateAllTracksDialog(root)
    root.mainloop()
