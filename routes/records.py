from calendar import monthrange
from datetime import date

from flask import Blueprint, request

from models import AttendanceRecord, ClientCompany
from utils import get_client_company_name, get_day_mark, get_employee, get_employees_by_client_company, get_month_attendance_map, get_our_business_name, get_work_type_name, month_str_default, parse_date, parse_month, render_page, status_badge

records_bp = Blueprint("records", __name__)


@records_bp.route("/records")
def records_page() -> str:
    selected_client_raw = request.args.get("client_company_id", "")
    selected_client_company_id = int(selected_client_raw) if selected_client_raw.isdigit() else None
    selected_month = request.args.get("month", month_str_default())
    selected_tab = request.args.get("tab", "all")
    year, month = parse_month(selected_month)

    client_filter_options = ['<option value="">전체 거래처</option>']
    for client in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if selected_client_company_id == client.id else ""
        client_filter_options.append(f'<option value="{client.id}" {selected}>{client.name}</option>')
    filter_form = f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <input type="hidden" name="tab" value="{selected_tab}">
                <div><label>거래처 필터</label><select name="client_company_id">{"".join(client_filter_options)}</select></div>
                <div><label>월 선택</label><input type="month" name="month" value="{selected_month}"></div>
                <div><button class="btn btn-white" type="submit">조회</button></div>
            </form>
        </div>
    </div>
    """

    if selected_tab == "monthly":
        days_in_month = monthrange(year, month)[1]
        employees_for_grid = get_employees_by_client_company(selected_client_company_id)
        header_days = "".join(f"<th>{day}</th>" for day in range(1, days_in_month + 1))
        month_rows = ""
        for employee in employees_for_grid:
            monthly_map = get_month_attendance_map(employee.id, year, month)
            present_cnt = hospital_cnt = absent_cnt = vacation_cnt = off_cnt = 0
            month_rows += f'<tr><td class="name-col"><a href="/employees/{employee.id}">{employee.name}</a></td><td class="nation-col">{employee.nationality}</td>'
            for day_num in range(1, days_in_month + 1):
                record = monthly_map.get(day_num)
                day_mark = get_day_mark(record)
                weekday = date(year, month, day_num).weekday()
                if day_mark == "O":
                    present_cnt += 1
                    month_rows += "<td>O</td>"
                elif day_mark == "H":
                    hospital_cnt += 1
                    month_rows += "<td>H</td>"
                elif day_mark == "X":
                    absent_cnt += 1
                    month_rows += "<td>X</td>"
                elif day_mark == "V":
                    vacation_cnt += 1
                    month_rows += "<td>V</td>"
                else:
                    if weekday >= 5:
                        off_cnt += 1
                        month_rows += "<td>-</td>"
                    else:
                        month_rows += "<td></td>"
            month_rows += f"<td>{present_cnt}</td><td>{hospital_cnt}</td><td>{vacation_cnt}</td><td>{absent_cnt}</td><td>{off_cnt}</td></tr>"
        tab_content = f"""
        <div class="panel">
            <div class="panel-head"><h2>월별 출석현황</h2><p>O=출근 / H=병원 / V=휴가 / X=결근 / -=휴무</p></div>
            <div class="panel-body month-grid">
                <table>
                    <thead><tr><th class="name-col">이름</th><th class="nation-col">국적</th>{header_days}<th>출근</th><th>병원</th><th>휴가</th><th>결근</th><th>휴무</th></tr></thead>
                    <tbody>{month_rows or '<tr><td colspan="100">인력이 없습니다.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        """
    else:
        query = AttendanceRecord.query
        if selected_client_company_id is not None:
            query = query.filter_by(client_company_id=selected_client_company_id)
        filtered_records = [record for record in query.order_by(AttendanceRecord.work_date.desc(), AttendanceRecord.employee_id.asc()).all() if parse_date(record.work_date).year == year and parse_date(record.work_date).month == month]
        record_rows = ""
        for index, record in enumerate(filtered_records, start=1):
            employee = get_employee(record.employee_id)
            if not employee:
                continue
            record_rows += f"""
            <tr>
                <td>{index}</td>
                <td>{record.work_date}</td>
                <td><a href="/employees/{employee.id}">{employee.name}</a></td>
                <td>{employee.nationality}</td>
                <td>{get_our_business_name(record.our_business_id)}</td>
                <td>{get_client_company_name(record.client_company_id)}</td>
                <td>{get_work_type_name(record.work_type_id)}</td>
                <td>{record.check_in_at or '-'}</td>
                <td>{record.check_out_at or '-'}</td>
                <td>{status_badge(record.status)}</td>
                <td>{record.reason or '-'}</td>
            </tr>
            """
        tab_content = f"""
        <div class="panel">
            <div class="panel-head"><h2>전체 출퇴기록</h2><p>{selected_month} 기준 실제 데이터 조회</p></div>
            <div class="panel-body">
                <table>
                    <thead><tr><th>번호</th><th>날짜</th><th>이름</th><th>국적</th><th>사업자</th><th>거래처</th><th>근무타입</th><th>출근</th><th>퇴근</th><th>상태</th><th>사유</th></tr></thead>
                    <tbody>{record_rows or '<tr><td colspan="11">기록이 없습니다.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        """
    content = f"{filter_form}{tab_content}"
    quick = [
        {"label": "근태조회", "href": "/records?tab=all", "active": selected_tab == "all"},
        {"label": "월별현황", "href": "/records?tab=monthly", "active": selected_tab == "monthly"},
    ]
    return render_page("기록조회", "records", content, quick)
