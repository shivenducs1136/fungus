"""MCP stdio server for storing and retrieving architectural knowledge."""

import os
import re
import string
import sys
from pathlib import Path
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from app.core.logging_config import get_logger

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "git-scripts"))
from extract_regex_from_commit import get_git_commits, extract_matches  # noqa: E402


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

_SENSITIVE_PATTERNS = (
    re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)(api[_-]?key|secret|token|access[_-]?token|refresh[_-]?token)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)([^\s,;]+)"),
    re.compile(r"(?i)(postgres(?:ql)?://[^:\s]+:)([^@\s]+)(@)"),
)

_REDACTION_PLACEHOLDER = "[REDACTED]"

mcp = FastMCP("fungus-knowledge-mcp")

_LOG_DIR = Path(os.getenv("FUNGUS_LOG_DIR", Path(__file__).resolve().parents[2] / "logs"))
_LOG_DIR.mkdir(parents=True, exist_ok=True)

log = get_logger("fungus.mcp.server", "mcp_server.log")


def _base_url() -> str:
    """Resolve the knowledge server base URL from environment or default."""
    url = os.getenv("KNOWLEDGE_SERVER_BASE_URL", DEFAULT_KNOWLEDGE_SERVER_URL).rstrip("/")
    log.debug("Resolved base URL: %s", url)
    return url


