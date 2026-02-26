from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
import os
from datetime import date



# -------------------------
# USER / AUTH MODEL
# -------------------------

class BaseForms(db.Model):
    __tablename__ = "base_forms"

    id = db.Column(db.Integer, primary_key=True)
    base_reimburs = db.Column(db.LargeBinary, nullable=True)
    base_perdi = db.Column(db.LargeBinary, nullable=True)

    @staticmethod
    def get_or_init(app):
        base = BaseForms.query.first()

        if not base:
            base = BaseForms()
            db.session.add(base)
            db.session.commit()

        # ---- Reimbursement base ----
        if not base.base_reimburs:
            reimb_path = os.path.join(
                app.root_path,
                "static/pdf_templates/reimbursement_form.pdf"
            )
            with open(reimb_path, "rb") as f:
                base.base_reimburs = f.read()

        # ---- Per diem base ----
        if not base.base_perdi:
            perdi_path = os.path.join(
                app.root_path,
                "static/pdf_templates/perdiem_form.pdf"
            )
            with open(perdi_path, "rb") as f:
                base.base_perdi = f.read()

        db.session.commit()
        return base

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)

    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=False)

    # --- Account Control ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    failed_attempts = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime)

    # --- Role Logic ---
    req_admin = db.Column(db.String(50))
    district_list = db.Column(db.String(2000))
    my_requestors = db.Column(db.String(10000))

    # --- Delegation ---
    delegated_from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    delegated_districts = db.Column(db.String(2000))
    delegation_active = db.Column(db.Boolean, default=False)

    # --- Signature ---
    signature = db.Column(db.LargeBinary, nullable=True)
    signature_mime = db.Column(db.String(100))

    # --- Password Methods ---
    def set_password(self, password: str):
        """Hashes the password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Checks a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

# -------------------------
# PERDIEM REQUEST (SECTION 1)
# -------------------------

class PerdiemRequest(db.Model):
    __tablename__ = "perdiem_requests"

    id = db.Column(db.Integer, primary_key=True)
    perdiem_code = db.Column(db.String(50), unique=True, nullable=False)
    requestor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    requestor_name=db.Column(db.String(20), nullable=False)
    mode = db.Column(db.String(20), nullable=False)
    from_ = db.Column(db.String(80), nullable=False)
    

    district = db.Column(db.String(50), nullable=False)
    send_to = db.Column(db.String(150), nullable=False)
    contra = db.Column(db.String(150), nullable=False)
    contra_name = db.Column(db.String(150), nullable=False)

    birr_amount = db.Column(db.Numeric(12, 2), nullable=False)
    amount_in_words = db.Column(db.Text, nullable=False)
    reason_for_claim = db.Column(db.Text, nullable=False)
   
    status = db.Column(db.String(50), nullable=False)
    status_req_admin = db.Column(db.String(50), nullable=True)
    status_inter_apr = db.Column(db.String(50), nullable=True)
    status_manager_apr = db.Column(db.String(50), nullable=True)
    status_final_apr = db.Column(db.String(50), nullable=True)
    current_role = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    #updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    pdf_path = db.Column(db.String(255),nullable=True)
    r_pdf_path = db.Column(db.String(255), nullable=True)
    pdf_path_req = db.Column(db.String(255),nullable=True)
    r_pdf_path_req = db.Column(db.String(255), nullable=True)
    pdf_path_inter = db.Column(db.String(255),nullable=True)
    r_pdf_path_inter = db.Column(db.String(255), nullable=True)
    pdf_path_final = db.Column(db.String(255),nullable=True)
    r_pdf_path_final = db.Column(db.String(255), nullable=True)

    overlay_reimburs_form= db.Column(db.LargeBinary, nullable=True)
    overlay_perdi_form= db.Column(db.LargeBinary, nullable=True)
    
    reimburs_form=db.Column(db.LargeBinary, nullable=True)
    perdi_form=db.Column(db.LargeBinary, nullable=True)
    all_process_finished = db.Column(db.Boolean,default=False,nullable=True)

    final_net_system_tot=db.Column(db.Numeric(12, 2), nullable=True)

    
    
    per_diem_forms = db.relationship(
        "PerDiemForm",
        uselist=False,
        cascade="all, delete-orphan"
    )

    receipt = db.relationship(
        "Receipt",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    comments = db.relationship(
        "Comment",
        backref="perdiem_request",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
 
    notifications = db.relationship(
        "Notification",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<perdiem {self.perdiem_code}>"

class PerDiemForm(db.Model):
    __tablename__ = "per_diem_forms"

    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("perdiem_requests.id"), nullable=False)
    mode = db.Column(db.String(20), nullable=False)

    form2_file=db.Column(db.LargeBinary, nullable=True)
    form2_mime = db.Column(db.String(50), nullable=True)

    daily_rate=db.Column(db.Numeric(12, 2), nullable=True)
    number_of_days=db.Column(db.Numeric(12, 2), nullable=True)
    perdiem_day_total=db.Column(db.Numeric(12, 2), nullable=True)
    
    travel_begin = db.Column(db.Date,nullable=True)
    travel_end = db.Column(db.Date,nullable=True)
    travel_begin_day_type = db.Column(db.String(10))
    travel_end_day_type = db.Column(db.String(10))

    employee_name = db.Column(db.String(100),nullable=True)
    employee_position = db.Column(db.String(100),nullable=True)
    employee_account = db.Column(db.Numeric(12, 2), nullable=True)
    employee_grade = db.Column(db.Numeric(12, 2), nullable=True)
    employee_office = db.Column(db.String(100),nullable=True)

    advance_taken = db.Column(db.Numeric(12, 2), nullable=True)
    perdiem_receipt_total=db.Column(db.Numeric(12, 2), nullable=True)
    Total_perdiem=db.Column(db.Numeric(12, 2), nullable=True)
    net_amount=db.Column(db.Numeric(12, 2), nullable=True)
    perdiem_currency=db.Column(db.String(100),nullable=True)

    pdf_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by_req = db.Column(db.Integer, db.ForeignKey("users.id"),nullable=True)
    approved_by_req_admin = db.Column(db.Integer, db.ForeignKey("users.id"),nullable=True)
    approved_at_req = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at_req_admin = db.Column(db.DateTime,nullable=True)

# -------------------------
# RECEIPTS
# -------------------------

class Receipt(db.Model):
    __tablename__ = "receipts"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("perdiem_requests.id"), nullable=False)
    mode = db.Column(db.String(20), nullable=False)  # "self" or "system"
    category = db.Column(db.String(50), nullable=False)  # 'form2', 'air_ticket', 'food', etc.
    file_data = db.Column(db.LargeBinary, nullable=False)
    file_mime = db.Column(db.String(50), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    ocr_text = db.Column(db.Text, nullable=True)
    category_total=db.Column(db.Numeric(12, 2), nullable=True)
# -------------------------
#COMMENT 
# -------------------------

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("perdiem_requests.id"), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="comments")


# -------------------------
# NOTIFICATIONS / INBOX
# -------------------------

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("perdiem_requests.id"))

    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    message = db.Column(db.String(255))
    link = db.Column(db.String(255))

    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -------------------------
# FINAL PDF RECORD
# -------------------------

class FinalPDF(db.Model):
    __tablename__ = "final_pdfs"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("perdiem_requests.id"))

    file_path = db.Column(db.String(255))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
