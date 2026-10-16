
import os
import json
import base64
import logging
import urllib.request
import urllib.error

from pathlib import Path
from email.utils import formataddr
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================
# RESEND HTTPS API CONFIGURATION
# ============================================================

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv(
    "RESEND_FROM_EMAIL",
    "onboarding@resend.dev",
)
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "FleetSet")

logger.info(
    "Resend configuration status: api_key_set=%s, sender_set=%s",
    bool(RESEND_API_KEY),
    bool(RESEND_FROM_EMAIL),
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
    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY is not configured")
        return {
            "success": False,
            "message": "Email service is not configured.",
        }

    if not RESEND_FROM_EMAIL:
        logger.error("RESEND_FROM_EMAIL is not configured")
        return {
            "success": False,
            "message": "Email sender is not configured.",
        }

    if not recipient_email or not recipient_email.strip():
        return {
            "success": False,
            "message": "Recipient email is required.",
        }

    recipient_email = recipient_email.strip()

    # --------------------------------------------------------
    # Build the Resend API payload
    # --------------------------------------------------------

    payload = {
        "from": formataddr((EMAIL_FROM_NAME, RESEND_FROM_EMAIL)),
        "to": [recipient_email],
        "subject": subject,
        "text": body,
    }

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
                "message": "Report PDF file not found.",
            }

        try:
            pdf_data = path.read_bytes()

            payload["attachments"] = [
                {
                    "filename": path.name,
                    "content": base64.b64encode(
                        pdf_data
                    ).decode("ascii"),
                }
            ]

        except OSError:
            logger.exception("Unable to read email attachment")
            return {
                "success": False,
                "message": "Unable to read the report PDF file.",
            }

    # --------------------------------------------------------
    # Send through Resend HTTPS API
    # --------------------------------------------------------

    request_body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        RESEND_API_URL,
        data=request_body,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        logger.info(
            "Sending email through Resend: recipient=%s, attachment=%s",
            recipient_email,
            attachment_path is not None,
        )

        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:
            response_body = response.read().decode("utf-8")
            result = json.loads(response_body) if response_body else {}

        email_id = result.get("id")

        logger.info(
            "Resend accepted email: email_id=%s, recipient=%s",
            email_id,
            recipient_email,
        )

        return {
            "success": True,
            "message": "Email accepted for delivery.",
        }

    
    except urllib.error.HTTPError as exc:
        error_body = ""

        try:
            error_body = exc.read().decode("utf-8")
            error_data = json.loads(error_body) if error_body else {}
        except (ValueError, OSError):
            error_data = {}

        # Log the provider's response, never the API key.
        error_message = (
            error_data.get("message")
            or error_data.get("error")
            or error_data.get("name")
            or error_body[:1000]
            or "No error details returned"
        )

        logger.error(
            "Resend API rejected email: status=%s, response=%s",
            exc.code,
            str(error_message)[:1000],
        )

        if exc.code == 401:
            return {
                "success": False,
                "message": (
                    "Resend rejected the API key. "
                    "Verify that the key is valid and active."
                ),
            }

        if exc.code == 403:
            return {
                "success": False,
                "message": (
                    "Resend denied the email request (HTTP 403). "
                    "Check API permissions and account restrictions. "
                    "See the Render logs for details."
                ),
            }

        if exc.code == 422:
            return {
                "success": False,
                "message": (
                    "Resend rejected the email request. "
                    "Check the sender, recipient, and request details."
                ),
            }

        return {
            "success": False,
            "message": (
                f"Email provider returned HTTP {exc.code}. "
                "Check the Render logs for details."
            ),
        }

    except urllib.error.URLError as exc:
        logger.error(
            "Resend network error: %s",
            str(exc.reason),
        )
        return {
            "success": False,
            "message": (
                "Unable to connect to the email provider. "
                "Check the Render logs."
            ),
        }

    except TimeoutError:
        logger.exception("Resend request timed out")
        return {
            "success": False,
            "message": "Email provider request timed out.",
        }

    except (OSError, ValueError) as exc:
        logger.exception(
            "Email delivery error: type=%s",
            type(exc).__name__,
        )
        return {
            "success": False,
            "message": (
                "Unexpected email delivery error. "
                "Check the Render logs."
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
            "message": "Report PDF file not found.",
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
            "message": "Password reset URL is required.",
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
