from app import app
from models import Receipt

with app.app_context():
    receipts = Receipt.query.all()

    for r in receipts:
        print("ID:", r.id)
        print("Request ID:", r.request_id)
        print("Mode:", r.mode)
        print("Category:", r.category)
        print("File MIME:", r.file_mime)
        print("Uploaded At:", r.uploaded_at)
        print("OCR Text:", r.ocr_text)
        print("Category_total:", r.category_total)
        print("-" * 50)
