from flask import Blueprint, render_template, request, redirect, url_for, flash,abort
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db

from datetime import datetime
from PIL import Image
import numpy as np
import io

from models import User
from routes import mailer

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# -------------------------
# REGISTER PAGE (GET)
# -------------------------
DISTRICTS = ["ADAMA", "BAHIR DAR", "CENTRAL ADDIS", "DESSIE", "DIRE DAWA",
             "EAST ADDIS", "HAWASSA", "JIMMA", "MEKELLE", "WEST ADDIS"]

@auth_bp.route("/register", methods=["GET"])
def register_page():
    #
    requestor_admins = User.query.filter_by(role="REQUESTOR_ADMIN").all()
    managerial_approver_exists = User.query.filter_by(role="MANAGERIAL_APPROVER").first() is not None
    managerial_delegate_approver_exists = User.query.filter_by(role="MANAGERIAL_DELEGATE").first() is not None
    final_approver_exists = User.query.filter_by(role="FINAL_APPROVER").first() is not None
    return render_template("register.html",
                           managerial_approver_exists=managerial_approver_exists,
                           final_approver_exists=final_approver_exists,
                           managerial_delegate_approver_exists=managerial_delegate_approver_exists,
                           requestor_admins=requestor_admins,
                           districts=DISTRICTS)

# -------------------------
# LOGIN
# -------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required", "danger")
            return render_template("login.html")

        user = User.query.filter_by(username=username).first()

        # -------------------------
        # USER NOT FOUND
        # -------------------------
        if user is None:
            flash("Invalid username or password", "danger")
            print("login failed in here")
            return render_template("login.html")

        # -------------------------
        # NOT APPROVED
        # -------------------------
        if not user.is_approved:
            flash("Account not approved yet", "warning")
            return render_template("login.html")

        # -------------------------
        # ACCOUNT DISABLED
        # -------------------------
        if not user.is_active:
            flash("Account is disabled", "danger")
            return render_template("login.html")

        # -------------------------
        # WRONG PASSWORD
        # -------------------------
        if not user.check_password(password):
            user.failed_attempts += 1
            db.session.commit()

            flash("Invalid username or password", "danger")
         
            return render_template("login.html")

        # -------------------------
        # SUCCESS LOGIN
        # -------------------------
        user.failed_attempts = 0
        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user)
        return redirect(url_for("dashboard.index"))

    return render_template("login.html")


# -------------------------
# REMOVE BACKGROUND FUNCTION
# -------------------------

from PIL import Image
import io

def remove_background(image_file):
    # Read input image
    input_image = Image.open(image_file).convert("RGBA")

    # Remove background using AI model
    output_image = remove(input_image)

    # Save to memory
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG")
    output_buffer.seek(0)

    return output_buffer



# -------------------------
# UPLOAD SIGNATURE
# -------------------------
@auth_bp.route("/upload-signature", methods=["POST"])
@login_required
def upload_signature():

    file = request.files.get("signature")

    if not file:
        flash("signature is Required!", "danger")
        return redirect(url_for("dashboard.index"))
    

    if file.mimetype not in ["image/png", "image/jpeg"]:
        flash("Only PNG or JPG allowed", "danger")
        return redirect(url_for("dashboard.index"))

    file.stream.seek(0)
    processed = remove_background(file)

    current_user.signature = processed.read()
    current_user.signature_mime = "image/png"

    db.session.commit()

    flash("Signature uploaded successfully", "success")
    return redirect(url_for("dashboard.index"))

import base64
import re

