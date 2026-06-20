"""MCP stdio server for storing and retrieving architectural knowledge."""

import json
import os
import re
import subprocess
import sys
import string
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP


DEFAULT_KNOWLEDGE_SERVER_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_JIRA_REGEX = r"\[[A-Z][A-Z0-9]+-\d+\]"
DEFAULT_RETRIEVAL_DEPTH = 3
SUMMARY_SECTION_NAMES = (
    "Problem",
    "Decision",
    "Alternatives considered",
    "Constraints",
    "Impact/risk",
    "Validation performed",
)

mcp = FastMCP("fungus-knowledge-mcp")


def _base_url() -> str:
    """Resolve the knowledge server base URL from environment or default."""
    return os.getenv("KNOWLEDGE_SERVER_BASE_URL", DEFAULT_KNOWLEDGE_SERVER_URL).rstrip("/")


def _timeout_seconds() -> float:
    """Resolve outbound HTTP timeout for knowledge server calls."""
    raw = os.getenv("KNOWLEDGE_SERVER_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def _error_payload(operation: str, _exc: Exception) -> dict[str, Any]:
    """Return a normalized, tool-friendly error payload."""
    if operation == "save_knowledge":
        return {
            "message": "Unable to save knowledge right now. Please try again in a moment."
        }
    if operation == "retrieve_knowledge":
        return {
            "message": "Unable to fetch knowledge right now. Please try again in a moment."
        }
    return {"message": "Something went wrong. Please try again."}


def _repo_root() -> Path:
    """Resolve the repository root path from this module location."""
    return Path(__file__).resolve().parents[2]


def _git_script_path() -> Path:
    """Resolve path to the git commit regex extraction script."""
    return _repo_root() / "git-scripts" / "extract_regex_from_commit.py"


def _normalize_jira_id(jira_id: str) -> str:
    """Normalize bracketed and unbracketed JIRA IDs to API format."""
    ticket = jira_id.strip()
    if ticket.startswith("[") and ticket.endswith("]"):
        ticket = ticket[1:-1].strip()
    return ticket


def _extract_jira_ids_from_output(chunks: list[str]) -> list[str]:
    """Extract and deduplicate JIRA IDs from script output chunks, preserving order."""
    seen: set[str] = set()
    ordered: list[str] = []

    for chunk in chunks:
        for token in re.findall(DEFAULT_JIRA_REGEX, chunk):
            cleaned = _normalize_jira_id(token)
            if cleaned not in seen:
                seen.add(cleaned)
                ordered.append(cleaned)

    return ordered


def _extract_jira_ids_for_code(
    file_path: str,
    start_line: int,
    end_line: int,
    depth: int,
    jira_regex: str,
) -> list[str]:
    """Use the git helper script to derive JIRA IDs from commit history for a code range."""
    script = _git_script_path()
    if not script.exists():
        raise FileNotFoundError(f"Git script not found: {script}")

    cmd = [
        sys.executable,
        str(script),
        file_path,
        jira_regex,
        str(start_line),
        "--end-line",
        str(end_line),
        "--depth",
        str(depth),
    ]
    output = subprocess.check_output(
        cmd,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(_repo_root()),
    )
    payload = json.loads(output)
    if not isinstance(payload, list):
        raise ValueError("Unexpected git script output format")

    return _extract_jira_ids_from_output(payload)


def _build_section_pattern(section_name: str) -> re.Pattern[str]:
    """Build regex used to extract one labeled summary section."""
    all_sections_pattern = "|".join(re.escape(name) for name in SUMMARY_SECTION_NAMES)
    pattern = rf"(?:^|\n)\s*{re.escape(section_name)}:\s*(.*?)(?=(?:\n+\s*(?:{all_sections_pattern}):)|$)"
    return re.compile(pattern, flags=re.IGNORECASE | re.DOTALL)


def _extract_summary_sections(content: str) -> dict[str, str]:
    """Extract named sections from content if present."""
    extracted: dict[str, str] = {}
    for section_name in SUMMARY_SECTION_NAMES:
        match = _build_section_pattern(section_name).search(content)
        if not match:
            continue
        value = match.group(1).strip()
        if value:
            extracted[section_name] = value
    return extracted


def _merge_entries_for_summary(entries: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Merge entries into deduplicated section buckets for display."""
    merged: dict[str, list[str]] = {name: [] for name in SUMMARY_SECTION_NAMES}

    for entry in entries:
        content = str(entry.get("content", "")).strip()
        if not content:
            continue

        extracted_sections = _extract_summary_sections(content)
        if extracted_sections:
            for section_name, section_value in extracted_sections.items():
                _append_unique_summary_point(merged[section_name], section_value)
            continue

        # Preserve full content when it does not use expected section labels.
        _append_unique_summary_point(merged["Decision"], content)

    return merged


def _render_jira_summary(jira_id: str, entries: list[dict[str, Any]]) -> list[str]:
    """Render one JIRA section in user-safe markdown."""
    lines = [
        f"## **Knowledge Summary for {jira_id}**",
        f"**Entries included:** {len(entries)}",
    ]

    if not entries:
        lines.append("No entries found for this JIRA ID.")
        lines.append("")
        return lines

    merged = _merge_entries_for_summary(entries)
    lines.append("### **Combined Summary**")
    for section_name in SUMMARY_SECTION_NAMES:
        points = merged[section_name]
        if not points:
            continue
        lines.append(f"**{section_name}:**")
        for point in points:
            lines.append(f"- {point}")

    lines.append("")
    lines.append("Need deeper history or more context? Share a file/line range or request a higher depth.")
    lines.append("")
    return lines


def _format_retrieval_summary(results: dict[str, list[dict[str, Any]]]) -> str:
    """Build a readable, user-safe summary without exposing raw DB fields."""
    lines: list[str] = []
    for jira_id, entries in results.items():
        lines.extend(_render_jira_summary(jira_id, entries))

    return "\n".join(lines).strip()


def _normalize_summary_text(value: str) -> str:
    """Normalize text for low-cost similarity checks."""
    compact = " ".join(value.lower().split())
    return compact.translate(str.maketrans("", "", string.punctuation)).strip()


def _is_similar_summary_point(existing: str, candidate: str) -> bool:
    """Heuristically identify duplicate or near-duplicate summary points."""
    existing_norm = _normalize_summary_text(existing)
    candidate_norm = _normalize_summary_text(candidate)

    if not existing_norm or not candidate_norm:
        return False
    if existing_norm == candidate_norm:
        return True
    if existing_norm in candidate_norm or candidate_norm in existing_norm:
        return True

    existing_tokens = set(existing_norm.split())
    candidate_tokens = set(candidate_norm.split())
    if not existing_tokens or not candidate_tokens:
        return False

    overlap = existing_tokens.intersection(candidate_tokens)
    similarity = len(overlap) / min(len(existing_tokens), len(candidate_tokens))
    return similarity >= 0.75


def _append_unique_summary_point(points: list[str], candidate: str) -> None:
    """Merge similar points by keeping the richer phrasing and avoiding repetition."""
    for index, existing in enumerate(points):
        if _is_similar_summary_point(existing, candidate):
            if len(candidate.strip()) > len(existing.strip()):
                points[index] = candidate.strip()
            return
    points.append(candidate.strip())


def _resolve_depth(depth: int | None) -> int:
    """Resolve retrieval depth to default when omitted."""
    return depth if depth is not None else DEFAULT_RETRIEVAL_DEPTH


def _resolve_save_content(
    chat_context: str | None,
    content: str | None,
    metadata: dict[str, Any] | None,
) -> str:
    """Combine all available save inputs without losing user-provided information."""
    parts: list[str] = []

    if chat_context and chat_context.strip():
        parts.append(chat_context.strip())
    if content and content.strip():
        normalized = content.strip()
        if normalized not in parts:
            parts.append(normalized)

    if metadata and isinstance(metadata, dict):
        for key in ("chat_context", "conversation_summary", "context"):
            raw = metadata.get(key)
            if isinstance(raw, str) and raw.strip():
                normalized = raw.strip()
                if normalized not in parts:
                    parts.append(normalized)

    return "\n\n".join(parts).strip()


async def _save_context(ticket_ids: list[str], content: str, metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Persist knowledge content via the FastAPI knowledge endpoint."""
    payload = {
        "ticket_ids": ticket_ids,
        "content": content,
        "metadata": metadata,
    }
    url = f"{_base_url()}/api/v1/context/"

    async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


async def _retrieve_context(jira_ids: list[str], depth: int | None) -> dict[str, list[dict[str, Any]]]:
    """Fetch architectural context entries for supplied JIRA IDs."""
    results: dict[str, list[dict[str, Any]]] = {}

    async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
        for jira_id in jira_ids:
            normalized = _normalize_jira_id(jira_id)

            if depth is not None:
                if depth < 1:
                    raise ValueError("depth must be >= 1 when provided")
                url = f"{_base_url()}/api/v1/context/jira/{normalized}/recent"
                response = await client.get(url, params={"depth": depth})
            else:
                url = f"{_base_url()}/api/v1/context/jira/{normalized}"
                response = await client.get(url)

            if response.status_code == 404:
                results[normalized] = []
                continue

            response.raise_for_status()
            body = response.json()
            results[normalized] = body if isinstance(body, list) else []

    return results


@mcp.tool(
    description=(
        "Generic save tool for architectural knowledge. "
        "Provide jira_ids and chat_context/content from the current chat. "
        "If the user does not provide chat_context explicitly, the client/agent should summarize the active chat and send it."
    )
)
async def save_knowledge(
    jira_ids: list[str],
    chat_context: str | None = None,
    content: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist architectural knowledge and return generated key metadata."""
    resolved_content = _resolve_save_content(chat_context, content, metadata)
    if not jira_ids:
        return {"message": "Please add JIRA ID(s) against which the context should be saved."}
    if not resolved_content:
        return {
            "message": (
                "Missing chat content. The MCP server cannot read the active chat by itself; "
                "your client/agent must pass a summary/transcript as chat_context (or content)."
            )
        }

    try:
        data = await _save_context(jira_ids, resolved_content, metadata)
        key = data.get("key", "<unknown-key>")
        entry_id = data.get("entry_id", "<unknown-entry>")
        return {"message": f"Context saved successfully for {key} (entry_id: {entry_id})."}
    except Exception as exc:  # noqa: BLE001 - convert all network/protocol errors to tool payload
        return _error_payload("save_knowledge", exc)


@mcp.tool(
    description=(
        "Alias for save_knowledge; accepts jira_ids + chat context and stores it in the knowledge server."
    )
)
async def save_architectural_knowledge(
    jira_ids: list[str],
    chat_context: str | None = None,
    content: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compatibility alias for save_knowledge."""
    return await save_knowledge(jira_ids=jira_ids, chat_context=chat_context, content=content, metadata=metadata)


@mcp.tool(
    description=(
        "Alias with alternate naming used in chat prompts; behaves the same as save_knowledge."
    )
)
async def save_architecture_knowledge(
    jira_ids: list[str],
    chat_context: str | None = None,
    content: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Alternate-name alias for save_knowledge."""
    return await save_knowledge(jira_ids=jira_ids, chat_context=chat_context, content=content, metadata=metadata)


@mcp.tool(
    description=(
        "Generic retrieval tool. Accept jira_ids directly, or provide a code location to auto-extract JIRA IDs from git history."
    )
)
async def retrieve_knowledge(
    jira_ids: list[str] | None = None,
    file_path: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    depth: int | None = DEFAULT_RETRIEVAL_DEPTH,
    jira_regex: str = DEFAULT_JIRA_REGEX,
) -> dict[str, Any]:
    """Fetch architectural context entries from explicit or git-derived JIRA IDs."""
    resolved_jira_ids = list(jira_ids or [])

    if not resolved_jira_ids and file_path:
        if start_line is None:
            return {"message": "start_line is required when file_path is provided"}
        actual_end_line = end_line if end_line is not None else start_line
        effective_depth = _resolve_depth(depth)

        if actual_end_line < start_line:
            return {"message": "end_line must be >= start_line"}

        try:
            resolved_jira_ids = _extract_jira_ids_for_code(
                file_path=file_path,
                start_line=start_line,
                end_line=actual_end_line,
                depth=effective_depth,
                jira_regex=jira_regex,
            )
        except Exception as exc:  # noqa: BLE001
            return _error_payload("retrieve_knowledge", exc)

    if not resolved_jira_ids:
        return {"message": "No jira_ids provided or extracted from git history"}

    try:
        results = await _retrieve_context(resolved_jira_ids, depth)
        summary = _format_retrieval_summary(results).strip()
        if not summary:
            summary = "No architectural knowledge entries found for the provided JIRA IDs."
        return {
            "message": summary,
        }
    except Exception as exc:  # noqa: BLE001 - convert all network/protocol errors to tool payload
        return _error_payload("retrieve_knowledge", exc)


@mcp.tool(
    description=(
        "Compatibility alias for retrieve_knowledge using explicit jira_ids."
    )
)
async def retrieve_architectural_knowledge(
    jira_ids: list[str],
    depth: int | None = DEFAULT_RETRIEVAL_DEPTH,
) -> dict[str, Any]:
    """Compatibility alias for retrieve_knowledge with explicit JIRA IDs."""
    return await retrieve_knowledge(jira_ids=jira_ids, depth=_resolve_depth(depth))


@mcp.tool(
    description=(
        "Retrieve architectural knowledge from selected code by running git history extraction then querying the knowledge server."
    )
)
async def retrieve_knowledge_from_code(
    file_path: str,
    start_line: int,
    end_line: int | None = None,
    depth: int = DEFAULT_RETRIEVAL_DEPTH,
    jira_regex: str = DEFAULT_JIRA_REGEX,
) -> dict[str, Any]:
    """Code-selection helper alias for retrieve_knowledge."""
    return await retrieve_knowledge(
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        depth=depth,
        jira_regex=jira_regex,
    )


def main() -> None:
    """Run the MCP server over stdio for desktop clients."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()