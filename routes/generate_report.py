from flask import Blueprint, flash, send_file, request, redirect, url_for
from flask_login import login_required
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from collections import defaultdict
from datetime import datetime
import os
from  routes import mailer

from models import PerdiemRequest,User


generate_report_bp = Blueprint(
    "generate_report",
    __name__,
    url_prefix="/generate_report"
)


# =====================================================
# ROUTE: Generate + View Finance Report WITH DATE FILTER
# =====================================================
@generate_report_bp.route("/finance_report")
@login_required
def finance_report():

    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    # If user didn't select dates → go back
    if not start_date_str or not end_date_str:
        return redirect(url_for("finance_processor.finance_dashboard"))

    # Convert to datetime
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    # Include whole end day
    end_date = end_date.replace(hour=23, minute=59, second=59)

    requests = PerdiemRequest.query.filter(
        PerdiemRequest.status == "PROCESSED_BY_FINANCE",
        PerdiemRequest.created_at.between(start_date, end_date)
    ).all()

    grand_total = sum(float(r.birr_amount or 0) for r in requests)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_folder = "generated_reports"
    os.makedirs(report_folder, exist_ok=True)

    filename = os.path.join(
        report_folder,
        f"finance_processed_report_{timestamp}.pdf"
    )

    generate_finance_report(
        requests,
        grand_total,
        filename,
        start_date_str,
        end_date_str
    )

        # ======================================
    # SEND REPORT TO FINANCE USERS
    # ======================================

    finance_users = User.query.filter_by(role="FINANCE").all()

    for finance_user in finance_users:

        subject = "Finance Processed Report"

        body = f"""
        The finance processed report has been generated.<br><br>
        <strong>Period:</strong> {start_date_str} → {end_date_str}<br>
        <strong>Grand Total:</strong> {grand_total:,.2f} ETB<br><br>
        Please find the attached PDF report.
        """

        mailer.send_mail_with_attachment(
            username=finance_user.username,
            rec_email=finance_user.email,
            subject=subject,
            body=body,
            body_color="#1e3a8a",
            attachment_path=filename
        )

    return send_file(
        filename,
        mimetype="application/pdf",
        as_attachment=False
    )


# =====================================================
# PDF BUILDER FUNCTION
# =====================================================
def generate_finance_report(requests, grand_total, filename, start_date, end_date):

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=40
    )

    elements = []
    styles = getSampleStyleSheet()

    # -----------------------------
    # TITLE
    # -----------------------------
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=10
    )

    elements.append(Paragraph("FINANCE PROCESSED PERDIEM REPORT", title_style))
    elements.append(Spacer(1, 5))

    # Date Range
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.grey
    )

    elements.append(
    Paragraph(
        f'<font color="#0b3d91">Period:</font> '
        f'<font color="#0b3d91"><b>{start_date} → {end_date}</b></font>',
        styles['Normal']
    )
    )
    elements.append(Spacer(1, 15))

    elements.append(
        HRFlowable(width="100%", thickness=2,
                   color=colors.HexColor("#1e3a8a"))
    )
    elements.append(Spacer(1, 20))

    # -----------------------------
    # GRAND TOTAL
    # -----------------------------
    total_data = [
        ["GRAND TOTAL"],
        [f"{grand_total:,.2f} ETB"]
    ]

    total_table = Table(total_data, colWidths=[400])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 16),
        ('FONTSIZE', (0, 1), (-1, 1), 28),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 20),
        ('TOPPADDING', (0, 1), (-1, 1), 20),
    ]))

    elements.append(total_table)
    elements.append(Spacer(1, 30))

    # -----------------------------
    # GROUP BY DISTRICT
    # -----------------------------
    district_groups = defaultdict(list)

    for r in requests:
        district_name = r.district or "Unknown District"
        district_groups[district_name].append(r)

    for district in sorted(district_groups.keys()):

        district_requests = district_groups[district]

        elements.append(
            Paragraph(f"District: {district}", styles['Heading2'])
        )
        elements.append(Spacer(1, 10))

        table_data = [["Code", "Requestor", "Amount", "Date"]]

        district_total = 0

        for r in district_requests:
            amount = float(r.birr_amount or 0)
            date_value = (
                r.created_at.strftime("%Y-%m-%d")
                if r.created_at else "N/A"
            )

            table_data.append([
                r.perdiem_code or "N/A",
                r.requestor_name or "N/A",
                f"{amount:,.2f}",
                date_value
            ])

            district_total += amount

        detail_table = Table(
            table_data,
            repeatRows=1,
            colWidths=[170, 120, 100, 80]
        )

        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0),
             colors.HexColor("#1e3a8a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ]))

        elements.append(detail_table)
        elements.append(Spacer(1, 5))

        subtotal_data = [
            ["District Total", f"{district_total:,.2f} ETB"]
        ]

        subtotal_table = Table(subtotal_data, colWidths=[250, 150])
        subtotal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1),
             colors.HexColor("#1e3a8a")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))

        elements.append(subtotal_table)
        elements.append(Spacer(1, 20))

    doc.build(elements)
    flash("Report Generated Sucessfully!","success")