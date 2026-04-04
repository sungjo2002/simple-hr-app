import os

from flask import Flask
from sqlalchemy import inspect, text

from models import db
from routes.attendance import attendance_bp
from routes.businesses import businesses_bp
from routes.clients import clients_bp
from routes.employees import employees_bp
from routes.home import home_bp
from routes.payroll import payroll_bp
from routes.records import records_bp
from routes.settings import settings_bp
from seed import seed_database


def _get_database_uri() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url.replace("postgres://", "postgresql://", 1)
    return "sqlite:///hr.db"


def _ensure_employee_retirement_columns() -> None:
    inspector = inspect(db.engine)
    column_names = {column["name"] for column in inspector.get_columns("employees")}
    statements = []
    if "retirement_date" not in column_names:
        statements.append("ALTER TABLE employees ADD COLUMN retirement_date VARCHAR(10) NOT NULL DEFAULT ''")
    if "retirement_reason" not in column_names:
        statements.append("ALTER TABLE employees ADD COLUMN retirement_reason TEXT NOT NULL DEFAULT ''")
    if "recontact_target" not in column_names:
        statements.append("ALTER TABLE employees ADD COLUMN recontact_target VARCHAR(1) NOT NULL DEFAULT 'N'")
    if "next_contact_date" not in column_names:
        statements.append("ALTER TABLE employees ADD COLUMN next_contact_date VARCHAR(10) NOT NULL DEFAULT ''")
    if "retirement_note" not in column_names:
        statements.append("ALTER TABLE employees ADD COLUMN retirement_note TEXT NOT NULL DEFAULT ''")
    for statement in statements:
        db.session.execute(text(statement))
    if statements:
        db.session.commit()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = _get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    app.register_blueprint(home_bp)
    app.register_blueprint(businesses_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(settings_bp)

    with app.app_context():
        db.create_all()
        _ensure_employee_retirement_columns()
        if os.getenv("SEED_DATABASE", "true").lower() == "true":
            seed_database()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
