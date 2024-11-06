import os
from tkinter import *
from tkinter import ttk, filedialog

from src.Application.Utilities.ToolTips import ToolTip


def reset_root(root_dir):
    files_to_remove = ['All Recordings.csv', 'All Squares.csv']

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for file in filenames:
            # Check if the file name matches any in the list
            if file in files_to_remove:
                file_path = os.path.join(dirpath, file)
                os.remove(file_path)  # Delete the file
                print(f"Deleted {file_path}")


class Dialog:

    def __init__(self, root):
        root.title('Reset Root Directory')
        self.root_dir = ""

        content = ttk.Frame(root)
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

        # Fill the button frame
        btn_process = ttk.Button(frame_buttons, text='Reset', command=self.process)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.exit_dialog)
        btn_process.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        tooltip = "This will delete all 'All Recordings.csv' and 'All Squares.csv' files in the selected directory tree."
        ToolTip(btn_process, tooltip, wraplength=400)

        # Fill the directory frame
        btn_root_dir = ttk.Button(frame_directory, text='Root Directory', width=15, command=self.select_dir)
        self.lbl_root_dir = ttk.Label(frame_directory, text=self.root_dir, width=50)

        btn_root_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_root_dir.grid(column=1, row=0, padx=20, pady=5)

    def select_dir(self):
        self.root_dir = filedialog.askdirectory()
        if len(self.root_dir) != 0:
            self.lbl_root_dir.config(text=self.root_dir)

    def process(self):
        reset_root(self.root_dir)

    def exit_dialog(self):
        root.destroy()


root = Tk()
root.eval('tk::PlaceWindow . center')
Dialog(root)
root.mainloop()
