from app import app, db
from models import PerdiemRequest
import pprint
from sqlalchemy import LargeBinary

pp = pprint.PrettyPrinter(indent=2)

with app.app_context():
    all_requests = PerdiemRequest.query.all()

    for r in all_requests:
        row_dict = {}

        for c in r.__table__.columns:
            value = getattr(r, c.name)

            # ✅ Only show size for LargeBinary fields
            if isinstance(c.type, LargeBinary) and value is not None:
                value = f"<{len(value)} bytes>"

            row_dict[c.name] = value

        pp.pprint(row_dict)
