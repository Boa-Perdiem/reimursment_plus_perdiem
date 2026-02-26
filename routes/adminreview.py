from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from models import PerdiemRequest

adminreview_bp = Blueprint(
    'adminreview', __name__, template_folder='templates', url_prefix='/adminreview'
)


@adminreview_bp.route('/<int:request_id>')
@login_required
def comments_view(request_id):
    
    perdiem = PerdiemRequest.query.get_or_404(request_id)

    comments_by_role = {
        "REQUESTOR_ADMIN": [],
        "INTERMEDIATE_APPROVER": [],
        "MANAGERIAL_APPROVER": [],
        "FINAL_APPROVER": []
    }

    # Iterate over all comments
    for comment in perdiem.comments:
        if comment.role in comments_by_role:
            comments_by_role[comment.role].append(comment)

    # Get latest comment per role
    latest_comments = {
        role: comments[-1].comment if comments else "PENDING"
        for role, comments in comments_by_role.items()
    }

    return render_template(
        "adminreview_dashboard.html",
        perdiem=perdiem,
        whole_comments=latest_comments,
        comments_by_role=comments_by_role
    )
