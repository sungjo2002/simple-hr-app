from flask import Blueprint, flash, redirect, request, url_for

from models import ClientCompany, OurBusiness, db
from utils import export_table, paginate_items, render_page, render_pagination, render_table_toolbar, sort_items, today_str

businesses_bp = Blueprint("businesses", __name__)


def _business_action_forms(item: OurBusiness, compact: bool = False) -> str:
    gap = "6px" if compact else "8px"
    return f"""
    <div class="actions" style="gap:{gap}; flex-wrap:wrap;">
        <a class="btn btn-white" href="/our-businesses/{item.id}/edit">수정</a>
        <form method="post" action="/our-businesses/{item.id}/toggle-active" onsubmit="return confirm('사업자 사용여부를 전환할까요?');" style="display:inline;">
            <button class="btn btn-white" type="submit">{'비활성' if item.is_active else '활성'}</button>
        </form>
        <form method="post" action="/our-businesses/{item.id}/delete" onsubmit="return confirm('사업자를 삭제할까요? 연결된 거래처가 있으면 삭제할 수 없습니다.');" style="display:inline;">
            <button class="btn btn-danger" type="submit">삭제</button>
        </form>
    </div>
    """


@businesses_bp.route("/our-businesses")
def our_businesses_page() -> str:
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "id")
    direction = request.args.get("direction", "asc")
    page_raw = request.args.get("page", "1")
    export_format = request.args.get("export", "").strip().lower()
    page = int(page_raw) if page_raw.isdigit() else 1

    items = OurBusiness.query.order_by(OurBusiness.id.asc()).all()
    if q:
        q_lower = q.lower()
        items = [
            item for item in items
            if q_lower in item.name.lower()
            or q_lower in item.business_number.lower()
            or q_lower in item.phone.lower()
            or q_lower in item.ceo_name.lower()
        ]

    sort_funcs = {
        "id": lambda item: item.id,
        "name": lambda item: item.name.lower(),
        "business_number": lambda item: item.business_number,
        "phone": lambda item: item.phone,
        "is_active": lambda item: item.is_active,
    }
    items = sort_items(items, sort, sort_funcs, direction)

    export_headers = ["번호", "사업자명", "사업자등록번호", "대표전화", "사용여부"]
    export_rows = [[item.id, item.name, item.business_number, item.phone, "사용" if item.is_active else "미사용"] for item in items]
    export_response = export_table("our_businesses", "사업자목록", export_headers, export_rows, export_format)
    if export_response:
        return export_response

    paged_items, total_count, total_pages = paginate_items(items, page, 10)
    rows = ""
    for item in paged_items:
        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td><a href="/our-businesses/{item.id}">{item.name}</a></td>
            <td>{item.business_number}</td>
            <td>{item.phone}</td>
            <td>{'사용' if item.is_active else '미사용'}</td>
            <td>{_business_action_forms(item, compact=True)}</td>
        </tr>
        """

    current_params = {"q": q, "sort": sort, "direction": direction}
    toolbar = render_table_toolbar(
        base_path="/our-businesses",
        current_params=current_params,
        search_placeholder="사업자명, 등록번호, 대표전화 검색",
        search_value=q,
        sort_options=[("id", "번호"), ("name", "사업자명"), ("business_number", "사업자등록번호"), ("phone", "대표전화"), ("is_active", "사용여부")],
        current_sort=sort,
        current_direction=direction,
        create_href="/our-businesses/new",
        create_label="+ 사업자등록",
        reset_href="/our-businesses",
    )
    pagination = render_pagination("/our-businesses", current_params, page, total_pages, total_count)
    content = f"""
    <div class="panel">
        <div class="panel-head"><h2>사업자목록</h2><p>우리측 운영 사업자 관리</p></div>
        <div class="panel-body">
            {toolbar}
            <table>
                <thead><tr><th>번호</th><th>사업자명</th><th>사업자등록번호</th><th>대표전화</th><th>사용여부</th><th>관리</th></tr></thead>
                <tbody>{rows or '<tr><td colspan="6">데이터가 없습니다.</td></tr>'}</tbody>
            </table>
            {pagination}
        </div>
    </div>
    """
    quick = [{"label": "사업자목록", "href": "/our-businesses", "active": True}, {"label": "사업자등록", "href": "/our-businesses/new", "active": False}]
    return render_page("사업자관리", "our_businesses", content, quick)


@businesses_bp.route("/our-businesses/new", methods=["GET", "POST"])
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
        flash("사업자가 등록되었습니다.", "success")
        return redirect(url_for("businesses.our_businesses_page"))

    content = """
    <div class="panel">
        <div class="panel-head"><h2>사업자등록</h2><p>우리측 운영 사업자 등록</p></div>
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
                    <div><label>사용여부</label><select name="is_active"><option value="Y">사용</option><option value="N">미사용</option></select></div>
                    <div style="grid-column:1 / -1;"><label>메모</label><textarea name="memo"></textarea></div>
                </div>
                <div class="actions"><button class="btn btn-primary" type="submit">저장</button><a class="btn btn-white" href="/our-businesses">취소</a></div>
            </form>
        </div>
    </div>
    """
    quick = [{"label": "사업자목록", "href": "/our-businesses", "active": False}, {"label": "사업자등록", "href": "/our-businesses/new", "active": True}]
    return render_page("사업자등록", "our_businesses", content, quick)


@businesses_bp.route("/our-businesses/<int:our_business_id>/edit", methods=["GET", "POST"])
def our_business_edit(our_business_id: int) -> str:
    item = OurBusiness.query.get_or_404(our_business_id)
    if request.method == "POST":
        item.name = request.form["name"].strip()
        item.ceo_name = request.form["ceo_name"].strip()
        item.business_number = request.form["business_number"].strip()
        item.phone = request.form["phone"].strip()
        item.address = request.form["address"].strip()
        item.business_type = request.form.get("business_type", "").strip()
        item.business_item = request.form.get("business_item", "").strip()
        item.email = request.form.get("email", "").strip()
        item.is_active = request.form.get("is_active", "Y") == "Y"
        item.memo = request.form.get("memo", "").strip()
        item.updated_at = today_str()
        db.session.commit()
        flash("사업자 정보가 수정되었습니다.", "success")
        return redirect(url_for("businesses.our_business_detail", our_business_id=item.id))

    content = f"""
    <div class="panel">
        <div class="panel-head"><h2>사업자수정</h2><p>{item.name}</p></div>
        <div class="panel-body">
            <form method="post">
                <div class="form-grid">
                    <div><label>사업자명</label><input name="name" value="{item.name}" required></div>
                    <div><label>대표자명</label><input name="ceo_name" value="{item.ceo_name}" required></div>
                    <div><label>사업자등록번호</label><input name="business_number" value="{item.business_number}" required></div>
                    <div><label>대표전화</label><input name="phone" value="{item.phone}" required></div>
                    <div><label>주소</label><input name="address" value="{item.address}" required></div>
                    <div><label>업태</label><input name="business_type" value="{item.business_type or ''}"></div>
                    <div><label>종목</label><input name="business_item" value="{item.business_item or ''}"></div>
                    <div><label>이메일</label><input name="email" value="{item.email or ''}"></div>
                    <div><label>사용여부</label><select name="is_active"><option value="Y" {'selected' if item.is_active else ''}>사용</option><option value="N" {'selected' if not item.is_active else ''}>미사용</option></select></div>
                    <div style="grid-column:1 / -1;"><label>메모</label><textarea name="memo">{item.memo or ''}</textarea></div>
                </div>
                <div class="actions"><button class="btn btn-primary" type="submit">수정 저장</button><a class="btn btn-white" href="/our-businesses/{item.id}">취소</a></div>
            </form>
        </div>
    </div>
    """
    quick = [{"label": "사업자목록", "href": "/our-businesses", "active": False}, {"label": "사업자수정", "href": f"/our-businesses/{item.id}/edit", "active": True}]
    return render_page("사업자수정", "our_businesses", content, quick)


@businesses_bp.route("/our-businesses/<int:our_business_id>/toggle-active", methods=["POST"])
def our_business_toggle_active(our_business_id: int):
    item = OurBusiness.query.get_or_404(our_business_id)
    item.is_active = not item.is_active
    item.updated_at = today_str()
    db.session.commit()
    flash(f"사업자가 {'활성' if item.is_active else '비활성'} 상태로 변경되었습니다.", "success")
    return redirect(request.referrer or url_for("businesses.our_businesses_page"))


@businesses_bp.route("/our-businesses/<int:our_business_id>/delete", methods=["POST"])
def our_business_delete(our_business_id: int):
    item = OurBusiness.query.get_or_404(our_business_id)
    linked_clients = ClientCompany.query.filter_by(our_business_id=our_business_id).count()
    if linked_clients:
        flash("연결된 거래처가 있어 사업자를 삭제할 수 없습니다. 먼저 거래처를 정리하거나 비활성으로 전환하세요.", "error")
        return redirect(request.referrer or url_for("businesses.our_business_detail", our_business_id=our_business_id))

    db.session.delete(item)
    db.session.commit()
    flash("사업자가 삭제되었습니다.", "success")
    return redirect(url_for("businesses.our_businesses_page"))


@businesses_bp.route("/our-businesses/<int:our_business_id>")
def our_business_detail(our_business_id: int) -> str:
    item = OurBusiness.query.get_or_404(our_business_id)
    client_count = ClientCompany.query.filter_by(our_business_id=our_business_id).count()
    content = f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-head"><h2>사업자상세</h2><p>{item.name}</p></div>
        <div class="panel-body">
            {_business_action_forms(item)}
        </div>
    </div>
    <div class="panel">
        <div class="panel-head"><h2>사업자상세</h2><p>{item.name}</p></div>
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
    quick = [{"label": "사업자목록", "href": "/our-businesses", "active": True}, {"label": "사업자등록", "href": "/our-businesses/new", "active": False}]
    return render_page("사업자상세", "our_businesses", content, quick)
