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

from send2trash import send2trash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
TEST_DIR = os.path.join(BASE_DIR, "test_git/")

USERHOME = os.path.abspath(os.path.expanduser('~'))
DESKTOP = os.path.abspath(USERHOME + '/Desktop/'+ "status.txt")
TIMING = datetime.now().strftime("%a_%d_%b_%Y_%H_%M_%S_%p")

def cleanup():
    """Cleanup files"""
    send2trash(STORAGE_DIR)

# keep for later
def kill_process(process):
    if process.poll() is None: # don't send the signal unless it seems it is necessary
        try:
            process.kill()
        except PermissionError: # ignore
            print("Os error. cannot kill kill_process")
            pass

def check_git_support():
    """Check if a git repo can be initialized in present shell"""
    try:
        os.mkdir(TEST_DIR)
    except FileExistsError:
        shutil.rmtree(TEST_DIR)
        os.mkdir(TEST_DIR)

    os.chdir(TEST_DIR)
    process = Popen("git init", stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
    output, _ = process.communicate()
    msg = str(output.decode("utf-8"))
    # print(msg)
    if "Initialized empty Git repository" in msg:
        os.chdir(BASE_DIR)
        send2trash(TEST_DIR)
        return True
    return False

def get_time_str(directory=BASE_DIR):
    """Docstring"""
    path = os.path.abspath(os.path.join(directory, "REPO_STATUS_@_{}.txt".format(TIMING)))
    return path

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

def initialize():
    """Initialize the data necessary for pygit to operate

    Parameters
    -----------
    gitPath : str
        Optional, Path to a git executable, if git is not in your system path.
    masterDirectory : str
        Optional, Full pathname to directory with multiple git repos
    simpleDirectory : list
        A list of full pathname to individual git repos.

    Notes
    ------
    Accepts command line inputs only.
    """
    try:
        os.mkdir(STORAGE_DIR)
    except FileExistsError:
        shutil.rmtree(STORAGE_DIR)
        os.mkdir(STORAGE_DIR)

    storage = shelve.open(os.path.join(STORAGE_DIR, "storage"))
    storage['last_index'] = str(0)

    parser = argparse.ArgumentParser(prog="Pygit. Initialize pygit's working directories.")
    parser.add_argument("-v", "--verbosity", type=int, help="turn verbosity ON/OFF", choices=[0,1])
    parser.add_argument('-g', '--gitPath', help="Full pathname to git executable. cmd or bash.")
    parser.add_argument('-p', '--masterDirectory', help="Full pathname to directory with multiple git repos.")
    parser.add_argument('-r', '--simpleDirectory', help="A list of full pathname to individual git repos.", nargs='+')

    args = parser.parse_args()

    if args.gitPath:
        for _, __, files in os.walk(args.gitPath):
            if "git-cmd.exe" in files:
                storage['GIT_WINDOWS'] = args.gitPath
            elif "git-bash.exe" in files:
                storage['GIT_BASH'] = args.gitPath
            else:
                print("A valid git executable was not found in the directory.\n")
                pass

    else:
        if check_git_support():
            storage['out_of_box_git_support'] = True

            if args.verbosity:
                print("Your system supports git out of the box.\n")
        elif "git" in os.environ['PATH']:
            storage['out_of_box_git_support'] = False

            user_paths = os.environ['PATH'].split(os.pathsep)
            for path in user_paths:
                if "git-cmd.exe" in path:
                    storage['GIT_WINDOWS'] = path
                    break
                if "git-bash.exe" in path:
                    storage['GIT_BASH'] = path
                    break
        else:
            print("Git was not found in your system path.\nYou may need to set the location manually using the -g flag.\n")

    if args.masterDirectory:
        last_index = int(storage['last_index'])

        if args.verbosity:
            print("Master directory set to ", args.masterDirectory, "\n")

        for path, _, __ in os.walk(args.masterDirectory):
            master_absolute_path = os.path.abspath(path)
            if is_git_repo(master_absolute_path):

                if sys.platform == 'win32':
                    name = master_absolute_path.split("\\")[-1]
                if sys.platform == 'linux':
                    name = master_absolute_path.split("/")[-1]

                storage[str(last_index)] = [name, master_absolute_path]
                last_index += 1
        storage['last_index'] = str(last_index)
        storage.close()

    if args.simpleDirectory:
        last_index = int(storage['last_index'])

        for directory in args.simpleDirectory:
            if is_git_repo(directory):
                if sys.platform == 'win32':
                    name = directory.split("\\")[-1]
                if sys.platform == 'linux':
                    name = directory.split("/")[-1]
                storage[str(last_index)] = [name, directory]
            else:
                print(directory, " is not a valid git repo.\nContinuing...")
                continue
            last_index += 1
        storage['last_index'] = str(last_index)
        storage.close()

    if args.verbosity:
        print("Done\nThe following directories were set.\n")
        shelf = shelve.open(os.path.join(STORAGE_DIR, "storage"))

        for key in shelf:
            print(key, "", shelf[key])
            print()
        shelf.close()
    return

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
            print("{} repo may have been moved.\n Run initialize() to update paths".format(self.name))
        self.dir = os.getcwd()

    def fetch(self):
        """git fetch"""
        process = Popen([self.git_exec, "git fetch"], shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        # output, error = process.communicate()
        _, _ = process.communicate()

    def status(self):
        """git status"""
        self.fetch() # always do a fetch before reporting status
        process = Popen([self.git_exec, "git status"], shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        output, _ = process.communicate()
        return str(output.decode("utf-8"))

    def add_all(self, files="."):
        """git add"""
        files = "` ".join(files.split())
        add_file = 'git add {}'.format(files)
        process = Popen([self.git_exec, add_file], shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
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
        process = Popen([self.git_exec, 'git', 'commit', '-m', message], shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE,)
        output, _ = process.communicate()
        return str(output.decode("utf-8"))

    def add_commit(self):
        """git add followed by commit"""
        self.add_all()
        self.commit()

    def push(self):
        """git push"""
        process = Popen([self.git_exec, 'git push'], shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        output, _ = process.communicate()
        return str("Push completed.{}".format(str(output.decode("utf-8"))))

    def pull(self):
        """git pull"""
        process = Popen([self.git_exec, 'git pull'], shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        output, _ = process.communicate()
        return str("Pull completed.\n{}".format(str(output.decode("utf-8"))))

    def reset(self, number='1'):
        """git reset"""
        process = Popen([self.git_exec, 'git reset HEAD~', number], shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
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

def repo_list():
    """Show all available repositories, path, and unique ID"""
    os.system("cls")
    storage = shelve.open(os.path.join(STORAGE_DIR, "storage"))

    for key in storage:
        print("{:2} : {:<30} : {:<}".format(storage[key], storage[key][0], storage[key][1]))

def load(repo_id): # id is string
    """Load a repository with specified id"""
    try:
        with open(IDS, "r") as rhand:
            repo_ids = json.load(rhand)
    except FileNotFoundError:
        print("Please run 'pygit.initialize()' first")
    name = repo_ids.get(repo_id, None)

    with open(REPO_PATH, "r") as rhand:
        paths = json.load(rhand)
    path = paths.get(name, None)

    with open(EXEC_PATH, "r") as rhand:
        git_executable_path = json.load(rhand)
    exe = git_executable_path.get("git", None)
# http://l4wisdom.com/python/python_shelve.php
    storage = shelve.open(os.path.join(STORAGE_DIR, "storage"))


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
        print("Please run 'pygit.initialize()' first")

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

    status_path, timing = get_time_str(STORAGE_DIR)

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
    initialize()
