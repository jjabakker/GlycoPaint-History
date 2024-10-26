import tkinter as tk
from tkinter import ttk
from src.Application.Image_Viewer.Heatmap_Dialog.Heatmap_Support import (
    get_colormap_colors,
    get_heatmap_min_max)


class HeatMapDialog:

    #--------------------------------------------------------------
    # Setting up
    #--------------------------------------------------------------

    def __init__(self, image_viewer):

        # Create a new top-level window for the controls
        self.image_viewer = image_viewer
        self.toggle = False

        # Set windows properties
        self.control_window = tk.Toplevel(self.image_viewer.parent)
        self.control_window.title("Heatmap Control Window")
        self.control_window.resizable(False, False)
        self.control_window.geometry("310x350")
        self.control_window.resizable(False, False)
        self.control_window.attributes('-topmost', True)
        self.control_window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_userinterface()

        # Initialise by pretending a value has been changed
        self.on_heatmap_variable_change()

    def setup_userinterface(self):
        """
        This function sets up the UI elements for the control window.
        Three frames are creates.
        """

        # Create a content frame for the control window
        self.content = ttk.Frame(self.control_window, padding=(5, 5, 5, 5))
        self.content.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        # Create three frames for the different sections of the control window
        self.frame_mode_buttons = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_legend = ttk.Frame(self.content, borderwidth=2, padding=(5, 5, 5, 5))
        self.frame_controls = ttk.Frame(self.content, borderwidth=2, padding=(5, 5, 5, 5))

        # Set up the UI elements for the three frames
        self.setup_heatmap_variable_buttons()
        self.setup_legend()
        self.setup_controls()

        # Place the frames in the content frame
        self.frame_mode_buttons.grid(row=0, column=0, padx=5, pady=10)
        self.frame_legend.grid(row=0, column=1, padx=5, pady=10)
        self.frame_controls.grid(row=1, column=0, padx=5, pady=10)

    def setup_heatmap_variable_buttons(self):
        """
        Add radio buttons for the provided option names, by cycling through the option names
        The variable that is updated is the image_viewer.heatmap_option.
        When a change occurs on_heatmap_variable_change is called.
        """

        # Add a label for radio button group
        lbl_radio = tk.Label(self.frame_mode_buttons, text="Select an Option:", font=("Arial", 12))
        lbl_radio.grid(row=2, column=0, padx=5, pady=5)

        # Add radio buttons for the provided option names
        self.option_names = ["Tau", "Density", "Mean DC", "Track Duration", "Cum Track Duration"]
        for idx, name in enumerate(self.option_names, start=1):
            radio_btn = tk.Radiobutton(self.frame_mode_buttons, text=name, command=self.on_heatmap_variable_change,
                                       variable=self.image_viewer.heatmap_option, value=idx)
            radio_btn.grid(row=2 + idx, column=0, padx=5, pady=2, sticky=tk.W)
        self.image_viewer.heatmap_option.set(1)

        lbl_radio.grid(row=1, column=0, padx=5, pady=10)

    def setup_legend(self):
        """
        Add a legend to the control window. The legend shows the color scale of the heatmap.
        There are also two labels that show the min and max values of the heatmap.
        """

        canvas = tk.Canvas(self.frame_legend, width=30)

        colors = get_colormap_colors('Blues', 10)
        for i, color in enumerate(colors):
            canvas.create_rectangle(10, 10 + i * 20, 30, 80 + i * 20, fill=color, outline=color)
        self.lbl_min = tk.Label(self.frame_legend, text="", font=("Arial", 12))
        self.lbl_max = tk.Label(self.frame_legend, text="", font=("Arial", 12))

        canvas.grid(row=0, column=0, rowspan=11, padx=5, pady=10)
        self.lbl_min.grid(row=1, column=6, padx=5, pady=10)
        self.lbl_max.grid(row=10, column=6, padx=5, pady=10)

    def setup_controls(self):
        """
        Add a close button and a toggle button to the control window.
        """

        close_button = tk.Button(self.frame_controls, text="Close", command=self.on_close)
        toggle_button = tk.Button(self.frame_controls, text="Toggle", command=self.on_toggle)

        close_button.grid(row=0, column=0, padx=5, pady=10)
        toggle_button.grid(row=0, column=1, padx=5, pady=10)

    #--------------------------------------------------------------
    # Event Handlers
    #--------------------------------------------------------------

    def on_close(self):
        """
        When the user closes the control window, the Viewer dialog is notified, and the dialog is destroyed.
        """

        self.image_viewer.set_dialog_buttons(tk.NORMAL)
        self.image_viewer.heatmap_option.set(-1)
        self.control_window.destroy()

    def on_toggle(self):
        """
        If the user presses the toggle button a message is sent to the image viewer
        to toggle between the heatmap and the selected squares
        """

        if not self.toggle:
            self.image_viewer.display_selected_squares()
        else:
            self.image_viewer.display_heatmap()
        self.toggle = not self.toggle

    def on_heatmap_variable_change(self):
        """
        This function is called by the UI when a different heatmap variable is selected
        When that happens, the min and max values of the new heatmap are updated
        """

        min_val, max_val = get_heatmap_min_max(self.image_viewer.df_all_squares, self.image_viewer.heatmap_option.get())
        self.lbl_min.config(text=str(min_val))
        self.lbl_max.config(text=str(max_val))



