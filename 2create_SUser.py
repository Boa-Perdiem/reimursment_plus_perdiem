from app import app
from extensions import db
from models import User

with app.app_context():
    user = User(
        username="superadmin",
        email="superadmin@example.com",
        role="SUPER_ADMIN",
        is_approved=True
    )
    user.set_password("StrongPassword123!")  # hashed automatically

    db.session.add(user)
    db.session.commit()
    print("✅ Super admin created")
