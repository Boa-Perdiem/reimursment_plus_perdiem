from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import User
from datetime import datetime
import base64

from routes import mailer

super_admin_bp = Blueprint("super_admin", __name__, url_prefix="/super-admin")


@super_admin_bp.route("/")
@login_required
def super_admin_page():
    if current_user.role != "SUPER_ADMIN":
        abort(403)

    users = User.query.all()

    for user in users:
        if user.signature:  
            user.signature_b64 = base64.b64encode(user.signature).decode('utf-8')
            user.signature_mime = 'image/png'  
        else:
            user.signature_b64 = None
            user.signature_mime = None

    return render_template("super_user.html", users=users)


# Approve a user (sets is_approved True)
@super_admin_bp.route("/approve/<int:user_id>", methods=["POST"])
@login_required
def approve_user(user_id):
    if current_user.role != "SUPER_ADMIN":
        abort(403)
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()

    subject = "Account Approved"
    body = f"""
    Hello {user.username},

    Your account has been approved by SUPER ADMIN.
    You can now log in to the system.
    """

    mailer.notify_super_and_user(
        user,
        subject,
        body,
        body_color="#28a745"   # green
    )
    flash(f"User {user.username} approved", "success")
    return redirect(url_for("super_admin.super_admin_page"))


@super_admin_bp.route("/reject/<int:user_id>", methods=["POST"])
@login_required
def reject_user(user_id):
    if current_user.role != "SUPER_ADMIN":
        abort(403)

    user = User.query.get_or_404(user_id)

    username = user.username
    user_email = user.email  

    for comment in user.comments:
        db.session.delete(comment)

    # Delete user
    db.session.delete(user)
    db.session.commit()

    subject = "Account Rejected"
    body = f"""
    Hello {username},

    Your account request has been rejected by SUPER ADMIN.
    Please contact administration for more information.
    """

    # Since user is deleted, create temporary object
    class TempUser:
        def __init__(self, username, email):
            self.username = username
            self.email = email

    temp_user = TempUser(username, user_email)

    mailer.notify_super_and_user(
        temp_user,
        subject,
        body,
        body_color="#dc3545"   # red
    )

    flash(f"User {username} has been rejected and deleted", "warning")
    return redirect(url_for("super_admin.super_admin_page"))



# Activate a user account (sets is_active True)
@super_admin_bp.route("/activate/<int:user_id>", methods=["POST"])
@login_required
def activate_user(user_id):
    if current_user.role != "SUPER_ADMIN":
        abort(403)
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    subject = "Account Activated"
    body = f"""
    Hello {user.username},

    Your account has been activated.
    """

    mailer.notify_super_and_user(user, subject, body, "#198754")
    flash(f"User {user.username} activated", "success")
    return redirect(url_for("super_admin.super_admin_page"))


# Disable a user account (sets is_active False)
@super_admin_bp.route("/disable/<int:user_id>", methods=["POST"])
@login_required
def disable_user(user_id):
    if current_user.role != "SUPER_ADMIN":
        abort(403)
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    subject = "Account Disabled"
    body = f"""
    Hello {user.username},

    Your account has been disabled by SUPER ADMIN.
    """

    mailer.notify_super_and_user(user, subject, body, "#dc3545")
    flash(f"User {user.username} disabled", "info")
    return redirect(url_for("super_admin.super_admin_page"))


# Force password reset (sets a temporary password, e.g., username)
@super_admin_bp.route("/force-reset/<int:user_id>", methods=["POST"])
@login_required
def force_reset_password(user_id):
    if current_user.role != "SUPER_ADMIN":
        abort(403)
    user = User.query.get_or_404(user_id)
    temp_password = user.username  
    user.set_password(temp_password)
    user.password_changed_at = datetime.utcnow()
    db.session.commit()
    subject = "Password Reset by SUPER ADMIN"
    body = f"""
    Hello {user.username},

    Your password has been reset by SUPER ADMIN.

    Temporary password: {user.username}

    You must change it immediately after login.
    """

    mailer.notify_super_and_user(user, subject, body, "#ffc107")
    flash(f"Password reset for {user.username}", "warning")
    print("Password reset for "+ user.username +" warning")
    return redirect(url_for("super_admin.super_admin_page"))
