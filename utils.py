from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from typing import Any

from flask import render_template_string

from models import (
    AdminMenu,
    AttendanceRecord,
    ClientCompany,
    ClientCompanyPayrollSetting,
    ClientCompanySetting,
    ClientCompanyWorkType,
    Employee,
    EmployeeDocument,
    OurBusiness,
    UiLabel,
    db,
)

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


def ui_text(label_key: str, default: str) -> str:
    item = UiLabel.query.filter_by(label_key=label_key, is_active=True).first()
    return item.label_text if item and item.label_text else default


def _public_menu_items() -> list[AdminMenu]:
    return (
        AdminMenu.query
        .filter(AdminMenu.code != "admin_shortcut")
        .filter(AdminMenu.route_path.notlike("/admin%"))
        .order_by(AdminMenu.sort_order.asc(), AdminMenu.id.asc())
        .all()
    )


def build_public_navigation(active: str) -> list[dict[str, Any]]:
    items = _public_menu_items()
    code_map = {item.code: item for item in items}
    children_map: dict[str, list[AdminMenu]] = {}
    for item in items:
        if item.parent_code:
            children_map.setdefault(item.parent_code, []).append(item)

    navigation: list[dict[str, Any]] = []
    for item in items:
        if item.parent_code:
            continue
        children = [
            {
                "code": child.code,
                "label": child.name,
                "href": child.route_path or "#",
                "active": active == child.code,
                "enabled": child.is_active,
            }
            for child in children_map.get(item.code, [])
            if child.is_active
        ]
        enabled = item.is_active
        active_here = active == item.code or any(child["active"] for child in children)
        href = item.route_path or (children[0]["href"] if children else "#")
        if not enabled and not children:
            continue
        navigation.append(
            {
                "code": item.code,
                "label": item.name,
                "href": href,
                "active": active_here,
                "enabled": enabled,
                "children": children,
            }
        )
    return navigation


def build_admin_navigation(active: str) -> list[dict[str, Any]]:
    return [
        {"code": "admin_home", "label": ui_text("admin_nav_home", "관리자 홈"), "href": "/admin", "active": active == "admin_home"},
        {"code": "admin_menus", "label": ui_text("admin_nav_menus", "메뉴관리"), "href": "/admin/menus", "active": active == "admin_menus"},
        {"code": "admin_labels", "label": ui_text("admin_nav_labels", "문구관리"), "href": "/admin/labels", "active": active == "admin_labels"},
    ]


