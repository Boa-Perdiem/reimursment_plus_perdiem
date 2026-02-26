from app import app
from extensions import db
from models import User

with app.app_context():

    super1 = User(
        username="superadmin1",
        email="super1@system.com",
        role="SUPER_ADMIN",
        is_approved=True
    )
    super1.set_password("StrongPassword123!")

    super2 = User(
        username="superadmin2",
        email="super2@system.com",
        role="SUPER_ADMIN",
        is_approved=True
    )
    super2.set_password("StrongPassword123!")

    db.session.add(super1)
    db.session.add(super2)
    db.session.commit()

    print("✅ Super admins created")
