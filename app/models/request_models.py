"""Request models for context operations."""

import re

from datetime import datetime, timezone
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


class DemoBookingRequest(BaseModel):
    """Request payload for booking a demo."""

    name: str = Field(min_length=1, max_length=120)
    work_email: str = Field(min_length=5, max_length=254)
    time: str = Field(min_length=1, max_length=80, description="Preferred time window")
    contact_number: str = Field(min_length=7, max_length=20, description="Must include country code")
    short_note: Optional[str] = Field(default=None, max_length=2000)
    scheduled_datetime: datetime

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Name cannot be blank")
        return value.strip()

    @field_validator("work_email")
    @classmethod
    def validate_work_email(cls, value: str) -> str:
        cleaned = value.strip()
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", cleaned):
            raise ValueError("Invalid work email address")
        return cleaned

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Time cannot be blank")
        return value.strip()

    @field_validator("contact_number")
    @classmethod
    def validate_contact_number(cls, value: str) -> str:
        cleaned = value.strip().replace(" ", "")
        if not re.match(r"^\+\d{6,15}$", cleaned):
            raise ValueError("Contact number must include country code (e.g. +15551234567)")
        return cleaned

    @field_validator("short_note")
    @classmethod
    def validate_short_note(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("scheduled_datetime")
    @classmethod
    def validate_scheduled_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value