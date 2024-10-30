import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk  # Importing from Pillow


def _paint_messagebox(_root, title, message, icon_path):
    # Create a new window for the messagebox
    msg_box = tk.Toplevel()
    msg_box.title(title)
    msg_box.geometry("300x150")

    # Prevent user from interacting with other windows
    msg_box.grab_set()

    # Load and set the custom icon (image) using Pillow
    try:
        img = Image.open(icon_path)
        img = img.resize((50, 50), Image.Resampling.LANCZOS)  # Resize the image if needed
        icon = ImageTk.PhotoImage(img)  # Convert to ImageTk format
    except Exception as e:
        print(f"Error loading image: {e}")  # Print error for debugging
        icon = None  # If image loading fails, set icon to None

    if icon:
        icon_label = ttk.Label(msg_box, image=icon)
        icon_label.image = icon  # Keep a reference to avoid garbage collection
        icon_label.grid(row=0, column=0, padx=10, pady=10)
    else:
        # Fallback in case the image doesn't load
        icon_label = ttk.Label(msg_box, text="[Image not available]")
        icon_label.grid(row=0, column=0, padx=10, pady=10)

    # Add the message text
    message_label = ttk.Label(msg_box, text=message, wraplength=500)
    message_label.grid(row=0, column=1, padx=10, pady=10)

    # Add an OK button to close the messagebox
    ok_button = ttk.Button(msg_box, text="OK", command=msg_box.destroy)
    ok_button.grid(row=1, column=1, padx=10, pady=10, sticky='e')

    # Calculate center position relative to the root window
    root_x = _root.winfo_x()
    root_y = _root.winfo_y()
    root_width = _root.winfo_width()
    root_height = _root.winfo_height()

    # Calculate x and y coordinates for centering the messagebox
    msg_box_width = 600
    msg_box_height = 150

    x_position = root_x + (root_width // 2) - (msg_box_width // 2)
    y_position = root_y + (root_height // 2) - (msg_box_height // 2)

    # Set the position of the messagebox
    msg_box.geometry(f"{msg_box_width}x{msg_box_height}+{x_position}+{y_position}")

    # Run the messagebox window
    msg_box.mainloop()


def paint_messagebox(_root, title, message):
    _paint_messagebox(_root, title, message, 'paint1.png')

    if __name__ == "__main__":
        # Create the main window
        root = tk.Tk()
        root.withdraw()  # Hide the main window

        # Call the custom messagebox with a user-defined icon
        paint_messagebox(root, "Paint Message", "This is a custom message with a user-defined icon.")

        root.mainloop()
