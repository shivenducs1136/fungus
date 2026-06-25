import argparse
import re
import json
import sys
import os
from pathlib import Path

import git
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.logging_config import get_logger

log = get_logger("fungus.git_scripts.extract_regex", "extract_regex_from_commit.log")


def get_git_commits(filepath, start_line, end_line, depth):
    log.info("get_git_commits — filepath=%r start_line=%d end_line=%d depth=%d", filepath, start_line, end_line, depth)

    file_dir = os.path.dirname(os.path.abspath(filepath))
    log.debug("Resolved file directory: %s", file_dir)

    try:
        repo = git.Repo(file_dir, search_parent_directories=True)
        log.debug("Opened repo at: %s", repo.working_dir)
    except git.InvalidGitRepositoryError:
        log.error("No git repository found for path: %s", file_dir)
        raise

    # Make filepath relative to repo root for GitPython calls
    repo_root = Path(repo.working_dir)
    abs_filepath = Path(filepath).resolve()
    try:
        rel_filepath = str(abs_filepath.relative_to(repo_root))
    except ValueError:
        rel_filepath = str(abs_filepath)
    log.debug("Relative filepath for git calls: %s", rel_filepath)

    commit_messages: list[str] = []

    try:
        if depth == 1:
            log.debug("Using GitPython blame for lines %d-%d", start_line, end_line)
            blame_entries = repo.blame("HEAD", rel_filepath, L=f"{start_line},{end_line}")
            seen_hashes: set[str] = set()
            for blame_commit, _ in blame_entries:
                if blame_commit is None:
                    continue
                hexsha = blame_commit.hexsha
                if hexsha not in seen_hashes and not hexsha.startswith("0" * 40):
                    seen_hashes.add(hexsha)
                    commit_messages.append(blame_commit.message)
            log.debug("GitPython blame found %d unique commit(s)", len(seen_hashes))
        else:
            log.debug("Using git log -L per-line for depth=%d over %d lines", depth, end_line - start_line + 1)
            seen_hashes: set[str] = set()
            for line_num in range(start_line, end_line + 1):
                raw = repo.git.log(
                    f"-L{line_num},{line_num}:{rel_filepath}",
                    f"-n{depth}",
                    format="COMMIT_HASH:%H",
                )
                hashes = re.findall(r"^COMMIT_HASH:([a-f0-9]{40})$", raw, re.MULTILINE)
                log.debug("Line %d yielded %d commit hash(es): %s", line_num, len(hashes), hashes)
                for hexsha in hashes:
                    if hexsha not in seen_hashes:
                        seen_hashes.add(hexsha)
                        commit_messages.append(repo.commit(hexsha).message)

        if not commit_messages:
            log.info("No commits found for the specified line range — returning empty list")
            return []

        log.info("Fetched %d unique commit message(s)", len(commit_messages))
        return commit_messages

    except git.GitCommandError as e:
        log.error("GitPython command failed — %s", e)
        raise


def extract_matches(commit_messages, regex_pattern):
    log.info("extract_matches — commit_count=%d regex=%r", len(commit_messages), regex_pattern)

    if not commit_messages:
        log.info("No commit messages to search — returning empty list")
        return []

    matches_per_commit = []
    for idx, msg in enumerate(commit_messages):
        matches = re.findall(regex_pattern, msg)
        if matches:
            joined_matches = "".join(matches)
            log.debug("Commit %d: found %d match(es) — %s", idx, len(matches), matches)
            matches_per_commit.append(joined_matches)
        else:
            log.debug("Commit %d: no matches found", idx)

    log.info("extract_matches complete — %d commit(s) with matches out of %d total", len(matches_per_commit), len(commit_messages))
    return matches_per_commit


def main():
    parser = argparse.ArgumentParser(description="Extract regex matches from git commit messages for a line or range.")
    parser.add_argument("filepath", help="Path to the file")
    parser.add_argument("regex", help="Regex pattern to match (e.g., '\\[TPR-\\d+\\]')")
    parser.add_argument("start_line", type=int, help="Starting line number")
    parser.add_argument("--end-line", type=int, help="Ending line number (defaults to start_line)", default=None)
    parser.add_argument("--depth", type=int, help="Number of historical commits to fetch", default=1)

    args = parser.parse_args()
    log.info(
        "main — filepath=%r regex=%r start_line=%d end_line=%s depth=%d",
        args.filepath,
        args.regex,
        args.start_line,
        args.end_line,
        args.depth,
    )

    try:
        re.compile(args.regex)
        log.debug("Regex pattern is valid: %r", args.regex)
    except re.error as e:
        log.error("Invalid regex pattern %r — %s", args.regex, e)
        print(json.dumps({"error": "Invalid regex pattern", "details": str(e)}), file=sys.stderr)
        sys.exit(1)

    end_line = args.end_line if args.end_line is not None else args.start_line
    log.debug("Effective end_line resolved to %d", end_line)

    commit_messages = get_git_commits(args.filepath, args.start_line, end_line, args.depth)
    results = extract_matches(commit_messages, args.regex)

    log.info("Final results: %d item(s) — %s", len(results), results)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
