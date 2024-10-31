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

        # Store original unique values for reset functionality
        self.original_values = {col: sorted(self.df[col].unique()) for col in self.filter_columns}

        # Frame to hold listboxes and buttons
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky="NSEW")

        self.listboxes = {}  # Listboxes for each column
        self.filtered_df = self.df.copy()  # DataFrame to store the filtered results

        # Generate a listbox and filter button for each column
        for i, col in enumerate(self.filter_columns):
            # Label for the column name
            ttk.Label(frame, text=col).grid(row=0, column=i, padx=5, sticky="W")

            # Create a listbox with multiple selection mode
            listbox = tk.Listbox(frame, height=6, width=15, selectmode=tk.MULTIPLE)
            listbox.grid(row=1, column=i, padx=5, pady=5)
            self.listboxes[col] = listbox

            # Populate listbox with all unique values from the column
            self.populate_listbox(col)

            # Create a filter button below the listbox
            filter_button = ttk.Button(frame, text="Filter", command=lambda c=col: self.apply_filter(c))
            filter_button.grid(row=2, column=i, padx=(5, 2), pady=5, sticky="EW")

        # Button to reset all listboxes
        reset_all_button = ttk.Button(frame, text="Reset All", command=self.reset_all_filters)
        reset_all_button.grid(row=4, column=0, columnspan=len(self.filter_columns), pady=10)

        # Button to confirm and return the filtered DataFrame
        confirm_button = ttk.Button(frame, text="Apply All Filters", command=self.apply_all_filters)
        confirm_button.grid(row=4, column=1, columnspan=len(self.filter_columns), pady=10)

        # Cancel button to close the dialog
        cancel_button = ttk.Button(frame, text="Cancel", command=self.cancel)
        cancel_button.grid(row=4, column=2,
                           pady=10)

    def populate_listbox(self, col):
        """ Populate the listbox with original unique values from the column. """
        listbox = self.listboxes[col]
        listbox.delete(0, tk.END)  # Clear existing values
        for value in self.original_values[col]:
            listbox.insert(tk.END, value)

    def reset_all_filters(self):
        """ Clear all selections in all listboxes and restore their content. """
        for col in self.filter_columns:
            self.listboxes[col].selection_clear(0, tk.END)  # Clear selections
            self.populate_listbox(col)  # Restore original values

        self.filtered_df = self.df.copy()  # Reset the filtered DataFrame

    def apply_filter(self, col):
        """ Apply filter based on selected values in the specified listbox. """
        listbox = self.listboxes[col]
        selected_values = [listbox.get(i) for i in listbox.curselection()]

        if selected_values:
            # Trigger filtering when the button is pressed
            filtered_df = self.df[self.df[col].isin(selected_values)]

            # Update the filtered DataFrame with the current filter
            self.filtered_df = self.filtered_df[self.filtered_df[col].isin(selected_values)]

            # Update each listbox with filtered unique values
            for c, lb in self.listboxes.items():
                current_values = sorted(self.filtered_df[c].unique())
                lb.delete(0, tk.END)  # Clear existing values
                for value in current_values:
                    lb.insert(tk.END, value)

    def apply_all_filters(self):
        """ Collect selected values for all listboxes and apply filters. """
        selected_filters = {}
        for col, listbox in self.listboxes.items():
            count = listbox.size()
            current_values = [listbox.get(i) for i in range(count)]



            # selected_values = [listbox.get(i) for i in listbox.curselection()]
            if current_values:
                selected_filters[col] = current_values

        # Pass the selected filters to the main window through the callback
        print(selected_filters)
        self.callback(selected_filters)

        # Close the dialog
        self.destroy()

    def cancel(self):
        """ Close the dialog without applying any filters. """
        self.destroy()


if __name__ == "__main__":
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