# update_user_email.py

from app import app, db
from models import User

def update_user_email(username, new_email):
    """Update the email of a user by their username."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found.")
            return

        old_email = user.email
        user.email = new_email
        db.session.commit()

        print(f"✅ User '{username}' email updated from '{old_email}' to '{new_email}'.")

if __name__ == "__main__":
    username_input = input("Enter username: ")
    new_email_input = input("Enter new email: ")
    update_user_email(username_input, new_email_input)