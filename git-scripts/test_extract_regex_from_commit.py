import io
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import git

from extract_regex_from_commit import extract_matches, get_git_commits, main


class TestExtractJiraIds(unittest.TestCase):

    def test_01_extract_single_match(self):
        commit_messages = ["[TPR-123] Fix typo"]
        matches = extract_matches(commit_messages, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-123]"])

    def test_02_extract_multiple_matches_single_commit(self):
        commit_messages = ["[TPR-123] [TPR-124] Fix login"]
        matches = extract_matches(commit_messages, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-123][TPR-124]"])

    def test_03_extract_no_matches(self):
        commit_messages = ["Refactor code without Jira ID"]
        matches = extract_matches(commit_messages, r"\[TPR-\d+\]")
        self.assertEqual(matches, [])

    def test_04_extract_multiple_commits(self):
        commit_messages = ["[TPR-1] First", "[TPR-2] Second"]
        matches = extract_matches(commit_messages, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-1]", "[TPR-2]"])

    def test_05_extract_mixed_commits(self):
        commit_messages = ["[TPR-1] First", "No match here", "[TPR-2] [TPR-3] Second"]
        matches = extract_matches(commit_messages, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-1]", "[TPR-2][TPR-3]"])

    def test_06_multiline_commit_message(self):
        commit_messages = [
            "[TPR-99] Initial line\nMore details here.\nAlso fixes [TPR-100]"
        ]
        matches = extract_matches(commit_messages, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-99][TPR-100]"])

    def test_07_different_regex_pattern(self):
        commit_messages = ["FOO-123 BAR-456"]
        matches = extract_matches(commit_messages, r"[A-Z]+-\d+")
        self.assertEqual(matches, ["FOO-123BAR-456"])

    def test_08_empty_git_output(self):
        matches = extract_matches([], r"\[TPR-\d+\]")
        self.assertEqual(matches, [])

    def test_09_empty_commit_message_body(self):
        commit_messages = [""]
        matches = extract_matches(commit_messages, r"\[TPR-\d+\]")
        self.assertEqual(matches, [])

    def test_10_missing_end_marker(self):
        commit_messages = ["[TPR-123] Unfinished"]
        matches = extract_matches(commit_messages, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-123]"])

    def test_11_multiple_commits_no_matches(self):
        commit_messages = ["No match", "Still no match"]
        matches = extract_matches(commit_messages, r"\[TPR-\d+\]")
        self.assertEqual(matches, [])

    def test_12_regex_matching_full_string(self):
        commit_messages = ["MATCHME"]
        matches = extract_matches(commit_messages, r"MATCHME")
        self.assertEqual(matches, ["MATCHME"])

    @patch("extract_regex_from_commit.git.Repo")
    def test_13_get_git_commits_depth_1(self, mock_repo_cls):
        repo_root = Path("/repo")
        file_path = str(repo_root / "test.txt")

        mock_repo = MagicMock()
        mock_repo.working_dir = str(repo_root)
        mock_repo_cls.return_value = mock_repo

        commit = MagicMock()
        commit.hexsha = "abcdef1234567890abcdef1234567890abcdef12"
        commit.message = "[TPR-1] msg"
        mock_repo.blame.return_value = [(commit, ["line"])]

        res = get_git_commits(file_path, 10, 15, 1)

        mock_repo.blame.assert_called_once()
        blame_args, blame_kwargs = mock_repo.blame.call_args
        self.assertEqual(blame_args[0], "HEAD")
        self.assertTrue(str(blame_args[1]).endswith("test.txt"))
        self.assertEqual(blame_kwargs, {"L": "10,15"})
        self.assertEqual(res, ["[TPR-1] msg"])

    @patch("extract_regex_from_commit.git.Repo")
    def test_14_get_git_commits_depth_greater_than_1(self, mock_repo_cls):
        repo_root = Path("/repo")
        file_path = str(repo_root / "test.txt")

        mock_repo = MagicMock()
        mock_repo.working_dir = str(repo_root)
        mock_repo_cls.return_value = mock_repo

        mock_repo.git.log.side_effect = [
            "COMMIT_HASH:1111111111111111111111111111111111111111\nCOMMIT_HASH:2222222222222222222222222222222222222222\n",
            "COMMIT_HASH:2222222222222222222222222222222222222222\nCOMMIT_HASH:3333333333333333333333333333333333333333\n",
        ]

        def _commit_lookup(hexsha):
            commit = MagicMock()
            commit.message = f"msg-{hexsha[-4:]}"
            return commit

        mock_repo.commit.side_effect = _commit_lookup

        res = get_git_commits(file_path, 5, 6, 2)

        self.assertEqual(mock_repo.git.log.call_count, 2)
        log_calls = mock_repo.git.log.call_args_list
        self.assertEqual(log_calls[0].args[1], "-n2")
        self.assertEqual(log_calls[1].args[1], "-n2")
        self.assertEqual(log_calls[0].kwargs, {"format": "COMMIT_HASH:%H"})
        self.assertEqual(log_calls[1].kwargs, {"format": "COMMIT_HASH:%H"})
        self.assertTrue(str(log_calls[0].args[0]).startswith("-L5,5:"))
        self.assertTrue(str(log_calls[1].args[0]).startswith("-L6,6:"))
        self.assertTrue(str(log_calls[0].args[0]).endswith("test.txt"))
        self.assertTrue(str(log_calls[1].args[0]).endswith("test.txt"))
        self.assertEqual(res, ["msg-1111", "msg-2222", "msg-3333"])

    @patch("extract_regex_from_commit.git.Repo")
    def test_15_get_git_commits_error_handling(self, mock_repo_cls):
        repo_root = Path("/repo")
        file_path = str(repo_root / "missing.txt")

        mock_repo = MagicMock()
        mock_repo.working_dir = str(repo_root)
        mock_repo_cls.return_value = mock_repo
        mock_repo.blame.side_effect = git.GitCommandError("git blame", 128, stderr="fatal: no such path")

        with self.assertRaises(git.GitCommandError):
            get_git_commits(file_path, 1, 1, 1)

    @patch("extract_regex_from_commit.extract_matches")
    @patch("extract_regex_from_commit.get_git_commits")
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.argv", ["extract_jira_ids.py", "file.txt", r"\[TPR-\d+\]", "10"])
    def test_16_main_single_line_default_depth(self, _stdout, mock_get_git_commits, mock_extract_matches):
        mock_get_git_commits.return_value = ["[TPR-1] msg"]
        mock_extract_matches.return_value = ["[TPR-1]"]

        main()

        mock_get_git_commits.assert_called_once_with("file.txt", 10, 10, 1)
        mock_extract_matches.assert_called_once_with(["[TPR-1] msg"], r"\[TPR-\d+\]")
        self.assertEqual(_stdout.getvalue().strip(), '["[TPR-1]"]')

    @patch("extract_regex_from_commit.extract_matches")
    @patch("extract_regex_from_commit.get_git_commits")
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.argv", ["extract_jira_ids.py", "file.txt", r"\[TPR-\d+\]", "5", "--end-line", "6", "--depth", "5"])
    def test_17_main_line_range_with_depth(self, _stdout, mock_get_git_commits, mock_extract_matches):
        mock_get_git_commits.return_value = ["[TPR-2] msg"]
        mock_extract_matches.return_value = ["[TPR-2]"]

        main()

        mock_get_git_commits.assert_called_once_with("file.txt", 5, 6, 5)
        mock_extract_matches.assert_called_once_with(["[TPR-2] msg"], r"\[TPR-\d+\]")
        self.assertEqual(_stdout.getvalue().strip(), '["[TPR-2]"]')

    def test_18_regex_with_capture_groups(self):
        commit_messages = ["[TPR-1] msg"]
        matches = extract_matches(commit_messages, r"(?:\[TPR-\d+\])")
        self.assertEqual(matches, ["[TPR-1]"])

    def test_19_special_characters_in_commit_message(self):
        commit_messages = ["Fix! @#$ %^&*()_+ [TPR-42] {}|"]
        matches = extract_matches(commit_messages, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-42]"])

    def test_20_unicode_in_commit_message(self):
        commit_messages = ["[TPR-123] \U0001f527 Fix bug \u2728"]
        matches = extract_matches(commit_messages, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-123]"])

    @patch("sys.stderr", new_callable=io.StringIO)
    @patch("sys.argv", ["extract_jira_ids.py", "file.txt", "*", "10"])
    def test_21_invalid_regex_pattern(self, mock_stderr):
        with self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 1)
        self.assertIn('"error": "Invalid regex pattern"', mock_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
