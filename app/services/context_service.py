"""Service for CRUD operations on context entries indexed by JIRA IDs."""

import json
import uuid

from pathlib import Path
from datetime import datetime, timezone

from app.core.exceptions import ContextNotFoundException, StorageException


class ContextService:
    """Service for CRUD operations on context entries indexed by JIRA IDs."""

    STORE_FILE = Path(__file__).parent.parent / "storage" / "knowledge_store.json"
    JIRA_INDEX_FILE = Path(__file__).parent.parent / "storage" / "jira_index.json"

    @staticmethod
    def normalize_ticket_id(ticket_id: str) -> str:
        """Normalize a ticket ID into bracketed format, e.g. ERP-24 -> [ERP-24]."""
        cleaned = ticket_id.strip()
        if cleaned.startswith("[") and cleaned.endswith("]"):
            cleaned = cleaned[1:-1].strip()
        return f"[{cleaned}]"

    @classmethod
    def normalize_ticket_ids(cls, ticket_ids: list[str]) -> list[str]:
        """Normalize and deduplicate ticket IDs while preserving deterministic order."""
        normalized = [cls.normalize_ticket_id(ticket_id) for ticket_id in ticket_ids]
        return sorted(set(normalized))

    @classmethod
    def jira_id_variants(cls, jira_id: str) -> set[str]:
        """Return legacy and normalized Jira ID variants for backward-compatible lookup."""
        raw = jira_id.strip()
        variants = {raw}
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            if inner:
                variants.add(inner)
                variants.add(f"[{inner}]")
        else:
            variants.add(f"[{raw}]")
        return variants

    @staticmethod
    def generate_key(ticket_ids: list[str]) -> str:
        """Generate a normalized key from sorted, deduplicated ticket IDs."""
        return "".join(sorted(set(ticket_ids)))

    @classmethod
    def _read_json(cls, file_path: Path) -> dict:
        """Read and parse a JSON file, returning empty dict if not found."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as ex:
            raise StorageException(f"Failed reading {file_path.name}: {ex}")

    @classmethod
    def _write_json(cls, file_path: Path, data: dict) -> None:
        """Write data as JSON to a file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as ex:
            raise StorageException(f"Failed writing {file_path.name}: {ex}")

    @classmethod
    def _get_store(cls) -> dict:
        return cls._read_json(cls.STORE_FILE)

    @classmethod
    def _save_store(cls, store: dict) -> None:
        cls._write_json(cls.STORE_FILE, store)

    @classmethod
    def _get_jira_index(cls) -> dict:
        return cls._read_json(cls.JIRA_INDEX_FILE)

    @classmethod
    def _save_jira_index(cls, index: dict) -> None:
        cls._write_json(cls.JIRA_INDEX_FILE, index)

    @classmethod
    def create(cls, ticket_ids: list[str], content: str, metadata: dict | None) -> dict:
        """Create a new context entry."""
        normalized_ticket_ids = cls.normalize_ticket_ids(ticket_ids)
        store = cls._get_store()
        key = cls.generate_key(normalized_ticket_ids)
        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        entry = {
            "entry_id": entry_id,
            "ticket_ids": normalized_ticket_ids,
            "content": content,
            "metadata": metadata or {},
            "created_at": now,
        }

        store.setdefault(key, []).append(entry)
        cls._save_store(store)

        # Update JIRA index
        jira_index = cls._get_jira_index()
        for ticket_id in normalized_ticket_ids:
            jira_index.setdefault(ticket_id, []).append(key)
            # Keep one key reference per ticket to avoid duplicate reads later.
            jira_index[ticket_id] = list(
                set(jira_index[ticket_id])
            )  # Remove duplicates
        cls._save_jira_index(jira_index)

        return {"key": key, "entry_id": entry_id}

    @classmethod
    def list_keys(cls) -> list[str]:
        """List all stored keys."""
        return list(cls._get_store().keys())

    @classmethod
    def get_all(cls, key: str) -> list[dict]:
        """Get all entries for a key."""
        store = cls._get_store()
        if key not in store:
            raise ContextNotFoundException(f"Key '{key}' not found")
        return store[key]

    @classmethod
    def get_entry(cls, key: str, entry_id: str) -> dict:
        """Get a single entry by key and entry_id."""
        store = cls._get_store()
        if key not in store:
            raise ContextNotFoundException(f"Key '{key}' not found")
        for entry in store[key]:
            if entry["entry_id"] == entry_id:
                return entry
        raise ContextNotFoundException(f"Entry '{entry_id}' not found in key '{key}'")

    @classmethod
    def get_by_jira(cls, jira_id: str) -> list[dict]:
        """Get all entries containing the given JIRA ID."""
        jira_index = cls._get_jira_index()
        candidate_ids = cls.jira_id_variants(jira_id)
        matching_ids = [candidate_id for candidate_id in candidate_ids if candidate_id in jira_index]
        if not matching_ids:
            raise ContextNotFoundException(f"JIRA ID '{jira_id}' not found")

        store = cls._get_store()
        results = []
        visited_entry_ids = set()
        for matching_id in matching_ids:
            for key in jira_index[matching_id]:
                if key in store:
                    for entry in store[key]:
                        entry_id = entry.get("entry_id")
                        if entry_id not in visited_entry_ids:
                            results.append(entry)
                            visited_entry_ids.add(entry_id)
        return results

    @classmethod
    def get_recent_by_jira(cls, jira_id: str, depth: int) -> list[dict]:
        """Get the most recent N entries containing the given JIRA ID."""
        entries = cls.get_by_jira(jira_id)
        # created_at is stored as ISO 8601, so lexicographic sort is chronological.
        sorted_entries = sorted(
            entries,
            key=lambda entry: entry.get("created_at", ""),
            reverse=True,
        )
        return sorted_entries[:depth]

    @classmethod
    def update(
        cls, key: str, entry_id: str, content: str, metadata: dict | None
    ) -> dict:
        """Update an existing entry."""
        store = cls._get_store()
        if key not in store:
            raise ContextNotFoundException(f"Key '{key}' not found")

        for entry in store[key]:
            if entry["entry_id"] == entry_id:
                entry["content"] = content
                entry["metadata"] = metadata or {}
                entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                cls._save_store(store)
                return entry

        raise ContextNotFoundException(f"Entry '{entry_id}' not found in key '{key}'")

    @classmethod
    def delete(cls, key: str, entry_id: str) -> None:
        """Delete an entry. Removes the key if empty."""
        store = cls._get_store()
        if key not in store:
            raise ContextNotFoundException(f"Key '{key}' not found")

        deleted_entry = next((e for e in store[key] if e["entry_id"] == entry_id), None)
        if deleted_entry is None:
            raise ContextNotFoundException(
                f"Entry '{entry_id}' not found in key '{key}'"
            )

        store[key] = [e for e in store[key] if e["entry_id"] != entry_id]

        # If key bucket is empty, remove the key and clean up JIRA index
        if not store[key]:
            del store[key]
            jira_index = cls._get_jira_index()
            for ticket_id in deleted_entry["ticket_ids"]:
                if ticket_id in jira_index:
                    # Remove stale key references for this ticket after bucket deletion.
                    jira_index[ticket_id] = [
                        k for k in jira_index[ticket_id] if k != key
                    ]
                    if not jira_index[ticket_id]:
                        del jira_index[ticket_id]
            cls._save_jira_index(jira_index)

        cls._save_store(store)
