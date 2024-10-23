from tkinter import *

from src.Application.Compile_Project_Output.Compile_Project_Output import CompileDialog

root = Tk()
root.eval('tk::PlaceWindow . center')
CompileDialog(root)
root.mainloop()
