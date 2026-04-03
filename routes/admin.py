
from __future__ import annotations

import re

from flask import Blueprint, redirect, request, url_for
from sqlalchemy import func

from models import AdminMenu, AttendanceRecord, ClientCompany, Employee, OurBusiness, UiLabel, db
from utils import ATTENDANCE_STATUS, render_page, today_str, ui_text

admin_bp = Blueprint("admin", __name__)


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
            <div>
                <h3>{title}</h3>
                <p>1단계 범위 안에서 바로 관리할 수 있는 항목들입니다.</p>
            </div>
        </div>
        <div class="panel-body">
            <ul>{rows}</ul>
        </div>
    </div>
    """


def _normalize_code(raw: str) -> str:
    value = re.sub(r"[^a-z0-9_]+", "_", raw.strip().lower())
    return value.strip("_")


def _ordered_menus() -> list[AdminMenu]:
    items = AdminMenu.query.order_by(AdminMenu.sort_order.asc(), AdminMenu.id.asc()).all()
    code_map = {item.code: item for item in items}
    roots = [item for item in items if not item.parent_code or item.parent_code not in code_map]
    ordered: list[AdminMenu] = []
    for root in roots:
        ordered.append(root)
        children = [item for item in items if item.parent_code == root.code]
        ordered.extend(children)
    return ordered


def _valid_parent_code(item: AdminMenu, parent_code: str) -> str:
    if not parent_code or parent_code == item.code:
        return ""
    parent = AdminMenu.query.filter_by(code=parent_code).first()
    if parent is None:
        return ""
    if parent.parent_code:
        return ""
    return parent.code


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
            _summary_card(ui_text("admin_card_business", "사업자"), business_count, "등록된 우리 사업자 수"),
            _summary_card(ui_text("admin_card_client", "거래처"), client_count, "등록된 거래처 수"),
            _summary_card(ui_text("admin_card_employee", "직원"), employee_count, "등록된 인력 수"),
            _summary_card(ui_text("admin_card_menu", "메뉴"), menu_count, "노출 중인 사용자 메뉴 수"),
            _summary_card(ui_text("admin_card_label", "문구"), label_count, "활성화된 UI 문구 수"),
        ]
    )

    status_rows = ""
    for key, label in ATTENDANCE_STATUS.items():
        status_rows += f"""
        <tr>
            <th style="width:180px;">{label}</th>
            <td>{status_counts.get(key, 0)}명</td>
            <td>{current_date} 기준 근태 상태</td>
        </tr>
        """

    content = f"""
    <div class="hero-card">
        <div>
            <div class="eyebrow">MULTI BUSINESS ADMIN</div>
            <h2 style="margin:0 0 10px;">{ui_text("admin_home_title", "관리자 홈")}</h2>
            <p style="margin:0;color:#cbd5e1;">{ui_text("admin_home_desc", "운영 현황과 설정 작업을 시작하는 관리자 전용 첫 화면입니다.")}</p>
        </div>
        <div class="hero-actions">
            <a href="/admin/menus" class="btn btn-primary">{ui_text("admin_nav_menus", "메뉴관리")}</a>
            <a href="/admin/labels" class="btn btn-subtle">{ui_text("admin_nav_labels", "문구관리")}</a>
        </div>
    </div>

    <div class="stat-grid">{cards}</div>

    <div class="panel">
        <div class="panel-head">
            <div>
                <h3>오늘 운영 요약</h3>
                <p>사용자 화면과 분리된 관리자 섹션에서 바로 현재 상태를 확인합니다.</p>
            </div>
        </div>
        <div class="panel-body">
            <table>{status_rows}</table>
        </div>
    </div>

    <div class="two-col">
        {_guide_box("메뉴관리에서 하는 일", [
            "상단 메뉴 이름 수정",
            "메뉴 순서 변경",
            "메뉴 숨김 및 노출 전환",
            "상위/하위 메뉴 설정",
            "메뉴 URL 변경",
        ])}
        {_guide_box("문구관리에서 하는 일", [
            "페이지 제목 수정",
            "버튼 문구 수정",
            "안내 문구 수정",
            "대시보드 카드 제목 수정",
            "DB 기반 문구 키 추가",
        ])}
    </div>
    """
    return render_page(
        ui_text("admin_home_title", "관리자 홈"),
        "admin_home",
        content,
        layout="admin",
        page_description=ui_text("admin_home_desc", "운영 현황과 설정 작업을 시작하는 관리자 전용 첫 화면입니다."),
    )


@admin_bp.route("/admin/menus", methods=["GET", "POST"])
def admin_menus() -> str:
    if request.method == "POST":
        items = AdminMenu.query.order_by(AdminMenu.id.asc()).all()
        for item in items:
            item.name = request.form.get(f"name_{item.id}", item.name).strip() or item.name
            item.route_path = request.form.get(f"route_path_{item.id}", item.route_path).strip()
            sort_raw = request.form.get(f"sort_order_{item.id}", str(item.sort_order)).strip()
            item.sort_order = int(sort_raw) if sort_raw.isdigit() else item.sort_order
            item.is_active = request.form.get(f"is_active_{item.id}") == "on"
            parent_code = request.form.get(f"parent_code_{item.id}", "").strip()
            item.parent_code = _valid_parent_code(item, parent_code)

        new_name = request.form.get("new_name", "").strip()
        new_code = _normalize_code(request.form.get("new_code", ""))
        if new_name and new_code and AdminMenu.query.filter_by(code=new_code).first() is None:
            new_sort_raw = request.form.get("new_sort_order", "99").strip()
            new_item = AdminMenu(
                code=new_code,
                name=new_name,
                route_path=request.form.get("new_route_path", "").strip(),
                sort_order=int(new_sort_raw) if new_sort_raw.isdigit() else 99,
                is_active=request.form.get("new_is_active") == "on",
            )
            new_item.parent_code = _valid_parent_code(new_item, request.form.get("new_parent_code", "").strip())
            db.session.add(new_item)

        db.session.commit()
        return redirect(url_for("admin.admin_menus", saved="1"))

    items = _ordered_menus()
    parent_options = AdminMenu.query.order_by(AdminMenu.sort_order.asc(), AdminMenu.id.asc()).all()
    rows = ""
    for item in items:
        depth_class = "indent" if item.parent_code else ""
        parent_select_options = ['<option value="">상위 없음</option>']
        for parent in parent_options:
            if parent.code == item.code or parent.parent_code:
                continue
            selected = "selected" if item.parent_code == parent.code else ""
            parent_select_options.append(f'<option value="{parent.code}" {selected}>{parent.name}</option>')
        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td class="{depth_class}">
                <div class="muted">{item.code}</div>
                <input type="text" name="name_{item.id}" value="{item.name}">
            </td>
            <td><input type="number" name="sort_order_{item.id}" value="{item.sort_order}"></td>
            <td>
                <select name="parent_code_{item.id}">
                    {''.join(parent_select_options)}
                </select>
            </td>
            <td><input type="text" name="route_path_{item.id}" value="{item.route_path}"></td>
            <td style="width:110px;">
                <label><input type="checkbox" name="is_active_{item.id}" {"checked" if item.is_active else ""}> 노출</label>
            </td>
        </tr>
        """

    new_parent_options = ['<option value="">상위 없음</option>']
    for parent in parent_options:
        if parent.parent_code:
            continue
        new_parent_options.append(f'<option value="{parent.code}">{parent.name}</option>')

    notice = '<div class="notice">메뉴 설정이 저장되었습니다. 사용자 화면 상단 메뉴에 바로 반영됩니다.</div>' if request.args.get("saved") else ""
    content = f"""
    {notice}
    <div class="hero-card">
        <div>
            <div class="eyebrow">MENU MANAGEMENT</div>
            <h2 style="margin:0 0 10px;">{ui_text("admin_menu_title", "메뉴관리")}</h2>
            <p style="margin:0;color:#cbd5e1;">{ui_text("admin_menu_desc", "사용자 상단 메뉴 이름, 순서, 노출, URL, 상하위 구조를 관리합니다.")}</p>
        </div>
        <div class="hero-actions">
            <button type="submit" form="menu-form" class="btn btn-primary">저장</button>
        </div>
    </div>

    <form id="menu-form" method="post" class="stack">
        <div class="panel">
            <div class="panel-head">
                <div>
                    <h3>현재 메뉴 구조</h3>
                    <p>한 테이블에서 상위/하위 메뉴를 함께 관리합니다. 하위 메뉴 밑에 다시 하위를 두는 구조는 1단계에서 막아 중복 구조를 방지합니다.</p>
                </div>
                <span class="chip">실제 상단 메뉴 반영</span>
            </div>
            <div class="panel-body">
                <table>
                    <tr>
                        <th style="width:70px;">번호</th>
                        <th>메뉴명</th>
                        <th style="width:110px;">순서</th>
                        <th style="width:180px;">상위 메뉴</th>
                        <th>URL</th>
                        <th style="width:110px;">노출</th>
                    </tr>
                    {rows}
                </table>
            </div>
        </div>

        <div class="panel">
            <div class="panel-head">
                <div>
                    <h3>새 메뉴 추가</h3>
                    <p>필요한 경우에만 새 메뉴를 추가합니다. 코드에는 영문/숫자/밑줄만 권장합니다.</p>
                </div>
            </div>
            <div class="panel-body">
                <div class="two-col">
                    <div>
                        <label>메뉴 코드</label>
                        <input type="text" name="new_code" placeholder="example_menu">
                    </div>
                    <div>
                        <label>메뉴명</label>
                        <input type="text" name="new_name" placeholder="예: 통계관리">
                    </div>
                    <div>
                        <label>URL</label>
                        <input type="text" name="new_route_path" placeholder="/stats">
                    </div>
                    <div>
                        <label>순서</label>
                        <input type="number" name="new_sort_order" value="99">
                    </div>
                    <div>
                        <label>상위 메뉴</label>
                        <select name="new_parent_code">{''.join(new_parent_options)}</select>
                    </div>
                    <div>
                        <label>노출</label>
                        <div style="padding-top:10px;"><label><input type="checkbox" name="new_is_active" checked> 바로 노출</label></div>
                    </div>
                </div>
            </div>
        </div>
    </form>
    """
    return render_page(
        ui_text("admin_menu_title", "메뉴관리"),
        "admin_menus",
        content,
        layout="admin",
        page_description=ui_text("admin_menu_desc", "사용자 상단 메뉴 이름, 순서, 노출, URL, 상하위 구조를 관리합니다."),
    )


