import os

import tkinter as tk
from tkinter import ttk


class HeatMapControlDialiog:
    def __init__(self, image_viewer):
        # Create a new top-level window for the controls

        self.image_viewer = image_viewer

        self.control_window = tk.Toplevel(self.image_viewer.root)
        self.control_window.title("Heatmap Control Window")
        self.control_window.geometry("300x350")
        self.option_names = ["Tau", "Density", "Track Count", "Track Duration",
                             "Cum Track Duration"]  # Customize option names

        # Bind the closing event to a custom function
        self.control_window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Configure the grid to center controls
        self.control_window.columnconfigure(0, weight=1)

        # Add some controls to the control window
        lbl_control = tk.Label(self.control_window, text="Control Window", font=("Arial", 16))
        lbl_control.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W + tk.E)

        # Add a slider that updates the value in the main window
        slider = ttk.Scale(self.control_window, from_=0, to=100, orient='horizontal',
                           variable=image_viewer.slider_value)
        slider.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W + tk.E)

        # Add a label for radio button group
        lbl_radio = tk.Label(self.control_window, text="Select an Option:", font=("Arial", 12))
        lbl_radio.grid(row=2, column=0, padx=5, pady=5)

        # Add radio buttons for the provided option names
        for idx, name in enumerate(self.option_names, start=1):
            radio_btn = tk.Radiobutton(self.control_window, text=name, variable=image_viewer.rb_heatmap_parameter_value,
                                       value=idx)
            radio_btn.grid(row=2 + idx, column=0, padx=5, pady=2, sticky=tk.W)
        self.image_viewer.rb_heatmap_parameter_value.set(1)

        # Add a checkbox for an additional setting
        checkbox = tk.Checkbutton(self.control_window, text="Enable Feature", variable=self.image_viewer.checkbox_value)
        checkbox.grid(row=8, column=0, padx=5, pady=10, sticky=tk.W)

        # Add a button to close the control window
        button = tk.Button(self.control_window, text="Close", command=self.on_close)
        button.grid(row=9, column=0, padx=5, pady=10)

    def on_close(self):
        self.image_viewer.rb_heatmap_parameter_value.set(-1)
        self.control_window.destroy()  # Actually close the control window
