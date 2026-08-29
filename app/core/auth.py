"""API key authentication dependency."""

import os
import secrets
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
_API_KEY = os.getenv("FUNGUS_API_KEY", "")


def require_api_key(api_key: str | None = Security(_API_KEY_HEADER)) -> None:
    """Reject requests that do not supply the correct API key header."""
    if not _API_KEY:
        # Warn loudly at startup; skip enforcement only in explicit dev mode
        if os.getenv("FUNGUS_AUTH_DISABLED", "").lower() == "true":
            return
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: FUNGUS_API_KEY is not set.",
        )
    if not api_key or not secrets.compare_digest(api_key, _API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
