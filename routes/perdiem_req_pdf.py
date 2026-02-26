from flask import Blueprint, send_file, abort,flash
from flask_login import login_required
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
import os

from models import (
    PerdiemRequest,
    PerDiemForm,
    Receipt,
)
from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, redirect, url_for, abort, current_app
from extensions import db   

perdiem_req_pdf_bp = Blueprint("perdiem_req_pdf", __name__, url_prefix="/perdiem_req_pdf")
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")



@perdiem_req_pdf_bp.route("/perdiem/<int:request_id>")

def generate_per_req_trueperdiem_pdf(request_id):

    perdiem = PerdiemRequest.query.get_or_404(request_id)
    perdiem_f = PerDiemForm.query.get_or_404(request_id)

    print("hey i am smart")

    if current_user.role == "REQUESTOR" and perdiem.requestor_id != current_user.id:
        abort(500)

    # ---------------------------------------------------
    # IF PDF ALREADY GENERATED → SERVE IT SAFELY
    # ---------------------------------------------------
    perdiem.pdf_path=None
    if perdiem.pdf_path and os.path.exists(perdiem.pdf_path):
        return send_file(
            perdiem.pdf_path,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=os.path.basename(perdiem.pdf_path)
        )

    # ---------------------------------------------------
    # ENSURE ALL SECTIONS ARE APPROVED
    # ---------------------------------------------------
    if not all([
        perdiem.per_diem_forms,
        perdiem.receipt,
       
    ]):
        abort(403)


    OVERLAY_PDF = os.path.join(
        current_app.root_path,
        "static/tmp",
        f"overlayperdiem_{perdiem.perdiem_code}.pdf"
    )

    FINAL_PDF = os.path.join(
        current_app.root_path,
        "static/generated",
        f"perdiem{perdiem.perdiem_code}.pdf"
    )

    os.makedirs(os.path.dirname(OVERLAY_PDF), exist_ok=True)
    os.makedirs(os.path.dirname(FINAL_PDF), exist_ok=True)


    c = canvas.Canvas(OVERLAY_PDF, pagesize=(595, 842))  # A4
    c.setFont("Times-Roman", 11)


    u_name=current_user.username
    u_role=current_user.role

    # ---------- SIGNATURES (DIRECT STATIC FILES) ----------
    from reportlab.lib.utils import ImageReader
    import io
    def draw_signature(u_name, u_role, x, y):

        signature_data = current_user.signature
        if signature_data:
            
            sig_image = ImageReader(io.BytesIO(signature_data))
            c.drawImage(sig_image, x, y, width=60, height=20, mask='auto')

        
        
    if (u_role == "REQUESTOR_ADMIN"):    
        c.setFont("Times-Roman", 11) 
        c.drawString(423, 211, perdiem_f.created_at.strftime("%d-%m-%Y"))
        c.drawString(175, 211, current_user.username)
        draw_signature(u_name,"REQUESTOR_ADMIN", 315, 209)
    
    
        
    c.save()

    # ------------------------------
    # MERGE WITH TEMPLATE
    # ------------------------------
    base_pdf = PdfReader(BytesIO(perdiem.perdi_form))
    overlay_pdf = PdfReader(OVERLAY_PDF)

    writer = PdfWriter()
    base_page = base_pdf.pages[0]
    base_page.merge_page(overlay_pdf.pages[0])
    writer.add_page(base_page)

    with open(FINAL_PDF, "wb") as f:
        writer.write(f)
    with open(FINAL_PDF, "rb") as pdf_file:
        perdiem.perdi_form = pdf_file.read()

    #perdiem.status = "APPROVED"
    perdiem.pdf_path = FINAL_PDF
    db.session.commit()

    return send_file(
        FINAL_PDF,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=os.path.basename(FINAL_PDF)
    )

from io import BytesIO
from flask import send_file
from reportlab.lib.units import inch

def draw_wrapped_text_custom(
    c,
    text,
    y_start,
    x_positions,
    max_widths,
    line_height,
    font_name="Helvetica",
    font_size=9,
):
    """
    Draw text character by character with:
    - custom starting X for each line
    - custom max width for each line
    - custom line height
    - y_start = top of first line
    """
    c.setFont(font_name, font_size)
    y = y_start
    text_index = 0  # pointer into text

    for line_num, (x_start, max_width) in enumerate(zip(x_positions, max_widths)):
        x = x_start
        while text_index < len(text):
            char = text[text_index]
            char_width = c.stringWidth(char, font_name, font_size)
            # if next char exceeds max width, move to next line
            if x + char_width > x_start + max_width:
                break  # go to next line
            c.drawString(x, y, char)
            x += char_width
            text_index += 1
        y -= line_height  # move Y down for next line
        if text_index >= len(text):
            break  # finished text


@perdiem_req_pdf_bp.route("/perdiem/db/<int:request_id>")
@login_required
def view_perdiem_pdf_from_db(request_id):
    perdiem = PerdiemRequest.query.get_or_404(request_id)

    if not perdiem.perdi_form:
        abort(404)

    return send_file(
        BytesIO(perdiem.perdi_form),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"perdiem_{perdiem.perdiem_code}.pdf"
    )
'''
def draw_wrapped_text_char(c, text, x_start, y_start, max_width, line_height, font_name="Helvetica", font_size=9):
    c.setFont(font_name, font_size)
    x = x_start
    y = y_start

    for char in text:
     
        char_width = c.stringWidth(char, font_name, font_size)
       
        if x + char_width > x_start + max_width:
           
            y -= line_height
            x = x_start  
        
        c.drawString(x, y, char)
        x += char_width  '''