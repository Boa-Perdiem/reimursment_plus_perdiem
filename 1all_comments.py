# list_comments_from_requests.py
from app import app
from extensions import db
from models import PerdiemRequest, User

with app.app_context():
    requests = PerdiemRequest.query.all()

    print(f"{'RequestID':<10} | {'PerdiemCode':<15} | {'CommentID':<10} | {'User':<20} | {'Role':<20} | Comment")
    print("-" * 120)

    for req in requests:
        if req.comments:
            # If multiple comments, iterate over them
            comment_list = req.comments if isinstance(req.comments, list) else [req.comments]
            for c in comment_list:
                user = User.query.get(c.user_id)
                username = user.username if user else f"UserID:{c.user_id}"
                print(
                    f"{req.id:<10} | {req.perdiem_code:<15} | {c.id:<10} | {username:<20} | {c.role:<20} | {c.comment}"
                )
        else:
            print(f"{req.id:<10} | {req.perdiem_code:<15} | {'-':<10} | {'-':<20} | {'-':<20} | No comments")
