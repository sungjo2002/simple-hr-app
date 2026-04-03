from flask import Blueprint, flash, redirect, request, url_for

from models import ClientCompany, ClientCompanyPayrollSetting, ClientCompanySetting, ClientCompanyWorkType, Employee, db
from utils import (
    export_table,
    get_client_company,
    get_client_company_work_types,
    get_our_business_name,
    paginate_items,
    render_our_business_options,
    render_page,
    render_pagination,
    render_table_toolbar,
    sort_items,
    today_str,
)

clients_bp = Blueprint("clients", __name__)


@clients_bp.route("/client-companies")
def client_companies_page() -> str:
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "id")
    direction = request.args.get("direction", "asc")
    page_raw = request.args.get("page", "1")
    export_format = request.args.get("export", "").strip().lower()
    page = int(page_raw) if page_raw.isdigit() else 1

    items = ClientCompany.query.order_by(ClientCompany.id.asc()).all()
    if q:
        q_lower = q.lower()
        items = [
            item for item in items
            if q_lower in item.name.lower()
            or q_lower in item.business_number.lower()
            or q_lower in item.phone.lower()
            or q_lower in get_our_business_name(item.our_business_id).lower()
        ]

    sort_funcs = {
        "id": lambda item: item.id,
        "our_business": lambda item: get_our_business_name(item.our_business_id).lower(),
        "name": lambda item: item.name.lower(),
        "business_number": lambda item: item.business_number,
        "phone": lambda item: item.phone,
        "is_active": lambda item: item.is_active,
    }
    items = sort_items(items, sort, sort_funcs, direction)

    export_headers = ["번호", "사업자", "거래처명", "사업자등록번호", "대표전화", "사용여부"]
    export_rows = [[item.id, get_our_business_name(item.our_business_id), item.name, item.business_number, item.phone, "사용" if item.is_active else "미사용"] for item in items]
    export_response = export_table("client_companies", "거래처목록", export_headers, export_rows, export_format)
    if export_response:
        return export_response

    paged_items, total_count, total_pages = paginate_items(items, page, 10)
    rows = ""
    for item in paged_items:
        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td>{get_our_business_name(item.our_business_id)}</td>
            <td><a href="/client-companies/{item.id}">{item.name}</a></td>
            <td>{item.business_number}</td>
            <td>{item.phone}</td>
            <td>{"사용" if item.is_active else "미사용"}</td>
        </tr>
        """

    current_params = {"q": q, "sort": sort, "direction": direction}
    toolbar = render_table_toolbar(
        base_path="/client-companies",
        current_params=current_params,
        search_placeholder="거래처명, 사업자, 등록번호, 대표전화 검색",
        search_value=q,
        sort_options=[("id", "번호"), ("our_business", "사업자"), ("name", "거래처명"), ("business_number", "사업자등록번호"), ("phone", "대표전화"), ("is_active", "사용여부")],
        current_sort=sort,
        current_direction=direction,
        create_href="/client-companies/new",
        create_label="+ 거래처등록",
        reset_href="/client-companies",
    )
    pagination = render_pagination("/client-companies", current_params, page, total_pages, total_count)
    content = f"""
    <div class="panel">
        <div class="panel-head"><h2>거래처목록</h2><p>사업자 소속 거래처 사업자 관리</p></div>
        <div class="panel-body">
            {toolbar}
            <table>
                <thead><tr><th>번호</th><th>사업자</th><th>거래처명</th><th>사업자등록번호</th><th>대표전화</th><th>사용여부</th></tr></thead>
                <tbody>{rows or '<tr><td colspan="6">데이터가 없습니다.</td></tr>'}</tbody>
            </table>
            {pagination}
        </div>
    </div>
    """
    quick = [{"label": "거래처목록", "href": "/client-companies", "active": True}, {"label": "거래처등록", "href": "/client-companies/new", "active": False}]
    return render_page("거래처관리", "client_companies", content, quick)


@clients_bp.route("/client-companies/new", methods=["GET", "POST"])
def client_company_new() -> str:
    if request.method == "POST":
        item = ClientCompany(
            our_business_id=int(request.form["our_business_id"]),
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

        db.session.add(ClientCompanySetting(client_company_id=item.id, attendance_open_time="08:00", late_standard_time="09:00", workday_standard_hours=8, hospital_paid=True, document_view_policy="sensitive_super_admin_only"))
        db.session.add(ClientCompanyPayrollSetting(client_company_id=item.id, default_pay_type="monthly", base_salary=2200000, daily_wage=100000, hourly_wage=10000, night_allowance_rate=1.5, overtime_allowance_rate=1.5, hospital_pay_type="paid", absence_deduction_amount=80000, meal_allowance=100000, transport_allowance=70000, position_allowance=30000))
        db.session.add(ClientCompanyWorkType(client_company_id=item.id, name="주간", code="DAY", is_active=True))
        db.session.add(ClientCompanyWorkType(client_company_id=item.id, name="야간", code="NIGHT", is_active=True))
        db.session.commit()
        flash("거래처가 등록되었습니다.", "success")
        return redirect(url_for("clients.client_companies_page"))

    business_options = render_our_business_options()
    content = f"""
    <div class="panel">
        <div class="panel-head"><h2>거래처등록</h2><p>사업자 소속 거래처 사업자 등록</p></div>
        <div class="panel-body">
            <form method="post">
                <div class="form-grid">
                    <div><label>사업자</label><select name="our_business_id">{business_options}</select></div>
                    <div><label>거래처명</label><input name="name" required></div>
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
                <div class="actions"><button class="btn btn-primary" type="submit">저장</button><a class="btn btn-white" href="/client-companies">취소</a></div>
            </form>
        </div>
    </div>
    """
    quick = [{"label": "거래처목록", "href": "/client-companies", "active": False}, {"label": "거래처등록", "href": "/client-companies/new", "active": True}]
    return render_page("거래처등록", "client_companies", content, quick)


@clients_bp.route("/client-companies/<int:client_company_id>")
def client_company_detail(client_company_id: int) -> str:
    item = get_client_company(client_company_id)
    if not item:
        return "거래처를 찾을 수 없습니다.", 404
    work_types = ", ".join(w.name for w in get_client_company_work_types(client_company_id)) or "-"
    employee_count = Employee.query.filter_by(current_client_company_id=client_company_id).count()
    content = f"""
    <div class="panel">
        <div class="panel-head"><h2>거래처상세</h2><p>{item.name}</p></div>
        <div class="panel-body">
            <table>
                <tr><th style="width:220px;">사업자</th><td>{get_our_business_name(item.our_business_id)}</td></tr>
                <tr><th>거래처명</th><td>{item.name}</td></tr>
                <tr><th>대표자명</th><td>{item.ceo_name}</td></tr>
                <tr><th>사업자등록번호</th><td>{item.business_number}</td></tr>
                <tr><th>대표전화</th><td>{item.phone}</td></tr>
                <tr><th>주소</th><td>{item.address}</td></tr>
                <tr><th>업태</th><td>{item.business_type or '-'}</td></tr>
                <tr><th>종목</th><td>{item.business_item or '-'}</td></tr>
                <tr><th>이메일</th><td>{item.email or '-'}</td></tr>
                <tr><th>사용여부</th><td>{"사용" if item.is_active else "미사용"}</td></tr>
                <tr><th>근무타입</th><td>{work_types}</td></tr>
                <tr><th>배치 인원</th><td>{employee_count}</td></tr>
                <tr><th>메모</th><td>{item.memo or '-'}</td></tr>
            </table>
        </div>
    </div>
    """
    quick = [{"label": "거래처목록", "href": "/client-companies", "active": True}, {"label": "거래처등록", "href": "/client-companies/new", "active": False}]
    return render_page("거래처상세", "client_companies", content, quick)
