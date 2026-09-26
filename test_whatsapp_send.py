from pathlib import Path

from app.services.whatsapp_service import (
    send_whatsapp_document,
)


PDF_PATH = Path(
    "generated_reports/"
    "FleetSet_string_2026-09-01_2026-09-09_20260909_231356.pdf"
)


RECIPIENT_PHONE = "+91 8157095375"


result = send_whatsapp_document(
    recipient_phone=RECIPIENT_PHONE,
    pdf_path=PDF_PATH,
    caption=(
        "FleetSet Report\n"
        "Report period: 01-09-2026 to 09-09-2026"
    ),
)


print("\n========== WHATSAPP TEST ==========")

print("Success:", result.get("success"))
print("Message:", result.get("message"))

if result.get("recipient_phone"):
    print(
        "Recipient:",
        result["recipient_phone"]
    )

if result.get("status_code"):
    print(
        "Status Code:",
        result["status_code"]
    )

if result.get("media_id"):
    print(
        "Media ID:",
        result["media_id"]
    )

if result.get("response"):
    print(
        "Response:",
        result["response"]
    )

print("===================================\n")