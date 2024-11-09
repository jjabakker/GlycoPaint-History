import os
import time
import tkinter as tk
from tkinter import ttk, filedialog

from src.Application.Generate_Squares.Generate_Squares import (
    process_project,
    process_experiment)
from src.Application.Generate_Squares.Utilities.Generate_Squares_Support_Functions import (
    get_grid_defaults_from_file,
    save_grid_defaults_to_file)
from src.Application.Utilities.General_Support_Functions import (
    get_default_locations,
    save_default_locations,
    format_time_nicely,
    classify_directory
)
from src.Application.Utilities.Paint_Messagebox import paint_messagebox
from src.Application.Utilities.ToolTips import ToolTip
from src.Common.Support.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)
from src.Common.Support.PaintConfig import load_paint_config

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
        self.min_required_density_ratio = tk.DoubleVar(value=values.get('min_required_density_ratio', 0.5))
        self.max_allowable_variability = tk.DoubleVar(value=values.get('max_allowable_variability', 0.5))
        self.max_square_coverage = tk.DoubleVar(value=GenerateSquaresDialog.DEFAULT_MAX_SQUARE_COVERAGE)
        self.process_average_tau = tk.IntVar(value=values.get('process_recording_tau', 0))
        self.process_square_specific_tau = tk.IntVar(value=values.get('process_square_tau', 1))
        self.root_directory, self.paint_directory, self.images_directory, self.level = get_default_locations()

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

        msg_nr_of_squares = "The number of squares in a row for the grid. The total number of squares will be this value squared."
        msg_min_tracks = "The minimum number of tracks required to calculate Tau. With too few tracks, curvefitting is unreliable."
        msg_min_r_squared = "The minimum allowable R-squared value for the tracks. Tau values with lower R-squared values are discarded."
        msg_min_required_density_ratio = "The minimum required density ratio for the tracks. Used to distinguish 'cell' squares from background"
        msg_max_allowable_variability = "The maximum allowable variability for the tracks. Used to filter out squares with high variability."

        params = [
            ("Nr of Squares in Row", self.nr_of_squares_in_row, 1, msg_nr_of_squares),
            ("Minimum tracks to calculate Tau", self.min_tracks_for_tau, 2, msg_min_tracks),
            ("Min allowable R-squared", self.min_r_squared, 3, msg_min_r_squared),
            ("Min Required Density Ratio", self.min_required_density_ratio, 4, msg_min_required_density_ratio),
            ("Max Allowable Variability", self.max_allowable_variability, 5, msg_max_allowable_variability),
        ]

        for label_text, var, row, tooltip in params:
            self.create_labeled_entry(frame, label_text, var, row, tooltip)

    def create_labeled_entry(self, frame, label_text, var, row, tooltip):
        """Helper method to create a label and corresponding entry."""
        label = ttk.Label(frame, text=label_text, width=30, anchor=tk.W)
        label.grid(column=0, row=row, padx=5, pady=5)
        entry = ttk.Entry(frame, textvariable=var, width=10)
        entry.grid(column=1, row=row)
        if tooltip:
            ToolTip(label, tooltip, wraplength=400)

    def create_processing_controls(self, frame):
        """Create the processing checkboxes."""

        msg_square_tau = "If checked, the program will calculate a Tau for each square individually."
        msg_recording_tau = "If checked, the program will calculate one Tau for all visible squares combined."
        msg_all_tracks = "If checked, the program will generate an All Tracks file and calculate an average Diffusion Coefficient for each square (necessary if you wish to see a heatmap"

        self.create_checkbox(frame, "Square Tau", self.process_square_specific_tau, 0, tooltip=msg_square_tau)
        self.create_checkbox(frame, "Recording Tau", self.process_average_tau, 1, tooltip=msg_recording_tau)

    def create_checkbox(self, frame, text, var, row, tooltip=None):
        """Helper method to create a labeled checkbox."""
        checkbox = ttk.Checkbutton(frame, text=text, variable=var)
        checkbox.grid(column=0, row=row, padx=5, pady=10, sticky=tk.W)
        checkbox.config(padding=(10, 0, 0, 0))
        if tooltip:
            ToolTip(checkbox, tooltip, wraplength=400)

    def create_directory_controls(self, frame):
        """Create controls for directory management."""
        btn_change_dir = ttk.Button(frame, text='Change Directory', width=15, command=self.on_change_dir)
        self.lbl_directory = ttk.Label(frame, text=self.paint_directory, width=80)
        btn_change_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_directory.grid(column=1, row=0, padx=20, pady=5)

        tooltip = "Specify a Project or an Experiment directory here."
        ToolTip(btn_change_dir, tooltip, wraplength=400)

    def create_button_controls(self, frame):
        """Create buttons for the UI."""
        btn_generate = ttk.Button(frame, text='Generate', command=self.on_generate_squares_pressed)
        btn_exit = ttk.Button(frame, text='Exit', command=self.on_exit_pressed)

        # Create two empty columns to balance the buttons in the center
        frame.grid_columnconfigure(0, weight=1)  # Left empty column
        frame.grid_columnconfigure(1, weight=0)  # Buttons column
        frame.grid_columnconfigure(2, weight=1)  # Right empty column

        # Center the buttons by placing them in column 1
        btn_generate.grid(column=1, row=0, padx=10, pady=0, sticky="ew")  # Center Process button
        btn_exit.grid(column=1, row=1, padx=10, pady=0, sticky="ew")  # Center Exit button

    def on_change_dir(self):
        """Change the paint directory through a dialog."""
        paint_directory = filedialog.askdirectory(initialdir=self.paint_directory)
        if paint_directory:
            self.paint_directory = paint_directory
            self.lbl_directory.config(text=paint_directory)

    def on_exit_pressed(self):
        """Handle the exit button click."""
        self.root.destroy()

    def on_generate_squares_pressed(self):
        """Generate the squares and save the parameters."""
        start_time = time.time()

        if not os.path.isdir(self.paint_directory):
            paint_logger.error("The selected directory does not exist")
            paint_messagebox(self.root, title='Warning', message="The selected directory does not exist")
            return

        dir_type, _ = classify_directory(self.paint_directory)
        if dir_type == 'Project':
            generate_function = process_project
            called_from_project = True
        elif dir_type == 'Experiment':
            generate_function = process_experiment
            called_from_project = False
        else:
            msg = "The selected directory does not seem to be a project directory, nor an experiment directory"
            paint_logger.error(msg)
            paint_messagebox(self.root, title='Warning', message=msg)
            return

        generate_function(
            paint_directory=self.paint_directory,
            nr_of_squares_in_row=self.nr_of_squares_in_row.get(),
            min_r_squared=self.min_r_squared.get(),
            min_tracks_for_tau=self.min_tracks_for_tau.get(),
            min_required_density_ratio=self.min_required_density_ratio.get(),
            max_allowable_variability=self.max_allowable_variability.get(),
            max_square_coverage=self.max_square_coverage.get(),
            process_recording_tau=self.process_average_tau.get(),
            process_square_tau=self.process_square_specific_tau.get(),
            called_from_project=called_from_project,
            paint_force=True,
            verbose=False
        )
        run_time = time.time() - start_time
        paint_logger.info(f"Total processing time is {format_time_nicely(run_time)}")
        self.save_parameters()
        self.on_exit_pressed()

    def save_parameters(self):
        save_grid_defaults_to_file(
            nr_of_squares_in_row=self.nr_of_squares_in_row.get(),
            min_tracks_for_tau=self.min_tracks_for_tau.get(),
            min_r_squared=self.min_r_squared.get(),
            min_required_density_ratio=self.min_required_density_ratio.get(),
            max_allowable_variability=self.max_allowable_variability.get(),
            max_square_coverage=self.max_square_coverage.get(),
            process_recording_tau=self.process_average_tau.get(),
            process_square_tau=self.process_square_specific_tau.get()
        )
        save_default_locations(self.root_directory, self.paint_directory, self.images_directory, self.level)


if __name__ == "__main__":
    paint_config = load_paint_config('/src/Config/Paint.json')

    root = tk.Tk()
    root.eval('tk::PlaceWindow . center')
    GenerateSquaresDialog(root)
    root.mainloop()
