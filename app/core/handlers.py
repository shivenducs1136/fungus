"""Exception handlers for context operations."""

from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import ContextNotFoundException, StorageException


async def context_not_found_handler(request: Request, exc: ContextNotFoundException) -> JSONResponse:
    """Handle ContextNotFoundException with 404 response."""
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
    return JSONResponse(
        status_code=500,
        content={
            "error": "STORAGE_ERROR",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )