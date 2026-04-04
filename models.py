from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()


def today_str() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


class OurBusiness(db.Model):
    __tablename__ = "our_businesses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    ceo_name = db.Column(db.String(120), nullable=False, default="")
    business_number = db.Column(db.String(30), nullable=False, unique=True)
    phone = db.Column(db.String(30), nullable=False, default="")
    address = db.Column(db.String(255), nullable=False, default="")
    business_type = db.Column(db.String(120), nullable=False, default="")
    business_item = db.Column(db.String(120), nullable=False, default="")
    email = db.Column(db.String(120), nullable=False, default="")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    memo = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.String(10), nullable=False, default=today_str)
    updated_at = db.Column(db.String(10), nullable=False, default=today_str)


class ClientCompany(db.Model):
    __tablename__ = "client_companies"

    id = db.Column(db.Integer, primary_key=True)
    our_business_id = db.Column(db.Integer, db.ForeignKey("our_businesses.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    ceo_name = db.Column(db.String(120), nullable=False, default="")
    business_number = db.Column(db.String(30), nullable=False, unique=True)
    phone = db.Column(db.String(30), nullable=False, default="")
    address = db.Column(db.String(255), nullable=False, default="")
    business_type = db.Column(db.String(120), nullable=False, default="")
    business_item = db.Column(db.String(120), nullable=False, default="")
    email = db.Column(db.String(120), nullable=False, default="")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    memo = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.String(10), nullable=False, default=today_str)
    updated_at = db.Column(db.String(10), nullable=False, default=today_str)


class ClientCompanySetting(db.Model):
    __tablename__ = "client_company_settings"

    id = db.Column(db.Integer, primary_key=True)
    client_company_id = db.Column(db.Integer, db.ForeignKey("client_companies.id"), nullable=False, unique=True)
    attendance_open_time = db.Column(db.String(5), nullable=False, default="08:00")
    late_standard_time = db.Column(db.String(5), nullable=False, default="09:00")
    workday_standard_hours = db.Column(db.Integer, nullable=False, default=8)
    hospital_paid = db.Column(db.Boolean, nullable=False, default=True)
    document_view_policy = db.Column(db.String(100), nullable=False, default="sensitive_super_admin_only")
    created_at = db.Column(db.String(10), nullable=False, default=today_str)
    updated_at = db.Column(db.String(10), nullable=False, default=today_str)


class ClientCompanyWorkType(db.Model):
    __tablename__ = "client_company_work_types"

    id = db.Column(db.Integer, primary_key=True)
    client_company_id = db.Column(db.Integer, db.ForeignKey("client_companies.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(30), nullable=False, default="")
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class ClientCompanyPayrollSetting(db.Model):
    __tablename__ = "client_company_payroll_settings"

    id = db.Column(db.Integer, primary_key=True)
    client_company_id = db.Column(db.Integer, db.ForeignKey("client_companies.id"), nullable=False, unique=True)
    default_pay_type = db.Column(db.String(20), nullable=False, default="monthly")
    base_salary = db.Column(db.Integer, nullable=False, default=0)
    daily_wage = db.Column(db.Integer, nullable=False, default=0)
    hourly_wage = db.Column(db.Integer, nullable=False, default=0)
    night_allowance_rate = db.Column(db.Float, nullable=False, default=1.5)
    overtime_allowance_rate = db.Column(db.Float, nullable=False, default=1.5)
    hospital_pay_type = db.Column(db.String(20), nullable=False, default="paid")
    absence_deduction_amount = db.Column(db.Integer, nullable=False, default=0)
    meal_allowance = db.Column(db.Integer, nullable=False, default=0)
    transport_allowance = db.Column(db.Integer, nullable=False, default=0)
    position_allowance = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.String(10), nullable=False, default=today_str)
    updated_at = db.Column(db.String(10), nullable=False, default=today_str)


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    our_business_id = db.Column(db.Integer, db.ForeignKey("our_businesses.id"), nullable=False)
    current_client_company_id = db.Column(db.Integer, db.ForeignKey("client_companies.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    english_name = db.Column(db.String(120), nullable=False, default="")
    local_name = db.Column(db.String(120), nullable=False, default="")
    nationality = db.Column(db.String(80), nullable=False, default="")
    passport_number = db.Column(db.String(50), nullable=False, default="")
    id_card_number = db.Column(db.String(50), nullable=False, default="")
    birth_date = db.Column(db.String(10), nullable=False, default="")
    gender = db.Column(db.String(20), nullable=False, default="")
    phone = db.Column(db.String(30), nullable=False, default="")
    profile_photo_path = db.Column(db.String(255), nullable=False, default="")
    hire_date = db.Column(db.String(10), nullable=False, default=today_str)
    status = db.Column(db.String(20), nullable=False, default="active")
    work_type_id = db.Column(db.Integer, db.ForeignKey("client_company_work_types.id"), nullable=True)
    pay_type = db.Column(db.String(20), nullable=False, default="monthly")
    created_at = db.Column(db.String(10), nullable=False, default=today_str)
    updated_at = db.Column(db.String(10), nullable=False, default=today_str)


class EmployeeDocument(db.Model):
    __tablename__ = "employee_documents"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    document_type = db.Column(db.String(30), nullable=False, default="other")
    file_name = db.Column(db.String(255), nullable=False, default="")
    file_path = db.Column(db.String(255), nullable=False, default="")
    preview_photo_path = db.Column(db.String(255), nullable=False, default="")
    extracted_text = db.Column(db.Text, nullable=False, default="")
    extracted_name = db.Column(db.String(120), nullable=False, default="")
    extracted_english_name = db.Column(db.String(120), nullable=False, default="")
    extracted_local_name = db.Column(db.String(120), nullable=False, default="")
    extracted_nationality = db.Column(db.String(80), nullable=False, default="")
    extracted_document_number = db.Column(db.String(50), nullable=False, default="")
    extracted_birth_date = db.Column(db.String(10), nullable=False, default="")
    extracted_gender = db.Column(db.String(20), nullable=False, default="")
    file_mime_type = db.Column(db.String(100), nullable=False, default="application/pdf")
    is_sensitive = db.Column(db.Boolean, nullable=False, default=True)
    uploaded_by = db.Column(db.String(50), nullable=False, default="super_admin")
    created_at = db.Column(db.String(10), nullable=False, default=today_str)


class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_work_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    our_business_id = db.Column(db.Integer, db.ForeignKey("our_businesses.id"), nullable=False)
    client_company_id = db.Column(db.Integer, db.ForeignKey("client_companies.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    work_date = db.Column(db.String(10), nullable=False)
    work_type_id = db.Column(db.Integer, db.ForeignKey("client_company_work_types.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="before_work")
    check_in_at = db.Column(db.String(8), nullable=False, default="")
    check_out_at = db.Column(db.String(8), nullable=False, default="")
    overtime_minutes = db.Column(db.Integer, nullable=False, default=0)
    night_minutes = db.Column(db.Integer, nullable=False, default=0)
    reason = db.Column(db.String(255), nullable=False, default="")
    created_by = db.Column(db.String(50), nullable=False, default="admin")
    updated_by = db.Column(db.String(50), nullable=False, default="admin")
    created_at = db.Column(db.String(10), nullable=False, default=today_str)
    updated_at = db.Column(db.String(10), nullable=False, default=today_str)


class PayrollRun(db.Model):
    __tablename__ = "payroll_runs"

    id = db.Column(db.Integer, primary_key=True)
    our_business_id = db.Column(db.Integer, db.ForeignKey("our_businesses.id"), nullable=False)
    client_company_id = db.Column(db.Integer, db.ForeignKey("client_companies.id"), nullable=False)
    target_year = db.Column(db.Integer, nullable=False)
    target_month = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="calculated")
    calculated_by = db.Column(db.String(50), nullable=False, default="admin")
    calculated_at = db.Column(
        db.String(19),
        nullable=False,
        default=lambda: __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    created_at = db.Column(db.String(10), nullable=False, default=today_str)


class PayrollItem(db.Model):
    __tablename__ = "payroll_items"

    id = db.Column(db.Integer, primary_key=True)
    payroll_run_id = db.Column(db.Integer, db.ForeignKey("payroll_runs.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    work_days = db.Column(db.Integer, nullable=False, default=0)
    hospital_days = db.Column(db.Integer, nullable=False, default=0)
    vacation_days = db.Column(db.Integer, nullable=False, default=0)
    absent_days = db.Column(db.Integer, nullable=False, default=0)
    night_minutes = db.Column(db.Integer, nullable=False, default=0)
    overtime_minutes = db.Column(db.Integer, nullable=False, default=0)
    base_amount = db.Column(db.Integer, nullable=False, default=0)
    allowance_amount = db.Column(db.Integer, nullable=False, default=0)
    deduction_amount = db.Column(db.Integer, nullable=False, default=0)
    final_amount = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.String(10), nullable=False, default=today_str)
    updated_at = db.Column(db.String(10), nullable=False, default=today_str)
