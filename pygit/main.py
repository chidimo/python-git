"""pygit"""

# https://stackoverflow.com/questions/19687394/python-script-to-determine-if-a-directory-is-a-git-repository
# http://gitpython.readthedocs.io/en/stable/

import os
import sys
import json
import shutil
import shelve
import argparse
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT

try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    print("tkinter was not found.")
    pass

from send2trash import send2trash


TOP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERHOME = os.path.abspath(os.path.expanduser('~'))
BASE_PATH = os.path.join(TOP_DIR, "pygit_files")
TIMING = datetime.now().strftime("%a_%d_%b_%Y_%H_%M_%S_%p")

SEARCH_PATHS = os.path.abspath(os.path.join(BASE_PATH, "search_path.json"))
REPO_PATH = os.path.abspath(os.path.join(BASE_PATH, "repo_path.json"))
EXEC_PATH = os.path.abspath(os.path.join(BASE_PATH, "exec_path.json"))
IDS = os.path.abspath(os.path.join(BASE_PATH, "id_path.json"))
DESKTOP = os.path.abspath(USERHOME + '/Desktop/'+ "status.txt")

FILE_WIN = r"git-cmd.exe"
FILE_BASH = r"git-bash.exe"


def get_time_str(directory):
    """Docstring"""
    timing = datetime.now().strftime("%a_%d_%b_%Y_%H_%M_%S_%p")
    path = os.path.abspath(os.path.join(directory, "REPO_STATUS_@_{}.txt".format(timing)))
    return path, timing

def is_git_repo(directory):
    """Determine if a folder is a git repo
    Checks for the presence of a .git folder inside a directory
    """
    if ".git" in os.listdir(directory):
        return True
    return False

def need_attention(status):
    """Return True if a repo status is not same as that of remote"""
    msg = ["staged", "behind", "ahead"]
    if any([each in status for each in msg]):
        return True
    return False

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

def get_and_store_repository_and_git_paths():
    storage = shelve.open("storage_paths")

    parser = argparse.ArgumentParser(prog="Pygit. Set directories")
    parser.add_argument("-v", "--verbosity", type=int, help="turn verbosity ON/OFF", choices=[0,1])
    parser.add_argument('-g', '--gitPath', help="Path to git executable. cmd or bash")
    parser.add_argument('-p', '--repoMpath', help="Path to directory with multiple git repos")
    parser.add_argument('-r', '--repoPath', help="Path to single git repo", nargs='+')

    args = parser.parse_args()

    if args.gitPath:
        storage['gitPath'] = gitPath
    else:
        user_path = os.environ['PATH']
        if git in user_path:
            storage['gitPath'] = user_path
        else:
            print('Git was not found on your system path.\nPlease set it manually')
            pass
    if args.repoMpath:







def set_search_paths():
    """Set search paths for repo and git executable"""
    repo_search_path = select_directory(title="Select path to scan for REPO directories")
    git_search_path = select_directory(title="Select path to scan for GIT executable")

    search_path = {}
    search_path["repos"] = repo_search_path
    search_path["execs"] = git_search_path

    with open(SEARCH_PATHS, "w+") as fhand:
        json.dump(search_path, fhand)

def git_repo_path_and_exec_path():
    """Return a list of all git repo paths, names and git executable path"""

    with open(SEARCH_PATHS, "r+") as rhand:
        spaths = json.load(rhand)

    repository_directory = spaths["repos"]
    git_repos = [os.path.abspath(root) for root, _, __ in os.walk(repository_directory) if is_git_repo(root)]
    names = [each.split("\\")[-1] for each in git_repos]

    git_directory = spaths["execs"]
    execs = {}
    for root, _, files in os.walk(git_directory):
        if FILE_WIN in files:
            git_executable_path = os.path.abspath(os.path.join(root, FILE_WIN))
            execs["win"] = git_executable_path
        if FILE_BASH in files:
            git_executable_path = os.path.abspath(os.path.join(root, FILE_BASH))
            execs["bash"] = git_executable_path
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
    repository_path = {}
    git_executable_path = {}
    repos, names, git_path = git_repo_path_and_exec_path()

    git_executable_path["git"] = git_path[git_type]
    with open(EXEC_PATH, "w") as fhand:
        json.dump(git_executable_path, fhand)

    for name, repo in zip(names, repos):
        repository_path[name] = repo
    with open(REPO_PATH, "w+") as fhand:
        json.dump(repository_path, fhand)
    return repository_path # need this for set_all()

