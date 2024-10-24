import os
import time
import tkinter as tk
from tkinter import ttk, filedialog

from src.Application.Generate_Squares.Generate_Squares  import (
    process_all_images_in_root_directory,
    process_all_images_in_experiment_directory)

from src.Application.Utilities.Paint_Messagebox import paint_messagebox

from src.Application.Utilities.Config import load_paint_config

from src.Application.Utilities.General_Support_Functions import (
    get_default_locations,
    save_default_locations
)

from src.Application.Generate_Squares.Utilities.Generate_Squares_Support_Functions import (
    get_grid_defaults_from_file,
    save_grid_defaults_to_file)

from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')


class GenerateSquaresDialog:
    DEFAULT_MAX_SQUARE_COVERAGE = 100  # Use constant for non-changing values

    def __init__(self, _root):
        self.root = _root
        self.load_saved_parameters()  # Initialize saved parameters and directories
        self.create_ui(_root)
        _root.title('Generate Squares')

    def load_saved_parameters(self):
        """Load parameters from disk or use default values if unavailable."""
        values = get_grid_defaults_from_file()
        self.nr_of_squares_in_row = tk.IntVar(value=values.get('nr_of_squares_in_row', 10))
        self.min_tracks_for_tau = tk.IntVar(value=values.get('min_tracks_for_tau', 10))
        self.min_r_squared = tk.DoubleVar(value=values.get('min_r_squared', 0.5))
        self.min_density_ratio = tk.DoubleVar(value=values.get('min_density_ratio', 0.5))
        self.max_variability = tk.DoubleVar(value=values.get('max_variability', 0.5))
        self.max_square_coverage = tk.DoubleVar(value=GenerateSquaresDialog.DEFAULT_MAX_SQUARE_COVERAGE)
        self.process_average_tau = tk.IntVar(value=values.get('process_single', 0))
        self.process_square_specific_tau = tk.IntVar(value=values.get('process_traditional', 1))
        self.root_directory, self.experiment_directory, self.images_directory, self.conf_file = get_default_locations()

    def create_ui(self, _root):
        """Create and layout the UI components."""
        content = ttk.Frame(_root)

        # Define frames
        frame_parameters = self.create_frame(content, 30)
        frame_processing = self.create_frame(content)
        frame_directory = self.create_frame(content)
        frame_buttons = self.create_frame(content)

        # Create controls in frames
        self.create_parameter_controls(frame_parameters)
        self.create_processing_controls(frame_processing)
        self.create_directory_controls(frame_directory)
        self.create_button_controls(frame_buttons)

        # Grid configuration for proper layout
        content.grid(column=0, row=0, sticky="nsew")

        # Add weight to center the frames within the grid
        _root.grid_rowconfigure(0, weight=1)  # Center vertically
        _root.grid_columnconfigure(0, weight=1)  # Center horizontally

        # Layout the frames
        frame_parameters.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        frame_processing.grid(column=1, row=0, padx=5, pady=5, sticky="nsew")
        frame_directory.grid(column=0, row=1, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Center the button frame exactly in the middle
        frame_buttons.grid(column=0, row=2, columnspan=2, padx=5, pady=5, sticky="nsew")
        _root.grid_rowconfigure(2, weight=1)
        _root.grid_columnconfigure(0, weight=1)

    def create_frame(self, parent, padding=5):
        """Helper method to create a standard frame."""
        return ttk.Frame(parent, borderwidth=5, relief='ridge', padding=(padding, padding, padding, padding))

    def create_parameter_controls(self, frame):
        """Create parameter controls for the UI."""
        params = [
            ("Nr of Squares in Row", self.nr_of_squares_in_row, 1),
            ("Minimum tracks to calculate Tau", self.min_tracks_for_tau, 2),
            ("Min allowable R-squared", self.min_r_squared, 3),
            ("Min Required Density Ratio", self.min_density_ratio, 4),
            ("Max Allowable Variability", self.max_variability, 5),
        ]

        for label_text, var, row in params:
            self.create_labeled_entry(frame, label_text, var, row)

    def create_labeled_entry(self, frame, label_text, var, row):
        """Helper method to create a label and corresponding entry."""
        label = ttk.Label(frame, text=label_text, width=30, anchor=tk.W)
        label.grid(column=0, row=row, padx=5, pady=5)
        entry = ttk.Entry(frame, textvariable=var, width=10)
        entry.grid(column=1, row=row)

    def create_processing_controls(self, frame):
        """Create the processing checkboxes."""
        self.create_checkbox(frame, "Square Specific Tau", self.process_square_specific_tau, 0)
        self.create_checkbox(frame, "Averaged Tau", self.process_average_tau, 1)

    def create_checkbox(self, frame, text, var, row):
        """Helper method to create a labeled checkbox."""
        checkbox = ttk.Checkbutton(frame, text=text, variable=var)
        checkbox.grid(column=0, row=row, padx=5, pady=10, sticky=tk.W)
        checkbox.config(padding=(10, 0, 0, 0))

    def create_directory_controls(self, frame):
        """Create controls for directory management."""
        btn_change_dir = ttk.Button(frame, text='Change Directory', width=15, command=self.change_dir)
        self.lbl_directory = ttk.Label(frame, text=self.experiment_directory, width=80)
        btn_change_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_directory.grid(column=1, row=0, padx=20, pady=5)

    def create_button_controls(self, frame):
        """Create buttons for the UI."""
        btn_process = ttk.Button(frame, text='Process', command=self.process_grid)
        btn_exit = ttk.Button(frame, text='Exit', command=self.exit_pressed)

        # Create two empty columns to balance the buttons in the center
        frame.grid_columnconfigure(0, weight=1)  # Left empty column
        frame.grid_columnconfigure(1, weight=0)  # Buttons column
        frame.grid_columnconfigure(2, weight=1)  # Right empty column

        # Center the buttons by placing them in column 1
        btn_process.grid(column=1, row=0, padx=10, pady=0, sticky="ew")  # Center Process button
        btn_exit.grid(column=1, row=1, padx=10, pady=0, sticky="ew")  # Center Exit button

    def change_dir(self):
        """Change the paint directory through a dialog."""
        paint_directory = filedialog.askdirectory(initialdir=self.experiment_directory)
        if paint_directory:
            self.experiment_directory = paint_directory
            self.lbl_directory.config(text=paint_directory)

    def exit_pressed(self):
        """Handle the exit button click."""
        self.root.destroy()

    def process_grid(self):
        """Process the grid and save the parameters."""
        start_time = time.time()

        process_function = self.determine_process_function()
        if process_function:
            process_function(
                self.experiment_directory, self.nr_of_squares_in_row.get(), self.min_r_squared.get(),
                self.min_tracks_for_tau.get(), self.min_density_ratio.get(), self.max_variability.get(),
                self.max_square_coverage.get(), self.process_average_tau.get(), self.process_square_specific_tau.get()
            )
            self.log_processing_time(time.time() - start_time)
            self.save_parameters()
        else:
            paint_logger.error('Invalid directory selected')
            paint_messagebox(self.root, 'Error GS:001', "The directory does not contain an 'experiment_tm.csv' file.'")

        # self.exit_pressed()

    def determine_process_function(self):
        """Determine the processing function based on the directory contents."""
        if os.path.isfile(os.path.join(self.experiment_directory, 'experiment_tm.csv')):
            return process_all_images_in_experiment_directory
        elif os.path.isfile(os.path.join(self.experiment_directory, 'root.txt')):
            return process_all_images_in_root_directory
        return None

    def save_parameters(self):
        """Save current settings to disk."""
        save_grid_defaults_to_file(
            self.nr_of_squares_in_row.get(), self.min_tracks_for_tau.get(), self.min_r_squared.get(),
            self.min_density_ratio.get(), self.max_variability.get(), self.max_square_coverage.get(),
            self.process_average_tau.get(), self.process_square_specific_tau.get()
        )
        save_default_locations(self.root_directory, self.experiment_directory, self.images_directory, self.conf_file)

    def log_processing_time(self, run_time):
        """Log the processing time."""
        paint_logger.info(f"Total processing time is {run_time:.1f} seconds")



if __name__ == "__main__":
    paint_config = load_paint_config('/src/Config/Paint.json')

    root = tk.Tk()
    root.eval('tk::PlaceWindow . center')
    GenerateSquaresDialog(root)
    root.mainloop()
