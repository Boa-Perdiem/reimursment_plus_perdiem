from app import create_app
from models import Delegation, User

app = create_app()

with app.app_context():
    delegations = Delegation.query.all()

    for d in delegations:
        from_user = User.query.get(d.from_user_id)
        to_user = User.query.get(d.to_user_id)

        print({
            "delegation_id": d.id,
            "from_user_id": d.from_user_id,
            "from_username": from_user.username if from_user else None,
            "to_user_id": d.to_user_id,
            "to_username": to_user.username if to_user else None,
            "districts": d.districts,
            "is_active": d.is_active,
            "accepted_at": d.accepted_at,
            "terminated_at": d.terminated_at,
            "created_at": d.created_at
        })
