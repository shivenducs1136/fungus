"""Request models for context operations."""

import re

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class StoreContextRequest(BaseModel):
    """Request to create a new context entry."""

    ticket_ids: List[str] = Field(
        min_length=1,
        description="One or more JIRA IDs (e.g., ['PROJ-1', 'PROJ-2'])."
    )
    content: str = Field(
        min_length=1,
        max_length=50000,
        description="Context content (architectural reasoning, decisions, etc.)."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata (author, source, tags, etc.)."
    )

    @field_validator("ticket_ids")
    @classmethod
    def validate_ticket_ids(cls, ticket_ids: List[str]) -> List[str]:
        """Clean and validate ticket IDs."""
        cleaned = []
        for ticket in ticket_ids:
            ticket = ticket.strip()
            if not ticket:
                raise ValueError("JIRA ID cannot be blank")

            # Expand strings like "[ERP-24] [ERP-25]" into separate ticket IDs.
            has_bracket_syntax = "[" in ticket or "]" in ticket
            if has_bracket_syntax:
                bracket_groups = re.findall(r"\[[^\[\]]+\]", ticket)
                compact = re.sub(r"\s+", "", ticket)
                if not bracket_groups or "".join(bracket_groups) != compact:
                    raise ValueError("Invalid bracketed JIRA ID format")
                cleaned.extend(bracket_groups)
            else:
                cleaned.append(ticket)
        return cleaned

    @field_validator("content")
    @classmethod
    def validate_content(cls, content: str) -> str:
        """Validate content."""
        if not content.strip():
            raise ValueError("Content cannot be blank")
        return content


class UpdateContextRequest(BaseModel):
    """Request to update an existing context entry."""

    content: str = Field(
        min_length=1,
        max_length=50000,
        description="Updated content."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated metadata."
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, content: str) -> str:
        """Validate content."""
        if not content.strip():
            raise ValueError("Content cannot be blank")
        return content