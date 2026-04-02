from flask import Blueprint, request

from models import ClientCompany
from utils import (
    calculate_employee_scorecard,
    count_status_for_client_company,
    get_client_company_name,
    get_display_status,
    get_employee,
    get_employees_by_client_company,
    get_our_business_name,
    get_work_type_name,
    render_page,
    score_bar_class,
    status_badge,
    today_str,
)

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def home() -> str:
    current_date = request.args.get("work_date", today_str())
    client_company_raw = request.args.get("client_company_id", "")
    client_company_id = int(client_company_raw) if client_company_raw.isdigit() else None
    employee_keyword = request.args.get("employee_keyword", "").strip()
    selected_employee_raw = request.args.get("selected_employee_id", "")
    selected_employee_id = int(selected_employee_raw) if selected_employee_raw.isdigit() else None

    filtered_employees = get_employees_by_client_company(client_company_id)

    total = len(filtered_employees)
    before_count = count_status_for_client_company(client_company_id, current_date, "before_work")
    working_count = count_status_for_client_company(client_company_id, current_date, "working")
    completed_count = count_status_for_client_company(client_company_id, current_date, "completed")
    hospital_count = count_status_for_client_company(client_company_id, current_date, "hospital")
    absent_count = count_status_for_client_company(client_company_id, current_date, "absent")

    if employee_keyword:
        lowered = employee_keyword.lower()
        filtered_employees = [e for e in filtered_employees if lowered in e.name.lower()]

    if selected_employee_id:
        selected_employee = get_employee(selected_employee_id)
        if selected_employee and (client_company_id is None or selected_employee.current_client_company_id == client_company_id):
            filtered_employees = [selected_employee]

    rows = ""
    for employee in filtered_employees:
        row_style = ' style="background:#eff6ff;"' if selected_employee_id == employee.id else ""
        rows += f"""
        <tr{row_style}>
            <td>{employee.id}</td>
            <td><a href="/?work_date={current_date}&client_company_id={client_company_id or ''}&employee_keyword={employee_keyword}&selected_employee_id={employee.id}">{employee.name}</a></td>
            <td>{employee.nationality}</td>
            <td>{get_our_business_name(employee.our_business_id)}</td>
            <td>{get_client_company_name(employee.current_client_company_id)}</td>
            <td>{get_work_type_name(employee.work_type_id)}</td>
            <td>{status_badge(get_display_status(employee.id, current_date))}</td>
        </tr>
        """
    if not rows:
        rows = '<tr><td colspan="7">인력이 없습니다.</td></tr>'

    client_options = ['<option value="">전체 거래처</option>']
    for client in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if client_company_id == client.id else ""
        client_options.append(f'<option value="{client.id}" {selected}>{client.name}</option>')

    matched_employees = get_employees_by_client_company(client_company_id)
    if employee_keyword:
        lowered = employee_keyword.lower()
        matched_employees = [e for e in matched_employees if lowered in e.name.lower()]
    if selected_employee_id is None and matched_employees:
        selected_employee_id = matched_employees[0].id

    selected_employee = get_employee(selected_employee_id) if selected_employee_id else None
    scorecard = calculate_employee_scorecard(selected_employee_id) if selected_employee_id else None

    score_html = '<div class="muted">사원을 검색하면 지표가 표시됩니다.</div>'
    if selected_employee and scorecard:
        work_score = scorecard["work_score"]
        sincerity_score = scorecard["sincerity_score"]
        stability_score = scorecard["stability_score"]
        score_html = f"""
        <div class="score-box">
            <div class="score-row"><div class="score-label">일 잘함</div><div class="bar-wrap"><div class="bar-fill {score_bar_class(work_score)}" style="width:{work_score}%;"></div></div><div class="score-num">{work_score}</div></div>
            <div class="score-row"><div class="score-label">성실도</div><div class="bar-wrap"><div class="bar-fill {score_bar_class(sincerity_score)}" style="width:{sincerity_score}%;"></div></div><div class="score-num">{sincerity_score}</div></div>
            <div class="score-row"><div class="score-label">안정성</div><div class="bar-wrap"><div class="bar-fill {score_bar_class(stability_score)}" style="width:{stability_score}%;"></div></div><div class="score-num">{stability_score}</div></div>
            <div class="muted" style="margin-top:4px;">선택 인력: {selected_employee.name} / 기록 {scorecard["record_count"]}건</div>
        </div>
        """

    content = f"""
    <div class="notice">데이터는 SQLite DB 파일에 저장됩니다. 앱을 다시 켜도 유지됩니다.</div>
    <form method="get" class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <div class="form-grid">
                <div><label>조회 날짜</label><input type="date" name="work_date" value="{current_date}"></div>
                <div><label>거래처 선택</label><select name="client_company_id">{"".join(client_options)}</select></div>
            </div>
            <div class="actions">
                <button class="btn btn-white" type="submit">조회</button>
                <a class="btn btn-white" href="/">초기화</a>
            </div>
        </div>
    </form>
    <div class="cards">
        <div class="card"><div class="label">전체 인력</div><div class="value">{total}</div></div>
        <div class="card"><div class="label">출근전</div><div class="value">{before_count}</div></div>
        <div class="card"><div class="label">근무중</div><div class="value">{working_count}</div></div>
        <div class="card"><div class="label">퇴근완료</div><div class="value">{completed_count}</div></div>
        <div class="card"><div class="label">병원</div><div class="value">{hospital_count}</div></div>
        <div class="card"><div class="label">결근</div><div class="value">{absent_count}</div></div>
    </div>
    <div class="home-grid">
        <div>
            <div class="panel" style="margin-bottom:18px;">
                <div class="panel-head"><h2>사원검색</h2><p>검색 결과와 인력현황 연동</p></div>
                <div class="panel-body">
                    <form method="get">
                        <input type="hidden" name="work_date" value="{current_date}">
                        <input type="hidden" name="client_company_id" value="{client_company_id or ''}">
                        <label>사원 이름 검색</label>
                        <input name="employee_keyword" value="{employee_keyword}" placeholder="예: 성조, 응우옌">
                        <div class="actions">
                            <button class="btn btn-primary" type="submit">검색</button>
                            <a class="btn btn-white" href="/?work_date={current_date}&client_company_id={client_company_id or ''}">초기화</a>
                        </div>
                    </form>
                </div>
            </div>
            <div class="panel">
                <div class="panel-head"><h2>인력 지표</h2><p>가로 그래프</p></div>
                <div class="panel-body">{score_html}</div>
            </div>
        </div>
        <div class="panel">
            <div class="panel-head"><h2>인력현황</h2><p>{current_date} 기준</p></div>
            <div class="panel-body">
                <table>
                    <thead><tr><th>번호</th><th>이름</th><th>국적</th><th>사업자</th><th>거래처</th><th>근무타입</th><th>상태</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_page("메인", "home", content)
