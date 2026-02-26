from flask import Blueprint, Response, flash, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
from datetime import datetime
from routes import reimburs_final_pdf,mailer

from extensions import db
from models import (
    PerdiemRequest,
    PerDiemForm,
    Receipt, 
    Comment,
    User,
)

final_approver_bp = Blueprint("final_approver", __name__, url_prefix="/final_approver")


@final_approver_bp.route("/<int:request_id>", methods=["GET", "POST"])
@login_required
def final_approver_dashboard(request_id):
    perdiem = PerdiemRequest.query.get_or_404(request_id)
    receipts = Receipt.query.filter_by(request_id=request_id).all()

    if request.method == "POST":
        # Detect decline
        is_decline = request.form.get("decline") == "1"

        if is_decline:
            perdiem.status = "DECLINED_BY_FINAL_APPROVER"
            perdiem.status_final_apr = "DECLINED"
            flash("Request Declined","danger")
        else:
            perdiem.status = "APPROVED_BY_FINAL_APPROVER"
            perdiem.status_final_apr = "APPROVED"
            flash("Request Approved","success")

        # Save comment
        comment_text = request.form.get("comment", "").strip()
        if not comment_text:
            comment_text = "N/A"

        comment = Comment(
            request_id=request_id,
            role=current_user.role,
            user_id=current_user.id,
            comment=comment_text,
            created_at=datetime.utcnow()
        )
        db.session.add(comment)
        db.session.commit()

        # Generate PDF only for approvals
        if not is_decline:
            reimburs_final_pdf.generate_reimb_final_pdf(request_id=perdiem.id)
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

            #for Finance

            finance_user = User.query.filter(User.role == "FINANCE").first()

            rec_emails = finance_user.email 
            usernames = finance_user.username 

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

            mailer.send_finance_forms_mail(username=usernames,rec_email=rec_emails,subject=subject,body=body,body_color=body_color,reimburs_file=perdiem.reimburs_form,perdi_file=perdiem.perdi_form)
        
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
            body = f'Your Request {perdiem.perdiem_code} with <br>Amount <strong>{perdiem.birr_amount}</strong> had been changed to status <strong>{perdiem.status}</strong> just now.<br><br><span style="color:black">Comment/Reason Given by Decliner <strong>{current_user.username}</strong> role <strong>{current_user.role}</strong> :</span> <br>{comment_text}<br><br>'

            mailer.send_final_clearance_mail(username, rec_email, subject, body, body_color)


        return redirect(url_for("dashboard.index"))

 
    receipts_json = [
        {
            "id": r.id,
            "category": r.category,
            "mode": r.mode,
            "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for r in receipts
    ]

    return render_template(
        "fin_approver_dashboard.html",
        perdiem=perdiem,
        receipts=receipts_json
    )


@final_approver_bp.route("/serve_pdf/<int:request_id>/<string:field>")
@login_required
def serve_pdf_db(request_id, field):
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


@final_approver_bp.route("/serve_receipt/<int:receipt_id>")
@login_required
def serve_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)

    return Response(
        receipt.file_data,
        mimetype=receipt.file_mime,
        headers={"Content-Disposition": f"inline; filename=receipt_{receipt_id}"}
    )
