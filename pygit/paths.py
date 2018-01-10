"""Paths"""

import os
from datetime import datetime

TOP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERHOME = os.path.abspath(os.path.expanduser('~'))
BASE_PATH = os.path.join(TOP_DIR, "pygit_files")
TIMING = datetime.now().strftime("%a_%d_%b_%Y_%H_%M_%S_%p")

def get_time_str(directory):
    """Docstring"""
    timing = datetime.now().strftime("%a_%d_%b_%Y_%H_%M_%S_%p")
    path = os.path.abspath(os.path.join(directory, "REPO_STATUS_{}.txt".format(timing)))
    return path, timing

SEARCH_PATHS = os.path.abspath(os.path.join(BASE_PATH, "search_path.json"))
REPO_PATH = os.path.abspath(os.path.join(BASE_PATH, "repo_path.json"))
EXEC_PATH = os.path.abspath(os.path.join(BASE_PATH, "exec_path.json"))
IDS = os.path.abspath(os.path.join(BASE_PATH, "id_path.json"))
DESKTOP = os.path.abspath(USERHOME + '/Desktop/'+ "status.txt")

FILE_WIN = r"git-cmd.exe"
FILE_BASH = r"git-bash.exe"
