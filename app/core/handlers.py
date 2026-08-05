"""Exception handlers for context operations."""

from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import ContextNotFoundException, StorageException
from app.core.logging_config import get_logger

log = get_logger("fungus.knowledge_server.handlers")


async def context_not_found_handler(request: Request, exc: ContextNotFoundException) -> JSONResponse:
    """Handle ContextNotFoundException with 404 response."""
    log.warning("Context not found - path=%s method=%s detail=%s", request.url.path, request.method, exc)
    return JSONResponse(
        status_code=404,
        content={
            "error": "CONTEXT_NOT_FOUND",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def storage_error_handler(request: Request, exc: StorageException) -> JSONResponse:
    """Handle StorageException with 500 response."""
    log.error("Storage exception - path=%s method=%s detail=%s", request.url.path, request.method, exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "STORAGE_ERROR",
            "message": "Storage operation failed.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )