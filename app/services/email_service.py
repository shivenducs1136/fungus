"""Email automation utilities for outbound demo booking notifications."""

from email.message import EmailMessage
import os
import smtplib

from app.core.logging_config import get_logger

log = get_logger("fungus.knowledge_server.service.email")


class EmailService:
    """Sends transactional emails related to demo bookings."""

    @staticmethod
    def _is_enabled() -> bool:
        return os.getenv("DEMO_EMAIL_ENABLED", "false").lower() in {"1", "true", "yes"}

    @staticmethod
    def send_demo_booking_confirmation(
        recipient_email: str,
        recipient_name: str,
        scheduled_datetime: str,
        preferred_time: str,
        contact_number: str,
        short_note: str | None,
    ) -> str:
        """Send a confirmation email to the requester when booking is created."""
        if not EmailService._is_enabled():
            log.info("Demo booking email disabled - recipient=%s", recipient_email)
            return "skipped"

        host = os.getenv("SMTP_HOST")
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        sender = os.getenv("SMTP_SENDER_EMAIL", username)

        if not host or not username or not password or not sender:
            log.warning("SMTP configuration missing; skipping demo booking email")
            return "skipped"

        msg = EmailMessage()
        msg["Subject"] = "Demo Booking Confirmation"
        msg["From"] = sender
        msg["To"] = recipient_email

        note_text = short_note if short_note else "N/A"
        msg.set_content(
            "Hello {name},\n\n"
            "Thank you for booking a demo with us.\n\n"
            "Scheduled Date Time: {scheduled_datetime}\n"
            "Preferred Time: {preferred_time}\n"
            "Contact Number: {contact_number}\n"
            "Short Note: {short_note}\n\n"
            "Our team will contact you soon.\n"
            "Regards,\nFungus Team".format(
                name=recipient_name,
                scheduled_datetime=scheduled_datetime,
                preferred_time=preferred_time,
                contact_number=contact_number,
                short_note=note_text,
            )
        )

        try:
            with smtplib.SMTP(host=host, port=port, timeout=15) as smtp:
                if os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}:
                    smtp.starttls()
                smtp.login(username, password)
                smtp.send_message(msg)
            log.info("Demo booking email sent - recipient=%s", recipient_email)
            return "sent"
        except Exception as ex:
            log.error("Failed to send demo booking email - recipient=%s error=%s", recipient_email, ex)
            return "skipped"
