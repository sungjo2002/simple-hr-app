아래는 수정 반영된 `app.py` 전체입니다.

```python
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from typing import Any

from flask import Flask, redirect, render_template_string, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hr.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

ATTENDANCE_STATUS = {
    "before_work": "출근전",
    "working": "근무중",
    "completed": "퇴근완료",
    "hospital": "병원",
    "vacation": "휴가",
    "absent": "결근",
}

DOCUMENT_TYPE_LABELS = {
    "id_card": "신분증",
    "passport": "여권",
    "other": "기타 문서",
}

PAY_TYPE_LABELS = {
    "monthly": "월급제",
    "daily": "일급제",
    "hourly": "시급제",
}


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_time_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def parse_month(value: str) -> tuple[int, int]:
    year_str, month_str = value.split("-")
    return int(year_str), int(month_str)


def month_str_default() -> str:
    return datetime.now().strftime("%Y-%m")


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
    nationality = db.Column(db.String(80), nullable=False, default="")
    phone = db.Column(db.String(30), nullable=False, default="")
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
    calculated_at = db.Column(db.String(19), nullable=False, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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


def get_our_business(our_business_id: int) -> OurBusiness | None:
    return db.session.get(OurBusiness, our_business_id)


def get_our_business_name(our_business_id: int | None) -> str:
    if our_business_id is None:
        return "-"
    item = db.session.get(OurBusiness, our_business_id)
    return item.name if item else "-"


def get_client_company(client_company_id: int) -> ClientCompany | None:
    return db.session.get(ClientCompany, client_company_id)


def get_client_company_name(client_company_id: int | None) -> str:
    if client_company_id is None:
        return "-"
    item = db.session.get(ClientCompany, client_company_id)
    return item.name if item else "-"


def get_client_company_setting(client_company_id: int) -> ClientCompanySetting | None:
    return ClientCompanySetting.query.filter_by(client_company_id=client_company_id).first()


def get_client_company_payroll_setting(client_company_id: int) -> ClientCompanyPayrollSetting | None:
    return ClientCompanyPayrollSetting.query.filter_by(client_company_id=client_company_id).first()


def get_client_company_work_types(client_company_id: int) -> list[ClientCompanyWorkType]:
    return (
        ClientCompanyWorkType.query
        .filter_by(client_company_id=client_company_id, is_active=True)
        .order_by(ClientCompanyWorkType.id.asc())
        .all()
    )


def get_employee(employee_id: int) -> Employee | None:
    return db.session.get(Employee, employee_id)


def get_work_type(work_type_id: int | None) -> ClientCompanyWorkType | None:
    if work_type_id is None:
        return None
    return db.session.get(ClientCompanyWorkType, work_type_id)


def get_work_type_name(work_type_id: int | None) -> str:
    work_type = get_work_type(work_type_id)
    return work_type.name if work_type else "-"


def get_employee_documents(employee_id: int) -> list[EmployeeDocument]:
    return EmployeeDocument.query.filter_by(employee_id=employee_id).order_by(EmployeeDocument.id.desc()).all()


def get_attendance_record(employee_id: int, work_date: str) -> AttendanceRecord | None:
    return AttendanceRecord.query.filter_by(employee_id=employee_id, work_date=work_date).first()


def get_today_status(employee_id: int) -> str:
    record = get_attendance_record(employee_id, today_str())
    return record.status if record else "before_work"


def get_display_status(employee_id: int, work_date: str) -> str:
    record = get_attendance_record(employee_id, work_date)
    return record.status if record else "before_work"


def get_employees_by_client_company(client_company_id: int | None) -> list[Employee]:
    query = Employee.query
    if client_company_id is not None:
        query = query.filter_by(current_client_company_id=client_company_id)
    return query.order_by(Employee.id.asc()).all()


def count_status_for_client_company(client_company_id: int | None, work_date: str, status: str) -> int:
    return sum(
        1
        for employee in get_employees_by_client_company(client_company_id)
        if get_display_status(employee.id, work_date) == status
    )


def status_badge(status: str) -> str:
    label = ATTENDANCE_STATUS.get(status, status)
    mapping = {
        "before_work": "yellow",
        "working": "green",
        "completed": "blue",
        "hospital": "orange",
        "vacation": "sky",
        "absent": "red",
    }
    css = mapping.get(status, "gray")
    return f'<span class="badge {css}">{label}</span>'


def format_won(value: float | int) -> str:
    return f"{int(round(value)):,}"


def clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def score_bar_class(score: int) -> str:
    if score >= 80:
        return "bar-good"
    if score >= 50:
        return "bar-mid"
    return "bar-warn"


def calculate_employee_scorecard(employee_id: int | None) -> dict[str, Any]:
    if employee_id is None:
        return {
            "work_score": 0,
            "sincerity_score": 0,
            "stability_score": 0,
            "record_count": 0,
        }

    employee = get_employee(employee_id)
    if not employee:
        return {
            "work_score": 0,
            "sincerity_score": 0,
            "stability_score": 0,
            "record_count": 0,
        }

    records = (
        AttendanceRecord.query
        .filter_by(employee_id=employee_id)
        .order_by(AttendanceRecord.work_date.desc())
        .limit(60)
        .all()
    )

    if not records:
        return {
            "work_score": 50,
            "sincerity_score": 50,
            "stability_score": 50,
            "record_count": 0,
        }

    completed_count = sum(1 for r in records if r.status == "completed")
    working_count = sum(1 for r in records if r.status == "working")
    hospital_count = sum(1 for r in records if r.status == "hospital")
    vacation_count = sum(1 for r in records if r.status == "vacation")
    absent_count = sum(1 for r in records if r.status == "absent")
    trouble_count = sum(
        1 for r in records
        if "무단" in (r.reason or "") or "말썽" in (r.reason or "") or "문제" in (r.reason or "")
    )

    total = len(records)
    productive_ratio = (completed_count + working_count * 0.7) / total
    sincerity_ratio = (completed_count + working_count + vacation_count * 0.8) / total
    stability_ratio = max(0.0, 1.0 - ((absent_count * 1.2 + trouble_count * 1.5 + hospital_count * 0.3) / total))

    overtime_bonus = min(10.0, sum(r.overtime_minutes for r in records) / 600.0)
    work_score = clamp_score(productive_ratio * 100 + overtime_bonus)
    sincerity_score = clamp_score(sincerity_ratio * 100 - absent_count * 8)
    stability_score = clamp_score(stability_ratio * 100)

    return {
        "work_score": work_score,
        "sincerity_score": sincerity_score,
        "stability_score": stability_score,
        "record_count": total,
    }


def ensure_attendance_record(employee: Employee, work_date: str) -> AttendanceRecord:
    record = get_attendance_record(employee.id, work_date)
    if record:
        return record

    record = AttendanceRecord(
        our_business_id=employee.our_business_id,
        client_company_id=employee.current_client_company_id or 0,
        employee_id=employee.id,
        work_date=work_date,
        work_type_id=employee.work_type_id,
        status="before_work",
        check_in_at="",
        check_out_at="",
        overtime_minutes=0,
        night_minutes=0,
        reason="",
        created_by="admin",
        updated_by="admin",
        created_at=today_str(),
        updated_at=today_str(),
    )
    db.session.add(record)
    db.session.commit()
    return record


def update_attendance(
    employee_id: int,
    work_date: str,
    action_type: str,
    reason: str = "",
    overtime_minutes: int = 0,
    night_minutes: int = 0,
) -> None:
    employee = get_employee(employee_id)
    if not employee or not employee.current_client_company_id:
        return

    record = ensure_attendance_record(employee, work_date)
    now_time = now_time_str()

    record.our_business_id = employee.our_business_id
    record.client_company_id = employee.current_client_company_id
    record.work_type_id = employee.work_type_id

    if action_type == "checkin":
        record.status = "working"
        record.check_in_at = record.check_in_at or now_time
        record.reason = ""
    elif action_type == "checkout":
        if not record.check_in_at:
            record.check_in_at = now_time
        record.status = "completed"
        record.check_out_at = now_time
    elif action_type == "hospital":
        record.status = "hospital"
        record.check_in_at = ""
        record.check_out_at = ""
        record.reason = reason or "병원 진료"
    elif action_type == "vacation":
        record.status = "vacation"
        record.check_in_at = ""
        record.check_out_at = ""
        record.reason = reason or "휴가"
    elif action_type == "absent":
        record.status = "absent"
        record.check_in_at = ""
        record.check_out_at = ""
        record.reason = reason or "결근"
    elif action_type == "reset":
        record.status = "before_work"
        record.check_in_at = ""
        record.check_out_at = ""
        record.reason = ""

    record.overtime_minutes = max(0, overtime_minutes)
    record.night_minutes = max(0, night_minutes)
    record.updated_by = "admin"
    record.updated_at = today_str()
    db.session.commit()


def get_month_attendance_map(employee_id: int, year: int, month: int) -> dict[int, AttendanceRecord]:
    result: dict[int, AttendanceRecord] = {}
    records = AttendanceRecord.query.filter_by(employee_id=employee_id).all()
    for record in records:
        dt = parse_date(record.work_date)
        if dt.year == year and dt.month == month:
            result[dt.day] = record
    return result


def get_day_mark(record: AttendanceRecord | None) -> str:
    if not record:
        return ""
    if record.status in {"working", "completed"}:
        return "O"
    if record.status == "hospital":
        return "H"
    if record.status == "absent":
        return "X"
    if record.status == "vacation":
        return "V"
    return ""


def calculate_payroll_for_employee(employee: Employee, year: int, month: int) -> dict[str, Any]:
    if not employee.current_client_company_id:
        return {
            "employee_id": employee.id,
            "work_days": 0,
            "hospital_days": 0,
            "absent_days": 0,
            "vacation_days": 0,
            "night_minutes": 0,
            "overtime_minutes": 0,
            "base_amount": 0,
            "allowance_amount": 0,
            "deduction_amount": 0,
            "final_amount": 0,
        }

    payroll_setting = get_client_company_payroll_setting(employee.current_client_company_id)
    company_setting = get_client_company_setting(employee.current_client_company_id)

    if not payroll_setting or not company_setting:
        return {
            "employee_id": employee.id,
            "work_days": 0,
            "hospital_days": 0,
            "absent_days": 0,
            "vacation_days": 0,
            "night_minutes": 0,
            "overtime_minutes": 0,
            "base_amount": 0,
            "allowance_amount": 0,
            "deduction_amount": 0,
            "final_amount": 0,
        }

    records = AttendanceRecord.query.filter_by(employee_id=employee.id).all()
    records = [r for r in records if parse_date(r.work_date).year == year and parse_date(r.work_date).month == month]

    work_days = sum(1 for r in records if r.status in {"working", "completed"})
    hospital_days = sum(1 for r in records if r.status == "hospital")
    absent_days = sum(1 for r in records if r.status == "absent")
    vacation_days = sum(1 for r in records if r.status == "vacation")
    night_minutes = sum(r.night_minutes for r in records)
    overtime_minutes = sum(r.overtime_minutes for r in records)

    pay_type = employee.pay_type or payroll_setting.default_pay_type

    if pay_type == "monthly":
        base_amount = payroll_setting.base_salary
    elif pay_type == "daily":
        base_amount = work_days * payroll_setting.daily_wage
        if payroll_setting.hospital_pay_type == "paid":
            base_amount += hospital_days * payroll_setting.daily_wage
    else:
        standard_hours = company_setting.workday_standard_hours
        worked_hours = work_days * standard_hours
        if payroll_setting.hospital_pay_type == "paid":
            worked_hours += hospital_days * standard_hours
        base_amount = worked_hours * payroll_setting.hourly_wage

    night_hour_amount = (night_minutes / 60.0) * payroll_setting.hourly_wage * max(0.0, payroll_setting.night_allowance_rate - 1.0)
    overtime_hour_amount = (overtime_minutes / 60.0) * payroll_setting.hourly_wage * max(0.0, payroll_setting.overtime_allowance_rate - 1.0)

    allowance_amount = (
        payroll_setting.meal_allowance
        + payroll_setting.transport_allowance
        + payroll_setting.position_allowance
        + night_hour_amount
        + overtime_hour_amount
    )
    deduction_amount = absent_days * payroll_setting.absence_deduction_amount
    final_amount = base_amount + allowance_amount - deduction_amount

    return {
        "employee_id": employee.id,
        "work_days": work_days,
        "hospital_days": hospital_days,
        "absent_days": absent_days,
        "vacation_days": vacation_days,
        "night_minutes": night_minutes,
        "overtime_minutes": overtime_minutes,
        "base_amount": int(round(base_amount)),
        "allowance_amount": int(round(allowance_amount)),
        "deduction_amount": int(round(deduction_amount)),
        "final_amount": int(round(final_amount)),
    }


def seed_database() -> None:
    if OurBusiness.query.first():
        return

    our1 = OurBusiness(
        name="에이스인력",
        ceo_name="김대표",
        business_number="111-11-11111",
        phone="02-1111-1111",
        address="서울특별시 구로구 예시로 1",
        business_type="서비스업",
        business_item="인력공급",
        email="ace@example.com",
        is_active=True,
        memo="우리측 사업자",
    )
    our2 = OurBusiness(
        name="미래서비스",
        ceo_name="박대표",
        business_number="222-22-22222",
        phone="031-222-2222",
        address="경기도 수원시 예시로 22",
        business_type="서비스업",
        business_item="파견관리",
        email="mirae@example.com",
        is_active=True,
        memo="",
    )
    db.session.add_all([our1, our2])
    db.session.commit()

    clients = [
        ClientCompany(
            our_business_id=our1.id,
            name="그린시스템",
            ceo_name="홍길동",
            business_number="123-45-67890",
            phone="02-1234-5678",
            address="경북 경주시 예시로 101",
            business_type="제조업",
            business_item="전자조립",
            email="green@example.com",
            is_active=True,
            memo="주간/야간 운영",
        ),
        ClientCompany(
            our_business_id=our1.id,
            name="블루팩토리",
            ceo_name="김공장",
            business_number="234-56-78901",
            phone="051-222-8899",
            address="부산광역시 예시구 산업로 22",
            business_type="제조업",
            business_item="부품생산",
            email="blue@example.com",
            is_active=True,
            memo="",
        ),
        ClientCompany(
            our_business_id=our2.id,
            name="스타물류",
            ceo_name="박성호",
            business_number="345-67-89012",
            phone="031-555-1111",
            address="경기도 화성시 물류로 77",
            business_type="운수업",
            business_item="물류센터",
            email="star@example.com",
            is_active=True,
            memo="야간 운영",
        ),
    ]
    db.session.add_all(clients)
    db.session.commit()

    for client in clients:
        db.session.add(
            ClientCompanySetting(
                client_company_id=client.id,
                attendance_open_time="08:00",
                late_standard_time="09:00",
                workday_standard_hours=8,
                hospital_paid=True,
                document_view_policy="sensitive_super_admin_only",
            )
        )
        db.session.add(
            ClientCompanyPayrollSetting(
                client_company_id=client.id,
                default_pay_type="monthly",
                base_salary=2200000,
                daily_wage=100000,
                hourly_wage=10000,
                night_allowance_rate=1.5,
                overtime_allowance_rate=1.5,
                hospital_pay_type="paid",
                absence_deduction_amount=80000,
                meal_allowance=100000,
                transport_allowance=70000,
                position_allowance=30000,
            )
        )
    db.session.commit()

    work_types = [
        ClientCompanyWorkType(client_company_id=clients[0].id, name="주간", code="DAY", is_active=True),
        ClientCompanyWorkType(client_company_id=clients[0].id, name="야간", code="NIGHT", is_active=True),
        ClientCompanyWorkType(client_company_id=clients[1].id, name="1조", code="A", is_active=True),
        ClientCompanyWorkType(client_company_id=clients[1].id, name="2조", code="B", is_active=True),
        ClientCompanyWorkType(client_company_id=clients[2].id, name="주간", code="DAY", is_active=True),
        ClientCompanyWorkType(client_company_id=clients[2].id, name="야간", code="NIGHT", is_active=True),
    ]
    db.session.add_all(work_types)
    db.session.commit()

    wt_green_day = next(w for w in work_types if w.client_company_id == clients[0].id and w.name == "주간")
    wt_green_night = next(w for w in work_types if w.client_company_id == clients[0].id and w.name == "야간")
    wt_blue_a = next(w for w in work_types if w.client_company_id == clients[1].id and w.name == "1조")
    wt_blue_b = next(w for w in work_types if w.client_company_id == clients[1].id and w.name == "2조")
    wt_star_day = next(w for w in work_types if w.client_company_id == clients[2].id and w.name == "주간")
    wt_star_night = next(w for w in work_types if w.client_company_id == clients[2].id and w.name == "야간")

    employees = [
        Employee(our_business_id=our1.id, current_client_company_id=clients[0].id, name="성조", nationality="한국", phone="010-1111-2222", hire_date="2026-03-01", status="active", work_type_id=wt_green_day.id, pay_type="monthly"),
        Employee(our_business_id=our1.id, current_client_company_id=clients[0].id, name="응우옌", nationality="베트남", phone="010-3333-4444", hire_date="2026-03-15", status="active", work_type_id=wt_green_night.id, pay_type="daily"),
        Employee(our_business_id=our1.id, current_client_company_id=clients[1].id, name="알리", nationality="우즈베키스탄", phone="010-5555-6666", hire_date="2026-03-20", status="active", work_type_id=wt_blue_a.id, pay_type="hourly"),
        Employee(our_business_id=our1.id, current_client_company_id=clients[1].id, name="김민수", nationality="한국", phone="010-7000-0004", hire_date="2026-02-10", status="active", work_type_id=wt_blue_b.id, pay_type="monthly"),
        Employee(our_business_id=our2.id, current_client_company_id=clients[2].id, name="마리아", nationality="필리핀", phone="010-7000-0009", hire_date="2026-02-11", status="active", work_type_id=wt_star_night.id, pay_type="daily"),
        Employee(our_business_id=our2.id, current_client_company_id=clients[2].id, name="한유진", nationality="한국", phone="010-7000-0014", hire_date="2026-03-04", status="active", work_type_id=wt_star_day.id, pay_type="hourly"),
    ]
    db.session.add_all(employees)
    db.session.commit()

    docs = [
        EmployeeDocument(employee_id=employees[0].id, document_type="id_card", file_name="sungjo_idcard.pdf", file_path="/uploads/sungjo_idcard.pdf", file_mime_type="application/pdf", is_sensitive=True, uploaded_by="super_admin"),
        EmployeeDocument(employee_id=employees[1].id, document_type="passport", file_name="nguyen_passport.jpg", file_path="/uploads/nguyen_passport.jpg", file_mime_type="image/jpeg", is_sensitive=True, uploaded_by="super_admin"),
    ]
    db.session.add_all(docs)
    db.session.commit()

    records = [
        AttendanceRecord(our_business_id=employees[0].our_business_id, client_company_id=employees[0].current_client_company_id, employee_id=employees[0].id, work_date=today_str(), work_type_id=employees[0].work_type_id, status="working", check_in_at="08:55:00", check_out_at="", overtime_minutes=0, night_minutes=0, reason="", created_by="admin", updated_by="admin"),
        AttendanceRecord(our_business_id=employees[1].our_business_id, client_company_id=employees[1].current_client_company_id, employee_id=employees[1].id, work_date=today_str(), work_type_id=employees[1].work_type_id, status="hospital", check_in_at="", check_out_at="", overtime_minutes=0, night_minutes=0, reason="병원 진료", created_by="admin", updated_by="admin"),
        AttendanceRecord(our_business_id=employees[2].our_business_id, client_company_id=employees[2].current_client_company_id, employee_id=employees[2].id, work_date=today_str(), work_type_id=employees[2].work_type_id, status="completed", check_in_at="07:50:00", check_out_at="18:10:00", overtime_minutes=70, night_minutes=0, reason="", created_by="admin", updated_by="admin"),
        AttendanceRecord(our_business_id=employees[3].our_business_id, client_company_id=employees[3].current_client_company_id, employee_id=employees[3].id, work_date=today_str(), work_type_id=employees[3].work_type_id, status="absent", check_in_at="", check_out_at="", overtime_minutes=0, night_minutes=0, reason="무단 결근", created_by="admin", updated_by="admin"),
        AttendanceRecord(our_business_id=employees[4].our_business_id, client_company_id=employees[4].current_client_company_id, employee_id=employees[4].id, work_date=today_str(), work_type_id=employees[4].work_type_id, status="completed", check_in_at="20:00:00", check_out_at="06:00:00", overtime_minutes=45, night_minutes=240, reason="", created_by="admin", updated_by="admin"),
    ]
    db.session.add_all(records)
    db.session.commit()


BASE_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<style>
    :root {
        --bg: #eef2f6;
        --panel: #ffffff;
        --line: #d8e0ea;
        --text: #111827;
        --muted: #6b7280;
        --primary: #1f2937;
        --blue: #2563eb;
        --green: #16a34a;
        --orange: #ea580c;
        --red: #dc2626;
        --sky: #0284c7;
        --yellow: #ca8a04;
    }
    * { box-sizing: border-box; }
    body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: var(--bg);
        color: var(--text);
    }
    .topbar {
        background: linear-gradient(180deg, #22354a, #182536);
        color: white;
        padding: 16px 24px;
        font-size: 28px;
        font-weight: bold;
    }
    .menu, .quickbar {
        padding: 10px 14px;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        border-bottom: 1px solid var(--line);
    }
    .menu { background: #d8dde4; }
    .quickbar { background: #f8fafc; }
    .menu a, .quickbar a {
        text-decoration: none;
        color: var(--text);
        background: white;
        border: 1px solid #bcc6d1;
        border-radius: 10px;
        padding: 10px 14px;
        font-weight: bold;
        font-size: 14px;
    }
    .menu a.active {
        background: var(--primary);
        color: white;
        border-color: var(--primary);
    }
    .wrap {
        width: min(100%, 1800px);
        margin: 0 auto;
        padding: clamp(12px, 2vw, 20px);
    }
    .cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 14px;
        margin-bottom: 20px;
    }
    .card, .panel, .side-box {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        min-width: 0;
    }
    .card { padding: 18px; }
    .label {
        font-size: 13px;
        color: var(--muted);
        margin-bottom: 8px;
    }
    .value {
        font-size: 30px;
        font-weight: bold;
    }
    .panel-head {
        padding: 16px 18px;
        border-bottom: 1px solid #e5e7eb;
    }
    .panel-head h2, .panel-head h3 {
        margin: 0;
        font-size: 22px;
    }
    .panel-head p {
        margin: 6px 0 0;
        font-size: 13px;
        color: var(--muted);
    }
    .panel-body {
        padding: 18px;
    }
    .home-grid {
        display: grid;
        grid-template-columns: minmax(320px, 380px) minmax(0, 1fr);
        gap: 18px;
        align-items: start;
    }
    .content-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.35fr) minmax(340px, 0.85fr);
        gap: 18px;
        align-items: start;
    }
    .two-col {
        display: grid;
        grid-template-columns: minmax(240px, 280px) minmax(0, 1fr);
        gap: 18px;
    }
    .form-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 14px;
    }
    .actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 18px;
        align-items: end;
    }
    .subtabs {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 16px;
    }
    .subtabs a, .subtabs span {
        text-decoration: none;
        padding: 10px 14px;
        border-radius: 10px;
        background: #f3f4f6;
        border: 1px solid #d1d5db;
        color: var(--text);
        font-size: 13px;
        font-weight: bold;
    }
    .subtabs .active {
        background: var(--primary);
        color: white;
        border-color: var(--primary);
    }
    label {
        display: block;
        margin-bottom: 6px;
        font-size: 13px;
        font-weight: bold;
        color: #374151;
    }
    input, select, textarea {
        width: 100%;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 14px;
        background: white;
    }
    textarea {
        min-height: 90px;
        resize: vertical;
    }
    .btn {
        display: inline-block;
        text-decoration: none;
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 11px 16px;
        font-weight: bold;
        cursor: pointer;
        font-size: 14px;
    }
    .btn-primary { background: var(--blue); color: white; }
    .btn-green { background: var(--green); color: white; }
    .btn-orange { background: var(--orange); color: white; }
    .btn-sky { background: var(--sky); color: white; }
    .btn-white {
        background: white;
        color: var(--text);
        border-color: #c8d0da;
    }
    .photo-box {
        height: 220px;
        border: 2px dashed #cbd5e1;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f8fafc;
        color: var(--muted);
        font-weight: bold;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        table-layout: auto;
    }
    th, td {
        border-top: 1px solid #edf1f5;
        padding: 12px 10px;
        text-align: left;
        font-size: 14px;
        vertical-align: middle;
    }
    th {
        background: #f3f5f8;
        color: #374151;
        font-weight: bold;
    }
    .table-actions {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
    }
    .badge {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: bold;
        white-space: nowrap;
    }
    .green { background: #dcfce7; color: #166534; }
    .blue { background: #dbeafe; color: #1d4ed8; }
    .yellow { background: #fef3c7; color: #92400e; }
    .orange { background: #ffedd5; color: #9a3412; }
    .sky { background: #e0f2fe; color: #0369a1; }
    .red { background: #fee2e2; color: #b91c1c; }
    .gray { background: #e5e7eb; color: #374151; }
    .muted {
        color: var(--muted);
        font-size: 13px;
    }
    .month-grid { overflow-x: auto; }
    .month-grid table th, .month-grid table td {
        text-align: center;
        min-width: 42px;
        white-space: nowrap;
    }
    .month-grid table th.name-col, .month-grid table td.name-col {
        text-align: left;
        min-width: 110px;
        position: sticky;
        left: 0;
        background: white;
        z-index: 2;
    }
    .month-grid table th.nation-col, .month-grid table td.nation-col {
        text-align: left;
        min-width: 100px;
        position: sticky;
        left: 110px;
        background: white;
        z-index: 2;
    }
    .notice {
        background: #eff6ff;
        color: #1e3a8a;
        border: 1px solid #bfdbfe;
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 16px;
        font-size: 14px;
    }
    .score-box {
        display: grid;
        gap: 12px;
        min-width: 0;
    }
    .score-row {
        display: grid;
        grid-template-columns: 84px minmax(0, 1fr) 50px;
        gap: 10px;
        align-items: center;
    }
    .score-label {
        font-size: 13px;
        font-weight: bold;
        color: #374151;
    }
    .bar-wrap {
        width: 100%;
        height: 18px;
        background: #e5e7eb;
        border-radius: 999px;
        overflow: hidden;
    }
    .bar-fill {
        height: 100%;
        border-radius: 999px;
    }
    .bar-good { background: linear-gradient(90deg, #22c55e, #16a34a); }
    .bar-mid { background: linear-gradient(90deg, #60a5fa, #2563eb); }
    .bar-warn { background: linear-gradient(90deg, #fb923c, #ea580c); }
    .score-num {
        text-align: right;
        font-size: 13px;
        font-weight: bold;
    }
    .search-result-list {
        display: grid;
        gap: 8px;
        margin-top: 12px;
        min-width: 0;
    }
    .search-result-item {
        display: block;
        text-decoration: none;
        color: #111827;
        background: white;
        border: 1px solid #d8e0ea;
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 14px;
        font-weight: bold;
        min-width: 0;
        word-break: keep-all;
    }
    .search-result-item small {
        display: block;
        color: #6b7280;
        font-weight: normal;
        margin-top: 4px;
    }
    @media (max-width: 1280px) {
        .content-grid,
        .home-grid {
            grid-template-columns: 1fr;
        }
        .two-col {
            grid-template-columns: 1fr;
        }
    }
    @media (max-width: 768px) {
        .wrap {
            padding: 12px;
        }
        .menu,
        .quickbar {
            padding: 10px;
        }
        .topbar {
            font-size: 22px;
            padding: 14px 16px;
        }
        th, td {
            font-size: 13px;
            padding: 10px 8px;
        }
        .score-row {
            grid-template-columns: 72px minmax(0, 1fr) 44px;
        }
    }
</style>
</head>
<body>
    <div class="topbar">멀티사업자 파견관리 · 출퇴근 · 급여관리 시스템</div>

    <div class="menu">
        <a href="/" class="{{ 'active' if active=='home' else '' }}">메인</a>
        <a href="/client-companies" class="{{ 'active' if active=='client_companies' else '' }}">거래처관리</a>
        <a href="/employees" class="{{ 'active' if active=='employees' else '' }}">인력관리</a>
        <a href="/attendance" class="{{ 'active' if active=='attendance' else '' }}">출퇴근관리</a>
        <a href="/records" class="{{ 'active' if active=='records' else '' }}">기록조회</a>
        <a href="/payroll" class="{{ 'active' if active=='payroll' else '' }}">급여관리</a>
        <a href="/settings" class="{{ 'active' if active=='settings' else '' }}">설정</a>
        <a href="/our-businesses" class="{{ 'active' if active=='our_businesses' else '' }}">사업자관리</a>
    </div>

    {% if quick_links %}
    <div class="quickbar">
        {% for item in quick_links %}
            <a href="{{ item.href }}">{{ item.label }}</a>
        {% endfor %}
    </div>
    {% endif %}

    <div class="wrap">
        {{ content|safe }}
    </div>
</body>
</html>
"""


def render_page(title: str, active: str, content: str, quick_links: list[dict[str, str]] | None = None) -> str:
    return render_template_string(
        BASE_HTML,
        title=title,
        active=active,
        content=content,
        quick_links=quick_links or [],
    )


def render_our_business_options(selected_id: int | None = None) -> str:
    options = []
    for item in OurBusiness.query.order_by(OurBusiness.id.asc()).all():
        selected = "selected" if item.id == selected_id else ""
        use_label = "사용" if item.is_active else "미사용"
        options.append(f'<option value="{item.id}" {selected}>{item.name} ({use_label})</option>')
    return "".join(options)


def render_client_company_options(selected_id: int | None = None, our_business_id: int | None = None) -> str:
    query = ClientCompany.query
    if our_business_id is not None:
        query = query.filter_by(our_business_id=our_business_id)
    options = []
    for item in query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if item.id == selected_id else ""
        options.append(f'<option value="{item.id}" {selected}>{item.name}</option>')
    return "".join(options)


def render_work_type_options(client_company_id: int, selected_work_type_id: int | None = None) -> str:
    options = []
    for work_type in get_client_company_work_types(client_company_id):
        selected = "selected" if work_type.id == selected_work_type_id else ""
        options.append(f'<option value="{work_type.id}" {selected}>{work_type.name}</option>')
    return "".join(options)


@app.route("/")
def home() -> str:
    current_date = request.args.get("work_date", today_str())
    client_company_raw = request.args.get("client_company_id", "")
    client_company_id = int(client_company_raw) if client_company_raw.isdigit() else None
    employee_keyword = request.args.get("employee_keyword", "").strip()
    selected_employee_raw = request.args.get("selected_employee_id", "")
    selected_employee_id = int(selected_employee_raw) if selected_employee_raw.isdigit() else None

    filtered_employees = get_employees_by_client_company(client_company_id)

    total = len(filtered_employees)
    before_count = count_status_for_client_company(client_company_id, current_date, "before_work")
    working_count = count_status_for_client_company(client_company_id, current_date, "working")
    completed_count = count_status_for_client_company(client_company_id, current_date, "completed")
    hospital_count = count_status_for_client_company(client_company_id, current_date, "hospital")
    absent_count = count_status_for_client_company(client_company_id, current_date, "absent")

    if employee_keyword:
        lowered = employee_keyword.lower()
        filtered_employees = [e for e in filtered_employees if lowered in e.name.lower()]

    if selected_employee_id:
        selected_employee = get_employee(selected_employee_id)
        if selected_employee and (
            client_company_id is None or selected_employee.current_client_company_id == client_company_id
        ):
            filtered_employees = [selected_employee]

    rows = ""
    for employee in filtered_employees:
        row_style = ""
        if selected_employee_id == employee.id:
            row_style = ' style="background:#eff6ff;"'
        rows += f"""
        <tr{row_style}>
            <td>{employee.id}</td>
            <td><a href="/?work_date={current_date}&client_company_id={client_company_id or ''}&employee_keyword={employee_keyword}&selected_employee_id={employee.id}">{employee.name}</a></td>
            <td>{employee.nationality}</td>
            <td>{get_our_business_name(employee.our_business_id)}</td>
            <td>{get_client_company_name(employee.current_client_company_id)}</td>
            <td>{get_work_type_name(employee.work_type_id)}</td>
            <td>{status_badge(get_display_status(employee.id, current_date))}</td>
        </tr>
        """

    if not rows:
        rows = '<tr><td colspan="7">인력이 없습니다.</td></tr>'

    client_options = ['<option value="">전체 거래처</option>']
    for client in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if client_company_id == client.id else ""
        client_options.append(f'<option value="{client.id}" {selected}>{client.name}</option>')

    search_query = Employee.query
    if employee_keyword:
        like_keyword = f"%{employee_keyword}%"
        search_query = search_query.filter(Employee.name.ilike(like_keyword))
    if client_company_id is not None:
        search_query = search_query.filter_by(current_client_company_id=client_company_id)

    searched_employees = search_query.order_by(Employee.name.asc()).limit(10).all()

    if selected_employee_id is None and searched_employees:
        selected_employee_id = searched_employees[0].id

    selected_employee = get_employee(selected_employee_id) if selected_employee_id else None
    scorecard = calculate_employee_scorecard(selected_employee_id) if selected_employee_id else None

    search_results_html = ""
    for employee in searched_employees:
        active_class = ' style="border-color:#2563eb; background:#eff6ff;"' if selected_employee_id == employee.id else ""
        search_results_html += f'''
        <a class="search-result-item" href="/?work_date={current_date}&client_company_id={client_company_id or ''}&employee_keyword={employee_keyword}&selected_employee_id={employee.id}"{active_class}>
            {employee.name}
            <small>{employee.nationality} / {get_client_company_name(employee.current_client_company_id)} / {get_work_type_name(employee.work_type_id)}</small>
        </a>
        '''

    if not search_results_html:
        search_results_html = '<div class="muted">검색 결과가 없습니다.</div>'

    score_html = """
    <div class="muted">사원을 검색하면 지표가 표시됩니다.</div>
    """
    if selected_employee and scorecard:
        work_score = scorecard["work_score"]
        sincerity_score = scorecard["sincerity_score"]
        stability_score = scorecard["stability_score"]

        score_html = f"""
        <div class="score-box">
            <div class="score-row">
                <div class="score-label">일 잘함</div>
                <div class="bar-wrap"><div class="bar-fill {score_bar_class(work_score)}" style="width:{work_score}%;"></div></div>
                <div class="score-num">{work_score}</div>
            </div>
            <div class="score-row">
                <div class="score-label">성실도</div>
                <div class="bar-wrap"><div class="bar-fill {score_bar_class(sincerity_score)}" style="width:{sincerity_score}%;"></div></div>
                <div class="score-num">{sincerity_score}</div>
            </div>
            <div class="score-row">
                <div class="score-label">안정성</div>
                <div class="bar-wrap"><div class="bar-fill {score_bar_class(stability_score)}" style="width:{stability_score}%;"></div></div>
                <div class="score-num">{stability_score}</div>
            </div>
            <div class="muted" style="margin-top:4px;">
                선택 인력: {selected_employee.name} / 기록 {scorecard["record_count"]}건
            </div>
        </div>
        """

    content = f"""
    <div class="notice">
        데이터는 SQLite DB 파일에 저장됩니다. 앱을 다시 켜도 유지됩니다.
    </div>

    <form method="get" class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <div class="form-grid">
                <div>
                    <label>조회 날짜</label>
                    <input type="date" name="work_date" value="{current_date}">
                </div>
                <div>
                    <label>거래처 선택</label>
                    <select name="client_company_id">{"".join(client_options)}</select>
                </div>
            </div>
            <div class="actions">
                <button class="btn btn-white" type="submit">조회</button>
                <a class="btn btn-white" href="/">초기화</a>
            </div>
        </div>
    </form>

    <div class="cards">
        <div class="card"><div class="label">전체 인력</div><div class="value">{total}</div></div>
        <div class="card"><div class="label">출근전</div><div class="value">{before_count}</div></div>
        <div class="card"><div class="label">근무중</div><div class="value">{working_count}</div></div>
        <div class="card"><div class="label">퇴근완료</div><div class="value">{completed_count}</div></div>
        <div class="card"><div class="label">병원</div><div class="value">{hospital_count}</div></div>
        <div class="card"><div class="label">결근</div><div class="value">{absent_count}</div></div>
    </div>

    <div class="home-grid">
        <div>
            <div class="panel" style="margin-bottom:18px;">
                <div class="panel-head">
                    <h2>사원검색</h2>
                    <p>검색 결과와 인력현황 연동</p>
                </div>
                <div class="panel-body">
                    <form method="get">
                        <input type="hidden" name="work_date" value="{current_date}">
                        <input type="hidden" name="client_company_id" value="{client_company_id or ''}">
                        <label>사원 이름 검색</label>
                        <input name="employee_keyword" value="{employee_keyword}" placeholder="예: 성조, 응우옌">
                        <div class="actions">
                            <button class="btn btn-primary" type="submit">검색</button>
                            <a class="btn btn-white" href="/?work_date={current_date}&client_company_id={client_company_id or ''}">초기화</a>
                        </div>
                    </form>

                    <div class="search-result-list">
                        {search_results_html}
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-head">
                    <h2>인력 지표</h2>
                    <p>가로 그래프</p>
                </div>
                <div class="panel-body">
                    {score_html}
                </div>
            </div>
        </div>

        <div class="panel">
            <div class="panel-head">
                <h2>인력현황</h2>
                <p>{current_date} 기준</p>
            </div>
            <div class="panel-body">
                <table>
                    <thead>
                        <tr>
                            <th>번호</th>
                            <th>이름</th>
                            <th>국적</th>
                            <th>사업자</th>
                            <th>거래처</th>
                            <th>근무타입</th>
                            <th>상태</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_page("메인", "home", content)


@app.route("/our-businesses")
def our_businesses_page() -> str:
    rows = ""
    for item in OurBusiness.query.order_by(OurBusiness.id.asc()).all():
        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td><a href="/our-businesses/{item.id}">{item.name}</a></td>
            <td>{item.business_number}</td>
            <td>{item.phone}</td>
            <td>{"사용" if item.is_active else "미사용"}</td>
        </tr>
        """

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>사업자목록</h2>
            <p>우리측 운영 사업자 관리</p>
        </div>
        <div class="panel-body">
            <div class="actions" style="margin-top:0; margin-bottom:16px;">
                <a class="btn btn-primary" href="/our-businesses/new">+ 사업자등록</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>번호</th>
                        <th>사업자명</th>
                        <th>사업자등록번호</th>
                        <th>대표전화</th>
                        <th>사용여부</th>
                    </tr>
                </thead>
                <tbody>{rows or '<tr><td colspan="5">데이터가 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "사업자목록", "href": "/our-businesses"},
        {"label": "사업자등록", "href": "/our-businesses/new"},
    ]
    return render_page("사업자관리", "our_businesses", content, quick)


@app.route("/our-businesses/new", methods=["GET", "POST"])
def our_business_new() -> str:
    if request.method == "POST":
        item = OurBusiness(
            name=request.form["name"].strip(),
            ceo_name=request.form["ceo_name"].strip(),
            business_number=request.form["business_number"].strip(),
            phone=request.form["phone"].strip(),
            address=request.form["address"].strip(),
            business_type=request.form.get("business_type", "").strip(),
            business_item=request.form.get("business_item", "").strip(),
            email=request.form.get("email", "").strip(),
            is_active=request.form.get("is_active", "Y") == "Y",
            memo=request.form.get("memo", "").strip(),
            created_at=today_str(),
            updated_at=today_str(),
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for("our_businesses_page"))

    content = """
    <div class="panel">
        <div class="panel-head">
            <h2>사업자등록</h2>
            <p>우리측 운영 사업자 등록</p>
        </div>
        <div class="panel-body">
            <form method="post">
                <div class="form-grid">
                    <div><label>사업자명</label><input name="name" required></div>
                    <div><label>대표자명</label><input name="ceo_name" required></div>
                    <div><label>사업자등록번호</label><input name="business_number" required></div>
                    <div><label>대표전화</label><input name="phone" required></div>
                    <div><label>주소</label><input name="address" required></div>
                    <div><label>업태</label><input name="business_type"></div>
                    <div><label>종목</label><input name="business_item"></div>
                    <div><label>이메일</label><input name="email"></div>
                    <div>
                        <label>사용여부</label>
                        <select name="is_active">
                            <option value="Y">사용</option>
                            <option value="N">미사용</option>
                        </select>
                    </div>
                    <div style="grid-column: 1 / -1;"><label>메모</label><textarea name="memo"></textarea></div>
                </div>
                <div class="actions">
                    <button class="btn btn-primary" type="submit">저장</button>
                    <a class="btn btn-white" href="/our-businesses">취소</a>
                </div>
            </form>
        </div>
    </div>
    """
    quick = [
        {"label": "사업자목록", "href": "/our-businesses"},
        {"label": "사업자등록", "href": "/our-businesses/new"},
    ]
    return render_page("사업자등록", "our_businesses", content, quick)


@app.route("/our-businesses/<int:our_business_id>")
def our_business_detail(our_business_id: int) -> str:
    item = get_our_business(our_business_id)
    if not item:
        return "사업자를 찾을 수 없습니다.", 404

    client_count = ClientCompany.query.filter_by(our_business_id=our_business_id).count()

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>사업자상세</h2>
            <p>{item.name}</p>
        </div>
        <div class="panel-body">
            <table>
                <tr><th style="width:220px;">사업자명</th><td>{item.name}</td></tr>
                <tr><th>대표자명</th><td>{item.ceo_name}</td></tr>
                <tr><th>사업자등록번호</th><td>{item.business_number}</td></tr>
                <tr><th>대표전화</th><td>{item.phone}</td></tr>
                <tr><th>주소</th><td>{item.address}</td></tr>
                <tr><th>업태</th><td>{item.business_type or '-'}</td></tr>
                <tr><th>종목</th><td>{item.business_item or '-'}</td></tr>
                <tr><th>이메일</th><td>{item.email or '-'}</td></tr>
                <tr><th>사용여부</th><td>{"사용" if item.is_active else "미사용"}</td></tr>
                <tr><th>거래처 수</th><td>{client_count}</td></tr>
                <tr><th>메모</th><td>{item.memo or '-'}</td></tr>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "사업자목록", "href": "/our-businesses"},
        {"label": "사업자등록", "href": "/our-businesses/new"},
    ]
    return render_page("사업자상세", "our_businesses", content, quick)


@app.route("/client-companies")
def client_companies_page() -> str:
    rows = ""
    for item in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td>{get_our_business_name(item.our_business_id)}</td>
            <td><a href="/client-companies/{item.id}">{item.name}</a></td>
            <td>{item.business_number}</td>
            <td>{item.phone}</td>
            <td>{"사용" if item.is_active else "미사용"}</td>
        </tr>
        """

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>거래처목록</h2>
            <p>사업자 소속 거래처 사업자 관리</p>
        </div>
        <div class="panel-body">
            <div class="actions" style="margin-top:0; margin-bottom:16px;">
                <a class="btn btn-primary" href="/client-companies/new">+ 거래처등록</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>번호</th>
                        <th>사업자</th>
                        <th>거래처명</th>
                        <th>사업자등록번호</th>
                        <th>대표전화</th>
                        <th>사용여부</th>
                    </tr>
                </thead>
                <tbody>{rows or '<tr><td colspan="6">데이터가 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "거래처목록", "href": "/client-companies"},
        {"label": "거래처등록", "href": "/client-companies/new"},
    ]
    return render_page("거래처관리", "client_companies", content, quick)


@app.route("/client-companies/new", methods=["GET", "POST"])
def client_company_new() -> str:
    if request.method == "POST":
        item = ClientCompany(
            our_business_id=int(request.form["our_business_id"]),
            name=request.form["name"].strip(),
            ceo_name=request.form["ceo_name"].strip(),
            business_number=request.form["business_number"].strip(),
            phone=request.form["phone"].strip(),
            address=request.form["address"].strip(),
            business_type=request.form.get("business_type", "").strip(),
            business_item=request.form.get("business_item", "").strip(),
            email=request.form.get("email", "").strip(),
            is_active=request.form.get("is_active", "Y") == "Y",
            memo=request.form.get("memo", "").strip(),
            created_at=today_str(),
            updated_at=today_str(),
        )
        db.session.add(item)
        db.session.commit()

        db.session.add(
            ClientCompanySetting(
                client_company_id=item.id,
                attendance_open_time="08:00",
                late_standard_time="09:00",
                workday_standard_hours=8,
                hospital_paid=True,
                document_view_policy="sensitive_super_admin_only",
            )
        )
        db.session.add(
            ClientCompanyPayrollSetting(
                client_company_id=item.id,
                default_pay_type="monthly",
                base_salary=2200000,
                daily_wage=100000,
                hourly_wage=10000,
                night_allowance_rate=1.5,
                overtime_allowance_rate=1.5,
                hospital_pay_type="paid",
                absence_deduction_amount=80000,
                meal_allowance=100000,
                transport_allowance=70000,
                position_allowance=30000,
            )
        )
        db.session.add(ClientCompanyWorkType(client_company_id=item.id, name="주간", code="DAY", is_active=True))
        db.session.add(ClientCompanyWorkType(client_company_id=item.id, name="야간", code="NIGHT", is_active=True))
        db.session.commit()

        return redirect(url_for("client_companies_page"))

    business_options = render_our_business_options()

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>거래처등록</h2>
            <p>사업자 소속 거래처 사업자 등록</p>
        </div>
        <div class="panel-body">
            <form method="post">
                <div class="form-grid">
                    <div><label>사업자</label><select name="our_business_id">{business_options}</select></div>
                    <div><label>거래처명</label><input name="name" required></div>
                    <div><label>대표자명</label><input name="ceo_name" required></div>
                    <div><label>사업자등록번호</label><input name="business_number" required></div>
                    <div><label>대표전화</label><input name="phone" required></div>
                    <div><label>주소</label><input name="address" required></div>
                    <div><label>업태</label><input name="business_type"></div>
                    <div><label>종목</label><input name="business_item"></div>
                    <div><label>이메일</label><input name="email"></div>
                    <div>
                        <label>사용여부</label>
                        <select name="is_active">
                            <option value="Y">사용</option>
                            <option value="N">미사용</option>
                        </select>
                    </div>
                    <div style="grid-column: 1 / -1;"><label>메모</label><textarea name="memo"></textarea></div>
                </div>
                <div class="actions">
                    <button class="btn btn-primary" type="submit">저장</button>
                    <a class="btn btn-white" href="/client-companies">취소</a>
                </div>
            </form>
        </div>
    </div>
    """
    quick = [
        {"label": "거래처목록", "href": "/client-companies"},
        {"label": "거래처등록", "href": "/client-companies/new"},
    ]
    return render_page("거래처등록", "client_companies", content, quick)


@app.route("/client-companies/<int:client_company_id>")
def client_company_detail(client_company_id: int) -> str:
    item = get_client_company(client_company_id)
    if not item:
        return "거래처를 찾을 수 없습니다.", 404

    work_types = ", ".join(w.name for w in get_client_company_work_types(client_company_id)) or "-"
    employee_count = Employee.query.filter_by(current_client_company_id=client_company_id).count()

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>거래처상세</h2>
            <p>{item.name}</p>
        </div>
        <div class="panel-body">
            <table>
                <tr><th style="width:220px;">사업자</th><td>{get_our_business_name(item.our_business_id)}</td></tr>
                <tr><th>거래처명</th><td>{item.name}</td></tr>
                <tr><th>대표자명</th><td>{item.ceo_name}</td></tr>
                <tr><th>사업자등록번호</th><td>{item.business_number}</td></tr>
                <tr><th>대표전화</th><td>{item.phone}</td></tr>
                <tr><th>주소</th><td>{item.address}</td></tr>
                <tr><th>업태</th><td>{item.business_type or '-'}</td></tr>
                <tr><th>종목</th><td>{item.business_item or '-'}</td></tr>
                <tr><th>이메일</th><td>{item.email or '-'}</td></tr>
                <tr><th>사용여부</th><td>{"사용" if item.is_active else "미사용"}</td></tr>
                <tr><th>근무타입</th><td>{work_types}</td></tr>
                <tr><th>배치 인원</th><td>{employee_count}</td></tr>
                <tr><th>메모</th><td>{item.memo or '-'}</td></tr>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "거래처목록", "href": "/client-companies"},
        {"label": "거래처등록", "href": "/client-companies/new"},
    ]
    return render_page("거래처상세", "client_companies", content, quick)


@app.route("/employees")
def employees_page() -> str:
    client_company_raw = request.args.get("client_company_id", "")
    client_company_id = int(client_company_raw) if client_company_raw.isdigit() else None

    rows = ""
    for employee in get_employees_by_client_company(client_company_id):
        rows += f"""
        <tr>
            <td>{employee.id}</td>
            <td><a href="/employees/{employee.id}">{employee.name}</a></td>
            <td>{employee.nationality}</td>
            <td>{get_our_business_name(employee.our_business_id)}</td>
            <td>{get_client_company_name(employee.current_client_company_id)}</td>
            <td>{get_work_type_name(employee.work_type_id)}</td>
            <td>{PAY_TYPE_LABELS.get(employee.pay_type, "-")}</td>
            <td>{status_badge(get_today_status(employee.id))}</td>
        </tr>
        """

    filter_options = ['<option value="">전체 거래처</option>']
    for item in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if item.id == client_company_id else ""
        filter_options.append(f'<option value="{item.id}" {selected}>{item.name}</option>')

    content = f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <div style="min-width:260px;">
                    <label>거래처 필터</label>
                    <select name="client_company_id">{"".join(filter_options)}</select>
                </div>
                <div>
                    <button class="btn btn-white" type="submit">조회</button>
                </div>
                <div>
                    <a class="btn btn-white" href="/employees">초기화</a>
                </div>
            </form>
        </div>
    </div>

    <div class="panel">
        <div class="panel-head">
            <h2>인력목록</h2>
            <p>사업자 / 거래처 / 근무타입 기준 관리</p>
        </div>
        <div class="panel-body">
            <div class="actions" style="margin-top:0; margin-bottom:16px;">
                <a class="btn btn-primary" href="/employees/new">인력등록</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>번호</th>
                        <th>이름</th>
                        <th>국적</th>
                        <th>사업자</th>
                        <th>거래처</th>
                        <th>근무타입</th>
                        <th>급여형태</th>
                        <th>오늘 상태</th>
                    </tr>
                </thead>
                <tbody>{rows or '<tr><td colspan="8">인력이 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "인력목록", "href": "/employees"},
        {"label": "인력등록", "href": "/employees/new"},
    ]
    return render_page("인력관리", "employees", content, quick)


@app.route("/employees/new", methods=["GET", "POST"])
def employee_new() -> str:
    businesses = OurBusiness.query.order_by(OurBusiness.id.asc()).all()
    if not businesses:
        return "먼저 사업자를 등록하세요.", 400

    selected_our_business_raw = request.values.get("our_business_id", str(businesses[0].id))
    selected_our_business_id = int(selected_our_business_raw) if selected_our_business_raw.isdigit() else businesses[0].id

    clients = ClientCompany.query.filter_by(our_business_id=selected_our_business_id).order_by(ClientCompany.id.asc()).all()
    if not clients:
        return "선택한 사업자의 거래처가 없습니다. 먼저 거래처를 등록하세요.", 400

    selected_client_raw = request.values.get("client_company_id", str(clients[0].id))
    selected_client_company_id = int(selected_client_raw) if selected_client_raw.isdigit() else clients[0].id
    work_types = get_client_company_work_types(selected_client_company_id)
    if not work_types:
        return "선택한 거래처의 근무타입이 없습니다.", 400

    if request.method == "POST":
        item = Employee(
            our_business_id=int(request.form["our_business_id"]),
            current_client_company_id=int(request.form["client_company_id"]),
            name=request.form["name"].strip(),
            nationality=request.form["nationality"].strip(),
            phone=request.form.get("phone", "").strip(),
            hire_date=request.form.get("hire_date", today_str()),
            status="active",
            work_type_id=int(request.form["work_type_id"]),
            pay_type=request.form.get("pay_type", "monthly"),
            created_at=today_str(),
            updated_at=today_str(),
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for("employees_page"))

    business_options = render_our_business_options(selected_our_business_id)
    client_options = render_client_company_options(selected_client_company_id, selected_our_business_id)
    work_type_options = render_work_type_options(selected_client_company_id)

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>인력등록</h2>
            <p>사업자와 거래처에 배치되는 인력 등록</p>
        </div>
        <div class="panel-body">
            <form method="get" class="panel" style="box-shadow:none; border-radius:14px; margin-bottom:16px;">
                <div class="panel-body">
                    <div class="form-grid">
                        <div>
                            <label>사업자</label>
                            <select name="our_business_id" onchange="this.form.submit()">{business_options}</select>
                        </div>
                        <div>
                            <label>거래처</label>
                            <select name="client_company_id" onchange="this.form.submit()">{client_options}</select>
                        </div>
                    </div>
                </div>
            </form>

            <form method="post">
                <input type="hidden" name="our_business_id" value="{selected_our_business_id}">
                <input type="hidden" name="client_company_id" value="{selected_client_company_id}">
                <div class="form-grid">
                    <div><label>사업자</label><input value="{get_our_business_name(selected_our_business_id)}" disabled></div>
                    <div><label>거래처</label><input value="{get_client_company_name(selected_client_company_id)}" disabled></div>
                    <div><label>이름</label><input name="name" required></div>
                    <div><label>국적</label><input name="nationality" required></div>
                    <div><label>연락처</label><input name="phone"></div>
                    <div><label>입사일</label><input type="date" name="hire_date" value="{today_str()}"></div>
                    <div>
                        <label>급여형태</label>
                        <select name="pay_type">
                            <option value="monthly">월급제</option>
                            <option value="daily">일급제</option>
                            <option value="hourly">시급제</option>
                        </select>
                    </div>
                    <div>
                        <label>근무타입</label>
                        <select name="work_type_id">{work_type_options}</select>
                    </div>
                </div>
                <div class="actions">
                    <button class="btn btn-primary" type="submit">저장</button>
                    <a class="btn btn-white" href="/employees">취소</a>
                </div>
            </form>
        </div>
    </div>
    """
    quick = [
        {"label": "인력목록", "href": "/employees"},
        {"label": "인력등록", "href": "/employees/new"},
    ]
    return render_page("인력등록", "employees", content, quick)


@app.route("/employees/<int:employee_id>", methods=["GET", "POST"])
def employee_detail(employee_id: int) -> str:
    employee = get_employee(employee_id)
    if not employee:
        return "인력을 찾을 수 없습니다.", 404

    if request.method == "POST":
        file_name = request.form.get("file_name", "").strip() or "unnamed.pdf"
        doc = EmployeeDocument(
            employee_id=employee_id,
            document_type=request.form.get("document_type", "other"),
            file_name=file_name,
            file_path=f"/uploads/{file_name}",
            file_mime_type=request.form.get("file_mime_type", "application/pdf"),
            is_sensitive=request.form.get("is_sensitive", "Y") == "Y",
            uploaded_by="super_admin",
            created_at=today_str(),
        )
        db.session.add(doc)
        db.session.commit()
        return redirect(url_for("employee_detail", employee_id=employee_id))

    attendance_rows = ""
    employee_records = AttendanceRecord.query.filter_by(employee_id=employee_id).order_by(AttendanceRecord.work_date.desc()).all()
    for index, record in enumerate(employee_records, start=1):
        attendance_rows += f"""
        <tr>
            <td>{index}</td>
            <td>{record.work_date}</td>
            <td>{get_work_type_name(record.work_type_id)}</td>
            <td>{record.check_in_at or '-'}</td>
            <td>{record.check_out_at or '-'}</td>
            <td>{status_badge(record.status)}</td>
            <td>{record.reason or '-'}</td>
        </tr>
        """

    document_rows = ""
    for index, document in enumerate(get_employee_documents(employee_id), start=1):
        document_rows += f"""
        <tr>
            <td>{index}</td>
            <td>{DOCUMENT_TYPE_LABELS.get(document.document_type, document.document_type)}</td>
            <td>{document.file_name}</td>
            <td>{document.file_mime_type}</td>
            <td>{'민감' if document.is_sensitive else '일반'}</td>
            <td>{document.created_at}</td>
        </tr>
        """

    content = f"""
    <div class="two-col">
        <div class="side-box" style="padding:14px;">
            <h3 style="margin:0 0 12px;">인력 사진</h3>
            <div class="photo-box">사진 등록 영역</div>
            <div class="actions">
                <button class="btn btn-primary" type="button">사진 등록</button>
                <button class="btn btn-white" type="button">사진 변경</button>
            </div>
        </div>

        <div>
            <div class="panel" style="margin-bottom:18px;">
                <div class="panel-head">
                    <h2>인력상세</h2>
                    <p>기본정보 / 문서 / 출퇴근 기록</p>
                </div>
                <div class="panel-body">
                    <table>
                        <tr><th style="width:220px;">이름</th><td>{employee.name}</td></tr>
                        <tr><th>국적</th><td>{employee.nationality}</td></tr>
                        <tr><th>사업자</th><td>{get_our_business_name(employee.our_business_id)}</td></tr>
                        <tr><th>거래처</th><td>{get_client_company_name(employee.current_client_company_id)}</td></tr>
                        <tr><th>근무타입</th><td>{get_work_type_name(employee.work_type_id)}</td></tr>
                        <tr><th>연락처</th><td>{employee.phone or '-'}</td></tr>
                        <tr><th>입사일</th><td>{employee.hire_date}</td></tr>
                        <tr><th>급여형태</th><td>{PAY_TYPE_LABELS.get(employee.pay_type, '-')}</td></tr>
                        <tr><th>오늘 상태</th><td>{status_badge(get_today_status(employee_id))}</td></tr>
                    </table>
                </div>
            </div>

            <div class="panel">
                <div class="panel-head">
                    <h2>문서 등록</h2>
                    <p>파일 메타데이터 저장</p>
                </div>
                <div class="panel-body">
                    <form method="post">
                        <div class="form-grid">
                            <div>
                                <label>문서종류</label>
                                <select name="document_type">
                                    <option value="id_card">신분증</option>
                                    <option value="passport">여권</option>
                                    <option value="other">기타 문서</option>
                                </select>
                            </div>
                            <div><label>파일명</label><input name="file_name" placeholder="예: passport.pdf"></div>
                            <div>
                                <label>MIME 타입</label>
                                <select name="file_mime_type">
                                    <option value="application/pdf">application/pdf</option>
                                    <option value="image/jpeg">image/jpeg</option>
                                    <option value="image/png">image/png</option>
                                </select>
                            </div>
                            <div>
                                <label>민감 문서 여부</label>
                                <select name="is_sensitive">
                                    <option value="Y">민감</option>
                                    <option value="N">일반</option>
                                </select>
                            </div>
                        </div>
                        <div class="actions">
                            <button class="btn btn-primary" type="submit">문서 저장</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <div class="panel" style="margin-top:18px;">
        <div class="panel-head">
            <h2>등록 문서 목록</h2>
            <p>민감 문서는 최고관리자만 열람 가능 정책</p>
        </div>
        <div class="panel-body">
            <table>
                <thead>
                    <tr>
                        <th>번호</th>
                        <th>종류</th>
                        <th>파일명</th>
                        <th>MIME</th>
                        <th>권한</th>
                        <th>등록일</th>
                    </tr>
                </thead>
                <tbody>{document_rows or '<tr><td colspan="6">등록된 문서가 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>

    <div class="panel" style="margin-top:18px;">
        <div class="panel-head">
            <h2>출퇴근 기록</h2>
            <p>관리자가 직접 처리한 1일 1레코드 기록</p>
        </div>
        <div class="panel-body">
            <table>
                <thead>
                    <tr>
                        <th>번호</th>
                        <th>날짜</th>
                        <th>근무타입</th>
                        <th>출근</th>
                        <th>퇴근</th>
                        <th>상태</th>
                        <th>사유</th>
                    </tr>
                </thead>
                <tbody>{attendance_rows or '<tr><td colspan="7">기록이 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "인력목록", "href": "/employees"},
        {"label": "인력등록", "href": "/employees/new"},
    ]
    return render_page("인력상세", "employees", content, quick)


@app.route("/attendance", methods=["GET", "POST"])
def attendance_page() -> str:
    selected_date = request.values.get("work_date", today_str())
    selected_client_raw = request.values.get("client_company_id", "")
    selected_client_company_id = int(selected_client_raw) if selected_client_raw.isdigit() else None

    if request.method == "POST":
        update_attendance(
            employee_id=int(request.form["employee_id"]),
            work_date=request.form["work_date"],
            action_type=request.form["action_type"],
            reason=request.form.get("reason", "").strip(),
            overtime_minutes=int(request.form.get("overtime_minutes", 0) or 0),
            night_minutes=int(request.form.get("night_minutes", 0) or 0),
        )
        redirect_client_id = request.form.get("client_company_id", "")
        return redirect(
            url_for(
                "attendance_page",
                work_date=request.form["work_date"],
                client_company_id=redirect_client_id,
            )
        )

    employee_list = get_employees_by_client_company(selected_client_company_id)
    client_filter_options = ['<option value="">전체 거래처</option>']
    for client in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if selected_client_company_id == client.id else ""
        client_filter_options.append(f'<option value="{client.id}" {selected}>{client.name}</option>')

    employee_options = ""
    for employee in employee_list:
        employee_options += (
            f'<option value="{employee.id}">'
            f'{employee.name} / {employee.nationality} / {get_client_company_name(employee.current_client_company_id)} / {get_work_type_name(employee.work_type_id)}'
            f"</option>"
        )

    rows = ""
    for employee in employee_list:
        record = get_attendance_record(employee.id, selected_date)
        rows += f"""
        <tr>
            <td>{employee.name}</td>
            <td>{employee.nationality}</td>
            <td>{get_our_business_name(employee.our_business_id)}</td>
            <td>{get_client_company_name(employee.current_client_company_id)}</td>
            <td>{get_work_type_name(employee.work_type_id)}</td>
            <td>{status_badge(record.status if record else "before_work")}</td>
            <td>{record.check_in_at if record and record.check_in_at else '-'}</td>
            <td>{record.check_out_at if record and record.check_out_at else '-'}</td>
            <td>{record.reason if record and record.reason else '-'}</td>
        </tr>
        """

    content = f"""
    <div class="content-grid">
        <div class="panel">
            <div class="panel-head">
                <h2>오늘 출퇴현황</h2>
                <p>선택 날짜: <strong>{selected_date}</strong></p>
            </div>
            <div class="panel-body">
                <form method="get" class="actions" style="margin-top:0; margin-bottom:16px;">
                    <div>
                        <label>날짜 선택</label>
                        <input type="date" name="work_date" value="{selected_date}">
                    </div>
                    <div>
                        <label>거래처 선택</label>
                        <select name="client_company_id">{"".join(client_filter_options)}</select>
                    </div>
                    <div>
                        <button class="btn btn-white" type="submit">조회</button>
                    </div>
                    <div>
                        <a class="btn btn-white" href="/attendance?work_date={today_str()}">오늘</a>
                    </div>
                </form>

                <table>
                    <thead>
                        <tr>
                            <th>이름</th>
                            <th>국적</th>
                            <th>사업자</th>
                            <th>거래처</th>
                            <th>근무타입</th>
                            <th>상태</th>
                            <th>출근</th>
                            <th>퇴근</th>
                            <th>사유</th>
                        </tr>
                    </thead>
                    <tbody>{rows or '<tr><td colspan="9">인력이 없습니다.</td></tr>'}</tbody>
                </table>
            </div>
        </div>

        <div class="panel">
            <div class="panel-head">
                <h2>출근 / 퇴근 / 병원 / 휴가 / 결근 처리</h2>
                <p>1일 1레코드 갱신 방식</p>
            </div>
            <div class="panel-body">
                <form method="post">
                    <input type="hidden" name="client_company_id" value="{selected_client_company_id or ''}">

                    <label>인력 선택</label>
                    <select name="employee_id" required>{employee_options}</select>

                    <label>날짜</label>
                    <input type="date" name="work_date" value="{selected_date}" required>

                    <label>처리 구분</label>
                    <select name="action_type">
                        <option value="checkin">출근처리</option>
                        <option value="checkout">퇴근처리</option>
                        <option value="hospital">병원처리</option>
                        <option value="vacation">휴가처리</option>
                        <option value="absent">결근처리</option>
                        <option value="reset">초기화</option>
                    </select>

                    <div class="form-grid" style="margin-top:14px;">
                        <div><label>연장분(분)</label><input type="number" name="overtime_minutes" value="0"></div>
                        <div><label>야간분(분)</label><input type="number" name="night_minutes" value="0"></div>
                    </div>

                    <label style="margin-top:14px;">사유 / 메모</label>
                    <input name="reason" placeholder="병원 / 휴가 / 결근 시 메모 입력">

                    <div class="actions">
                        <button class="btn btn-green" type="submit">저장</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    """
    quick = [
        {"label": "출퇴근관리", "href": "/attendance"},
        {"label": "기록조회", "href": "/records"},
    ]
    return render_page("출퇴근관리", "attendance", content, quick)


@app.route("/records")
def records_page() -> str:
    selected_client_raw = request.args.get("client_company_id", "")
    selected_client_company_id = int(selected_client_raw) if selected_client_raw.isdigit() else None
    selected_month = request.args.get("month", month_str_default())
    selected_tab = request.args.get("tab", "all")
    year, month = parse_month(selected_month)

    client_filter_options = ['<option value="">전체 거래처</option>']
    for client in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if selected_client_company_id == client.id else ""
        client_filter_options.append(f'<option value="{client.id}" {selected}>{client.name}</option>')

    subtabs = f"""
    <div class="subtabs">
        <a class="{'active' if selected_tab == 'all' else ''}" href="/records?tab=all&client_company_id={selected_client_company_id or ''}&month={selected_month}">전체 출퇴기록</a>
        <a class="{'active' if selected_tab == 'monthly' else ''}" href="/records?tab=monthly&client_company_id={selected_client_company_id or ''}&month={selected_month}">월별 출석현황</a>
    </div>
    """

    filter_form = f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <input type="hidden" name="tab" value="{selected_tab}">
                <div>
                    <label>거래처 필터</label>
                    <select name="client_company_id">{"".join(client_filter_options)}</select>
                </div>
                <div>
                    <label>월 선택</label>
                    <input type="month" name="month" value="{selected_month}">
                </div>
                <div>
                    <button class="btn btn-white" type="submit">조회</button>
                </div>
            </form>
        </div>
    </div>
    """

    if selected_tab == "monthly":
        days_in_month = monthrange(year, month)[1]
        employees_for_grid = get_employees_by_client_company(selected_client_company_id)

        header_days = "".join(f"<th>{day}</th>" for day in range(1, days_in_month + 1))
        month_rows = ""

        for employee in employees_for_grid:
            monthly_map = get_month_attendance_map(employee.id, year, month)
            present_cnt = 0
            hospital_cnt = 0
            absent_cnt = 0
            vacation_cnt = 0
            off_cnt = 0

            month_rows += (
                f'<tr><td class="name-col"><a href="/employees/{employee.id}">{employee.name}</a></td>'
                f'<td class="nation-col">{employee.nationality}</td>'
            )

            for day in range(1, days_in_month + 1):
                record = monthly_map.get(day)
                day_mark = get_day_mark(record)
                weekday = date(year, month, day).weekday()

                if day_mark == "O":
                    present_cnt += 1
                    month_rows += "<td>O</td>"
                elif day_mark == "H":
                    hospital_cnt += 1
                    month_rows += "<td>H</td>"
                elif day_mark == "X":
                    absent_cnt += 1
                    month_rows += "<td>X</td>"
                elif day_mark == "V":
                    vacation_cnt += 1
                    month_rows += "<td>V</td>"
                else:
                    if weekday >= 5:
                        off_cnt += 1
                        month_rows += "<td>-</td>"
                    else:
                        month_rows += "<td></td>"

            month_rows += (
                f"<td>{present_cnt}</td>"
                f"<td>{hospital_cnt}</td>"
                f"<td>{vacation_cnt}</td>"
                f"<td>{absent_cnt}</td>"
                f"<td>{off_cnt}</td></tr>"
            )

        tab_content = f"""
        <div class="panel">
            <div class="panel-head">
                <h2>월별 출석현황</h2>
                <p>O=출근 / H=병원 / V=휴가 / X=결근 / -=휴무</p>
            </div>
            <div class="panel-body month-grid">
                <table>
                    <thead>
                        <tr>
                            <th class="name-col">이름</th>
                            <th class="nation-col">국적</th>
                            {header_days}
                            <th>출근</th>
                            <th>병원</th>
                            <th>휴가</th>
                            <th>결근</th>
                            <th>휴무</th>
                        </tr>
                    </thead>
                    <tbody>{month_rows or '<tr><td colspan="100">인력이 없습니다.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        """
    else:
        query = AttendanceRecord.query
        if selected_client_company_id is not None:
            query = query.filter_by(client_company_id=selected_client_company_id)
        filtered_records = [
            record
            for record in query.order_by(AttendanceRecord.work_date.desc(), AttendanceRecord.employee_id.asc()).all()
            if parse_date(record.work_date).year == year and parse_date(record.work_date).month == month
        ]

        record_rows = ""
        for index, record in enumerate(filtered_records, start=1):
            employee = get_employee(record.employee_id)
            if not employee:
                continue

            record_rows += f"""
            <tr>
                <td>{index}</td>
                <td>{record.work_date}</td>
                <td><a href="/employees/{employee.id}">{employee.name}</a></td>
                <td>{employee.nationality}</td>
                <td>{get_our_business_name(record.our_business_id)}</td>
                <td>{get_client_company_name(record.client_company_id)}</td>
                <td>{get_work_type_name(record.work_type_id)}</td>
                <td>{record.check_in_at or '-'}</td>
                <td>{record.check_out_at or '-'}</td>
                <td>{status_badge(record.status)}</td>
                <td>{record.reason or '-'}</td>
            </tr>
            """

        tab_content = f"""
        <div class="panel">
            <div class="panel-head">
                <h2>전체 출퇴기록</h2>
                <p>{selected_month} 기준 실제 데이터 조회</p>
            </div>
            <div class="panel-body">
                <table>
                    <thead>
                        <tr>
                            <th>번호</th>
                            <th>날짜</th>
                            <th>이름</th>
                            <th>국적</th>
                            <th>사업자</th>
                            <th>거래처</th>
                            <th>근무타입</th>
                            <th>출근</th>
                            <th>퇴근</th>
                            <th>상태</th>
                            <th>사유</th>
                        </tr>
                    </thead>
                    <tbody>{record_rows or '<tr><td colspan="11">기록이 없습니다.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        """

    content = f"""
    {subtabs}
    {filter_form}
    {tab_content}
    """
    quick = [
        {"label": "전체 출퇴기록", "href": "/records?tab=all"},
        {"label": "월별 출석현황", "href": "/records?tab=monthly"},
    ]
    return render_page("기록조회", "records", content, quick)


@app.route("/payroll")
def payroll_page() -> str:
    clients = ClientCompany.query.order_by(ClientCompany.id.asc()).all()
    if not clients:
        return "먼저 거래처를 등록하세요.", 400

    selected_client_raw = request.args.get("client_company_id", str(clients[0].id))
    selected_client_company_id = int(selected_client_raw) if selected_client_raw.isdigit() else clients[0].id
    selected_month = request.args.get("month", month_str_default())
    year, month = parse_month(selected_month)

    filtered_employees = get_employees_by_client_company(selected_client_company_id)
    rows = ""
    total_final_amount = 0

    for employee in filtered_employees:
        payroll = calculate_payroll_for_employee(employee, year, month)
        total_final_amount += payroll["final_amount"]

        rows += f"""
        <tr>
            <td><a href="/employees/{employee.id}">{employee.name}</a></td>
            <td>{employee.nationality}</td>
            <td>{PAY_TYPE_LABELS.get(employee.pay_type, '-')}</td>
            <td>{payroll["work_days"]}</td>
            <td>{payroll["hospital_days"]}</td>
            <td>{payroll["vacation_days"]}</td>
            <td style="color:#b91c1c; font-weight:bold;">{payroll["absent_days"]}</td>
            <td>{round(payroll["night_minutes"] / 60, 1)}h</td>
            <td>{round(payroll["overtime_minutes"] / 60, 1)}h</td>
            <td>{format_won(payroll["base_amount"])}</td>
            <td>{format_won(payroll["allowance_amount"])}</td>
            <td>{format_won(payroll["deduction_amount"])}</td>
            <td style="font-weight:bold; color:#1d4ed8;">{format_won(payroll["final_amount"])}</td>
        </tr>
        """

    client_options = []
    for client in clients:
        selected = "selected" if client.id == selected_client_company_id else ""
        client_options.append(f'<option value="{client.id}" {selected}>{client.name}</option>')

    selected_client = get_client_company(selected_client_company_id)

    content = f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <div>
                    <label>거래처 선택</label>
                    <select name="client_company_id">{"".join(client_options)}</select>
                </div>
                <div>
                    <label>월 선택</label>
                    <input type="month" name="month" value="{selected_month}">
                </div>
                <div>
                    <button class="btn btn-white" type="submit">조회</button>
                </div>
            </form>
        </div>
    </div>

    <div class="cards">
        <div class="card"><div class="label">사업자</div><div class="value" style="font-size:22px;">{get_our_business_name(selected_client.our_business_id if selected_client else None)}</div></div>
        <div class="card"><div class="label">거래처</div><div class="value" style="font-size:22px;">{get_client_company_name(selected_client_company_id)}</div></div>
        <div class="card"><div class="label">대상 월</div><div class="value" style="font-size:22px;">{selected_month}</div></div>
        <div class="card"><div class="label">대상 인력</div><div class="value">{len(filtered_employees)}</div></div>
        <div class="card"><div class="label">총 실지급액</div><div class="value" style="font-size:22px;">{format_won(total_final_amount)}</div></div>
    </div>

    <div class="panel">
        <div class="panel-head">
            <h2>급여대장</h2>
            <p>출퇴근 기록 기반 계산 결과</p>
        </div>
        <div class="panel-body">
            <table>
                <thead>
                    <tr>
                        <th>이름</th>
                        <th>국적</th>
                        <th>급여형태</th>
                        <th>근무일수</th>
                        <th>병원</th>
                        <th>휴가</th>
                        <th>결근</th>
                        <th>야간</th>
                        <th>연장시간</th>
                        <th>기본급</th>
                        <th>수당</th>
                        <th>공제</th>
                        <th>실지급액</th>
                    </tr>
                </thead>
                <tbody>{rows or '<tr><td colspan="13">인력이 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "급여관리", "href": "/payroll"},
    ]
    return render_page("급여관리", "payroll", content, quick)


@app.route("/settings")
def settings_page() -> str:
    content = """
    <div class="panel">
        <div class="panel-head">
            <h2>설정</h2>
            <p>권한 / 문서 / 운영 기준</p>
        </div>
        <div class="panel-body">
            <table>
                <tr><th style="width:220px;">저장 방식</th><td>SQLite DB 파일 저장</td></tr>
                <tr><th>최고관리자</th><td>웹 사용 가능 / 앱 사용 가능 / 민감 문서 열람 가능</td></tr>
                <tr><th>부관리자</th><td>앱만 사용 가능 / 출퇴근 처리 / 기록 조회</td></tr>
                <tr><th>직원</th><td>앱 조회 중심 / 직접 출퇴근 불가</td></tr>
                <tr><th>문서 권한</th><td>민감 문서는 최고관리자만 열람 가능</td></tr>
                <tr><th>출퇴근 정책</th><td>직원이 아니라 관리자가 직접 처리</td></tr>
                <tr><th>근무타입</th><td>거래처별 개별 설정, 공통 고정값 사용 안 함</td></tr>
            </table>
        </div>
    </div>
    """
    return render_page("설정", "settings", content)


with app.app_context():
    db.create_all()
    seed_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

변경 내용

* 사원 검색하면 인력현황도 같이 필터링됩니다.
* 검색 결과에서 선택한 사원은 인력현황 행도 같이 강조됩니다.
* `사원검색`은 왼쪽 위, `지표`는 왼쪽 아래, `인력현황`은 오른쪽에 유지됩니다.
* 지표는 세로 카드가 아니라 **가로 막대 그래프**로 바뀌었습니다.
