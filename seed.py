
from models import (
    AdminMenu,
    AdminPage,
    UiLabel,
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


def _seed_ui_defaults() -> None:
    menu_defaults = [
        ("home", "홈", "", "/", 1),
        ("employees", "직원관리", "", "/employees", 2),
        ("attendance", "근태관리", "", "/attendance", 3),
        ("company", "회사관리", "", "/client-companies", 4),
        ("our_businesses", "사업자관리", "company", "/our-businesses", 1),
        ("client_companies", "거래처관리", "company", "/client-companies", 2),
        ("payroll", "급여관리", "", "/payroll", 5),
        ("records", "기록조회", "", "/records", 6),
        ("settings", "설정", "", "/settings", 7),
        ("admin", "관리자", "", "/admin", 8),
        ("admin_home", "관리자 홈", "admin", "/admin", 1),
        ("admin_menus", "메뉴관리", "admin", "/admin/menus", 2),
        ("admin_labels", "문구관리", "admin", "/admin/labels", 3),
    ]
    for code, name, parent_code, route_path, sort_order in menu_defaults:
        item = AdminMenu.query.filter_by(code=code).first()
        if item is None:
            db.session.add(
                AdminMenu(
                    code=code,
                    name=name,
                    parent_code=parent_code,
                    route_path=route_path,
                    sort_order=sort_order,
                    is_active=True,
                )
            )

    page_defaults = [
        ("home", "홈", "/", "main", "홈 대시보드"),
        ("employees", "직원관리", "/employees", "main", "직원 목록과 등록"),
        ("attendance", "근태관리", "/attendance", "main", "출퇴근 및 상태 관리"),
        ("client_companies", "거래처관리", "/client-companies", "main", "거래처 관리"),
        ("our_businesses", "사업자관리", "/our-businesses", "main", "우리 사업자 관리"),
        ("payroll", "급여관리", "/payroll", "main", "급여 계산 및 요약"),
        ("records", "기록조회", "/records", "main", "기록 조회"),
        ("settings", "설정", "/settings", "main", "기본 설정"),
        ("admin_home", "관리자 홈", "/admin", "admin", "관리자 운영 현황 대시보드"),
        ("menu_management", "메뉴관리", "/admin/menus", "admin", "메뉴 구조와 링크 관리"),
        ("label_management", "문구관리", "/admin/labels", "admin", "메뉴명, 제목, 버튼명 관리"),
    ]
    for page_key, page_name, route_path, category, description in page_defaults:
        item = AdminPage.query.filter_by(page_key=page_key).first()
        if item is None:
            db.session.add(
                AdminPage(
                    page_key=page_key,
                    page_name=page_name,
                    route_path=route_path,
                    category=category,
                    description=description,
                    is_active=True,
                )
            )

    label_defaults = [
        ("home_page_title", "홈", "page", "브라우저 타이틀과 홈 제목"),
        ("home_hero_title", "오늘의 인력 운영 상황을 한 번에 확인하세요", "home", "홈 상단 대표 제목"),
        ("home_hero_description", "상태 카드와 검색, 거래처 필터를 한 흐름으로 확인할 수 있습니다.", "home", "홈 상단 설명"),
        ("home_notice_text", "홈 화면은 요약 중심으로, 근태·직원·기록 기능은 상단 메뉴에서 분리해 중복 느낌을 줄였습니다.", "home", "홈 안내 문구"),
        ("home_filter_apply_button", "조회 적용", "button", "홈 조회 버튼"),
        ("home_filter_reset_button", "전체 초기화", "button", "홈 초기화 버튼"),
        ("home_search_panel_title", "사원검색", "home", "홈 검색 패널 제목"),
        ("home_search_panel_description", "이름 검색과 상세 선택 흐름을 간단하게 유지합니다.", "home", "홈 검색 패널 설명"),
        ("home_card_total", "전체", "dashboard_card", "홈 전체 카드 제목"),
        ("home_card_before_work", "출근전", "dashboard_card", "홈 출근전 카드 제목"),
        ("home_card_working", "근무중", "dashboard_card", "홈 근무중 카드 제목"),
        ("home_card_completed", "퇴근완료", "dashboard_card", "홈 퇴근완료 카드 제목"),
        ("home_card_hospital", "병원", "dashboard_card", "홈 병원 카드 제목"),
        ("home_card_absent", "결근", "dashboard_card", "홈 결근 카드 제목"),
        ("admin_home_title", "관리자 홈", "admin", "관리자 홈 제목"),
        ("admin_home_description", "홈페이지처럼 한눈에 보는 운영 현황과 1단계 관리 기능 진입 화면입니다.", "admin", "관리자 홈 설명"),
        ("admin_menu_title", "메뉴관리", "admin", "메뉴관리 화면 제목"),
        ("admin_menu_description", "상단 메뉴명, 순서, 노출 여부, 상하위 메뉴, URL을 수정합니다.", "admin", "메뉴관리 설명"),
        ("admin_label_title", "문구관리", "admin", "문구관리 화면 제목"),
        ("admin_label_description", "페이지 제목, 버튼 문구, 안내 문구, 카드 제목을 수정합니다.", "admin", "문구관리 설명"),
        ("admin_card_businesses", "사업자", "dashboard_card", "관리자 카드 제목"),
        ("admin_card_clients", "거래처", "dashboard_card", "관리자 카드 제목"),
        ("admin_card_employees", "직원", "dashboard_card", "관리자 카드 제목"),
        ("admin_card_menus", "메뉴", "dashboard_card", "관리자 카드 제목"),
        ("admin_card_labels", "문구", "dashboard_card", "관리자 카드 제목"),
        ("button_save", "저장", "button", "공통 저장 버튼"),
        ("button_add", "추가", "button", "공통 추가 버튼"),
    ]
    for label_key, label_text, category, description in label_defaults:
        item = UiLabel.query.filter_by(label_key=label_key).first()
        if item is None:
            db.session.add(
                UiLabel(
                    label_key=label_key,
                    label_text=label_text,
                    category=category,
                    description=description,
                    is_active=True,
                )
            )


def seed_database() -> None:
    _seed_ui_defaults()
    db.session.commit()

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
