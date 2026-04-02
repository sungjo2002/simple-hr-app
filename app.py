```python
@app.route("/records")
def records_page() -> str:
    selected_company_raw = request.args.get("company_id", "")
    selected_company_id = int(selected_company_raw) if selected_company_raw.isdigit() else None
    selected_month = request.args.get("month", month_str_default())
    selected_tab = request.args.get("tab", "all")
    year, month = parse_month(selected_month)

    company_filter_options = ['<option value="">전체 회사</option>']
    for company in companies:
        selected = "selected" if selected_company_id == company["id"] else ""
        company_filter_options.append(
            f'<option value="{company["id"]}" {selected}>{company["name"]}</option>'
        )

    subtabs = f"""
    <div class="subtabs">
        <a class="{'active' if selected_tab == 'all' else ''}" href="/records?tab=all&company_id={selected_company_id or ''}&month={selected_month}">전체 출퇴기록</a>
        <a class="{'active' if selected_tab == 'monthly' else ''}" href="/records?tab=monthly&company_id={selected_company_id or ''}&month={selected_month}">월별 출석현황</a>
    </div>
    """

    filter_form = f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <input type="hidden" name="tab" value="{selected_tab}">
                <div>
                    <label>회사 필터</label>
                    <select name="company_id">{"".join(company_filter_options)}</select>
                </div>
                <div>
                    <label>월 선택</label>
                    <input type="month" name="month" value="{selected_month}">
                </div>
                <div>
                    <button class="btn btn-white" type="submit">조회</button>
                </div>
            </form>
        </div>
    </div>
    """

    if selected_tab == "monthly":
        days_in_month = monthrange(year, month)[1]
        employees_for_grid = get_employees_by_company(selected_company_id)

        header_days = "".join(f"<th>{day}</th>" for day in range(1, days_in_month + 1))
        month_rows = ""

        for employee in employees_for_grid:
            monthly_map = get_month_attendance_map(employee["id"], year, month)
            present_cnt = 0
            hospital_cnt = 0
            absent_cnt = 0
            vacation_cnt = 0
            off_cnt = 0

            month_rows += (
                f'<tr><td class="name-col"><a href="/employees/{employee["id"]}">{employee["name"]}</a></td>'
                f'<td class="nation-col">{employee["nationality"]}</td>'
            )

            for day in range(1, days_in_month + 1):
                record = monthly_map.get(day)
                day_mark = get_day_mark(record)
                weekday = datetime(year, month, day).weekday()

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

            month_rows += (
                f"<td>{present_cnt}</td>"
                f"<td>{hospital_cnt}</td>"
                f"<td>{vacation_cnt}</td>"
                f"<td>{absent_cnt}</td>"
                f"<td>{off_cnt}</td></tr>"
            )

        tab_content = f"""
        <div class="panel">
            <div class="panel-head">
                <h2>월별 출석현황</h2>
                <p>O=출근 / H=병원 / V=휴가 / X=결근 / -=휴무</p>
            </div>
            <div class="panel-body month-grid">
                <table>
                    <thead>
                        <tr>
                            <th class="name-col">이름</th>
                            <th class="nation-col">국적</th>
                            {header_days}
                            <th>출근</th>
                            <th>병원</th>
                            <th>휴가</th>
                            <th>결근</th>
                            <th>휴무</th>
                        </tr>
                    </thead>
                    <tbody>{month_rows or '<tr><td colspan="100">사원이 없습니다.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        """
    else:
        filtered_records = []
        for record in attendance_records:
            dt = parse_date(record["work_date"])
            if dt.year != year or dt.month != month:
                continue
            if selected_company_id and record["company_id"] != selected_company_id:
                continue
            filtered_records.append(record)

        filtered_records.sort(
            key=lambda item: (item["work_date"], item["employee_id"]),
            reverse=True,
        )

        record_rows = ""
        for index, record in enumerate(filtered_records, start=1):
            employee = get_employee(record["employee_id"])
            if not employee:
                continue

            record_rows += f"""
            <tr>
                <td>{index}</td>
                <td>{record["work_date"]}</td>
                <td><a href="/employees/{employee["id"]}">{employee["name"]}</a></td>
                <td>{employee["nationality"]}</td>
                <td>{get_company_name(record["company_id"])}</td>
                <td>{get_work_type_name(record["work_type_id"])}</td>
                <td>{record["check_in_at"] or '-'}</td>
                <td>{record["check_out_at"] or '-'}</td>
                <td>{status_badge(record["status"])}</td>
                <td>{record["reason"] or '-'}</td>
            </tr>
            """

        tab_content = f"""
        <div class="panel">
            <div class="panel-head">
                <h2>전체 출퇴기록</h2>
                <p>{selected_month} 기준 실제 데이터 조회</p>
            </div>
            <div class="panel-body">
                <table>
                    <thead>
                        <tr>
                            <th>번호</th>
                            <th>날짜</th>
                            <th>사원명</th>
                            <th>국적</th>
                            <th>회사</th>
                            <th>근무타입</th>
                            <th>출근</th>
                            <th>퇴근</th>
                            <th>상태</th>
                            <th>사유</th>
                        </tr>
                    </thead>
                    <tbody>{record_rows or '<tr><td colspan="10">기록이 없습니다.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        """

    content = f"""
    {subtabs}
    {filter_form}
    {tab_content}
    """

    quick = [
        {"label": "전체 출퇴기록", "href": "/records?tab=all"},
        {"label": "월별 출석현황", "href": "/records?tab=monthly"},
    ]
    return render_page("기록조회", "records", content, quick)
```

**a.** `attendance_records` 월 샘플 데이터도 같이 만들어서 월별 출석현황을 더 자연스럽게 채우기
**b.** 회사/사원/월 필터를 상단 고정 검색바 형태로 정리하기