class Commands:
    """Commands class

    Parameters
    -----------
    repo_name : str
        The repository name. See list of repositories by running
    repository_directory : str
        The absolute path to the directory
    git_exec : str
        The path to the git executable on the system
    message : str
        Commit message

    Returns
    --------
    : Commands object
	"""

    def __str__(self):
        return "{}: {}".format(self.name, self.dir)

    def __init__(self, repo_name, repository_directory, git_exec, message="minor changes"):
        self.name = repo_name
        self.dir = repository_directory
        self.git_exec = git_exec
        self.message = message

        try:
            os.chdir(self.dir)
        except (FileNotFoundError, TypeError):
            print("{} repo may have been moved.\n Run set_all() to update paths".format(self.name))
        self.dir = os.getcwd()

    def fetch(self):
        """git fetch"""
        process = Popen([self.git_exec, "git fetch"], shell=True,
                        stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        # output, error = process.communicate()
        _, _ = process.communicate()

    def status(self):
        """git status"""
        self.fetch() # always do a fetch before reporting status
        process = Popen([self.git_exec, "git status"], shell=True,
                        stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        output, _ = process.communicate()
        return str(output.decode("utf-8"))

    def add_all(self, files="."):
        """git add"""
        files = "` ".join(files.split())
        add_file = 'git add {}'.format(files)
        process = Popen([self.git_exec, add_file],
                        shell=True, stdin=PIPE, stdout=PIPE,
                        stderr=STDOUT,)
        output, _ = process.communicate()
        return str(output.decode("utf-8"))

    def commit(self):
        """git commit"""
        msg = "Commit message.\nPress enter to use 'minor changes'"
        enter = input(msg)
        if enter == "":
            message = self.message
        else:
            message = enter
        # message = "` ".join(message.split())
        process = Popen([self.git_exec, 'git', 'commit', '-m', message],
                        shell=False, stdin=PIPE, stdout=PIPE,
                        stderr=PIPE,)
        output, _ = process.communicate()
        return str(output.decode("utf-8"))

    def add_commit(self):
        """git add followed by commit"""
        self.add_all()
        self.commit()

    def push(self):
        """git push"""
        process = Popen([self.git_exec, 'git push'], shell=True,
                        stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        output, _ = process.communicate()
        return str("Push completed.{}".format(str(output.decode("utf-8"))))

    def pull(self):
        """git pull"""
        process = Popen([self.git_exec, 'git pull'], shell=True,
                        stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        output, _ = process.communicate()
        return str("Pull completed.\n{}".format(str(output.decode("utf-8"))))

    def reset(self, number='1'):
        """git reset"""
        process = Popen([self.git_exec, 'git reset HEAD~', number], shell=True,
                        stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        output, _ = process.communicate()
        return str(output.decode("utf-8"))

    # def branch(self):
    #     """Return the branch being tracked by local"""
    #     process = Popen([self.git_exec, 'git branch -vv'], shell=True,
    #                     stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
    #     output, _ = process.communicate()
    #     out_text = str(output.decode("utf-8"))
    #     try:
    #         line = [each for each in out_text.split("\n") if each.startswith("*")][0]
    #     except IndexError: # no lines start with *
    #         return
    #     branch_name = re.search(r"\[origin\/(.*)\]", line)
    #     return branch_name.group(1)

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
    """Cleanup files"""
    send2trash(BASE_PATH)

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
        git_executable_path = json.load(rhand)
    exe = git_executable_path.get("git", None)

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
