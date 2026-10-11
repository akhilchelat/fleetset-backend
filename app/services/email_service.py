import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "FleetSet")


def send_report_email(
    recipient_email: str,
    pdf_path: str | Path,
    subject: str,
    body: str,
):
    if not SMTP_USERNAME:
        return {
            "success": False,
            "message": "SMTP_USERNAME is not configured",
        }

    if not SMTP_PASSWORD:
        return {
            "success": False,
            "message": "SMTP_PASSWORD is not configured",
        }

    if not SMTP_FROM_EMAIL:
        return {
            "success": False,
            "message": "SMTP_FROM_EMAIL is not configured",
        }

    if not recipient_email:
        return {
            "success": False,
            "message": "Recipient email is required",
        }

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        return {
            "success": False,
            "message": "Report PDF file not found",
        }

    try:
        message = EmailMessage()

        message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        message["To"] = recipient_email
        message["Subject"] = subject

        message.set_content(body)

        with open(pdf_path, "rb") as pdf_file:
            pdf_data = pdf_file.read()

        message.add_attachment(
            pdf_data,
            maintype="application",
            subtype="pdf",
            filename=pdf_path.name,
        )

        with smtplib.SMTP_SSL(
            SMTP_HOST,
            SMTP_PORT,
            timeout=30,
        ) as smtp:
            smtp.login(
                SMTP_USERNAME,
                SMTP_PASSWORD,
            )

            smtp.send_message(message)

        return {
            "success": True,
            "message": "Report email sent successfully",
        }

    except smtplib.SMTPAuthenticationError as exc:
        smtp_error = exc.smtp_error

        if isinstance(smtp_error, bytes):
            smtp_error = smtp_error.decode(errors="ignore")

        return {
            "success": False,
            "message": (
                "Gmail authentication failed. "
                f"SMTP code: {exc.smtp_code}. "
                f"SMTP message: {smtp_error}"
            ),
        }

    except smtplib.SMTPException as exc:
        return {
            "success": False,
            "message": f"SMTP error: {str(exc)}",
        }

    except OSError as exc:
        return {
            "success": False,
            "message": f"Unable to access report PDF: {str(exc)}",
        }

    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to send report email: {str(exc)}",
        }


def send_password_reset_email(
    recipient_email: str,
    reset_url: str,
):
    if not SMTP_USERNAME or not SMTP_PASSWORD or not SMTP_FROM_EMAIL:
        return {
            "success": False,
            "message": "SMTP email configuration is incomplete",
        }

    if not recipient_email or not reset_url:
        return {
            "success": False,
            "message": "Recipient email and reset URL are required",
        }

    try:
        message = EmailMessage()
        message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        message["To"] = recipient_email
        message["Subject"] = "Reset your FleetSet password"

        message.set_content(
            "We received a request to reset your FleetSet password.\n\n"
            f"Use this link to choose a new password:\n{reset_url}\n\n"
            "This link expires after 30 minutes and can only be used once.\n"
            "If you did not request a password reset, you can ignore this email."
        )

        with smtplib.SMTP_SSL(
            SMTP_HOST,
            SMTP_PORT,
            timeout=30,
        ) as smtp:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)

        return {
            "success": True,
            "message": "Password reset email sent",
        }

    except Exception:
        # Do not expose SMTP credentials or internal errors to API clients.
        return {
            "success": False,
            "message": "Unable to send password reset email",
        }


def send_password_reset_email(
    recipient_email: str,
    reset_url: str,
):
    if not SMTP_USERNAME or not SMTP_PASSWORD or not SMTP_FROM_EMAIL:
        return {"success": False, "message": "Email configuration incomplete"}

    try:
        message = EmailMessage()
        message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        message["To"] = recipient_email
        message["Subject"] = "Reset your FleetSet password"

        message.set_content(
            "A request was made to reset your FleetSet password.\n\n"
            f"Open this link in your FleetSet mobile app:\n{reset_url}\n\n"
            "This link expires in 30 minutes and can only be used once.\n"
            "If you did not request this, you can ignore this email."
        )

        with smtplib.SMTP_SSL(
            SMTP_HOST, SMTP_PORT, timeout=30
        ) as smtp:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)

        return {"success": True, "message": "Email sent"}

    except Exception:
        # Keep internal SMTP details out of the API response.
        return {"success": False, "message": "Email delivery failed"}    
        