from app import app
from extensions import db
from models import Delegation

# ---------------------------
# Enter the application context
# ---------------------------
with app.app_context():
    delegations = Delegation.query.all()
    
    if not delegations:
        print("No delegations found.")
    else:
        for d in delegations:
            print(
                f"ID: {d.id}, From: {d.from_user.username}, To: {d.to_user.username}, "
                f"Perdiem ID: {d.perdiem_request_id}, Active: {d.is_active}, Created: {d.created_at}"
            )
