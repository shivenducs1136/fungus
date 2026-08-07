from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, UniqueConstraint
from app.core.database import Base
from datetime import datetime, timezone

class ContextEntry(Base):
    __tablename__ = "context_entries"

    id = Column(String, primary_key=True, index=True)
    group_key = Column(String, index=True, nullable=False)
    ticket_ids = Column(JSON, nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True)

class ContextJiraIndex(Base):
    __tablename__ = "context_jira_index"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jira_id = Column(String, index=True, nullable=False)
    group_key = Column(String, index=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('jira_id', 'group_key', name='uq_jira_group_key'),
    )


class DemoBooking(Base):
    __tablename__ = "demo_bookings"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    work_email = Column(String, nullable=False, index=True)
    preferred_time = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    short_note = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    scheduled_at = Column(DateTime, nullable=False)