@auth_bp.route("/create-account", methods=["POST"])
def create_account():
    username = request.form.get("username", "").strip()
    email_input = request.form.get("email", "").strip()
    password = request.form.get("password")
    role = request.form.get("role")
    req_admin = request.form.get("req_admin")
    district_list = request.form.get("district_list")

    file = request.files.get("signature")
    drawn_signature = request.form.get("drawn_signature")

    # ===============================
    # Required Fields Validation
    # ===============================
    if not username or not password or not role:
        flash("All required fields must be filled.", "danger")
        return redirect(url_for("auth.register_page"))

    # ===============================
    # Signature Handling (Upload OR Draw)
    # ===============================
    signature_bytes = None
    signature_mime = None

    # 1️⃣ If drawn signature exists
    if drawn_signature:
        try:
            header, encoded = drawn_signature.split(",", 1)
            signature_bytes = base64.b64decode(encoded)
            signature_mime = "image/png"
        except Exception:
            flash("Invalid drawn signature.", "danger")
            return redirect(url_for("auth.register_page"))

    # 2️⃣ If uploaded file exists AND has filename
    elif file and file.filename:
        try:
            file.stream.seek(0)
            processed = remove_background(file)
            signature_bytes = processed.read()
            signature_mime = file.mimetype
        except Exception:
            flash("Invalid uploaded signature image.", "danger")
            return redirect(url_for("auth.register_page"))

    else:
        flash("Signature is required (upload or draw).", "danger")
        return redirect(url_for("auth.register_page"))

    # ===============================
    # Auto Email Generation
    # ===============================
    if not email_input:
        clean_name = re.sub(r'[^a-zA-Z\s]', '', username)
        email_prefix = ".".join(clean_name.lower().split())
        email = f"{email_prefix}@bankofabyssinia.com"
    else:
        email = email_input.lower()

    # ===============================
    # Duplicate Checks
    # ===============================
    if User.query.filter_by(username=username).first():
        flash("Username already exists.", "danger")
        return redirect(url_for("auth.register_page"))

    if User.query.filter_by(email=email).first():
        flash("Email already exists.", "danger")
        return redirect(url_for("auth.register_page"))

    # ===============================
    # Create User
    # ===============================
    user = User(
        username=username,
        email=email,
        role=role,
        signature=signature_bytes,
        signature_mime=signature_mime,
        is_approved=False
    )

    user.set_password(password)

    # ===============================
    # Role Logic
    # ===============================
    if role == "REQUESTOR":
        user.req_admin = req_admin

        admin_user = User.query.filter_by(username=req_admin).first()
        if admin_user:
            existing = admin_user.my_requestors.split(",") if admin_user.my_requestors else []
            if username not in existing:
                existing.append(username)
            admin_user.my_requestors = ",".join(existing)

    elif role == "INTERMEDIATE_APPROVER":
        user.district_list = district_list

    db.session.add(user)
    db.session.commit()

    subject = "New Account Created - Awaiting Approval"
    body = f"""
    Username: {user.username}
    Role: {user.role}
    Email: {user.email}

    The account is waiting for SUPER ADMIN approval.
    """

    print(">>> CREATE ACCOUNT EMAIL FUNCTION CALLED")
    mailer.notify_super_and_user(
        user,
        subject,
        body,
        body_color="#FFA500"   # orange
    )

    flash("Account created. Await approval.", "success")
    return redirect(url_for("auth.login"))


# -------------------------
# LOGOUT
# -------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("auth.login"))



@auth_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        current_pw = request.form.get("current_password")
        new_pw = request.form.get("new_password")

        if not current_user.check_password(current_pw):
            flash("Current password incorrect","danger")

            return redirect(url_for("dashboard.index"))

        current_user.set_password(new_pw)
        current_user.password_changed_at = datetime.utcnow()
        db.session.commit()

        subject = "Password Changed Successfully"
        body = f"""
        Hello {current_user.username},

        Your password was changed successfully.

        If this was not you, contact SUPER ADMIN immediately.
        """

        mailer.notify_super_and_user(
            current_user,
            subject,
            body,
            "#0dcaf0"
)

        flash("Password updated successfully","success")
        return redirect(url_for("dashboard.index"))
    
    # GET method → render a form
    return render_template("change_password.html")
