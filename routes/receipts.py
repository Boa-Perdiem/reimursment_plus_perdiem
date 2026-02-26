from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
from datetime import datetime

from extensions import db
from models import (
    PerdiemRequest,
    PerDiemForm,
    Receipt, 
    Comment,
)


receipts_bp = Blueprint("receipts", __name__, url_prefix="/receipts")



@receipts_bp.route("/<int:request_id>", methods=["GET", "POST"])
@login_required
def requestor_admin_dashboard(request_id):
   

    perdiem = PerdiemRequest.query.get_or_404(request_id)

    '''existing_approval = PerDiemForm.query.filter_by(
        request_id=perdiem.id
    ).first()'''

    if request.method == "POST":
        #if existing_approval:
        #    abort(403)

        req_perdiem = PerdiemRequest(         
             status="APPROVED_BY_REQUESTOR_ADMIN",
             status_req_admin="APPROVED"
        )

        db.session.add(req_perdiem)
        db.session.commit()

        admin_perdiem = PerDiemForm(         
            approved_by_req_admin=current_user.username,
            approved_at_req_admin=datetime.utcnow()
        )

        db.session.add(admin_perdiem)
        db.session.commit()

        comment = Comment(         
            request_id = request_id,
            role =   current_user.role, 
            user_id = current_user.id, 
            comment = request.form["comment"],
            created_at = datetime.utcnow()
        )

        db.session.add(Comment)
        db.session.commit()

        return redirect(url_for("dashboard.index"))

    return render_template(
        "requestor_admin_dashboard.html",
        perdiem=perdiem,
        #already_approved=bool(existing_approval)
    )
