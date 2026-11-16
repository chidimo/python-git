#! /usr/bin/python3.6

import argparse
import logging
import os
import shelve
import shutil
import sys
from datetime import datetime
from pathlib import Path, PurePath, PureWindowsPath
from subprocess import PIPE, STDOUT, Popen

from send2trash import send2trash

BASE_DIR = Path.home()
DESKTOP = BASE_DIR / 'Desktop'
SHELF_DIR = BASE_DIR / 'python-git-shelf'
STATUS_DIR = BASE_DIR / 'python-git-status'
TEST_DIR = BASE_DIR / "TEST_FOLDER"

def logging_def(log_file_name):
    FORMATTER = logging.Formatter("%(asctime)s:%(funcName)s:%(levelname)s\n%(message)s")
    file_logger = logging.FileHandler(log_file_name)
    file_logger.setFormatter(FORMATTER)

    logger = logging.getLogger(log_file_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_logger)
    logger.propagate = False
    return logger


pygit_logger = logging_def('pygit_logger.log')
# logging.disable(logging.CRITICAL)


class PygitException(Exception):
    """An exception just occurred"""


def show_verbose_output(verbosity, *args):
    """Logs output"""
    if verbosity:
        for arg in args:
            pygit_logger.debug(arg)


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


def need_attention(status_msg):
    """Return True if a repo status is not exactly same as that of remote"""
    msg = ["not staged", "behind", "ahead", "Untracked"]
    return any(each in status_msg for each in msg)


def is_git_repo(directory):
    """
    Determine if a folder is a git repo
    Checks the 'git status' message for error
    """
    files = os.listdir(directory)
    return '.git' in files


def run_git(*args, git_exec=None, stderr=STDOUT):
    """Run `git *args` in the current directory and return its stdout as text.

    Arguments are passed to git as a list and never through a shell, so values
    such as file names or commit messages are treated as single arguments and
    cannot inject commands. If `git_exec` is given, it is used as a wrapper
    executable that is invoked as `git_exec git *args`.
    """
    command = ['git', *args]
    if git_exec:
        command = [git_exec] + command
    process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=stderr)
    output, _ = process.communicate()
    return output.decode("utf-8")


def check_git_support():
    """
    Return True if git is available via command line.
    If not, check if its available as an executable in installation folder.
    """
    try:
        return "git version" in run_git('--version')
    except OSError: # git is not on the path
        return False


def get_command_line_arguments():
    """Get arguments from command line"""

    parser = argparse.ArgumentParser(prog="Pygit. Initialize working directories for python-git")
    parser.add_argument("-v", "--verbosity", type=int, help="turn verbosity ON/OFF", choices=[0,1])
    parser.add_argument("-r", "--rules", help="Set a list of string patterns for folders to skip during setup", nargs='+')
    parser.add_argument('-g', '--gitPath', help="Full pathname to git executable. cmd or bash.")
    parser.add_argument('-m', '--mainDirectory', help="Full pathname to directory holding any number of git repos.")
    parser.add_argument('-s', '--simpleDirectory', help="A list of full pathnames to any number of individual git repos.", nargs='+')
    return parser.parse_args()


def shelve_git_path(git_path, _verbosity):
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


def enforce_exclusion(folder_name, verbosity):
    """Return True if a folder starts with any character in exclusion_folder_start"""
    exclusion_folder_start = [".", "_"] # skip folders that start with any of these characters
    if any(str(PurePath(folder_name)).startswith(each) for each in exclusion_folder_start):
        if verbosity:
            show_verbose_output(verbosity, folder_name, " starts with one of ", exclusion_folder_start, " skipping\n")
        return True
    return False


def match_rule(rules, path, verbosity):
    """Return True if a folder matches a rule in rules"""
    if rules and  any(rule in path for rule in rules):
        show_verbose_output(verbosity, path, " matches an exclusion rule. Skipping\n")
        return True
    return False


def save_main(main_directory):
    """Saves the location of the main directory"""
    global MAIN_SHELF
    MAIN_SHELF = shelve.open(str(PurePath(SHELF_DIR / "MAIN_SHELF")))
    MAIN_SHELF["main"] = main_directory
    MAIN_SHELF.close()


