# stream = '$AC;IVER3-3089;$OSI,8080808080,S,1,30.36342050,-89.09611017,0.00,162.91,N,6.204,P0,-1.8894,test_5D\r\n'
# # stream= "$AC;IVER3-3089;$OSI,FAFAD5D5C1,N,12,30.35313633,-89.62795283,3.12,37.97,N,15.404,P0,-1.5404,manualLownmoer,0.0792,139.5,0.3,66.5,False,IVER3-3089,3.0,True,False*69\r\n"
# import re
#
#
# def test(stream):
#     if not stream.startswith('$AC') and not re.search('\*', stream):
#         print("hello")
#         return None
#     print('dddddd')
# test(stream)

import tkinter as tk
from tkinter import messagebox

root = tk.Tk()

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()