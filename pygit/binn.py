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

import os, sys, site

# https://stackoverflow.com/questions/36187264/how-to-get-installation-directory-using-setuptools-and-pkg-ressources
def binaries_directory():
    """Return the installation directory, or None"""
    if '--user' in sys.argv:
        paths = (site.getusersitepackages(),)
    else:
        py_version = '%s.%s' % (sys.version_info[0], sys.version_info[1])
        paths = (s % (py_version) for s in (
            sys.prefix + '/lib/python%s/dist-packages/',
            sys.prefix + '/lib/python%s/site-packages/',
            sys.prefix + '/local/lib/python%s/dist-packages/',
            sys.prefix + '/local/lib/python%s/site-packages/',
            '/Library/Python/%s/site-packages/',
        ))

    for path in paths:
        if os.path.exists(path):
            return path
    print('no installation path found', file=sys.stderr)
    return None
