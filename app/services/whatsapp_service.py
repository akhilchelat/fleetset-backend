import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


# ============================================================
# WHATSAPP CONFIGURATION
# ============================================================

def validate_whatsapp_config():
    """
    Validate required WhatsApp Cloud API configuration.
    """

    missing = []

    if not WHATSAPP_API_URL:
        missing.append("WHATSAPP_API_URL")

    if not WHATSAPP_ACCESS_TOKEN:
        missing.append("WHATSAPP_ACCESS_TOKEN")

    if not WHATSAPP_PHONE_NUMBER_ID:
        missing.append("WHATSAPP_PHONE_NUMBER_ID")

    if missing:
        return {
            "success": False,
            "message": (
                "Missing WhatsApp configuration: "
                + ", ".join(missing)
            ),
        }

    return {
        "success": True,
        "message": "WhatsApp configuration is valid",
    }


# ============================================================
# INDIAN PHONE NUMBER NORMALIZATION
# ============================================================

def normalize_indian_phone(phone: str) -> str:
    """
    Normalize an Indian mobile number into WhatsApp format.

    Accepted formats:

        8157095375
        918157095375
        +918157095375
        +91 8157095375
        08157095375
        08157-095375
        +91-8157095375

    Returns:

        918157095375

    WhatsApp expects the number without:
        +
        spaces
        -
        brackets
    """

    if not phone:
        raise ValueError("Phone number is required.")

    # Convert to string and remove surrounding spaces
    phone = str(phone).strip()

    # Remove common formatting characters
    phone = (
        phone
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    # --------------------------------------------------------
    # Case 1:
    # +91XXXXXXXXXX
    # --------------------------------------------------------

    if phone.startswith("+91"):
        phone = phone[1:]

    # --------------------------------------------------------
    # Case 2:
    # 0XXXXXXXXXX
    # Example:
    # 08157095375
    # --------------------------------------------------------

    elif len(phone) == 11 and phone.startswith("0"):
        phone = "91" + phone[1:]

    # --------------------------------------------------------
    # Case 3:
    # XXXXXXXXXX
    # Example:
    # 8157095375
    # --------------------------------------------------------

    elif len(phone) == 10:
        phone = "91" + phone

    # --------------------------------------------------------
    # Case 4:
    # 91XXXXXXXXXX
    # Already normalized
    # --------------------------------------------------------

    elif len(phone) == 12 and phone.startswith("91"):
        pass

    else:
        raise ValueError(
            "Invalid Indian phone number. "
            "Use a valid 10-digit Indian mobile number."
        )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    if len(phone) != 12 or not phone.startswith("91"):
        raise ValueError(
            "Invalid Indian phone number format."
        )

    # Extract the actual 10-digit mobile number
    mobile_number = phone[2:]

    # Indian mobile numbers normally begin with 6, 7, 8 or 9
    if not mobile_number.isdigit():
        raise ValueError(
            "Phone number must contain only digits."
        )

    if mobile_number[0] not in "6789":
        raise ValueError(
            "Invalid Indian mobile number. "
            "Mobile number must start with 6, 7, 8 or 9."
        )

    return phone


# ============================================================
# SEND PDF DOCUMENT THROUGH WHATSAPP
# ============================================================

def send_whatsapp_document(
    recipient_phone: str,
    pdf_path: str | Path,
    caption: str = "FleetSet Report",
):
    """
    Upload a PDF to WhatsApp Cloud API and send it
    as a document message.

    Parameters:
        recipient_phone:
            Indian mobile number in any supported format.

        pdf_path:
            Path to the PDF file.

        caption:
            Caption displayed with the PDF.

    Returns:
        Dictionary containing success/failure information.
    """

    # ========================================================
    # 1. VALIDATE CONFIGURATION
    # ========================================================

    config = validate_whatsapp_config()

    if not config["success"]:
        return config

    # ========================================================
    # 2. NORMALIZE PHONE NUMBER
    # ========================================================

    try:
        recipient_phone = normalize_indian_phone(
            recipient_phone
        )

    except ValueError as exc:
        return {
            "success": False,
            "message": str(exc),
        }

    # ========================================================
    # 3. VALIDATE PDF PATH
    # ========================================================

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        return {
            "success": False,
            "message": f"PDF file not found: {pdf_path}",
        }

    if not pdf_path.is_file():
        return {
            "success": False,
            "message": f"PDF path is not a file: {pdf_path}",
        }

    # ========================================================
    # 4. WHATSAPP API HEADERS
    # ========================================================

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }

    # ========================================================
    # 5. UPLOAD PDF TO WHATSAPP MEDIA
    # ========================================================

    upload_url = (
        f"{WHATSAPP_API_URL}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/media"
    )

    try:

        with open(pdf_path, "rb") as pdf_file:

            files = {
                "file": (
                    pdf_path.name,
                    pdf_file,
                    "application/pdf",
                )
            }

            data = {
                "messaging_product": "whatsapp",
                "type": "application/pdf",
            }

            upload_response = requests.post(
                upload_url,
                headers=headers,
                files=files,
                data=data,
                timeout=60,
            )

    except requests.RequestException as exc:

        return {
            "success": False,
            "message": (
                "WhatsApp upload request failed: "
                f"{exc}"
            ),
        }

    # ========================================================
    # 6. CHECK MEDIA UPLOAD RESPONSE
    # ========================================================

    if upload_response.status_code not in (200, 201):

        return {
            "success": False,
            "message": "WhatsApp media upload failed",
            "status_code": upload_response.status_code,
            "response": upload_response.text,
        }

    # ========================================================
    # 7. GET MEDIA ID
    # ========================================================

    try:

        upload_data = upload_response.json()

        media_id = upload_data["id"]

    except (KeyError, ValueError):

        return {
            "success": False,
            "message": (
                "WhatsApp did not return a media ID"
            ),
            "response": upload_response.text,
        }

    # ========================================================
    # 8. SEND DOCUMENT MESSAGE
    # ========================================================

    message_url = (
        f"{WHATSAPP_API_URL}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    message_payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "document",
        "document": {
            "id": media_id,
            "caption": caption,
            "filename": pdf_path.name,
        },
    }

    try:

        message_response = requests.post(
            message_url,
            headers={
                **headers,
                "Content-Type": "application/json",
            },
            json=message_payload,
            timeout=60,
        )

    except requests.RequestException as exc:

        return {
            "success": False,
            "message": (
                "WhatsApp message request failed: "
                f"{exc}"
            ),
        }

    # ========================================================
    # 9. CHECK MESSAGE RESPONSE
    # ========================================================

    if message_response.status_code not in (200, 201):

        return {
            "success": False,
            "message": "WhatsApp message failed",
            "status_code": message_response.status_code,
            "response": message_response.text,
        }

    # ========================================================
    # 10. PARSE RESPONSE
    # ========================================================

    try:

        message_data = message_response.json()

    except ValueError:

        message_data = {
            "raw_response": message_response.text
        }

    # ========================================================
    # 11. SUCCESS
    # ========================================================

    return {
        "success": True,
        "message": "PDF sent successfully through WhatsApp",
        "recipient_phone": recipient_phone,
        "media_id": media_id,
        "response": message_data,
    }