
from __future__ import annotations

from html import escape
from urllib.parse import urlencode

from flask import Blueprint, redirect, request
from sqlalchemy import func

from models import AdminMenu, AttendanceRecord, ClientCompany, Employee, OurBusiness, UiLabel, db
from utils import ATTENDANCE_STATUS, render_page, today_str, ui_text

admin_bp = Blueprint("admin", __name__)


def _redirect_url(base_path: str, message: str = "", error: str = "") -> str:
    query = {}
    if message:
        query["message"] = message
    if error:
        query["error"] = error
    if not query:
        return base_path
    return f"{base_path}?{urlencode(query)}"


def _alert_box() -> str:
    message = request.args.get("message", "").strip()
    error = request.args.get("error", "").strip()
    if not message and not error:
        return ""
    text = escape(error or message)
    css_class = "notice danger" if error else "notice"
    return f'<div class="{css_class}" style="margin-bottom:18px;">{text}</div>'


def _summary_card(title: str, value: int, description: str) -> str:
    return f"""
    <div class="stat-card">
        <div class="stat-label">{escape(title)}</div>
        <div class="stat-value">{value}</div>
        <div class="stat-meta">{escape(description)}</div>
    </div>
    """


def _is_descendant(menu_code: str, parent_code: str) -> bool:
    if not parent_code:
        return False
    code_map = {item.code: item for item in AdminMenu.query.all()}
    cursor = code_map.get(parent_code)
    visited: set[str] = set()
    while cursor and cursor.code not in visited:
        if cursor.code == menu_code:
            return True
        visited.add(cursor.code)
        cursor = code_map.get(cursor.parent_code or "")
    return False


def _menu_parent_options(current_code: str | None = None) -> str:
    items = AdminMenu.query.order_by(AdminMenu.sort_order.asc(), AdminMenu.id.asc()).all()
    options = ['<option value="">최상위 메뉴</option>']
    for item in items:
        if current_code and item.code == current_code:
            continue
        depth = 1 if item.parent_code else 0
        label = ("— " * depth) + item.name
        options.append(f'<option value="{escape(item.code)}">{escape(label)}</option>')
    return "".join(options)


@admin_bp.route("/admin")
def admin_home() -> str:
    current_date = today_str()
    business_count = OurBusiness.query.count()
    client_count = ClientCompany.query.count()
    employee_count = Employee.query.count()
    menu_count = AdminMenu.query.filter_by(is_active=True).count()
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
            _summary_card(ui_text("admin_card_businesses", "사업자"), business_count, "등록된 사업자 기준"),
            _summary_card(ui_text("admin_card_clients", "거래처"), client_count, "등록된 거래처 기준"),
            _summary_card(ui_text("admin_card_employees", "직원"), employee_count, "재직/등록 인력 포함"),
            _summary_card(ui_text("admin_card_menus", "메뉴"), menu_count, "현재 노출 메뉴 수"),
            _summary_card(ui_text("admin_card_labels", "문구"), label_count, "현재 활성 문구 수"),
        ]
    )

    status_rows = ""
    for key, label in ATTENDANCE_STATUS.items():
        status_rows += f"""
        <tr>
            <th style="width:180px;">{escape(label)}</th>
            <td>{status_counts.get(key, 0)}명</td>
            <td>{current_date} 기준 근태 상태 집계</td>
        </tr>
        """

    content = f"""
    {_alert_box()}
    <div class="hero-card">
        <div>
            <div class="eyebrow">ADMIN CONTROL</div>
            <h1 style="margin:0 0 8px;">{escape(ui_text("admin_home_title", "관리자 홈"))}</h1>
            <p style="margin:0;color:#475569;">{escape(ui_text("admin_home_description", "홈페이지처럼 한눈에 보는 운영 현황과 1단계 관리 기능 진입 화면입니다."))}</p>
        </div>
        <div class="hero-actions">
            <a href="/admin/menus" class="btn btn-primary">{escape(ui_text("admin_menu_title", "메뉴관리"))}</a>
            <a href="/admin/labels" class="btn">{escape(ui_text("admin_label_title", "문구관리"))}</a>
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
        <div class="panel">
            <div class="panel-head">
                <h2>1단계 구성</h2>
                <p>이번 단계에서는 메뉴와 문구를 실제 화면에 반영하도록 연결합니다.</p>
            </div>
            <div class="panel-body">
                <ul class="bullet-list">
                    <li>상단 메뉴 이름, 순서, URL, 숨김/노출, 상하위 메뉴 관리</li>
                    <li>페이지 제목, 버튼 문구, 안내 문구, 카드 제목 관리</li>
                    <li>관리자 홈 / 메뉴관리 / 문구관리 본문 분리</li>
                </ul>
            </div>
        </div>
        <div class="panel">
            <div class="panel-head">
                <h2>다음 단계 확장 포인트</h2>
                <p>지금 구조를 유지하면서 2단계 화면 섹션관리로 확장할 수 있게 남겨둡니다.</p>
            </div>
            <div class="panel-body">
                <ul class="bullet-list">
                    <li>AdminPage를 기준으로 화면 섹션 연결 가능</li>
                    <li>UiLabel 추가 등록으로 코드 문구를 점진적 DB 전환</li>
                    <li>메뉴 트리를 그대로 재사용해 관리자 섹션 확장 가능</li>
                </ul>
            </div>
        </div>
    </div>
    """
    return render_page(ui_text("admin_home_title", "관리자 홈"), "admin_home", content)


