
from sqlalchemy import inspect
import os
from pathlib import Path

from flask import Flask, send_from_directory

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


def _ensure_upload_folder(app: Flask) -> None:
    upload_root = Path(app.root_path) / "uploads"
    upload_root.mkdir(parents=True, exist_ok=True)
    (upload_root / "profiles").mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_root)


def _add_column_if_missing(table_name: str, column_name: str, ddl: str) -> None:
    inspector = inspect(db.engine)
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in existing:
        return
    with db.engine.begin() as connection:
        connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")


def _ensure_runtime_schema() -> None:
    employee_columns = [
        ("english_name", "english_name VARCHAR(120) NOT NULL DEFAULT ''"),
        ("local_name", "local_name VARCHAR(120) NOT NULL DEFAULT ''"),
        ("passport_number", "passport_number VARCHAR(50) NOT NULL DEFAULT ''"),
        ("id_card_number", "id_card_number VARCHAR(50) NOT NULL DEFAULT ''"),
        ("birth_date", "birth_date VARCHAR(10) NOT NULL DEFAULT ''"),
        ("gender", "gender VARCHAR(20) NOT NULL DEFAULT ''"),
        ("profile_photo_path", "profile_photo_path VARCHAR(255) NOT NULL DEFAULT ''"),
    ]
    document_columns = [
        ("preview_photo_path", "preview_photo_path VARCHAR(255) NOT NULL DEFAULT ''"),
        ("extracted_text", "extracted_text TEXT NOT NULL DEFAULT ''"),
        ("extracted_name", "extracted_name VARCHAR(120) NOT NULL DEFAULT ''"),
        ("extracted_english_name", "extracted_english_name VARCHAR(120) NOT NULL DEFAULT ''"),
        ("extracted_local_name", "extracted_local_name VARCHAR(120) NOT NULL DEFAULT ''"),
        ("extracted_nationality", "extracted_nationality VARCHAR(80) NOT NULL DEFAULT ''"),
        ("extracted_document_number", "extracted_document_number VARCHAR(50) NOT NULL DEFAULT ''"),
        ("extracted_birth_date", "extracted_birth_date VARCHAR(10) NOT NULL DEFAULT ''"),
        ("extracted_gender", "extracted_gender VARCHAR(20) NOT NULL DEFAULT ''"),
    ]
    for column_name, ddl in employee_columns:
        _add_column_if_missing("employees", column_name, ddl)
    for column_name, ddl in document_columns:
        _add_column_if_missing("employee_documents", column_name, ddl)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = _get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    _ensure_upload_folder(app)

    app.register_blueprint(home_bp)
    app.register_blueprint(businesses_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(settings_bp)

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename: str):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    with app.app_context():
        db.create_all()
        _ensure_runtime_schema()
        if os.getenv("SEED_DATABASE", "true").lower() == "true":
            seed_database()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
