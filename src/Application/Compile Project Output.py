from tkinter import *

from src.Application.Support.Compile_Project_Output import CompileDialog

root = Tk()
root.eval('tk::PlaceWindow . center')
CompileDialog(root)
root.mainloop()
