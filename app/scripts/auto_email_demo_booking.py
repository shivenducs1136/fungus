"""Manual runner for demo booking confirmation email automation.

Usage:
python -m app.scripts.auto_email_demo_booking \
  --email someone@company.com \
  --name "Jane Doe" \
  --scheduled-datetime "2026-08-15T10:30:00+00:00" \
  --time "10:30 AM UTC" \
  --contact-number "+15551234567" \
  --short-note "Interested in architecture walkthrough"
"""

import argparse

from app.services.email_service import EmailService


def main() -> None:
    parser = argparse.ArgumentParser(description="Send demo booking confirmation email")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--scheduled-datetime", required=True)
    parser.add_argument("--time", required=True)
    parser.add_argument("--contact-number", required=True)
    parser.add_argument("--short-note", required=False, default=None)
    args = parser.parse_args()

    status = EmailService.send_demo_booking_confirmation(
        recipient_email=args.email,
        recipient_name=args.name,
        scheduled_datetime=args.scheduled_datetime,
        preferred_time=args.time,
        contact_number=args.contact_number,
        short_note=args.short_note,
    )
    print({"email_status": status})


if __name__ == "__main__":
    main()
