
from __future__ import annotations

from flask import Blueprint
from sqlalchemy import func

from models import AdminMenu, AdminPage, AttendanceRecord, ClientCompany, Employee, OurBusiness, UiLabel
from utils import ATTENDANCE_STATUS, render_page, today_str

admin_bp = Blueprint("admin", __name__)


def _admin_links(active_key: str) -> list[dict[str, str | bool]]:
    items = [
        {"label": "관리자홈", "href": "/admin", "active": active_key == "dashboard"},
        {"label": "메뉴관리", "href": "/admin/menus", "active": active_key == "menus"},
        {"label": "화면관리", "href": "/admin/pages", "active": active_key == "pages"},
        {"label": "문구관리", "href": "/admin/labels", "active": active_key == "labels"},
        {"label": "관리로그", "href": "/admin/logs", "active": active_key == "logs"},
    ]
    return items


def _summary_card(title: str, value: int, description: str) -> str:
    return f"""
    <div class="stat-card">
        <div class="stat-label">{title}</div>
        <div class="stat-value">{value}</div>
        <div class="stat-meta">{description}</div>
    </div>
    """


def _guide_box(title: str, items: list[str]) -> str:
    rows = "".join(f"<li>{item}</li>" for item in items)
    return f"""
    <div class="panel">
        <div class="panel-head">
            <h2>{title}</h2>
            <p>관리자 페이지에서 바로 이어질 예정인 작업입니다.</p>
        </div>
        <div class="panel-body">
            <ul class="bullet-list">{rows}</ul>
        </div>
    </div>
    """


@admin_bp.route("/admin")
def admin_home() -> str:
    current_date = today_str()
    business_count = OurBusiness.query.count()
    client_count = ClientCompany.query.count()
    employee_count = Employee.query.count()
    menu_count = AdminMenu.query.filter_by(is_active=True).count()
    page_count = AdminPage.query.filter_by(is_active=True).count()
    label_count = UiLabel.query.filter_by(is_active=True).count()

    status_counts = dict(
        AttendanceRecord.query.with_entities(
            AttendanceRecord.status,
            func.count(AttendanceRecord.id),
        )
        .filter(AttendanceRecord.work_date == current_date)
        .group_by(AttendanceRecord.status)
        .all()
    )

    cards = "".join(
        [
            _summary_card("사업자", business_count, "등록된 사업자 기준"),
            _summary_card("거래처", client_count, "등록된 거래처 기준"),
            _summary_card("직원", employee_count, "재직/등록 인력 포함"),
            _summary_card("메뉴", menu_count, "관리자 관리 대상 메뉴"),
            _summary_card("화면", page_count, "연결 가능한 화면"),
            _summary_card("문구", label_count, "관리 가능한 UI 문구"),
        ]
    )

    status_rows = ""
    for key, label in ATTENDANCE_STATUS.items():
        status_rows += f"""
        <tr>
            <th style="width:180px;">{label}</th>
            <td>{status_counts.get(key, 0)}명</td>
            <td>{current_date} 기준 근태 상태 집계</td>
        </tr>
        """

    content = f"""
    <div class="hero-card">
        <div>
            <div class="eyebrow">ADMIN CONTROL</div>
            <h1 style="margin:0 0 8px;">관리자 홈</h1>
            <p style="margin:0;color:#475569;">홈페이지처럼 한눈에 보는 운영 현황과, 나중에 메뉴관리·화면관리·문구관리로 이어질 수 있는 관리자 전용 시작 화면입니다.</p>
        </div>
        <div class="hero-actions">
            <a href="/admin/menus" class="btn btn-primary">메뉴관리</a>
            <a href="/admin/pages" class="btn">화면관리</a>
            <a href="/admin/labels" class="btn">문구관리</a>
        </div>
    </div>

    <div class="stat-grid">{cards}</div>

    <div class="panel">
        <div class="panel-head">
            <h2>오늘 운영 요약</h2>
            <p>근태 기준 핵심 상태만 먼저 확인합니다.</p>
        </div>
        <div class="panel-body">
            <table>{status_rows}</table>
        </div>
    </div>

    <div class="two-col">
        {_guide_box("관리자에서 할 수 있게 잡아둔 것", [
            "상단 메뉴명과 하위 메뉴명 관리",
            "메뉴 클릭 시 연결할 화면 경로 관리",
            "화면 제목과 안내 문구 관리",
            "나중에 새 관리자 기능 화면 확장",
        ])}
        {_guide_box("다음 확장 방향", [
            "관리자 계정과 권한 분리",
            "화면별 접근 권한 제어",
            "수정 이력 로그 저장",
            "문구 수정 즉시 반영 구조 연결",
        ])}
    </div>
    """
    return render_page("관리자", "admin", content, _admin_links("dashboard"))


