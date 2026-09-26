from app.services.whatsapp_service import (
    validate_whatsapp_config,
)


result = validate_whatsapp_config()

print("\n========== WHATSAPP CONFIG TEST ==========")
print("Success:", result["success"])
print("Message:", result["message"])
print("==========================================\n")