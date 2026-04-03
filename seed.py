from models import (
    AttendanceRecord,
    ClientCompany,
    ClientCompanyPayrollSetting,
    ClientCompanySetting,
    ClientCompanyWorkType,
    Employee,
    EmployeeDocument,
    OurBusiness,
    db,
)
from utils import today_str


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
