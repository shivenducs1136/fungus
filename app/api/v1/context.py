"""Context API endpoints for CRUD operations on architectural decisions."""

from datetime import datetime, timezone
from fastapi import APIRouter, Query

from app.models.request_models import StoreContextRequest, UpdateContextRequest
from app.models.response_models import (
    CreateContextResponse,
    ListKeysResponse,
    ContextEntryResponse,
    UpdateContextResponse,
    DeleteContextResponse,
)
from app.services.context_service import ContextService

router = APIRouter(
    prefix="/api/v1/context",
    tags=["Context"],
    responses={404: {"description": "Entry not found"}, 500: {"description": "Storage error"}},
)


# CREATE
@router.post("/", status_code=201, response_model=CreateContextResponse)
def create_context(request: StoreContextRequest):
    """Create a new context entry. Key is derived from sorted, concatenated JIRA IDs."""
    result = ContextService.create(
        request.ticket_ids, request.content, request.metadata
    )
    return {
        "status": "created",
        "key": result["key"],
        "entry_id": result["entry_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# LIST all keys
@router.get("/", response_model=ListKeysResponse)
def list_keys():
    """List all JIRA-ID keys currently stored."""
    return {"keys": ContextService.list_keys()}


# SEARCH by a single JIRA ID (must be defined before /{key} to avoid conflicts)
@router.get("/jira/{jira_id}", response_model=list[ContextEntryResponse])
def search_by_jira(jira_id: str):
    """Return all entries that contain this JIRA ID (works for concatenated keys too)."""
    return ContextService.get_by_jira(jira_id)


@router.get("/jira/{jira_id}/recent", response_model=list[ContextEntryResponse])
def get_recent_by_jira(jira_id: str, depth: int = Query(..., ge=1)):
    """Return the most recent depth number of entries for a JIRA ID."""
    # depth is validated by FastAPI/Pydantic (must be >= 1).
    return ContextService.get_recent_by_jira(jira_id, depth)


# READ all entries under a key
@router.get("/{key}", response_model=list[ContextEntryResponse])
def get_entries(key: str):
    """Get all entries stored under a specific key (e.g. TPR-123 or TPR-123_TPR-456)."""
    return ContextService.get_all(key)


# READ a single entry
@router.get("/{key}/{entry_id}", response_model=ContextEntryResponse)
def get_entry(key: str, entry_id: str):
    """Get a specific entry by key and entry_id."""
    return ContextService.get_entry(key, entry_id)


# UPDATE
@router.put("/{key}/{entry_id}", response_model=UpdateContextResponse)
def update_entry(key: str, entry_id: str, request: UpdateContextRequest):
    """Update the content and/or metadata of an existing entry."""
    return ContextService.update(key, entry_id, request.content, request.metadata)


# DELETE
@router.delete("/{key}/{entry_id}", status_code=200, response_model=DeleteContextResponse)
def delete_entry(key: str, entry_id: str):
    """Delete a specific entry. If the key bucket becomes empty it is also removed."""
    ContextService.delete(key, entry_id)
    return {"status": "deleted", "key": key, "entry_id": entry_id}
