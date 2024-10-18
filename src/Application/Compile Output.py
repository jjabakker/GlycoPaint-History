from tkinter import *

from src.Automation.Support.Compile_Output import CompileDialog

root = Tk()
root.eval('tk::PlaceWindow . center')
CompileDialog(root)
root.mainloop()