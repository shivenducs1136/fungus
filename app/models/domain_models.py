from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime, timezone

class ContextEntry(Base):
    __tablename__ = "context_entries"

    id = Column(String, primary_key=True, index=True)
    group_key = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True)

    tickets = relationship("EntryTicket", back_populates="entry",
                           cascade="all, delete-orphan", lazy="joined")

class EntryTicket(Base):
    __tablename__ = "entry_tickets"

    entry_id = Column(String, ForeignKey("context_entries.id", ondelete="CASCADE"),
                      primary_key=True)
    jira_id = Column(String, primary_key=True, index=True)

    entry = relationship("ContextEntry", back_populates="tickets")


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
