
import os
import json
import base64
import logging
import urllib.request
import urllib.error

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv(
    "EMAIL_FROM",
    "FleetSet <onboarding@resend.dev>",
)

RESEND_API_URL = "https://api.resend.com/emails"
REQUEST_TIMEOUT = 30


def _send_email(
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: str | Path | None = None,
):
    if not RESEND_API_KEY:
        return {
            "success": False,
            "message": "RESEND_API_KEY is not configured",
        }

    if not EMAIL_FROM:
        return {
            "success": False,
            "message": "EMAIL_FROM is not configured",
        }

    if not recipient_email:
        return {
            "success": False,
            "message": "Recipient email is required",
        }

    payload = {
        "from": EMAIL_FROM,
        "to": [recipient_email],
        "subject": subject,
        "text": body,
    }

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

        payload["attachments"] = [
            {
                "filename": path.name,
                "content": base64.b64encode(pdf_data).decode("ascii"),
            }
        ]

    request = urllib.request.Request(
        RESEND_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
        ) as response:
            response_body = response.read().decode("utf-8")
            result = json.loads(response_body)

        return {
            "success": True,
            "message": "Email accepted by Resend",
            "email_id": result.get("id"),
        }

    except urllib.error.HTTPError as exc:
        try:
            error_body = exc.read().decode(
                "utf-8",
                errors="replace",
            )
        except Exception:
            error_body = ""

        logger.error(
            "Resend API error HTTP %s: %s",
            exc.code,
            error_body[:1000],
        )

        return {
            "success": False,
            "message": (
                f"Resend rejected the email request (HTTP {exc.code}). "
                "Check the backend logs and Resend configuration."
            ),
        }

    except (urllib.error.URLError, TimeoutError, OSError):
        logger.exception("Could not connect to Resend")
        return {
            "success": False,
            "message": (
                "Unable to connect to the email provider. "
                "Please try again later."
            ),
        }

    except (ValueError, TypeError):
        logger.exception("Invalid response from Resend")
        return {
            "success": False,
            "message": "Invalid response received from the email provider",
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
