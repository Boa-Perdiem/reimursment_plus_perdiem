# check_perdiem_requests.py
from app import app
from extensions import db
from models import PerdiemRequest

with app.app_context():
    requests = PerdiemRequest.query.all()  # fetch all perdiem requests

    # Print table header
    print(f"{'ID':<3} | {'Perdiem Code':<15} | {'Requestor':<20} | {'Mode':<10} | {'From':<15} | {'District':<15} | {'Amount':<10} | {'Status':<15} | {'Current Role':<15}")
    print("-" * 130)

    for r in requests:
        print(
            f"{r.id:<3} | "
            f"{r.perdiem_code:<15} | "
            f"{r.requestor_name:<20} | "
            f"{r.mode:<10} | "
            f"{r.from_:<15} | "
            f"{r.district:<15} | "
            f"{r.birr_amount:<10} | "
            f"{r.status:<15} | "
            f"{r.current_role:<15}"
        )
