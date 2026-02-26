from flask import Blueprint, Response, render_template, request, redirect, url_for, abort, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from num2words import num2words
from models import User
from routes import reimb_pdf,perdiem_pdf,mailer
import random
from extensions import db
from models import (
    PerdiemRequest,
    PerDiemForm,
    Receipt,
)


from utils.receipt_ocr import run_receipt_ocr
from utils.aggregate_receipt_totals import aggregate_category_totals

# -------------------------------------------------
# FILE VALIDATION CONFIG
# -------------------------------------------------
ALLOWED_MIME_TYPES = {
    "air_ticket": {"application/pdf", "image/jpeg", "image/png"},
    "food": {"application/pdf", "image/jpeg", "image/png"},
    "bedroom": {"application/pdf", "image/jpeg", "image/png"},
    "fuel_transport": {"application/pdf", "image/jpeg", "image/png"},
    "other": {"application/pdf", "image/jpeg", "image/png"},
}

MAX_RECEIPT_SIZES = {
    "air_ticket": 3 * 1024 * 1024,
    "food": 3 * 1024 * 1024,
    "bedroom": 3 * 1024 * 1024,
    "fuel_transport": 3 * 1024 * 1024,
    "other": 3 * 1024 * 1024,
}

FORM2_MAX_SIZE = 5 * 1024 * 1024  # 5MB
FORM2_ALLOWED_MIME = {"application/pdf"}

