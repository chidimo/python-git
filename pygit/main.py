#! /usr/bin/python3.6

import os
import sys
import shutil
import shelve
import argparse
import logging

from pathlib import Path, PurePath, PureWindowsPath
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT

from send2trash import send2trash

USERHOME = Path.home()
DESKTOP = USERHOME / 'Desktop'
STATUS_DIR = DESKTOP / "status"
BASE_DIR = Path().resolve() / 'pygit'
SHELF_DIR = Path.joinpath(BASE_DIR, "shelf-dir")
TEST_DIR = Path.joinpath(BASE_DIR, "test-dir")
TIME_STAMP = datetime.now().strftime("%a_%d_%b_%Y_%H_%M_%S_%p")


def logging_def(log_file_name):
    FORMATTER = logging.Formatter("%(asctime)s:%(funcName)s:%(levelname)s\n%(message)s")
    # console_logger = logging.StreamHandler(sys.stdout)
    file_logger = logging.FileHandler(log_file_name)
    file_logger.setFormatter(FORMATTER)

    logger = logging.getLogger(log_file_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_logger)
    logger.propagate = False
    return logger


log_init_process = logging_def('log_init_process.log')


def cleanup():
    """Cleanup files"""
    send2trash(SHELF_DIR)
    return

# keep for later
def kill_process(process):
    if process.poll() is None: # don't send the signal unless it seems it is necessary
        try:
            process.kill()
        except PermissionError: # ignore
            print("Os error. cannot kill kill_process")
            pass
    return


def need_attention(status_msg):
    """Return True if a repo status is not exactly same as that of remote"""
    msg = ["not staged", "behind", "ahead", "Untracked"]
    if any([each in status_msg for each in msg]):
        return True
    return False


def clear_screen():
    if sys.platform == 'win32':
        os.system('cls')
    if sys.platform == 'linux':
        os.system('clear')
    return


def is_git_repo(directory):
    """
    Determine if a folder is a git repo
    Checks the 'git status' message for error
    """
    files = os.listdir(directory)
    if '.git' in files:
        return True
    return False


def check_git_support():
    """
    Return True if git is available via command line.
    If not, check if its available as an executable in installation folder.
    """
    proc = Popen(['git', '--version'], shell=True, stdout=PIPE,)
    msg, _ = proc.communicate()
    msg = msg.decode('utf-8')

    if "git version" in msg:
        return True
    return False


def create_shelves():
    """Create shelves for used by python-git"""
    try:
        Path.mkdir(SHELF_DIR)
    except FileExistsError:
        shutil.rmtree(SHELF_DIR)
        Path.mkdir(SHELF_DIR)

    global NAME_SHELF, INDEX_SHELF

    NAME_SHELF = shelve.open(str(PurePath(SHELF_DIR / "NAME_SHELF"))) # Use the string representation to open path to avoid errors
    INDEX_SHELF = shelve.open(str(PurePath(SHELF_DIR / "INDEX_SHELF")))
    return NAME_SHELF, INDEX_SHELF


