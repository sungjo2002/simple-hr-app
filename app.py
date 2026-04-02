아래 파일로 **`app.py` 전체를 통째로 교체**하세요.

```python
from __future__ import annotations

from calendar import monthrange
from datetime import datetime
from typing import Any

from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

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


companies: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "그린시스템",
        "ceo_name": "홍길동",
        "business_number": "123-45-67890",
        "phone": "02-1234-5678",
        "address": "경북 경주시 예시로 101",
        "business_type": "서비스업",
        "business_item": "인력관리",
        "email": "green@example.com",
        "is_active": True,
        "memo": "테스트 회사",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "id": 2,
        "name": "블루팩토리",
        "ceo_name": "김대표",
        "business_number": "234-56-78901",
        "phone": "051-222-8899",
        "address": "부산광역시 예시구 산업로 22",
        "business_type": "제조업",
        "business_item": "부품생산",
        "email": "blue@example.com",
        "is_active": True,
        "memo": "",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "id": 3,
        "name": "스타물류",
        "ceo_name": "박성호",
        "business_number": "345-67-89012",
        "phone": "031-555-1111",
        "address": "경기도 화성시 물류로 77",
        "business_type": "운수업",
        "business_item": "물류센터",
        "email": "star@example.com",
        "is_active": True,
        "memo": "주간/야간 운영",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "id": 4,
        "name": "한빛케어",
        "ceo_name": "이선영",
        "business_number": "456-78-90123",
        "phone": "042-777-2020",
        "address": "대전광역시 유성구 메디컬로 15",
        "business_type": "서비스업",
        "business_item": "간병지원",
        "email": "hanbit@example.com",
        "is_active": True,
        "memo": "병원 파견 인력",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "id": 5,
        "name": "대성건업",
        "ceo_name": "최대성",
        "business_number": "567-89-01234",
        "phone": "053-888-3030",
        "address": "대구광역시 달서구 현장로 88",
        "business_type": "건설업",
        "business_item": "건설인력",
        "email": "daesung@example.com",
        "is_active": True,
        "memo": "현장별 조 편성",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "id": 6,
        "name": "미래푸드",
        "ceo_name": "정미래",
        "business_number": "678-90-12345",
        "phone": "032-444-6060",
        "address": "인천광역시 남동구 식품로 9",
        "business_type": "제조업",
        "business_item": "식품가공",
        "email": "miraefood@example.com",
        "is_active": True,
        "memo": "2교대 운영",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "id": 7,
        "name": "오션테크",
        "ceo_name": "조현우",
        "business_number": "789-01-23456",
        "phone": "064-555-9090",
        "address": "제주특별자치도 제주시 테크로 55",
        "business_type": "제조업",
        "business_item": "전자부품",
        "email": "ocean@example.com",
        "is_active": True,
        "memo": "조별 생산라인",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
]

company_settings: list[dict[str, Any]] = [
    {
        "company_id": 1,
        "attendance_open_time": "08:00",
        "late_standard_time": "09:00",
        "workday_standard_hours": 8,
        "hospital_paid": True,
        "document_view_policy": "sensitive_super_admin_only",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 2,
        "attendance_open_time": "07:00",
        "late_standard_time": "08:30",
        "workday_standard_hours": 8,
        "hospital_paid": False,
        "document_view_policy": "sensitive_super_admin_only",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 3,
        "attendance_open_time": "08:00",
        "late_standard_time": "09:00",
        "workday_standard_hours": 8,
        "hospital_paid": True,
        "document_view_policy": "sensitive_super_admin_only",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 4,
        "attendance_open_time": "08:30",
        "late_standard_time": "09:00",
        "workday_standard_hours": 8,
        "hospital_paid": True,
        "document_view_policy": "sensitive_super_admin_only",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 5,
        "attendance_open_time": "06:30",
        "late_standard_time": "07:00",
        "workday_standard_hours": 8,
        "hospital_paid": False,
        "document_view_policy": "sensitive_super_admin_only",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 6,
        "attendance_open_time": "07:30",
        "late_standard_time": "08:00",
        "workday_standard_hours": 8,
        "hospital_paid": True,
        "document_view_policy": "sensitive_super_admin_only",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 7,
        "attendance_open_time": "08:00",
        "late_standard_time": "08:30",
        "workday_standard_hours": 8,
        "hospital_paid": False,
        "document_view_policy": "sensitive_super_admin_only",
        "created_at": today_str(),
        "updated_at": today_str(),
    },
]

company_work_types: list[dict[str, Any]] = [
    {"id": 1, "company_id": 1, "name": "주간", "code": "DAY", "is_active": True},
    {"id": 2, "company_id": 1, "name": "야간", "code": "NIGHT", "is_active": True},
    {"id": 3, "company_id": 2, "name": "1조", "code": "A", "is_active": True},
    {"id": 4, "company_id": 2, "name": "2조", "code": "B", "is_active": True},
    {"id": 5, "company_id": 2, "name": "3조", "code": "C", "is_active": True},
    {"id": 6, "company_id": 3, "name": "주간", "code": "DAY", "is_active": True},
    {"id": 7, "company_id": 3, "name": "야간", "code": "NIGHT", "is_active": True},
    {"id": 8, "company_id": 4, "name": "주간", "code": "DAY", "is_active": True},
    {"id": 9, "company_id": 4, "name": "오후", "code": "PM", "is_active": True},
    {"id": 10, "company_id": 4, "name": "야간", "code": "NIGHT", "is_active": True},
    {"id": 11, "company_id": 5, "name": "1조", "code": "A", "is_active": True},
    {"id": 12, "company_id": 5, "name": "2조", "code": "B", "is_active": True},
    {"id": 13, "company_id": 6, "name": "주간", "code": "DAY", "is_active": True},
    {"id": 14, "company_id": 6, "name": "야간", "code": "NIGHT", "is_active": True},
    {"id": 15, "company_id": 7, "name": "A조", "code": "A", "is_active": True},
    {"id": 16, "company_id": 7, "name": "B조", "code": "B", "is_active": True},
    {"id": 17, "company_id": 7, "name": "C조", "code": "C", "is_active": True},
]

company_payroll_settings: list[dict[str, Any]] = [
    {
        "company_id": 1,
        "default_pay_type": "monthly",
        "base_salary": 2200000,
        "daily_wage": 100000,
        "hourly_wage": 10000,
        "night_allowance_rate": 1.5,
        "overtime_allowance_rate": 1.5,
        "hospital_pay_type": "paid",
        "absence_deduction_amount": 80000,
        "meal_allowance": 150000,
        "transport_allowance": 100000,
        "position_allowance": 50000,
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 2,
        "default_pay_type": "daily",
        "base_salary": 0,
        "daily_wage": 110000,
        "hourly_wage": 10500,
        "night_allowance_rate": 1.5,
        "overtime_allowance_rate": 1.5,
        "hospital_pay_type": "unpaid",
        "absence_deduction_amount": 90000,
        "meal_allowance": 120000,
        "transport_allowance": 80000,
        "position_allowance": 0,
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 3,
        "default_pay_type": "monthly",
        "base_salary": 2300000,
        "daily_wage": 105000,
        "hourly_wage": 10200,
        "night_allowance_rate": 1.5,
        "overtime_allowance_rate": 1.5,
        "hospital_pay_type": "paid",
        "absence_deduction_amount": 85000,
        "meal_allowance": 100000,
        "transport_allowance": 80000,
        "position_allowance": 30000,
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 4,
        "default_pay_type": "daily",
        "base_salary": 0,
        "daily_wage": 115000,
        "hourly_wage": 10800,
        "night_allowance_rate": 1.5,
        "overtime_allowance_rate": 1.5,
        "hospital_pay_type": "paid",
        "absence_deduction_amount": 70000,
        "meal_allowance": 90000,
        "transport_allowance": 70000,
        "position_allowance": 20000,
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 5,
        "default_pay_type": "daily",
        "base_salary": 0,
        "daily_wage": 120000,
        "hourly_wage": 11000,
        "night_allowance_rate": 1.5,
        "overtime_allowance_rate": 1.5,
        "hospital_pay_type": "unpaid",
        "absence_deduction_amount": 95000,
        "meal_allowance": 80000,
        "transport_allowance": 90000,
        "position_allowance": 0,
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 6,
        "default_pay_type": "hourly",
        "base_salary": 0,
        "daily_wage": 108000,
        "hourly_wage": 10600,
        "night_allowance_rate": 1.5,
        "overtime_allowance_rate": 1.5,
        "hospital_pay_type": "paid",
        "absence_deduction_amount": 85000,
        "meal_allowance": 70000,
        "transport_allowance": 60000,
        "position_allowance": 0,
        "created_at": today_str(),
        "updated_at": today_str(),
    },
    {
        "company_id": 7,
        "default_pay_type": "monthly",
        "base_salary": 2400000,
        "daily_wage": 115000,
        "hourly_wage": 11200,
        "night_allowance_rate": 1.5,
        "overtime_allowance_rate": 1.5,
        "hospital_pay_type": "unpaid",
        "absence_deduction_amount": 90000,
        "meal_allowance": 100000,
        "transport_allowance": 70000,
        "position_allowance": 40000,
        "created_at": today_str(),
        "updated_at": today_str(),
    },
]

employees: list[dict[str, Any]] = [
    {"id": 1, "company_id": 1, "name": "성조", "nationality": "한국", "phone": "010-1111-2222", "hire_date": "2026-03-01", "status": "active", "work_type_id": 1, "pay_type": "monthly", "created_at": today_str(), "updated_at": today_str()},
    {"id": 2, "company_id": 1, "name": "응우옌", "nationality": "베트남", "phone": "010-3333-4444", "hire_date": "2026-03-15", "status": "active", "work_type_id": 2, "pay_type": "daily", "created_at": today_str(), "updated_at": today_str()},
    {"id": 3, "company_id": 2, "name": "알리", "nationality": "우즈베키스탄", "phone": "010-5555-6666", "hire_date": "2026-03-20", "status": "active", "work_type_id": 3, "pay_type": "hourly", "created_at": today_str(), "updated_at": today_str()},
    {"id": 4, "company_id": 1, "name": "김민수", "nationality": "한국", "phone": "010-7000-0004", "hire_date": "2026-02-10", "status": "active", "work_type_id": 1, "pay_type": "monthly", "created_at": today_str(), "updated_at": today_str()},
    {"id": 5, "company_id": 1, "name": "소피아", "nationality": "필리핀", "phone": "010-7000-0005", "hire_date": "2026-02-14", "status": "active", "work_type_id": 2, "pay_type": "daily", "created_at": today_str(), "updated_at": today_str()},
    {"id": 6, "company_id": 2, "name": "박준호", "nationality": "한국", "phone": "010-7000-0006", "hire_date": "2026-01-08", "status": "active", "work_type_id": 4, "pay_type": "daily", "created_at": today_str(), "updated_at": today_str()},
    {"id": 7, "company_id": 2, "name": "도안", "nationality": "베트남", "phone": "010-7000-0007", "hire_date": "2026-01-21", "status": "active", "work_type_id": 5, "pay_type": "hourly", "created_at": today_str(), "updated_at": today_str()},
    {"id": 8, "company_id": 3, "name": "이하늘", "nationality": "한국", "phone": "010-7000-0008", "hire_date": "2026-02-03", "status": "active", "work_type_id": 6, "pay_type": "monthly", "created_at": today_str(), "updated_at": today_str()},
    {"id": 9, "company_id": 3, "name": "마리아", "nationality": "필리핀", "phone": "010-7000-0009", "hire_date": "2026-02-11", "status": "active", "work_type_id": 7, "pay_type": "daily", "created_at": today_str(), "updated_at": today_str()},
    {"id": 10, "company_id": 4, "name": "정수빈", "nationality": "한국", "phone": "010-7000-0010", "hire_date": "2026-01-30", "status": "active", "work_type_id": 8, "pay_type": "daily", "created_at": today_str(), "updated_at": today_str()},
    {"id": 11, "company_id": 4, "name": "칼로스", "nationality": "멕시코", "phone": "010-7000-0011", "hire_date": "2026-02-18", "status": "active", "work_type_id": 10, "pay_type": "hourly", "created_at": today_str(), "updated_at": today_str()},
    {"id": 12, "company_id": 5, "name": "최현우", "nationality": "한국", "phone": "010-7000-0012", "hire_date": "2026-01-12", "status": "active", "work_type_id": 11, "pay_type": "daily", "created_at": today_str(), "updated_at": today_str()},
    {"id": 13, "company_id": 5, "name": "압둘", "nationality": "우즈베키스탄", "phone": "010-7000-0013", "hire_date": "2026-02-20", "status": "active", "work_type_id": 12, "pay_type": "daily", "created_at": today_str(), "updated_at": today_str()},
    {"id": 14, "company_id": 6, "name": "한유진", "nationality": "한국", "phone": "010-7000-0014", "hire_date": "2026-03-04", "status": "active", "work_type_id": 13, "pay_type": "hourly", "created_at": today_str(), "updated_at": today_str()},
    {"id": 15, "company_id": 6, "name": "린", "nationality": "태국", "phone": "010-7000-0015", "hire_date": "2026-03-09", "status": "active", "work_type_id": 14, "pay_type": "hourly", "created_at": today_str(), "updated_at": today_str()},
    {"id": 16, "company_id": 7, "name": "오세훈", "nationality": "한국", "phone": "010-7000-0016", "hire_date": "2026-02-01", "status": "active", "work_type_id": 15, "pay_type": "monthly", "created_at": today_str(), "updated_at": today_str()},
    {"id": 17, "company_id": 7, "name": "제이슨", "nationality": "미국", "phone": "010-7000-0017", "hire_date": "2026-02-07", "status": "active", "work_type_id": 16, "pay_type": "hourly", "created_at": today_str(), "updated_at": today_str()},
    {"id": 18, "company_id": 7, "name": "누르잔", "nationality": "카자흐스탄", "phone": "010-7000-0018", "hire_date": "2026-02-25", "status": "active", "work_type_id": 17, "pay_type": "daily", "created_at": today_str(), "updated_at": today_str()},
]

employee_documents: list[dict[str, Any]] = [
    {"id": 1, "employee_id": 1, "document_type": "id_card", "file_name": "sungjo_idcard.pdf", "file_path": "/uploads/sungjo_idcard.pdf", "file_mime_type": "application/pdf", "is_sensitive": True, "uploaded_by": "super_admin", "created_at": today_str()},
    {"id": 2, "employee_id": 2, "document_type": "passport", "file_name": "nguyen_passport.jpg", "file_path": "/uploads/nguyen_passport.jpg", "file_mime_type": "image/jpeg", "is_sensitive": True, "uploaded_by": "super_admin", "created_at": today_str()},
    {"id": 3, "employee_id": 9, "document_type": "passport", "file_name": "maria_passport.pdf", "file_path": "/uploads/maria_passport.pdf", "file_mime_type": "application/pdf", "is_sensitive": True, "uploaded_by": "super_admin", "created_at": today_str()},
]

attendance_records: list[dict[str, Any]] = [
    {"id": 1, "company_id": 1, "employee_id": 1, "work_date": today_str(), "work_type_id": 1, "status": "working", "check_in_at": "08:55:00", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 0, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 2, "company_id": 1, "employee_id": 2, "work_date": today_str(), "work_type_id": 2, "status": "hospital", "check_in_at": "", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 0, "reason": "병원 진료", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 3, "company_id": 2, "employee_id": 3, "work_date": today_str(), "work_type_id": 3, "status": "completed", "check_in_at": "07:50:00", "check_out_at": "18:10:00", "overtime_minutes": 70, "night_minutes": 0, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 4, "company_id": 1, "employee_id": 4, "work_date": today_str(), "work_type_id": 1, "status": "completed", "check_in_at": "08:47:00", "check_out_at": "18:03:00", "overtime_minutes": 30, "night_minutes": 0, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 5, "company_id": 1, "employee_id": 5, "work_date": today_str(), "work_type_id": 2, "status": "working", "check_in_at": "20:05:00", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 180, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 6, "company_id": 2, "employee_id": 6, "work_date": today_str(), "work_type_id": 4, "status": "working", "check_in_at": "08:12:00", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 0, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 7, "company_id": 2, "employee_id": 7, "work_date": today_str(), "work_type_id": 5, "status": "absent", "check_in_at": "", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 0, "reason": "무단 결근", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 8, "company_id": 3, "employee_id": 8, "work_date": today_str(), "work_type_id": 6, "status": "working", "check_in_at": "08:58:00", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 0, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 9, "company_id": 3, "employee_id": 9, "work_date": today_str(), "work_type_id": 7, "status": "vacation", "check_in_at": "", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 0, "reason": "연차", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 10, "company_id": 4, "employee_id": 10, "work_date": today_str(), "work_type_id": 8, "status": "completed", "check_in_at": "08:32:00", "check_out_at": "17:58:00", "overtime_minutes": 0, "night_minutes": 0, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 11, "company_id": 4, "employee_id": 11, "work_date": today_str(), "work_type_id": 10, "status": "working", "check_in_at": "21:01:00", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 240, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 12, "company_id": 5, "employee_id": 12, "work_date": today_str(), "work_type_id": 11, "status": "working", "check_in_at": "06:45:00", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 0, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 13, "company_id": 5, "employee_id": 13, "work_date": today_str(), "work_type_id": 12, "status": "hospital", "check_in_at": "", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 0, "reason": "진료 예약", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 14, "company_id": 6, "employee_id": 14, "work_date": today_str(), "work_type_id": 13, "status": "completed", "check_in_at": "07:28:00", "check_out_at": "18:12:00", "overtime_minutes": 42, "night_minutes": 0, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 15, "company_id": 6, "employee_id": 15, "work_date": today_str(), "work_type_id": 14, "status": "working", "check_in_at": "19:55:00", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 210, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 16, "company_id": 7, "employee_id": 16, "work_date": today_str(), "work_type_id": 15, "status": "working", "check_in_at": "08:05:00", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 0, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 17, "company_id": 7, "employee_id": 17, "work_date": today_str(), "work_type_id": 16, "status": "completed", "check_in_at": "08:10:00", "check_out_at": "18:20:00", "overtime_minutes": 50, "night_minutes": 0, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
    {"id": 18, "company_id": 7, "employee_id": 18, "work_date": today_str(), "work_type_id": 17, "status": "before_work", "check_in_at": "", "check_out_at": "", "overtime_minutes": 0, "night_minutes": 0, "reason": "", "created_by": "admin", "updated_by": "admin", "created_at": today_str(), "updated_at": today_str()},
]

payroll_runs: list[dict[str, Any]] = []
payroll_items: list[dict[str, Any]] = []


def next_id(items: list[dict[str, Any]]) -> int:
    return max((item["id"] for item in items), default=0) + 1


def get_company(company_id: int) -> dict[str, Any] | None:
    return next((c for c in companies if c["id"] == company_id), None)


def get_company_name(company_id: int | None) -> str:
    if company_id is None:
        return "-"
    company = get_company(company_id)
    return company["name"] if company else "-"


def get_company_setting(company_id: int) -> dict[str, Any] | None:
    return next((s for s in company_settings if s["company_id"] == company_id), None)


def get_company_payroll_setting(company_id: int) -> dict[str, Any] | None:
    return next((s for s in company_payroll_settings if s["company_id"] == company_id), None)


def get_employee(employee_id: int) -> dict[str, Any] | None:
    return next((e for e in employees if e["id"] == employee_id), None)


def get_work_type(work_type_id: int | None) -> dict[str, Any] | None:
    if work_type_id is None:
        return None
    return next((w for w in company_work_types if w["id"] == work_type_id), None)


def get_work_type_name(work_type_id: int | None) -> str:
    work_type = get_work_type(work_type_id)
    return work_type["name"] if work_type else "-"


def get_company_work_types(company_id: int) -> list[dict[str, Any]]:
    return [
        w
        for w in company_work_types
        if w["company_id"] == company_id and w["is_active"]
    ]


def get_employee_documents(employee_id: int) -> list[dict[str, Any]]:
    return [d for d in employee_documents if d["employee_id"] == employee_id]


def get_attendance_record(employee_id: int, work_date: str) -> dict[str, Any] | None:
    return next(
        (
            r
            for r in attendance_records
            if r["employee_id"] == employee_id and r["work_date"] == work_date
        ),
        None,
    )


def get_today_status(employee_id: int) -> str:
    record = get_attendance_record(employee_id, today_str())
    return record["status"] if record else "before_work"


def get_display_status(employee_id: int, work_date: str) -> str:
    record = get_attendance_record(employee_id, work_date)
    return record["status"] if record else "before_work"


def get_employees_by_company(company_id: int | None) -> list[dict[str, Any]]:
    if company_id is None:
        return list(employees)
    return [e for e in employees if e["company_id"] == company_id]


def count_status_for_company(company_id: int | None, work_date: str, status: str) -> int:
    return sum(
        1
        for employee in get_employees_by_company(company_id)
        if get_display_status(employee["id"], work_date) == status
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


def ensure_attendance_record(employee: dict[str, Any], work_date: str) -> dict[str, Any]:
    record = get_attendance_record(employee["id"], work_date)
    if record:
        return record

    record = {
        "id": next_id(attendance_records),
        "company_id": employee["company_id"],
        "employee_id": employee["id"],
        "work_date": work_date,
        "work_type_id": employee["work_type_id"],
        "status": "before_work",
        "check_in_at": "",
        "check_out_at": "",
        "overtime_minutes": 0,
        "night_minutes": 0,
        "reason": "",
        "created_by": "admin",
        "updated_by": "admin",
        "created_at": today_str(),
        "updated_at": today_str(),
    }
    attendance_records.append(record)
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
    if not employee:
        return

    record = ensure_attendance_record(employee, work_date)
    now_time = now_time_str()

    if action_type == "checkin":
        record["status"] = "working"
        record["check_in_at"] = record["check_in_at"] or now_time
        record["reason"] = ""
    elif action_type == "checkout":
        if not record["check_in_at"]:
            record["check_in_at"] = now_time
        record["status"] = "completed"
        record["check_out_at"] = now_time
    elif action_type == "hospital":
        record["status"] = "hospital"
        record["check_in_at"] = ""
        record["check_out_at"] = ""
        record["reason"] = reason or "병원 진료"
    elif action_type == "vacation":
        record["status"] = "vacation"
        record["check_in_at"] = ""
        record["check_out_at"] = ""
        record["reason"] = reason or "휴가"
    elif action_type == "absent":
        record["status"] = "absent"
        record["check_in_at"] = ""
        record["check_out_at"] = ""
        record["reason"] = reason or "결근"
    elif action_type == "reset":
        record["status"] = "before_work"
        record["check_in_at"] = ""
        record["check_out_at"] = ""
        record["reason"] = ""

    record["overtime_minutes"] = max(0, overtime_minutes)
    record["night_minutes"] = max(0, night_minutes)
    record["updated_by"] = "admin"
    record["updated_at"] = today_str()


def get_month_attendance_map(
    employee_id: int,
    year: int,
    month: int,
) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for record in attendance_records:
        if record["employee_id"] != employee_id:
            continue
        dt = parse_date(record["work_date"])
        if dt.year == year and dt.month == month:
            result[dt.day] = record
    return result


def get_day_mark(record: dict[str, Any] | None) -> str:
    if not record:
        return ""
    if record["status"] in {"working", "completed"}:
        return "O"
    if record["status"] == "hospital":
        return "H"
    if record["status"] == "absent":
        return "X"
    if record["status"] == "vacation":
        return "V"
    return ""


def calculate_payroll_for_employee(
    employee: dict[str, Any],
    year: int,
    month: int,
) -> dict[str, Any]:
    payroll_setting = get_company_payroll_setting(employee["company_id"])
    company_setting = get_company_setting(employee["company_id"])

    if not payroll_setting or not company_setting:
        return {
            "employee_id": employee["id"],
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

    records = []
    for record in attendance_records:
        if record["employee_id"] != employee["id"]:
            continue
        dt = parse_date(record["work_date"])
        if dt.year == year and dt.month == month:
            records.append(record)

    work_days = sum(1 for r in records if r["status"] in {"working", "completed"})
    hospital_days = sum(1 for r in records if r["status"] == "hospital")
    absent_days = sum(1 for r in records if r["status"] == "absent")
    vacation_days = sum(1 for r in records if r["status"] == "vacation")
    night_minutes = sum(r["night_minutes"] for r in records)
    overtime_minutes = sum(r["overtime_minutes"] for r in records)

    pay_type = employee.get("pay_type") or payroll_setting["default_pay_type"]

    if pay_type == "monthly":
        base_amount = payroll_setting["base_salary"]
    elif pay_type == "daily":
        base_amount = work_days * payroll_setting["daily_wage"]
        if payroll_setting["hospital_pay_type"] == "paid":
            base_amount += hospital_days * payroll_setting["daily_wage"]
    else:
        standard_hours = company_setting["workday_standard_hours"]
        worked_hours = work_days * standard_hours
        if payroll_setting["hospital_pay_type"] == "paid":
            worked_hours += hospital_days * standard_hours
        base_amount = worked_hours * payroll_setting["hourly_wage"]

    night_hour_amount = (
        night_minutes / 60.0
    ) * payroll_setting["hourly_wage"] * max(
        0.0,
        payroll_setting["night_allowance_rate"] - 1.0,
    )
    overtime_hour_amount = (
        overtime_minutes / 60.0
    ) * payroll_setting["hourly_wage"] * max(
        0.0,
        payroll_setting["overtime_allowance_rate"] - 1.0,
    )

    allowance_amount = (
        payroll_setting["meal_allowance"]
        + payroll_setting["transport_allowance"]
        + payroll_setting["position_allowance"]
        + night_hour_amount
        + overtime_hour_amount
    )

    deduction_amount = absent_days * payroll_setting["absence_deduction_amount"]
    final_amount = base_amount + allowance_amount - deduction_amount

    return {
        "employee_id": employee["id"],
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
        max-width: 1440px;
        margin: 0 auto;
        padding: 20px;
    }
    .cards {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 14px;
        margin-bottom: 20px;
    }
    .card, .panel, .side-box {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
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
    .panel-body { padding: 18px; }
    .content-grid {
        display: grid;
        grid-template-columns: 1.3fr 0.7fr;
        gap: 18px;
    }
    .two-col {
        display: grid;
        grid-template-columns: 280px 1fr;
        gap: 18px;
    }
    .form-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
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
    @media (max-width: 1180px) {
        .cards { grid-template-columns: 1fr 1fr 1fr; }
        .content-grid, .two-col, .form-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 700px) {
        .cards { grid-template-columns: 1fr 1fr; }
    }
</style>
</head>
<body>
    <div class="topbar">멀티회사 사원관리 · 출퇴근 · 급여관리 시스템</div>

    <div class="menu">
        <a href="/" class="{{ 'active' if active=='home' else '' }}">메인</a>
        <a href="/companies" class="{{ 'active' if active=='companies' else '' }}">회사관리</a>
        <a href="/employees" class="{{ 'active' if active=='employees' else '' }}">사원관리</a>
        <a href="/attendance" class="{{ 'active' if active=='attendance' else '' }}">출퇴근관리</a>
        <a href="/records" class="{{ 'active' if active=='records' else '' }}">기록조회</a>
        <a href="/payroll" class="{{ 'active' if active=='payroll' else '' }}">급여관리</a>
        <a href="/settings" class="{{ 'active' if active=='settings' else '' }}">설정</a>
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


def render_page(
    title: str,
    active: str,
    content: str,
    quick_links: list[dict[str, str]] | None = None,
) -> str:
    return render_template_string(
        BASE_HTML,
        title=title,
        active=active,
        content=content,
        quick_links=quick_links or [],
    )


def render_company_options(selected_company_id: int | None = None) -> str:
    options = []
    for company in companies:
        selected = "selected" if company["id"] == selected_company_id else ""
        use_label = "사용" if company["is_active"] else "미사용"
        options.append(
            f'<option value="{company["id"]}" {selected}>{company["name"]} ({use_label})</option>'
        )
    return "".join(options)


def render_work_type_options(company_id: int, selected_work_type_id: int | None = None) -> str:
    options = []
    for work_type in get_company_work_types(company_id):
        selected = "selected" if work_type["id"] == selected_work_type_id else ""
        options.append(f'<option value="{work_type["id"]}" {selected}>{work_type["name"]}</option>')
    return "".join(options)


@app.route("/")
def home() -> str:
    current_date = request.args.get("work_date", today_str())
    company_id_raw = request.args.get("company_id", "")
    company_id = int(company_id_raw) if company_id_raw.isdigit() else None
    filtered_employees = get_employees_by_company(company_id)

    total = len(filtered_employees)
    before_count = count_status_for_company(company_id, current_date, "before_work")
    working_count = count_status_for_company(company_id, current_date, "working")
    completed_count = count_status_for_company(company_id, current_date, "completed")
    hospital_count = count_status_for_company(company_id, current_date, "hospital")
    absent_count = count_status_for_company(company_id, current_date, "absent")

    rows = ""
    for employee in filtered_employees:
        company_name = get_company_name(employee["company_id"])
        work_type_name = get_work_type_name(employee["work_type_id"])
        display_status = get_display_status(employee["id"], current_date)
        rows += f"""
        <tr>
            <td>{employee["id"]}</td>
            <td><a href="/employees/{employee["id"]}">{employee["name"]}</a></td>
            <td>{employee["nationality"]}</td>
            <td>{company_name}</td>
            <td>{work_type_name}</td>
            <td>{status_badge(display_status)}</td>
        </tr>
        """

    if not rows:
        rows = '<tr><td colspan="6">사원이 없습니다.</td></tr>'

    company_options = ['<option value="">전체 회사</option>']
    for company in companies:
        selected = "selected" if company_id == company["id"] else ""
        company_options.append(
            f'<option value="{company["id"]}" {selected}>{company["name"]}</option>'
        )

    content = f"""
    <div class="notice">
        현재 구조는 운영형 흐름에 맞춘 메모리 기반 MVP입니다.
        서버 재시작 시 데이터는 초기화됩니다.
    </div>

    <form method="get" class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <div class="form-grid">
                <div>
                    <label>조회 날짜</label>
                    <input type="date" name="work_date" value="{current_date}">
                </div>
                <div>
                    <label>회사 선택</label>
                    <select name="company_id">{"".join(company_options)}</select>
                </div>
            </div>
            <div class="actions">
                <button class="btn btn-white" type="submit">조회</button>
                <a class="btn btn-white" href="/">초기화</a>
            </div>
        </div>
    </form>

    <div class="cards">
        <div class="card"><div class="label">전체 사원</div><div class="value">{total}</div></div>
        <div class="card"><div class="label">출근전</div><div class="value">{before_count}</div></div>
        <div class="card"><div class="label">근무중</div><div class="value">{working_count}</div></div>
        <div class="card"><div class="label">퇴근완료</div><div class="value">{completed_count}</div></div>
        <div class="card"><div class="label">병원</div><div class="value">{hospital_count}</div></div>
        <div class="card"><div class="label">결근</div><div class="value">{absent_count}</div></div>
    </div>

    <div class="content-grid">
        <div class="panel">
            <div class="panel-head">
                <h2>사원 현황</h2>
                <p>{current_date} 기준 상태</p>
            </div>
            <div class="panel-body">
                <table>
                    <thead>
                        <tr>
                            <th>사번</th>
                            <th>이름</th>
                            <th>국적</th>
                            <th>회사</th>
                            <th>근무타입</th>
                            <th>상태</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>

        <div>
            <div class="panel" style="margin-bottom:18px;">
                <div class="panel-head">
                    <h2>빠른 작업</h2>
                    <p>관리자 직접 처리</p>
                </div>
                <div class="panel-body">
                    <div class="actions" style="margin-top:0;">
                        <a class="btn btn-primary" href="/companies/new">회사등록</a>
                        <a class="btn btn-primary" href="/employees/new">사원등록</a>
                        <a class="btn btn-green" href="/attendance">출퇴근관리</a>
                        <a class="btn btn-sky" href="/records">기록조회</a>
                        <a class="btn btn-orange" href="/payroll">급여관리</a>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-head">
                    <h2>운영 기준</h2>
                    <p>1차 운영 버전 핵심 구조</p>
                </div>
                <div class="panel-body">
                    <ul style="margin:0; padding-left:18px; line-height:1.8;">
                        <li>멀티회사 관리</li>
                        <li>회사별 근무타입 설정</li>
                        <li>관리자 입력형 출퇴근</li>
                        <li>직원 앱은 조회 중심</li>
                        <li>출퇴근 기록 기반 급여 계산</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page("메인", "home", content)


@app.route("/companies")
def companies_page() -> str:
    rows = ""
    for company in companies:
        active_label = "사용" if company["is_active"] else "미사용"
        rows += f"""
        <tr>
            <td>{company["id"]}</td>
            <td><a href="/companies/{company["id"]}">{company["name"]}</a></td>
            <td>{company["business_number"]}</td>
            <td>{company["phone"]}</td>
            <td>{active_label}</td>
            <td class="table-actions">
                <a class="btn btn-white" href="/companies/{company["id"]}">상세</a>
                <a class="btn btn-white" href="/companies/{company["id"]}/settings">설정</a>
            </td>
        </tr>
        """

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>회사목록</h2>
            <p>멀티회사 기본정보 및 설정 관리</p>
        </div>
        <div class="panel-body">
            <div class="actions" style="margin-top:0; margin-bottom:16px;">
                <a class="btn btn-primary" href="/companies/new">+ 회사등록</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>번호</th>
                        <th>회사명</th>
                        <th>사업자등록번호</th>
                        <th>대표전화</th>
                        <th>사용여부</th>
                        <th>관리</th>
                    </tr>
                </thead>
                <tbody>{rows or '<tr><td colspan="6">회사가 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "회사목록", "href": "/companies"},
        {"label": "회사등록", "href": "/companies/new"},
    ]
    return render_page("회사관리", "companies", content, quick)


@app.route("/companies/new", methods=["GET", "POST"])
def company_new() -> str:
    if request.method == "POST":
        company_id = next_id(companies)
        is_active = request.form.get("is_active", "Y") == "Y"

        companies.append(
            {
                "id": company_id,
                "name": request.form["name"].strip(),
                "ceo_name": request.form["ceo_name"].strip(),
                "business_number": request.form["business_number"].strip(),
                "phone": request.form["phone"].strip(),
                "address": request.form["address"].strip(),
                "business_type": request.form.get("business_type", "").strip(),
                "business_item": request.form.get("business_item", "").strip(),
                "email": request.form.get("email", "").strip(),
                "is_active": is_active,
                "memo": request.form.get("memo", "").strip(),
                "created_at": today_str(),
                "updated_at": today_str(),
            }
        )

        company_settings.append(
            {
                "company_id": company_id,
                "attendance_open_time": "08:00",
                "late_standard_time": "09:00",
                "workday_standard_hours": 8,
                "hospital_paid": True,
                "document_view_policy": "sensitive_super_admin_only",
                "created_at": today_str(),
                "updated_at": today_str(),
            }
        )

        company_payroll_settings.append(
            {
                "company_id": company_id,
                "default_pay_type": "monthly",
                "base_salary": 2000000,
                "daily_wage": 100000,
                "hourly_wage": 10000,
                "night_allowance_rate": 1.5,
                "overtime_allowance_rate": 1.5,
                "hospital_pay_type": "paid",
                "absence_deduction_amount": 80000,
                "meal_allowance": 0,
                "transport_allowance": 0,
                "position_allowance": 0,
                "created_at": today_str(),
                "updated_at": today_str(),
            }
        )

        company_work_types.append(
            {"id": next_id(company_work_types), "company_id": company_id, "name": "주간", "code": "DAY", "is_active": True}
        )
        company_work_types.append(
            {"id": next_id(company_work_types), "company_id": company_id, "name": "야간", "code": "NIGHT", "is_active": True}
        )

        return redirect(url_for("companies_page"))

    content = """
    <div class="panel">
        <div class="panel-head">
            <h2>회사등록</h2>
            <p>회사 기본정보와 초기 설정 생성</p>
        </div>
        <div class="panel-body">
            <form method="post">
                <div class="form-grid">
                    <div><label>회사명</label><input name="name" required></div>
                    <div><label>대표자명</label><input name="ceo_name" required></div>
                    <div><label>사업자등록번호</label><input name="business_number" placeholder="123-45-67890" required></div>
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
                    <a class="btn btn-white" href="/companies">취소</a>
                </div>
            </form>
        </div>
    </div>
    """
    quick = [
        {"label": "회사목록", "href": "/companies"},
        {"label": "회사등록", "href": "/companies/new"},
    ]
    return render_page("회사등록", "companies", content, quick)


@app.route("/companies/<int:company_id>")
def company_detail(company_id: int) -> str:
    company = get_company(company_id)
    if not company:
        return "회사를 찾을 수 없습니다.", 404

    work_types = get_company_work_types(company_id)
    work_type_html = ", ".join(w["name"] for w in work_types) or "-"

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>회사상세</h2>
            <p>{company["name"]} 기본 정보</p>
        </div>
        <div class="panel-body">
            <table>
                <tr><th style="width:220px;">회사명</th><td>{company["name"]}</td></tr>
                <tr><th>대표자명</th><td>{company["ceo_name"]}</td></tr>
                <tr><th>사업자등록번호</th><td>{company["business_number"]}</td></tr>
                <tr><th>대표전화</th><td>{company["phone"]}</td></tr>
                <tr><th>주소</th><td>{company["address"]}</td></tr>
                <tr><th>업태</th><td>{company["business_type"] or '-'}</td></tr>
                <tr><th>종목</th><td>{company["business_item"] or '-'}</td></tr>
                <tr><th>이메일</th><td>{company["email"] or '-'}</td></tr>
                <tr><th>사용여부</th><td>{"사용" if company["is_active"] else "미사용"}</td></tr>
                <tr><th>근무타입</th><td>{work_type_html}</td></tr>
                <tr><th>메모</th><td>{company["memo"] or '-'}</td></tr>
            </table>
            <div class="actions">
                <a class="btn btn-white" href="/companies/{company_id}/settings">회사별 설정</a>
            </div>
        </div>
    </div>
    """
    quick = [
        {"label": "회사목록", "href": "/companies"},
        {"label": "회사상세", "href": f"/companies/{company_id}"},
        {"label": "회사별 설정", "href": f"/companies/{company_id}/settings"},
    ]
    return render_page("회사상세", "companies", content, quick)


@app.route("/companies/<int:company_id>/settings", methods=["GET", "POST"])
def company_settings_page(company_id: int) -> str:
    company = get_company(company_id)
    if not company:
        return "회사를 찾을 수 없습니다.", 404

    setting = get_company_setting(company_id)
    payroll_setting = get_company_payroll_setting(company_id)
    if not setting or not payroll_setting:
        return "회사 설정을 찾을 수 없습니다.", 404

    if request.method == "POST":
        form_type = request.form.get("form_type", "").strip()

        if form_type == "work_type_add":
            work_type_name = request.form.get("work_type_name", "").strip()
            if work_type_name:
                company_work_types.append(
                    {
                        "id": next_id(company_work_types),
                        "company_id": company_id,
                        "name": work_type_name,
                        "code": work_type_name.upper().replace(" ", "_")[:20],
                        "is_active": True,
                    }
                )
            return redirect(url_for("company_settings_page", company_id=company_id))

        if form_type == "company_setting_update":
            setting["attendance_open_time"] = request.form.get("attendance_open_time", "08:00")
            setting["late_standard_time"] = request.form.get("late_standard_time", "09:00")
            setting["workday_standard_hours"] = int(request.form.get("workday_standard_hours", 8) or 8)
            setting["hospital_paid"] = request.form.get("hospital_paid", "Y") == "Y"
            setting["updated_at"] = today_str()

            payroll_setting["default_pay_type"] = request.form.get("default_pay_type", "monthly")
            payroll_setting["base_salary"] = int(request.form.get("base_salary", 0) or 0)
            payroll_setting["daily_wage"] = int(request.form.get("daily_wage", 0) or 0)
            payroll_setting["hourly_wage"] = int(request.form.get("hourly_wage", 0) or 0)
            payroll_setting["night_allowance_rate"] = float(request.form.get("night_allowance_rate", 1.5) or 1.5)
            payroll_setting["overtime_allowance_rate"] = float(request.form.get("overtime_allowance_rate", 1.5) or 1.5)
            payroll_setting["hospital_pay_type"] = request.form.get("hospital_pay_type", "paid")
            payroll_setting["absence_deduction_amount"] = int(request.form.get("absence_deduction_amount", 0) or 0)
            payroll_setting["meal_allowance"] = int(request.form.get("meal_allowance", 0) or 0)
            payroll_setting["transport_allowance"] = int(request.form.get("transport_allowance", 0) or 0)
            payroll_setting["position_allowance"] = int(request.form.get("position_allowance", 0) or 0)
            payroll_setting["updated_at"] = today_str()
            return redirect(url_for("company_settings_page", company_id=company_id))

    work_type_rows = ""
    for index, work_type in enumerate(get_company_work_types(company_id), start=1):
        work_type_rows += f"""
        <tr>
            <td>{index}</td>
            <td>{work_type["name"]}</td>
            <td>{work_type["code"]}</td>
            <td>{"사용" if work_type["is_active"] else "미사용"}</td>
        </tr>
        """

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>회사별 설정</h2>
            <p>{company["name"]} 기준 설정</p>
        </div>
        <div class="panel-body">
            <div class="subtabs">
                <span class="active">기본설정</span>
                <span>근무타입설정</span>
                <span>출퇴기준설정</span>
                <span>문서설정</span>
                <span>권한설정</span>
                <span>급여설정</span>
            </div>

            <form method="post" class="panel" style="box-shadow:none; border-radius:14px; margin-bottom:16px;">
                <input type="hidden" name="form_type" value="company_setting_update">
                <div class="panel-head">
                    <h3>기본설정 / 출퇴기준 / 급여설정</h3>
                    <p>1차 운영형 통합 설정</p>
                </div>
                <div class="panel-body">
                    <div class="form-grid">
                        <div><label>출근 가능 시작시간</label><input name="attendance_open_time" value="{setting["attendance_open_time"]}"></div>
                        <div><label>지각 기준시간</label><input name="late_standard_time" value="{setting["late_standard_time"]}"></div>
                        <div><label>1일 기준 근무시간</label><input type="number" name="workday_standard_hours" value="{setting["workday_standard_hours"]}"></div>
                        <div>
                            <label>병원 유급 여부</label>
                            <select name="hospital_paid">
                                <option value="Y" {"selected" if setting["hospital_paid"] else ""}>유급</option>
                                <option value="N" {"selected" if not setting["hospital_paid"] else ""}>무급</option>
                            </select>
                        </div>
                        <div>
                            <label>기본 급여형태</label>
                            <select name="default_pay_type">
                                <option value="monthly" {"selected" if payroll_setting["default_pay_type"] == "monthly" else ""}>월급제</option>
                                <option value="daily" {"selected" if payroll_setting["default_pay_type"] == "daily" else ""}>일급제</option>
                                <option value="hourly" {"selected" if payroll_setting["default_pay_type"] == "hourly" else ""}>시급제</option>
                            </select>
                        </div>
                        <div><label>기본급</label><input type="number" name="base_salary" value="{payroll_setting["base_salary"]}"></div>
                        <div><label>일급</label><input type="number" name="daily_wage" value="{payroll_setting["daily_wage"]}"></div>
                        <div><label>시급</label><input type="number" name="hourly_wage" value="{payroll_setting["hourly_wage"]}"></div>
                        <div><label>야간수당 배율</label><input type="number" step="0.1" name="night_allowance_rate" value="{payroll_setting["night_allowance_rate"]}"></div>
                        <div><label>연장수당 배율</label><input type="number" step="0.1" name="overtime_allowance_rate" value="{payroll_setting["overtime_allowance_rate"]}"></div>
                        <div>
                            <label>병원 급여처리</label>
                            <select name="hospital_pay_type">
                                <option value="paid" {"selected" if payroll_setting["hospital_pay_type"] == "paid" else ""}>유급</option>
                                <option value="unpaid" {"selected" if payroll_setting["hospital_pay_type"] == "unpaid" else ""}>무급</option>
                            </select>
                        </div>
                        <div><label>결근 공제액</label><input type="number" name="absence_deduction_amount" value="{payroll_setting["absence_deduction_amount"]}"></div>
                        <div><label>식대</label><input type="number" name="meal_allowance" value="{payroll_setting["meal_allowance"]}"></div>
                        <div><label>교통비</label><input type="number" name="transport_allowance" value="{payroll_setting["transport_allowance"]}"></div>
                        <div><label>직책수당</label><input type="number" name="position_allowance" value="{payroll_setting["position_allowance"]}"></div>
                    </div>
                    <div class="actions">
                        <button class="btn btn-primary" type="submit">설정 저장</button>
                    </div>
                </div>
            </form>

            <div class="panel" style="box-shadow:none; border-radius:14px;">
                <div class="panel-head">
                    <h3>근무타입설정</h3>
                    <p>회사마다 다른 근무타입 직접 관리</p>
                </div>
                <div class="panel-body">
                    <form method="post" class="actions" style="margin-top:0; margin-bottom:16px;">
                        <input type="hidden" name="form_type" value="work_type_add">
                        <div style="min-width:260px;">
                            <label>근무타입명</label>
                            <input name="work_type_name" placeholder="예: 주간 / 야간 / 1조 / 2조">
                        </div>
                        <div>
                            <button class="btn btn-primary" type="submit">근무타입 추가</button>
                        </div>
                    </form>

                    <table>
                        <thead>
                            <tr>
                                <th>순서</th>
                                <th>근무타입명</th>
                                <th>코드</th>
                                <th>사용여부</th>
                            </tr>
                        </thead>
                        <tbody>{work_type_rows or '<tr><td colspan="4">근무타입이 없습니다.</td></tr>'}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    """
    quick = [
        {"label": "회사목록", "href": "/companies"},
        {"label": "회사상세", "href": f"/companies/{company_id}"},
        {"label": "회사별 설정", "href": f"/companies/{company_id}/settings"},
    ]
    return render_page("회사별 설정", "companies", content, quick)


@app.route("/employees")
def employees_page() -> str:
    company_id_raw = request.args.get("company_id", "")
    company_id = int(company_id_raw) if company_id_raw.isdigit() else None

    rows = ""
    for employee in get_employees_by_company(company_id):
        company_name = get_company_name(employee["company_id"])
        work_type_name = get_work_type_name(employee["work_type_id"])
        rows += f"""
        <tr>
            <td>{employee["id"]}</td>
            <td><a href="/employees/{employee["id"]}">{employee["name"]}</a></td>
            <td>{employee["nationality"]}</td>
            <td>{company_name}</td>
            <td>{work_type_name}</td>
            <td>{PAY_TYPE_LABELS.get(employee["pay_type"], "-")}</td>
            <td>{status_badge(get_today_status(employee["id"]))}</td>
        </tr>
        """

    filter_options = ['<option value="">전체 회사</option>']
    for company in companies:
        selected = "selected" if company["id"] == company_id else ""
        filter_options.append(
            f'<option value="{company["id"]}" {selected}>{company["name"]}</option>'
        )

    content = f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <div style="min-width:260px;">
                    <label>회사 필터</label>
                    <select name="company_id">{"".join(filter_options)}</select>
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
            <h2>사원목록</h2>
            <p>회사 / 근무타입 / 급여형태 기준 관리</p>
        </div>
        <div class="panel-body">
            <div class="actions" style="margin-top:0; margin-bottom:16px;">
                <a class="btn btn-primary" href="/employees/new">사원등록</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>사번</th>
                        <th>이름</th>
                        <th>국적</th>
                        <th>회사</th>
                        <th>근무타입</th>
                        <th>급여형태</th>
                        <th>오늘 상태</th>
                    </tr>
                </thead>
                <tbody>{rows or '<tr><td colspan="7">사원이 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "사원목록", "href": "/employees"},
        {"label": "사원등록", "href": "/employees/new"},
    ]
    return render_page("사원관리", "employees", content, quick)


@app.route("/employees/new", methods=["GET", "POST"])
def employee_new() -> str:
    if not companies:
        return "먼저 회사를 등록하세요.", 400

    selected_company_raw = request.values.get("company_id", str(companies[0]["id"]))
    selected_company_id = int(selected_company_raw) if selected_company_raw.isdigit() else companies[0]["id"]

    work_types = get_company_work_types(selected_company_id)
    if not work_types:
        return "선택한 회사의 근무타입이 없습니다.", 400

    if request.method == "POST":
        employee_id = next_id(employees)
        employees.append(
            {
                "id": employee_id,
                "company_id": int(request.form["company_id"]),
                "name": request.form["name"].strip(),
                "nationality": request.form["nationality"].strip(),
                "phone": request.form.get("phone", "").strip(),
                "hire_date": request.form.get("hire_date", today_str()),
                "status": "active",
                "work_type_id": int(request.form["work_type_id"]),
                "pay_type": request.form.get("pay_type", "monthly"),
                "created_at": today_str(),
                "updated_at": today_str(),
            }
        )
        return redirect(url_for("employees_page"))

    company_options = render_company_options(selected_company_id)
    work_type_options = render_work_type_options(selected_company_id)

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>사원등록</h2>
            <p>회사별 근무타입과 급여형태 기준 입력</p>
        </div>
        <div class="panel-body">
            <form method="get" class="panel" style="box-shadow:none; border-radius:14px; margin-bottom:16px;">
                <div class="panel-body">
                    <div class="form-grid">
                        <div>
                            <label>회사 선택</label>
                            <select name="company_id" onchange="this.form.submit()">{company_options}</select>
                        </div>
                        <div class="muted" style="padding-top:32px;">
                            회사 변경 시 해당 회사의 근무타입 목록으로 갱신됩니다.
                        </div>
                    </div>
                </div>
            </form>

            <form method="post">
                <input type="hidden" name="company_id" value="{selected_company_id}">
                <div class="form-grid">
                    <div><label>회사</label><input value="{get_company_name(selected_company_id)}" disabled></div>
                    <div><label>이름</label><input name="name" placeholder="예: 성조" required></div>
                    <div><label>국적</label><input name="nationality" placeholder="예: 한국" required></div>
                    <div><label>연락처</label><input name="phone" placeholder="010-0000-0000"></div>
                    <div><label>입사일</label><input type="date" name="hire_date" value="{today_str()}"></div>
                    <div>
                        <label>급여형태</label>
                        <select name="pay_type">
                            <option value="monthly">월급제</option>
                            <option value="daily">일급제</option>
                            <option value="hourly">시급제</option>
                        </select>
                    </div>
                    <div style="grid-column: 1 / -1;">
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
        {"label": "사원목록", "href": "/employees"},
        {"label": "사원등록", "href": "/employees/new"},
    ]
    return render_page("사원등록", "employees", content, quick)


@app.route("/employees/<int:employee_id>", methods=["GET", "POST"])
def employee_detail(employee_id: int) -> str:
    employee = get_employee(employee_id)
    if not employee:
        return "사원을 찾을 수 없습니다.", 404

    if request.method == "POST":
        file_name = request.form.get("file_name", "").strip() or "unnamed.pdf"
        employee_documents.append(
            {
                "id": next_id(employee_documents),
                "employee_id": employee_id,
                "document_type": request.form.get("document_type", "other"),
                "file_name": file_name,
                "file_path": f"/uploads/{file_name}",
                "file_mime_type": request.form.get("file_mime_type", "application/pdf"),
                "is_sensitive": request.form.get("is_sensitive", "Y") == "Y",
                "uploaded_by": "super_admin",
                "created_at": today_str(),
            }
        )
        return redirect(url_for("employee_detail", employee_id=employee_id))

    company_name = get_company_name(employee["company_id"])
    work_type_name = get_work_type_name(employee["work_type_id"])
    attendance_rows = ""

    employee_records = sorted(
        [r for r in attendance_records if r["employee_id"] == employee_id],
        key=lambda item: item["work_date"],
        reverse=True,
    )
    for index, record in enumerate(employee_records, start=1):
        attendance_rows += f"""
        <tr>
            <td>{index}</td>
            <td>{record["work_date"]}</td>
            <td>{get_work_type_name(record["work_type_id"])}</td>
            <td>{record["check_in_at"] or '-'}</td>
            <td>{record["check_out_at"] or '-'}</td>
            <td>{status_badge(record["status"])}</td>
            <td>{record["reason"] or '-'}</td>
        </tr>
        """

    document_rows = ""
    for index, document in enumerate(get_employee_documents(employee_id), start=1):
        document_rows += f"""
        <tr>
            <td>{index}</td>
            <td>{DOCUMENT_TYPE_LABELS.get(document["document_type"], document["document_type"])}</td>
            <td>{document["file_name"]}</td>
            <td>{document["file_mime_type"]}</td>
            <td>{'민감' if document["is_sensitive"] else '일반'}</td>
            <td>{document["created_at"]}</td>
        </tr>
        """

    content = f"""
    <div class="two-col">
        <div class="side-box" style="padding:14px;">
            <h3 style="margin:0 0 12px;">사원 사진</h3>
            <div class="photo-box">사진 등록 영역</div>
            <div class="actions">
                <button class="btn btn-primary" type="button">사진 등록</button>
                <button class="btn btn-white" type="button">사진 변경</button>
            </div>
        </div>

        <div>
            <div class="panel" style="margin-bottom:18px;">
                <div class="panel-head">
                    <h2>사원상세</h2>
                    <p>기본정보 / 문서 / 출퇴근 기록 연결</p>
                </div>
                <div class="panel-body">
                    <table>
                        <tr><th style="width:220px;">이름</th><td>{employee["name"]}</td></tr>
                        <tr><th>국적</th><td>{employee["nationality"]}</td></tr>
                        <tr><th>회사</th><td>{company_name}</td></tr>
                        <tr><th>근무타입</th><td>{work_type_name}</td></tr>
                        <tr><th>연락처</th><td>{employee["phone"] or '-'}</td></tr>
                        <tr><th>입사일</th><td>{employee["hire_date"]}</td></tr>
                        <tr><th>급여형태</th><td>{PAY_TYPE_LABELS.get(employee["pay_type"], '-')}</td></tr>
                        <tr><th>오늘 상태</th><td>{status_badge(get_today_status(employee_id))}</td></tr>
                    </table>
                </div>
            </div>

            <div class="panel">
                <div class="panel-head">
                    <h2>문서 등록</h2>
                    <p>PDF / JPG 등 파일 메타데이터 등록</p>
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
        {"label": "사원목록", "href": "/employees"},
        {"label": "사원등록", "href": "/employees/new"},
    ]
    return render_page("사원상세", "employees", content, quick)


@app.route("/attendance", methods=["GET", "POST"])
def attendance_page() -> str:
    selected_date = request.values.get("work_date", today_str())
    selected_company_raw = request.values.get("company_id", "")
    selected_company_id = int(selected_company_raw) if selected_company_raw.isdigit() else None

    if request.method == "POST":
        update_attendance(
            employee_id=int(request.form["employee_id"]),
            work_date=request.form["work_date"],
            action_type=request.form["action_type"],
            reason=request.form.get("reason", "").strip(),
            overtime_minutes=int(request.form.get("overtime_minutes", 0) or 0),
            night_minutes=int(request.form.get("night_minutes", 0) or 0),
        )
        redirect_company_id = request.form.get("company_id", "")
        return redirect(
            url_for(
                "attendance_page",
                work_date=request.form["work_date"],
                company_id=redirect_company_id,
            )
        )

    employee_list = get_employees_by_company(selected_company_id)
    company_filter_options = ['<option value="">전체 회사</option>']
    for company in companies:
        selected = "selected" if selected_company_id == company["id"] else ""
        company_filter_options.append(
            f'<option value="{company["id"]}" {selected}>{company["name"]}</option>'
        )

    employee_options = ""
    for employee in employee_list:
        company_name = get_company_name(employee["company_id"])
        employee_options += (
            f'<option value="{employee["id"]}">'
            f'{employee["name"]} / {employee["nationality"]} / {company_name} / {get_work_type_name(employee["work_type_id"])}'
            f"</option>"
        )

    rows = ""
    for employee in employee_list:
        record = get_attendance_record(employee["id"], selected_date)
        rows += f"""
        <tr>
            <td>{employee["name"]}</td>
            <td>{employee["nationality"]}</td>
            <td>{get_company_name(employee["company_id"])}</td>
            <td>{get_work_type_name(employee["work_type_id"])}</td>
            <td>{status_badge(record["status"] if record else "before_work")}</td>
            <td>{record["check_in_at"] if record and record["check_in_at"] else '-'}</td>
            <td>{record["check_out_at"] if record and record["check_out_at"] else '-'}</td>
            <td>{record["reason"] if record and record["reason"] else '-'}</td>
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
                        <label>회사 선택</label>
                        <select name="company_id">{"".join(company_filter_options)}</select>
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
                            <th>회사</th>
                            <th>근무타입</th>
                            <th>상태</th>
                            <th>출근</th>
                            <th>퇴근</th>
                            <th>사유</th>
                        </tr>
                    </thead>
                    <tbody>{rows or '<tr><td colspan="8">사원이 없습니다.</td></tr>'}</tbody>
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
                    <input type="hidden" name="company_id" value="{selected_company_id or ''}">

                    <label>사원 선택</label>
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
    selected_company_raw = request.args.get("company_id", "")
    selected_company_id = int(selected_company_raw) if selected_company_raw.isdigit() else None
    selected_month = request.args.get("month", month_str_default())
    selected_tab = request.args.get("tab", "all")
    year, month = parse_month(selected_month)

    company_filter_options = ['<option value="">전체 회사</option>']
    for company in companies:
        selected = "selected" if selected_company_id == company["id"] else ""
        company_filter_options.append(
            f'<option value="{company["id"]}" {selected}>{company["name"]}</option>'
        )

    subtabs = f"""
    <div class="subtabs">
        <a class="{'active' if selected_tab == 'all' else ''}" href="/records?tab=all&company_id={selected_company_id or ''}&month={selected_month}">전체 출퇴기록</a>
        <a class="{'active' if selected_tab == 'monthly' else ''}" href="/records?tab=monthly&company_id={selected_company_id or ''}&month={selected_month}">월별 출석현황</a>
    </div>
    """

    filter_form = f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <input type="hidden" name="tab" value="{selected_tab}">
                <div>
                    <label>회사 필터</label>
                    <select name="company_id">{"".join(company_filter_options)}</select>
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
        employees_for_grid = get_employees_by_company(selected_company_id)

        header_days = "".join(f"<th>{day}</th>" for day in range(1, days_in_month + 1))
        month_rows = ""

        for employee in employees_for_grid:
            monthly_map = get_month_attendance_map(employee["id"], year, month)
            present_cnt = 0
            hospital_cnt = 0
            absent_cnt = 0
            vacation_cnt = 0
            off_cnt = 0

            month_rows += (
                f'<tr><td class="name-col"><a href="/employees/{employee["id"]}">{employee["name"]}</a></td>'
                f'<td class="nation-col">{employee["nationality"]}</td>'
            )

            for day in range(1, days_in_month + 1):
                record = monthly_map.get(day)
                day_mark = get_day_mark(record)
                weekday = datetime(year, month, day).weekday()

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
                    <tbody>{month_rows or '<tr><td colspan="100">사원이 없습니다.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        """
    else:
        filtered_records = []
        for record in attendance_records:
            dt = parse_date(record["work_date"])
            if dt.year != year or dt.month != month:
                continue
            if selected_company_id and record["company_id"] != selected_company_id:
                continue
            filtered_records.append(record)

        filtered_records.sort(
            key=lambda item: (item["work_date"], item["employee_id"]),
            reverse=True,
        )

        record_rows = ""
        for index, record in enumerate(filtered_records, start=1):
            employee = get_employee(record["employee_id"])
            if not employee:
                continue

            record_rows += f"""
            <tr>
                <td>{index}</td>
                <td>{record["work_date"]}</td>
                <td><a href="/employees/{employee["id"]}">{employee["name"]}</a></td>
                <td>{employee["nationality"]}</td>
                <td>{get_company_name(record["company_id"])}</td>
                <td>{get_work_type_name(record["work_type_id"])}</td>
                <td>{record["check_in_at"] or '-'}</td>
                <td>{record["check_out_at"] or '-'}</td>
                <td>{status_badge(record["status"])}</td>
                <td>{record["reason"] or '-'}</td>
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
                            <th>사원명</th>
                            <th>국적</th>
                            <th>회사</th>
                            <th>근무타입</th>
                            <th>출근</th>
                            <th>퇴근</th>
                            <th>상태</th>
                            <th>사유</th>
                        </tr>
                    </thead>
                    <tbody>{record_rows or '<tr><td colspan="10">기록이 없습니다.</td></tr>'}</tbody>
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
    selected_company_raw = request.args.get("company_id", str(companies[0]["id"]) if companies else "")
    selected_company_id = int(selected_company_raw) if selected_company_raw.isdigit() else None
    selected_month = request.args.get("month", month_str_default())
    year, month = parse_month(selected_month)

    filtered_employees = get_employees_by_company(selected_company_id)
    rows = ""
    total_final_amount = 0

    for employee in filtered_employees:
        payroll = calculate_payroll_for_employee(employee, year, month)
        total_final_amount += payroll["final_amount"]

        rows += f"""
        <tr>
            <td><a href="/employees/{employee["id"]}">{employee["name"]}</a></td>
            <td>{employee["nationality"]}</td>
            <td>{PAY_TYPE_LABELS.get(employee["pay_type"], '-')}</td>
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

    company_options = []
    for company in companies:
        selected = "selected" if company["id"] == selected_company_id else ""
        company_options.append(
            f'<option value="{company["id"]}" {selected}>{company["name"]}</option>'
        )

    company_name = get_company_name(selected_company_id) if selected_company_id else "-"
    content = f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <div>
                    <label>회사 선택</label>
                    <select name="company_id">{"".join(company_options)}</select>
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
        <div class="card"><div class="label">회사</div><div class="value" style="font-size:22px;">{company_name}</div></div>
        <div class="card"><div class="label">대상 월</div><div class="value" style="font-size:22px;">{selected_month}</div></div>
        <div class="card"><div class="label">대상 사원</div><div class="value">{len(filtered_employees)}</div></div>
        <div class="card"><div class="label">총 실지급액</div><div class="value" style="font-size:22px;">{format_won(total_final_amount)}</div></div>
    </div>

    <div class="panel">
        <div class="panel-head">
            <h2>급여대장</h2>
            <p>출퇴근 기록 기반 계산 결과</p>
        </div>
        <div class="panel-body">
            <div class="actions" style="margin-top:0; margin-bottom:16px;">
                <button class="btn btn-primary" type="button">급여 계산 실행</button>
                <button class="btn btn-white" type="button">엑셀 다운로드</button>
            </div>
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
                <tbody>{rows or '<tr><td colspan="13">사원이 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "급여계산", "href": "/payroll"},
        {"label": "급여대장", "href": "/payroll"},
        {"label": "사원별 급여조회", "href": "/payroll"},
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
                <tr><th style="width:220px;">최고관리자</th><td>웹 사용 가능 / 앱 사용 가능 / 민감 문서 열람 가능</td></tr>
                <tr><th>부관리자</th><td>앱만 사용 가능 / 출퇴근 처리 / 기록 조회</td></tr>
                <tr><th>직원</th><td>앱 조회 중심 / 직접 출퇴근 불가</td></tr>
                <tr><th>문서 권한</th><td>민감 문서는 최고관리자만 열람 가능</td></tr>
                <tr><th>출퇴근 정책</th><td>직원이 아니라 관리자가 직접 처리</td></tr>
                <tr><th>근무타입</th><td>회사별 개별 설정, 공통 고정값 사용 안 함</td></tr>
            </table>
        </div>
    </div>
    """
    return render_page("설정", "settings", content)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

이 파일로 교체하면 해결될 가능성이 가장 큽니다.
그래도 에러가 나면 **에러 한 줄만** 보내주세요. 바로 그 줄 기준으로 잡겠습니다.
