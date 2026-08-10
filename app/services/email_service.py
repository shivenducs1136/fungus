"""Email automation utilities for outbound demo booking notifications."""

from email.message import EmailMessage
import base64
import os
import smtplib

from app.core.logging_config import get_logger

log = get_logger("fungus.knowledge_server.service.email")


class EmailService:
    """Sends transactional emails related to demo bookings."""

    ENV_DEMO_EMAIL_ENABLED = "DEMO_EMAIL_ENABLED"
    ENV_SMTP_HOST = "SMTP_HOST"
    ENV_SMTP_PORT = "SMTP_PORT"
    ENV_SMTP_USERNAME = "SMTP_USERNAME"
    ENV_SMTP_PASSWORD = "SMTP_PASSWORD"
    ENV_SMTP_PASSWORD_ENCRYPTED = "SMTP_PASSWORD_ENCRYPTED"
    ENV_SMTP_SENDER_EMAIL = "SMTP_SENDER_EMAIL"
    ENV_SMTP_USE_TLS = "SMTP_USE_TLS"
    ENV_SMTP_CREDENTIALS_KEY = "SMTP_CREDENTIALS_KEY"
    ENV_SMTP_CREDENTIALS_KEY_FILE = "SMTP_CREDENTIALS_KEY_FILE"

    DEFAULT_SMTP_KEY_FILE_PATH = "/run/secrets/smtp_credentials_key"

    @staticmethod
    def _decrypt_secret(ciphertext: str, key_value: str) -> str | None:
        try:
            from cryptography.fernet import Fernet  # Lazy import to avoid hard dependency at import time.

            key = key_value.strip().encode("utf-8")
            # Validate key format early to surface configuration errors.
            base64.urlsafe_b64decode(key)
            fernet = Fernet(key)
            plaintext = fernet.decrypt(ciphertext.strip().encode("utf-8"))
            return plaintext.decode("utf-8")
        except Exception as ex:
            log.error("Unable to decrypt SMTP_PASSWORD_ENCRYPTED: %s", ex)
            return None

    @staticmethod
    def _read_key_from_file(path: str) -> str | None:
        try:
            with open(path, "r", encoding="utf-8") as key_file:
                value = key_file.read().strip()
                return value or None
        except OSError as ex:
            log.warning("Unable to read SMTP credentials key file at %s: %s", path, ex)
            return None

    @classmethod
    def _resolve_credentials_key(cls) -> str | None:
        key_file_path = os.getenv(cls.ENV_SMTP_CREDENTIALS_KEY_FILE, cls.DEFAULT_SMTP_KEY_FILE_PATH).strip()
        if key_file_path:
            key_from_file = cls._read_key_from_file(key_file_path)
            if key_from_file:
                return key_from_file

        # Fallback for backward compatibility only.
        return os.getenv(cls.ENV_SMTP_CREDENTIALS_KEY)

    @classmethod
    def _resolve_smtp_password(cls) -> str | None:
        encrypted = os.getenv(cls.ENV_SMTP_PASSWORD_ENCRYPTED)
        if encrypted:
            key_value = cls._resolve_credentials_key()
            if not key_value:
                log.warning("SMTP_PASSWORD_ENCRYPTED is set but decryption key is unavailable")
                return None
            return cls._decrypt_secret(encrypted, key_value)

        return os.getenv(cls.ENV_SMTP_PASSWORD)

    @staticmethod
    def _is_enabled() -> bool:
        return os.getenv(EmailService.ENV_DEMO_EMAIL_ENABLED, "false").lower() in {"1", "true", "yes"}

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

        host = os.getenv(EmailService.ENV_SMTP_HOST)
        port = int(os.getenv(EmailService.ENV_SMTP_PORT, "587"))
        username = os.getenv(EmailService.ENV_SMTP_USERNAME)
        password = EmailService._resolve_smtp_password()
        sender = os.getenv(EmailService.ENV_SMTP_SENDER_EMAIL, username)

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
                if os.getenv(EmailService.ENV_SMTP_USE_TLS, "true").lower() in {"1", "true", "yes"}:
                    smtp.starttls()
                smtp.login(username, password)
                smtp.send_message(msg)
            log.info("Demo booking email sent - recipient=%s", recipient_email)
            return "sent"
        except Exception as ex:
            log.error("Failed to send demo booking email - recipient=%s error=%s", recipient_email, ex)
            return "skipped"
