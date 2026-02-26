import os
from flask import Blueprint, Response, flash, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
from datetime import datetime

from extensions import db
from models import (
    PerdiemRequest,
    User,
    PerDiemForm,
    Comment,
    Receipt,
)

from routes import reimburs_req_pdf, perdiem_req_pdf,mailer


requestor_admin_bp = Blueprint(
    "requestor_admin",
    __name__,
    url_prefix="/requestor_admin"
)


def require_requestor_admin_role():
    if current_user.role != "REQUESTOR_ADMIN":
        abort(403)


@requestor_admin_bp.route("/approve/<int:request_id>", methods=["GET", "POST"])
@login_required
def requestor_admin_dashboard(request_id):
    require_requestor_admin_role()

    perdiem = PerdiemRequest.query.get_or_404(request_id)
    receipts = Receipt.query.filter_by(request_id=request_id).all()

    # Always convert to JSON-serializable format
    receipts_json = [
        {
            "id": r.id,
            "category": r.category,
            "mode": r.mode,
            "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if r.uploaded_at else None
        }
        for r in receipts
    ]

    if request.method == "POST":
        # Check if this is a decline submission
        is_decline = request.form.get("decline") == "1"

        if is_decline:
            perdiem.status = "DECLINED_BY_REQUESTOR_ADMIN"
            perdiem.status_req_admin = "DECLINED"
            flash("Request Declined","danger")
            
        else:
            perdiem.status = "APPROVED_BY_REQUESTOR_ADMIN"
            perdiem.status_req_admin = "APPROVED"
            flash("Request Approved","success")

            if perdiem.mode == "system":
                admin_perdiem = PerDiemForm.query.filter_by(request_id=request_id).first()
                if admin_perdiem:
                    admin_perdiem.approved_by_req_admin = current_user.username
                    admin_perdiem.approved_at_req_admin = datetime.utcnow()

        comment_text = request.form.get("comment", "").strip() or "N/A"

        comment = Comment(
            request_id=request_id,
            role=current_user.role,
            user_id=current_user.id,
            comment=comment_text,
            created_at=datetime.utcnow()
        )
        db.session.add(comment)
        db.session.commit()


        if not is_decline:
            reimburs_req_pdf.generate_req_trueperdiem_pdf(request_id=perdiem.id)
            if perdiem.mode == "system":
                perdiem_req_pdf.generate_per_req_trueperdiem_pdf(request_id=perdiem.id)

            username = current_user.username
            rec_email = current_user.email
            body_color = "#00bb0c"  #sucess
            subject = f"Perdiem Request Approved for  {perdiem.perdiem_code} "
            body = f"You just approved this request. The Request:<br>Code: <strong>{perdiem.perdiem_code}</strong> <br>District: <strong>{perdiem.district}</strong> <br>Amount: <strong>{perdiem.birr_amount}</strong> <br>Submit Mode: <strong>{perdiem.mode}</strong> <br>Status: <strong>{perdiem.status}</strong>"

            mailer.send_final_clearance_mail(username, rec_email, subject, body, body_color)

            #for Requestor       
            admin = User.query.filter(User.username==perdiem.requestor_name).first()
            username = admin.username
            rec_email = admin.email
            body_color = "#2241ef"  #pending
            subject = f"Perdiem Request Status update for  {perdiem.perdiem_code} "
            body = f"Your Request {perdiem.perdiem_code}</strong> with <br>Amount <strong>{perdiem.birr_amount}</strong> had been changed to status <strong>{perdiem.status}</strong>  just now. <br> <br>"

            mailer.send_final_clearance_mail(username, rec_email, subject, body, body_color)

            #for Intermediate approver

            district = perdiem.district.strip().lower()

            admin_inter = User.query.filter(User.role == "INTERMEDIATE_APPROVER").all()
            matched_admins = []

            for user in admin_inter:
                # Combine user's own districts
                districts = []
                if user.district_list:
                    districts.extend([d.strip().lower() for d in user.district_list.split(",")])
                
                # Add delegated districts if delegation is active
                if user.delegation_active and user.delegated_districts:
                    districts.extend([d.strip().lower() for d in user.delegated_districts.split(",")])
                
                if district in districts:
                    matched_admins.append(user)

            if matched_admins:
                rec_emails = [admin.email for admin in matched_admins if admin.email]  # ignore None emails
                usernames = ", ".join([admin.username for admin in matched_admins])
                
                subject = f"Approval Needed for Perdiem Request {perdiem.perdiem_code}"
                body_color = "#849f00"
                body = f"""
                You have a new request approval.<br>
                Code: <strong>{perdiem.perdiem_code}</strong><br>
                District: <strong>{perdiem.district}</strong><br>
                Amount: <strong>{perdiem.birr_amount}</strong><br>
                Submit Mode: <strong>{perdiem.mode}</strong><br>
                Status: <strong>{perdiem.status}</strong><br><br>
                Please review and take appropriate action.
                """

                mailer.send_final_clearance_mail(usernames, rec_emails, subject, body, body_color)
                

                
        else:
            username = current_user.username
            rec_email = current_user.email
            body_color = "#f44336"  #Declined
            subject = f"Perdiem Request Declined for  {perdiem.perdiem_code} "
            body = f"You just Declined this request. The Request:<br>Code: <strong>{perdiem.perdiem_code}</strong> <br>District: <strong>{perdiem.district}</strong> <br>Amount: <strong>{perdiem.birr_amount}</strong> <br>Submit Mode: <strong>{perdiem.mode}</strong> <br>Status: <strong>{perdiem.status}</strong>"

            mailer.send_final_clearance_mail(username, rec_email, subject, body, body_color)

            #for Requestor 

            comment_filtered = Comment.query.filter(
            Comment.request_id == perdiem.id,
            Comment.user_id == current_user.id,
            Comment.role == current_user.role
        ).first()

            comment_text = comment_filtered.comment if comment_filtered else "No comment provided"
                  
            admin = User.query.filter(User.username==perdiem.requestor_name).first()
            username = admin.username
            rec_email = admin.email
            body_color = "#f44336"  #Declined
            subject = f"Perdiem Request Status update for  {perdiem.perdiem_code} "
            body = f'Your Request {perdiem.perdiem_code} with <br>Amount <strong>{perdiem.birr_amount}</strong> had been changed to status <strong>{perdiem.status}</strong> just now.<br><br><span style="color:black">Comment/Reason Given by Decliner  <strong> {current_user.username} </strong>  role <strong>{current_user.role}</strong> :</span> <br>{comment_text}<br><br>'

            mailer.send_final_clearance_mail(username, rec_email, subject, body, body_color)

        return redirect(url_for("dashboard.index"))

    return render_template(
        "requestor_admin_dashboard.html",
        perdiem=perdiem,
        receipts=receipts_json,
    )

@requestor_admin_bp.route("/serve_pdf/<int:request_id>/<string:field>")
@login_required
def serve_pdf_db(request_id, field):
    require_requestor_admin_role()

    if field not in ["reimburs_form", "perdi_form"]:
        abort(404)

    perdiem = PerdiemRequest.query.get_or_404(request_id)

    pdf_data = getattr(perdiem, field)
    if not pdf_data:
        abort(404)

    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={field}_{request_id}.pdf"
        }
    )

@requestor_admin_bp.route("/serve_receipt/<int:receipt_id>")
@login_required
def serve_receipt(receipt_id):
    require_requestor_admin_role()
    receipt = Receipt.query.get_or_404(receipt_id)

    return Response(
        receipt.file_data,
        mimetype=receipt.file_mime,
        headers={"Content-Disposition": f"inline; filename=receipt_{receipt_id}"}
    )

