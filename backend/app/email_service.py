import smtplib
from email.message import EmailMessage

from app.config import settings


def send_registration_confirmation_email(recipient_email: str, full_name: str, event_name: str, event_id: str) -> bool:
    """Send a registration confirmation email when a user confirms attendance.

    If SMTP configuration is missing, the method fails silently so registrations still work
    without blocking the event sign-up flow.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        return False

    subject = f"Registration confirmed for {event_name}"
    body = (
        f"Hello {full_name},\n\n"
        f"Your registration for {event_name} has been confirmed.\n"
        f"Event ID: {event_id}\n\n"
        "You can use your digital badge to access the event and check your status.\n\n"
        "Best regards,\n"
        "HACSA Axis Team"
    )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient_email
    message.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(message)

    return True
