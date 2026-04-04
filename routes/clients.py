from flask import Blueprint, redirect, request, url_for

from models import ClientCompany, ClientCompanyPayrollSetting, ClientCompanySetting, ClientCompanyWorkType, Employee, db
from utils import get_client_company, get_client_company_name, get_client_company_work_types, get_our_business_name, render_our_business_options, render_page, today_str

clients_bp = Blueprint("clients", __name__)


def _client_action_buttons(item: ClientCompany) -> str:
    toggle_label = "비활성" if item.is_active else "활성"
    return f"""
    <div class="actions" style="margin:0; gap:8px; flex-wrap:wrap;">
        <a class="btn btn-white" href="/client-companies/{item.id}/edit">수정</a>
        <form method="post" action="/client-companies/{item.id}/toggle" onsubmit="return confirm('상태를 변경할까요?');">
            <button class="btn btn-white" type="submit">{toggle_label}</button>
        </form>
        <form method="post" action="/client-companies/{item.id}/delete" onsubmit="return confirm('삭제할까요? 배치 인원이 있으면 삭제되지 않습니다.');">
            <button class="btn btn-danger" type="submit">삭제</button>
        </form>
    </div>
    """


@clients_bp.route("/client-companies")
def client_companies_page() -> str:
    rows = ""
    for item in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td>{get_our_business_name(item.our_business_id)}</td>
            <td><a href="/client-companies/{item.id}">{item.name}</a></td>
            <td>{item.business_number}</td>
            <td>{item.phone}</td>
            <td>{"사용" if item.is_active else "미사용"}</td>
            <td>{_client_action_buttons(item)}</td>
        </tr>
        """
    content = f"""
    <div class="panel">
        <div class="panel-head"><h2>거래처목록</h2><p>사업자 소속 거래처 사업자 관리</p></div>
        <div class="panel-body">
            <div class="actions" style="margin-top:0; margin-bottom:16px;"><a class="btn btn-primary" href="/client-companies/new">+ 거래처등록</a></div>
            <table>
                <thead><tr><th>번호</th><th>사업자</th><th>거래처명</th><th>사업자등록번호</th><th>대표전화</th><th>사용여부</th><th>관리</th></tr></thead>
                <tbody>{rows or '<tr><td colspan="7">데이터가 없습니다.</td></tr>'}</tbody>
            </table>
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
            <div class="actions" style="margin-top:0; margin-bottom:16px;">{_client_action_buttons(item)}</div>
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


@clients_bp.route("/client-companies/<int:client_company_id>/edit", methods=["GET", "POST"])
def client_company_edit(client_company_id: int) -> str:
    item = get_client_company(client_company_id)
    if not item:
        return "거래처를 찾을 수 없습니다.", 404

    if request.method == "POST":
        item.our_business_id = int(request.form["our_business_id"])
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
        return redirect(url_for("clients.client_company_detail", client_company_id=client_company_id))

    business_options = render_our_business_options(item.our_business_id)
    content = f"""
    <div class="panel">
        <div class="panel-head"><h2>거래처수정</h2><p>{item.name}</p></div>
        <div class="panel-body">
            <form method="post">
                <div class="form-grid">
                    <div><label>사업자</label><select name="our_business_id">{business_options}</select></div>
                    <div><label>거래처명</label><input name="name" value="{item.name}" required></div>
                    <div><label>대표자명</label><input name="ceo_name" value="{item.ceo_name}" required></div>
                    <div><label>사업자등록번호</label><input name="business_number" value="{item.business_number}" required></div>
                    <div><label>대표전화</label><input name="phone" value="{item.phone}" required></div>
                    <div><label>주소</label><input name="address" value="{item.address}" required></div>
                    <div><label>업태</label><input name="business_type" value="{item.business_type or ''}"></div>
                    <div><label>종목</label><input name="business_item" value="{item.business_item or ''}"></div>
                    <div><label>이메일</label><input name="email" value="{item.email or ''}"></div>
                    <div><label>사용여부</label><select name="is_active"><option value="Y" {"selected" if item.is_active else ""}>사용</option><option value="N" {"selected" if not item.is_active else ""}>미사용</option></select></div>
                    <div style="grid-column:1 / -1;"><label>메모</label><textarea name="memo">{item.memo or ''}</textarea></div>
                </div>
                <div class="actions"><button class="btn btn-primary" type="submit">저장</button><a class="btn btn-white" href="/client-companies/{item.id}">취소</a></div>
            </form>
        </div>
    </div>
    """
    quick = [{"label": "거래처목록", "href": "/client-companies", "active": False}, {"label": "거래처등록", "href": "/client-companies/new", "active": False}]
    return render_page("거래처수정", "client_companies", content, quick)


@clients_bp.route("/client-companies/<int:client_company_id>/toggle", methods=["POST"])
def client_company_toggle(client_company_id: int):
    item = get_client_company(client_company_id)
    if not item:
        return "거래처를 찾을 수 없습니다.", 404
    item.is_active = not item.is_active
    item.updated_at = today_str()
    db.session.commit()
    return redirect(request.referrer or url_for("clients.client_companies_page"))


@clients_bp.route("/client-companies/<int:client_company_id>/delete", methods=["POST"])
def client_company_delete(client_company_id: int):
    item = get_client_company(client_company_id)
    if not item:
        return "거래처를 찾을 수 없습니다.", 404
    employee_count = Employee.query.filter_by(current_client_company_id=client_company_id).count()
    if employee_count == 0:
        ClientCompanyWorkType.query.filter_by(client_company_id=client_company_id).delete()
        ClientCompanySetting.query.filter_by(client_company_id=client_company_id).delete()
        ClientCompanyPayrollSetting.query.filter_by(client_company_id=client_company_id).delete()
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for("clients.client_companies_page"))