@admin_bp.route("/admin/menus", methods=["GET", "POST"])
def admin_menus() -> str:
    if request.method == "POST":
        menu_id_raw = request.form.get("menu_id", "").strip()
        menu = db.session.get(AdminMenu, int(menu_id_raw)) if menu_id_raw.isdigit() else None
        if menu is None:
            return redirect(_redirect_url("/admin/menus", error="수정할 메뉴를 찾을 수 없습니다."))

        parent_code = request.form.get("parent_code", "").strip()
        if parent_code == menu.code:
            return redirect(_redirect_url("/admin/menus", error="메뉴 자신을 상위 메뉴로 지정할 수 없습니다."))
        if _is_descendant(menu.code, parent_code):
            return redirect(_redirect_url("/admin/menus", error="하위 메뉴를 다시 상위 메뉴로 지정할 수 없습니다."))

        name = request.form.get("name", "").strip()
        route_path = request.form.get("route_path", "").strip() or "#"
        sort_order_raw = request.form.get("sort_order", "").strip()
        sort_order = int(sort_order_raw) if sort_order_raw.lstrip("-").isdigit() else menu.sort_order

        if not name:
            return redirect(_redirect_url("/admin/menus", error="메뉴 이름은 비워둘 수 없습니다."))

        menu.name = name
        menu.parent_code = parent_code
        menu.route_path = route_path
        menu.sort_order = sort_order
        menu.is_active = request.form.get("is_active") == "Y"
        db.session.commit()
        return redirect(_redirect_url("/admin/menus", message="메뉴가 저장되었습니다."))

    items = AdminMenu.query.order_by(AdminMenu.sort_order.asc(), AdminMenu.id.asc()).all()
    parent_name_map = {item.code: item.name for item in items}
    rows = ""
    for item in items:
        parent_options = _menu_parent_options(item.code)
        parent_selected = f'value="{escape(item.parent_code)}"' if item.parent_code else 'value=""'
        parent_options = parent_options.replace(f'<option {parent_selected}>', '<option>')
        if item.parent_code:
            parent_options = parent_options.replace(
                f'<option value="{escape(item.parent_code)}">',
                f'<option value="{escape(item.parent_code)}" selected>',
            )
        else:
            parent_options = parent_options.replace('<option value="">최상위 메뉴</option>', '<option value="" selected>최상위 메뉴</option>', 1)

        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td style="min-width:220px;">
                <form method="post">
                    <input type="hidden" name="menu_id" value="{item.id}">
                    <input type="text" name="name" value="{escape(item.name)}">
            </td>
            <td style="min-width:160px;"><code>{escape(item.code)}</code></td>
            <td style="min-width:200px;">
                    <select name="parent_code">{parent_options}</select>
            </td>
            <td style="min-width:220px;"><input type="text" name="route_path" value="{escape(item.route_path)}"></td>
            <td style="width:120px;"><input type="number" name="sort_order" value="{item.sort_order}"></td>
            <td style="width:120px;">
                    <label style="display:flex;gap:6px;align-items:center;">
                        <input type="checkbox" name="is_active" value="Y" {"checked" if item.is_active else ""}>
                        {"노출" if item.is_active else "숨김"}
                    </label>
            </td>
            <td style="min-width:120px;">{escape(parent_name_map.get(item.parent_code, "-"))}</td>
            <td style="width:110px;">
                    <button class="btn btn-primary" type="submit">{escape(ui_text("button_save", "저장"))}</button>
                </form>
            </td>
        </tr>
        """

    content = f"""
    {_alert_box()}
    <div class="hero-card">
        <div>
            <div class="eyebrow">MENU MANAGEMENT</div>
            <h1 style="margin:0 0 8px;">{escape(ui_text("admin_menu_title", "메뉴관리"))}</h1>
            <p style="margin:0;color:#475569;">{escape(ui_text("admin_menu_description", "상단 메뉴명, 순서, 노출 여부, 상하위 메뉴, URL을 수정합니다."))}</p>
        </div>
        <div class="hero-actions">
            <a href="/admin" class="btn">관리자 홈</a>
            <a href="/" class="btn btn-primary">실제 화면 보기</a>
        </div>
    </div>

    <div class="panel">
        <div class="panel-head">
            <h2>메뉴 구조 편집</h2>
            <p>최상위 메뉴와 하위 메뉴를 한 테이블에서 관리해 중복 구조를 막습니다.</p>
        </div>
        <div class="panel-body">
            <div class="table-scroll js-drag-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>메뉴명</th>
                            <th>코드</th>
                            <th>상위 메뉴</th>
                            <th>URL</th>
                            <th>순서</th>
                            <th>노출</th>
                            <th>현재 부모</th>
                            <th>저장</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="panel">
        <div class="panel-head">
            <h2>반영 방식</h2>
            <p>저장 후 상단 메뉴와 관리자 섹션 퀵메뉴에 즉시 반영됩니다.</p>
        </div>
        <div class="panel-body">
            <ul class="bullet-list">
                <li>최상위 메뉴는 상단 네비게이션에 노출됩니다.</li>
                <li>상위 메뉴가 지정된 항목은 해당 섹션의 하위 메뉴로 노출됩니다.</li>
                <li>숨김 처리한 메뉴는 실제 네비게이션에서 제외됩니다.</li>
                <li>URL과 순서 변경도 같은 테이블에서 함께 관리됩니다.</li>
            </ul>
        </div>
    </div>
    """
    return render_page(ui_text("admin_menu_title", "메뉴관리"), "admin_menus", content)


@admin_bp.route("/admin/labels", methods=["GET", "POST"])
def admin_labels() -> str:
    if request.method == "POST":
        action = request.form.get("action", "update").strip()
        if action == "create":
            label_key = request.form.get("label_key", "").strip()
            label_text = request.form.get("label_text", "").strip()
            category = request.form.get("category", "").strip() or "custom"
            description = request.form.get("description", "").strip()

            if not label_key or not label_text:
                return redirect(_redirect_url("/admin/labels", error="문구 키와 문구 내용은 모두 입력해야 합니다."))
            if UiLabel.query.filter_by(label_key=label_key).first():
                return redirect(_redirect_url("/admin/labels", error="이미 존재하는 문구 키입니다."))

            db.session.add(
                UiLabel(
                    label_key=label_key,
                    label_text=label_text,
                    category=category,
                    description=description,
                    is_active=True,
                )
            )
            db.session.commit()
            return redirect(_redirect_url("/admin/labels", message="새 문구가 추가되었습니다."))

        label_id_raw = request.form.get("label_id", "").strip()
        label = db.session.get(UiLabel, int(label_id_raw)) if label_id_raw.isdigit() else None
        if label is None:
            return redirect(_redirect_url("/admin/labels", error="수정할 문구를 찾을 수 없습니다."))

        label_text = request.form.get("label_text", "").strip()
        if not label_text:
            return redirect(_redirect_url("/admin/labels", error="문구 내용은 비워둘 수 없습니다."))

        label.label_text = label_text
        label.is_active = request.form.get("is_active") == "Y"
        db.session.commit()
        return redirect(_redirect_url("/admin/labels", message="문구가 저장되었습니다."))

    items = UiLabel.query.order_by(UiLabel.category.asc(), UiLabel.label_key.asc()).all()
    grouped: dict[str, list[UiLabel]] = {}
    for item in items:
        grouped.setdefault(item.category, []).append(item)

    sections = ""
    for category, labels in grouped.items():
        cards = ""
        for item in labels:
            cards += f"""
            <form method="post" class="panel" style="margin-bottom:14px;">
                <input type="hidden" name="action" value="update">
                <input type="hidden" name="label_id" value="{item.id}">
                <div class="panel-head">
                    <div>
                        <h2 style="margin:0 0 6px;">{escape(item.label_key)}</h2>
                        <p>{escape(item.description or "-")}</p>
                    </div>
                </div>
                <div class="panel-body">
                    <div class="form-grid">
                        <div>
                            <label>문구 내용</label>
                            <input type="text" name="label_text" value="{escape(item.label_text)}">
                        </div>
                        <div>
                            <label>카테고리</label>
                            <input type="text" value="{escape(item.category)}" disabled>
                        </div>
                    </div>
                    <div class="actions" style="justify-content:space-between;">
                        <label style="display:flex;gap:6px;align-items:center;">
                            <input type="checkbox" name="is_active" value="Y" {"checked" if item.is_active else ""}>
                            활성
                        </label>
                        <button class="btn btn-primary" type="submit">{escape(ui_text("button_save", "저장"))}</button>
                    </div>
                </div>
            </form>
            """
        sections += f"""
        <div class="panel" style="margin-bottom:18px;">
            <div class="panel-head">
                <h2>{escape(category)}</h2>
                <p>{len(labels)}개 문구</p>
            </div>
            <div class="panel-body">{cards}</div>
        </div>
        """

    create_form = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>새 문구 추가</h2>
            <p>기존 코드 문구를 DB 기반으로 바꿀 때 키를 추가해 점진적으로 확장합니다.</p>
        </div>
        <div class="panel-body">
            <form method="post">
                <input type="hidden" name="action" value="create">
                <div class="form-grid">
                    <div>
                        <label>문구 키</label>
                        <input type="text" name="label_key" placeholder="example_button_text">
                    </div>
                    <div>
                        <label>카테고리</label>
                        <input type="text" name="category" placeholder="button">
                    </div>
                    <div style="grid-column:1 / -1;">
                        <label>문구 내용</label>
                        <input type="text" name="label_text" placeholder="버튼 문구">
                    </div>
                    <div style="grid-column:1 / -1;">
                        <label>설명</label>
                        <input type="text" name="description" placeholder="어디에 쓰는 문구인지 설명">
                    </div>
                </div>
                <div class="actions">
                    <button class="btn btn-primary" type="submit">{escape(ui_text("button_add", "추가"))}</button>
                </div>
            </form>
        </div>
    </div>
    """

    content = f"""
    {_alert_box()}
    <div class="hero-card">
        <div>
            <div class="eyebrow">LABEL MANAGEMENT</div>
            <h1 style="margin:0 0 8px;">{escape(ui_text("admin_label_title", "문구관리"))}</h1>
            <p style="margin:0;color:#475569;">{escape(ui_text("admin_label_description", "페이지 제목, 버튼 문구, 안내 문구, 카드 제목을 수정합니다."))}</p>
        </div>
        <div class="hero-actions">
            <a href="/admin" class="btn">관리자 홈</a>
            <a href="/" class="btn btn-primary">실제 화면 보기</a>
        </div>
    </div>

    {create_form}
    {sections}
    """
    return render_page(ui_text("admin_label_title", "문구관리"), "admin_labels", content)
