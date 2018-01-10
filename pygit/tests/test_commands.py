"""Test Commands"""

import os
import json
import unittest
from glob import glob
from random import choice
from send2trash import send2trash
from pygit.paths import BASE_PATH, REPO_PATH, EXEC_PATH, IDS
from pygit.api import set_all, load

# nose2 pygit.tests.test_command

class TestCommandsA(unittest.TestCase): # set up
    """Test git commands"""
    def setUp(self):
        """Pick a repo"""
        print("Start ", os.path.basename(__file__), " tests")
        set_all(git_type="win")

    def test_dummy_setup(self):
        """Dummy to setup our files"""
        assert os.path.exists(REPO_PATH)

class TestCommandsB(unittest.TestCase):
    def setUp(self):
        """Set up path"""
        with open(EXEC_PATH, "r") as rhand:
            self.exec_ = json.load(rhand)
        self.git = self.exec_["git"]

        with open(IDS, "r") as rhand:
            self.reps = json.load(rhand)

        self.ids = list(self.reps.keys())
        self.pick = choice(self.ids)

    def test_git_status(self):
        """Check for the text 'On branch master'"""
        name_obj = load(repo_id=self.pick)
        name_obj.fetch()
        self.assertIn("On branch master", name_obj.status())

    def test_git_add(self):
        """Check for 'Changes not staged for commit:'
        """
        for each in self.ids:
            git_obj = load(repo_id=each)
            status = git_obj.status()

            if "nothing to commit" in status:
                continue
            elif "Changes not staged for commit:" in status:
                git_obj.add_all()
                status = git_obj.status()
                checks = [each in status for each in ["modified", "new file", "deleted"]]
                self.assertTrue(any(checks))
            else:
                return "No changes to commit"

    def test_git_commit(self):
        """Check for 'Your branch is ahead of 'origin/master''
        """
        for each in self.ids:
            git_obj = load(repo_id=each)
            status = git_obj.status()

            if "nothing to commit" in status:
                continue
            else:
                git_obj.add_all()
                git_obj.commit()
                status = git_obj.status()
                self.assertIn("Your branch is ahead of 'origin/master'", status)

class TestCommandsZ(unittest.TestCase):
    """Clean up files"""
    def setUp(self):
        self.jsons = glob(os.path.join(BASE_PATH, "*_path.json"))

    def tearDown(self):
        self.jsons = [send2trash(each) for each in self.jsons]

    def test_dummy(self):
        """Trigger tearDown"""
        print("\nFinish ", os.path.basename(__file__), " tests")
        self.assertTrue(self.jsons)

if __name__ == "__main__":
    unittest.main()
