"""Graphical directory selection"""

try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    print("tkinter was not found.")
    pass


def select_directory(title="Select directory"):
    """Select and return a directory path"""
    try:
        root = tk.Tk()
        root.withdraw()
        initialdir = "/"
        root_dir = filedialog.askdirectory(parent=root,
                                        initialdir=initialdir,
                                       title=title)
    except:
        print("Tk inter was not found.")
    return root_dir
