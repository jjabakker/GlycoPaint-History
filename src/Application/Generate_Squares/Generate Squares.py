import tkinter as tk

from src.Application.Generate_Squares.Generate_Squares_Dialog import GenerateSquaresDialog

if __name__ == "__main__":
    root = tk.Tk()
    root.eval('tk::PlaceWindow . center')
    GenerateSquaresDialog(root)
    root.mainloop()
