from app import app
from extensions import db
from models import User

with app.app_context():
    users = User.query.all()

    if not users:
        print("No users found in the database.")
    else:
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Approved: {user.is_approved}")
            print(f"Active: {user.is_active}")
            print(f"Failed Attempts: {user.failed_attempts}")
            print(f"Last Login: {user.last_login}")
            print(f"Password Changed At: {user.password_changed_at}")
            print(f"Req Admin: {user.req_admin}")
            print(f"District List: {user.district_list}")
            print(f"My Requestors: {user.my_requestors}")
            print(f"Delegated From User ID: {user.delegated_from_user_id}")
            print(f"Delegated Districts: {user.delegated_districts}")
            print(f"Delegation Active: {user.delegation_active}")
            print(f"Signature Stored: {'Yes' if user.signature else 'No'}")
            print(f"Signature MIME: {user.signature_mime}")  
            print(f"password_hash : {user.password_hash}")
            print("-" * 60)
