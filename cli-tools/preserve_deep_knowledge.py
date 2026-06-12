"""
Deep Knowledge Context Tracker - Capture Tool

Usage:
    python preserve_deep_knowledge.py --tickets TPR-48892 [TPR-12345] --context '{"tickets": {...}}'

Sends the context payload to the backend API and prints:
    Deep-Knowledge-Key: ctx-<hash>

This line is designed to be appended as the very last line of a Git commit message.
"""

import argparse
import json
import re
import sys

import requests

API_URL = "http://localhost:8000/api/v1/knowledge"
JIRA_BRACKET_RE = re.compile(r"^\[?(TPR-\d+)\]?$", re.IGNORECASE)


def clean_ticket_id(raw: str) -> str:
    """
    Strip surrounding brackets from a Jira ticket ID.
    Accepts both 'TPR-48892' and '[TPR-48892]' and returns 'TPR-48892'.
    Raises ValueError if the format is unrecognised.
    """
    match = JIRA_BRACKET_RE.match(raw.strip())
    if not match:
        raise ValueError(
            f"Invalid Jira ticket ID '{raw}'. Expected format: TPR-XXXXX or [TPR-XXXXX]"
        )
    return match.group(1).upper()


def main():
    parser = argparse.ArgumentParser(
        description="Capture deep architectural knowledge and link it to Jira tickets."
    )
    parser.add_argument(
        "--tickets",
        nargs="+",
        required=True,
        metavar="TICKET",
        help="One or more Jira ticket IDs (e.g. TPR-48892 or [TPR-48892]).",
    )
    parser.add_argument(
        "--context",
        required=True,
        metavar="JSON",
        help="JSON string containing the session context payload.",
    )
    args = parser.parse_args()

    # --- Validate and parse the JSON context ---
    try:
        context_data = json.loads(args.context)
    except json.JSONDecodeError as exc:
        print(f"ERROR: --context is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(context_data, dict):
        print("ERROR: --context must be a JSON object (dict).", file=sys.stderr)
        sys.exit(1)

    # --- Clean and validate ticket IDs ---
    cleaned_tickets = []
    for raw in args.tickets:
        try:
            cleaned_tickets.append(clean_ticket_id(raw))
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

    # --- Build the payload ---
    # If the context already has a 'tickets' key, merge cleaned IDs as the
    # canonical keys; otherwise wrap the whole context under the tickets.
    if "tickets" in context_data and isinstance(context_data["tickets"], dict):
        # Re-key any existing ticket entries using cleaned IDs
        raw_tickets = context_data["tickets"]
        cleaned_ticket_data = {}
        for raw_key, value in raw_tickets.items():
            try:
                clean_key = clean_ticket_id(raw_key)
            except ValueError:
                clean_key = raw_key  # preserve unknown keys as-is
            cleaned_ticket_data[clean_key] = value
        payload = {**context_data, "tickets": cleaned_ticket_data}
    else:
        # Wrap the entire context under the first cleaned ticket ID
        payload = {"tickets": {tid: context_data for tid in cleaned_tickets}}

    # --- POST to the backend API ---
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(
            f"ERROR: Could not connect to the knowledge server at {API_URL}.\n"
            "Make sure the server is running: python knowledge-server/server.py",
            file=sys.stderr,
        )
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        print(
            f"ERROR: Server returned an error: {exc}\n{response.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    ctx_hash = response.json().get("hash")
    if not ctx_hash:
        print("ERROR: Server response did not contain a hash.", file=sys.stderr)
        sys.exit(1)

    # --- Print the key line (designed to be the last line of a commit message) ---
    print(f"Deep-Knowledge-Key: {ctx_hash}")


if __name__ == "__main__":
    main()