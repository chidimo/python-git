"""Commands"""

import os
import re
from subprocess import Popen, PIPE, STDOUT

class Commands:
    """Commands class

    Parameters
    -----------
    repo_name : str
        The repository name. See list of repositories by running
    repo_dir : str
        The absolute path to the directory
    git_exec : str
        The path to the git executable on the system
    message : str
        Commit message

    Returns
    --------
    : Commands object
	"""
    def __init__(self, repo_name, repo_dir, git_exec, message="minor changes"):
        self.name = repo_name
        self.dir = repo_dir
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

    def __str__(self):
        return "{}: {}".format(self.name, self.dir)

def main():
    """main"""
    print("See API for module usage")
    return

if __name__ == "__main__":
    main()
