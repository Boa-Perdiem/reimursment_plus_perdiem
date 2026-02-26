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
    BaseForms,
)
from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, redirect, url_for, abort, current_app
from extensions import db   

reimb_pdf_bp = Blueprint("reimb_pdf", __name__, url_prefix="/reimb_pdf")
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")





@reimb_pdf_bp.route("/perdiem/<int:request_id>")
@login_required
def generate_perdiem_pdf(request_id):

    perdiem = PerdiemRequest.query.get_or_404(request_id)
    base = BaseForms.get_or_init(current_app)



    if current_user.role not in ["REQUESTOR", "REQUESTOR_ADMIN"] and perdiem.requestor_id != current_user.id:
        abort(500)

    perdiem.r_pdf_path=None
    
    if not all([
        perdiem.per_diem_forms,
        perdiem.receipt,
    ]):
        abort(403)

    
    
    BASE_PDF = os.path.join(
        current_app.root_path,
        "static/pdf_templates/reimbursement_form.pdf"
    )

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


    c.drawString(443, 676, perdiem.created_at.strftime("%d-%m-%Y"))
    #c.drawString(128, 661, perdiem.from_)

    text_amtwords = perdiem.from_

    x_positions = [128, 90]     
    max_widths = [165, 203]       
    line_height = 12
    y_start = 661                      

    draw_wrapped_text_custom(
        c,
        text_amtwords,
        y_start,
        x_positions,
        max_widths,
        line_height
    )

    c.drawString(370, 661, perdiem.contra)
    #c.drawString(370, 649, perdiem.contra_name)

    text_from = perdiem.contra_name

    x_positions = [370, 370]     
    max_widths = [170, 170]       
    line_height = 12
    y_start = 649                      

    draw_wrapped_text_custom(
        c,
        text_from,
        y_start,
        x_positions,
        max_widths,
        line_height
    )

    c.drawString(145, 633, perdiem.district)

    ##These values needs to be changed for production

    if(perdiem.district =="BAHIR DAR"):
       District_code="298"+ " ("+"BDD"
    elif(perdiem.district =="CENTRAL ADDIS"):
        District_code="347"+ " ("+"CAD"
    elif(perdiem.district =="WEST ADDIS"):
        District_code="302"+ " ("+"WAD"
    elif(perdiem.district =="EAST ADDIS"):
        District_code="301"+ " ("+"EAD"
    elif(perdiem.district =="HAWASSA"):
        District_code="299"+ " ("+"HD"
    elif(perdiem.district =="DESSIE"):
        District_code="350"+ " ("+"DD"
    elif(perdiem.district =="DIRE DAWA"):
        District_code="351"+ " ("+"DDD"
    elif(perdiem.district =="ADAMA"):
        District_code="349"+ " ("+"AD"
    elif(perdiem.district =="MEKELLE"):
        District_code="300"+ " ("+"MD"
    elif(perdiem.district =="JIMMA"):
        District_code="348"+ " ("+"JD"

    
    c.drawString(90, 620, "ETB1260000010"+ District_code +" Claim)")

    #c.drawString(145, 603, perdiem.send_to)

    text_amtwords = perdiem.send_to

    x_positions = [145, 90]     
    max_widths = [148, 203]       
    line_height = 12
    y_start = 603                      

    draw_wrapped_text_custom(
        c,
        text_amtwords,
        y_start,
        x_positions,
        max_widths,
        line_height
    )


    c.drawString(340, 591, str("{:,.2f}".format(perdiem.birr_amount)) )

    #c.drawString(200, 558, perdiem.amount_in_words)

    text_amtwords = perdiem.amount_in_words

    x_positions = [200, 90]     
    max_widths = [321, 431]       
    line_height = 18
    y_start = 558                      

    draw_wrapped_text_custom(
        c,
        text_amtwords,
        y_start,
        x_positions,
        max_widths,
        line_height
    )

    #c.drawString(203, 524, perdiem.reason_for_claim)

    text_claim = perdiem.reason_for_claim

    x_positions = [206, 90, 90]     
    max_widths = [315, 431, 431]       
    line_height = 18
    y_start = 524                      

    draw_wrapped_text_custom(
        c,
        text_claim,
        y_start,
        x_positions,
        max_widths,
        line_height
    )


    '''draw_wrapped_text_char(
    c,
    perdiem.reason_for_claim,
    x_start=203,
    y_start=524,
    max_width=300,
    line_height=14
)'''


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

    if (u_role == "REQUESTOR"):
        draw_signature(u_name,"REQUESTOR", 90, 440)


    '''if (u_role == "REQUESTOR_ADMIN"):
        draw_signature(u_name,"REQUESTOR_ADMIN", 160, 440)
    if (u_role == "INTERMEDIATE_APPROVER"):
        draw_signature(u_name,"INTERMEDIATE_APPROVER", 295, 440)
        c.drawString(248, 442, perdiem.created_at.strftime("%d-%m-%Y"))
    if (u_role == "MANAGERIAL_APPROVER" or u_role == "FINAL_APPROVER"):
        draw_signature(u_name,"FINAL_APPROVER", 430, 440)'''

    c.save()

    # ------------------------------
    # MERGE WITH TEMPLATE
    # ------------------------------
  

    '''if not base.base_reimburs:
        with open(BASE_PDF, "rb") as f:
            base.base_reimburs = f.read()

    if not base.base_reimburs:
        abort(500)  '''

    base_pdf = PdfReader(BytesIO(base.base_reimburs))

    
    overlay_pdf = PdfReader(OVERLAY_PDF)

    writer = PdfWriter()
    base_page = base_pdf.pages[0]
    base_page.merge_page(overlay_pdf.pages[0])
    writer.add_page(base_page)


    with open(FINAL_PDF, "wb") as f:
        writer.write(f)
    with open(FINAL_PDF, "rb") as pdf_file:
        perdiem.reimburs_form = pdf_file.read()

    

    overlay_writer = PdfWriter()
    for page in overlay_pdf.pages:
        overlay_writer.add_page(page)

    overlay_stream = BytesIO()
    overlay_writer.write(overlay_stream)
    perdiem.overlay_reimburs_form = overlay_stream.getvalue() 

    #perdiem.status = "APPROVED"
    perdiem.r_pdf_path = FINAL_PDF
    db.session.commit()

    return send_file(
        FINAL_PDF,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=os.path.basename(FINAL_PDF)
    )

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


@reimb_pdf_bp.route("/perdiem/db/<int:request_id>")
@login_required
def view_perdiem_pdf_from_db(request_id):
    perdiem = PerdiemRequest.query.get_or_404(request_id)

    if not perdiem.reimburs_form:
        abort(404)

    return send_file(
        BytesIO(perdiem.reimburs_form),
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