APP_LAYOUT_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<style>
    :root {
        --bg:#f4f7fb;
        --panel:#ffffff;
        --panel-soft:#f8fbff;
        --line:#dbe4ef;
        --line-strong:#c8d4e3;
        --text:#0f172a;
        --muted:#64748b;
        --primary:#1d4ed8;
        --primary-soft:#eff6ff;
        --primary-deep:#102a43;
        --green:#16a34a;
        --orange:#ea580c;
        --red:#dc2626;
        --sky:#0284c7;
        --yellow:#ca8a04;
        --shadow:0 18px 38px rgba(15, 23, 42, 0.08);
        --shadow-soft:0 10px 24px rgba(15, 23, 42, 0.05);
    }
    * { box-sizing:border-box; }
    html, body { height:100%; }
    body {
        margin:0;
        font-family:Arial,sans-serif;
        background:
            radial-gradient(circle at top left, rgba(59,130,246,.08), transparent 24%),
            linear-gradient(180deg, #eef4fb 0%, #f7f9fc 28%, #f4f7fb 100%);
        color:var(--text);
    }
    .topbar {
        background:linear-gradient(135deg,#10243a 0%,#173a63 52%,#1d4ed8 100%);
        color:white;
        padding:16px 20px 18px;
        box-shadow:0 16px 30px rgba(15, 23, 42, .18);
    }
    .topbar-inner {
        width:min(100%, 1280px);
        margin:0 auto;
        display:flex;
        flex-wrap:wrap;
        gap:14px;
        align-items:flex-end;
        justify-content:space-between;
    }
    .brand-kicker {
        font-size:12px;
        letter-spacing:.14em;
        text-transform:uppercase;
        color:rgba(255,255,255,.72);
        margin-bottom:8px;
        font-weight:700;
    }
    .brand-title {
        font-size:26px;
        line-height:1.15;
        font-weight:800;
        margin:0;
    }
    .brand-desc {
        margin:8px 0 0;
        font-size:14px;
        color:rgba(255,255,255,.82);
    }
    .topbar-meta {
        display:flex;
        flex-wrap:wrap;
        gap:10px;
        justify-content:flex-end;
    }
    .meta-pill {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        padding:10px 12px;
        border-radius:999px;
        border:1px solid rgba(255,255,255,.16);
        background:rgba(255,255,255,.10);
        backdrop-filter:blur(8px);
        font-size:13px;
        font-weight:700;
        color:#f8fbff;
    }
    .meta-link {
        text-decoration:none;
    }
    .menu-shell {
        position:sticky;
        top:0;
        z-index:20;
        backdrop-filter: blur(12px);
        background:rgba(247,249,252,.82);
        border-bottom:1px solid rgba(203,213,225,.85);
    }
    .menu, .quickbar {
        width:min(100%,1280px);
        margin:0 auto;
        display:flex;
        flex-wrap:wrap;
        gap:14px;
        align-items:center;
        padding:14px 20px;
    }
    .menu a, .quickbar a {
        text-decoration:none;
        color:#334155;
        font-weight:800;
        font-size:14px;
        padding:9px 14px;
        border-radius:999px;
    }
    .menu a.active, .quickbar a.active {
        background:#dbeafe;
        color:#1d4ed8;
    }
    .section-chip {
        display:inline-flex;
        align-items:center;
        padding:8px 12px;
        border-radius:999px;
        background:#eff6ff;
        color:#1d4ed8;
        font-size:13px;
        font-weight:800;
    }
    .wrap {
        width:min(100%,1280px);
        margin:0 auto;
        padding:28px 20px 56px;
    }
    .hero-card, .panel, .stat-card {
        border:1px solid var(--line);
        border-radius:20px;
        background:var(--panel);
        box-shadow:var(--shadow-soft);
    }
    .hero-card {
        display:flex;
        justify-content:space-between;
        gap:18px;
        align-items:flex-start;
        padding:24px;
        margin-bottom:20px;
    }
    .hero-actions, .toolbar {
        display:flex;
        flex-wrap:wrap;
        gap:10px;
    }
    .btn {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        min-height:40px;
        padding:0 14px;
        border-radius:12px;
        border:1px solid var(--line);
        background:#fff;
        color:#0f172a;
        text-decoration:none;
        font-weight:800;
        cursor:pointer;
    }
    .btn-primary {
        background:var(--primary);
        border-color:var(--primary);
        color:#fff;
    }
    .btn-danger {
        background:#fff1f2;
        color:#be123c;
        border-color:#fecdd3;
    }
    .stat-grid {
        display:grid;
        grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));
        gap:16px;
        margin-bottom:20px;
    }
    .stat-card { padding:18px; }
    .stat-label { font-size:13px; color:var(--muted); font-weight:700; }
    .stat-value { font-size:30px; font-weight:800; margin:6px 0; }
    .stat-meta { color:var(--muted); font-size:13px; }
    .panel { margin-bottom:20px; overflow:hidden; }
    .panel-head {
        padding:20px 22px 0;
        display:flex;
        justify-content:space-between;
        gap:12px;
        align-items:flex-start;
        flex-wrap:wrap;
    }
    .panel-head h2, .panel-head h3 { margin:0; }
    .panel-head p { margin:6px 0 0; color:var(--muted); }
    .panel-body { padding:18px 22px 22px; }
    .two-col {
        display:grid;
        grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));
        gap:20px;
    }
    .eyebrow {
        display:inline-block;
        font-size:12px;
        font-weight:800;
        letter-spacing:.14em;
        text-transform:uppercase;
        color:#2563eb;
        margin-bottom:10px;
    }
    table {
        width:100%;
        border-collapse:collapse;
        background:#fff;
    }
    th, td {
        padding:12px 10px;
        border-bottom:1px solid #e2e8f0;
        text-align:left;
        vertical-align:top;
        font-size:14px;
    }
    th {
        background:#f8fafc;
        color:#334155;
        font-weight:800;
    }
    input, select, textarea {
        width:100%;
        min-height:40px;
        padding:10px 12px;
        border-radius:12px;
        border:1px solid var(--line-strong);
        background:#fff;
        font-size:14px;
    }
    textarea { min-height:96px; resize:vertical; }
    .notice {
        margin-bottom:16px;
        padding:14px 16px;
        border-radius:14px;
        background:#ecfeff;
        border:1px solid #a5f3fc;
        color:#155e75;
        font-weight:700;
    }
    .muted { color:var(--muted); }
    .indent { padding-left:24px; }
    @media (max-width: 860px) {
        .hero-card { flex-direction:column; }
    }
