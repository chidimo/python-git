"""Test Utils"""

import os
import unittest
from glob import glob
from send2trash import send2trash
from pygit.paths import BASE_PATH, SEARCH_PATHS, REPO_PATH
from pygit.utils import set_search_paths, get_repos_and_git, set_input_data

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

class TestUtilsZ(unittest.TestCase):
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
