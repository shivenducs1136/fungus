import argparse
import subprocess
import re
import json
import sys

def get_git_commits(filepath, start_line, end_line, depth):
    commit_hashes = set()
    
    try:
        if depth == 1:
            # For depth=1, use git blame to efficiently find the exact commit currently responsible for each line
            cmd = ["git", "blame", "-l", f"-L{start_line},{end_line}", filepath]
            output = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
            for line in output.splitlines():
                parts = line.split()
                if parts:
                    commit_hash = parts[0].lstrip('^')
                    # Ignore uncommitted lines (all zeros)
                    if commit_hash and not commit_hash.startswith('0000000000000000000000000000000000000000'):
                        commit_hashes.add(commit_hash)
        else:
            # For depth > 1, get history for each line individually to guarantee we reach the depth per line
            for line_num in range(start_line, end_line + 1):
                cmd = [
                    "git", "log", f"-L{line_num},{line_num}:{filepath}",
                    f"-n{depth}", "--format=COMMIT_HASH:%H"
                ]
                output = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
                matches = re.findall(r'^COMMIT_HASH:([a-f0-9]{40})$', output, re.MULTILINE)
                commit_hashes.update(matches)
                
        if not commit_hashes:
            return ""
            
        # Fetch the commit messages for all unique hashes
        hashes = list(commit_hashes)
        batch_size = 50
        all_output = ""
        
        for i in range(0, len(hashes), batch_size):
            batch = hashes[i:i+batch_size]
            cmd = ["git", "show", "-s", "--format=COMMIT_MSG_START%n%B%nCOMMIT_MSG_END"] + batch
            output = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
            all_output += output
            
        return all_output

    except subprocess.CalledProcessError as e:
        print(json.dumps({"error": str(e), "stderr": e.stderr}), file=sys.stderr)
        sys.exit(1)

def extract_matches(git_output, regex_pattern):
    matches_per_commit = []
    
    commit_messages = re.findall(r'COMMIT_MSG_START\n(.*?)\nCOMMIT_MSG_END', git_output, re.DOTALL)
    
    for msg in commit_messages:
        matches = re.findall(regex_pattern, msg)
        if matches:
            joined_matches = "".join(matches)
            matches_per_commit.append(joined_matches)
            
    return matches_per_commit

def main():
    parser = argparse.ArgumentParser(description="Extract regex matches from git commit messages for a line or range.")
    parser.add_argument("filepath", help="Path to the file")
    parser.add_argument("regex", help="Regex pattern to match (e.g., '\\[TPR-\\d+\\]')")
    parser.add_argument("start_line", type=int, help="Starting line number")
    parser.add_argument("--end-line", type=int, help="Ending line number (defaults to start_line)", default=None)
    parser.add_argument("--depth", type=int, help="Number of historical commits to fetch", default=1)
    
    args = parser.parse_args()
    
    # Validate the regex pattern before running git commands
    try:
        re.compile(args.regex)
    except re.error as e:
        print(json.dumps({"error": "Invalid regex pattern", "details": str(e)}), file=sys.stderr)
        sys.exit(1)
        
    end_line = args.end_line if args.end_line is not None else args.start_line
    
    git_output = get_git_commits(args.filepath, args.start_line, end_line, args.depth)
    results = extract_matches(git_output, args.regex)
    
    print(json.dumps(results))

if __name__ == "__main__":
    main()
