# routes/adminreview.py
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from models import ClearanceRequest

adminreview_bp = Blueprint(
    'adminreview', __name__, template_folder='templates', url_prefix='/adminreview'
)


def require_admin_role():
    if current_user.role != "ADMIN":
        abort(403)


@adminreview_bp.route('/<int:clearance_id>')
@login_required
def section_review(clearance_id):
    require_admin_role()
    clearance = ClearanceRequest.query.get_or_404(clearance_id)

    # Collect Section5 approvals
    section5_reviews = {
        "Section5 Warehouse": getattr(clearance.section5_approval, "status_s5", "PENDING") if clearance.section5_approval else "PENDING",
        "Section5 Transport": getattr(clearance.section5_transport_approval, "status_s5trans", "PENDING") if clearance.section5_transport_approval else "PENDING",
        "Section5 Credit Mngmt": getattr(clearance.section5_creditM_approval, "status_s5creditm", "PENDING") if clearance.section5_creditM_approval else "PENDING"
    }

    return render_template(
        "adminreview_dashboard.html",
        clearance=clearance,
        section5_reviews=section5_reviews
    )
