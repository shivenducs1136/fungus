"""Response models for context operations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, RootModel
from datetime import datetime


class ContextEntryResponse(BaseModel):
    """A single context entry."""

    entry_id: str = Field(description="Unique entry identifier (UUID).")
    ticket_ids: List[str] = Field(description="Associated JIRA IDs.")
    content: str = Field(description="Entry content.")
    metadata: Dict[str, Any] = Field(description="Entry metadata.")
    created_at: str = Field(description="Creation timestamp (ISO 8601).")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp.")


class CreateContextResponse(BaseModel):
    """Response after creating a context entry."""

    status: str = Field(default="created", description="Operation status.")
    key: str = Field(description="Generated key from sorted JIRA IDs.")
    entry_id: str = Field(description="Entry identifier.")
    timestamp: str = Field(description="Response timestamp (ISO 8601).")


class ListKeysResponse(BaseModel):
    """Response with a list of all keys."""

    keys: List[str] = Field(description="List of all stored keys.")


class GetEntriesResponse(RootModel[List[ContextEntryResponse]]):
    """Response with a list of entries."""

    pass


class GetEntryResponse(ContextEntryResponse):
    """Response with a single entry."""

    pass


class UpdateContextResponse(ContextEntryResponse):
    """Response after updating a context entry."""

    pass


class DeleteContextResponse(BaseModel):
    """Response after deleting a context entry."""

    status: str = Field(default="deleted", description="Operation status.")
    key: str = Field(description="Key of the deleted entry.")
    entry_id: str = Field(description="ID of the deleted entry.")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(description="Error code (e.g., CONTEXT_NOT_FOUND).")
    message: str = Field(description="Error message.")
    timestamp: str = Field(description="Error timestamp (ISO 8601).")