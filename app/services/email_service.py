
import os
import smtplib
import logging

from pathlib import Path
from email.message import EmailMessage
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "FleetSet")


def _send_email(
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: str | Path | None = None,
):
    if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
        return {
            "success": False,
            "message": "SMTP_EMAIL or SMTP_APP_PASSWORD is not configured",
        }

    if not recipient_email:
        return {
            "success": False,
            "message": "Recipient email is required",
        }

    message = EmailMessage()
    message["From"] = formataddr((EMAIL_FROM_NAME, SMTP_EMAIL))
    message["To"] = recipient_email
    message["Subject"] = subject
    message.set_content(body)

    if attachment_path is not None:
        path = Path(attachment_path)

        if not path.is_file():
            return {
                "success": False,
                "message": "Report PDF file not found",
            }

        try:
            pdf_data = path.read_bytes()
        except OSError:
            logger.exception("Unable to read report PDF")
            return {
                "success": False,
                "message": "Unable to read the report PDF file",
            }

        message.add_attachment(
            pdf_data,
            maintype="application",
            subtype="pdf",
            filename=path.name,
        )

    try:
        with smtplib.SMTP_SSL(
            SMTP_HOST,
            SMTP_PORT,
            timeout=30,
        ) as server:
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.send_message(message)

        return {
            "success": True,
            "message": "Email sent successfully",
        }

    except smtplib.SMTPAuthenticationError:
        logger.exception("Gmail SMTP authentication failed")
        return {
            "success": False,
            "message": "Gmail SMTP authentication failed. Check the email and app password.",
        }

    except (smtplib.SMTPException, OSError, TimeoutError):
        logger.exception("SMTP email delivery failed")
        return {
            "success": False,
            "message": "Unable to send email through SMTP. Check the SMTP configuration and network access.",
        }

    except Exception:
        logger.exception("Unexpected email sending error")
        return {
            "success": False,
            "message": "Unexpected error while sending email",
        }


def send_report_email(
    recipient_email: str,
    pdf_path: str | Path,
    subject: str,
    body: str,
):
    path = Path(pdf_path)

    if not path.is_file():
        return {
            "success": False,
            "message": "Report PDF file not found",
        }

    return _send_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        attachment_path=path,
    )


def send_password_reset_email(
    recipient_email: str,
    reset_url: str,
):
    if not reset_url:
        return {
            "success": False,
            "message": "Password reset URL is required",
        }

    body = (
        "A request was made to reset your FleetSet password.\n\n"
        f"Open this link to reset your password:\n{reset_url}\n\n"
        "This link expires in 30 minutes and can only be used once.\n"
        "If you did not request this, you can ignore this email."
    )

    return _send_email(
        recipient_email=recipient_email,
        subject="Reset your FleetSet password",
        body=body,
    )
