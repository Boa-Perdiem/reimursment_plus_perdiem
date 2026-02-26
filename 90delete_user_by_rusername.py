# delete_user.py

from app import app, db
from models import User, Comment   # 👈 import Comment


def delete_user_by_username(username):
    with app.app_context():

        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"❌ User '{username}' not found.")
            return

        # 🔥 Delete related comments first
        Comment.query.filter_by(user_id=user.id).delete()

        db.session.delete(user)
        db.session.commit()

        print(f"✅ User '{username}' and related comments deleted successfully.")


if __name__ == "__main__":
    username_input = input("Enter username to delete: ")
    delete_user_by_username(username_input)