import tkinter as tk
from tkinter import ttk


class DefineCellDialog:

    #--------------------------------------------------------------
    # Setting up
    #--------------------------------------------------------------

    def __init__(self, image_viewer, call_back_to_assign_squares_to_cell, call_back_to_reset_square_selection):

        # Create a new top-level window for the controls
        self.image_viewer = image_viewer
        self.call_back_to_assign_squares_to_cell = call_back_to_assign_squares_to_cell
        self.call_back_to_reset_square_selection = call_back_to_reset_square_selection

        # Set windows properties
        self.control_window = tk.Toplevel(self.image_viewer.parent)
        self.control_window.resizable(False, False)
        self.control_window.title("Define Cell")
        self.control_window.geometry("280x350")
        self.control_window.resizable(False, False)
        self.control_window.attributes('-topmost', True)
        self.control_window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_userinterface()

        # Initialise by pretending a value has been changed
        # self.on_heatmap_variable_change()

    def setup_userinterface(self):
        """
        This function sets up the UI elements for the control window.
        Three frames are creates.
        """

        # Create a content frame for the control window
        self.content = ttk.Frame(self.control_window, padding=(5, 5, 5, 5))
        self.content.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        # Create two frames for the different sections of the control window
        self.frame_cells = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_controls = ttk.Frame(self.content, borderwidth=2, padding=(5, 5, 5, 5))

        # Setup the UI elements for the two frames
        self.setup_frame_cells()
        self.setup_frame_controls()

        # Place the frames in the content frame
        self.frame_cells.grid(row=0, column=0, padx=5, pady=10)
        self.frame_controls.grid(row=1, column=0, padx=5, pady=10)

    def setup_frame_cells(self):

        # Define variables
        width_rb = 12
        self.cell_var = tk.StringVar(value=1)

        # Define colors for each cell
        cell_options = [
            ("Not on cell", "white", 0),
            ("On cell 1", "red", 1),
            ("On cell 2", "yellow", 2),
            ("On cell 3", "green", 3),
            ("On cell 4", "magenta", 4),
            ("On cell 5", "cyan", 5),
            ("On cell 6", "black", 6)
        ]

        # Variable to store the selected value
        self.cell_var = tk.IntVar(value=0)

        # Create radio buttons with colored squares
        for i, (text, color, value) in enumerate(cell_options):
            # Create and place the radio button
            rb = tk.Radiobutton(self.frame_cells, text=text, variable=self.cell_var, value=value)
            rb.grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)

            # Create and place the colored square
            color_square = tk.Label(self.frame_cells, bg=color, width=2, height=1, relief="solid", borderwidth=1)
            color_square.grid(row=i, column=1, padx=10, pady=5)

    # Bind the right mouse click
        # self.rb_cell1.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 1))
        # self.rb_cell2.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 2))
        # self.rb_cell3.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 3))
        # self.rb_cell4.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 4))
        # self.rb_cell5.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 5))
        # self.rb_cell6.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 6))
        # self.rb_cell0.bind('<Button-2>', lambda e: self.provide_report_on_cell(e, 0))

    def setup_frame_controls(self):
        """
        Add a close button and a toggle button to the control window.
        """

        close_button = tk.Button(self.frame_controls, text="Close", command=self.on_close)
        assign_button = tk.Button(self.frame_controls, text="Assign", command=self.on_assign)
        reset_button = tk.Button(self.frame_controls, text="Reset", command=self.on_reset)

        close_button.grid(row=0, column=0, padx=5, pady=10)
        assign_button.grid(row=0, column=1, padx=5, pady=10)
        reset_button.grid(row=0, column=2, padx=5, pady=10)

    #--------------------------------------------------------------
    # Event Handlers
    #--------------------------------------------------------------

    def on_close(self):
        """
        When the user closes the control window, the Viewer dialog is notified, and the dialog is destroyed.
        """

        self.on_reset()
        self.control_window.destroy()

    def on_assign(self):
        self.call_back_to_assign_squares_to_cell  (self.cell_var.get())
        pass

    def on_reset(self):
        self.call_back_to_reset_square_selection(0)
        pass





