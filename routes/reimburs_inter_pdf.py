from flask import Blueprint, send_file, abort
from flask_login import login_required
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
import os
from io import BytesIO
from models import (
    PerdiemRequest,
    PerDiemForm,
    Receipt,
)
from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, redirect, url_for, abort, current_app
from extensions import db   


reimb_inter_pdf_bp = Blueprint("reimb_inter_pdf", __name__, url_prefix="/reimb_inter_pdf")

@reimb_inter_pdf_bp.route("/perdiem/<int:request_id>")
@login_required
def generate_reimb_req_pdf(request_id):

    perdiem = PerdiemRequest.query.get_or_404(request_id)

    if current_user.role == "REQUESTOR" and perdiem.requestor_id != current_user.id:
        abort(500)

    perdiem.r_pdf_path_req=None
    '''if perdiem.r_pdf_path_req and os.path.exists(perdiem.r_pdf_path_req):
        return send_file(
            perdiem.r_pdf_path_req,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=os.path.basename(perdiem.r_pdf_path_req)
        )'''

    if not all([
        perdiem.per_diem_forms,
        perdiem.receipt,
       
    ]):
        abort(403)

    
    '''BASE_PDF = os.path.join(
        current_app.root_path,
        "static/generated/reimbrusment-perdiem.perdiem_code}.pdf"
    )'''

    OVERLAY_PDF = os.path.join(
        current_app.root_path,
        "static/tmp",
        f"overlay_reimbrusment_{perdiem.perdiem_code}.pdf"
    )

    FINAL_PDF = os.path.join(
        current_app.root_path,
        "static/generated",
        f"reimbrusment-{perdiem.perdiem_code}.pdf"
    )

    os.makedirs(os.path.dirname(OVERLAY_PDF), exist_ok=True)
    os.makedirs(os.path.dirname(FINAL_PDF), exist_ok=True)


    c = canvas.Canvas(OVERLAY_PDF, pagesize=(595, 842))  # A4
    c.setFont("Helvetica", 9)


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


    if (u_role == "INTERMEDIATE_APPROVER"):
        draw_signature(u_name,"INTERMEDIATE_APPROVER", 295, 440)
        c.drawString(248, 443, perdiem.created_at.strftime("%d-%m-%Y"))


    c.save()

  

    base_pdf = PdfReader(BytesIO(perdiem.reimburs_form))  # ✅ read PDF from binary

    overlay_pdf = PdfReader(OVERLAY_PDF)

    writer = PdfWriter()
    base_page = base_pdf.pages[0]
    base_page.merge_page(overlay_pdf.pages[0])
    writer.add_page(base_page)

    with open(FINAL_PDF, "wb") as f:
        writer.write(f)
    with open(FINAL_PDF, "rb") as pdf_file:
        perdiem.reimburs_form = pdf_file.read()

    #perdiem.status = "APPROVED"
    perdiem.r_pdf_path_req = FINAL_PDF
    db.session.commit()

    return send_file(
        FINAL_PDF,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=os.path.basename(FINAL_PDF)
    )