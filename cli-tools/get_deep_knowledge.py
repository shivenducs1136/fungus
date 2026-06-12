"""
Deep Knowledge Context Tracker - Retrieval Tool

Usage:
    python get_deep_knowledge.py --file <file_path> --line <line_number>

Workflow:
  1. Runs 'git blame' on the specified line to extract the commit hash.
  2. Runs 'git log' to read the full commit message for that hash.
  3. Parses the commit message for a 'Deep-Knowledge-Key: ctx-...' line.
  4. Fetches and prints the knowledge document from the backend API.
"""

import argparse
import json
import re
import subprocess
import sys

import requests

API_BASE_URL = "http://localhost:8000/api/v1/knowledge"
DEEP_KEY_RE = re.compile(r"Deep-Knowledge-Key:\s*(ctx-[a-zA-Z0-9]+)")


def run_command(cmd: list[str]) -> str:
    """
    Run a subprocess command and return its stdout as a stripped string.
    Exits with an error message if the command fails.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        print(
            f"ERROR: Command failed: {' '.join(cmd)}\n"
            f"  stderr: {exc.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)
    except FileNotFoundError:
        print(
            f"ERROR: Command not found: '{cmd[0]}'. Is git installed and on PATH?",
            file=sys.stderr,
        )
        sys.exit(1)


def extract_commit_hash_from_blame(blame_output: str) -> str:
    """
    Parse the commit hash from the first token of 'git blame --porcelain' output.
    """
    first_token = blame_output.split()[0] if blame_output else ""
    if not first_token:
        print("ERROR: Could not parse commit hash from git blame output.", file=sys.stderr)
        sys.exit(1)
    return first_token


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve deep architectural knowledge linked to a line of code via Git."
    )
    parser.add_argument(
        "--file",
        required=True,
        metavar="FILE_PATH",
        help="Path to the source file to inspect.",
    )
    parser.add_argument(
        "--line",
        required=True,
        metavar="LINE_NUMBER",
        help="Line number (or range N,M) to look up in git blame.",
    )
    args = parser.parse_args()

    file_path = args.file
    line_spec = args.line

    # Normalise line spec: accept both '42' and '42,42'
    if "," in line_spec:
        blame_range = line_spec
    else:
        blame_range = f"{line_spec},{line_spec}"

    # --- Step 1: git blame to get the commit hash ---
    print(f"[1/4] Running git blame on {file_path} line {blame_range} ...", file=sys.stderr)
    blame_output = run_command(
        ["git", "blame", "--porcelain", "-L", blame_range, "--", file_path]
    )
    commit_hash = extract_commit_hash_from_blame(blame_output)
    print(f"      Commit hash: {commit_hash}", file=sys.stderr)

    # --- Step 2: git log to get the full commit message ---
    print(f"[2/4] Reading commit message for {commit_hash} ...", file=sys.stderr)
    commit_message = run_command(
        ["git", "log", "-1", "--format=%B", commit_hash]
    )

    if not commit_message:
        print(
            f"ERROR: No commit message found for hash '{commit_hash}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Step 3: Parse the Deep-Knowledge-Key from the commit message ---
    print("[3/4] Parsing Deep-Knowledge-Key from commit message ...", file=sys.stderr)
    match = DEEP_KEY_RE.search(commit_message)
    if not match:
        print(
            "ERROR: No 'Deep-Knowledge-Key' found in the commit message.\n"
            "       This commit was not tagged with a knowledge context.",
            file=sys.stderr,
        )
        sys.exit(1)

    ctx_hash = match.group(1)
    print(f"      Found key: {ctx_hash}", file=sys.stderr)

    # --- Step 4: Fetch the knowledge document from the backend API ---
    print(f"[4/4] Fetching knowledge document for {ctx_hash} ...", file=sys.stderr)
    url = f"{API_BASE_URL}/{ctx_hash}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(
            f"ERROR: Could not connect to the knowledge server at {API_BASE_URL}.\n"
            "Make sure the server is running: python knowledge-server/server.py",
            file=sys.stderr,
        )
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        if response.status_code == 404:
            print(
                f"ERROR: Knowledge document '{ctx_hash}' not found in the store.\n"
                "       The server may have been reset or the key is stale.",
                file=sys.stderr,
            )
        else:
            print(f"ERROR: Server returned an error: {exc}", file=sys.stderr)
        sys.exit(1)

    document = response.json()

    # --- Output: pretty-print the JSON document to stdout ---
    print("\n" + "=" * 60, file=sys.stderr)
    print(f"  Deep Knowledge Document: {ctx_hash}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(json.dumps(document, indent=2))


if __name__ == "__main__":
    main()