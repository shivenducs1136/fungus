### $ `py extract_regex_from_commit.py`
Extract regex matches from git commit messages for a line or range.

positional arguments:
  - filepath             Path to the file
  - regex                Regex pattern to match (e.g., '\[TPR-\d+\]')
  - start_line           Starting line number

options:
  - -h, --help           show this help message and exit
  - --end-line END_LINE  Ending line number (defaults to start_line)
  - --depth DEPTH        Number of historical commits to fetch

### Automated testing

From repository root:

`./.venv/Scripts/python.exe -m pytest -q git-scripts/test_extract_regex_from_commit.py`

From `git-scripts/` directory:

`../.venv/Scripts/python.exe -m pytest -q test_extract_regex_from_commit.py`

### Manual testing

- for manual testing `tally-git-sample-manualtesting` dir is there
- it as a sub .git folder which has 100 commits having random jira ids and a sample python file having those commits
- we can use our tool to extract commits

### sample terminal outputs

``` bash
(.venv) PS D:\fungus\git-scripts\tally-git-sample-manualtesting> py ..\extract_regex_from_commit.py .\sample_code.py '\[TPR-\d+\]' 1
["[TPR-1001]"]
(.venv) PS D:\fungus\git-scripts\tally-git-sample-manualtesting> py ..\extract_regex_from_commit.py .\sample_code.py '\[TPR-\d+\]' 2
["[TPR-2002] [TPR-2102]"]
(.venv) PS D:\fungus\git-scripts\tally-git-sample-manualtesting> py ..\extract_regex_from_commit.py .\sample_code.py '\[TPR-\d+\]' 3
["[TPR-3003] [TPR-3103] [TPR-3203]"]
(.venv) PS D:\fungus\git-scripts\tally-git-sample-manualtesting> py ..\extract_regex_from_commit.py .\sample_code.py '\[TPR-\d+\]' 1 --end-line 3
["[TPR-1001]", "[TPR-3003] [TPR-3103] [TPR-3203]", "[TPR-2002] [TPR-2102]"]
(.venv) PS D:\fungus\git-scripts\tally-git-sample-manualtesting> py ..\extract_regex_from_commit.py .\sample_code.py '\[TPR-\d+\]' 1 --end-line 3 --depth 1
["[TPR-2002] [TPR-2102]", "[TPR-3003] [TPR-3103] [TPR-3203]", "[TPR-1001]"]
(.venv) PS D:\fungus\git-scripts\tally-git-sample-manualtesting> py ..\extract_regex_from_commit.py .\sample_code.py '\[TPR-\d+\]' 1 --end-line 3 --depth 3
["[TPR-2002] [TPR-2102]", "[TPR-1001]", "[TPR-3003] [TPR-3103] [TPR-3203]"]
```