</style>
</head>
<body>
    <div class="topbar">
        <div class="topbar-inner">
            <div>
                <div class="brand-kicker">{{ app_kicker }}</div>
                <h1 class="brand-title">{{ brand_title }}</h1>
                <p class="brand-desc">{{ brand_desc }}</p>
            </div>
            <div class="topbar-meta">
                <div class="meta-pill">오늘 {{ today }}</div>
                <div class="meta-pill">운영화면</div>
                <a class="meta-pill meta-link" href="/admin">{{ admin_entry_label }}</a>
            </div>
        </div>
    </div>
    <div class="menu-shell">
        <div class="menu">
            {% for item in navigation %}
                <a href="{{ item.href }}" class="{{ 'active' if item.active else '' }}">{{ item.label }}</a>
            {% endfor %}
        </div>
        {% if quick_links %}
        <div class="quickbar">
            {% for item in quick_links %}
                {% if item.get('kind') == 'chip' %}
                    <span class="section-chip">{{ item.label }}</span>
                {% else %}
                    <a href="{{ item.href }}" class="{{ 'active' if item.get('active') else '' }}">{{ item.label }}</a>
                {% endif %}
            {% endfor %}
        </div>
        {% endif %}
    </div>
    <div class="wrap">{{ content|safe }}</div>
