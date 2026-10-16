
import os
import smtplib
import logging

from pathlib import Path
from email.message import EmailMessage
from email.utils import formataddr
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================
# SMTP CONFIGURATION
# ============================================================

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "FleetSet")


logger.info(
    "SMTP configuration status: host=%s, port=%s, "
    "email_set=%s, app_password_set=%s",
    SMTP_HOST,
    SMTP_PORT,
    bool(SMTP_EMAIL),
    bool(SMTP_APP_PASSWORD),
)


# ============================================================
# COMMON EMAIL SENDER
# ============================================================

def _send_email(
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: str | Path | None = None,
):
    # --------------------------------------------------------
    # Validate configuration
    # --------------------------------------------------------

    if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
        logger.error(
            "SMTP configuration is incomplete: "
            "email_set=%s, app_password_set=%s",
            bool(SMTP_EMAIL),
            bool(SMTP_APP_PASSWORD),
        )

        return {
            "success": False,
            "message": (
                "SMTP_EMAIL or SMTP_APP_PASSWORD "
                "is not configured"
            ),
        }

    if not recipient_email or not recipient_email.strip():
        return {
            "success": False,
            "message": "Recipient email is required",
        }

    # --------------------------------------------------------
    # Build email
    # --------------------------------------------------------

    message = EmailMessage()
    message["From"] = formataddr(
        (EMAIL_FROM_NAME, SMTP_EMAIL)
    )
    message["To"] = recipient_email.strip()
    message["Subject"] = subject
    message.set_content(body)

    # --------------------------------------------------------
    # Attach PDF if provided
    # --------------------------------------------------------

    if attachment_path is not None:
        path = Path(attachment_path)

        if not path.is_file():
            logger.error(
                "Email attachment does not exist: %s",
                path.name,
            )

            return {
                "success": False,
                "message": "Report PDF file not found",
            }

        try:
            pdf_data = path.read_bytes()

            message.add_attachment(
                pdf_data,
                maintype="application",
                subtype="pdf",
                filename=path.name,
            )

        except OSError:
            logger.exception(
                "Unable to read email attachment"
            )

            return {
                "success": False,
                "message": (
                    "Unable to read the report PDF file"
                ),
            }

    # --------------------------------------------------------
    # Send email through SMTP
    # --------------------------------------------------------

    try:
        logger.info(
            "Starting SMTP delivery: host=%s, port=%s, "
            "recipient=%s, attachment=%s",
            SMTP_HOST,
            SMTP_PORT,
            recipient_email.strip(),
            attachment_path is not None,
        )

        with smtplib.SMTP_SSL(
            SMTP_HOST,
            SMTP_PORT,
            timeout=30,
        ) as server:

            logger.info(
                "SMTP SSL connection established"
            )

            server.login(
                SMTP_EMAIL,
                SMTP_APP_PASSWORD,
            )

            logger.info(
                "SMTP authentication succeeded"
            )

            server.send_message(message)

        logger.info(
            "Email delivered successfully to %s",
            recipient_email.strip(),
        )

        return {
            "success": True,
            "message": "Email sent successfully",
        }

    # --------------------------------------------------------
    # Authentication errors
    # --------------------------------------------------------

    except smtplib.SMTPAuthenticationError:
        logger.exception(
            "Gmail SMTP authentication failed"
        )

        return {
            "success": False,
            "message": (
                "Gmail SMTP authentication failed. "
                "Check the email and app password."
            ),
        }

    # --------------------------------------------------------
    # SMTP protocol errors
    # --------------------------------------------------------

    except smtplib.SMTPException as exc:
        logger.exception(
            "SMTP protocol error: type=%s error=%s",
            type(exc).__name__,
            str(exc),
        )

        return {
            "success": False,
            "message": (
                "SMTP email delivery failed. "
                "Check the Render logs for details."
            ),
        }

    # --------------------------------------------------------
    # Connection, network and timeout errors
    # --------------------------------------------------------

    except (OSError, TimeoutError) as exc:
        logger.exception(
            "SMTP connection/network error: "
            "type=%s error=%s",
            type(exc).__name__,
            str(exc),
        )

        return {
            "success": False,
            "message": (
                "Unable to connect to the SMTP server. "
                "Check the Render logs for details."
            ),
        }

    # --------------------------------------------------------
    # Unexpected errors
    # --------------------------------------------------------

    except Exception as exc:
        logger.exception(
            "Unexpected email delivery error: "
            "type=%s error=%s",
            type(exc).__name__,
            str(exc),
        )

        return {
            "success": False,
            "message": (
                "Unexpected error while sending email. "
                "Check the Render logs for details."
            ),
        }


# ============================================================
# SEND REPORT EMAIL
# ============================================================

def send_report_email(
    recipient_email: str,
    pdf_path: str | Path,
    subject: str,
    body: str,
):
    path = Path(pdf_path)

    if not path.is_file():
        logger.error(
            "Report PDF does not exist: %s",
            path.name,
        )

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


# ============================================================
# SEND PASSWORD RESET EMAIL
# ============================================================

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
        "Open this link to reset your password:\n"
        f"{reset_url}\n\n"
        "This link expires in 30 minutes and can only be used once.\n"
        "If you did not request this, you can ignore this email."
    )

    return _send_email(
        recipient_email=recipient_email,
        subject="Reset your FleetSet password",
        body=body,
    )
