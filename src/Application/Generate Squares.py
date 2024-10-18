import tkinter as tk

from src.Automation.Support.Generate_Squares import SquaresDialog

if __name__ == "__main__":
    root = tk.Tk()
    root.eval('tk::PlaceWindow . center')
    SquaresDialog(root)
    root.mainloop()