def get_command_line_arguments():
    """Get arguments from command line

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

    parser = argparse.ArgumentParser(prog="Pygit. Initialize python git's working directories.")
    parser.add_argument("-v", "--verbosity", type=int, help="turn verbosity ON/OFF", choices=[0,1])
    parser.add_argument("-r", "--rules", help="Set a list of string patterns for folders you don't want pygit to touch", nargs='+')
    parser.add_argument('-g', '--gitPath', help="Full pathname to git executable. cmd or bash.")
    parser.add_argument('-m', '--masterDirectory', help="Full pathname to directory holding any number of git repos.")
    parser.add_argument('-s', '--simpleDirectory', help="A list of full pathnames to any number of individual git repos.", nargs='+')
    parser.add_argument('-t', '--statusDirectory', help="Full pathname to directory for writing out status message.") # make mandatory

    return parser.parse_args()


def handle_git_path(git_path, verbosity):
    """Find and store the location of git executable"""

    if check_git_support():
        print("Your system is configured to work with git.\n")
    elif "git" in os.environ['PATH']:
        user_paths = os.environ['PATH'].split(os.pathsep)
        for path in user_paths:
            if "git-cmd.exe" in path:
                NAME_SHELF['GIT_WINDOWS'] = path
                return
            if "git-bash.exe" in path:
                NAME_SHELF['GIT_BASH'] = path
                return
    else:
        print("Git was not found in your system path.\nYou may need to set the location manually using the -g flag.\n")
            
    if git_path:
        for _, __, files in os.walk(git_path):
            if "git-cmd.exe" in files:
                NAME_SHELF['GIT_WINDOWS'] = git_path
            elif "git-bash.exe" in files:
                NAME_SHELF['GIT_BASH'] = git_path
            else:
                print("A valid git executable was not found in the directory.\n")
                return


def handle_master_directory(master_directory, verbosity, rules):
    """Find and store the locations of git repos"""
    if master_directory:
        if verbosity:
            print("Master directory set to ", master_directory, "\n\n")
            print("Please wait a few minutes while we look inside", master_directory, "\n")

        i = len(list(INDEX_SHELF.keys())) + 1

        folder_paths = [x for x in Path(master_directory).iterdir() if x.is_dir()]
        log_init_process.debug(folder_paths)

        for e in folder_paths: # log folders
            log_init_process.debug(e)

        for folder_name in folder_paths:
            bad_folder_starts = [".", "_"] # skip folders that start with any of these characters
            if any([str(PurePath(folder_name)).startswith(each) for each in bad_folder_starts]) :
                if verbosity:
                    log_init_process.debug(folder_name, " starts with one of ", bad_folder_starts, " skipping\n")
                continue

            path = Path(master_directory) / folder_name
            if rules:
                # if any of the string patterns is found in path folder_name, that folder will be skipped.
                if any([rule in path for rule in rules]):
                    if verbosity:
                        log_init_process.debug(path, " matches a rule. Skipping\n")
                    continue

            directory_absolute_path = Path(path).resolve()

            if is_git_repo(directory_absolute_path):
                if sys.platform == 'win32':
                    name = PureWindowsPath(directory_absolute_path).parts[-1]
                if sys.platform == 'linux':
                    name = PurePath(directory_absolute_path).parts[-1]

                if verbosity:
                    log_init_process.debug(directory_absolute_path, " is a git repository *** shelving\n")
                NAME_SHELF[name] = directory_absolute_path
                INDEX_SHELF[str(i)] = name
                i += 1
        NAME_SHELF.close()
        INDEX_SHELF.close()


def handle_simple_directory(simple_directory, verbosity):
    if simple_directory:

        i = len(list(INDEX_SHELF.keys())) + 1
        for directory in simple_directory:

            if is_git_repo(directory):
                if verbosity:
                    print(directory, " is a git repository *** shelving\n")
                if sys.platform == 'win32':
                    name = directory.split("\\")[-1]
                if sys.platform == 'linux':
                    name = directory.split("/")[-1]
                NAME_SHELF[name] = directory
                INDEX_SHELF[str(i)] = name
            else:
                log_init_process.debug(directory, " is not a valid git repo.\nContinuing...\n")
                continue
            i += 1

        NAME_SHELF.close()
        INDEX_SHELF.close()

def handle_status_directory(status_directory, verbosity):

    global STATUS_DIR
    if status_directory:
        STATUS_DIR = status_directory
        if verbosity:
            print("\nStatus will be saved in {}\n".format(STATUS_DIR))
    else:
        if verbosity:
            print("\nStatus will be saved in {}\n".format(STATUS_DIR))

    if verbosity:
        print("\nDone.\nThe following directories were set.\n")
        NAME_SHELF = shelve.open(str(PurePath(SHELF_DIR / "NAME_SHELF")))
        INDEX_SHELF = shelve.open(str(PurePath(SHELF_DIR / "INDEX_SHELF")))

        print("{:<4} {:<20} {:<}".format("Key", "| Name", "| Path"))
        print("*********************************")
        for key in INDEX_SHELF.keys():
            name = INDEX_SHELF[key]
            print("{:<4} {:<20} {:<}".format(key, name, NAME_SHELF[name]))
        INDEX_SHELF.close()
        NAME_SHELF.close()
    else:
        print("Finished indexing directories")
    return


def initialize():
    """Initialize the data necessary for pygit to operate"""

    clear_screen()
    args = get_command_line_arguments()
    verbosity = args.verbosity
    rules = args.rules

    handle_git_path(args.gitPath, verbosity)
    handle_master_directory(args.masterDirectory, verbosity, rules)
    handle_simple_directory(args.simpleDirectory, verbosity)
    handle_status_directory(args.statusDirectory, verbosity)
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


    def need_attention(self):
        """Return True if a repo status is not exactly same as that of remote"""
        msg = ["not staged", "behind", "ahead", "Untracked"]
        status_msg = self.status()
        if any([each in status_msg for each in msg]):
            return True
        return False


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
            process = Popen([self.git_exec, " git status"], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
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
            process = Popen([self.git_exec, 'git', ' commit ', '-m ', message], stdin=PIPE, stdout=PIPE, stderr=PIPE,)
        else:
            process = Popen(['git', ' commit', ' -m ', message], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,)
        output, _ = process.communicate()
        return str(output.decode("utf-8"))

    def stage_and_commit(self):
        """git add followed by commit"""
        self.stage_all()
        self.commit()

    def push_repo(self):
        """git push"""
        if self.git_exec:
            process = Popen([self.git_exec, ' git push'], stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        else:
            process = Popen(['git push'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,)
        output, _ = process.communicate()
        return str("Push completed.{}".format(str(output.decode("utf-8"))))

    def pull_repo(self):
        """git pull"""
        if self.git_exec:
            process = Popen([self.git_exec, ' git pull'], stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        else:
            process = Popen(['git pull'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,)
        output, _ = process.communicate()
        return str("Pull completed.\n{}".format(str(output.decode("utf-8"))))

    def reset(self, number='1'):
        """git reset"""
        if self.git_exec:
            process = Popen([self.git_exec, ' git reset HEAD~', number], stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
        else:
            process = Popen(['git reset HEAD~', number], stdin=PIPE, stdout=PIPE, stderr=STDOUT,)
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
    NAME_SHELF = shelve.open(str(PurePath(SHELF_DIR / "NAME_SHELF")))
    INDEX_SHELF = shelve.open(str(PurePath(SHELF_DIR / "INDEX_SHELF")))

    print("{:<4} {:<20} {:<}".format("Key", "| Name", "| Path"))
    print("******************************************")
    for key in INDEX_SHELF.keys():
        name = INDEX_SHELF[key]
        print("{:<4} {:<20} {:<}".format(key, name, NAME_SHELF[name]))
    INDEX_SHELF.close()
    NAME_SHELF.close()


def load(input_string): # id is string
    """Load a repository with specified id"""
    NAME_SHELF = shelve.open(str(PurePath(SHELF_DIR / "NAME_SHELF")))
    INDEX_SHELF = shelve.open(str(PurePath(SHELF_DIR / "INDEX_SHELF")))
    input_string = str(input_string)

    try:
        int(input_string) # if not coercible into an integer, then its probably a repo name rather than ID
        try:
            name = INDEX_SHELF[input_string]
            return Commands(name, NAME_SHELF[name])
        except KeyError:
            raise Exception("That index does not exist.")
    except ValueError:
        try:
            return Commands(input_string, NAME_SHELF[input_string])
        except KeyError:
            raise Exception("That repository name does not exist or is not indexed")
    INDEX_SHELF.close()
    NAME_SHELF.close()


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
        NAME_SHELF = shelve.open(str(PurePath(SHELF_DIR / "NAME_SHELF")))
        for key in NAME_SHELF.keys():
            yield load(key)
    else:
        for arg in args:
            yield load(arg)

def pull_repo(*args, _all=False):

    print("Pull repos\n\n")
    for each in load_multiple(*args, _all=_all):
        s = "*** {} ***\n{}".format(each.name, each.pull_repo())
        print(s)

def push_repo(*args, _all=False):

    print("Push  repos\n\n")
    for each in load_multiple(*args, _all=_all):
        s = "*** {} ***\n{}".format(each.name, each.push_repo())
        print(s)

def all_status(status_dir=STATUS_DIR):
    """Write status of all repositories to file in markdown format"""
    clear_screen()
    print("Getting repository status...")
    print("Please enter username and/or password when prompted")
    attention = []

    try:
        Path.mkdir(DESKTOP)
    except FileExistsError:
        pass
    try:
        Path.mkdir(status_dir)
    except FileExistsError:
        pass
    os.chdir(status_dir)

    fname = "REPO_STATUS_@_{}.md".format(TIME_STAMP)

    with open(fname, 'w+') as fhand:
        fhand.write("# Repository status as at {}".format(TIME_STAMP))
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
                print("\n\n***", name, "*** needs attention\n\n")
                attention.append(name)

        fhand.write("-------")
        fhand.write("\n## ATTENTION\n")

        attentions = ["{}. {}".format(index+1, name) for index, name in enumerate(attention)]

        fhand.write("\n".join(attentions))
    print("\n\nDone writing. Please find status files in ", STATUS_DIR)
    os.chdir(BASE_DIR)
    return

if __name__ == "__main__":
    create_shelves()
    print("Name: ", NAME_SHELF, "INdex: ", INDEX_SHELF)
    get_command_line_arguments()
