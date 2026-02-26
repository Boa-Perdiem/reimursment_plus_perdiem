# create_or_fix_users.py
from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash
from sqlalchemy import text

# Define all users
USERS = [
    ("requestor1", "REQUESTOR"),
    ("requestor2", "REQUESTOR"),
    ("requestor3", "REQUESTOR"),
    ("requestor4", "REQUESTOR"),
    ("requestor5", "REQUESTOR"),
    ("requestor6", "REQUESTOR"),
    ("requestor7", "REQUESTOR"),
    ("requestor8", "REQUESTOR"),
    ("requestor_admin", "REQUESTOR_ADMIN"),
    ("requestor_admin1", "REQUESTOR_ADMIN"),
    ("Desale", "INTERMEDIATE_APPROVER"),
    ("Marshet", "INTERMEDIATE_APPROVER"),
    ("Nardos", "INTERMEDIATE_APPROVER"),
    ("Frehiwot", "INTERMEDIATE_APPROVER"),
    ("Wondimu", "INTERMEDIATE_APPROVER"),
    ("Marta Zewdie", "MANAGERIAL_APPROVER"),
    ("Bantalem Taye", "FINAL_APPROVER")
]

# Map requestors to their admin
REQUESTOR_ADMIN_MAP = {
    "requestor1": "requestor_admin1",
    "requestor2": "requestor_admin",
    "requestor3": "requestor_admin1",
    "requestor4": "requestor_admin",
    "requestor5": "requestor_admin1",
    "requestor6": "requestor_admin",
    "requestor7": "requestor_admin1",
    "requestor8": "requestor_admin",
}

# Districts for intermediate approvers
INTERMEDIATE_DISTRICTS = {
    "Desale": ["HAWASSA", "WEST ADDIS"],
    "Marshet": ["MEKELLE", "ADAMA"],
    "Nardos": ["DIRE DAWA", "JIMMA"],
    "Frehiwot": ["BAHIR DAR", "CENTRAL ADDIS"],
    "Wondimu": ["EAST ADDIS", "DESSIE"]
}

with app.app_context():

    # -------------------------------
    # Ensure columns exist
    # -------------------------------
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN req_admin VARCHAR(50)"))
    except:
        pass

    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN district_list VARCHAR(200)"))
    except:
        pass

    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN my_requestors VARCHAR(10000)"))
    except:
        pass

    db.session.commit()

    # -------------------------------
    # Create or update users
    # -------------------------------
    for username, role in USERS:
        user = User.query.filter_by(username=username).first()
        if not user:
            # Create new user
            user = User(
                username=username,
                role=role,
                password_hash=generate_password_hash("password123")
            )

        # Update req_admin for requestors
        if role == "REQUESTOR":
            user.req_admin = REQUESTOR_ADMIN_MAP.get(username)
            user.district_list = None
        # Update districts for intermediate approvers
        elif role == "INTERMEDIATE_APPROVER":
            districts = INTERMEDIATE_DISTRICTS.get(username, [])
            user.district_list = ",".join(districts)
            user.req_admin = None
        else:
            # For admins and others
            user.req_admin = None
            user.district_list = None

        db.session.add(user)

    db.session.commit()

    # -------------------------------
    # Populate my_requestors for REQUESTOR_ADMIN
    # -------------------------------
    admins = User.query.filter(User.role == "REQUESTOR_ADMIN").all()
    for admin in admins:
        mapped_requestors = [u.username for u in User.query.filter(User.role == "REQUESTOR", User.req_admin == admin.username).all()]
        admin.my_requestors = ",".join(mapped_requestors) if mapped_requestors else None
        db.session.add(admin)

    db.session.commit()

    # -------------------------------
    # Print clean table
    # -------------------------------
    users = User.query.all()
    print(f"{'ID':<3} | {'Username':<20} | {'Role':<25} | {'Req_Admin':<20} | {'Districts':<25} | {'My Requestors'}")
    print("-" * 130)
    for user in users:
        print(
            f"{user.id:<3} | {user.username:<20} | {user.role:<25} | "
            f"{str(user.req_admin) if user.req_admin else '-':<20} | "
            f"{user.district_list if user.district_list else '-':<25} | "
            f"{user.my_requestors if user.my_requestors else '-'}"
        )

    print("\n✅ All users created/fixed successfully!")