dashboard_bp = Blueprint("dashboard", __name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
super_admin_bp = Blueprint("super_admin", __name__, url_prefix="/super-admin")
mailer_bp = Blueprint("mailer", __name__, url_prefix="/mailer")

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
@dashboard_bp.route("/")
@login_required
def index():
    role = current_user.role

    if role == "REQUESTOR":
        return redirect(url_for("dashboard.requestor"))
    if role == "REQUESTOR_ADMIN":
        return redirect(url_for("dashboard.approval_dashboard"))
    if role == "INTERMEDIATE_APPROVER":
        return redirect(url_for("dashboard.approval_dashboard"))
    if (role == "MANAGERIAL_APPROVER") or (role == "FINAL_APPROVER") or (role == "MANAGERIAL_DELEGATE"):
        return redirect(url_for("dashboard.approval_dashboard_final"))

    if role == "SUPER_ADMIN":
        return redirect(url_for("super_admin.super_admin_page"))        
    if role == "FINANCE":
        return redirect(url_for("dashboard.finance"))
   

    abort(500)



def calculate_daily_rate(grade: int) -> int:
    if 1 <= grade <= 4:
        return 1400
    elif 5 <= grade <= 8:
        return 1600
    elif 9 <= grade <= 11:
        return random.randrange(1200, 2301, 100)
    elif 12 <= grade <= 13:
        return random.randrange(1900, 2301, 100)
    elif 14 <= grade <= 16:
        return random.randrange(3000, 5001, 100)
    raise ValueError("Invalid employee grade")


def calculate_number_of_days(start_date, end_date, start_half=False, end_half=False):
    delta_days = (end_date - start_date).days + 1
    deduction = 0
    if start_half:
        deduction += 0.4
    if end_half:
        deduction += 0.4
    return round(delta_days - deduction, 1)


# -------------------------------------------------
# REQUESTOR
# -------------------------------------------------

@dashboard_bp.route("/requestor", methods=["GET", "POST"])
def requestor():
    if current_user.role != "REQUESTOR":
        abort(403)

    if request.method == "POST":

        print("FORM DATA:", request.form)
        print("FILES:", request.files)
        print("SUBMIT MODE:", request.form.get("submit_mode"))

        

        #reimb_pdf.generate_perdiem_pdf(request_id=perdiem.id)



        try:
            submit_mode = request.form.get("submit_mode")
            if submit_mode not in ("self", "system"):
                #flash("Per Diem request submitted successfully!", "success")
                print(request.form)
                raise ValueError("Invalid submit mode")
        

            birr_raw = request.form.get("Birr", "0").replace(",", "")
            birr_innum = float(birr_raw)

            birr_part = int(birr_innum)
            cents_part = round((birr_innum - birr_part) * 100)

            if cents_part:
                birr_words = (
                    f"{num2words(birr_part).capitalize()} birr and "
                    f"{num2words(cents_part)} cents only"
                )
            else:
                birr_words = f"{num2words(birr_part).capitalize()} birr only"

            perdiem = PerdiemRequest(
                perdiem_code=f"BOA-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                requestor_id=current_user.id,
                requestor_name=current_user.username,
                mode=submit_mode,
                from_=request.form["From"],
                contra=request.form["Contra"],
                contra_name=request.form["Contra_name"],
                district=request.form["District"],
                birr_amount=birr_innum,
                send_to=request.form["Send_To"],
                amount_in_words=birr_words,
                reason_for_claim=request.form["Reason_For_Claim"],
                current_role=current_user.role,
                status="SUBMITTED",
                created_at=datetime.utcnow()
            )

            db.session.add(perdiem)
            db.session.flush()

            # ---------------- FORM 2 ----------------
            if submit_mode == "self":
                form2 = request.files.get("form2_file")
                if not form2 or not form2.filename:
                    raise ValueError("Form 2 file is required")

                if form2.mimetype not in FORM2_ALLOWED_MIME:
                    raise ValueError("Form 2 must be PDF only")

                form2.seek(0, 2)
                size = form2.tell()
                form2.seek(0)

                if size > FORM2_MAX_SIZE:
                    raise ValueError("Form 2 exceeds 5 MB size limit")

                perdiem_form = PerDiemForm(
                    request_id=perdiem.id,
                    form2_file=form2.read(),
                    mode=submit_mode,
                    approved_by_req=current_user.username,
                    approved_at_req=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )

                


            else:
                grade = int(request.form["employee_grade"])
                name = str(request.form["employee_name"])
                position=str(request.form["employee_position"])
                office= str(request.form["employee_office"])
                
                daily_rate = calculate_daily_rate(grade)
                start = datetime.strptime(request.form["travel_begin"], "%Y-%m-%d")
                start_half=request.form["travel_begin_day_type"]
                end = datetime.strptime(request.form["travel_end"], "%Y-%m-%d")
                end_half=request.form["travel_end_day_type"]
                
                advance_taken=request.form["advance_taken"]
                #Total_perdiem=
                #net_amount=Total_perdiem - advance_taken

                days = calculate_number_of_days(
                    start, end,
                    request.form["travel_begin_day_type"] == "half",
                    request.form["travel_end_day_type"] == "half"
                )

                perdiem_form = PerDiemForm(
                    request_id=perdiem.id,
                    mode=submit_mode,
                    
                    travel_begin = start,
                    travel_end = end,
                    travel_begin_day_type = start_half,
                    travel_end_day_type = end_half,

                    employee_name=name,
                    employee_grade=grade,
                    employee_position=position,
                    employee_office=office,

                    number_of_days=days,
                    daily_rate=daily_rate,
                    perdiem_day_total=daily_rate * days,
                    advance_taken=advance_taken,
                    #Total_perdiem=Total_perdiem,
                    #net_amount=net_amount,
                    
                    approved_by_req=current_user.username,
                    approved_at_req=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )

            db.session.add(perdiem_form)

            # ---------------- RECEIPTS ----------------
            receipt_map_self = {
                "receipt_air_ticket": "air_ticket",
                "receipt_food": "food",
                "receipt_bedroom": "bedroom",
                "receipt_fuel": "fuel_transport",
                "receipt_others": "other",
            }

            receipt_map_system = {
                "sys_receipt_air_ticket": "air_ticket",
                "sys_receipt_food": "food",
                "sys_receipt_bedroom": "bedroom",
                "sys_receipt_fuel": "fuel_transport",
                "sys_receipt_others": "other",
            }

            if submit_mode == "self":
                receipt_map = receipt_map_self
            elif submit_mode == "system":
                receipt_map = receipt_map_system
            else:
                receipt_map = {}

            for field, category in receipt_map.items():
                for f in request.files.getlist(field):
                    if not f or not f.filename:
                        continue

                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(0)

                    if f.mimetype not in ALLOWED_MIME_TYPES[category]:
                        raise ValueError(f"{category.replace('_',' ').title()} invalid file type")

                    if size > MAX_RECEIPT_SIZES[category]:
                        raise ValueError(f"{category.replace('_',' ').title()} exceeds 3 MB")

                    db.session.add(
                        Receipt(
                            request_id=perdiem.id,
                            mode=submit_mode,
                            category=category,
                            file_data=f.read(),
                            file_mime=f.mimetype,
                            uploaded_at=datetime.utcnow()
                        )
                    )

        
            db.session.commit()
 
            #reimb_pdf.generate_perdiem_pdf(request_id=perdiem.id)

    # ---------------- OCR RECEIPTS ----------------
            import tempfile
            import os
            from collections import defaultdict

            try:
                receipts = Receipt.query.filter_by(request_id=perdiem.id).all()

                category_counter = defaultdict(int)

                for receipt in receipts:
                    category_counter[receipt.category] += 1

                    suffix = ".pdf" if receipt.file_mime == "application/pdf" else ".png"

                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(receipt.file_data)
                        temp_path = tmp.name

                    output_path, extracted_text = run_receipt_ocr(
                        receipt_path=temp_path,
                        perdiem_code=perdiem.perdiem_code,
                        requestor_name=perdiem.requestor_name,
                        category=receipt.category,
                        category_index=category_counter[receipt.category]
                    )

                    receipt.ocr_text = extracted_text
     

                    os.remove(temp_path)

                db.session.commit()

    

            except Exception as ocr_err:
                # OCR must never break submission
                print(f"OCR failed for perdiem {perdiem.id}: {ocr_err}")

            # 🔴 PUT YOUR VALIDATION RIGHT HERE
            if submit_mode == "system" or submit_mode == "self":
                receipt_count = Receipt.query.filter_by(request_id=perdiem.id).count()
                print("Receipt count:", receipt_count)

                if receipt_count == 0:
                    print("No receipts uploaded — deleting request")

                    PerDiemForm.query.filter_by(request_id=perdiem.id).delete()
                    db.session.delete(perdiem)
                    db.session.commit()

                    if submit_mode == "self":
                        flash("For Approval Purpose Self mode requires at least one receipt.", "danger")

                    if submit_mode == "system":
                        flash("To Auto Generate Perdiem Form System mode requires at least one receipt.", "danger")
                    return redirect(url_for("dashboard.requestor"))
            
        
            aggregate_category_totals(perdiem.id)
            if not (perdiem.r_pdf_path and os.path.exists(perdiem.r_pdf_path)):
                perdiem_pdf.generate_trueperdiem_pdf(request_id=perdiem.id)
                reimb_pdf.generate_perdiem_pdf(request_id=perdiem.id)
                


            db.session.refresh(perdiem)

            if not perdiem.reimburs_form or not perdiem.perdi_form:
                print("PDF generation failed — deleting request")

                # delete related children first (optional if cascade enabled)
                Receipt.query.filter_by(request_id=perdiem.id).delete()
                PerDiemForm.query.filter_by(request_id=perdiem.id).delete()

                db.session.delete(perdiem)
                db.session.commit()

                flash("Submission failed. Please try again.", "danger")
                return redirect(url_for("dashboard.requestor"))

            perdiem.all_process_finished = True  
            db.session.commit()

            username = current_user.username
            rec_email = current_user.email
            body_color = "#00bb0c"  #sucess
            subject = "Perdiem Request Submitted Successfully!"
            body = f"You have submitted your request. Your Request:<br>Code: <strong>{perdiem.perdiem_code}</strong> <br>District: <strong>{perdiem.district}</strong> <br>Amount: <strong>{perdiem.birr_amount}</strong> <br>Submit Mode: <strong>{perdiem.mode}</strong> <br>Status: <strong>{perdiem.status}</strong>"

            mailer.send_final_clearance_mail(username, rec_email, subject, body, body_color)

            admin = User.query.filter_by(username=current_user.req_admin).first()
            username = admin.username
            rec_email = admin.email
            body_color = "#849f00"  #pending
            subject=f"Approval Needed for Perdiem Request {perdiem.perdiem_code}"

            body = f"You have a new  request approval. The Request:<br>Code: <strong>{perdiem.perdiem_code}</strong> <br>District: <strong>{perdiem.district}</strong> <br>Amount: <strong>{perdiem.birr_amount}</strong> <br>Submit Mode: <strong>{perdiem.mode}</strong> <br>Status: <strong>{perdiem.status}</strong> <br> <br> please review and take appropriate action "

            mailer.send_final_clearance_mail(username, rec_email, subject, body, body_color)
            print("pdf generated")
            flash("Per Diem request submitted successfully!", "success")
            return redirect(url_for("dashboard.requestor"))

        except Exception as e:
            db.session.rollback()
            flash(str(e), "danger")

            requests = PerdiemRequest.query.filter_by(
                requestor_id=current_user.id
            ).all()

            return render_template(
                "requestor_dashboard.html",
                requests=requests,
                form_data=request.form
            )

    requests = PerdiemRequest.query.filter_by(requestor_id=current_user.id).all()
    return render_template("requestor_dashboard.html", requests=requests)

# -------------------------------------------------
# GENERATE PDF(Requestor)
# -------------------------------------------------

@dashboard_bp.route("/serve_pdf/<int:request_id>/<string:field>", methods=["GET"])
def serve_pdf(request_id, field):
    # get the perdiem record
    perdiem_record = PerdiemRequest.query.get_or_404(request_id)

    if field not in ["reimburs_form", "perdi_form"]:
        abort(404)

 
    print("safasfsaaf")
    pdf_data = getattr(perdiem_record, field)
    print(pdf_data)
    if pdf_data is None:
        abort(404)

    return Response(
        bytes(pdf_data),  # ensure bytes
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={field}_{request_id}.pdf"}
    )


 # -------------------------------------------------
# DELETE RECEIPT (INDIVIDUAL)
# -------------------------------------------------   

@dashboard_bp.route("/receipt/<int:receipt_id>/delete", methods=["POST"])
@login_required
def delete_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)

    if receipt.request.mode != "REQUESTOR":
        abort(403)

    db.session.delete(receipt)
    db.session.commit()
    return jsonify({"success": True})



