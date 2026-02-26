from flask import Blueprint, send_file, abort,flash
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

perdiem_pdf_bp = Blueprint("perdiem_pdf", __name__, url_prefix="/perdiem_pdf")
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")



@perdiem_pdf_bp.route("/perdiem/<int:request_id>")

def generate_trueperdiem_pdf(request_id):

    perdiem = PerdiemRequest.query.get_or_404(request_id)
    perdiem_f = PerDiemForm.query.get_or_404(request_id)
    base = BaseForms.get_or_init(current_app)

    if current_user.role not in ["REQUESTOR", "REQUESTOR_ADMIN"] and perdiem.requestor_id != current_user.id:
        abort(500)


    if (perdiem.mode == "SELF") or (perdiem.mode == "self"):

        # Form 2 is 100% mandatory
        if not perdiem_f.form2_file:
            abort(400, "Form 2 PDF is required for Self Per Diem")

        perdiem.perdi_form = perdiem_f.form2_file
        db.session.commit()

       
        return send_file(
            BytesIO(perdiem_f.form2_file),
            mimetype="application/pdf",
            as_attachment=False,
            download_name=f"form2_{perdiem.perdiem_code}.pdf"
        )
    else:

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

        BASE_PDF = os.path.join(
            current_app.root_path,
            "static/pdf_templates/Per_Diem_Form.pdf"
        )

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

        #c.drawString(216, 688, perdiem.district)
        if(perdiem.district =="BAHIR DAR"):
            c.drawString(244, 688, perdiem.district)
        elif(perdiem.district =="CENTRAL ADDIS") or (perdiem.district =="HAWASSA") or (perdiem.district =="MEKELLE"):
            c.drawString(216, 688, perdiem.district)
        elif(perdiem.district =="WEST ADDIS") or (perdiem.district =="EAST ADDIS"):
            c.drawString(240, 688, perdiem.district)
        elif(perdiem.district =="DESSIE"):
            c.drawString(267, 688, perdiem.district)
        elif(perdiem.district =="DIRE DAWA"):
            c.drawString(242, 688, perdiem.district)
        elif(perdiem.district =="ADAMA") or (perdiem.district =="JIMMA"):
            c.drawString(262, 688, perdiem.district)
    

        '''if(perdiem.district =="BAHIR DAR"):
            c.drawString(92, 560, "BJR-ADD Round Trip")
        elif(perdiem.district =="MEKELLE"):
            c.drawString(92, 560, "MQX-ADD Round Trip")
        elif(perdiem.district =="DESSIE"):
            c.drawString(92, 560, "DSE-ADD Round Trip")
        elif(perdiem.district =="DIRE DAWA"):
            c.drawString(192, 5603, "DIRE-ADD Round Trip")
        elif(perdiem.district =="HAWASSA"):
            c.drawString(92, 5603, "AWA-ADD Round Trip")
        elif(perdiem.district =="JIMMA"):
            c.drawString(92, 560, "JIM-ADD Round Trip")
        else:
            c.drawString(92, 560, "Abroad")'''
        
        
        

        c.drawString(90, 636, str(perdiem_f.employee_name))
        c.drawString(230, 636, str(perdiem_f.employee_office))
        c.drawString(410, 636, str(perdiem_f.employee_position))

        #c.drawString(90, 560, str(perdiem_f.country))
        date_obj_begin = datetime.strptime(str(perdiem_f.travel_begin), "%Y-%m-%d")
        travel_begin_in_words = date_obj_begin.strftime("%b %d, %Y")  
        c.drawString(197, 560, travel_begin_in_words)
        date_obj_end = datetime.strptime(str(perdiem_f.travel_end), "%Y-%m-%d")
        travel_end_in_words = date_obj_end.strftime("%b %d, %Y")  
        c.drawString(304, 560, travel_end_in_words)


        

        '''c.drawString(356, 467, str(perdiem_f.air_currency))
        c.drawString(356, 454, str(int(perdiem_f.food_currency)))
        c.drawString(356, 441, str(perdiem_f.bed_currency))
        c.drawString(356, 428, str(perdiem_f.fuel_currency))
        c.drawString(356, 415, str(perdiem_f.other_currency))'''

        '''Receipt_R = Receipt.query.filter_by(request_id=request_id).all()
        print(Receipt_R)'''

        from sqlalchemy import func

        air_receipt = Receipt.query.filter_by(
            request_id=request_id,
            category="air_ticket"
        ).first()

        food_receipt = Receipt.query.filter_by(
            request_id=request_id,
            category="food"
        ).first()

        bed_receipt = Receipt.query.filter_by(
            request_id=request_id,
            category="bedroom"
        ).first()

        fuel_receipt = Receipt.query.filter_by(
            request_id=request_id,
            category="fuel_transport"
        ).first()

        other_receipt = Receipt.query.filter_by(
            request_id=request_id,
            category="other"
        ).first()


        air_total   = air_receipt.category_total   if air_receipt else 0
        food_total  = food_receipt.category_total  if food_receipt else 0
        bed_total   = bed_receipt.category_total   if bed_receipt else 0
        fuel_total  = fuel_receipt.category_total  if fuel_receipt else 0
        other_total = other_receipt.category_total if other_receipt else 0

        Receipt_total_perdiem = air_total + food_total + bed_total + fuel_total + other_total

        
        c.drawString(437, 467, format_number(air_total))
        c.drawString(437, 454, format_number(food_total))
        c.drawString(437, 441, format_number(bed_total))
        c.drawString(437, 428, format_number(fuel_total))
        c.drawString(437, 415, format_number(other_total))
        c.drawString(437, 402, format_number(Receipt_total_perdiem))
        



        c.drawString(170, 376, str(perdiem_f.employee_name))
        c.drawString(122, 351, perdiem.created_at.strftime("%d-%m-%Y")) 



        c.setFont("Times-Roman", 9)
        name = perdiem_f.employee_name

        if isinstance(name, str):
            parts = name.strip().split()
            first_name = parts[0] if parts else ""
        else:
            first_name = ""

        c.drawString(118, 265, first_name)

        def safe_int(value, default=0):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        
        daily_rate = int(perdiem_f.daily_rate) if perdiem_f.daily_rate is not None else 0
        c.drawString(207, 265, str(safe_int(perdiem_f.daily_rate)))    
        c.drawString(241, 265, str(perdiem_f.number_of_days))
        c.drawString(275, 265, format_number(perdiem_f.perdiem_day_total))
        c.drawString(321, 265, format_number(Receipt_total_perdiem))

        Total_perdiem = perdiem_f.perdiem_day_total + Receipt_total_perdiem

        c.drawString(371, 265, format_number(Total_perdiem))
        c.drawString(420, 265, format_number(perdiem_f.advance_taken))
        net_amount = Total_perdiem - perdiem_f.advance_taken
        c.drawString(466, 265, format_number(net_amount))
        
        perdiem.birr_amount=net_amount
        db.session.commit()
        print(perdiem.birr_amount)


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
            c.setFont("Times-Roman", 11)
            c.drawString(175, 236, current_user.username)
            draw_signature(u_name,"REQUESTOR", 315, 233)
            c.drawString(423, 236, perdiem_f.created_at.strftime("%d-%m-%Y"))
            

            
        c.save()

        # ------------------------------
        # MERGE WITH TEMPLATE
        # ------------------------------


        base_pdf = PdfReader(BytesIO(base.base_perdi))
      

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
        flash("System Auto-Generated the Perdiem Form Perfectly", "success")

        return send_file(
            FINAL_PDF,
            mimetype="application/pdf",
            as_attachment=False,
            
            download_name=os.path.basename(FINAL_PDF)
            
        )

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


@perdiem_pdf_bp.route("/perdiem/db/<int:request_id>")
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


def draw_total_if_exists(c, x, y, value):
    if not value:
        return

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return

    if numeric_value == 0:
        return

    if numeric_value.is_integer():
        c.drawString(x, y, str(int(numeric_value)))
    else:
        c.drawString(x, y, f"{numeric_value:.2f}")

def format_number(value):
    if not value:
        return ""
    return f"{float(value):,.2f}"






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