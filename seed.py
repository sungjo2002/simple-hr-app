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


def _seed_admin_defaults() -> None:
    menu_defaults = [
        ("home", "홈", "", "/", 1, True),
        ("employees", "직원관리", "", "/employees", 2, True),
        ("attendance", "근태관리", "", "/attendance", 3, True),
        ("company_management", "회사관리", "", "/client-companies", 4, True),
        ("our_businesses", "사업자관리", "company_management", "/our-businesses", 1, True),
        ("client_companies", "거래처관리", "company_management", "/client-companies", 2, True),
        ("payroll", "급여관리", "", "/payroll", 5, True),
        ("records", "기록조회", "", "/records", 6, True),
        ("settings", "설정", "", "/settings", 7, True),
        ("admin_shortcut", "관리자", "", "/admin", 8, True),
    ]
    for code, name, parent_code, route_path, sort_order, is_active in menu_defaults:
        item = AdminMenu.query.filter_by(code=code).first()
        if item is None:
            item = AdminMenu(
                code=code,
                name=name,
                parent_code=parent_code,
                route_path=route_path,
                sort_order=sort_order,
                is_active=is_active,
            )
            db.session.add(item)

    page_defaults = [
        ("admin_dashboard", "관리자 홈", "/admin", "admin", "관리자 운영 요약"),
        ("menu_management", "메뉴관리", "/admin/menus", "admin", "사용자 메뉴 구조 관리"),
        ("label_management", "문구관리", "/admin/labels", "admin", "페이지/버튼/안내 문구 관리"),
    ]
    for page_key, page_name, route_path, category, description in page_defaults:
        item = AdminPage.query.filter_by(page_key=page_key).first()
        if item is None:
            item = AdminPage(
                page_key=page_key,
                page_name=page_name,
                route_path=route_path,
                category=category,
                description=description,
                is_active=True,
            )
            db.session.add(item)

    label_defaults = [
        ("app_brand_name", "멀티사업자 인력·근태·급여 관리", "brand", "사용자 화면 서비스명"),
        ("app_brand_kicker", "multi business hr", "brand", "사용자 화면 상단 작은 제목"),
        ("app_brand_desc", "인력, 근태, 급여를 한 화면 흐름으로 관리하는 운영 서비스입니다.", "brand", "사용자 화면 상단 설명"),
        ("home_page_title", "홈", "page", "홈 화면 브라우저 제목"),
        ("home_hero_title", "오늘 인력 운영 현황", "home", "홈 화면 제목"),
        ("home_hero_desc", "거래처별 인력 상황과 근태 현황을 한 번에 확인할 수 있습니다.", "home", "홈 화면 설명"),
        ("home_search_button", "조회", "button", "홈 조회 버튼"),
        ("home_reset_button", "초기화", "button", "홈 초기화 버튼"),
        ("home_card_total", "전체 인력", "dashboard", "홈 카드 제목"),
        ("home_card_before", "출근전", "dashboard", "홈 카드 제목"),
        ("home_card_working", "근무중", "dashboard", "홈 카드 제목"),
        ("home_card_completed", "퇴근완료", "dashboard", "홈 카드 제목"),
        ("home_card_hospital", "병원", "dashboard", "홈 카드 제목"),
        ("home_card_absent", "결근", "dashboard", "홈 카드 제목"),
        ("admin_entry_label", "관리자", "admin", "사용자 화면 관리자 진입 버튼"),
        ("admin_brand_name", "멀티사업자 관리자", "admin", "관리자 화면 서비스명"),
        ("admin_brand_kicker", "admin center", "admin", "관리자 화면 상단 작은 제목"),
        ("admin_brand_desc", "사용자 화면과 분리된 설정 전용 관리 영역입니다.", "admin", "관리자 영역 설명"),
        ("admin_back_to_service", "운영 화면으로 돌아가기", "admin", "관리자 하단 돌아가기 버튼"),
        ("admin_nav_home", "관리자 홈", "admin", "관리자 메뉴명"),
        ("admin_nav_menus", "메뉴관리", "admin", "관리자 메뉴명"),
        ("admin_nav_labels", "문구관리", "admin", "관리자 메뉴명"),
        ("admin_home_title", "관리자 홈", "admin", "관리자 홈 제목"),
        ("admin_home_desc", "운영 현황과 설정 작업을 시작하는 관리자 전용 첫 화면입니다.", "admin", "관리자 홈 설명"),
        ("admin_menu_title", "메뉴관리", "admin", "메뉴관리 제목"),
        ("admin_menu_desc", "사용자 상단 메뉴 이름, 순서, 노출, URL, 상하위 구조를 관리합니다.", "admin", "메뉴관리 설명"),
        ("admin_label_title", "문구관리", "admin", "문구관리 제목"),
        ("admin_label_desc", "페이지 제목, 버튼명, 안내문구, 카드 제목을 단계적으로 DB 기반으로 관리합니다.", "admin", "문구관리 설명"),
        ("admin_card_business", "사업자", "admin", "관리자 카드 제목"),
        ("admin_card_client", "거래처", "admin", "관리자 카드 제목"),
        ("admin_card_employee", "직원", "admin", "관리자 카드 제목"),
        ("admin_card_menu", "메뉴", "admin", "관리자 카드 제목"),
        ("admin_card_label", "문구", "admin", "관리자 카드 제목"),
    ]
    for label_key, label_text, category, description in label_defaults:
        item = UiLabel.query.filter_by(label_key=label_key).first()
        if item is None:
            item = UiLabel(
                label_key=label_key,
                label_text=label_text,
                category=category,
                description=description,
                is_active=True,
            )
            db.session.add(item)


