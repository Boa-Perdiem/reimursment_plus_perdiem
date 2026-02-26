from flask import Blueprint, render_template, request, redirect, url_for, abort, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from num2words import num2words
from routes import reimb_pdf
import random
from extensions import db
from models import (
    PerdiemRequest,
    PerDiemForm,
    Receipt,
)



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
    if role == "MANAGERIAL_APPROVER":
        return redirect(url_for("dashboard.approval_dashboard"))
    if role == "FINAL_APPROVER":
        return redirect(url_for("dashboard.approval_dashboard"))

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
@login_required
def requestor():
    if current_user.role != "REQUESTOR":
        abort(403)

    if request.method == "POST":

        print("FORM DATA:", request.form)
        print("FILES:", request.files)
        print("SUBMIT MODE:", request.form.get("submit_mode"))



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
                daily_rate = calculate_daily_rate(grade)

                start = datetime.strptime(request.form["travel_begin"], "%Y-%m-%d")
                end = datetime.strptime(request.form["travel_end"], "%Y-%m-%d")
                
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
                    employee_grade=grade,
                    daily_rate=daily_rate,
                    number_of_days=days,
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

            reimb_pdf.generate_perdiem_pdf(request_id=perdiem.id)
            
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

@dashboard_bp.route("/generate_perdiem_pdf_ready/<int:request_id>", methods=["POST"])
@login_required
def generate_perdiem_pdf_ready(request_id):
    try:
        reimb_pdf.generate_perdiem_pdf(request_id=request_id)
        return jsonify({"success": True, "message": "PDF generated and ready."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    
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