def shelve_main_directory(main_directory, verbosity, rules):
    """Find and store the locations of git repos"""

    if main_directory:
        save_main(main_directory)
        show_verbose_output(verbosity, "Main directory set to ", main_directory, "Now Shelving")

        i = len(list(INDEX_SHELF.keys())) + 1
        folder_paths = [x for x in Path(main_directory).iterdir() if x.is_dir()]

        for f in folder_paths: # log folders
            show_verbose_output(verbosity, f)

        for folder_name in folder_paths:
            path = Path(main_directory) / folder_name
            if enforce_exclusion(folder_name, verbosity):
                continue
            if match_rule(rules, path, verbosity):
                continue

            directory_absolute_path = Path(path).resolve()
            if is_git_repo(directory_absolute_path):
                if sys.platform == 'win32':
                    name = PureWindowsPath(directory_absolute_path).parts[-1]
                if sys.platform == 'linux':
                    name = PurePath(directory_absolute_path).parts[-1]

                show_verbose_output(verbosity, directory_absolute_path, " is a git repository *** shelving\n")

                NAME_SHELF[name] = directory_absolute_path
                INDEX_SHELF[str(i)] = name
                i += 1


def shelve_simple_directory(simple_directory, verbosity):
    if simple_directory:

        i = len(list(INDEX_SHELF.keys())) + 1
        for directory in simple_directory:

            if is_git_repo(directory):
                show_verbose_output(verbosity, " is a git repository *** shelving\n")
                if sys.platform == 'win32':
                    name = directory.split("\\")[-1]
                if sys.platform == 'linux':
                    name = directory.split("/")[-1]
                NAME_SHELF[name] = directory
                INDEX_SHELF[str(i)] = name
            else:
                show_verbose_output(verbosity, " is not a valid git repo.\nContinuing...\n")
                continue
            i += 1


def initialize():
    """Initialize the data necessary for pygit to operate"""
    print("Initializing ...")

    global NAME_SHELF, INDEX_SHELF
    try:
        Path.mkdir(SHELF_DIR)
    except FileExistsError:
        shutil.rmtree(SHELF_DIR)
        Path.mkdir(SHELF_DIR)

    try:
        Path.mkdir(STATUS_DIR)
    except FileExistsError:
        pass

    NAME_SHELF = shelve.open(str(PurePath(SHELF_DIR / "NAME_SHELF"))) # Use the string representation to open path to avoid errors
    INDEX_SHELF = shelve.open(str(PurePath(SHELF_DIR / "INDEX_SHELF")))

    args = get_command_line_arguments()
    verbosity = args.verbosity
    rules = args.rules
    shelve_git_path(args.gitPath, verbosity)
    shelve_main_directory(args.mainDirectory, verbosity, rules)
    shelve_simple_directory(args.simpleDirectory, verbosity)

    INDEX_SHELF.close()
    NAME_SHELF.close()

    if verbosity:
        print("\nIndexed git repos.\n")
        NAME_SHELF = shelve.open(str(PurePath(SHELF_DIR / "NAME_SHELF")))
        INDEX_SHELF = shelve.open(str(PurePath(SHELF_DIR / "INDEX_SHELF")))

        print(f"Status saved in {STATUS_DIR}")
        print("{:<4} {:<20} {:<}".format("Key", "| Name", "| Path"))
        print("*********************************")
        for key in INDEX_SHELF.keys():
            name = INDEX_SHELF[key]
            print(f"{key:<4} {name:<20} {NAME_SHELF[name]!s:<}")
    else:
        print("Indexing done")


def update():
    """Update INDEX_SHELF"""
    NAME_SHELF = shelve.open(str(PurePath(SHELF_DIR / "NAME_SHELF")))
    INDEX_SHELF = shelve.open(str(PurePath(SHELF_DIR / "INDEX_SHELF")))
    MAIN_SHELF = shelve.open(str(PurePath(SHELF_DIR / "MAIN_SHELF")))

    main = MAIN_SHELF["main"]
    print(f"Main {main}")
    save_main(main)

    i = len(list(INDEX_SHELF.keys())) + 1
    folder_paths = [x for x in Path(main).iterdir() if x.is_dir()]

    for folder_name in folder_paths:
        path = Path(main) / folder_name

        directory_absolute_path = Path(path).resolve()
        if is_git_repo(directory_absolute_path):
            if sys.platform == 'win32':
                name = PureWindowsPath(directory_absolute_path).parts[-1]
            if sys.platform == 'linux':
                name = PurePath(directory_absolute_path).parts[-1]

            NAME_SHELF[name] = directory_absolute_path
            INDEX_SHELF[str(i)] = name
            i += 1

    print("Update completed successfully")


