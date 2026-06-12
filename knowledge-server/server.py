"""
Deep Knowledge Context Tracker - Backend API Server
Runs on port 8000. Uses tally_ai_store.json as a local NoSQL document store.
"""

import hashlib
import json
import os
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="Deep Knowledge Context Tracker", version="1.0.0")

STORE_FILE = os.path.join(os.path.dirname(__file__), "tally_ai_store.json")


def load_store() -> dict:
    """Load the JSON store from disk. Returns empty dict if file doesn't exist."""
    if not os.path.exists(STORE_FILE):
        return {}
    with open(STORE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_store(store: dict) -> None:
    """Persist the JSON store to disk."""
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)


def generate_hash(payload: dict, timestamp: str) -> str:
    """
    Generate a deterministic ctx-hash from the payload + timestamp.
    Returns 'ctx-' followed by the first 12 hex characters of SHA-256.
    """
    raw = json.dumps(payload, sort_keys=True) + timestamp
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"ctx-{digest[:12]}"


@app.post("/api/v1/knowledge", status_code=201)
def store_knowledge(payload: dict):
    """
    Accept a JSON payload, generate a ctx-hash, persist the document,
    and return the hash.

    Expected payload shape:
    {
        "tickets": {
            "TPR-XXXXX": {
                "focus": "...",
                "discovered_constraints": [...],
                "discarded_approaches": [...],
                "final_solution": "..."
            }
        }
    }
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Build the full document that will be stored
    document = {
        "timestamp": timestamp,
        **payload,
    }

    ctx_hash = generate_hash(payload, timestamp)

    store = load_store()
    store[ctx_hash] = document
    save_store(store)

    return {"hash": ctx_hash}


@app.get("/api/v1/knowledge/{ctx_hash}")
def retrieve_knowledge(ctx_hash: str):
    """
    O(1) lookup: retrieve the document associated with the given ctx-hash.
    """
    store = load_store()
    document = store.get(ctx_hash)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"No knowledge document found for hash '{ctx_hash}'.",
        )
    return JSONResponse(content=document)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)