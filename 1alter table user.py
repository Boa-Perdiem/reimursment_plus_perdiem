# alter_users.py
from app import app
from extensions import db
from sqlalchemy import text

with app.app_context():  # ✅ MUST have app context
    # Add req_admin column if it doesn't exist
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN req_admin VARCHAR(50)"))
        print("req_admin column added.")
    except Exception as e:
        print(f"req_admin column probably exists: {e}")

    # Add district_list column if it doesn't exist
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN district_list VARCHAR(200)"))
        print("district_list column added.")
    except Exception as e:
        print(f"district_list column probably exists: {e}")

    db.session.commit()
    print("Database alteration complete.")
