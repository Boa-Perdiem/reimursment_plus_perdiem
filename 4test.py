from app import app
from models import User

with app.app_context():
    u = User.query.filter_by(username="superadmin1").first()
    print("Approved:", u.is_approved)
    print("Active:", u.is_active)

import os
print(os.path.abspath("boa_perdiem.db"))
