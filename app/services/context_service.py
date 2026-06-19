"""Service for CRUD operations on context entries indexed by JIRA IDs."""

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models.domain_models import ContextEntry, ContextJiraIndex
from app.core.exceptions import ContextNotFoundException, StorageException

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
            "ticket_ids": entry.ticket_ids,
            "content": entry.content,
            "metadata": entry.metadata_json,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        }

    @classmethod
    def create(cls, db: Session, ticket_ids: list[str], content: str, metadata: dict | None) -> dict:
        """Create a new context entry."""
        normalized_ticket_ids = cls.normalize_ticket_ids(ticket_ids)
        key = cls.generate_key(normalized_ticket_ids)
        entry_id = str(uuid.uuid4())
        
        try:
            entry = ContextEntry(
                id=entry_id,
                group_key=key,
                ticket_ids=normalized_ticket_ids,
                content=content,
                metadata_json=metadata or {}
            )
            db.add(entry)
            
            # Update JIRA index
            for ticket_id in normalized_ticket_ids:
                # Check if this index already exists
                existing_idx = db.query(ContextJiraIndex).filter(
                    ContextJiraIndex.jira_id == ticket_id,
                    ContextJiraIndex.group_key == key
                ).first()
                if not existing_idx:
                    idx = ContextJiraIndex(jira_id=ticket_id, group_key=key)
                    db.add(idx)
                    try:
                        db.flush()
                    except IntegrityError:
                        db.rollback()
                        # Duplicate key from race condition, ignore and continue
                        pass
                    
            db.commit()
            return {"key": key, "entry_id": entry_id}
        except SQLAlchemyError as ex:
            db.rollback()
            raise StorageException(f"Database error during create: {str(ex)}")

    @classmethod
    def list_keys(cls, db: Session) -> list[str]:
        """List all stored keys."""
        try:
            rows = db.query(ContextEntry.group_key).distinct().all()
            return [r[0] for r in rows]
        except SQLAlchemyError as ex:
            raise StorageException(f"Database error during list_keys: {str(ex)}")

    @classmethod
    def get_all(cls, db: Session, key: str) -> list[dict]:
        """Get all entries for a key."""
        try:
            entries = db.query(ContextEntry).filter(ContextEntry.group_key == key).all()
            if not entries:
                raise ContextNotFoundException(f"Key '{key}' not found")
            return [cls._to_dict(e) for e in entries]
        except SQLAlchemyError as ex:
            raise StorageException(f"Database error during get_all: {str(ex)}")

    @classmethod
    def get_entry(cls, db: Session, key: str, entry_id: str) -> dict:
        """Get a single entry by key and entry_id."""
        try:
            entry = db.query(ContextEntry).filter(
                ContextEntry.group_key == key,
                ContextEntry.id == entry_id
            ).first()
            if not entry:
                raise ContextNotFoundException(f"Entry '{entry_id}' not found in key '{key}'")
            return cls._to_dict(entry)
        except SQLAlchemyError as ex:
            raise StorageException(f"Database error during get_entry: {str(ex)}")

    @classmethod
    def get_by_jira(cls, db: Session, jira_id: str) -> list[dict]:
        """Get all entries containing the given JIRA ID."""
        try:
            normalized_jira_id = cls.normalize_ticket_id(jira_id)
            
            # Find all keys for this jira_id
            keys = db.query(ContextJiraIndex.group_key).filter(
                ContextJiraIndex.jira_id == normalized_jira_id
            ).all()
            
            if not keys:
                raise ContextNotFoundException(f"JIRA ID '{jira_id}' not found")
                
            key_list = [k[0] for k in keys]
            entries = db.query(ContextEntry).filter(ContextEntry.group_key.in_(key_list)).all()
            
            return [cls._to_dict(e) for e in entries]
        except SQLAlchemyError as ex:
            raise StorageException(f"Database error during get_by_jira: {str(ex)}")

    @classmethod
    def get_recent_by_jira(cls, db: Session, jira_id: str, depth: int) -> list[dict]:
        """Get the most recent N entries containing the given JIRA ID."""
        try:
            normalized_jira_id = cls.normalize_ticket_id(jira_id)
            
            keys = db.query(ContextJiraIndex.group_key).filter(
                ContextJiraIndex.jira_id == normalized_jira_id
            ).all()
            
            if not keys:
                raise ContextNotFoundException(f"JIRA ID '{jira_id}' not found")
                
            key_list = [k[0] for k in keys]
            entries = db.query(ContextEntry).filter(
                ContextEntry.group_key.in_(key_list)
            ).order_by(ContextEntry.created_at.desc()).limit(depth).all()
            
            return [cls._to_dict(e) for e in entries]
        except SQLAlchemyError as ex:
            raise StorageException(f"Database error during get_recent_by_jira: {str(ex)}")

    @classmethod
    def update(
        cls, db: Session, key: str, entry_id: str, content: str, metadata: dict | None
    ) -> dict:
        """Update an existing entry."""
        try:
            entry = db.query(ContextEntry).filter(
                ContextEntry.group_key == key,
                ContextEntry.id == entry_id
            ).first()
            
            if not entry:
                raise ContextNotFoundException(f"Entry '{entry_id}' not found in key '{key}'")
                
            entry.content = content
            entry.metadata_json = metadata or {}
            entry.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            db.refresh(entry)
            return cls._to_dict(entry)
        except SQLAlchemyError as ex:
            db.rollback()
            raise StorageException(f"Database error during update: {str(ex)}")

    @classmethod
    def delete(cls, db: Session, key: str, entry_id: str) -> None:
        """Delete an entry. Removes the key if empty."""
        try:
            entry = db.query(ContextEntry).filter(
                ContextEntry.group_key == key,
                ContextEntry.id == entry_id
            ).first()
            
            if not entry:
                raise ContextNotFoundException(f"Entry '{entry_id}' not found in key '{key}'")
                
            db.delete(entry)
            db.flush()
            
            # Check if the key bucket is now empty
            remaining = db.query(ContextEntry).filter(ContextEntry.group_key == key).count()
            if remaining == 0:
                # Remove JIRA index references for this key
                db.query(ContextJiraIndex).filter(ContextJiraIndex.group_key == key).delete()
            db.commit()
        except SQLAlchemyError as ex:
            db.rollback()
            raise StorageException(f"Database error during delete: {str(ex)}")
