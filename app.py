from flask import Flask
from extensions import db, login_manager, migrate


def create_app():
    app = Flask(__name__)


    # ---------------- CONFIG ----------------
    app.config['SECRET_KEY'] = 'change-this-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boa_perdiem.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    login_manager.login_view = 'auth.login'

    # ---------------- INIT ----------------
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # ---------------- MODELS ----------------
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------------- BLUEPRINTS ----------------
    from routes.auth import auth_bp
    from routes.dashboards import dashboard_bp
    #from routes.notifications import notification_bp
    from routes.requestor_admin import requestor_admin_bp
    from routes.intermediate_approver import intermediate_approver_bp
    from routes.managerial_approver import managerial_approver_bp
    from routes.final_approver import final_approver_bp
    from routes.receipts import receipts_bp
    from routes.reimb_pdf import reimb_pdf_bp
    from routes.reimburs_req_pdf import reimb_req_pdf_bp
    from routes.reimburs_inter_pdf import reimb_inter_pdf_bp
    from routes.reimburs_final_pdf import reimburs_final_pdf_bp
    from routes.perdiem_pdf import perdiem_pdf_bp
    from routes.perdiem_req_pdf import perdiem_req_pdf_bp
    from routes.adminreview import adminreview_bp 
    from routes.view_reimburs import view_reimburs_bp
    from routes.view_perdi import view_perdi_bp  
    from routes.super_admin import super_admin_bp
    from routes.finance_processor import finance_processor_bp 
    from routes.generate_report import generate_report_bp 
    from routes.mailer import mailer_bp 

    
    #app.register_blueprint(adminreview_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    #app.register_blueprint(notification_bp)
    app.register_blueprint(requestor_admin_bp)
    #app.register_blueprint(requestor_admin_bp)
    app.register_blueprint(intermediate_approver_bp)
    app.register_blueprint(managerial_approver_bp)
    app.register_blueprint(final_approver_bp)
    app.register_blueprint(receipts_bp)
    app.register_blueprint(reimb_pdf_bp)
    app.register_blueprint(reimb_inter_pdf_bp)
    app.register_blueprint(reimburs_final_pdf_bp)
    app.register_blueprint(reimb_req_pdf_bp)
    app.register_blueprint(perdiem_pdf_bp)
    app.register_blueprint(perdiem_req_pdf_bp)
    app.register_blueprint(adminreview_bp)
    app.register_blueprint(view_reimburs_bp)
    app.register_blueprint(view_perdi_bp)
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(finance_processor_bp)
    app.register_blueprint(generate_report_bp)
    app.register_blueprint(mailer_bp)
    

        # ---------------- CREATE DB + DEFAULT SUPER ADMIN ----------------
    with app.app_context():
        db.create_all()

        from models import User

        existing_admin = User.query.filter_by(username="superadmin").first()

        if not existing_admin:
            user = User(
                username="superadmin",
                email="superadmin@example.com",
                role="SUPER_ADMIN",
                is_approved=True
            )
            user.set_password("StrongPassword123!")

            db.session.add(user)
            db.session.commit()
            print("✅ Super admin created")
        else:
            print("ℹ️ Super admin already exists")

    return app


app = create_app()

if __name__ == "__main__":
    # For Docker, bind to 0.0.0.0 so the container is accessible
    app.run(host="0.0.0.0", port=8000, debug=True)