</body>
</html>
"""

ADMIN_LAYOUT_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<style>
    :root {
        --bg:#0f172a;
        --panel:#111c34;
        --panel-soft:#182645;
        --line:#223251;
        --text:#e5eefc;
        --muted:#94a3b8;
        --primary:#38bdf8;
        --accent:#8b5cf6;
        --success:#22c55e;
        --danger:#fb7185;
        --shadow:0 22px 48px rgba(2, 6, 23, .35);
    }
    * { box-sizing:border-box; }
    body {
        margin:0;
        font-family:Arial,sans-serif;
        color:var(--text);
        background:
            radial-gradient(circle at top left, rgba(56,189,248,.12), transparent 24%),
            radial-gradient(circle at top right, rgba(139,92,246,.12), transparent 22%),
            linear-gradient(180deg, #09111f 0%, #0f172a 100%);
    }
    .admin-shell {
        min-height:100vh;
        display:grid;
        grid-template-columns:280px 1fr;
    }
    .admin-sidebar {
        padding:24px 18px;
        border-right:1px solid rgba(148,163,184,.16);
        background:rgba(9,17,31,.88);
        position:sticky;
        top:0;
        height:100vh;
    }
    .admin-brand {
        padding:18px;
        border-radius:24px;
        background:linear-gradient(160deg, rgba(56,189,248,.18), rgba(139,92,246,.18));
        border:1px solid rgba(148,163,184,.18);
        box-shadow:var(--shadow);
        margin-bottom:18px;
    }
    .admin-brand small {
        display:block;
        color:#7dd3fc;
        font-size:12px;
        letter-spacing:.16em;
        text-transform:uppercase;
        font-weight:800;
        margin-bottom:8px;
    }
    .admin-brand h1 {
        margin:0 0 8px;
        font-size:28px;
        line-height:1.2;
    }
    .admin-brand p {
        margin:0;
        color:#cbd5e1;
        font-size:14px;
    }
    .admin-nav {
        display:flex;
        flex-direction:column;
        gap:10px;
        margin-top:18px;
    }
    .admin-nav a, .back-link {
        text-decoration:none;
        color:#dbeafe;
        background:rgba(30,41,59,.85);
        border:1px solid rgba(148,163,184,.14);
        padding:13px 14px;
        border-radius:16px;
        font-weight:800;
    }
    .admin-nav a.active {
        background:linear-gradient(135deg, rgba(56,189,248,.18), rgba(99,102,241,.28));
        border-color:rgba(56,189,248,.35);
        color:#f8fafc;
    }
    .back-link {
        display:block;
        margin-top:18px;
        text-align:center;
        color:#cbd5e1;
    }
    .admin-main {
        padding:24px;
    }
    .admin-topbar {
        display:flex;
        justify-content:space-between;
        gap:16px;
        align-items:flex-start;
        margin-bottom:20px;
        padding:18px 22px;
        border-radius:24px;
        background:rgba(17,28,52,.82);
        border:1px solid rgba(148,163,184,.14);
        box-shadow:var(--shadow);
    }
    .admin-topbar h2 { margin:0 0 6px; font-size:30px; }
    .admin-topbar p { margin:0; color:#cbd5e1; }
    .admin-badge {
        display:inline-flex;
        align-items:center;
        height:40px;
        padding:0 14px;
        border-radius:999px;
        background:rgba(56,189,248,.14);
        color:#7dd3fc;
        border:1px solid rgba(56,189,248,.24);
        font-weight:800;
        white-space:nowrap;
    }
    .hero-card, .panel, .stat-card {
        border:1px solid rgba(148,163,184,.12);
        border-radius:22px;
        background:rgba(17,28,52,.88);
        box-shadow:var(--shadow);
    }
    .hero-card {
        display:flex;
        justify-content:space-between;
        gap:18px;
        align-items:flex-start;
        padding:24px;
        margin-bottom:20px;
    }
    .hero-actions, .toolbar, .form-grid {
        display:flex;
        flex-wrap:wrap;
        gap:10px;
    }
    .btn {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        min-height:40px;
        padding:0 14px;
        border-radius:14px;
        border:1px solid rgba(148,163,184,.18);
        background:#16233e;
        color:#f8fafc;
        text-decoration:none;
        font-weight:800;
        cursor:pointer;
    }
    .btn-primary {
        background:linear-gradient(135deg,#0284c7,#6366f1);
        border-color:transparent;
    }
    .btn-subtle {
        background:rgba(30,41,59,.9);
    }
    .stat-grid {
        display:grid;
        grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));
        gap:16px;
        margin-bottom:20px;
    }
    .stat-card { padding:18px; }
    .stat-label { font-size:13px; color:#94a3b8; font-weight:700; }
    .stat-value { font-size:30px; font-weight:800; margin:6px 0; }
    .stat-meta { color:#cbd5e1; font-size:13px; }
    .panel { margin-bottom:20px; overflow:hidden; }
    .panel-head {
        padding:20px 22px 0;
        display:flex;
        justify-content:space-between;
        gap:12px;
        align-items:flex-start;
        flex-wrap:wrap;
    }
    .panel-head h3, .panel-head h2 { margin:0; }
    .panel-head p { margin:6px 0 0; color:#cbd5e1; }
    .panel-body { padding:18px 22px 22px; }
    .two-col {
        display:grid;
        grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));
        gap:20px;
    }
    .eyebrow {
        display:inline-block;
        font-size:12px;
        font-weight:800;
        letter-spacing:.16em;
        text-transform:uppercase;
        color:#7dd3fc;
        margin-bottom:10px;
    }
    table {
        width:100%;
        border-collapse:collapse;
        background:transparent;
    }
    th, td {
        padding:12px 10px;
        border-bottom:1px solid rgba(148,163,184,.12);
        text-align:left;
        vertical-align:top;
        font-size:14px;
    }
    th {
        background:rgba(15,23,42,.6);
        color:#cbd5e1;
        font-weight:800;
    }
    input, select, textarea {
        width:100%;
        min-height:40px;
        padding:10px 12px;
        border-radius:12px;
        border:1px solid rgba(148,163,184,.22);
        background:#0f172a;
        color:#f8fafc;
        font-size:14px;
    }
    textarea { min-height:96px; resize:vertical; }
    .notice {
        margin-bottom:16px;
        padding:14px 16px;
        border-radius:14px;
        background:rgba(34,197,94,.14);
        border:1px solid rgba(34,197,94,.30);
        color:#dcfce7;
        font-weight:700;
    }
    .muted { color:#94a3b8; }
    .indent { padding-left:24px; }
    .stack { display:grid; gap:16px; }
    .chip {
        display:inline-flex;
        align-items:center;
        min-height:28px;
        padding:0 10px;
        border-radius:999px;
        font-size:12px;
        font-weight:800;
        background:rgba(56,189,248,.14);
        color:#7dd3fc;
    }
    @media (max-width: 980px) {
        .admin-shell { grid-template-columns:1fr; }
        .admin-sidebar { position:static; height:auto; border-right:0; border-bottom:1px solid rgba(148,163,184,.16); }
        .admin-topbar, .hero-card { flex-direction:column; }
    }
</style>
</head>
<body>
    <div class="admin-shell">
        <aside class="admin-sidebar">
            <div class="admin-brand">
                <small>{{ admin_kicker }}</small>
                <h1>{{ admin_brand }}</h1>
                <p>{{ admin_desc }}</p>
            </div>
            <nav class="admin-nav">
                {% for item in navigation %}
                    <a href="{{ item.href }}" class="{{ 'active' if item.active else '' }}">{{ item.label }}</a>
                {% endfor %}
            </nav>
            <a class="back-link" href="/">{{ back_to_service }}</a>
        </aside>
        <main class="admin-main">
            <div class="admin-topbar">
                <div>
                    <h2>{{ title }}</h2>
                    <p>{{ page_description }}</p>
                </div>
                <div class="admin-badge">관리자 전용 섹션</div>
            </div>
            {{ content|safe }}
        </main>
    </div>
</body>
</html>
"""


