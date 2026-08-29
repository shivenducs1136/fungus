"""Service for CRUD operations on context entries indexed by JIRA IDs."""

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.domain_models import ContextEntry, EntryTicket
from app.core.exceptions import ContextNotFoundException, StorageException
from app.core.logging_config import get_logger

log = get_logger("fungus.knowledge_server.service.context")

class ContextService:
    """Service for CRUD operations on context entries indexed by JIRA IDs."""

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

    @staticmethod
    def generate_key(ticket_ids: list[str]) -> str:
        """Generate a normalized key from sorted, deduplicated ticket IDs."""
        return "".join(sorted(set(ticket_ids)))

    @classmethod
    def _to_dict(cls, entry: ContextEntry) -> dict:
        return {
            "entry_id": entry.id,
            "ticket_ids": [t.jira_id for t in entry.tickets],
            "content": entry.content,
            "metadata": entry.metadata_json,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        }

    @classmethod
    def create(cls, db: Session, ticket_ids: list[str], content: str, metadata: dict | None) -> dict:
        """Create a new context entry."""
        log.info("create called - ticket_count=%d content_length=%d", len(ticket_ids), len(content))
        normalized_ticket_ids = cls.normalize_ticket_ids(ticket_ids)
        key = cls.generate_key(normalized_ticket_ids)
        entry_id = str(uuid.uuid4())
        
        try:
            entry = ContextEntry(
                id=entry_id,
                group_key=key,
                content=content,
                metadata_json=metadata or {}
            )
            for jira_id in normalized_ticket_ids:
                entry.tickets.append(EntryTicket(entry_id=entry_id, jira_id=jira_id))
            db.add(entry)
            db.commit()
            log.info("create success - key=%s entry_id=%s", key, entry_id)
            return {"key": key, "entry_id": entry_id}
        except SQLAlchemyError as ex:
            db.rollback()
            log.error("create failed - %s", ex)
            raise StorageException("Storage operation failed.")

    @classmethod
    def list_keys(cls, db: Session) -> list[str]:
        """List all stored keys."""
        try:
            rows = db.query(ContextEntry.group_key).distinct().all()
            log.info("list_keys success - count=%d", len(rows))
            return [r[0] for r in rows]
        except SQLAlchemyError as ex:
            log.error("list_keys failed - %s", ex)
            raise StorageException("Storage operation failed.")

    @classmethod
    def get_all(cls, db: Session, key: str) -> list[dict]:
        """Get all entries for a key."""
        try:
            entries = db.query(ContextEntry).filter(ContextEntry.group_key == key).all()
            if not entries:
                log.warning("get_all not found - key=%s", key)
                raise ContextNotFoundException(f"Key '{key}' not found")
            log.info("get_all success - key=%s count=%d", key, len(entries))
            return [cls._to_dict(e) for e in entries]
        except SQLAlchemyError as ex:
            log.error("get_all failed - key=%s error=%s", key, ex)
            raise StorageException("Storage operation failed.")

    @classmethod
    def get_entry(cls, db: Session, key: str, entry_id: str) -> dict:
        """Get a single entry by key and entry_id."""
        try:
            entry = db.query(ContextEntry).filter(
                ContextEntry.group_key == key,
                ContextEntry.id == entry_id
            ).first()
            if not entry:
                log.warning("get_entry not found - key=%s entry_id=%s", key, entry_id)
                raise ContextNotFoundException(f"Entry '{entry_id}' not found in key '{key}'")
            log.info("get_entry success - key=%s entry_id=%s", key, entry_id)
            return cls._to_dict(entry)
        except SQLAlchemyError as ex:
            log.error("get_entry failed - key=%s entry_id=%s error=%s", key, entry_id, ex)
            raise StorageException("Storage operation failed.")

    @classmethod
    def get_by_jira(cls, db: Session, jira_id: str) -> list[dict]:
        """Get all entries containing the given JIRA ID."""
        try:
            normalized_jira_id = cls.normalize_ticket_id(jira_id)
            entries = (
                db.query(ContextEntry)
                .join(EntryTicket)
                .filter(EntryTicket.jira_id == normalized_jira_id)
                .all()
            )
            if not entries:
                log.warning("get_by_jira not found - jira_id=%s normalized=%s", jira_id, normalized_jira_id)
                raise ContextNotFoundException(f"JIRA ID '{jira_id}' not found")
            log.info("get_by_jira success - jira_id=%s count=%d", jira_id, len(entries))
            return [cls._to_dict(e) for e in entries]
        except SQLAlchemyError as ex:
            log.error("get_by_jira failed - jira_id=%s error=%s", jira_id, ex)
            raise StorageException("Storage operation failed.")

    @classmethod
    def get_recent_by_jira(cls, db: Session, jira_id: str, depth: int) -> list[dict]:
        """Get the most recent N entries containing the given JIRA ID."""
        try:
            normalized_jira_id = cls.normalize_ticket_id(jira_id)
            entries = (
                db.query(ContextEntry)
                .join(EntryTicket)
                .filter(EntryTicket.jira_id == normalized_jira_id)
                .order_by(ContextEntry.created_at.desc())
                .limit(depth)
                .all()
            )
            if not entries:
                log.warning("get_recent_by_jira not found - jira_id=%s normalized=%s", jira_id, normalized_jira_id)
                raise ContextNotFoundException(f"JIRA ID '{jira_id}' not found")
            log.info("get_recent_by_jira success - jira_id=%s depth=%d count=%d", jira_id, depth, len(entries))
            return [cls._to_dict(e) for e in entries]
        except SQLAlchemyError as ex:
            log.error("get_recent_by_jira failed - jira_id=%s depth=%d error=%s", jira_id, depth, ex)
            raise StorageException("Storage operation failed.")

    @classmethod
    def update(
        cls, db: Session, key: str, entry_id: str, content: str, metadata: dict | None
    ) -> dict:
        """Update an existing entry."""
        log.info("update called - key=%s entry_id=%s content_length=%d", key, entry_id, len(content))
        try:
            entry = db.query(ContextEntry).filter(
                ContextEntry.group_key == key,
                ContextEntry.id == entry_id
            ).first()
            
            if not entry:
                log.warning("update not found - key=%s entry_id=%s", key, entry_id)
                raise ContextNotFoundException(f"Entry '{entry_id}' not found in key '{key}'")
                
            entry.content = content
            entry.metadata_json = metadata or {}
            entry.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            db.refresh(entry)
            log.info("update success - key=%s entry_id=%s", key, entry_id)
            return cls._to_dict(entry)
        except SQLAlchemyError as ex:
            db.rollback()
            log.error("update failed - key=%s entry_id=%s error=%s", key, entry_id, ex)
            raise StorageException("Storage operation failed.")

    @classmethod
    def delete(cls, db: Session, key: str, entry_id: str) -> None:
        """Delete an entry. Ticket associations are cascade-deleted by the DB."""
        log.info("delete called - key=%s entry_id=%s", key, entry_id)
        try:
            entry = db.query(ContextEntry).filter(
                ContextEntry.group_key == key,
                ContextEntry.id == entry_id
            ).first()
            
            if not entry:
                log.warning("delete not found - key=%s entry_id=%s", key, entry_id)
                raise ContextNotFoundException(f"Entry '{entry_id}' not found in key '{key}'")
                
            db.delete(entry)
            db.commit()
            log.info("delete success - key=%s entry_id=%s", key, entry_id)
        except SQLAlchemyError as ex:
            db.rollback()
            log.error("delete failed - key=%s entry_id=%s error=%s", key, entry_id, ex)
            raise StorageException("Storage operation failed.")