def seed_database() -> None:
    _seed_admin_defaults()

    if OurBusiness.query.first():
        db.session.commit()
        return

    our1 = OurBusiness(
        name="에이스인력",
        ceo_name="김대표",
        business_number="111-11-11111",
        phone="02-1111-1111",
        business_type="서비스업",
        business_item="인력공급",
        email="ace@example.com",
        is_active=True,
    )
    our2 = OurBusiness(
        name="미래서비스",
        ceo_name="박대표",
        business_number="222-22-22222",
        phone="031-222-2222",
        business_type="서비스업",
        business_item="파견관리",
        email="mirae@example.com",
        is_active=True,
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
            business_type="제조업",
            business_item="전자조립",
            email="green@example.com",
            is_active=True,
        ),
        ClientCompany(
            our_business_id=our1.id,
            name="서울물류",
            ceo_name="이사장",
            business_number="234-56-78901",
            phone="02-3333-4444",
            business_type="물류업",
            business_item="물류하역",
            email="seoul@example.com",
            is_active=True,
        ),
        ClientCompany(
            our_business_id=our2.id,
            name="한빛케어",
            ceo_name="최원장",
            business_number="345-67-89012",
            phone="031-555-6666",
            business_type="서비스업",
            business_item="시설관리",
            email="hanbit@example.com",
            is_active=True,
        ),
    ]
    db.session.add_all(clients)
    db.session.commit()

    settings = [
        ClientCompanySetting(
            client_company_id=clients[0].id,
            attendance_open_time="08:00",
            late_standard_time="09:00",
            workday_standard_hours=8,
            hospital_paid=True,
            document_view_policy="sensitive_super_admin_only",
        ),
        ClientCompanySetting(
            client_company_id=clients[1].id,
            attendance_open_time="07:30",
            late_standard_time="08:30",
            workday_standard_hours=8,
            hospital_paid=False,
            document_view_policy="manager_and_above",
        ),
        ClientCompanySetting(
            client_company_id=clients[2].id,
            attendance_open_time="09:00",
            late_standard_time="09:30",
            workday_standard_hours=8,
            hospital_paid=True,
            document_view_policy="sensitive_super_admin_only",
        ),
    ]
    payroll_settings = [
        ClientCompanyPayrollSetting(
            client_company_id=clients[0].id,
            default_pay_type="monthly",
            base_salary=2800000,
            daily_wage=130000,
            hourly_wage=12000,
        ),
        ClientCompanyPayrollSetting(
            client_company_id=clients[1].id,
            default_pay_type="daily",
            base_salary=0,
            daily_wage=145000,
            hourly_wage=13000,
        ),
        ClientCompanyPayrollSetting(
            client_company_id=clients[2].id,
            default_pay_type="hourly",
            base_salary=0,
            daily_wage=0,
            hourly_wage=15000,
        ),
    ]
    db.session.add_all(settings + payroll_settings)
    db.session.commit()

    work_types = [
        ClientCompanyWorkType(client_company_id=clients[0].id, name="주간조", code="DAY", is_active=True),
        ClientCompanyWorkType(client_company_id=clients[0].id, name="야간조", code="NIGHT", is_active=True),
        ClientCompanyWorkType(client_company_id=clients[1].id, name="상차", code="LOAD", is_active=True),
        ClientCompanyWorkType(client_company_id=clients[1].id, name="하차", code="UNLOAD", is_active=True),
        ClientCompanyWorkType(client_company_id=clients[2].id, name="시설관리", code="CARE", is_active=True),
    ]
    db.session.add_all(work_types)
    db.session.commit()

    employees = [
        Employee(
            our_business_id=our1.id,
            current_client_company_id=clients[0].id,
            work_type_id=work_types[0].id,
            name="김철수",
            nationality="대한민국",
            phone="010-1111-1111",
            hire_date="2024-01-10",
            status="active",
        ),
        Employee(
            our_business_id=our1.id,
            current_client_company_id=clients[0].id,
            work_type_id=work_types[1].id,
            name="박영희",
            nationality="대한민국",
            phone="010-2222-2222",
            hire_date="2024-03-04",
            status="active",
        ),
        Employee(
            our_business_id=our1.id,
            current_client_company_id=clients[1].id,
            work_type_id=work_types[2].id,
            name="장민수",
            nationality="우즈베키스탄",
            phone="010-3333-3333",
            hire_date="2024-02-15",
            status="active",
        ),
        Employee(
            our_business_id=our2.id,
            current_client_company_id=clients[2].id,
            work_type_id=work_types[4].id,
            name="이수진",
            nationality="대한민국",
            phone="010-4444-4444",
            hire_date="2024-01-20",
            status="active",
        ),
    ]
    db.session.add_all(employees)
    db.session.commit()

    documents = [
        EmployeeDocument(employee_id=employees[0].id, document_type="id_card", file_name="kim_id.pdf"),
        EmployeeDocument(employee_id=employees[1].id, document_type="id_card", file_name="park_id.pdf"),
        EmployeeDocument(employee_id=employees[2].id, document_type="passport", file_name="jang_passport.pdf"),
        EmployeeDocument(employee_id=employees[3].id, document_type="other", file_name="lee_license.pdf"),
    ]
    db.session.add_all(documents)

    current_date = today_str()
    attendances = [
        AttendanceRecord(employee_id=employees[0].id, work_date=current_date, status='working'),
        AttendanceRecord(employee_id=employees[1].id, work_date=current_date, status='completed'),
        AttendanceRecord(employee_id=employees[2].id, work_date=current_date, status='before_work'),
        AttendanceRecord(employee_id=employees[3].id, work_date=current_date, status='hospital'),
    ]
    db.session.add_all(attendances)
    db.session.commit()
