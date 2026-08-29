"""Context API endpoints for CRUD operations on architectural decisions."""

from datetime import datetime, timezone
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from app.models.request_models import StoreContextRequest, UpdateContextRequest
from app.models.response_models import (
    CreateContextResponse,
    ListKeysResponse,
    ContextEntryResponse,
    UpdateContextResponse,
    DeleteContextResponse,
)
from app.services.context_service import ContextService
from app.core.database import get_db
from app.core.auth import require_api_key
from app.core.logging_config import get_logger

log = get_logger("fungus.knowledge_server.api.context")

router = APIRouter(
    prefix="/api/v1/context",
    tags=["Context"],
    dependencies=[Depends(require_api_key)],
    responses={404: {"description": "Entry not found"}, 500: {"description": "Storage error"}},
)


# CREATE
@router.post("/", status_code=201, response_model=CreateContextResponse)
def create_context(request: StoreContextRequest, db: Session = Depends(get_db)):
    """Create a new context entry. Key is derived from sorted, concatenated JIRA IDs."""
    log.info("POST /context - ticket_count=%d content_length=%d", len(request.ticket_ids), len(request.content))
    result = ContextService.create(
        db, request.ticket_ids, request.content, request.metadata
    )
    return {
        "status": "created",
        "key": result["key"],
        "entry_id": result["entry_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# LIST all keys
@router.get("/", response_model=ListKeysResponse)
def list_keys(db: Session = Depends(get_db)):
    """List all JIRA-ID keys currently stored."""
    log.info("GET /context - list keys")
    return {"keys": ContextService.list_keys(db)}


# SEARCH by a single JIRA ID (must be defined before /{key} to avoid conflicts)
@router.get("/jira/{jira_id}", response_model=list[ContextEntryResponse])
def search_by_jira(jira_id: str, db: Session = Depends(get_db)):
    """Return all entries that contain this JIRA ID (works for concatenated keys too)."""
    log.info("GET /context/jira/%s", jira_id)
    return ContextService.get_by_jira(db, jira_id)


@router.get("/jira/{jira_id}/recent", response_model=list[ContextEntryResponse])
def get_recent_by_jira(jira_id: str, depth: int = Query(..., ge=1), db: Session = Depends(get_db)):
    """Return the most recent depth number of entries for a JIRA ID."""
    log.info("GET /context/jira/%s/recent depth=%d", jira_id, depth)
    return ContextService.get_recent_by_jira(db, jira_id, depth)


# READ all entries under a key
@router.get("/{key}", response_model=list[ContextEntryResponse])
def get_entries(key: str, db: Session = Depends(get_db)):
    """Get all entries stored under a specific key (e.g. TPR-123 or TPR-123_TPR-456)."""
    log.info("GET /context/%s", key)
    return ContextService.get_all(db, key)


# READ a single entry
@router.get("/{key}/{entry_id}", response_model=ContextEntryResponse)
def get_entry(key: str, entry_id: str, db: Session = Depends(get_db)):
    """Get a specific entry by key and entry_id."""
    log.info("GET /context/%s/%s", key, entry_id)
    return ContextService.get_entry(db, key, entry_id)


# UPDATE
@router.put("/{key}/{entry_id}", response_model=UpdateContextResponse)
def update_entry(key: str, entry_id: str, request: UpdateContextRequest, db: Session = Depends(get_db)):
    """Update the content and/or metadata of an existing entry."""
    log.info("PUT /context/%s/%s content_length=%d", key, entry_id, len(request.content))
    return ContextService.update(db, key, entry_id, request.content, request.metadata)


# DELETE
@router.delete("/{key}/{entry_id}", status_code=200, response_model=DeleteContextResponse)
def delete_entry(key: str, entry_id: str, db: Session = Depends(get_db)):
    """Delete a specific entry. If the key bucket becomes empty it is also removed."""
    log.info("DELETE /context/%s/%s", key, entry_id)
    ContextService.delete(db, key, entry_id)
    return {"status": "deleted", "key": key, "entry_id": entry_id}
