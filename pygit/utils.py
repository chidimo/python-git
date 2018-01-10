"""Utilities module"""

import os
import json
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
from .paths import FILE_WIN, FILE_BASH, REPO_PATH, SEARCH_PATHS, EXEC_PATH

def is_git_repo(directory):
    """Determine if a folder is a git repo

    Checks for the presence of a .git folder inside a directory
    """
    if ".git" in os.listdir(directory):
        return True
    return False

def need_attention(status):
    """Return True if a repo status is not same as that of remote"""
    msg = ["Changes not staged for commit", "Your branch is behind", "Your branch is ahead"]
    if any([each in status for each in msg]):
        return True
    return False

def select_directory(title="Select directory"):
    """Select and return a directory path"""
    root = tk.Tk()
    root.withdraw()
    initial_dir = "/"
    root_dir = filedialog.askdirectory(parent=root,
                                       initialdir=initial_dir,
                                       title=title)
    return root_dir

def set_search_paths():
    """Set search paths for repo and git executable"""
    repo_search_path = select_directory(title="Select path to scan for repo directories")
    git_search_path = select_directory(title="Select path to scan for git executable")

    search_path = {}
    search_path["repos"] = repo_search_path
    search_path["execs"] = git_search_path

    with open(SEARCH_PATHS, "w+") as fhand:
        json.dump(search_path, fhand)

def get_repos_and_git():
    """Return a list of all git repo paths, names and git exec path"""

    with open(SEARCH_PATHS, "r+") as rhand:
        spaths = json.load(rhand)

    repo_dir = spaths["repos"]
    git_repos = [os.path.abspath(root) for root, _, __ in os.walk(repo_dir) if is_git_repo(root)]
    names = [each.split("\\")[-1] for each in git_repos]

    git_dir = spaths["execs"]
    execs = {}
    for root, _, files in os.walk(git_dir):
        if FILE_WIN in files:
            exec_path = os.path.abspath(os.path.join(root, FILE_WIN))
            execs["win"] = exec_path
        if FILE_BASH in files:
            exec_path = os.path.abspath(os.path.join(root, FILE_BASH))
            execs["bash"] = exec_path
    return git_repos, names, execs

def set_input_data(git_type="win"):
    """populate all input data

    Notes
    ------
    The following details are exported to file

    1. Repo names
    2. Repo directories
    3. Git executable path
    """
    repo_path = {}
    exec_path = {}
    repos, names, git_path = get_repos_and_git()

    exec_path["git"] = git_path[git_type]
    with open(EXEC_PATH, "w") as fhand:
        json.dump(exec_path, fhand)

    for name, repo in zip(names, repos):
        repo_path[name] = repo
    with open(REPO_PATH, "w+") as fhand:
        json.dump(repo_path, fhand)
    return repo_path # need this for set_all()

def main():
    """Do nothing"""
    return

if __name__ == "__main__":
    main()
