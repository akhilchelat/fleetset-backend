from app.services.whatsapp_service import (
    WHATSAPP_API_URL,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
)

print("API URL:", WHATSAPP_API_URL)

print(
    "Token loaded:",
    bool(WHATSAPP_ACCESS_TOKEN)
)

print(
    "Token length:",
    len(WHATSAPP_ACCESS_TOKEN)
    if WHATSAPP_ACCESS_TOKEN
    else 0
)

print(
    "Phone Number ID loaded:",
    bool(WHATSAPP_PHONE_NUMBER_ID)
)