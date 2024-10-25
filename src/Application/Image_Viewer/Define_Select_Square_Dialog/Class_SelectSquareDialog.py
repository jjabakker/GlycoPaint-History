import tkinter as tk
from tkinter import ttk


class SelectSquareDialog:

    # --------------------------------------------------------------------------------------------------------
    # Setting up
    # --------------------------------------------------------------------------------------------------------

    def __init__(self, image_viewer, callback, min_required_density_ratio, max_allowable_variability,
                 min_track_duration, max_track_duration, neighbour_mode):
        """
        The callback function that is called is self.update_select_squares
        """

        # Create a new top-level window
        self.image_viewer = image_viewer
        self.callback = callback   # This is the callback function the UI calls when the sliders are changed

        self.min_required_density_ratio = None
        self.max_allowable_variability = None
        self.min_track_duration = None
        self.max_track_duration = None
        self.neighbour_mode = None

        # Set window properties
        self.select_dialog = tk.Toplevel(self.image_viewer.parent)
        self.select_dialog.title("Select Square Window")
        self.select_dialog.resizable(False, False)
        self.select_dialog.geometry("300x790")
        self.select_dialog.attributes('-topmost', True)
        self.select_dialog.protocol("WM_DELETE_WINDOW", self.on_close)

        # Set up the user interface
        self.setup_userinterface()

        # Initialise the controls
        self.initialise_controls(
            min_required_density_ratio, max_allowable_variability, min_track_duration,
            max_track_duration, neighbour_mode)

    def setup_userinterface(self):

        # Set up the content frame
        self.content = ttk.Frame(self.select_dialog, padding=(5, 5, 5, 5))
        self.content.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        # There are two frames in the content frame, one for the filters and one for the exit buttons
        self.frame_filter = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_exit_buttons = ttk.Frame(self.content, padding=(5, 5, 5, 5))

        # Set up the frames
        self.setup_frame_filter()
        self.setup_frame_exit_buttons()

        # Place the frames in the content frame
        self.frame_filter.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.frame_exit_buttons.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

    def setup_frame_exit_buttons(self):

        # Create a button to close the window
        close_button = tk.Button(self.frame_exit_buttons, text="Ok", command=self.on_close, width=10)
        close_button.grid(row=0, column=0, padx=5, pady=5, columnspan=2)

        # To center the button in the frame
        self.frame_exit_buttons.columnconfigure(0, weight=1)

    def setup_frame_filter(self):

        # Create frames for the different filters
        self.frame_neighbours = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_variability = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_density_ratio = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_duration = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_buttons = ttk.Frame(self.frame_filter, borderwidth=1, padding=(5, 5, 5, 5))

        # Set up the frames
        self.setup_frame_neighbours()
        self.setup_frame_variability()
        self.setup_frame_density_ratio()
        self.setup_frame_duration()
        self.setup_frame_buttons()

        # Place the frames in the filter frame
        self.frame_neighbours.grid(column=0, row=0, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.frame_variability.grid(column=0, row=1, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.frame_density_ratio.grid(column=0, row=2, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.frame_duration.grid(column=0, row=3, padx=5, pady=5, sticky=tk.N)
        self.frame_buttons.grid(column=0, row=4, padx=5, pady=1, sticky=(tk.N, tk.S, tk.E, tk.W))

    def setup_frame_buttons(self):

        bn_set_neighbours_all = tk.Button(self.frame_buttons, text="Set for All", command=self.set_for_all, width=10)
        bn_set_neighbours_all.grid(column=0, row=0, padx=5, pady=5)
        self.frame_buttons.columnconfigure(0, weight=1)

    def setup_frame_neighbours(self):

        # Create three radio buttons for the neighbour mode
        self.neighbour_var = tk.StringVar(value="")
        self.rb_neighbour_free = tk.Radiobutton(
            self.frame_neighbours, text="Free", variable=self.neighbour_var, width=12, value="Free",
            command=lambda: self.filter_changed('Neighbour Mode'), anchor=tk.W)
        self.rb_neighbour_strict = tk.Radiobutton(
            self.frame_neighbours, text="Strict", variable=self.neighbour_var, width=12, value="Strict",
            command=lambda: self.filter_changed('Neighbour Mode'), anchor=tk.W)
        self.rb_neighbour_relaxed = tk.Radiobutton(
            self.frame_neighbours, text="Relaxed", variable=self.neighbour_var, width=12, value="Relaxed",
            command=lambda: self.filter_changed('Neighbour Mode'), anchor=tk.W)

        # Place the radio buttons and button in the grid
        self.rb_neighbour_free.grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.rb_neighbour_relaxed.grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        self.rb_neighbour_strict.grid(column=0, row=2, padx=5, pady=5, sticky=tk.W)

    def setup_frame_variability(self):
        """
        Create a scale for the variability.
        The moment that the slider button is released, the variability_changed function is called.
        The value of the slider is stored in the variability variable
        """

        self.variability = tk.DoubleVar(value=self.max_allowable_variability)
        self.lbl_variability_text = ttk.Label(self.frame_variability, text='Max Allowable Variability', width=20)
        self.sc_variability = tk.Scale(self.frame_variability, from_=1.5, to=10, variable=self.variability,
                                       orient='vertical', resolution=0.5)
        self.sc_variability.bind("<ButtonRelease-1>", lambda event: self.filter_changed('Max Allowable Variability'))
        self.lbl_variability_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_variability.grid(column=0, row=1, padx=5, pady=5)

    def setup_frame_density_ratio(self):
        """
        Create a scale for the Minimum Required Density Ratio.
        The moment that the slider button is released, the density_ratio_changed function is called.
        The value of the slider is stored in the self.density_ratio variable
        """

        self.density_ratio = tk.DoubleVar(value=self.min_required_density_ratio)
        self.lbl_density_ratio_text = ttk.Label(
            self.frame_density_ratio, text='Min Required Density Ratio', width=20)
        self.sc_density_ratio = tk.Scale(
            self.frame_density_ratio, from_=2, to=40, variable=self.density_ratio, orient='vertical', resolution=0.1)
        self.sc_density_ratio.bind("<ButtonRelease-1>", lambda event: self.filter_changed('Min Required Density Ratio'))
        self.lbl_density_ratio_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_density_ratio.grid(column=0, row=1, padx=5, pady=5)

    def setup_frame_duration(self):
        """
        Create a frame for the track duration.
        The frame contains two scales, one for the minimum duration and one for the maximum duration.
        """

        self.frame_max_duration = ttk.Frame(self.frame_duration, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_min_duration = ttk.Frame(self.frame_duration, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.setup_max_duration()
        self.setup_min_duration()

        self.lbl_track_duration_text = ttk.Label(self.frame_duration, text='Track Duration', width=10)
        self.lbl_track_duration_text.grid(row=0, column=0, padx=5, pady=5, columnspan=2, sticky=tk.N)
        self.frame_max_duration.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)
        self.frame_min_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N)

    def setup_max_duration(self):
        """
        Create a scale for the Maximum Track Duration.
        The moment that the slider button is released, the track_duration_changed function is called.
        The value of the slider is stored in the self.track_max_duration variable
        """

        self.track_max_duration = tk.DoubleVar(value=self.max_track_duration)
        self.lbl_track_max_duration_text = ttk.Label(self.frame_max_duration, text='Max', width=10)
        self.sc_track_max_duration = tk.Scale(
            self.frame_max_duration, from_=0, to=200, variable=self.track_max_duration, orient='vertical',
            resolution=0.1)
        self.sc_track_max_duration.bind("<ButtonRelease-1>", lambda event: self.filter_changed('Max Track Duration'))

        self.lbl_track_max_duration_text.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W + tk.E)
        self.sc_track_max_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W + tk.E)

    def setup_min_duration(self):
        """
        Create a scale for the Minimum Track Duration.
        The moment that the slider button is released, the track_duration_changed function is called.
        The value of the slider is stored in the self.track_min_duration variable
        """

        self.track_min_duration = tk.DoubleVar(value=self.min_track_duration)
        self.lbl_track_min_duration_text = ttk.Label(self.frame_min_duration, text='Min', width=10)
        self.sc_track_min_duration = tk.Scale(
            self.frame_min_duration, from_=0, to=200, variable=self.track_min_duration, orient='vertical',
            resolution=0.1)
        self.sc_track_min_duration.bind("<ButtonRelease-1>", lambda event: self.filter_changed('Min Track Duration'))
        self.lbl_track_min_duration_text.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W + tk.E)
        self.sc_track_min_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W + tk.E)

    # --------------------------------------------------------------------------------------------------------
    # Event Handlers
    # --------------------------------------------------------------------------------------------------------

    def filter_changed(self, changed_slider):
        """
        Notify the main window about the track duration change, using the callback function provided by the
        Image Viewer (update_select_squares)
        """

        self.callback(changed_slider, self.sc_density_ratio.get(), self.sc_variability.get(),
                      self.track_min_duration.get(), self.track_max_duration.get(), self.neighbour_var.get())


    def set_for_all(self):
        self.callback("Set for All", self.sc_density_ratio.get(), self.sc_variability.get(),
                      self.track_min_duration.get(), self.track_max_duration.get(), self.neighbour_var.get())
        pass

    def on_close(self):
        """
        Set the radio button to an invalid value of -1 and destroy the window    @@
        The callback function (update_select_squares) is called in the ImageViewer dialog
        """

        self.image_viewer.update_select_squares("Exit", self.sc_density_ratio.get(), self.sc_variability.get(),
                      self.track_min_duration.get(), self.track_max_duration.get(), self.neighbour_var.get())
        self.image_viewer.set_dialog_buttons(tk.NORMAL)
        self.select_dialog.destroy()

    # --------------------------------------------------------------------------------------------------------
    # Information from the Image Viewer
    # --------------------------------------------------------------------------------------------------------

    def initialise_controls(self, min_required_density_ratio, max_allowable_variability, min_track_duration,
                            max_track_duration, neighbour_mode):

        # Set the initial values for the sliders and radio buttons as advised by the Image Viewer
        self.min_required_density_ratio = min_required_density_ratio
        self.max_allowable_variability = max_allowable_variability
        self.min_track_duration = min_track_duration
        self.max_track_duration = max_track_duration
        self.neighbour_mode = neighbour_mode

        # Set the sliders to the initial values
        self.density_ratio.set(min_required_density_ratio)
        self.variability.set(max_allowable_variability)
        self.track_min_duration.set(min_track_duration)
        self.track_max_duration.set(max_track_duration)
        self.neighbour_var.set(neighbour_mode)