@admin_bp.route("/admin/menus")
def admin_menus() -> str:
    items = AdminMenu.query.order_by(AdminMenu.sort_order.asc(), AdminMenu.id.asc()).all()
    rows = ""
    for item in items:
        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td>{item.name}</td>
            <td>{item.code}</td>
            <td>{item.parent_code or "-"}</td>
            <td>{item.route_path or "-"}</td>
            <td>{"사용" if item.is_active else "미사용"}</td>
        </tr>
        """
    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>메뉴관리</h2>
            <p>나중에 관리자에서 메뉴명, 순서, 연결 링크를 바꿀 수 있게 하기 위한 기본 화면입니다.</p>
        </div>
        <div class="panel-body">
            <div class="toolbar">
                <a href="/admin" class="btn">관리자 홈</a>
                <a href="/admin/pages" class="btn">화면관리 보기</a>
            </div>
            <table>
                <tr>
                    <th style="width:80px;">번호</th>
                    <th>메뉴명</th>
                    <th>코드</th>
                    <th>상위코드</th>
                    <th>연결경로</th>
                    <th style="width:120px;">상태</th>
                </tr>
                {rows or '<tr><td colspan="6">등록된 관리자 메뉴가 없습니다.</td></tr>'}
            </table>
        </div>
    </div>
    """
    return render_page("메뉴관리", "admin", content, _admin_links("menus"))


@admin_bp.route("/admin/pages")
def admin_pages() -> str:
    items = AdminPage.query.order_by(AdminPage.page_name.asc()).all()
    rows = ""
    for item in items:
        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td>{item.page_name}</td>
            <td>{item.page_key}</td>
            <td>{item.route_path}</td>
            <td>{item.category}</td>
            <td>{"사용" if item.is_active else "미사용"}</td>
        </tr>
        """
    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>화면관리</h2>
            <p>회사관리에서 거래처관리 클릭 시 어떤 화면으로 연결할지 같은 기준을 관리하기 위한 영역입니다.</p>
        </div>
        <div class="panel-body">
            <div class="toolbar">
                <a href="/admin/menus" class="btn">메뉴관리 보기</a>
                <a href="/admin/labels" class="btn">문구관리 보기</a>
            </div>
            <table>
                <tr>
                    <th style="width:80px;">번호</th>
                    <th>화면명</th>
                    <th>페이지키</th>
                    <th>경로</th>
                    <th>분류</th>
                    <th style="width:120px;">상태</th>
                </tr>
                {rows or '<tr><td colspan="6">등록된 화면 정보가 없습니다.</td></tr>'}
            </table>
        </div>
    </div>
    """
    return render_page("화면관리", "admin", content, _admin_links("pages"))


@admin_bp.route("/admin/labels")
def admin_labels() -> str:
    items = UiLabel.query.order_by(UiLabel.category.asc(), UiLabel.label_key.asc()).all()
    rows = ""
    for item in items:
        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td>{item.category}</td>
            <td>{item.label_key}</td>
            <td>{item.label_text}</td>
            <td>{item.description or "-"}</td>
        </tr>
        """
    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>문구관리</h2>
            <p>메뉴명, 페이지 제목, 버튼 문구를 나중에 관리자에서 바로 바꾸기 위한 준비 화면입니다.</p>
        </div>
        <div class="panel-body">
            <table>
                <tr>
                    <th style="width:80px;">번호</th>
                    <th style="width:120px;">분류</th>
                    <th>키</th>
                    <th>문구</th>
                    <th>설명</th>
                </tr>
                {rows or '<tr><td colspan="5">등록된 문구가 없습니다.</td></tr>'}
            </table>
        </div>
    </div>
    """
    return render_page("문구관리", "admin", content, _admin_links("labels"))


@admin_bp.route("/admin/logs")
def admin_logs() -> str:
    content = """
    <div class="panel">
        <div class="panel-head">
            <h2>관리로그</h2>
            <p>나중에 메뉴 변경, 문구 변경, 화면 연결 변경 이력을 이곳에 쌓을 수 있게 확장할 자리입니다.</p>
        </div>
        <div class="panel-body">
            <table>
                <tr>
                    <th style="width:160px;">기능</th>
                    <th>설명</th>
                </tr>
                <tr><td>메뉴변경로그</td><td>메뉴명, 순서, 노출 여부 변경 이력</td></tr>
                <tr><td>화면연결로그</td><td>메뉴 클릭 시 연결 화면 경로 변경 이력</td></tr>
                <tr><td>문구변경로그</td><td>페이지 제목, 버튼명, 안내 문구 수정 이력</td></tr>
                <tr><td>권한로그</td><td>관리자 권한 추가/수정/삭제 이력</td></tr>
            </table>
        </div>
    </div>
    """
    return render_page("관리로그", "admin", content, _admin_links("logs"))
