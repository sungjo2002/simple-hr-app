from flask import Blueprint, redirect, request, url_for

from models import ClientCompany
from utils import get_attendance_record, get_client_company_name, get_employees_by_client_company, get_our_business_name, get_work_type_name, render_page, status_badge, today_str, update_attendance

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

    employee_list = get_employees_by_client_company(selected_client_company_id)
    client_filter_options = ['<option value="">전체 거래처</option>']
    for client in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if selected_client_company_id == client.id else ""
        client_filter_options.append(f'<option value="{client.id}" {selected}>{client.name}</option>')

    employee_options = ""
    for employee in employee_list:
        employee_options += f'<option value="{employee.id}">{employee.name} / {employee.nationality} / {get_client_company_name(employee.current_client_company_id)} / {get_work_type_name(employee.work_type_id)}</option>'

    rows = ""
    for employee in employee_list:
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

    content = f"""
    <div class="content-grid">
        <div class="panel">
            <div class="panel-head"><h2>오늘 출퇴현황</h2><p>선택 날짜: <strong>{selected_date}</strong></p></div>
            <div class="panel-body">
                <form method="get" class="actions" style="margin-top:0; margin-bottom:16px;">
                    <div><label>날짜 선택</label><input type="date" name="work_date" value="{selected_date}"></div>
                    <div><label>거래처 선택</label><select name="client_company_id">{"".join(client_filter_options)}</select></div>
                    <div><button class="btn btn-white" type="submit">조회</button></div>
                    <div><a class="btn btn-white" href="/attendance?work_date={today_str()}">오늘</a></div>
                </form>
                <table>
                    <thead><tr><th>이름</th><th>국적</th><th>사업자</th><th>거래처</th><th>근무타입</th><th>상태</th><th>출근</th><th>퇴근</th><th>사유</th></tr></thead>
                    <tbody>{rows or '<tr><td colspan="9">인력이 없습니다.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        <div class="panel">
            <div class="panel-head"><h2>출근 / 퇴근 / 병원 / 휴가 / 결근 처리</h2><p>1일 1레코드 갱신 방식</p></div>
            <div class="panel-body">
                <form method="post">
                    <input type="hidden" name="client_company_id" value="{selected_client_company_id or ''}">
                    <label>인력 선택</label><select name="employee_id" required>{employee_options}</select>
                    <label>날짜</label><input type="date" name="work_date" value="{selected_date}" required>
                    <label>처리 구분</label>
                    <select name="action_type">
                        <option value="checkin">출근처리</option><option value="checkout">퇴근처리</option><option value="hospital">병원처리</option><option value="vacation">휴가처리</option><option value="absent">결근처리</option><option value="reset">초기화</option>
                    </select>
                    <div class="form-grid" style="margin-top:14px;">
                        <div><label>연장분(분)</label><input type="number" name="overtime_minutes" value="0"></div>
                        <div><label>야간분(분)</label><input type="number" name="night_minutes" value="0"></div>
                    </div>
                    <label style="margin-top:14px;">사유 / 메모</label><input name="reason" placeholder="병원 / 휴가 / 결근 시 메모 입력">
                    <div class="actions"><button class="btn btn-green" type="submit">저장</button></div>
                </form>
            </div>
        </div>
    </div>
    """
    quick = [{"label": "오늘근태", "href": "/attendance"}, {"label": "근태조회", "href": "/records?tab=all"}, {"label": "월별현황", "href": "/records?tab=monthly"}]
    return render_page("근태관리", "attendance", content, quick)