@dashboard_bp.route('/approval_dashboard')
@login_required
def approval_dashboard():
    if current_user.role not in ["REQUESTOR_ADMIN", "INTERMEDIATE_APPROVER"]:
        abort(403)

    # All perdiem requests
    perdiems = PerdiemRequest.query.all()

    # All other intermediate approvers (for delegation dropdown)
    other_approvers = []
    if current_user.role == "INTERMEDIATE_APPROVER":
        other_approvers = User.query.filter(
            User.role == "INTERMEDIATE_APPROVER",
            User.id != current_user.id
        ).all()

    # Compute current user's districts safely
    my_districts = []
    if current_user.district_list:
        try:
            if ":" in current_user.district_list:
                my_districts = current_user.district_list.split(":")[1].split(",")
            else:
                my_districts = current_user.district_list.split(",")
        except Exception:
            my_districts = []

    delegated_districts = []
    if current_user.delegation_active and current_user.delegated_districts:
        delegated_districts = current_user.delegated_districts.split(",")

    relevant_districts = my_districts + delegated_districts

        # Determine delegator if there’s a pending or active delegation
    delegator = None
    if current_user.delegated_from_user_id and not current_user.delegation_active:
        delegator = User.query.get(current_user.delegated_from_user_id)

    active_delegator = None
    if current_user.delegation_active and current_user.delegated_from_user_id:
        active_delegator = User.query.get(current_user.delegated_from_user_id)

    active_delegation_from_me = None

    if current_user.role == "INTERMEDIATE_APPROVER":
        active_delegation_from_me = User.query.filter(
            User.delegated_from_user_id == current_user.id,
            User.delegation_active == True
        ).first()

        # For delegator view: requests they delegated
    delegated_requests = []
    if current_user.role == "INTERMEDIATE_APPROVER":
        delegatee = User.query.filter(
            User.delegated_from_user_id == current_user.id,
            User.delegation_active == True
        ).first()

        if delegatee:
            delegated_requests = PerdiemRequest.query.filter(
                PerdiemRequest.district.in_(delegatee.district_list.split(","))
            ).all()

    pending_delegations_sent = []
    if current_user.role == "INTERMEDIATE_APPROVER":
        pending_delegations_sent = User.query.filter(
            User.delegated_from_user_id == current_user.id,
            User.delegation_active == False  # pending only
        ).all()

    # True if the current user has any pending or active delegation
    has_active_or_pending_delegation = False

    # Pending delegation sent by me
    pending_delegation_sent = User.query.filter(
        User.delegated_from_user_id == current_user.id,
        User.delegation_active == False
    ).first()

    # Active delegation from me
    active_delegation_from_me = User.query.filter(
        User.delegated_from_user_id == current_user.id,
        User.delegation_active == True
    ).first()

    if pending_delegation_sent or active_delegation_from_me:
        has_active_or_pending_delegation = True



    return render_template(
        'approval_landing_dashboard.html',
        perdiems=perdiems,
        other_approvers=other_approvers,
        my_districts=my_districts,
        delegated_districts=delegated_districts,
        relevant_districts=relevant_districts,
        current_user=current_user,
        delegator=delegator,
        active_delegator=active_delegator,
        active_delegation_from_me=active_delegation_from_me,
        #delegated_requests=delegated_requests,
        pending_delegations_sent=pending_delegations_sent,
        has_active_or_pending_delegation=has_active_or_pending_delegation
    )

