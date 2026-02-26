from flask import Blueprint, send_file, abort, current_app
from flask_login import login_required, current_user
from io import BytesIO
from models import PerdiemRequest

view_reimburs_bp = Blueprint("view_reimburs", __name__, url_prefix="/view_reimburs")

@view_reimburs_bp.route("/perdiem/<int:request_id>")
@login_required
def view_reimburs_db_pdf(request_id):

    perdiem = PerdiemRequest.query.get_or_404(request_id)

    


    if not perdiem.reimburs_form:
        abort(404) 


    pdf_stream = BytesIO(perdiem.reimburs_form)
    
 
    pdf_stream.seek(0)

  
    return send_file(
        pdf_stream,
        as_attachment=False,  # True if you want download
        download_name=f"ReimbursForm_{perdiem.perdiem_code}.pdf",
        mimetype="application/pdf"
    )
