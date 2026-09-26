import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "FleetSet")

print("SMTP_USERNAME:", SMTP_USERNAME)
print("SMTP_PASSWORD configured:", bool(SMTP_PASSWORD))
print("SMTP_FROM_EMAIL:", SMTP_FROM_EMAIL)



def send_report_email(
    recipient_email: str,
    pdf_path: str | Path,
    subject: str,
    body: str,
):
    """
    Send a FleetSet report PDF through Gmail SMTP.
    """

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

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        return {
            "success": False,
            "message": "Report PDF file not found",
        }

    try:
        message = EmailMessage()

        message["From"] = (
            f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        )
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

        with smtplib.SMTP_SSL(SMTP_HOST,
                              SMTP_PORT,
                              timeout=30,) as smtp:
              smtp.login(SMTP_USERNAME, SMTP_PASSWORD,)

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
                "message": (f"Gmail authentication failed. "
                            f"SMTP code: {exc.smtp_code}. "
                            f"SMTP message: {smtp_error}"),}

    except smtplib.SMTPException as exc:
        return {
            "success": False,
            "message": f"SMTP error: {str(exc)}",
        }

    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to send report email: {str(exc)}",
        }