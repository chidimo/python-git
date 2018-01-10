"""Test API"""

import json
import os
import random
import unittest
from glob import glob
from send2trash import send2trash
from pygit.api import set_all, load
from pygit.paths import BASE_PATH, IDS
from pygit.commands import Commands
# import inspect

class TestApiA(unittest.TestCase):
    """Basic setup to test API"""
    def setUp(self):
        """Setup"""
        print("Start ", os.path.basename(__file__), " tests")
        set_all(git_type="win")

    def test_ids_exist(self): # always regen for this test to work
        """Test id file created and that its content is a dictionary"""
        assert os.path.exists(IDS)
        with open(IDS) as rhand:
            self.assertIsInstance(json.load(rhand), dict)

class TestApiB(unittest.TestCase):
    """main body of tests"""
    def test_loader(self):
        """Test Loader returns an instance of Commands and it has all attributes"""
        with open(IDS, "r") as rhand:
            ids = json.load(rhand)
        random_id = random.choice(list(ids.keys()))
        opobj = load(repo_id=random_id)
        self.assertIsInstance(opobj, Commands)
        # methods = [each[0] for each in inspect.getmembers(opobj, predicate=inspect.ismethod)]

class TestApiZ(unittest.TestCase):
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
