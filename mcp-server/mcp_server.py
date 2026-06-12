"""
Deep Knowledge Context Tracker - MCP Server

Exposes two tools to Cline (and any MCP-compatible client):

  1. preserve_deep_knowledge  — Captures architectural reasoning for a set of
                                Jira tickets and stores it in the knowledge
                                server. Returns the Deep-Knowledge-Key to
                                append as the last line of the Git commit.

  2. fetch_knowledge          — Given a Deep-Knowledge-Key (ctx-XXXX), fetches
                                and returns the full knowledge document from
                                the knowledge server.

                                NOTE: Cline is responsible for running
                                'git blame' and 'git log' itself (via
                                execute_command) to extract the ctx-hash from
                                the commit message before calling this tool.

Prerequisites:
  - The knowledge server must be running:
      python knowledge-server/server.py
  - Install dependencies:
      pip install -r mcp-server/requirements.txt
"""

import json
import re
from typing import Any

import requests
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KNOWLEDGE_SERVER_URL = "http://localhost:8000/api/v1/knowledge"
JIRA_BRACKET_RE = re.compile(r"^\[?(TPR-\d+)\]?$", re.IGNORECASE)

# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "deep-knowledge",
    instructions=(
        "Tools for capturing and retrieving architectural knowledge linked to "
        "Git commits. Use 'preserve_deep_knowledge' before every non-trivial "
        "commit. To retrieve knowledge before modifying code: run 'git blame' "
        "and 'git log' yourself via execute_command to extract the "
        "Deep-Knowledge-Key, then call 'fetch_knowledge' with the ctx-hash."
    ),
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clean_ticket_id(raw: str) -> str:
    """Strip brackets from a Jira ID: '[TPR-48892]' → 'TPR-48892'."""
    match = JIRA_BRACKET_RE.match(raw.strip())
    if not match:
        raise ValueError(
            f"Invalid Jira ticket ID '{raw}'. Expected: TPR-XXXXX or [TPR-XXXXX]"
        )
    return match.group(1).upper()


# ---------------------------------------------------------------------------
# Tool 1: preserve_deep_knowledge
# ---------------------------------------------------------------------------


@mcp.tool()
def preserve_deep_knowledge(
    tickets: list[str],
    focus: str,
    discovered_constraints: list[str],
    discarded_approaches: list[str],
    final_solution: str,
) -> str:
    """
    Capture architectural reasoning for one or more Jira tickets and store it
    in the knowledge server.

    Args:
        tickets:                List of Jira ticket IDs, e.g. ["TPR-48892"] or
                                ["[TPR-48892]", "TPR-12345"].
        focus:                  One-line description of what this change fixes
                                or implements.
        discovered_constraints: List of constraints discovered during
                                investigation (legacy rules, hidden deps, etc.).
        discarded_approaches:   List of approaches that were tried and rejected,
                                with reasons.
        final_solution:         Precise description of the solution implemented.

    Returns:
        The line to append as the very last line of the Git commit message,
        e.g. "Deep-Knowledge-Key: ctx-8589f5485964".
    """
    # --- Clean ticket IDs ---
    cleaned: dict[str, Any] = {}
    for raw in tickets:
        try:
            tid = _clean_ticket_id(raw)
        except ValueError as exc:
            return f"ERROR: {exc}"
        cleaned[tid] = {
            "focus": focus,
            "discovered_constraints": discovered_constraints,
            "discarded_approaches": discarded_approaches,
            "final_solution": final_solution,
        }

    payload = {"tickets": cleaned}

    # --- POST to knowledge server ---
    try:
        response = requests.post(KNOWLEDGE_SERVER_URL, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return (
            "ERROR: Could not connect to the knowledge server at "
            f"{KNOWLEDGE_SERVER_URL}.\n"
            "Make sure it is running: python knowledge-server/server.py"
        )
    except requests.exceptions.HTTPError as exc:
        return f"ERROR: Knowledge server returned an error: {exc}\n{response.text}"

    ctx_hash = response.json().get("hash")
    if not ctx_hash:
        return "ERROR: Knowledge server response did not contain a hash."

    return (
        f"Deep-Knowledge-Key: {ctx_hash}\n\n"
        f"Append the line above as the **absolute last line** of your Git commit "
        f"message (after Signed-off-by: if present). No trailing newline after it."
    )


# ---------------------------------------------------------------------------
# Tool 2: fetch_knowledge
# ---------------------------------------------------------------------------


@mcp.tool()
def fetch_knowledge(ctx_hash: str) -> str:
    """
    Fetch and return the architectural knowledge document for a given
    Deep-Knowledge-Key.

    This tool only performs the HTTP lookup. The caller (Cline) is responsible
    for running 'git blame' and 'git log' via execute_command to extract the
    ctx-hash from the commit message before calling this tool.

    Workflow (Cline's responsibility before calling this tool):
      1. git -C <repo_dir> blame --porcelain -L <line>,<line> -- <file>
         → extract the 40-char commit hash from the first token
      2. git -C <repo_dir> log -1 --format="%B" <commit_hash>
         → read the full commit message
      3. Regex: search for "Deep-Knowledge-Key: (ctx-[a-zA-Z0-9]+)"
      4. Call fetch_knowledge(ctx_hash=<extracted_key>)

    Args:
        ctx_hash: The Deep-Knowledge-Key value, e.g. "ctx-a86482cc3ed6".
                  The "ctx-" prefix is required.

    Returns:
        The full knowledge document as formatted Markdown, or an error message.
    """
    if not ctx_hash.startswith("ctx-"):
        return (
            f"ERROR: Invalid ctx_hash '{ctx_hash}'. "
            "Expected format: 'ctx-<hex>', e.g. 'ctx-a86482cc3ed6'."
        )

    url = f"{KNOWLEDGE_SERVER_URL}/{ctx_hash}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return (
            f"ERROR: Could not connect to the knowledge server at "
            f"{KNOWLEDGE_SERVER_URL}.\n"
            "Make sure it is running: python knowledge-server/server.py"
        )
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            return (
                f"No knowledge document found for key '{ctx_hash}'.\n"
                "The server may have been reset or the store file deleted."
            )
        return f"ERROR: Knowledge server returned HTTP {response.status_code}."

    document = response.json()

    # --- Format output for Cline's context window ---
    lines = [
        "# Deep Knowledge Document",
        f"**Key:** `{ctx_hash}`",
        f"**Timestamp:** {document.get('timestamp', 'unknown')}",
        "",
    ]

    tickets = document.get("tickets", {})
    for ticket_id, info in tickets.items():
        lines += [
            f"## Ticket: {ticket_id}",
            f"**Focus:** {info.get('focus', '')}",
            "",
            "**Discovered Constraints:**",
        ]
        for c in info.get("discovered_constraints", []):
            lines.append(f"- {c}")
        lines += ["", "**Discarded Approaches:**"]
        for a in info.get("discarded_approaches", []):
            lines.append(f"- {a}")
        lines += [
            "",
            f"**Final Solution:** {info.get('final_solution', '')}",
            "",
        ]

    lines.append("---")
    lines.append("*Read the constraints and discarded approaches above carefully*")
    lines.append("*before making any changes to this code.*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")