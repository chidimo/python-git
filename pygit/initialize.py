#! /usr/bin/python3.6

import os
import sys
import shutil
import shelve
import argparse
from subprocess import Popen, PIPE

from send2trash import send2trash

USERHOME = os.path.abspath(os.path.expanduser('~'))
DESKTOP = os.path.abspath(USERHOME + '/Desktop/')

STATUS_DIR = os.path.join(DESKTOP ,"status")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELF_DIR = os.path.join(BASE_DIR, "shelves")
TEST_DIR = os.path.join(BASE_DIR, "test_git/")

def get_site_packages_directory():
    """Returns site packages directory"""
    # try iterating over sys.path
    try:
        return next(p for p in sys.path if 'site-packages' in p)
    except StopIteration:
        pass

    # try manually constructing the path and check if it exists
    py_version = '{}.{}'.format(sys.version_info[0], sys.version_info[1])

    prefix_paths = [
        sys.prefix + '/lib/python{}/dist-packages/',
        sys.prefix + '/lib/python{}/site-packages/',
        sys.prefix + '/local/lib/python{}/dist-packages/',
        sys.prefix + '/local/lib/python{}/site-packages/',
        '/Library/Python/{}/site-packages/',
    ]

    py_installation_paths = [each.format(py_version) for each in prefix_paths]
    paths = py_installation_paths + [
        # these paths for versionless installs like jupyter
        sys.prefix + '/lib/dist-packages/',
        sys.prefix + '/lib/site-packages/',
        sys.prefix + '/local/lib/dist-packages/',
        sys.prefix + '/local/lib/site-packages/',
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def help():
    """How to call the initialization program"""
    site_package_directory = get_site_packages_directory()
    source_directory = '{}/pygit/initialize.py'.format(site_package_directory)
    # source_directory = '{}/python-git-3.2-py3.6.egg/pygit/initialize.py'.format(site_package_directory)
    print('\n\nTo initialize pygit, run')
    print('python', source_directory)
    print('with the relevant command line arguments\n\n')
    help = source_directory + ' -h'
    print('run \n', help, '\nfor help')
    return

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
    """
    Check if git is available via command line.
    If not, check if its available as an executable in installation folder.
    """
    proc = Popen(['git --version'], shell=True, stdout=PIPE,)
    msg, ab = proc.communicate()
    msg = msg.decode('utf-8')

    if "git version" in msg:
        return True
    return False

def is_git_repo(directory):
    """
    Determine if a folder is a git repo
    Checks the 'git status' message for error
    """
    files = os.listdir(directory)
    if '.git' in files:
        return True
    return False

def need_attention(status_msg):
    """Return True if a repo status is not same as that of remote"""
    msg = ["not staged", "behind", "ahead", "Untracked"]
    if any([each in status_msg for each in msg]):
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
            print("Your system supports git.\n")
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
            print("Now looking inside folders ... Please wait a few minutes.\n")

        i = len(list(index_shelf.keys())) + 1

        folder_paths = [
            name for name in os.listdir(args.masterDirectory) \
            if os.path.isdir(os.path.join(args.masterDirectory, name))
        ]

        for name in folder_paths:
            bad_folder_starts = [".", "_"] # skip folders that start with any of these characters
            if any([name.startswith(each) for each in bad_folder_starts]) :
                if args.verbosity:
                    print(name, " starts with one of ", bad_folder_starts, " skipping\n")
                continue
            path = os.path.join(args.masterDirectory, name)
            if args.rules:
                # if any of the string patterns is found in path name, that folder will be skipped.
                if any([rule in path for rule in args.rules]):
                    if args.verbosity:
                        print(path, " matches a rule. Skipping\n")
                    continue

            directory_absolute_path = os.path.abspath(path)

            if is_git_repo(directory_absolute_path):
                if args.verbosity:
                    print(directory_absolute_path, " is a git repository")
                if sys.platform == 'win32':
                    name = directory_absolute_path.split("\\")[-1]
                if sys.platform == 'linux':
                    name = directory_absolute_path.split("/")[-1]

                if args.verbosity:
                    print("Now shelving ", name, "\n")
                name_shelf[name] = directory_absolute_path
                index_shelf[str(i)] = name
                i += 1
        name_shelf.close()
        index_shelf.close()

    if args.simpleDirectory:

        i = len(list(index_shelf.keys())) + 1
        for directory in args.simpleDirectory:

            if is_git_repo(directory):
                if args.verbosity:
                    print("Now shelving ", args.simpleDirectory, "\n")
                if sys.platform == 'win32':
                    name = directory.split("\\")[-1]
                if sys.platform == 'linux':
                    name = directory.split("/")[-1]
                name_shelf[name] = directory
                index_shelf[str(i)] = name
            else:
                print(directory, " is not a valid git repo.\nContinuing...\n")
                continue
            i += 1

        name_shelf.close()
        index_shelf.close()

    global STATUS_DIR
    if args.statusDirectory:
        STATUS_DIR = args.statusDirectory
        if args.verbosity:
            print("\nStatus will be saved in {}\n".format(STATUS_DIR))
    else:
        if args.verbosity:
            print("\nStatus will be saved in {}\n".format(STATUS_DIR))

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

if __name__ == "__main__":
    initialize()
