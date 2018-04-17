"""main"""

import os
import shelve
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT

from .initialize import clear_screen, need_attention, DESKTOP, STATUS_DIR, BASE_DIR, SHELF_DIR

TIMING = datetime.now().strftime("%a_%d_%b_%Y_%H_%M_%S_%p")

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
                print(name, " needs attention")
                attention.append(name)

        fhand.write("-------")
        fhand.write("\n## ATTENTION\n")

        attentions = ["{}. {}".format(index+1, name) for index, name in enumerate(attention)]

        fhand.write("\n".join(attentions))
    print("\n\nDone writing. Please check the status folder")
    os.chdir(BASE_DIR)

if __name__ == "__main__":
    pass
