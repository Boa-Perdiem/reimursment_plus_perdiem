from app import app
from extensions import db
from models import User

# Query users with roles FINAL_APPROVER or MANAGERIAL_APPROVER
users_to_delete = User.query.filter(User.role.in_(["FINAL_APPROVER"])).all()

# Delete them
for user in users_to_delete:
    db.session.delete(user)

# Commit the changes
db.session.commit()

print(f"Deleted {len(users_to_delete)} users.")