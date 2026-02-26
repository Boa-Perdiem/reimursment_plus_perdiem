import smtplib
from email.message import EmailMessage
import os

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "mismakmandefro1@gmail.com"
APP_PASSWORD = "zctyishnvouozxrn"
# APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

def name_to_email(full_name):
    print(f"[STEP] Converting full name '{full_name}' to email address...")
    email = full_name.lower().replace(" ", ".") + "@bankofabyssinia.com"
    print(f"[STEP] Converted email: {email}")
    return email

def send_clearance_email(full_name, pdf_path):
    print(f"[STEP] Preparing to send clearance email to '{full_name}'...")
    recipient = name_to_email(full_name)

    msg = EmailMessage()
    msg["Subject"] = f"Exit Clearance Approval – {full_name}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient
    msg.set_content(f"""Dear {full_name},

Your exit clearance request has been fully approved.
Please find the approved clearance document attached.

Regards,
BOA Exit Clearance System
""")
    print(f"[STEP] Email message created with subject: '{msg['Subject']}'")

    print(f"[STEP] Attaching PDF: {pdf_path}...")
    with open(pdf_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(pdf_path)
        )
    print(f"[STEP] PDF attached successfully.")

    print(f"[STEP] Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}...")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        print(f"[STEP] Starting TLS...")
        server.starttls()
        print(f"[STEP] Logging in as {SENDER_EMAIL}...")
        server.login(SENDER_EMAIL, APP_PASSWORD)
        print(f"[STEP] Sending email to {recipient}...")
        server.send_message(msg)
        print(f"[STEP] Email sent successfully to {recipient}!")

# Example usage:
# send_clearance_email("John Doe", "approved_clearance.pdf")