def render_page(
    title: str,
    active: str,
    content: str,
    quick_links: list[dict[str, str]] | None = None,
    layout: str = "app",
    page_description: str = "",
) -> str:
    if layout == "admin":
        return render_template_string(
            ADMIN_LAYOUT_HTML,
            title=title,
            content=content,
            navigation=build_admin_navigation(active),
            page_description=page_description or ui_text("admin_page_description", "관리자 전용 설정 화면입니다."),
            admin_brand=ui_text("admin_brand_name", "멀티사업자 관리자"),
            admin_kicker=ui_text("admin_brand_kicker", "admin center"),
            admin_desc=ui_text("admin_brand_desc", "사용자 화면과 분리된 설정 전용 관리 영역입니다."),
            back_to_service=ui_text("admin_back_to_service", "운영 화면으로 돌아가기"),
        )

    return render_template_string(
        APP_LAYOUT_HTML,
        title=title,
        active=active,
        content=content,
        navigation=build_public_navigation(active),
        quick_links=quick_links or [],
        app_kicker=ui_text("app_brand_kicker", "multi business hr"),
        brand_title=ui_text("app_brand_name", "멀티사업자 인력·근태·급여 관리"),
        brand_desc=ui_text("app_brand_desc", "인력, 근태, 급여를 한 화면 흐름으로 관리하는 운영 서비스입니다."),
        today=today_str(),
        admin_entry_label=ui_text("admin_entry_label", "관리자"),
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
