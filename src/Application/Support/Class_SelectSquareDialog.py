import tkinter as tk
from tkinter import ttk, messagebox


class SelectSquareDialog:

    def __init__(self, image_viewer, callback):


        self.image_viewer = image_viewer
        self.callback = callback
        self.experiments_changed = False  # Initialize experiment change flag

        self.slider_window = tk.Toplevel(self.image_viewer.parent)
        self.slider_window.title("Select Square Window")
        self.slider_window.geometry("300x600")
        self.slider_window.attributes('-topmost', True)

        # Bind the closing event to a custom function
        self.slider_window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_userinterface()

    def setup_userinterface(self):
        self.content = ttk.Frame(self.slider_window, padding=(5, 5, 5, 5))
        self.content.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        self.frame_filter = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_filter.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.setup_frame_filter()

    def setup_frame_filter(self):
        self.frame_variability = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_density_ratio = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove',
                                             padding=(5, 5, 5, 5))
        self.frame_duration = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))

        self.setup_frame_variability()
        self.setup_frame_density_ratio()
        self.setup_frame_duration()

        self.frame_variability.grid(column=0, row=0, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.frame_density_ratio.grid(column=0, row=1, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.frame_duration.grid(column=0, row=2, padx=5, pady=5, sticky=tk.N)

    def setup_frame_variability(self):
        self.variability = tk.DoubleVar(value=5.0)
        self.lbl_variability_text = ttk.Label(self.frame_variability, text='Max Allowable Variability', width=20)
        self.sc_variability = tk.Scale(self.frame_variability, from_=1.5, to=10, variable=self.variability,
                                       orient='vertical', resolution=0.5)
        self.sc_variability.bind("<ButtonRelease-1>", self.variability_changed)
        self.lbl_variability_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_variability.grid(column=0, row=1, padx=5, pady=5)

    def setup_frame_density_ratio(self):
        self.density_ratio = tk.DoubleVar(value=10.0)
        self.lbl_density_ratio_text = ttk.Label(self.frame_density_ratio, text='Min Required Density Ratio',
                                                width=20)
        self.sc_density_ratio = tk.Scale(self.frame_density_ratio, from_=2, to=40, variable=self.density_ratio,
                                         orient='vertical', resolution=0.1)
        self.sc_density_ratio.bind("<ButtonRelease-1>", self.density_ratio_changed)
        self.lbl_density_ratio_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_density_ratio.grid(column=0, row=1, padx=5, pady=5)

    def setup_frame_duration(self):
        self.frame_max_duration = ttk.Frame(self.frame_duration, borderwidth=1, relief='groove',
                                            padding=(5, 5, 5, 5))
        self.frame_min_duration = ttk.Frame(self.frame_duration, borderwidth=1, relief='groove',
                                            padding=(5, 5, 5, 5))

        self.setup_max_duration()
        self.setup_min_duration()

        self.lbl_track_duration_text = ttk.Label(self.frame_duration, text='Track Duration', width=10)
        self.lbl_track_duration_text.grid(row=0, column=0, padx=5, pady=5, columnspan=2, sticky=tk.N)
        self.frame_max_duration.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)
        self.frame_min_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N)

    def setup_max_duration(self):
        self.track_max_duration = tk.DoubleVar(value=200)
        self.lbl_track_max_duration_text = ttk.Label(self.frame_max_duration, text='Max', width=10)
        self.sc_track_max_duration = tk.Scale(self.frame_max_duration, from_=0, to=200,
                                              variable=self.track_max_duration,
                                              orient='vertical', resolution=0.1)
        self.sc_track_max_duration.bind("<ButtonRelease-1>", lambda event: self.track_duration_changed('max'))

        self.lbl_track_max_duration_text.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W + tk.E)
        self.sc_track_max_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W + tk.E)

    def setup_min_duration(self):
        self.track_min_duration = tk.DoubleVar(value=0)
        self.lbl_track_min_duration_text = ttk.Label(self.frame_min_duration, text='Min', width=10)
        self.sc_track_min_duration = tk.Scale(self.frame_min_duration, from_=0, to=200,
                                              variable=self.track_min_duration,
                                              orient='vertical', resolution=0.1)
        self.sc_track_min_duration.bind("<ButtonRelease-1>", lambda event: self.track_duration_changed('min'))
        self.lbl_track_min_duration_text.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W + tk.E)
        self.sc_track_min_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W + tk.E)

    def variability_changed(self, _):
        self.experiments_changed = True
        self.callback("variability", self.sc_density_ratio.get(), self.sc_variability.get(),
                      self.track_min_duration.get(), self.track_max_duration.get())

    def density_ratio_changed(self, _):
        self.experiments_changed = True
        self.callback("density_ratio", self.sc_density_ratio.get(), self.sc_variability.get(),
                      self.track_min_duration.get(), self.track_max_duration.get())

    def track_duration_changed(self, changed_slider):
        self.experiments_changed = True

        if changed_slider == 'min':
            self.callback("min_duration", self.sc_density_ratio.get(), self.sc_variability.get(),
                          self.track_min_duration.get(),
                          self.track_max_duration.get())
        elif changed_slider == 'max':
            self.callback("max_duration", self.sc_density_ratio.get(), self.sc_variability.get(),
                          self.track_min_duration.get(),
                          self.track_max_duration.get())

    def on_close(self):
        self.image_viewer.rb_heatmap_parameter_value.set(-1)
        self.slider_window.destroy()



# Main block
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Dummy image_viewer class to pass to SelectSquareDialog
    class DummyImageViewer:
        parent = root
        df_experiment = {'Density Ratio Setting': 0, 'Variability Setting': 0}
        rb_heatmap_parameter_value = tk.IntVar()

        def display_selected_squares(self):
            print("Displaying selected squares")

        def display_heatmap(self):
            print("Displaying heatmap")

    # Create an instance of DummyImageViewer
    image_viewer = DummyImageViewer()

    # Create and show the SelectSquareDialog
    app = SelectSquareDialog(image_viewer)
    root.mainloop()