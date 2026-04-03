from flask import Blueprint, request

from models import ClientCompany
from utils import (
    PAY_TYPE_LABELS,
    calculate_payroll_for_employee,
    export_table,
    format_won,
    get_client_company,
    get_client_company_name,
    get_employees_by_client_company,
    get_our_business_name,
    month_str_default,
    paginate_items,
    parse_month,
    render_page,
    render_pagination,
    render_table_toolbar,
    sort_items,
)

payroll_bp = Blueprint("payroll", __name__)


@payroll_bp.route("/payroll")
def payroll_page() -> str:
    clients = ClientCompany.query.order_by(ClientCompany.id.asc()).all()
    if not clients:
        return "먼저 거래처를 등록하세요.", 400

    selected_client_raw = request.args.get("client_company_id", str(clients[0].id))
    selected_client_company_id = int(selected_client_raw) if selected_client_raw.isdigit() else clients[0].id
    selected_month = request.args.get("month", month_str_default())
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "name")
    direction = request.args.get("direction", "asc")
    page_raw = request.args.get("page", "1")
    export_format = request.args.get("export", "").strip().lower()
    page = int(page_raw) if page_raw.isdigit() else 1
    year, month = parse_month(selected_month)

    items = []
    for employee in get_employees_by_client_company(selected_client_company_id):
        payroll = calculate_payroll_for_employee(employee, year, month)
        row = {"employee": employee, "payroll": payroll}
        items.append(row)

    if q:
        q_lower = q.lower()
        items = [
            row for row in items
            if q_lower in row["employee"].name.lower()
            or q_lower in row["employee"].nationality.lower()
            or q_lower in PAY_TYPE_LABELS.get(row["employee"].pay_type, "-").lower()
        ]

    sort_funcs = {
        "name": lambda row: row["employee"].name.lower(),
        "nationality": lambda row: row["employee"].nationality.lower(),
        "pay_type": lambda row: PAY_TYPE_LABELS.get(row["employee"].pay_type, "-"),
        "work_days": lambda row: row["payroll"]["work_days"],
        "absent_days": lambda row: row["payroll"]["absent_days"],
        "final_amount": lambda row: row["payroll"]["final_amount"],
    }
    items = sort_items(items, sort, sort_funcs, direction)

    export_headers = ["이름", "국적", "급여형태", "근무일수", "병원", "휴가", "결근", "야간", "연장시간", "기본급", "수당", "공제", "실지급액"]
    export_rows = [
        [
            row["employee"].name,
            row["employee"].nationality,
            PAY_TYPE_LABELS.get(row["employee"].pay_type, "-"),
            row["payroll"]["work_days"],
            row["payroll"]["hospital_days"],
            row["payroll"]["vacation_days"],
            row["payroll"]["absent_days"],
            round(row["payroll"]["night_minutes"] / 60, 1),
            round(row["payroll"]["overtime_minutes"] / 60, 1),
            row["payroll"]["base_amount"],
            row["payroll"]["allowance_amount"],
            row["payroll"]["deduction_amount"],
            row["payroll"]["final_amount"],
        ]
        for row in items
    ]
    export_response = export_table("payroll", "급여대장", export_headers, export_rows, export_format)
    if export_response:
        return export_response

    total_final_amount = sum(row["payroll"]["final_amount"] for row in items)
    paged_items, total_count, total_pages = paginate_items(items, page, 10)

    rows = ""
    for row in paged_items:
        employee = row["employee"]
        payroll = row["payroll"]
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
    current_params = {"client_company_id": selected_client_company_id, "month": selected_month, "q": q, "sort": sort, "direction": direction}
    toolbar = render_table_toolbar(
        base_path="/payroll",
        current_params=current_params,
        search_placeholder="이름, 국적, 급여형태 검색",
        search_value=q,
        sort_options=[("name", "이름"), ("nationality", "국적"), ("pay_type", "급여형태"), ("work_days", "근무일수"), ("absent_days", "결근"), ("final_amount", "실지급액")],
        current_sort=sort,
        current_direction=direction,
        reset_href=f"/payroll?client_company_id={selected_client_company_id}&month={selected_month}",
    ).replace('<input type="hidden" name="page" value="1">', f'<input type="hidden" name="page" value="1"><input type="hidden" name="client_company_id" value="{selected_client_company_id}"><input type="hidden" name="month" value="{selected_month}">')
    pagination = render_pagination("/payroll", current_params, page, total_pages, total_count)

    content = f"""
    <div class="panel" style="margin-bottom:18px;" id="payroll-filter">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <div><label>거래처 선택</label><select name="client_company_id">{''.join(client_options)}</select></div>
                <div><label>월 선택</label><input type="month" name="month" value="{selected_month}"></div>
                <input type="hidden" name="q" value="{q}">
                <input type="hidden" name="sort" value="{sort}">
                <input type="hidden" name="direction" value="{direction}">
                <div><button class="btn btn-white" type="submit">조회</button></div>
            </form>
        </div>
    </div>
    <div class="cards">
        <div class="card"><div class="label">사업자</div><div class="value" style="font-size:22px;">{get_our_business_name(selected_client.our_business_id if selected_client else None)}</div></div>
        <div class="card"><div class="label">거래처</div><div class="value" style="font-size:22px;">{get_client_company_name(selected_client_company_id)}</div></div>
        <div class="card"><div class="label">대상 월</div><div class="value" style="font-size:22px;">{selected_month}</div></div>
        <div class="card"><div class="label">대상 인력</div><div class="value">{total_count}</div></div>
        <div class="card"><div class="label">총 실지급액</div><div class="value" style="font-size:22px;">{format_won(total_final_amount)}</div></div>
    </div>
    <div class="panel" id="payroll-table">
        <div class="panel-head"><h2>급여대장</h2><p>출퇴근 기록 기반 계산 결과</p></div>
        <div class="panel-body">
            {toolbar}
            <table>
                <thead><tr><th>이름</th><th>국적</th><th>급여형태</th><th>근무일수</th><th>병원</th><th>휴가</th><th>결근</th><th>야간</th><th>연장시간</th><th>기본급</th><th>수당</th><th>공제</th><th>실지급액</th></tr></thead>
                <tbody>{rows or '<tr><td colspan="13">인력이 없습니다.</td></tr>'}</tbody>
            </table>
            {pagination}
        </div>
    </div>
    """
    return render_page("급여관리", "payroll", content, [
        {"label": "급여계산", "href": "/payroll", "active": True},
        {"label": "지급내역", "href": "/payroll#payroll-table", "active": False},
    ])
