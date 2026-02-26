import os
import uuid
from flask import abort
from werkzeug.utils import secure_filename
from config import ALLOWED_MIME_TYPES, CATEGORY_SIZE_LIMITS


def validate_and_save_files(
    files,
    category,
    clearance_id,
    base_path
):
    """
    files        -> list of FileStorage
    category     -> receipt_air_ticket, receipt_food, etc
    clearance_id -> same request ID
    base_path    -> UPLOAD_ROOT
    """

    saved_files = []

    if not files:
        return saved_files

    limit = CATEGORY_SIZE_LIMITS.get(category)

    for file in files:
        if file.filename == "":
            continue

        # MIME validation
        if file.mimetype not in ALLOWED_MIME_TYPES["common"]:
            abort(400, f"Invalid file type: {file.mimetype}")

        # Size validation
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)

        if limit and size > limit:
            abort(400, f"{category} exceeds size limit")

        # Directory: uploads/<clearance_id>/<category>/
        target_dir = os.path.join(base_path, str(clearance_id), category)
        os.makedirs(target_dir, exist_ok=True)

        # Safe unique filename
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(target_dir, secure_filename(filename))

        file.save(path)
        saved_files.append(path)

    return saved_files
