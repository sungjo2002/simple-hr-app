from flask import Blueprint, redirect, request, url_for

from models import ClientCompany
from utils import (
    export_table,
    get_attendance_record,
    get_client_company_name,
    get_employees_by_client_company,
    get_our_business_name,
    get_work_type_name,
    paginate_items,
    render_page,
    render_pagination,
    render_table_toolbar,
    sort_items,
    status_badge,
    today_str,
    update_attendance,
)

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/attendance", methods=["GET", "POST"])
def attendance_page() -> str:
    selected_date = request.values.get("work_date", today_str())
    selected_client_raw = request.values.get("client_company_id", "")
    selected_client_company_id = int(selected_client_raw) if selected_client_raw.isdigit() else None

    if request.method == "POST":
        update_attendance(
            employee_id=int(request.form["employee_id"]),
            work_date=request.form["work_date"],
            action_type=request.form["action_type"],
            reason=request.form.get("reason", "").strip(),
            overtime_minutes=int(request.form.get("overtime_minutes", 0) or 0),
            night_minutes=int(request.form.get("night_minutes", 0) or 0),
        )
        return redirect(url_for("attendance.attendance_page", work_date=request.form["work_date"], client_company_id=request.form.get("client_company_id", "")))

    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "name")
    direction = request.args.get("direction", "asc")
    page_raw = request.args.get("page", "1")
    export_format = request.args.get("export", "").strip().lower()
    page = int(page_raw) if page_raw.isdigit() else 1

    employee_list = get_employees_by_client_company(selected_client_company_id)
    if q:
        q_lower = q.lower()
        employee_list = [
            employee for employee in employee_list
            if q_lower in employee.name.lower()
            or q_lower in employee.nationality.lower()
            or q_lower in get_our_business_name(employee.our_business_id).lower()
            or q_lower in get_client_company_name(employee.current_client_company_id).lower()
            or q_lower in get_work_type_name(employee.work_type_id).lower()
        ]

    sort_funcs = {
        "name": lambda employee: employee.name.lower(),
        "nationality": lambda employee: employee.nationality.lower(),
        "our_business": lambda employee: get_our_business_name(employee.our_business_id).lower(),
        "client_company": lambda employee: get_client_company_name(employee.current_client_company_id).lower(),
        "work_type": lambda employee: get_work_type_name(employee.work_type_id).lower(),
        "status": lambda employee: (get_attendance_record(employee.id, selected_date).status if get_attendance_record(employee.id, selected_date) else "before_work"),
    }
    employee_list = sort_items(employee_list, sort, sort_funcs, direction)

    export_headers = ["이름", "국적", "사업자", "거래처", "근무타입", "상태", "출근", "퇴근", "사유"]
    export_rows = []
    for employee in employee_list:
        record = get_attendance_record(employee.id, selected_date)
        export_rows.append([
            employee.name,
            employee.nationality,
            get_our_business_name(employee.our_business_id),
            get_client_company_name(employee.current_client_company_id),
            get_work_type_name(employee.work_type_id),
            record.status if record else "before_work",
            record.check_in_at if record and record.check_in_at else "-",
            record.check_out_at if record and record.check_out_at else "-",
            record.reason if record and record.reason else "-",
        ])
    export_response = export_table("attendance", "출퇴현황", export_headers, export_rows, export_format)
    if export_response:
        return export_response

    paged_employees, total_count, total_pages = paginate_items(employee_list, page, 10)
    client_filter_options = ['<option value="">전체 거래처</option>']
    for client in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if selected_client_company_id == client.id else ""
        client_filter_options.append(f'<option value="{client.id}" {selected}>{client.name}</option>')

    employee_options = ""
    for employee in employee_list:
        employee_options += f'<option value="{employee.id}">{employee.name} / {employee.nationality} / {get_client_company_name(employee.current_client_company_id)} / {get_work_type_name(employee.work_type_id)}</option>'

    rows = ""
    for employee in paged_employees:
        record = get_attendance_record(employee.id, selected_date)
        rows += f"""
        <tr>
            <td>{employee.name}</td>
            <td>{employee.nationality}</td>
            <td>{get_our_business_name(employee.our_business_id)}</td>
            <td>{get_client_company_name(employee.current_client_company_id)}</td>
            <td>{get_work_type_name(employee.work_type_id)}</td>
            <td>{status_badge(record.status if record else "before_work")}</td>
            <td>{record.check_in_at if record and record.check_in_at else '-'}</td>
            <td>{record.check_out_at if record and record.check_out_at else '-'}</td>
            <td>{record.reason if record and record.reason else '-'}</td>
        </tr>
        """

    current_params = {"work_date": selected_date, "client_company_id": selected_client_raw, "q": q, "sort": sort, "direction": direction}
    toolbar = render_table_toolbar(
        base_path="/attendance",
        current_params=current_params,
        search_placeholder="이름, 국적, 사업자, 거래처, 근무타입 검색",
        search_value=q,
        sort_options=[("name", "이름"), ("nationality", "국적"), ("our_business", "사업자"), ("client_company", "거래처"), ("work_type", "근무타입"), ("status", "상태")],
        current_sort=sort,
        current_direction=direction,
        reset_href=f"/attendance?work_date={selected_date}",
    ).replace('<input type="hidden" name="page" value="1">', f'<input type="hidden" name="page" value="1"><input type="hidden" name="work_date" value="{selected_date}"><input type="hidden" name="client_company_id" value="{selected_client_raw}">')
    pagination = render_pagination("/attendance", current_params, page, total_pages, total_count)

    content = f"""
    <div class="content-grid">
        <div class="panel" id="attendance-table">
            <div class="panel-head"><h2>오늘 출퇴현황</h2><p>선택 날짜: <strong>{selected_date}</strong></p></div>
            <div class="panel-body">
                <form method="get" class="actions" style="margin-top:0; margin-bottom:16px;">
                    <div><label>날짜 선택</label><input type="date" name="work_date" value="{selected_date}"></div>
                    <div><label>거래처 선택</label><select name="client_company_id">{''.join(client_filter_options)}</select></div>
                    <input type="hidden" name="q" value="{q}">
                    <input type="hidden" name="sort" value="{sort}">
                    <input type="hidden" name="direction" value="{direction}">
                    <div><button class="btn btn-white" type="submit">조회</button></div>
                    <div><a class="btn btn-white" href="/attendance?work_date={today_str()}">오늘</a></div>
                </form>
                {toolbar}
                <table>
                    <thead><tr><th>이름</th><th>국적</th><th>사업자</th><th>거래처</th><th>근무타입</th><th>상태</th><th>출근</th><th>퇴근</th><th>사유</th></tr></thead>
                    <tbody>{rows or '<tr><td colspan="9">인력이 없습니다.</td></tr>'}</tbody>
                </table>
                {pagination}
            </div>
        </div>
        <div class="panel">
            <div class="panel-head"><h2>출근 / 퇴근 / 병원 / 휴가 / 결근 처리</h2><p>1일 1레코드 갱신 방식</p></div>
            <div class="panel-body">
                <form method="post">
                    <input type="hidden" name="work_date" value="{selected_date}">
                    <input type="hidden" name="client_company_id" value="{selected_client_raw}">
                    <div class="form-grid">
                        <div style="grid-column:1 / -1;"><label>인력 선택</label><select name="employee_id" required>{employee_options}</select></div>
                        <div><label>처리 유형</label><select name="action_type"><option value="check_in">출근</option><option value="check_out">퇴근</option><option value="hospital">병원</option><option value="vacation">휴가</option><option value="absent">결근</option></select></div>
                        <div><label>사유</label><input name="reason" placeholder="병원/휴가/결근 사유"></div>
                        <div><label>연장근무(분)</label><input type="number" name="overtime_minutes" value="0" min="0"></div>
                        <div><label>야간근무(분)</label><input type="number" name="night_minutes" value="0" min="0"></div>
                    </div>
                    <div class="actions"><button class="btn btn-primary" type="submit">저장</button></div>
                </form>
            </div>
        </div>
    </div>
    """
    quick = [{"label": "출퇴현황", "href": "/attendance", "active": True}]
    return render_page("출퇴관리", "attendance", content, quick)
