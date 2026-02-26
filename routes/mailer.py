import os
import smtplib
from email.message import EmailMessage
from flask_login import login_required

from flask import Blueprint, flash, send_file, abort

mailer_bp = Blueprint("mailer", __name__, url_prefix="/mailer")


def send_final_clearance_mail(username, rec_email, subject, body, body_color):


    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    #SENDER_EMAIL = "mismakmandefro1@gmail.com"
    #APP_PASSWORD = "zctyishnvouozxrn"

    SENDER_EMAIL = "supporrt.boaperdiem@gmail.com"
    APP_PASSWORD = "gzcgchtbyvylbigs"
    
    RECEIVER_EMAIL = rec_email

    print("[MAIL] Approval completed. Preparing email...", flush=True)
    print(f"[MAIL] From: {SENDER_EMAIL}", flush=True)
    print(f"[MAIL] To  : {RECEIVER_EMAIL}", flush=True)


    try:
        recipient = rec_email

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient
    
        msg.add_alternative(f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <p>Dear<strong> {username},</strong></p>
            <p style="color: {body_color};">{body}</p>
            <p><br><br>Kind Regards,<br>BOA Perdiem System</p>
        </body>
        </html>
        """, subtype='html')

        #print(f"[STEP] Attaching PDF: {pdf_path}...")

        '''with open(pdf_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="pdf",
                filename=os.path.basename(pdf_path)
            )'''
        print(f"[STEP] Email sent successfully.")

        print(f"[STEP] Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            print(f"[STEP] Starting TLS...")
            server.starttls()
            print(f"[STEP] Logging in as {SENDER_EMAIL}...")
            server.login(SENDER_EMAIL, APP_PASSWORD)
            print(f"[STEP] Sending email to {recipient}...")
            server.send_message(msg)
            print(f"[STEP] Email sent successfully to {recipient}!")
        flash("email sent sucessfully","success")

    except Exception as e:
        flash(str(e),"danger")
 
        print("[MAIL][ERROR] Email failed:", str(e), flush=True)


def notify_super_and_user(user, subject, body, body_color="#0d6efd"):
    
    try:

        from models import User

    
        super_admins = User.query.filter_by(role="SUPER_ADMIN").all()

        recipients = []

    
        for admin in super_admins:
            if admin.email:
                recipients.append(admin.email)

    
        if user.email and user.email not in recipients:
            recipients.append(user.email)


        for email in recipients:
            send_final_clearance_mail(
                username=user.username,
                rec_email=email,
                subject=subject,
                body=body,
                body_color=body_color
        
            )
        flash("email sent sucessfully","success")
    except Exception as e:
        flash(str(e),"danger")
 
        print("[MAIL][ERROR] Email failed:", str(e), flush=True)

def send_mail_with_attachment(username, rec_email, subject, body, body_color, attachment_path):

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    SENDER_EMAIL = "mismakmandefro1@gmail.com"
    APP_PASSWORD = "zctyishnvouozxrn"

    print("[MAIL] Preparing email with attachment...", flush=True)
    print(f"[MAIL] To: {rec_email}", flush=True)

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = rec_email

        # HTML Body
        msg.add_alternative(f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <p>Dear <strong>{username}</strong>,</p>
            <p style="color:{body_color};">{body}</p>
            <p><br>Kind Regards,<br>BOA Perdiem System</p>
        </body>
        </html>
        """, subtype="html")

        # 🔥 Attach PDF
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="pdf",
                    filename=os.path.basename(attachment_path)
                )
            print("[MAIL] Attachment added:", attachment_path)
        else:
            print("[MAIL] Attachment not found!")

        # Send Email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)

        print("[MAIL] Email with attachment sent successfully!")
        flash("email sent sucessfully","success")

    except Exception as e:
        flash(str(e),"danger")
        print("[MAIL][ERROR] Attachment email failed:", str(e), flush=True)

def send_finance_forms_mail(username, rec_email, subject, body, body_color,
                            reimburs_file=None, perdi_file=None):

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    SENDER_EMAIL = "mismakmandefro1@gmail.com"
    APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = rec_email

        # HTML BODY
        msg.add_alternative(f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <p>Dear <strong>{username}</strong>,</p>
            <p style="color:{body_color};">{body}</p>
            <p><br>Kind Regards,<br>BOA Perdiem System</p>
        </body>
        </html>
        """, subtype="html")

        # ----------------------------
        # Attach Reimbursement Form
        # ----------------------------
        if reimburs_file:
            msg.add_attachment(
                reimburs_file,
                maintype="application",
                subtype="pdf",
                filename="Reimbursement_Form.pdf"
            )

        # ----------------------------
        # Attach Perdiem Form
        # ----------------------------
        if perdi_file:
            msg.add_attachment(
                perdi_file,
                maintype="application",
                subtype="pdf",
                filename="Perdiem_Form.pdf"
            )

        # SEND
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)

        print("[MAIL] Finance forms email sent successfully!")

    except Exception as e:
        print("[MAIL][ERROR] Finance email failed:", str(e))