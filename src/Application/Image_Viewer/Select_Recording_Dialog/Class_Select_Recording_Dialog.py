import pandas as pd
import tkinter as tk
from tkinter import ttk

# Sample DataFrame with example data
data = {
    'Probe Type': ['Type1', 'Type2', 'Type1', 'Type3', 'Type2'],
    'Probe': ['A', 'B', 'A', 'C', 'B'],
    'Cell Type': ['X', 'Y', 'Z', 'Z', 'Y'],
    'Adjuvant': ['Adj1', 'Adj2', 'Adj1', 'Adj3', 'Adj2'],
    'Concentration': [1, 2, 1, 3, 2]
}
df = pd.DataFrame(data)


class SelectRecordingDialog(tk.Toplevel):

    def __init__(self, parent, dataframe, callback):
        super().__init__(parent)
        self.title("Select Recordings")
        self.df = dataframe.copy()
        self.callback = callback
        self.parent = parent
        self.dropdown_selections = {}  # Store current selections

        # Why is this necessary
        # Drop rows with missing values
        # self.df.dropna(inplace=True)

        # Only filter on these specific columns
        self.filter_columns = ['Probe Type', 'Probe', 'Cell Type', 'Adjuvant', 'Concentration']

        # Make it string type
        self.df['Concentration'] = self.df['Concentration'].astype(str)


        # Frame to hold dropdowns and listboxes
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky="NSEW")

        self.dropdowns = {}  # Comboboxes for each column
        self.listboxes = {}  # Listboxes for each column

        # Generate a combobox, listbox, and reset button for each column
        for i, col in enumerate(self.filter_columns):
            # Label for the column name
            ttk.Label(frame, text=col).grid(row=0, column=i, padx=5, sticky="W")

            # Create a combobox for selecting filter criteria
            unique_values = sorted(self.df[col].unique())
            combo = ttk.Combobox(frame, values=unique_values, state="readonly", width=15)
            combo.set("")  # Default to empty (no selection)
            combo.grid(row=1, column=i, padx=5)
            self.dropdowns[col] = combo
            combo.bind("<<ComboboxSelected>>", self.on_selection)

            # Create a listbox to show current available options
            listbox = tk.Listbox(frame, height=6, width=15)
            listbox.grid(row=2, column=i, padx=5, pady=5)
            self.listboxes[col] = listbox

            # Bind listbox selection to update combobox
            listbox.bind("<<ListboxSelect>>", lambda e, c=col: self.on_listbox_select(e, c))

            # Create a reset button for the combobox below the listbox
            reset_button = ttk.Button(frame, text="Reset", command=lambda c=col: self.reset_filter(c))
            reset_button.grid(row=3, column=i, padx=5, pady=5)

            # Initially populate the listbox with all values
            for value in unique_values:
                listbox.insert(tk.END, value)

        # Button to confirm and return the filtered DataFrame
        confirm_button = ttk.Button(self, text="Apply Filters", command=self.apply_filter)
        confirm_button.grid(row=4, column=0, columnspan=len(self.df.columns), pady=10)

    def on_selection(self, event):
        self.update_dropdowns()

    def on_listbox_select(self, event, col):
        # Ensure there is a selection in the listbox before accessing it
        if event.widget.curselection():
            # Get the selected value from the listbox
            selected_value = event.widget.get(event.widget.curselection())

            # Update the combobox with the selected listbox value and trigger filtering
            self.dropdowns[col].set(selected_value)
            self.update_dropdowns()

    def reset_filter(self, col):
        # Clear the combobox selection and refresh options
        self.dropdowns[col].set("")
        self.update_dropdowns()

    def update_dropdowns(self):
        filtered_df = self.df.copy()

        # Filter based on current selections
        for col, combo in self.dropdowns.items():
            selected_value = combo.get()
            if selected_value:
                filtered_df = filtered_df[filtered_df[col] == selected_value]

        # Update each combobox and listbox with filtered values
        for col, combo in self.dropdowns.items():
            current_values = sorted(filtered_df[col].unique())
            combo['values'] = current_values
            if combo.get() not in current_values:
                combo.set("")

            # Update the listbox for each column
            self.listboxes[col].delete(0, tk.END)
            for value in current_values:
                self.listboxes[col].insert(tk.END, value)

    def apply_filter(self):
        # Collect current selections in the dropdowns
        self.dropdown_selections = {col: combo.get() for col, combo in self.dropdowns.items() if combo.get()}

        # Pass the selection back to the main window through the callback
        self.callback(self.dropdown_selections)

        # Close the dialog
        self.destroy()


if __name__ == "__main__":
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
            # Callback to receive the filtered data from the dialog
            # Update the label with the selected filter criteria
            filter_text = ", ".join(f"{k}: {v}" for k, v in selected_filters.items())
            self.result_label.config(text=f"Filtered Data: {filter_text}")


# Run the main window
if __name__ == "__main__":
    main_app = MainWindow()
    main_app.mainloop()