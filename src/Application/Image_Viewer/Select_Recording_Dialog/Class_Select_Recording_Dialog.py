import tkinter as tk
from tkinter import ttk
import pandas as pd


class SelectRecordingDialog(tk.Toplevel):
    def __init__(self, parent, dataframe, callback):
        super().__init__(parent)
        self.title("Select Recordings")
        self.df = dataframe.copy()
        self.callback = callback
        self.parent = parent

        # Only filter on these specific columns
        self.filter_columns = ['Probe Type', 'Probe', 'Cell Type', 'Adjuvant', 'Concentration']

        # Make 'Concentration' a string type
        self.df['Concentration'] = self.df['Concentration'].astype(str)

        # Frame to hold listboxes and reset buttons
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky="NSEW")

        self.listboxes = {}  # Listboxes for each column

        # Generate a listbox and reset button for each column
        for i, col in enumerate(self.filter_columns):
            # Label for the column name
            ttk.Label(frame, text=col).grid(row=0, column=i, padx=5, sticky="W")

            # Create a listbox with multiple selection mode
            listbox = tk.Listbox(frame, height=6, width=15, selectmode=tk.MULTIPLE)
            listbox.grid(row=1, column=i, padx=5, pady=5)
            self.listboxes[col] = listbox

            # Populate listbox with all unique values from the column
            unique_values = sorted(self.df[col].unique())
            for value in unique_values:
                listbox.insert(tk.END, value)

            # Create a reset button below the listbox
            reset_button = ttk.Button(frame, text="Reset", command=lambda c=col: self.reset_filter(c))
            reset_button.grid(row=2, column=i, padx=5, pady=5)

            # Bind the listbox selection event
            listbox.bind("<ButtonRelease-1>", self.on_listbox_select)

        # Button to confirm and return the filtered DataFrame
        confirm_button = ttk.Button(frame, text="Apply Filters", command=self.apply_filter)
        confirm_button.grid(row=3, column=0, columnspan=len(self.filter_columns), pady=10)

    def reset_filter(self, col):
        # Clear all selections in the listbox for the specified column
        self.listboxes[col].selection_clear(0, tk.END)

    def on_listbox_select(self, event):
        listbox = event.widget
        # Check if Shift key is held down
        if event.state & 0x0001:  # Bit 0 represents the Shift key
            # Continue selecting without clearing previous selections
            self.update_listboxes()

    def update_listboxes(self):
        filtered_df = self.df.copy()

        # Get the current selected values for each listbox
        selected_filters = {}
        for col, listbox in self.listboxes.items():
            selected_values = [listbox.get(i) for i in listbox.curselection()]
            if selected_values:
                selected_filters[col] = selected_values

        # Apply filters to DataFrame based on selected values
        for col, values in selected_filters.items():
            filtered_df = filtered_df[filtered_df[col].isin(values)]

        # Update each listbox with filtered unique values
        for col, listbox in self.listboxes.items():
            current_values = sorted(filtered_df[col].unique())
            listbox.delete(0, tk.END)  # Clear existing values
            for value in current_values:
                listbox.insert(tk.END, value)

    def apply_filter(self):
        # Collect selected values for each listbox (column) into a dictionary
        selected_filters = {}
        for col, listbox in self.listboxes.items():
            selected_values = [listbox.get(i) for i in listbox.curselection()]
            if selected_values:
                selected_filters[col] = selected_values

        # Pass the selected filters to the main window through the callback
        self.callback(selected_filters)

        # Close the dialog
        self.destroy()


# Sample DataFrame with example data
data = {
    'Probe Type': ['Type1', 'Type2', 'Type1', 'Type3', 'Type2'],
    'Probe': ['A', 'B', 'A', 'C', 'B'],
    'Cell Type': ['X', 'Y', 'X', 'Z', 'Y'],
    'Adjuvant': ['Adj1', 'Adj2', 'Adj1', 'Adj3', 'Adj2'],
    'Concentration': [1, 2, 1, 3, 2]
}
df = pd.DataFrame(data)


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Main Window")

        # Button to open filter dialog
        open_dialog_button = ttk.Button(self, text="Open Filter Dialog", command=self.open_filter_dialog)
        open_dialog_button.pack(pady=20)

        # Label to display filter results
        self.result_label = ttk.Label(self, text="Filtered Data: None")
        self.result_label.pack(pady=20)

    def open_filter_dialog(self):
        # Open the filter dialog and pass a callback to receive the data
        SelectRecordingDialog(self, df, self.on_filter_applied)

    def on_filter_applied(self, selected_filters):
        # Display the selected filters
        filter_text = ", ".join(f"{k}: {v}" for k, v in selected_filters.items())
        self.result_label.config(text=f"Filtered Data: {filter_text}")


# Run the main window
if __name__ == "__main__":
    main_app = MainWindow()
    main_app.mainloop()