"""Service for creating and retrieving demo bookings."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import StorageException
from app.core.logging_config import get_logger
from app.models.domain_models import DemoBooking
from app.services.email_service import EmailService

log = get_logger("fungus.knowledge_server.service.demo_booking")


class DemoBookingService:
    """Service layer for demo booking operations."""

    @staticmethod
    def _to_utc_iso(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

    @staticmethod
    def _to_dict(booking: DemoBooking, email_status: str) -> dict:
        return {
            "status": "created",
            "booking_id": booking.id,
            "name": booking.name,
            "work_email": booking.work_email,
            "time": booking.preferred_time,
            "contact_number": booking.contact_number,
            "short_note": booking.short_note,
            "submitted_datetime": DemoBookingService._to_utc_iso(booking.submitted_at),
            "scheduled_datetime": DemoBookingService._to_utc_iso(booking.scheduled_at),
            "email_status": email_status,
        }

    @classmethod
    def create(
        cls,
        db: Session,
        name: str,
        work_email: str,
        preferred_time: str,
        contact_number: str,
        short_note: str | None,
        scheduled_datetime,
    ) -> dict:
        """Create a demo booking record and trigger automated email notification."""
        booking = DemoBooking(
            id=str(uuid.uuid4()),
            name=name,
            work_email=work_email,
            preferred_time=preferred_time,
            contact_number=contact_number,
            short_note=short_note,
            submitted_at=datetime.now(timezone.utc),
            scheduled_at=scheduled_datetime,
        )

        try:
            db.add(booking)
            db.commit()
            db.refresh(booking)
            email_status = EmailService.send_demo_booking_confirmation(
                recipient_email=booking.work_email,
                recipient_name=booking.name,
                scheduled_datetime=cls._to_utc_iso(booking.scheduled_at),
                preferred_time=booking.preferred_time,
                contact_number=booking.contact_number,
                short_note=booking.short_note,
            )
            log.info("Demo booking created - booking_id=%s email_status=%s", booking.id, email_status)
            return cls._to_dict(booking, email_status)
        except SQLAlchemyError as ex:
            db.rollback()
            log.error("Demo booking create failed - error=%s", ex)
            raise StorageException("Storage operation failed.")
