import os

UPLOAD_ROOT = os.path.join(os.getcwd(), "uploads")

ALLOWED_MIME_TYPES = {
    "common": {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg"
    },
    "form2": {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
}

# Per-category size limits (bytes)
CATEGORY_SIZE_LIMITS = {
    "receipt_air_ticket": 5 * 1024 * 1024,   # 5 MB
    "receipt_food": 3 * 1024 * 1024,         # 3 MB
    "receipt_bedroom": 3 * 1024 * 1024,
    "receipt_fuel": 3 * 1024 * 1024,
    "receipt_others": 2 * 1024 * 1024,
}