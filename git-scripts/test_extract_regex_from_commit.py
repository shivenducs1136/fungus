import unittest
from unittest.mock import patch, MagicMock, call
import subprocess
import sys

from extract_regex_from_commit import get_git_commits, extract_matches, main

class TestExtractJiraIds(unittest.TestCase):
    
    def test_01_extract_single_match(self):
        git_output = "COMMIT_MSG_START\n[TPR-123] Fix typo\nCOMMIT_MSG_END\n"
        matches = extract_matches(git_output, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-123]"])
        
    def test_02_extract_multiple_matches_single_commit(self):
        git_output = "COMMIT_MSG_START\n[TPR-123] [TPR-124] Fix login\nCOMMIT_MSG_END\n"
        matches = extract_matches(git_output, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-123] [TPR-124]"])
        
    def test_03_extract_no_matches(self):
        git_output = "COMMIT_MSG_START\nRefactor code without Jira ID\nCOMMIT_MSG_END\n"
        matches = extract_matches(git_output, r"\[TPR-\d+\]")
        self.assertEqual(matches, [])
        
    def test_04_extract_multiple_commits(self):
        git_output = (
            "COMMIT_MSG_START\n[TPR-1] First\nCOMMIT_MSG_END\n"
            "diff content here\n"
            "COMMIT_MSG_START\n[TPR-2] Second\nCOMMIT_MSG_END\n"
        )
        matches = extract_matches(git_output, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-1]", "[TPR-2]"])
        
    def test_05_extract_mixed_commits(self):
        git_output = (
            "COMMIT_MSG_START\n[TPR-1] First\nCOMMIT_MSG_END\n"
            "COMMIT_MSG_START\nNo match here\nCOMMIT_MSG_END\n"
            "COMMIT_MSG_START\n[TPR-2] [TPR-3] Second\nCOMMIT_MSG_END\n"
        )
        matches = extract_matches(git_output, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-1]", "[TPR-2] [TPR-3]"])

    def test_06_multiline_commit_message(self):
        git_output = (
            "COMMIT_MSG_START\n"
            "[TPR-99] Initial line\n"
            "More details here.\n"
            "Also fixes [TPR-100]\n"
            "COMMIT_MSG_END\n"
        )
        matches = extract_matches(git_output, r"3\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-99] [TPR-100]"])
        
    def test_07_different_regex_pattern(self):
        git_output = "COMMIT_MSG_START\nFOO-123 BAR-456\nCOMMIT_MSG_END\n"
        matches = extract_matches(git_output, r"[A-Z]+-\d+")
        self.assertEqual(matches, ["FOO-123 BAR-456"])
        
    def test_08_empty_git_output(self):
        matches = extract_matches("", r"\[TPR-\d+\]")
        self.assertEqual(matches, [])
        
    def test_09_empty_commit_message_body(self):
        git_output = "COMMIT_MSG_START\n\nCOMMIT_MSG_END\n"
        matches = extract_matches(git_output, r"\[TPR-\d+\]")
        self.assertEqual(matches, [])

    def test_10_missing_end_marker(self):
        git_output = "COMMIT_MSG_START\n[TPR-123] Unfinished\n"
        matches = extract_matches(git_output, r"\[TPR-\d+\]")
        self.assertEqual(matches, [])

    def test_11_multiple_commits_no_matches(self):
        git_output = (
            "COMMIT_MSG_START\nNo match\nCOMMIT_MSG_END\n"
            "COMMIT_MSG_START\nStill no match\nCOMMIT_MSG_END\n"
        )
        matches = extract_matches(git_output, r"\[TPR-\d+\]")
        self.assertEqual(matches, [])
        
    def test_12_regex_matching_full_string(self):
        git_output = "COMMIT_MSG_START\nMATCHME\nCOMMIT_MSG_END\n"
        matches = extract_matches(git_output, r"MATCHME")
        self.assertEqual(matches, ["MATCHME"])

    @patch('subprocess.check_output')
    def test_13_get_git_commits_depth_1(self, mock_subproc):
        # mock git blame output
        mock_subproc.side_effect = [
            "^abcdef1234567890abcdef1234567890abcdef12 (user 2026 1) line 1\n",
            "COMMIT_MSG_START\n[TPR-1] msg\nCOMMIT_MSG_END\n"
        ]
        res = get_git_commits("test.txt", 10, 15, 1)
        calls = mock_subproc.mock_calls
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][1][0], ['git', 'blame', '-l', '-L10,15', 'test.txt'])
        self.assertEqual(calls[1][1][0], ['git', 'show', '-s', '--format=COMMIT_MSG_START%n%B%nCOMMIT_MSG_END', 'abcdef1234567890abcdef1234567890abcdef12'])
        self.assertEqual(res, "COMMIT_MSG_START\n[TPR-1] msg\nCOMMIT_MSG_END\n")

    @patch('subprocess.check_output')
    def test_14_get_git_commits_depth_greater_than_1(self, mock_subproc):
        # mock git log per line, then git show
        mock_subproc.side_effect = [
            "COMMIT_HASH:1111111111111111111111111111111111111111\n",
            "COMMIT_HASH:2222222222222222222222222222222222222222\n",
            "fake_msg"
        ]
        res = get_git_commits("test.txt", 5, 6, 2)
        calls = mock_subproc.mock_calls
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0][1][0], ['git', 'log', '-L5,5:test.txt', '-n2', '--format=COMMIT_HASH:%H'])
        self.assertEqual(calls[1][1][0], ['git', 'log', '-L6,6:test.txt', '-n2', '--format=COMMIT_HASH:%H'])
        # third call is git show, order of hashes may vary due to set
        git_show_cmd = calls[2][1][0]
        self.assertEqual(git_show_cmd[:4], ['git', 'show', '-s', '--format=COMMIT_MSG_START%n%B%nCOMMIT_MSG_END'])
        self.assertTrue('1111111111111111111111111111111111111111' in git_show_cmd)
        self.assertTrue('2222222222222222222222222222222222222222' in git_show_cmd)
        self.assertEqual(res, "fake_msg")

    @patch('sys.stderr', new_callable=MagicMock)
    @patch('subprocess.check_output')
    def test_15_get_git_commits_error_handling(self, mock_subproc, mock_stderr):
        mock_subproc.side_effect = subprocess.CalledProcessError(128, "git", stderr="fatal: file no longer exists")
        with self.assertRaises(SystemExit) as cm:
            get_git_commits("missing.txt", 1, 1, 1)
        self.assertEqual(cm.exception.code, 1)

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('subprocess.check_output')
    @patch('sys.argv', ['extract_jira_ids.py', 'file.txt', r'\[TPR-\d+\]', '10'])
    def test_16_main_single_line_default_depth(self, mock_subproc, mock_stdout):
        mock_subproc.side_effect = [
            "abcdef1234567890abcdef1234567890abcdef12 (user 1) msg\n",
            "COMMIT_MSG_START\n[TPR-1] msg\nCOMMIT_MSG_END\n"
        ]
        main()
        mock_stdout.write.assert_any_call('["[TPR-1]"]')

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('subprocess.check_output')
    @patch('sys.argv', ['extract_jira_ids.py', 'file.txt', r'\[TPR-\d+\]', '5', '--end-line', '6', '--depth', '5'])
    def test_17_main_line_range_with_depth(self, mock_subproc, mock_stdout):
        mock_subproc.side_effect = [
            "COMMIT_HASH:1111111111111111111111111111111111111111\n",
            "COMMIT_HASH:1111111111111111111111111111111111111111\n",
            "COMMIT_MSG_START\n[TPR-2] msg\nCOMMIT_MSG_END\n"
        ]
        main()
        mock_stdout.write.assert_any_call('["[TPR-2]"]')

    def test_18_regex_with_capture_groups(self):
        git_output = "COMMIT_MSG_START\n[TPR-1] msg\nCOMMIT_MSG_END\n"
        matches = extract_matches(git_output, r"(?:\[TPR-\d+\])")
        self.assertEqual(matches, ["[TPR-1]"])

    def test_19_special_characters_in_commit_message(self):
        git_output = "COMMIT_MSG_START\nFix! @#$ %^&*()_+ [TPR-42] {}|\nCOMMIT_MSG_END\n"
        matches = extract_matches(git_output, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-42]"])

    def test_20_unicode_in_commit_message(self):
        git_output = "COMMIT_MSG_START\n[TPR-123] \U0001f527 Fix bug \u2728\nCOMMIT_MSG_END\n"
        matches = extract_matches(git_output, r"\[TPR-\d+\]")
        self.assertEqual(matches, ["[TPR-123]"])

    @patch('sys.stderr', new_callable=MagicMock)
    @patch('sys.argv', ['extract_jira_ids.py', 'file.txt', '*', '10'])
    def test_21_invalid_regex_pattern(self, mock_stderr):
        with self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 1)
        mock_stderr.write.assert_any_call('{"error": "Invalid regex pattern", "details": "nothing to repeat at position 0"}')

if __name__ == '__main__':
    unittest.main()
