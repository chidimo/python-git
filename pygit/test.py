"""Tests for pygit.

Every test runs against a temporary directory. SHELF_DIR, STATUS_DIR and
BASE_DIR are patched so nothing is written to the user's home directory.
"""

import os
import shelve
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePath
from unittest import mock

from . import pygit


def git_available():
    return shutil.which("git") is not None


def make_git_repo(path):
    """Create an empty git repo at path."""
    Path(path).mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)


class TempDirTestCase(unittest.TestCase):
    """Base class: temp dir, patched module paths, cwd restored afterwards."""

    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.shelf_dir = self.tmp / "shelf"
        self.status_dir = self.tmp / "status"
        self.shelf_dir.mkdir()
        self.status_dir.mkdir()

        for name, value in (
            ("SHELF_DIR", self.shelf_dir),
            ("STATUS_DIR", self.status_dir),
            ("BASE_DIR", self.tmp),
        ):
            patcher = mock.patch.object(pygit, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def populate_shelves(self, repos):
        """repos: dict of name -> path. Index keys are assigned from '1'."""
        with shelve.open(str(PurePath(self.shelf_dir / "NAME_SHELF"))) as names, \
                shelve.open(str(PurePath(self.shelf_dir / "INDEX_SHELF"))) as index:
            for i, (name, path) in enumerate(repos.items(), start=1):
                names[name] = path
                index[str(i)] = name


class NeedAttentionTests(unittest.TestCase):
    def test_clean_status_needs_no_attention(self):
        msg = "On branch main\nYour branch is up to date.\nnothing to commit"
        self.assertFalse(pygit.need_attention(msg))

    def test_each_trigger_phrase_is_detected(self):
        for phrase in ("not staged", "behind", "ahead", "Untracked"):
            with self.subTest(phrase=phrase):
                self.assertTrue(pygit.need_attention(f"status: {phrase} here"))


class IsGitRepoTests(TempDirTestCase):
    def test_directory_with_dot_git_is_a_repo(self):
        (self.tmp / "repo" / ".git").mkdir(parents=True)
        self.assertTrue(pygit.is_git_repo(self.tmp / "repo"))

    def test_plain_directory_is_not_a_repo(self):
        (self.tmp / "plain").mkdir()
        self.assertFalse(pygit.is_git_repo(self.tmp / "plain"))


class ExclusionTests(unittest.TestCase):
    def test_hidden_and_underscore_folders_are_excluded(self):
        for name in (".hidden", "_private"):
            with self.subTest(name=name):
                self.assertTrue(pygit.enforce_exclusion(name, 0))

    def test_exclusion_checks_the_folder_name_not_the_whole_path(self):
        self.assertTrue(pygit.enforce_exclusion(Path("/a/b/.hidden"), 0))
        self.assertTrue(pygit.enforce_exclusion(Path("/a/b/_private"), 0))
        self.assertFalse(pygit.enforce_exclusion(Path("/a/.config/project"), 0))

    def test_normal_folder_is_not_excluded(self):
        self.assertFalse(pygit.enforce_exclusion("project", 0))

    def test_match_rule_matches_substring(self):
        self.assertTrue(pygit.match_rule(["node_modules"], "/a/node_modules/b", 0))

    def test_match_rule_accepts_path_objects(self):
        self.assertTrue(pygit.match_rule(["skipme"], Path("/a/skipme/b"), 0))
        self.assertFalse(pygit.match_rule(["skipme"], Path("/a/b"), 0))

    def test_match_rule_without_match_or_rules(self):
        self.assertFalse(pygit.match_rule(["node_modules"], "/a/b", 0))
        self.assertFalse(pygit.match_rule(None, "/a/b", 0))
        self.assertFalse(pygit.match_rule([], "/a/b", 0))


class CheckGitSupportTests(unittest.TestCase):
    def _run_with_output(self, output):
        proc = mock.Mock()
        proc.communicate.return_value = (output, b"")
        with mock.patch.object(pygit, "Popen", return_value=proc):
            return pygit.check_git_support()

    def test_true_when_git_reports_version(self):
        self.assertTrue(self._run_with_output(b"git version 2.45.0\n"))

    def test_false_when_output_has_no_version(self):
        self.assertFalse(self._run_with_output(b"command not found\n"))

    def test_false_when_git_is_not_installed(self):
        with mock.patch.object(pygit, "Popen", side_effect=FileNotFoundError):
            self.assertFalse(pygit.check_git_support())

    @unittest.skipUnless(git_available(), "git is not installed")
    def test_true_with_real_git(self):
        self.assertTrue(pygit.check_git_support())


class RunGitTests(unittest.TestCase):
    def _popen(self, output=b"out"):
        proc = mock.Mock()
        proc.communicate.return_value = (output, None)
        return mock.patch.object(pygit, "Popen", return_value=proc)

    def test_builds_argument_list_without_a_shell(self):
        with self._popen() as popen:
            result = pygit.run_git("add", "--", "a b.txt")
        self.assertEqual(result, "out")
        self.assertEqual(popen.call_args.args[0], ["git", "add", "--", "a b.txt"])
        self.assertFalse(popen.call_args.kwargs.get("shell", False))

    def test_git_exec_wraps_the_command(self):
        with self._popen() as popen:
            pygit.run_git("status", git_exec="/opt/git-cmd")
        self.assertEqual(popen.call_args.args[0], ["/opt/git-cmd", "git", "status"])

    def test_stderr_defaults_to_stdout_and_is_configurable(self):
        with self._popen() as popen:
            pygit.run_git("status")
            self.assertEqual(popen.call_args.kwargs["stderr"], pygit.STDOUT)
            pygit.run_git("push", stderr=pygit.PIPE)
            self.assertEqual(popen.call_args.kwargs["stderr"], pygit.PIPE)

    def test_no_shell_true_anywhere_in_the_module(self):
        source = Path(pygit.__file__).read_text()
        code_lines = [l for l in source.splitlines() if not l.lstrip().startswith("#")]
        self.assertFalse([l for l in code_lines if "shell=True" in l])


class CleanupTests(TempDirTestCase):
    def test_cleanup_sends_shelf_dir_to_trash(self):
        with mock.patch.object(pygit, "send2trash") as trash:
            pygit.cleanup()
        trash.assert_called_once_with(self.shelf_dir)


class ShowVerboseOutputTests(unittest.TestCase):
    def test_logs_only_when_verbose(self):
        with mock.patch.object(pygit, "pygit_logger") as logger:
            pygit.show_verbose_output(0, "quiet")
            logger.debug.assert_not_called()
            pygit.show_verbose_output(1, "a", "b")
            self.assertEqual(logger.debug.call_count, 2)


@unittest.skipUnless(git_available(), "git is not installed")
class CommandsTests(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.repo = self.tmp / "myrepo"
        make_git_repo(self.repo)

    def test_init_changes_into_repo_directory(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        self.assertEqual(Path(cmd.dir).resolve(), self.repo)
        self.assertEqual(Path(os.getcwd()).resolve(), self.repo)

    def test_init_with_missing_directory_does_not_raise(self):
        pygit.Commands("gone", str(self.tmp / "does-not-exist"))

    def test_str(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        self.assertEqual(str(cmd), f"Commands: myrepo: {cmd.dir}")

    def test_equality(self):
        a = pygit.Commands("myrepo", str(self.repo))
        b = pygit.Commands("myrepo", str(self.repo))
        c = pygit.Commands("other", str(self.repo))
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertNotEqual(a, "not a Commands object")

    def test_status_reports_branch_info(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        self.assertIn("On branch", cmd.status())

    def test_untracked_file_needs_attention(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        self.assertFalse(cmd.need_attention())
        (self.repo / "new.txt").write_text("hello")
        self.assertTrue(cmd.need_attention())

    def test_stage_all_stages_new_file(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        (self.repo / "new.txt").write_text("hello")
        cmd.stage_all()
        self.assertIn("new.txt", cmd.status())
        self.assertIn("Changes to be committed", cmd.status())

    def _staged_files(self):
        return subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=self.repo, capture_output=True, text=True, check=True,
        ).stdout.splitlines()

    def test_injection_payloads_are_not_executed(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        marker = self.repo / "pwned.txt"
        payloads = (
            "; touch pwned.txt",
            "x && touch pwned.txt",
            "$(touch pwned.txt)",
            "`touch pwned.txt`",
            "x | touch pwned.txt",
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                cmd.stage_file(payload)
                cmd.stage_all(payload)
                self.assertFalse(marker.exists())

    def test_stage_file_handles_names_with_spaces(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        (self.repo / "my file.txt").write_text("hello")
        cmd.stage_file("my file.txt")
        self.assertEqual(self._staged_files(), ["my file.txt"])

    def test_stage_file_treats_leading_dash_as_a_path(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        (self.repo / "-A").write_text("hello")
        (self.repo / "other.txt").write_text("hello")
        cmd.stage_file("-A")
        self.assertEqual(self._staged_files(), ["-A"])

    def test_stage_all_stages_each_listed_file(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        for name in ("a.txt", "b.txt", "c.txt"):
            (self.repo / name).write_text(name)
        cmd.stage_all("a.txt b.txt")
        self.assertEqual(self._staged_files(), ["a.txt", "b.txt"])

    def _commit_with_message(self, cmd, message):
        git_env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                   "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        with mock.patch.dict(os.environ, git_env), \
                mock.patch("builtins.input", return_value=message):
            cmd.commit()

    def _log(self):
        return subprocess.run(
            ["git", "log", "--format=%s"], cwd=self.repo,
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()

    def test_commit_message_is_taken_literally(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        (self.repo / "a.txt").write_text("a")
        cmd.stage_all()
        message = 'msg"; touch pwned.txt; echo "$(whoami)'
        self._commit_with_message(cmd, message)
        self.assertEqual(self._log(), [message])
        self.assertFalse((self.repo / "pwned.txt").exists())

    def test_commit_uses_default_message_on_empty_input(self):
        cmd = pygit.Commands("myrepo", str(self.repo), message="default msg")
        (self.repo / "a.txt").write_text("a")
        cmd.stage_all()
        self._commit_with_message(cmd, "")
        self.assertEqual(self._log(), ["default msg"])

    def test_reset_undoes_the_last_commit(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        for name in ("a.txt", "b.txt"):
            (self.repo / name).write_text(name)
            cmd.stage_all()
            self._commit_with_message(cmd, f"add {name}")
        cmd.reset()
        self.assertEqual(self._log(), ["add a.txt"])

    def test_reset_rejects_non_integer_count(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        with self.assertRaises(ValueError):
            cmd.reset("1; touch pwned.txt")
        self.assertFalse((self.repo / "pwned.txt").exists())

    def test_git_exec_is_used_as_wrapper(self):
        cmd = pygit.Commands("myrepo", str(self.repo), git_exec="/opt/git-cmd")
        with mock.patch.object(pygit, "Popen") as popen:
            popen.return_value.communicate.return_value = (b"", None)
            cmd.stage_file("a.txt")
        self.assertEqual(popen.call_args.args[0], ["/opt/git-cmd", "git", "add", "--", "a.txt"])

    def test_stage_file_stages_only_that_file(self):
        cmd = pygit.Commands("myrepo", str(self.repo))
        (self.repo / "a.txt").write_text("a")
        (self.repo / "b.txt").write_text("b")
        cmd.stage_file("a.txt")
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=self.repo, capture_output=True, text=True, check=True,
        ).stdout.split()
        self.assertEqual(staged, ["a.txt"])


class LoadTests(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.repo_a = self.tmp / "alpha"
        self.repo_b = self.tmp / "beta"
        self.repo_a.mkdir()
        self.repo_b.mkdir()
        self.populate_shelves({"alpha": self.repo_a, "beta": self.repo_b})

    def test_load_by_index(self):
        cmd = pygit.load("1")
        self.assertEqual(cmd.name, "alpha")
        self.assertEqual(Path(cmd.dir).resolve(), self.repo_a)

    def test_load_accepts_integer_index(self):
        self.assertEqual(pygit.load(2).name, "beta")

    def test_load_by_name(self):
        self.assertEqual(pygit.load("beta").name, "beta")

    def test_load_unknown_index_raises(self):
        with self.assertRaises(pygit.PygitException):
            pygit.load("99")

    def test_load_unknown_name_raises(self):
        with self.assertRaises(pygit.PygitException):
            pygit.load("nope")

    def test_load_multiple_yields_requested_repos(self):
        names = [c.name for c in pygit.load_multiple("1", "2")]
        self.assertEqual(names, ["alpha", "beta"])

    def test_load_multiple_all(self):
        names = sorted(c.name for c in pygit.load_multiple(_all=True))
        self.assertEqual(names, ["alpha", "beta"])

    def test_repos_prints_every_indexed_repo(self):
        with mock.patch("builtins.print") as fake_print:
            pygit.repos()
        output = "\n".join(str(c.args[0]) for c in fake_print.call_args_list if c.args)
        self.assertIn("alpha", output)
        self.assertIn("beta", output)

    def test_pull_and_push_run_on_each_repo(self):
        with mock.patch.object(pygit.Commands, "pull", return_value="pulled") as pull, \
                mock.patch.object(pygit.Commands, "push", return_value="pushed") as push, \
                mock.patch("builtins.print"):
            pygit.pull("1", "2")
            pygit.push(_all=True)
        self.assertEqual(pull.call_count, 2)
        self.assertEqual(push.call_count, 2)


@unittest.skipUnless(git_available(), "git is not installed")
class AllStatusTests(TempDirTestCase):
    def test_writes_markdown_report(self):
        clean = self.tmp / "clean"
        dirty = self.tmp / "dirty"
        make_git_repo(clean)
        make_git_repo(dirty)
        (dirty / "new.txt").write_text("hello")
        self.populate_shelves({"clean": clean, "dirty": dirty})

        with mock.patch("builtins.print"):
            pygit.all_status()

        reports = list(self.status_dir.glob("REPO_STATUS_@_*.md"))
        self.assertEqual(len(reports), 1)
        text = reports[0].read_text()
        self.assertIn("## REPOS NEEDING ATTENTION", text)
        self.assertIn("1. dirty", text)
        self.assertNotIn("1. clean", text)
        self.assertIn("## clean", text)
        self.assertIn("## dirty", text)


@unittest.skipUnless(sys.platform in ("linux", "win32"), "shelving repo names is only implemented for linux and windows")
class ShelveMainDirectoryTests(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.main = self.tmp / "main"
        make_repo_dirs = {
            "repo1": True, "repo2": True, "plain": False,
            ".hidden": True, "_private": True, "skipme": True,
        }
        for name, is_repo in make_repo_dirs.items():
            (self.main / name).mkdir(parents=True)
            if is_repo:
                (self.main / name / ".git").mkdir()

        self.name_shelf = shelve.open(str(PurePath(self.shelf_dir / "NAME_SHELF")))
        self.index_shelf = shelve.open(str(PurePath(self.shelf_dir / "INDEX_SHELF")))
        for name, shelf in (("NAME_SHELF", self.name_shelf), ("INDEX_SHELF", self.index_shelf)):
            patcher = mock.patch.object(pygit, name, shelf, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(self.name_shelf.close)
        self.addCleanup(self.index_shelf.close)

    def test_only_git_repos_are_indexed_and_exclusions_apply(self):
        pygit.shelve_main_directory(str(self.main), 0, ["skipme"])
        self.assertEqual(sorted(self.name_shelf.keys()), ["repo1", "repo2"])
        self.assertEqual(sorted(self.index_shelf.keys()), ["1", "2"])

    def test_no_main_directory_is_a_noop(self):
        pygit.shelve_main_directory(None, 0, None)
        self.assertEqual(list(self.name_shelf.keys()), [])


if __name__ == "__main__":
    unittest.main()
