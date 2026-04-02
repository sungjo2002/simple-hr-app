from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from typing import Any

from flask import render_template_string

from models import AttendanceRecord, ClientCompany, ClientCompanyPayrollSetting, ClientCompanySetting, ClientCompanyWorkType, Employee, EmployeeDocument, OurBusiness, db

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


BASE_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<style>
    :root { --bg:#eef2f6; --panel:#ffffff; --line:#d8e0ea; --text:#111827; --muted:#6b7280; --primary:#1f2937; --blue:#2563eb; --green:#16a34a; --orange:#ea580c; --red:#dc2626; --sky:#0284c7; --yellow:#ca8a04; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Arial,sans-serif; background:var(--bg); color:var(--text); }
    .topbar { background:linear-gradient(180deg,#22354a,#182536); color:white; padding:16px 24px; font-size:28px; font-weight:bold; }
    .menu,.quickbar { padding:10px 14px; display:flex; flex-wrap:wrap; gap:8px; border-bottom:1px solid var(--line); }
    .menu { background:#d8dde4; } .quickbar { background:#f8fafc; }
    .menu a,.quickbar a { text-decoration:none; color:var(--text); background:white; border:1px solid #bcc6d1; border-radius:10px; padding:10px 14px; font-weight:bold; font-size:14px; }
    .menu a.active { background:var(--primary); color:white; border-color:var(--primary); }
    .wrap { width:min(100%,1800px); margin:0 auto; padding:clamp(12px,2vw,20px); }
    .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin-bottom:20px; }
    .card,.panel,.side-box { background:var(--panel); border:1px solid var(--line); border-radius:16px; box-shadow:0 2px 10px rgba(0,0,0,.04); min-width:0; }
    .card { padding:18px; }
    .label { font-size:13px; color:var(--muted); margin-bottom:8px; }
    .value { font-size:30px; font-weight:bold; }
    .panel-head { padding:16px 18px; border-bottom:1px solid #e5e7eb; }
    .panel-head h2,.panel-head h3 { margin:0; font-size:22px; }
    .panel-head p { margin:6px 0 0; font-size:13px; color:var(--muted); }
    .panel-body { padding:18px; }
    .home-grid { display:grid; grid-template-columns:minmax(320px,380px) minmax(0,1fr); gap:18px; align-items:start; }
    .content-grid { display:grid; grid-template-columns:minmax(0,1.35fr) minmax(340px,.85fr); gap:18px; align-items:start; }
    .two-col { display:grid; grid-template-columns:minmax(240px,280px) minmax(0,1fr); gap:18px; }
    .form-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; }
    .actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:18px; align-items:end; }
    .subtabs { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; }
    .subtabs a,.subtabs span { text-decoration:none; padding:10px 14px; border-radius:10px; background:#f3f4f6; border:1px solid #d1d5db; color:var(--text); font-size:13px; font-weight:bold; }
    .subtabs .active { background:var(--primary); color:white; border-color:var(--primary); }
    label { display:block; margin-bottom:6px; font-size:13px; font-weight:bold; color:#374151; }
    input,select,textarea { width:100%; border:1px solid #cbd5e1; border-radius:10px; padding:10px 12px; font-size:14px; background:white; }
    textarea { min-height:90px; resize:vertical; }
    .btn { display:inline-block; text-decoration:none; border:1px solid transparent; border-radius:10px; padding:11px 16px; font-weight:bold; cursor:pointer; font-size:14px; }
    .btn-primary { background:var(--blue); color:white; }
    .btn-green { background:var(--green); color:white; }
    .btn-white { background:white; color:var(--text); border-color:#c8d0da; }
    .photo-box { height:220px; border:2px dashed #cbd5e1; border-radius:16px; display:flex; align-items:center; justify-content:center; background:#f8fafc; color:var(--muted); font-weight:bold; }
    table { width:100%; border-collapse:collapse; table-layout:auto; }
    th,td { border-top:1px solid #edf1f5; padding:12px 10px; text-align:left; font-size:14px; vertical-align:middle; }
    th { background:#f3f5f8; color:#374151; font-weight:bold; }
    .badge { display:inline-block; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:bold; white-space:nowrap; }
    .green { background:#dcfce7; color:#166534; } .blue { background:#dbeafe; color:#1d4ed8; } .yellow { background:#fef3c7; color:#92400e; } .orange { background:#ffedd5; color:#9a3412; } .sky { background:#e0f2fe; color:#0369a1; } .red { background:#fee2e2; color:#b91c1c; } .gray { background:#e5e7eb; color:#374151; }
    .muted { color:var(--muted); font-size:13px; }
    .month-grid { overflow-x:auto; }
    .month-grid table th,.month-grid table td { text-align:center; min-width:42px; white-space:nowrap; }
    .month-grid table th.name-col,.month-grid table td.name-col { text-align:left; min-width:110px; position:sticky; left:0; background:white; z-index:2; }
    .month-grid table th.nation-col,.month-grid table td.nation-col { text-align:left; min-width:100px; position:sticky; left:110px; background:white; z-index:2; }
    .notice { background:#eff6ff; color:#1e3a8a; border:1px solid #bfdbfe; border-radius:12px; padding:12px 14px; margin-bottom:16px; font-size:14px; }
    .score-box { display:grid; gap:12px; min-width:0; }
    .score-row { display:grid; grid-template-columns:84px minmax(0,1fr) 50px; gap:10px; align-items:center; }
    .score-label { font-size:13px; font-weight:bold; color:#374151; }
    .bar-wrap { width:100%; height:18px; background:#e5e7eb; border-radius:999px; overflow:hidden; }
    .bar-fill { height:100%; border-radius:999px; }
    .bar-good { background:linear-gradient(90deg,#22c55e,#16a34a); } .bar-mid { background:linear-gradient(90deg,#60a5fa,#2563eb); } .bar-warn { background:linear-gradient(90deg,#fb923c,#ea580c); }
    .score-num { text-align:right; font-size:13px; font-weight:bold; }
    @media (max-width:1280px) { .content-grid,.home-grid { grid-template-columns:1fr; } .two-col { grid-template-columns:1fr; } }
    @media (max-width:768px) { .wrap { padding:12px; } .menu,.quickbar { padding:10px; } .topbar { font-size:22px; padding:14px 16px; } th,td { font-size:13px; padding:10px 8px; } .score-row { grid-template-columns:72px minmax(0,1fr) 44px; } }
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
    <div class="wrap">{{ content|safe }}</div>
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
        return {"work_score": 0, "sincerity_score": 0, "stability_score": 0, "record_count": 0}

    employee = get_employee(employee_id)
    if not employee:
        return {"work_score": 0, "sincerity_score": 0, "stability_score": 0, "record_count": 0}

    records = AttendanceRecord.query.filter_by(employee_id=employee_id).order_by(AttendanceRecord.work_date.desc()).limit(60).all()
    if not records:
        return {"work_score": 50, "sincerity_score": 50, "stability_score": 50, "record_count": 0}

    completed_count = sum(1 for r in records if r.status == "completed")
    working_count = sum(1 for r in records if r.status == "working")
    hospital_count = sum(1 for r in records if r.status == "hospital")
    vacation_count = sum(1 for r in records if r.status == "vacation")
    absent_count = sum(1 for r in records if r.status == "absent")
    trouble_count = sum(1 for r in records if "무단" in (r.reason or "") or "말썽" in (r.reason or "") or "문제" in (r.reason or ""))

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
        return {"employee_id": employee.id, "work_days": 0, "hospital_days": 0, "absent_days": 0, "vacation_days": 0, "night_minutes": 0, "overtime_minutes": 0, "base_amount": 0, "allowance_amount": 0, "deduction_amount": 0, "final_amount": 0}

    payroll_setting = get_client_company_payroll_setting(employee.current_client_company_id)
    company_setting = get_client_company_setting(employee.current_client_company_id)
    if not payroll_setting or not company_setting:
        return {"employee_id": employee.id, "work_days": 0, "hospital_days": 0, "absent_days": 0, "vacation_days": 0, "night_minutes": 0, "overtime_minutes": 0, "base_amount": 0, "allowance_amount": 0, "deduction_amount": 0, "final_amount": 0}

    records = [r for r in AttendanceRecord.query.filter_by(employee_id=employee.id).all() if parse_date(r.work_date).year == year and parse_date(r.work_date).month == month]

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
    allowance_amount = payroll_setting.meal_allowance + payroll_setting.transport_allowance + payroll_setting.position_allowance + night_hour_amount + overtime_hour_amount
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
