from tkinter import *

from src.Application.Compile_Project.Compile_Project import CompileDialog

root = Tk()
root.eval('tk::PlaceWindow . center')
CompileDialog(root)
root.mainloop()
