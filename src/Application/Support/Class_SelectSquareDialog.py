import tkinter as tk
from tkinter import ttk, messagebox


class SelectSquareDialog:

    def __init__(self, image_viewer):
        # Create a new top-level window for the controls

        self.image_viewer = image_viewer
        self.experiments_changed = False  # Initialize experiment change flag
        self.toggle = False  # Initialize toggle state

        self.slider_window = tk.Toplevel(self.image_viewer.parent)
        self.slider_window.title("Select Square Window")
        self.slider_window.geometry("310x350")
        self.slider_window.attributes('-topmost', True)

        # Bind the closing event to a custom function
        self.slider_window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_userinterface()

    def setup_userinterface(self):
        # Define the UI elements

        self.content = ttk.Frame(self.slider_window, padding=(5, 5, 5, 5))

        self.frame_filter = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.setup_frame_filter()
        self.content.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

    def setup_frame_filter(self):
        # This frame is part of the content frame and contains the following frames: frame_variability, frame_density_ratio

        self.frame_variability = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_density_ratio = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_duration = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))

        self.setup_frame_variability()
        self.setup_frame_density_ratio()
        self.setup_frame_duration()

        self.frame_variability.grid(column=0, row=0, padx=5, pady=5, sticky=tk.N)
        self.frame_density_ratio.grid(column=0, row=1, padx=5, pady=5, sticky=tk.N)
        self.frame_duration.grid(column=0, row=2, padx=5, pady=5, sticky=tk.N)

        # The set for all button
        self.bn_set_for_all_slider = ttk.Button(self.frame_filter, text='Set for All', command=self.set_for_all_slider)
        self.bn_set_for_all_slider.grid(column=0, row=3, padx=5, pady=5)

    def setup_frame_variability(self):
        # Define the Max Allowable Variability slider ....

        self.variability = tk.DoubleVar()
        self.lbl_variability_text = ttk.Label(self.frame_variability, text='Max Allowable Variability', width=20)
        self.sc_variability = tk.Scale(self.frame_variability, from_=1.5, to=10, variable=self.variability,
                                       orient='vertical', resolution=0.5)
        self.sc_variability.bind("<ButtonRelease-1>", self.variability_changed)
        self.lbl_variability_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_variability.grid(column=0, row=1, padx=5, pady=5)

    def setup_frame_density_ratio(self):
        # Define the Min Required Density Ratio slider ...

        self.density_ratio = tk.DoubleVar()
        self.lbl_density_ratio_text = ttk.Label(self.frame_density_ratio, text='Min Required Density Ratio', width=20)
        self.sc_density_ratio = tk.Scale(self.frame_density_ratio, from_=2, to=40, variable=self.density_ratio,
                                         orient='vertical', resolution=0.1)
        self.sc_density_ratio.bind("<ButtonRelease-1>", self.density_ratio_changed)
        self.lbl_density_ratio_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_density_ratio.grid(column=