def _timeout_seconds() -> float:
    """Resolve outbound HTTP timeout for knowledge server calls."""
    raw = os.getenv("KNOWLEDGE_SERVER_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        result = float(raw)
        log.debug("Resolved timeout: %.1f seconds (raw env value: %r)", result, raw)
        return result
    except ValueError:
        log.warning(
            "Invalid KNOWLEDGE_SERVER_TIMEOUT_SECONDS value %r — falling back to default %.1f",
            raw,
            DEFAULT_TIMEOUT_SECONDS,
        )
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


def _normalize_jira_id(jira_id: str) -> str:
    """Normalize bracketed and unbracketed JIRA IDs to API format."""
    ticket = jira_id.strip()
    if ticket.startswith("[") and ticket.endswith("]"):
        ticket = ticket[1:-1].strip()
    return ticket


def _extract_jira_ids_from_output(chunks: list[str]) -> list[str]:
    """Extract and deduplicate JIRA IDs from script output chunks, preserving order."""
    log.debug("Extracting JIRA IDs from %d output chunks", len(chunks))
    seen: set[str] = set()
    ordered: list[str] = []
    for chunk in chunks:
        for token in re.findall(DEFAULT_JIRA_REGEX, chunk):
            cleaned = _normalize_jira_id(token)
            if cleaned not in seen:
                seen.add(cleaned)
                ordered.append(cleaned)

    log.debug("Extracted %d unique JIRA IDs: %s", len(ordered), ordered)
    return ordered


def _extract_jira_ids_for_code(
    file_path: str,
    start_line: int,
    end_line: int,
    depth: int,
    jira_regex: str,
) -> list[str]:
    """Derive JIRA IDs from commit history by calling git-script functions in-process."""
    log.info(
        "Extracting JIRA IDs for file=%r lines=%d-%d depth=%d regex=%r",
        file_path,
        start_line,
        end_line,
        depth,
        jira_regex,
    )
    git_output = get_git_commits(file_path, start_line, end_line, depth)
    raw_chunks = extract_matches(git_output, jira_regex)
    log.debug("extract_matches returned %d raw chunk(s)", len(raw_chunks))
    result = _extract_jira_ids_from_output(raw_chunks)
    log.info("Resolved %d JIRA IDs from code range: %s", len(result), result)
    return result


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


def _redact_sensitive_text(value: str) -> str:
    """Redact common secret-like tokens from user-visible summary text."""
    redacted = value
    redacted = _SENSITIVE_PATTERNS[0].sub(r"\1=" + _REDACTION_PLACEHOLDER, redacted)
    redacted = _SENSITIVE_PATTERNS[1].sub(r"\1=" + _REDACTION_PLACEHOLDER, redacted)
    redacted = _SENSITIVE_PATTERNS[2].sub(r"\1" + _REDACTION_PLACEHOLDER, redacted)
    redacted = _SENSITIVE_PATTERNS[3].sub(r"\1" + _REDACTION_PLACEHOLDER + r"\3", redacted)
    return redacted


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
            lines.append(f"- {_redact_sensitive_text(point)}")

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
    log.info("Saving context for ticket_ids=%s content_length=%d has_metadata=%s", ticket_ids, len(content), metadata is not None)
    payload = {
        "ticket_ids": ticket_ids,
        "content": content,
        "metadata": metadata,
    }
    url = f"{_base_url()}/api/v1/context/"
    log.debug("POST %s payload ticket_ids=%s content_length=%d", url, ticket_ids, len(content))

    try:
        async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
            response = await client.post(url, json=payload)
            log.debug("Response status: %d", response.status_code)
            response.raise_for_status()
            data = response.json()
            log.info("Context saved successfully — key=%s entry_id=%s", data.get("key"), data.get("entry_id"))
            return data
    except httpx.HTTPStatusError as exc:
        log.error(
            "HTTP error saving context — status=%d url=%s",
            exc.response.status_code,
            exc.request.url,
        )
        raise
    except httpx.RequestError as exc:
        log.error("Network error saving context — %s: %s", type(exc).__name__, exc)
        raise


async def _retrieve_context(jira_ids: list[str], depth: int | None) -> dict[str, list[dict[str, Any]]]:
    """Fetch architectural context entries for supplied JIRA IDs."""
    log.info("Retrieving context for %d JIRA IDs: %s  depth=%s", len(jira_ids), jira_ids, depth)
    results: dict[str, list[dict[str, Any]]] = {}

    try:
        async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
            for jira_id in jira_ids:
                normalized = _normalize_jira_id(jira_id)
                log.debug("normalized jira id: %s", normalized)
                if depth is not None:
                    if depth < 1:
                        log.error("Invalid depth value %d — must be >= 1", depth)
                        raise ValueError("depth must be >= 1 when provided")
                    url = f"{_base_url()}/api/v1/context/jira/{normalized}"
                    log.debug("GET %s params depth=%d", url, depth)
                    response = await client.get(url, params={"depth": depth})
                else:
                    url = f"{_base_url()}/api/v1/context/jira/{normalized}"
                    log.debug("GET %s (no depth filter)", url)
                    response = await client.get(url)

                log.debug("Response for %s: status=%d", normalized, response.status_code)

                if response.status_code == 404:
                    log.info("No entries found for JIRA ID %s (404)", normalized)
                    results[normalized] = []
                    continue

                response.raise_for_status()
                body = response.json()
                entries = body if isinstance(body, list) else []
                log.info("Retrieved %d entries for JIRA ID %s", len(entries), normalized)
                results[normalized] = entries

    except httpx.HTTPStatusError as exc:
        log.error(
            "HTTP error retrieving context — status=%d url=%s",
            exc.response.status_code,
            exc.request.url,
        )
        raise
    except httpx.RequestError as exc:
        log.error("Network error retrieving context — %s: %s", type(exc).__name__, exc)
        raise

    log.info(
        "Retrieval complete — %d JIRA IDs queried, total entries: %d",
        len(results),
        sum(len(v) for v in results.values()),
    )
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
    log.info(
        "save_knowledge called — jira_ids=%s has_chat_context=%s has_content=%s has_metadata=%s",
        jira_ids,
        chat_context is not None,
        content is not None,
        metadata is not None,
    )
    resolved_content = _resolve_save_content(chat_context, content, metadata)
    log.debug("Resolved content length: %d chars", len(resolved_content))

    if not jira_ids:
        log.warning("save_knowledge rejected — no JIRA IDs provided")
        return {"message": "Please add JIRA ID(s) against which the context should be saved."}
    if not resolved_content:
        log.warning("save_knowledge rejected — no resolvable content from chat_context/content/metadata")
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
        log.info("save_knowledge succeeded — key=%s entry_id=%s", key, entry_id)
        return {"message": f"Context saved successfully for {key} (entry_id: {entry_id})."}
    except Exception as exc:  # noqa: BLE001 - convert all network/protocol errors to tool payload
        log.error("save_knowledge failed — %s: %s", type(exc).__name__, exc)
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
    log.info(
        "retrieve_knowledge called — explicit_jira_ids=%s file_path=%r start_line=%s end_line=%s depth=%s",
        jira_ids,
        file_path,
        start_line,
        end_line,
        depth,
    )
    resolved_jira_ids = list(jira_ids or [])

    if not resolved_jira_ids and file_path:
        if start_line is None:
            log.warning("retrieve_knowledge rejected — file_path provided but start_line missing")
            return {"message": "start_line is required when file_path is provided"}
        actual_end_line = end_line if end_line is not None else start_line
        effective_depth = _resolve_depth(depth)
        log.debug("Code-range mode — file=%r lines=%d-%d effective_depth=%d", file_path, start_line, actual_end_line, effective_depth)

        if actual_end_line < start_line:
            log.warning("retrieve_knowledge rejected — end_line %d < start_line %d", actual_end_line, start_line)
            return {"message": "end_line must be >= start_line"}

        try:
            resolved_jira_ids = _extract_jira_ids_for_code(
                file_path=file_path,
                start_line=start_line,
                end_line=actual_end_line,
                depth=effective_depth,
                jira_regex=jira_regex,
            )
            log.info("Extracted %d JIRA IDs from git history: %s", len(resolved_jira_ids), resolved_jira_ids)
        except Exception as exc:  # noqa: BLE001
            log.error("JIRA ID extraction from git history failed — %s: %s", type(exc).__name__, exc)
            return _error_payload("retrieve_knowledge", exc)

    if not resolved_jira_ids:
        log.warning("retrieve_knowledge — no JIRA IDs available after resolution")
        return {"message": "No jira_ids provided or extracted from git history"}

    try:
        results = await _retrieve_context(resolved_jira_ids, depth)
        summary = _format_retrieval_summary(results).strip()
        if not summary:
            log.info("retrieve_knowledge — retrieval succeeded but no entries found for %s", resolved_jira_ids)
            summary = "No architectural knowledge entries found for the provided JIRA IDs."
        else:
            log.info("retrieve_knowledge succeeded — summary length=%d chars", len(summary))
        return {
            "message": summary,
        }
    except Exception as exc:  # noqa: BLE001 - convert all network/protocol errors to tool payload
        log.error("retrieve_knowledge failed during context fetch — %s: %s", type(exc).__name__, exc)
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
    log.info("Starting fungus-knowledge-mcp server (transport=stdio) log_dir=%s", _LOG_DIR)
    mcp.run(transport="stdio")
    log.info("MCP server exited")


if __name__ == "__main__":
    main()