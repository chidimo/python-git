"""API"""

import os
import json
import shutil
from glob import glob
from subprocess import Popen
from send2trash import send2trash
from .paths import REPO_PATH, IDS, EXEC_PATH, BASE_PATH
from .commands import Commands
from .utils import set_search_paths, set_input_data, need_attention, get_time_str

def set_all(git_type="win"):
    """Set all directories on first run"""
    if os.path.exists(BASE_PATH):
        msg1 = "\n\t{} already exists\n".format(BASE_PATH)
        msg2 = "\tWhat would you like to do?\n\n"
        msg3 = "\t1 ===== Regenerate\n"
        msg4 = "\t2 ===== Leave as is\n"
        decide = input(msg1 + msg2 + msg3 + msg4)

        if decide == "1":
            try:
                os.mkdir(BASE_PATH)
            except FileExistsError:
                shutil.rmtree(BASE_PATH)
                try:
                    os.mkdir(BASE_PATH)
                except PermissionError:
                    print("Please exit the folder before running set_all()")
            set_search_paths()
        elif decide == "2":
            print("File unchanged")
            return
    else:
        os.mkdir(BASE_PATH)
        set_search_paths()
    repos = set_input_data(git_type=git_type)

    ids = {} # set string-valued ids
    for ind, val in enumerate(repos):
        ids[ind] = val
    with open(IDS, "w+") as whand:
        json.dump(ids, whand)

def cleanup():
    """Clear all files"""
    files = glob(os.path.join(BASE_PATH, "*_path.json"))
    _ = [send2trash(each) for each in files]

def repo_list():
    """Show all available repositories, path, and unique ID"""
    os.system("cls")
    with open(IDS, "r") as rhand:
        repo_ids = json.load(rhand)

    with open(REPO_PATH, "r") as rhand:
        paths = json.load(rhand)

    for rep_id, rep_name in zip(repo_ids.keys(), repo_ids.values()):
        print("{:2} : {:<30} : {:<}".format(rep_id, rep_name, paths.get(rep_name, None)))

def load(repo_id): # id is string
    """Load a repository with specified id"""
    try:
        with open(IDS, "r") as rhand:
            repo_ids = json.load(rhand)
    except FileNotFoundError:
        print("Please run 'pygit.set_all()' first")
    name = repo_ids.get(repo_id, None)

    with open(REPO_PATH, "r") as rhand:
        paths = json.load(rhand)
    path = paths.get(name, None)

    with open(EXEC_PATH, "r") as rhand:
        exec_path = json.load(rhand)
    exe = exec_path.get("git", None)

    return Commands(name, path, exe)

def load_set(*args):
    """Create `commands` object for a set of repositories

    Parameters
    ------------
    args : int
        comma-separated string values

    Yields
    ---------
    A list of commands objects. One for each of the entered string
    """
    for each in args:
        yield load(each)

def load_all():
    """Load all repositories

    Yields
    --------
    command object of each repo
    """
    try:
        with open(IDS, "r") as rhand:
            repo_ids = json.load(rhand)
    except FileNotFoundError:
        print("Please run 'pygit.set_all()' first")

    for each in repo_ids.keys():
        yield load(each)

def pull_all():
    """Pull all repositories"""
    os.system("cls")
    print("Pulling all directories\n\n")
    for each in load_all():
        print("***", each.name, "***")
        print(each.pull())
        print()

def push_all():
    """Pull all repositories"""
    os.system("cls")
    print("Pushing all directories\n\n")
    for each in load_all():
        print("***", each.name, "***")
        print(each.push())
        print()

def status_all():
    """Write status of all repositories to text file"""
    os.system("cls")
    print("Getting repository status...Please be patient")
    attention = []

    status_path, timing = get_time_str(BASE_PATH)

    with open(status_path, 'w+') as fhand:
        fhand.write("Repository status as at {}".format(timing))
        fhand.write("\n\n")
        for each in load_all():
            name = each.name
            stat = each.status()
            heading = "*** {} ***".format(name)
            fhand.write(heading + "\n")
            fhand.write(stat + "\n\n\n")
            if need_attention(stat):
                attention.append(name)
        fhand.write("**"*25)
        fhand.write("\nThe following repos need attention\n\n")
        fhand.write("\n".join(attention))
    _ = Popen(["notepad.exe", status_path])

if __name__ == "__main__":
    pass
