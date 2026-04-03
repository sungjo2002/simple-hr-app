
from html import escape
from urllib.parse import urlencode

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
    ui_text,
)

home_bp = Blueprint("home", __name__)

STATUS_LABELS = {
    "all": "전체",
    "before_work": "출근전",
    "working": "근무중",
    "completed": "퇴근완료",
    "hospital": "병원",
    "absent": "결근",
}


def _home_url(
    current_date: str,
    client_company_id: int | None,
    employee_keyword: str,
    selected_employee_id: int | None,
    row_limit: int,
    status_filter: str,
) -> str:
    query = {
        "work_date": current_date,
        "client_company_id": client_company_id or "",
        "employee_keyword": employee_keyword,
        "selected_employee_id": selected_employee_id or "",
        "row_limit": row_limit,
        "status_filter": status_filter,
    }
    return f"/?{urlencode(query)}"


@home_bp.route("/")
def home() -> str:
    current_date = request.args.get("work_date", today_str())
    client_company_raw = request.args.get("client_company_id", "")
    client_company_id = int(client_company_raw) if client_company_raw.isdigit() else None
    employee_keyword = request.args.get("employee_keyword", "").strip()
    selected_employee_raw = request.args.get("selected_employee_id", "")
    selected_employee_id = int(selected_employee_raw) if selected_employee_raw.isdigit() else None
    row_limit_raw = request.args.get("row_limit", "10")
    row_limit = int(row_limit_raw) if row_limit_raw.isdigit() else 10
    if row_limit not in {5, 10, 15, 20, 30, 50}:
        row_limit = 10
    status_filter = request.args.get("status_filter", "all").strip()
    if status_filter not in {"", "all", "before_work", "working", "completed", "hospital", "absent"}:
        status_filter = "all"
    if not status_filter:
        status_filter = "all"

    all_employees = get_employees_by_client_company(client_company_id)

    total = len(all_employees)
    before_count = count_status_for_client_company(client_company_id, current_date, "before_work")
    working_count = count_status_for_client_company(client_company_id, current_date, "working")
    completed_count = count_status_for_client_company(client_company_id, current_date, "completed")
    hospital_count = count_status_for_client_company(client_company_id, current_date, "hospital")
    absent_count = count_status_for_client_company(client_company_id, current_date, "absent")

    filtered_employees = list(all_employees)

    if status_filter != "all":
        filtered_employees = [
            employee
            for employee in filtered_employees
            if get_display_status(employee.id, current_date) == status_filter
        ]

    if employee_keyword:
        lowered = employee_keyword.lower()
        filtered_employees = [employee for employee in filtered_employees if lowered in employee.name.lower()]

    selected_employee = None
    if selected_employee_id:
        candidate = get_employee(selected_employee_id)
        if candidate and (client_company_id is None or candidate.current_client_company_id == client_company_id):
            selected_employee = candidate

    visible_employees = filtered_employees[:row_limit]

    rows = ""
    for employee in visible_employees:
        row_style = ' style="background:#eff6ff;"' if selected_employee_id == employee.id else ""
        detail_href = _home_url(
            current_date=current_date,
            client_company_id=client_company_id,
            employee_keyword=employee_keyword,
            selected_employee_id=employee.id,
            row_limit=row_limit,
            status_filter=status_filter,
        )
        rows += f"""
        <tr{row_style}>
            <td>{employee.id}</td>
            <td><a class="js-keep-scroll" href="{detail_href}">{escape(employee.name)}</a></td>
            <td>{escape(employee.nationality or "-")}</td>
            <td>{escape(get_our_business_name(employee.our_business_id))}</td>
            <td>{escape(get_client_company_name(employee.current_client_company_id))}</td>
            <td>{escape(get_work_type_name(employee.work_type_id))}</td>
            <td>{status_badge(get_display_status(employee.id, current_date))}</td>
        </tr>
        """
    if not rows:
        rows = '<tr><td colspan="7">조건에 맞는 인력이 없습니다.</td></tr>'

    client_options = ['<option value="">전체 거래처</option>']
    for client in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if client_company_id == client.id else ""
        client_options.append(f'<option value="{client.id}" {selected}>{escape(client.name)}</option>')

    matched_employees = list(filtered_employees)
    if selected_employee is None and matched_employees:
        selected_employee = matched_employees[0]
        selected_employee_id = selected_employee.id
    elif selected_employee is not None and not any(employee.id == selected_employee.id for employee in matched_employees):
        selected_employee = matched_employees[0] if matched_employees else None
        selected_employee_id = selected_employee.id if selected_employee else None
    else:
        selected_employee_id = selected_employee.id if selected_employee else None

    scorecard = calculate_employee_scorecard(selected_employee_id) if selected_employee_id else None

    score_html = '<div class="empty-score">왼쪽에서 사원을 검색하거나 표의 이름을 누르면 인력 지표가 이곳에 표시됩니다.</div>'
    if selected_employee and scorecard:
        work_score = scorecard["work_score"]
        sincerity_score = scorecard["sincerity_score"]
        stability_score = scorecard["stability_score"]
        average_score = round((work_score + sincerity_score + stability_score) / 3)
        score_html = f"""
        <div class="score-box">
            <div class="score-header">
                <div>
                    <h3 class="score-title">{escape(selected_employee.name)} 인력지표</h3>
                    <div class="muted">{escape(selected_employee.nationality or "-")} · {escape(get_client_company_name(selected_employee.current_client_company_id))}</div>
                </div>
                <div class="score-chip">기록 {scorecard["record_count"]}건</div>
            </div>
            <div class="score-summary">
                <div class="score-summary-card">
                    <div class="score-summary-label">종합 점수</div>
                    <div class="score-summary-value">{average_score}</div>
                </div>
                <div class="score-summary-card">
                    <div class="score-summary-label">현재 상태</div>
                    <div class="score-summary-value" style="font-size:18px;">{STATUS_LABELS.get(get_display_status(selected_employee.id, current_date), "확인중")}</div>
                </div>
                <div class="score-summary-card">
                    <div class="score-summary-label">배치 사업장</div>
                    <div class="score-summary-value" style="font-size:18px;">{escape(get_our_business_name(selected_employee.our_business_id))}</div>
                </div>
            </div>
            <div class="score-row"><div class="score-label">업무 수행</div><div class="bar-wrap"><div class="bar-fill {score_bar_class(work_score)}" style="width:{work_score}%;"></div></div><div class="score-num">{work_score}</div></div>
            <div class="score-row"><div class="score-label">성실도</div><div class="bar-wrap"><div class="bar-fill {score_bar_class(sincerity_score)}" style="width:{sincerity_score}%;"></div></div><div class="score-num">{sincerity_score}</div></div>
            <div class="score-row"><div class="score-label">안정성</div><div class="bar-wrap"><div class="bar-fill {score_bar_class(stability_score)}" style="width:{stability_score}%;"></div></div><div class="score-num">{stability_score}</div></div>
            <div class="legend-list">
                <div class="legend-item">
                    <div class="legend-title">거래처</div>
                    <div class="legend-value">{escape(get_client_company_name(selected_employee.current_client_company_id))}</div>
                </div>
                <div class="legend-item">
                    <div class="legend-title">근무 타입</div>
                    <div class="legend-value">{escape(get_work_type_name(selected_employee.work_type_id))}</div>
                </div>
            </div>
        </div>
        """

    table_max_height = max(380, min(1120, 100 + row_limit * 54))
    visible_count = len(filtered_employees)
    shown_count = len(visible_employees)
    filter_title = STATUS_LABELS.get(status_filter, "전체")

    card_defs = [
        ("all", ui_text("home_card_total", "전체"), total, "조회 대상 전체 인원"),
        ("before_work", ui_text("home_card_before_work", "출근전"), before_count, "아직 출근 처리 전"),
        ("working", ui_text("home_card_working", "근무중"), working_count, "현재 근무 진행중"),
        ("completed", ui_text("home_card_completed", "퇴근완료"), completed_count, "당일 근무 종료"),
        ("hospital", ui_text("home_card_hospital", "병원"), hospital_count, "병원/진료 처리"),
        ("absent", ui_text("home_card_absent", "결근"), absent_count, "결근 처리 인원"),
    ]
    cards_html = []
    for key, label, value, note in card_defs:
        cards_html.append(
            f"""
            <a class="card card-link js-keep-scroll {'active' if status_filter == key else ''}" href="{_home_url(current_date, client_company_id, employee_keyword, None, row_limit, key)}">
                <div class="label">{label}</div>
                <div class="value">{value}</div>
                <div class="value-sub">{note}</div>
            </a>
            """
        )

    hero_metrics = f"""
    <div class="hero-metrics">
        <div class="hero-metric">
            <div class="hero-metric-label">오늘 조회일</div>
            <div class="hero-metric-value">{current_date}</div>
            <div class="hero-metric-note">현재 기준일</div>
        </div>
        <div class="hero-metric">
            <div class="hero-metric-label">선택 거래처</div>
            <div class="hero-metric-value">{escape(get_client_company_name(client_company_id)) if client_company_id else '전체'}</div>
            <div class="hero-metric-note">범위 필터</div>
        </div>
        <div class="hero-metric">
            <div class="hero-metric-label">현재 상태 필터</div>
            <div class="hero-metric-value">{filter_title}</div>
            <div class="hero-metric-note">아래 목록과 연동</div>
        </div>
        <div class="hero-metric">
            <div class="hero-metric-label">표시 인원</div>
            <div class="hero-metric-value">{shown_count} / {visible_count}</div>
            <div class="hero-metric-note">행 제한 반영</div>
        </div>
    </div>
    """

    content = f"""
    <div class="hero-panel" id="dashboard-top">
        <div class="hero-grid">
            <div>
                <h2 class="hero-title">{escape(ui_text("home_hero_title", "오늘의 인력 운영 상황을 한 번에 확인하세요"))}</h2>
                <p class="hero-copy">{escape(ui_text("home_hero_description", "상태 카드와 검색, 거래처 필터를 한 흐름으로 확인할 수 있습니다."))}</p>
            </div>
            {hero_metrics}
        </div>
    </div>

    <div class="notice">{escape(ui_text("home_notice_text", "홈 화면은 요약 중심으로, 근태·직원·기록 기능은 상단 메뉴에서 분리해 중복 느낌을 줄였습니다."))}</div>

    <form method="get" class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <div class="form-grid">
                <div><label>조회 날짜</label><input type="date" name="work_date" value="{current_date}"></div>
                <div><label>거래처 선택</label><select name="client_company_id">{"".join(client_options)}</select></div>
                <div><label>표시 행 수</label>
                    <select name="row_limit">
                        <option value="5" {"selected" if row_limit == 5 else ""}>5명</option>
                        <option value="10" {"selected" if row_limit == 10 else ""}>10명</option>
                        <option value="15" {"selected" if row_limit == 15 else ""}>15명</option>
                        <option value="20" {"selected" if row_limit == 20 else ""}>20명</option>
                        <option value="30" {"selected" if row_limit == 30 else ""}>30명</option>
                        <option value="50" {"selected" if row_limit == 50 else ""}>50명</option>
                    </select>
                </div>
            </div>
            <div class="actions">
                <button class="btn btn-primary" type="submit">{escape(ui_text("home_filter_apply_button", "조회 적용"))}</button>
                <a class="btn btn-white" href="/">{escape(ui_text("home_filter_reset_button", "전체 초기화"))}</a>
            </div>
        </div>
    </form>

    <div class="cards">
        {"".join(cards_html)}
    </div>

    <div class="home-grid">
        <div>
            <div class="panel" style="margin-bottom:18px;">
                <div class="panel-head"><div><h2>{escape(ui_text("home_search_panel_title", "사원검색"))}</h2><p>{escape(ui_text("home_search_panel_description", "이름 검색과 상세 선택 흐름을 간단하게 유지합니다."))}</p></div></div>
                <div class="panel-body">
                    <form method="get">
                        <input type="hidden" name="work_date" value="{current_date}">
                        <input type="hidden" name="client_company_id" value="{client_company_id or ''}">
                        <input type="hidden" name="row_limit" value="{row_limit}">
                        <input type="hidden" name="status_filter" value="{status_filter}">
                        <label>사원 이름 검색</label>
                        <input name="employee_keyword" value="{escape(employee_keyword)}" placeholder="예: 성조, 응우옌">
                        <div class="actions">
                            <button class="btn btn-primary" type="submit">검색</button>
                            <a class="btn btn-white" href="{_home_url(current_date, client_company_id, '', None, row_limit, status_filter)}">검색 초기화</a>
                        </div>
                    </form>
                </div>
            </div>
            <div class="panel">
                <div class="panel-head"><div><h2>인력 지표</h2><p>선택 인력의 업무 수행, 성실도, 안정성을 시각화</p></div></div>
                <div class="panel-body">{score_html}</div>
            </div>
        </div>
        <div class="panel">
            <div class="panel-head">
                <div>
                    <h2>{filter_title} 인력현황</h2>
                    <p>{current_date} 기준 · 카드, 검색, 거래처 필터가 동일하게 반영됩니다.</p>
                </div>
                <div class="panel-head-actions">
                    <form method="get" class="head-control">
                        <input type="hidden" name="work_date" value="{current_date}">
                        <input type="hidden" name="client_company_id" value="{client_company_id or ''}">
                        <input type="hidden" name="employee_keyword" value="{escape(employee_keyword)}">
                        <input type="hidden" name="selected_employee_id" value="{selected_employee_id or ''}">
                        <input type="hidden" name="status_filter" value="{status_filter}">
                        <label for="row_limit_top" style="margin:0;">인원수 제한</label>
                        <select id="row_limit_top" name="row_limit" onchange="this.form.submit()">
                            <option value="5" {"selected" if row_limit == 5 else ""}>5명</option>
                            <option value="10" {"selected" if row_limit == 10 else ""}>10명</option>
                            <option value="15" {"selected" if row_limit == 15 else ""}>15명</option>
                            <option value="20" {"selected" if row_limit == 20 else ""}>20명</option>
                            <option value="30" {"selected" if row_limit == 30 else ""}>30명</option>
                            <option value="50" {"selected" if row_limit == 50 else ""}>50명</option>
                        </select>
                    </form>
                    <div class="head-count">{filter_title} 상태 · 표시 {shown_count}명 / 전체 {visible_count}명</div>
                </div>
            </div>
            <div class="panel-body">
                <div class="table-scroll js-drag-scroll" style="max-height:{table_max_height}px;">
                    <table>
                        <thead><tr><th>번호</th><th>이름</th><th>국적</th><th>사업자</th><th>거래처</th><th>근무타입</th><th>상태</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                <div class="muted" style="margin-top:10px;">표 안에서 마우스로 끌어서 스크롤할 수 있습니다.</div>
            </div>
        </div>
    </div>
    """
    return render_page(ui_text("home_page_title", "홈"), "home", content)