@admin_bp.route("/admin/labels", methods=["GET", "POST"])
def admin_labels() -> str:
    if request.method == "POST":
        items = UiLabel.query.order_by(UiLabel.id.asc()).all()
        for item in items:
            item.label_text = request.form.get(f"label_text_{item.id}", item.label_text).strip() or item.label_text
            item.category = request.form.get(f"category_{item.id}", item.category).strip() or item.category
            item.description = request.form.get(f"description_{item.id}", item.description).strip()
            item.is_active = request.form.get(f"is_active_{item.id}") == "on"

        new_key = _normalize_code(request.form.get("new_label_key", ""))
        new_text = request.form.get("new_label_text", "").strip()
        if new_key and new_text and UiLabel.query.filter_by(label_key=new_key).first() is None:
            db.session.add(
                UiLabel(
                    label_key=new_key,
                    label_text=new_text,
                    category=request.form.get("new_category", "general").strip() or "general",
                    description=request.form.get("new_description", "").strip(),
                    is_active=request.form.get("new_is_active") == "on",
                )
            )

        db.session.commit()
        return redirect(url_for("admin.admin_labels", saved="1"))

    items = UiLabel.query.order_by(UiLabel.category.asc(), UiLabel.label_key.asc()).all()
    rows = ""
    for item in items:
        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td><input type="text" name="category_{item.id}" value="{item.category}"></td>
            <td>
                <div class="muted">{item.label_key}</div>
                <input type="text" name="label_text_{item.id}" value="{item.label_text}">
            </td>
            <td><input type="text" name="description_{item.id}" value="{item.description}"></td>
            <td style="width:110px;">
                <label><input type="checkbox" name="is_active_{item.id}" {"checked" if item.is_active else ""}> 사용</label>
            </td>
        </tr>
        """

    notice = '<div class="notice">문구 설정이 저장되었습니다. 연결된 화면에 바로 반영됩니다.</div>' if request.args.get("saved") else ""
    content = f"""
    {notice}
    <div class="hero-card">
        <div>
            <div class="eyebrow">LABEL MANAGEMENT</div>
            <h2 style="margin:0 0 10px;">{ui_text("admin_label_title", "문구관리")}</h2>
            <p style="margin:0;color:#cbd5e1;">{ui_text("admin_label_desc", "페이지 제목, 버튼명, 안내문구, 카드 제목을 단계적으로 DB 기반으로 관리합니다.")}</p>
        </div>
        <div class="hero-actions">
            <button type="submit" form="label-form" class="btn btn-primary">저장</button>
        </div>
    </div>

    <form id="label-form" method="post" class="stack">
        <div class="panel">
            <div class="panel-head">
                <div>
                    <h3>현재 문구 목록</h3>
                    <p>이미 연결된 홈 화면과 관리자 화면 문구는 저장 즉시 반영됩니다. 나머지 화면도 같은 방식으로 점진적으로 DB 기반 전환할 수 있습니다.</p>
                </div>
                <span class="chip">점진적 DB 전환</span>
            </div>
            <div class="panel-body">
                <table>
                    <tr>
                        <th style="width:70px;">번호</th>
                        <th style="width:130px;">분류</th>
                        <th>문구 키 / 문구</th>
                        <th>설명</th>
                        <th style="width:110px;">사용</th>
                    </tr>
                    {rows}
                </table>
            </div>
        </div>

        <div class="panel">
            <div class="panel-head">
                <div>
                    <h3>새 문구 추가</h3>
                    <p>새 키를 추가해두면 이후 화면에서 바로 연결할 수 있습니다.</p>
                </div>
            </div>
            <div class="panel-body">
                <div class="two-col">
                    <div>
                        <label>문구 키</label>
                        <input type="text" name="new_label_key" placeholder="example_button_text">
                    </div>
                    <div>
                        <label>문구</label>
                        <input type="text" name="new_label_text" placeholder="예: 저장하기">
                    </div>
                    <div>
                        <label>분류</label>
                        <input type="text" name="new_category" value="general">
                    </div>
                    <div>
                        <label>설명</label>
                        <input type="text" name="new_description" placeholder="어디에 쓰는 문구인지 설명">
                    </div>
                    <div>
                        <label>사용</label>
                        <div style="padding-top:10px;"><label><input type="checkbox" name="new_is_active" checked> 바로 사용</label></div>
                    </div>
                </div>
            </div>
        </div>
    </form>
    """
    return render_page(
        ui_text("admin_label_title", "문구관리"),
        "admin_labels",
        content,
        layout="admin",
        page_description=ui_text("admin_label_desc", "페이지 제목, 버튼명, 안내문구, 카드 제목을 단계적으로 DB 기반으로 관리합니다."),
    )
