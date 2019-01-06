# Python-Git

Automate the boring git stuff with python

## Motivation

Whenever I wanted to see the status of all my git repos I have to fire up the
`git-cmd.exe` shell on windows, navigate to each folder and then do a `git status`.
I have to do this both at home and at work.

But I got quickly tired of it. So I decided to make this tool to give me a quick
report so I can see what is ahead and what's behind and what's ahead at a glance.
In short, what needs attention so as to avoid those troubling merge conflicts.

## Requirements

Other thing you need is a computer with `git` either accessible from the command line (which means its in your system path) or as a standalone file somewhere in your system.
If you're working without installation rights, you can use a portable `git` and `python-git` will work just fine.

You can get a portable git version from [here](https://git-scm.com/download/win)

Just unzip it and place it somewhere on your disk. Later (during initialization), you'll need to tell `python-git` where this file is located.

## Installation
  
      pip install python-git

## Setup

After installation, an initial setup is required to tell `pygit` the folders it needs to work with. Open a terminal and `python -m pygit` the below line with appropriate command line arguments.

The output of `python -m pygit --help` is shown below.

```cmd
usage: Pygit. Initialize working directories for python-git
       [-h] [-v {0,1}] [-r RULES [RULES ...]] [-g GITPATH]
       [-m MASTERDIRECTORY] [-s SIMPLEDIRECTORY [SIMPLEDIRECTORY ...]]
       [-t STATUSDIRECTORY]

optional arguments:
  -h, --help            show this help message and exit
  -v {0,1}, --verbosity {0,1}
                        turn verbosity ON/OFF
  -r RULES [RULES ...], --rules RULES [RULES ...]
                        Set a list of string patterns for folders to skip
                        during setup
  -g GITPATH, --gitPath GITPATH
                        Full pathname to git executable. cmd or bash.
  -m MASTERDIRECTORY, --masterDirectory MASTERDIRECTORY
                        Full pathname to directory holding any number of git
                        repos.
  -s SIMPLEDIRECTORY [SIMPLEDIRECTORY ...], --simpleDirectory SIMPLEDIRECTORY [SIMPLEDIRECTORY ...]
                        A list of full pathnames to any number of individual
                        git repos.
  -t STATUSDIRECTORY, --statusDirectory STATUSDIRECTORY
                        Full pathname to directory for writing out status
                        message.
```

As an example you I have a folder in my `D:` drive that holds all my git repos, so I will setup `pygit` with the following command

      python -m pygit --m D:\git -v 1 -t D:\

## Usage

Activate python environment on command line.

      import pygit

In case things change (perhaps you moved folders around or you add a new git repo) and you want to reset your folders just redo the initialization step

      pygit.show_repos()

show all git repos in the format shown immediately below

      repository_id: repository_name: repository_full_path

      pygit.load(repo_id_or_name) # load a repo

where `repo_id` is a string-valued id assigned to that particular repo. The first value in the `show_repos` command's output.

The `load(input_string)` command returns a `Commands` object for that repo, which provides a gateway for issuing git commands on the repository

Operations that can be performed on `Commands` object are shown below.

```python
   r = pygit.load_repo(repo_id_or_name)
   r.fetch() # perform fetch
   r.status() # see status
   r.add_all() # stage all changes for commit
   r.commit(message='chore: minor changes') # commit changes. Press enter to accept default message
   r.push() # perform push action
   r.pull() # perform pull request
   r.add_commit() # add and commit at once
```

### Batch Operations

The following batch operations on indexed repos are available.

      pygit.load_multiple(*args) # load a set of repos
      pygit.load_multiple("2", "5") # load only repo 2 and 5

returns a  `generator`  of  `Commands`  objects for repositories 2 and 5. Afterwards you can iterate over the repos like below

```python
   for each in pygit.load_multiple("2", "5"):
      each.add_commit()
```

      pygit.all_status()

performs a `status` command on all indexed repos. The result is written to a markdown file.
Carries a timestamp of the time the command was issued. Call it a snapshot of your repo status if you will. Items which are out of sync with their remote counterpart are also highlighted as needing attention.

      pygit.pull_all()

perform a `pull` request on all indexed repos at once. It returns `None`.

      pygit.push_all()

performs a `push` action on all indexed repos at once. It returns `None`.

      pygit.load_all()

returns a  `generator`  of  `Commands`  object for each indexed repo.

## To do

1. Refactor `initialize()` function
1. Add `git-bash.exe`
1. Implement `Commands.branch()`
1. Refactor tests
1. Auto-run test after importation to make sure every other thing works fine.
1. Define an update function that updates the repo dictionaries for the case when a new repo is added but the overall directory structure remains unchanged.
