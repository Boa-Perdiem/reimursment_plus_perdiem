from flask import Blueprint, render_template, redirect, url_for, abort, send_file
from flask_login import login_required, current_user
from datetime import datetime
import os

from extensions import db
from models import (
    ClearanceRequest,
    Section2Approval,
    Section3Approval,
    Section4Approval,
    Section5Approval,
    Notification
)
from utils.pdf_generator import generate_final_clearance_pdf

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def require_admin():
    if current_user.role != "ADMIN":
        abort(403)


# -------------------------------------------------
# ADMIN DASHBOARD – OVERVIEW
# -------------------------------------------------
@admin_bp.route("/")
@login_required
def admin_dashboard():
    require_admin()

    clearances = ClearanceRequest.query.order_by(
        ClearanceRequest.created_at.desc()
    ).all()

    return render_template(
        "admin_dashboard.html",
        clearances=clearances
    )


# -------------------------------------------------
# ADMIN VIEW SINGLE CLEARANCE
# -------------------------------------------------
@admin_bp.route("/clearance/<int:clearance_id>")
@login_required
def view_clearance(clearance_id):
    require_admin()

    clearance = ClearanceRequest.query.get_or_404(clearance_id)

    section2 = Section2Approval.query.filter_by(clearance_id=clearance.id).all()
    section3 = Section3Approval.query.filter_by(clearance_id=clearance.id).all()
    section4 = Section4Approval.query.filter_by(clearance_id=clearance.id).all()
    section5 = Section5Approval.query.filter_by(clearance_id=clearance.id).all()

    return render_template(
        "admin_clearance_view.html",
        clearance=clearance,
        section2=section2,
        section3=section3,
        section4=section4,
        section5=section5
    )


# -------------------------------------------------
# FINALIZE & GENERATE PDF
# -------------------------------------------------
@admin_bp.route("/finalize/<int:clearance_id>", methods=["POST"])
@login_required
def finalize_clearance(clearance_id):
    require_admin()

    clearance = ClearanceRequest.query.get_or_404(clearance_id)

    # Ensure all sections are approved
    if not (
        Section2Approval.query.filter_by(clearance_id=clearance.id).first()
        and Section3Approval.query.filter_by(clearance_id=clearance.id).first()
        and Section4Approval.query.filter_by(clearance_id=clearance.id).first()
        and Section5Approval.query.filter_by(clearance_id=clearance.id).first()
    ):
        abort(400, "All sections must be approved before finalization")

    pdf_path = generate_final_clearance_pdf(clearance.id)

    clearance.finalized_at = datetime.utcnow()
    clearance.final_pdf_path = pdf_path
    db.session.commit()

    # Notify REQUESTOR
    notification = Notification(
        recipient_user_id=clearance.requestor_id,
        clearance_id=clearance.id,
        message="Your exit clearance has been fully approved. Final PDF is ready."
    )
    db.session.add(notification)
    db.session.commit()

    return redirect(url_for("admin.view_clearance", clearance_id=clearance.id))


# -------------------------------------------------
# DOWNLOAD FINAL PDF
# -------------------------------------------------
@admin_bp.route("/download/<int:clearance_id>")
@login_required
def download_final_pdf(clearance_id):
    require_admin()

    clearance = ClearanceRequest.query.get_or_404(clearance_id)

    if not clearance.final_pdf_path or not os.path.exists(clearance.final_pdf_path):
        abort(404)

    return send_file(
        clearance.final_pdf_path,
        as_attachment=True
    )