@dashboard_bp.route('/approval_dashboard_final')
@login_required
def approval_dashboard_final():
    if (current_user.role == 'REQUESTOR') or (current_user.role == 'REQUESTOR_ADMIN') or (current_user.role == 'INTERMEDIATE_APPROVER'):
        abort(403)

    perdiems = PerdiemRequest.query.all()
    perdiem_forms = PerDiemForm.query.all()
    receipts=Receipt.query.all()




    other_approvers = []
    if current_user.role == "MANAGERIAL_APPROVER":
        other_approvers = User.query.filter(
            User.role == "MANAGERIAL_DELEGATE",
            User.id != current_user.id
        ).all()

    
    if current_user.role == "MANAGERIAL_DELEGATE" and not current_user.delegation_active:
        perdiems = [] 


    is_managerial_approver = current_user.role == "MANAGERIAL_APPROVER"

    active_delegate = User.query.filter(
        User.delegated_from_user_id == current_user.id,
        User.delegation_active == True
    ).first()

    has_active_delegation = True if active_delegate else False

            # Determine delegator if there’s a pending or active delegation
    delegator = None
    if current_user.delegated_from_user_id and not current_user.delegation_active:
        delegator = User.query.get(current_user.delegated_from_user_id)

    active_delegator = None
    if current_user.delegation_active and current_user.delegated_from_user_id:
        active_delegator = User.query.get(current_user.delegated_from_user_id)

    active_delegation_from_me = None

    if current_user.role == "INTERMEDIATE_APPROVER":
        active_delegation_from_me = User.query.filter(
            User.delegated_from_user_id == current_user.id,
            User.delegation_active == True
        ).first()

        # For delegator view: requests they delegated
    delegated_requests = []
    if current_user.role == "MANAGERIAL_APPROVER":
        delegatee = User.query.filter(
            User.delegated_from_user_id == current_user.id,
            User.delegation_active == True
        ).first()

        
    pending_delegations_sent = []
    if current_user.role == "MANAGERIAL_APPROVER":
        pending_delegations_sent = User.query.filter(
            User.delegated_from_user_id == current_user.id,
            User.delegation_active == False  # pending only
        ).all()

    # True if the current user has any pending or active delegation
    has_active_or_pending_delegation = False

    # Pending delegation sent by me
    pending_delegation_sent = User.query.filter(
        User.delegated_from_user_id == current_user.id,
        User.delegation_active == False
    ).first()

    # Active delegation from me
    active_delegation_from_me = User.query.filter(
        User.delegated_from_user_id == current_user.id,
        User.delegation_active == True
    ).first()

    if pending_delegation_sent or active_delegation_from_me:
        has_active_or_pending_delegation = True



    return render_template(
        'final_approver_dashboard.html',
        perdiems=perdiems,
        perdiem_forms=perdiem_forms,
        receipts=receipts,
        current_user=current_user,
        other_approvers=other_approvers,
        is_managerial_approver=is_managerial_approver,
        active_delegate=active_delegate,
        has_active_delegation=has_active_delegation,
        delegator=delegator,
        active_delegator=active_delegator,
        active_delegation_from_me=active_delegation_from_me,
        #delegated_requests=delegated_requests,
        pending_delegations_sent=pending_delegations_sent,
        has_active_or_pending_delegation=has_active_or_pending_delegation
        
    )

@dashboard_bp.route('/finance')
@login_required
def finance():
    if (current_user.role == 'REQUESTOR') or (current_user.role == 'REQUESTOR_ADMIN') or (current_user.role == 'INTERMEDIATE_APPROVER'):
        abort(403)

    perdiems = PerdiemRequest.query.all()
    perdiem_forms = PerDiemForm.query.all()
    receipts=Receipt.query.all()



    return render_template(
        'finance_dashboard.html',
        perdiems=perdiems,
        perdiem_forms=perdiem_forms,
        receipts=receipts,
        current_user=current_user
    )

@dashboard_bp.route("/api/check_perdiem_status/<int:perdiem_id>")
@login_required
def check_perdiem_status(perdiem_id):
    perdiem = PerdiemRequest.query.get_or_404(perdiem_id)
    return jsonify({"all_process_finished": perdiem.all_process_finished})


