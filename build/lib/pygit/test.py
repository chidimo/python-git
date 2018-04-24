"""Test API"""

import json
import os
import random
import unittest
from glob import glob
from random import choice
from send2trash import send2trash
# import inspect

from .main import (
    USERHOME, DESKTOP, STATUS_DIR, BASE_DIR, SHELF_DIR, TEST_DIR, TIMING,
    cleanup, check_git_support, is_git_repo, need_attention, initialize,
    Commands, show_repos, load, load_multiple, pull, push, all_status
)

class TestAppSetupA(unittest.TestCase):
    """Basic setup to test API"""
    def setUp(self):
        """Setup"""
        print("Start ", os.path.basename(__file__), " tests")
        initialize()

    def test_ids_exist(self): # always regen for this test to work
        """Test id file created and that its content is a dictionary"""
        assert os.path.exists(IDS)
        with open(IDS) as rhand:
            self.assertIsInstance(json.load(rhand), dict)

class TestAppSetupB(unittest.TestCase):
    """main body of tests"""
    def test_loader(self):
        """Test Loader returns an instance of Commands and it has all attributes"""
        with open(IDS, "r") as rhand:
            ids = json.load(rhand)
        random_id = random.choice(list(ids.keys()))
        opobj = load(repo_id=random_id)
        self.assertIsInstance(opobj, Commands)
        # methods = [each[0] for each in inspect.getmembers(opobj, predicate=inspect.ismethod)]

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
        """Check branch is ahead or behind
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
                self.assertTrue(any(
                    ['is ahead' in status], ['is behind' in status],
                    ['not staged' in status], 'changes' in status))

class TestUtilsA(unittest.TestCase):
    """Test that search paths exist"""
    def setUp(self):
        print("Start ", os.path.basename(__file__), " tests")
        set_search_paths()
        set_input_data()

    def test_set_search_paths(self):
        """Test search directory created"""
        assert os.path.exists(SEARCH_PATHS)

class TestUtilsB(unittest.TestCase):
    """Test Utils"""
    def setUp(self):
        self.repos, self.names, self.exec_ = get_repos_and_git()

    def test_repo_path_exists(self):
        """Test repo directory created"""
        assert os.path.exists(REPO_PATH)

    def test_git_present(self):
        """Docstring"""
        self.assertTrue(self.exec_["win"])

    def test_repos_are_directories(self):
        """Test all git repos are directories"""
        for repo, name in zip(self.repos, self.names):
            self.assertTrue(os.path.isdir(repo))
            self.assertIsInstance(name, str)

class TestZ(unittest.TestCase): # remove after adding test data
    """Clean up files"""
    def setUp(self):
        pass

    def tearDown(self):
        self._ = send2trash(each)

    def test_dummy(self):
        """Trigger tearDown"""
        self.assertFalse(os.path.exists(BASE_PATH))

if __name__ == "__main__":
    unittest.main()
