from flask import Blueprint, request

from models import ClientCompany
from utils import PAY_TYPE_LABELS, calculate_payroll_for_employee, format_won, get_client_company, get_client_company_name, get_employees_by_client_company, get_our_business_name, month_str_default, parse_month, render_page

payroll_bp = Blueprint("payroll", __name__)


@payroll_bp.route("/payroll")
def payroll_page() -> str:
    clients = ClientCompany.query.order_by(ClientCompany.id.asc()).all()
    if not clients:
        return "먼저 거래처를 등록하세요.", 400

    selected_client_raw = request.args.get("client_company_id", str(clients[0].id))
    selected_client_company_id = int(selected_client_raw) if selected_client_raw.isdigit() else clients[0].id
    selected_month = request.args.get("month", month_str_default())
    year, month = parse_month(selected_month)

    filtered_employees = get_employees_by_client_company(selected_client_company_id)
    rows = ""
    total_final_amount = 0
    for employee in filtered_employees:
        payroll = calculate_payroll_for_employee(employee, year, month)
        total_final_amount += payroll["final_amount"]
        rows += f"""
        <tr>
            <td><a href="/employees/{employee.id}">{employee.name}</a></td>
            <td>{employee.nationality}</td>
            <td>{PAY_TYPE_LABELS.get(employee.pay_type, '-')}</td>
            <td>{payroll["work_days"]}</td>
            <td>{payroll["hospital_days"]}</td>
            <td>{payroll["vacation_days"]}</td>
            <td style="color:#b91c1c; font-weight:bold;">{payroll["absent_days"]}</td>
            <td>{round(payroll["night_minutes"] / 60, 1)}h</td>
            <td>{round(payroll["overtime_minutes"] / 60, 1)}h</td>
            <td>{format_won(payroll["base_amount"])}</td>
            <td>{format_won(payroll["allowance_amount"])}</td>
            <td>{format_won(payroll["deduction_amount"])}</td>
            <td style="font-weight:bold; color:#1d4ed8;">{format_won(payroll["final_amount"])}</td>
        </tr>
        """
    client_options = []
    for client in clients:
        selected = "selected" if client.id == selected_client_company_id else ""
        client_options.append(f'<option value="{client.id}" {selected}>{client.name}</option>')

    selected_client = get_client_company(selected_client_company_id)
    content = f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <div><label>거래처 선택</label><select name="client_company_id">{"".join(client_options)}</select></div>
                <div><label>월 선택</label><input type="month" name="month" value="{selected_month}"></div>
                <div><button class="btn btn-white" type="submit">조회</button></div>
            </form>
        </div>
    </div>
    <div class="cards">
        <div class="card"><div class="label">사업자</div><div class="value" style="font-size:22px;">{get_our_business_name(selected_client.our_business_id if selected_client else None)}</div></div>
        <div class="card"><div class="label">거래처</div><div class="value" style="font-size:22px;">{get_client_company_name(selected_client_company_id)}</div></div>
        <div class="card"><div class="label">대상 월</div><div class="value" style="font-size:22px;">{selected_month}</div></div>
        <div class="card"><div class="label">대상 인력</div><div class="value">{len(filtered_employees)}</div></div>
        <div class="card"><div class="label">총 실지급액</div><div class="value" style="font-size:22px;">{format_won(total_final_amount)}</div></div>
    </div>
    <div class="panel">
        <div class="panel-head"><h2>급여대장</h2><p>출퇴근 기록 기반 계산 결과</p></div>
        <div class="panel-body">
            <table>
                <thead><tr><th>이름</th><th>국적</th><th>급여형태</th><th>근무일수</th><th>병원</th><th>휴가</th><th>결근</th><th>야간</th><th>연장시간</th><th>기본급</th><th>수당</th><th>공제</th><th>실지급액</th></tr></thead>
                <tbody>{rows or '<tr><td colspan="13">인력이 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    return render_page("급여관리", "payroll", content, [{"label": "급여관리", "href": "/payroll"}])
