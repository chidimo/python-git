"""pygit"""

# https://stackoverflow.com/questions/19687394/python-script-to-determine-if-a-directory-is-a-git-repository
# http://gitpython.readthedocs.io/en/stable/

import os
import sys
import shutil
import shelve
import argparse
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT

from send2trash import send2trash

USERHOME = os.path.abspath(os.path.expanduser('~'))
DESKTOP = os.path.abspath(USERHOME + '/Desktop/')
TIMING = datetime.now().strftime("%a_%d_%b_%Y_%H_%M_%S_%p")

STATUS_DIR = os.path.join(DESKTOP ,"status")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELF_DIR = os.path.join(BASE_DIR, "shelves")
TEST_DIR = os.path.join(BASE_DIR, "test_git/")

def clear_screen():
    if sys.platform == 'win32':
        os.system('cls')
    if sys.platform == 'linux':
        os.system('clear')

def cleanup():
    """Cleanup files"""
    send2trash(SHELF_DIR)

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
    process = Popen("git init", shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
    output, _ = process.communicate()
    msg = str(output.decode("utf-8"))
    # print(msg)
    if "Initialized empty Git repository" in msg:
        os.chdir(BASE_DIR)
        shutil.rmtree(TEST_DIR)
        return True
    return False

def is_git_repo(directory):
    """Determine if a folder is a git repo
    Checks for the presence of a .git folder inside a directory
    """
    if ".git" in os.listdir(directory):
        return True
    return False

def need_attention(status):
    """Return True if a repo status is not same as that of remote"""
    msg = ["staged", "behind", "ahead", "Untracked"]
    if any([each in status for each in msg]):
        return True
    return False

def initialize():
    clear_screen()

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
        os.mkdir(SHELF_DIR)
    except FileExistsError:
        shutil.rmtree(SHELF_DIR)
        os.mkdir(SHELF_DIR)

    name_shelf = shelve.open(os.path.join(SHELF_DIR, "name_shelf"))
    index_shelf = shelve.open(os.path.join(SHELF_DIR, "index_shelf"))

    parser = argparse.ArgumentParser(prog="Pygit. Initialize pygit's working directories.")
    parser.add_argument("-v", "--verbosity", type=int, help="turn verbosity ON/OFF", choices=[0,1])
    parser.add_argument("-r", "--rules", help="Set a list of string patterns for folders you don't want pygit to touch", nargs='+')
    parser.add_argument('-g', '--gitPath', help="Full pathname to git executable. cmd or bash.")
    parser.add_argument('-m', '--masterDirectory', help="Full pathname to directory with multiple git repos.")
    parser.add_argument('-s', '--simpleDirectory', help="A list of full pathname to individual git repos.", nargs='+')
    parser.add_argument('-t', '--statusDirectory', help="Full pathname to directory for writing status.") # make mandatory

    args = parser.parse_args()

    if args.gitPath:
        for _, __, files in os.walk(args.gitPath):
            if "git-cmd.exe" in files:
                name_shelf['GIT_WINDOWS'] = args.gitPath
            elif "git-bash.exe" in files:
                name_shelf['GIT_BASH'] = args.gitPath
            else:
                print("A valid git executable was not found in the directory.\n")
                pass

    else:
        if check_git_support():
            if args.verbosity:
                print("Your system supports git out of the box.\n")
        elif "git" in os.environ['PATH']:
            user_paths = os.environ['PATH'].split(os.pathsep)
            for path in user_paths:
                if "git-cmd.exe" in path:
                    name_shelf['GIT_WINDOWS'] = path
                    break
                if "git-bash.exe" in path:
                    name_shelf['GIT_BASH'] = path
                    break
        else:
            print("Git was not found in your system path.\nYou may need to set the location manually using the -g flag.\n")

    if args.masterDirectory:

        if args.verbosity:
            print("Master directory set to ", args.masterDirectory, "\n")
            print("Now working on folders ... Please wait a few minutes.\n")

        i = len(list(index_shelf.keys())) + 1
        for path, _, __ in os.walk(args.masterDirectory):
            if path.startswith("."):
                continue
            if args.rules:
                # if any of the string patterns is found in path name, that folder will be skipped.
                if any([rule in path for rule in args.rules]):
                    if args.verbosity:
                        print(path, " matches a rule. Skipping")
                    continue

            directory_absolute_path = os.path.abspath(path)

            if is_git_repo(directory_absolute_path):
                if sys.platform == 'win32':
                    name = directory_absolute_path.split("\\")[-1]
                if sys.platform == 'linux':
                    name = directory_absolute_path.split("/")[-1]

                name_shelf[name] = directory_absolute_path
                index_shelf[str(i)] = name
                i += 1
        name_shelf.close()
        index_shelf.close()

    if args.simpleDirectory:
        if args.verbosity:
            print("Now shelving the following directories\n")
            print(args.simpleDirectory)

        i = len(list(index_shelf.keys())) + 1
        for directory in args.simpleDirectory:

            if is_git_repo(directory):
                if sys.platform == 'win32':
                    name = directory.split("\\")[-1]
                if sys.platform == 'linux':
                    name = directory.split("/")[-1]

                name_shelf[name] = directory
                index_shelf[str(i)] = name
            else:
                print(directory, " is not a valid git repo.\nContinuing...")
                continue
            i += 1

        name_shelf.close()
        index_shelf.close()

    global STATUS_DIR
    if args.statusDirectory:
        STATUS_DIR = args.statusDirectory
        if args.verbosity:
            print("\nStatus files to be saved in {}\n".format(STATUS_DIR))
    else:
        if args.verbosity:
            print("\nStatus files to be saved in {}\n".format(STATUS_DIR))

    if args.verbosity:
        print("\nDone.\nThe following directories were set.\n")
        name_shelf = shelve.open(os.path.join(SHELF_DIR, "name_shelf"))
        index_shelf = shelve.open(os.path.join(SHELF_DIR, "index_shelf"))

        print("{:<4} {:<20} {:<}".format("Key", "| Name", "| Path"))
        print("****************************")
        for key in index_shelf.keys():
            name = index_shelf[key]
            print("{:<4} {:<20} {:<}".format(key, name, name_shelf[name]))
        index_shelf.close()
        name_shelf.close()
    return

class Commands:
    """Commands class

    Parameters
    -----------
    repo_name : str
        The repository name. See list of repositories by running
    master_directory : str
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
        return "Commands: {}: {}".format(self.name, self.dir)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __init__(self, repo_name, master_directory, git_exec=None, message="minor changes"):
        self.name = repo_name
        self.dir = master_directory
        self.git_exec = git_exec
        self.message = message

        try:
            os.chdir(self.dir)
        except (FileNotFoundError, TypeError):
            print("{} may have been moved.\n Run initialize() to update paths".format(self.name))
        self.dir = os.getcwd()

    def fetch(self):
        """git fetch"""
        if self.git_exec:
            process = Popen([self.git_exec, "git fetch"], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        else:
            process = Popen("git fetch", shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        # output, error = process.communicate()
        process.communicate()

    def status(self):
        """git status"""
        self.fetch() # always do a fetch before reporting status
        if self.git_exec:
            process = Popen([self.git_exec, "git status"], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        else:
            process = Popen("git status", shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        output, _ = process.communicate()
        return str(output.decode("utf-8"))

    def stage_file(self, file_name):
        """git add file"""
        stage_file = 'git add {}'.format(file_name)
        if self.git_exec:
            process = Popen([self.git_exec, stage_file], stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        else:
            process = Popen(stage_file, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT,)

        output, _ = process.communicate()
        return str(output.decode("utf-8"))

    def stage_all(self, files="."):
        """git add all"""
        files = "` ".join(files.split())
        stage_file = 'git add {}'.format(files)
        if self.git_exec:
            process = Popen([self.git_exec, stage_file], stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        else:
            process = Popen(stage_file, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT,)

        process = Popen([self.git_exec, stage_file], stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        output, _ = process.communicate()
        return str(output.decode("utf-8"))

    def commit(self):
        """git commit"""
        enter = input("Commit message.\nPress enter to use 'minor changes'")
        if enter == "":
            message = self.message
        else:
            message = enter
        # message = "` ".join(message.split())
        if self.git_exec:
            process = Popen([self.git_exec, 'git', 'commit', '-m', message], stdin=PIPE, stdout=PIPE, stderr=PIPE,)
        else:
            process = Popen(['git', 'commit', '-m', message], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,)
        output, _ = process.communicate()
        return str(output.decode("utf-8"))

    def stage_and_commit(self):
        """git add followed by commit"""
        self.stage_all()
        self.commit()

    def push(self):
        """git push"""
        process = Popen([self.git_exec, 'git push'], stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        output, _ = process.communicate()
        return str("Push completed.{}".format(str(output.decode("utf-8"))))

    def pull(self):
        """git pull"""
        process = Popen([self.git_exec, 'git pull'], stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        output, _ = process.communicate()
        return str("Pull completed.\n{}".format(str(output.decode("utf-8"))))

    def reset(self, number='1'):
        """git reset"""
        process = Popen([self.git_exec, 'git reset HEAD~', number], stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
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

def show_repos():
    """Show all available repositories, path, and unique ID"""
    clear_screen()
    print("\nThe following repos are available.\n")
    name_shelf = shelve.open(os.path.join(SHELF_DIR, "name_shelf"))
    index_shelf = shelve.open(os.path.join(SHELF_DIR, "index_shelf"))

    print("{:<4} {:<20} {:<}".format("Key", "| Name", "| Path"))
    print("******************************************")
    for key in index_shelf.keys():
        name = index_shelf[key]
        print("{:<4} {:<20} {:<}".format(key, name, name_shelf[name]))
    index_shelf.close()
    name_shelf.close()

def load(input_string): # id is string
    """Load a repository with specified id"""
    name_shelf = shelve.open(os.path.join(SHELF_DIR, "name_shelf"))
    index_shelf = shelve.open(os.path.join(SHELF_DIR, "index_shelf"))
    input_string = str(input_string)

    try:
        int(input_string) # if not coercible into an integer, then its probably a repo name rather than ID
        try:
            name = index_shelf[input_string]
            return Commands(name, name_shelf[name])
        except KeyError:
            raise Exception("That index does not exist.")
            return
    except ValueError:
        try:
            return Commands(input_string, name_shelf[input_string])
        except KeyError:
            raise Exception("That repository name does not exist")
            return
    index_shelf.close()
    name_shelf.close()

def load_multiple(*args, _all=False):
    """Create `commands` object for a set of repositories

    Parameters
    ------------
    args : int
        comma-separated string values

    Yields
    ---------
    A list of commands objects. One for each of the entered string
    """

    if _all:
        name_shelf = shelve.open(os.path.join(SHELF_DIR, "name_shelf"))
        for key in name_shelf.keys():
            yield load(key)
    else:
        for each in args:
            yield load(each)

def pull(*args, _all=False):
    """Pull all repositories"""
    print("Pull repositories\n\n")
    for each in load_multiple(_all=True):
        print("***", each.name, "***")
        print(each.pull())
        print()

def push(*args, _all=False):
    """Pull all repositories"""
    print("Push  directories\n\n")
    for each in load_multiple(_all=True):
        print("***", each.name, "***")
        print(each.push(), "\n")

def all_status(status_dir=STATUS_DIR):
    """Write status of all repositories to text file"""
    os.system("cls")
    print("Getting repository status...Please be patient")
    attention = []

    try:
        os.mkdir(DESKTOP)
    except FileExistsError:
        pass
    try:
        os.mkdir(status_dir)
    except FileExistsError:
        pass
    os.chdir(status_dir)

    fname = "REPO_STATUS_@_{}.md".format(TIMING)

    with open(fname, 'w+') as fhand:
        fhand.write("# Repository status as at {}".format(TIMING))
        fhand.write("\n\n")
        for each in load_multiple(_all=True):
            name = each.name
            status = each.status()

            heading = "## {}".format(name)
            fhand.write(heading)
            fhand.write("\n\n")
            fhand.write(status)
            fhand.write("\n")

            if need_attention(status):
                attention.append(name)

        fhand.write("-------")
        fhand.write("\n## ATTENTION\n")

        attentions = ["{}. {}".format(index+1, name) for index, name in enumerate(attention)]

        fhand.write("\n".join(attentions))
    print("\n\nDone writing. Please check the status folder on your desktop")
    os.chdir(BASE_DIR)

if __name__ == "__main__":
    initialize()