class Commands:
    """Commands class

    Parameters
    -----------
    repo_name : str
        The repository name. See list of repositories by running
    main_directory : str
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
        return f"Commands: {self.name}: {self.dir}"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __init__(self, repo_name, main_directory, git_exec=None, message="minor changes"):
        self.name = repo_name
        self.dir = main_directory
        self.git_exec = git_exec
        self.message = message

        try:
            os.chdir(self.dir)
        except (FileNotFoundError, TypeError):
            print(f"{self.name} may have been moved.\n Run initialize() to update paths")
        self.dir = os.getcwd()


    def need_attention(self):
        """Return True if a repo status is not exactly same as that of remote"""
        msg = ["not staged", "behind", "ahead", "Untracked"]
        status_msg = self.status()
        return any(each in status_msg for each in msg)

    def _git(self, *args, stderr=STDOUT):
        """Run a git command with this object's git executable."""
        return run_git(*args, git_exec=self.git_exec, stderr=stderr)

    def fetch(self):
        """git fetch"""
        self._git('fetch')

    def status(self):
        """git status"""
        self.fetch() # always do a fetch before reporting status
        return self._git('status')

    def stage_file(self, file_name):
        """git add file"""
        # "--" stops git from treating a file_name that begins with "-" as an option.
        return self._git('add', '--', str(file_name))

    def stage_all(self, files="."):
        """git add all"""
        return self._git('add', '--', *files.split())

    def commit(self):
        """git commit"""
        enter = input("Commit message.\nPress enter to use 'minor changes'")
        if enter == "":
            message = self.message
        else:
            message = enter
        return self._git('commit', '-m', message, stderr=PIPE)

    def stage_and_commit(self):
        """git add followed by commit"""
        self.stage_all()
        self.commit()

    def push(self):
        """git push"""
        return f"Push completed.{self._git('push', stderr=PIPE)}"

    def pull(self):
        """git pull"""
        return f"Pull completed.\n{self._git('pull', stderr=PIPE)}"

    def reset(self, number='1'):
        """git reset"""
        return self._git('reset', f'HEAD~{int(number)}')


def repos():
    """Show all available repositories, path, and unique ID"""
    print("\nThe following repos are available.\n")
    NAME_SHELF = shelve.open(str(PurePath(SHELF_DIR / "NAME_SHELF")))
    INDEX_SHELF = shelve.open(str(PurePath(SHELF_DIR / "INDEX_SHELF")))

    print("{:<4} {:<20} {:<}".format("Key", "| Name", "| Path"))
    print("******************************************")
    for key in INDEX_SHELF.keys():
        name = INDEX_SHELF[key]
        print(f"{key:<4} {name:<20} {NAME_SHELF[name]!s:<}")
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
            return Commands(name, str(NAME_SHELF[name]))
        except KeyError:
            raise PygitException("That index does not exist.")
    except ValueError:
        try:
            return Commands(input_string, NAME_SHELF[input_string])
        except KeyError:
            raise PygitException("That repository name does not exist or is not indexed")
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


def pull(*args, _all=False):
    for each in load_multiple(*args, _all=_all):
        print(f"*** {each.name} ***\n{each.pull()}")


def push(*args, _all=False):
    for each in load_multiple(*args, _all=_all):
        print(f"*** {each.name} ***\n{each.push()}")


def all_status():
    """Write status of all repositories to file in markdown format"""
    print("Getting repo status.\n\nYou may be prompted for credentials...")

    os.chdir(STATUS_DIR)
    attention = ""
    messages = []
    TIME_STAMP = datetime.now().strftime("%a_%d_%b_%Y_%H_%M_%S_%p")

    fname = f"REPO_STATUS_@_{TIME_STAMP}.md"
    with open(fname, 'w+') as f:
        f.write(f"# Repository status as at {TIME_STAMP}\n\n")
        
        for each in load_multiple(_all=True):
            name = each.name
            status = each.status()

            messages.append(f"## {name}\n\n```cmd\n{status}```\n")

            if need_attention(status):
                attention += f"1. {name}\n"

        f.write("## REPOS NEEDING ATTENTION\n\n")
        f.write(attention)
        f.write("\n-------\n\n")
        f.write("## STATUS MESSAGES\n\n")
        f.write("\n".join(messages))

    print("\n\nDone. Status file saved in ", STATUS_DIR)
    os.chdir(BASE_DIR)

if __name__ == "__main__":
    initialize()
