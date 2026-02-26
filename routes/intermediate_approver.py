from flask import (
    Blueprint, Response, render_template, request,
    redirect, url_for, abort, jsonify, flash
)
from flask_login import login_required, current_user
from datetime import datetime

from extensions import db
from routes import reimburs_inter_pdf,mailer
from models import PerdiemRequest, Comment, User, Notification, Receipt  # Added Receipt import

intermediate_approver_bp = Blueprint(
    "intermediate_approver",
    __name__,
    url_prefix="/intermediate_approver"
)

def require_intermediate_role():
    if current_user.role != "INTERMEDIATE_APPROVER":
        abort(403)


# -----------------------
# DASHBOARD FOR ONE REQUEST
# -----------------------
@intermediate_approver_bp.route("/<int:request_id>", methods=["GET", "POST"])
@login_required
def intermediate_dashboard(request_id):
    require_intermediate_role()

    perdiem = PerdiemRequest.query.get_or_404(request_id)
    receipts = Receipt.query.filter_by(request_id=request_id).all()  # Added for modal

    if request.method == "POST":
        # Check if this is a decline submission
        is_decline = request.form.get("decline") == "1"

        if is_decline:
            perdiem.status = "DECLINED_BY_INTERMEDIATE_APPROVER"
            perdiem.status_inter_apr = "DECLINED"
            flash("Request Declined","danger")
        else:
            perdiem.status = "APPROVED_BY_INTERMEDIATE_APPROVER"
            perdiem.status_inter_apr = "APPROVED"
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

        if not is_decline:
            reimburs_inter_pdf.generate_reimb_req_pdf(perdiem.id)

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

            #for Managerial/Final Approver

            if perdiem.birr_amount < 50000:
          
                manager = User.query.filter(User.role == "MANAGERIAL_APPROVER").first()
                rec_emails = []
                usernames = ""

                if manager:
                    usernames = manager.username
                    rec_emails.append(manager.email)

                    delegate = User.query.filter(
                        User.role == "MANAGERIAL_DELEGATE",
                        User.delegated_from_user_id == manager.id,
                        User.delegation_active == True
                    ).first()

                    if delegate:
                        usernames += f", {delegate.username}"
                        rec_emails.append(delegate.email)

            elif 50000 <= perdiem.birr_amount < 300000:
                final_approver = User.query.filter(User.role == "FINAL_APPROVER").first()
                rec_emails = [final_approver.email] if final_approver else []
                usernames = final_approver.username if final_approver else ""

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
        "intermediate_approver_dashboard.html",
        perdiem=perdiem,
        receipts=receipts_json  # Pass to template
    )


# -----------------------
# CREATE DELEGATION REQUEST
# -----------------------
@login_required
@intermediate_approver_bp.route("/delegate", methods=["POST"])
def delegate_request():
    to_user_id = request.form.get("to_user_id")
    if not to_user_id:
        return jsonify({"error":"No user selected"})
    
    to_user = User.query.get(to_user_id)
    if not to_user:
        return jsonify({"error":"User not found"})

    # Store delegation info directly in User table
    to_user.delegated_from_user_id = current_user.id
    to_user.delegated_districts = current_user.district_list
    to_user.delegation_active = False  # pending
    db.session.commit()

    return jsonify({"success": f"Delegation request sent to {to_user.username}"})

@login_required
@intermediate_approver_bp.route("/accept_delegation", methods=["POST"])
def accept_delegation():
    current_user.delegation_active = True
    db.session.commit()
    return jsonify({"success":"Delegation accepted"})

@login_required
@intermediate_approver_bp.route("/decline_delegation", methods=["POST"])
def decline_delegation():
    current_user.delegated_from_user_id = None
    current_user.delegated_districts = None
    current_user.delegation_active = False
    db.session.commit()
    return jsonify({"success":"Delegation declined"})

@intermediate_approver_bp.route('/terminate_delegation', methods=['POST'])
@login_required
def terminate_delegation():

    # Case 1: I am the delegatee (delegation TO me)
    if current_user.delegation_active and current_user.delegated_from_user_id:
        current_user.delegation_active = False
        current_user.delegated_from_user_id = None
        current_user.delegated_districts = None
        db.session.commit()
        return jsonify(success="Delegation terminated")

    # Case 2: I am the delegator (delegation FROM me)
    delegatee = User.query.filter(
        User.delegated_from_user_id == current_user.id,
        User.delegation_active == True
    ).first()

    if delegatee:
        delegatee.delegation_active = False
        delegatee.delegated_from_user_id = None
        delegatee.delegated_districts = None
        db.session.commit()
        return jsonify(success="Delegation terminated")

    return jsonify(error="No active delegation found"), 400


# -----------------------
# SERVE PDF
# -----------------------
@intermediate_approver_bp.route("/serve_pdf/<int:request_id>/<string:field>")
@login_required
def serve_pdf_db(request_id, field):
    require_intermediate_role()

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
            "Content-Disposition":
            f"inline; filename={field}_{request_id}.pdf"
        }
    )


# -----------------------
# SERVE RECEIPT
# -----------------------
@intermediate_approver_bp.route("/serve_receipt/<int:receipt_id>")
@login_required
def serve_receipt(receipt_id):
    require_intermediate_role()
    receipt = Receipt.query.get_or_404(receipt_id)

    return Response(
        receipt.file_data,
        mimetype=receipt.file_mime,
        headers={"Content-Disposition": f"inline; filename=receipt_{receipt_id}"}
    )
