import os
import sys
import shutil
import shelve
import argparse
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT, call, check_call, run

USERHOME = os.path.abspath(os.path.expanduser('~'))

run(['echo', '$HOME', '>', 'find_home.txt'], shell=True)