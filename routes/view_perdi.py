from flask import Blueprint, send_file, abort, current_app
from flask_login import login_required, current_user
from io import BytesIO
from models import PerdiemRequest

view_perdi_bp = Blueprint("view_perdi", __name__, url_prefix="/view_perdi")

@view_perdi_bp.route("/perdiem/<int:request_id>")
@login_required
def view_perdi_db_pdf(request_id):

    perdiem = PerdiemRequest.query.get_or_404(request_id)

    


    if not perdiem.perdi_form:
        abort(404) 


    pdf_stream = BytesIO(perdiem.perdi_form)
    
 
    pdf_stream.seek(0)

  
    return send_file(
        pdf_stream,
        as_attachment=False,  # True if you want download
        download_name=f"ReimbursForm_{perdiem.perdiem_code}.pdf",
        mimetype="application/pdf"
    )
