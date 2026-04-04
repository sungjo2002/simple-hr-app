from flask import Blueprint, flash, redirect, request, url_for

from models import AttendanceRecord, ClientCompany, Employee, EmployeeDocument, OurBusiness, db
from utils import (
    DOCUMENT_TYPE_LABELS,
    PAY_TYPE_LABELS,
    export_table,
    get_client_company_name,
    get_employee,
    get_employee_documents,
    get_employees_by_client_company,
    get_our_business_name,
    get_today_status,
    get_work_type_name,
    paginate_items,
    render_client_company_options,
    render_our_business_options,
    render_page,
    render_pagination,
    render_table_toolbar,
    render_work_type_options,
    sort_items,
    status_badge,
    today_str,
)

employees_bp = Blueprint("employees", __name__)

RETIREMENT_REASON_OPTIONS = [
    "계약만료",
    "자진퇴사",
    "사업장 종료",
    "건강 문제",
    "비자 이슈",
    "귀국 예정",
    "기타",
]


def _employee_status_label(employee: Employee) -> str:
    return "재직" if employee.status == "active" else "퇴사"


def _employee_status_badge(employee: Employee) -> str:
    return status_badge(_employee_status_label(employee))


def _retirement_ready_label(employee: Employee) -> str:
    return "재연락 대상" if (employee.recontact_target or "N") == "Y" else "재연락 제외"


def _employee_action_forms(employee: Employee, compact: bool = False) -> str:
    gap = "6px" if compact else "8px"
    if employee.status == "active":
        retire_or_rehire = f'<a class="btn btn-white" href="/employees/{employee.id}/retire">퇴사처리</a>'
    else:
        retire_or_rehire = f'''
        <form method="post" action="/employees/{employee.id}/reactivate" onsubmit="return confirm('재입사 처리로 전환할까요?');" style="display:inline;">
            <button class="btn btn-primary" type="submit">재입사 처리</button>
        </form>
        '''
    return f'''
    <div class="actions" style="gap:{gap}; flex-wrap:wrap;">
        <a class="btn btn-white" href="/employees/{employee.id}/edit">수정</a>
        {retire_or_rehire}
        <form method="post" action="/employees/{employee.id}/delete" onsubmit="return confirm('직원을 삭제할까요? 근태/문서 기록이 있으면 삭제할 수 없습니다.');" style="display:inline;">
            <button class="btn btn-danger" type="submit">삭제</button>
        </form>
    </div>
    '''


@employees_bp.route("/employees")
def employees_page() -> str:
    client_company_raw = request.args.get("client_company_id", "")
    client_company_id = int(client_company_raw) if client_company_raw.isdigit() else None
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "id")
    direction = request.args.get("direction", "asc")
    page_raw = request.args.get("page", "1")
    export_format = request.args.get("export", "").strip().lower()
    page = int(page_raw) if page_raw.isdigit() else 1

    items = get_employees_by_client_company(client_company_id)
    if q:
        q_lower = q.lower()
        items = [
            employee for employee in items
            if q_lower in employee.name.lower()
            or q_lower in employee.nationality.lower()
            or q_lower in get_our_business_name(employee.our_business_id).lower()
            or q_lower in get_client_company_name(employee.current_client_company_id).lower()
            or q_lower in get_work_type_name(employee.work_type_id).lower()
            or q_lower in PAY_TYPE_LABELS.get(employee.pay_type, "-").lower()
            or q_lower in get_today_status(employee.id).lower()
            or q_lower in _employee_status_label(employee).lower()
            or q_lower in (employee.retirement_reason or "").lower()
            or q_lower in _retirement_ready_label(employee).lower()
        ]

    sort_funcs = {
        "id": lambda employee: employee.id,
        "name": lambda employee: employee.name.lower(),
        "nationality": lambda employee: employee.nationality.lower(),
        "our_business": lambda employee: get_our_business_name(employee.our_business_id).lower(),
        "client_company": lambda employee: get_client_company_name(employee.current_client_company_id).lower(),
        "work_type": lambda employee: get_work_type_name(employee.work_type_id).lower(),
        "pay_type": lambda employee: PAY_TYPE_LABELS.get(employee.pay_type, "-"),
        "status": lambda employee: _employee_status_label(employee),
        "today_status": lambda employee: get_today_status(employee.id),
        "retirement_date": lambda employee: employee.retirement_date or "",
        "next_contact_date": lambda employee: employee.next_contact_date or "",
    }
    items = sort_items(items, sort, sort_funcs, direction)

    export_headers = [
        "번호", "이름", "국적", "사업자", "거래처", "근무타입", "급여형태",
        "재직상태", "퇴사일", "재연락 대상", "다음 연락일", "오늘 상태"
    ]
    export_rows = [
        [
            employee.id,
            employee.name,
            employee.nationality,
            get_our_business_name(employee.our_business_id),
            get_client_company_name(employee.current_client_company_id),
            get_work_type_name(employee.work_type_id),
            PAY_TYPE_LABELS.get(employee.pay_type, "-"),
            _employee_status_label(employee),
            employee.retirement_date or "-",
            _retirement_ready_label(employee),
            employee.next_contact_date or "-",
            get_today_status(employee.id),
        ]
        for employee in items
    ]
    export_response = export_table("employees", "인력목록", export_headers, export_rows, export_format)
    if export_response:
        return export_response

    paged_items, total_count, total_pages = paginate_items(items, page, 10)
    rows = ""
    for employee in paged_items:
        rows += f'''
        <tr>
            <td>{employee.id}</td>
            <td><a href="/employees/{employee.id}">{employee.name}</a></td>
            <td>{employee.nationality}</td>
            <td>{get_our_business_name(employee.our_business_id)}</td>
            <td>{get_client_company_name(employee.current_client_company_id)}</td>
            <td>{get_work_type_name(employee.work_type_id)}</td>
            <td>{PAY_TYPE_LABELS.get(employee.pay_type, "-")}</td>
            <td>{_employee_status_badge(employee)}</td>
            <td>{employee.retirement_date or '-'}</td>
            <td>{status_badge(_retirement_ready_label(employee))}</td>
            <td>{employee.next_contact_date or '-'}</td>
            <td>{status_badge(get_today_status(employee.id))}</td>
            <td>{_employee_action_forms(employee, compact=True)}</td>
        </tr>
        '''

    filter_options = ['<option value="">전체 거래처</option>']
    for company in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if client_company_id == company.id else ""
        filter_options.append(f'<option value="{company.id}" {selected}>{company.name}</option>')

    toolbar = render_table_toolbar(
        base_path="/employees",
        current_params={"client_company_id": client_company_id or "", "q": q, "sort": sort, "direction": direction},
        search_placeholder="이름, 국적, 사업자, 거래처, 퇴사사유 검색",
        search_value=q,
        sort_options=[
            ("id", "번호"), ("name", "이름"), ("nationality", "국적"), ("our_business", "사업자"),
            ("client_company", "거래처"), ("work_type", "근무타입"), ("pay_type", "급여형태"),
            ("status", "재직상태"), ("retirement_date", "퇴사일"), ("next_contact_date", "다음 연락일"),
            ("today_status", "오늘 상태")
        ],
        current_sort=sort,
        current_direction=direction,
        create_href="/employees/new",
        create_label="+ 직원등록",
        reset_href="/employees",
        filter_html=f'''
        <div>
            <label>거래처 선택</label>
            <select name="client_company_id">{"".join(filter_options)}</select>
        </div>
        ''',
    )
    pagination = render_pagination(
        "/employees",
        {"client_company_id": client_company_id or "", "q": q, "sort": sort, "direction": direction},
        page,
        total_pages,
        total_count,
    )
    content = f'''
    <div class="panel">
        <div class="panel-head"><h2>직원목록</h2><p>배치 인력 조회 및 퇴사 대상 관리</p></div>
        <div class="panel-body">
            {toolbar}
            <table>
                <thead>
                    <tr>
                        <th>번호</th><th>이름</th><th>국적</th><th>사업자</th><th>거래처</th><th>근무타입</th><th>급여형태</th>
                        <th>재직상태</th><th>퇴사일</th><th>재연락 대상</th><th>다음 연락일</th><th>오늘 상태</th><th>관리</th>
                    </tr>
                </thead>
                <tbody>{rows or '<tr><td colspan="13">데이터가 없습니다.</td></tr>'}</tbody>
            </table>
            {pagination}
        </div>
    </div>
    '''
    quick = [{"label": "사원목록", "href": "/employees", "active": True}, {"label": "사원등록", "href": "/employees/new", "active": False}]
    return render_page("직원관리", "employees", content, quick)


@employees_bp.route("/employees/new", methods=["GET", "POST"])
def employee_new() -> str:
    businesses = OurBusiness.query.order_by(OurBusiness.id.asc()).all()
    if not businesses:
        return "먼저 사업자를 등록하세요.", 400

    selected_our_business_raw = request.values.get("our_business_id", str(businesses[0].id))
    selected_our_business_id = int(selected_our_business_raw) if selected_our_business_raw.isdigit() else businesses[0].id

    clients = ClientCompany.query.filter_by(our_business_id=selected_our_business_id).order_by(ClientCompany.id.asc()).all()
    if not clients:
        return "선택한 사업자의 거래처가 없습니다. 먼저 거래처를 등록하세요.", 400

    selected_client_raw = request.values.get("client_company_id", str(clients[0].id))
    selected_client_company_id = int(selected_client_raw) if selected_client_raw.isdigit() else clients[0].id

    if request.method == "POST":
        item = Employee(
            our_business_id=int(request.form["our_business_id"]),
            current_client_company_id=int(request.form["client_company_id"]),
            name=request.form["name"].strip(),
            nationality=request.form["nationality"].strip(),
            phone=request.form.get("phone", "").strip(),
            hire_date=request.form.get("hire_date", today_str()),
            status="active",
            retirement_date="",
            retirement_reason="",
            recontact_target="N",
            next_contact_date="",
            retirement_note="",
            work_type_id=int(request.form["work_type_id"]),
            pay_type=request.form.get("pay_type", "monthly"),
            created_at=today_str(),
            updated_at=today_str(),
        )
        db.session.add(item)
        db.session.commit()
        flash("직원이 등록되었습니다.", "success")
        return redirect(url_for("employees.employees_page"))

    business_options = render_our_business_options(selected_our_business_id)
    client_options = render_client_company_options(selected_client_company_id, selected_our_business_id)
    work_type_options = render_work_type_options(selected_client_company_id)

    content = f'''
    <div class="panel">
        <div class="panel-head"><h2>인력등록</h2><p>사업자와 거래처에 배치되는 인력 등록</p></div>
        <div class="panel-body">
            <form method="get" class="panel" style="box-shadow:none; border-radius:14px; margin-bottom:16px;">
                <div class="panel-body">
                    <div class="form-grid">
                        <div><label>사업자</label><select name="our_business_id" onchange="this.form.submit()">{business_options}</select></div>
                        <div><label>거래처</label><select name="client_company_id" onchange="this.form.submit()">{client_options}</select></div>
                    </div>
                </div>
            </form>
            <form method="post">
                <input type="hidden" name="our_business_id" value="{selected_our_business_id}">
                <input type="hidden" name="client_company_id" value="{selected_client_company_id}">
                <div class="form-grid">
                    <div><label>사업자</label><input value="{get_our_business_name(selected_our_business_id)}" disabled></div>
                    <div><label>거래처</label><input value="{get_client_company_name(selected_client_company_id)}" disabled></div>
                    <div><label>이름</label><input name="name" required></div>
                    <div><label>국적</label><input name="nationality" required></div>
                    <div><label>연락처</label><input name="phone"></div>
                    <div><label>입사일</label><input type="date" name="hire_date" value="{today_str()}"></div>
                    <div><label>근무타입</label><select name="work_type_id">{work_type_options}</select></div>
                    <div><label>급여형태</label><select name="pay_type"><option value="monthly">월급</option><option value="daily">일급</option><option value="hourly">시급</option></select></div>
                </div>
                <div class="actions"><button class="btn btn-primary" type="submit">저장</button><a class="btn btn-white" href="/employees">취소</a></div>
            </form>
        </div>
    </div>
    '''
    quick = [{"label": "사원목록", "href": "/employees", "active": False}, {"label": "사원등록", "href": "/employees/new", "active": True}]
    return render_page("직원등록", "employees", content, quick)


@employees_bp.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
def employee_edit(employee_id: int) -> str:
    employee = get_employee(employee_id)
    if not employee:
        return "인력을 찾을 수 없습니다.", 404

    selected_our_business_id = int(request.values.get("our_business_id", employee.our_business_id))
    selected_client_company_id = int(request.values.get("client_company_id", employee.current_client_company_id or 0))

    businesses = OurBusiness.query.order_by(OurBusiness.id.asc()).all()
    if not businesses:
        return "먼저 사업자를 등록하세요.", 400

    clients = ClientCompany.query.filter_by(our_business_id=selected_our_business_id).order_by(ClientCompany.id.asc()).all()
    if clients and selected_client_company_id == 0:
        selected_client_company_id = clients[0].id

    if request.method == "POST":
        employee.our_business_id = int(request.form["our_business_id"])
        employee.current_client_company_id = int(request.form["client_company_id"])
        employee.name = request.form["name"].strip()
        employee.nationality = request.form["nationality"].strip()
        employee.phone = request.form.get("phone", "").strip()
        employee.hire_date = request.form.get("hire_date", today_str())
        employee.work_type_id = int(request.form["work_type_id"])
        employee.pay_type = request.form.get("pay_type", "monthly")
        employee.updated_at = today_str()
        db.session.commit()
        flash("직원 정보가 수정되었습니다.", "success")
        return redirect(url_for("employees.employee_detail", employee_id=employee.id))

    business_options = render_our_business_options(selected_our_business_id)
    client_options = render_client_company_options(selected_client_company_id, selected_our_business_id)
    work_type_options = render_work_type_options(selected_client_company_id, employee.work_type_id)

    content = f'''
    <div class="panel">
        <div class="panel-head"><h2>직원수정</h2><p>{employee.name}</p></div>
        <div class="panel-body">
            <form method="get" class="panel" style="box-shadow:none; border-radius:14px; margin-bottom:16px;">
                <input type="hidden" name="name" value="{employee.name}">
                <div class="panel-body">
                    <div class="form-grid">
                        <div><label>사업자</label><select name="our_business_id" onchange="this.form.submit()">{business_options}</select></div>
                        <div><label>거래처</label><select name="client_company_id" onchange="this.form.submit()">{client_options}</select></div>
                    </div>
                </div>
            </form>
            <form method="post">
                <input type="hidden" name="our_business_id" value="{selected_our_business_id}">
                <input type="hidden" name="client_company_id" value="{selected_client_company_id}">
                <div class="form-grid">
                    <div><label>사업자</label><input value="{get_our_business_name(selected_our_business_id)}" disabled></div>
                    <div><label>거래처</label><input value="{get_client_company_name(selected_client_company_id)}" disabled></div>
                    <div><label>이름</label><input name="name" value="{employee.name}" required></div>
                    <div><label>국적</label><input name="nationality" value="{employee.nationality}" required></div>
                    <div><label>연락처</label><input name="phone" value="{employee.phone or ''}"></div>
                    <div><label>입사일</label><input type="date" name="hire_date" value="{employee.hire_date}"></div>
                    <div><label>근무타입</label><select name="work_type_id">{work_type_options}</select></div>
                    <div><label>급여형태</label><select name="pay_type"><option value="monthly" {'selected' if employee.pay_type == 'monthly' else ''}>월급</option><option value="daily" {'selected' if employee.pay_type == 'daily' else ''}>일급</option><option value="hourly" {'selected' if employee.pay_type == 'hourly' else ''}>시급</option></select></div>
                    <div><label>재직상태</label><input value="{_employee_status_label(employee)}" disabled></div>
                </div>
                <div class="actions"><button class="btn btn-primary" type="submit">수정 저장</button><a class="btn btn-white" href="/employees/{employee.id}">취소</a></div>
            </form>
        </div>
    </div>
    '''
    quick = [{"label": "사원목록", "href": "/employees", "active": False}, {"label": "직원수정", "href": f"/employees/{employee.id}/edit", "active": True}]
    return render_page("직원수정", "employees", content, quick)


@employees_bp.route("/employees/<int:employee_id>/retire", methods=["GET", "POST"])
def employee_retire(employee_id: int) -> str:
    employee = get_employee(employee_id)
    if not employee:
        return "인력을 찾을 수 없습니다.", 404

    if request.method == "POST":
        employee.status = "retired"
        employee.retirement_date = request.form.get("retirement_date", "").strip() or today_str()
        employee.retirement_reason = request.form.get("retirement_reason", "").strip()
        employee.recontact_target = "Y" if request.form.get("recontact_target", "N") == "Y" else "N"
        employee.next_contact_date = request.form.get("next_contact_date", "").strip()
        employee.retirement_note = request.form.get("retirement_note", "").strip()
        employee.updated_at = today_str()
        db.session.commit()
        flash("퇴사처리가 저장되었습니다. 재연락 대상 정보가 함께 관리됩니다.", "success")
        return redirect(url_for("employees.employee_detail", employee_id=employee.id))

    reason_options = ['<option value="">사유 선택</option>']
    for option in RETIREMENT_REASON_OPTIONS:
        selected = "selected" if employee.retirement_reason == option else ""
        reason_options.append(f'<option value="{option}" {selected}>{option}</option>')

    checked_yes = "checked" if (employee.recontact_target or "N") == "Y" else ""
    checked_no = "checked" if (employee.recontact_target or "N") != "Y" else ""

    content = f'''
    <div class="panel">
        <div class="panel-head"><h2>퇴사처리</h2><p>{employee.name} · 재연락 대상 여부까지 함께 관리</p></div>
        <div class="panel-body">
            <form method="post">
                <div class="form-grid">
                    <div><label>이름</label><input value="{employee.name}" disabled></div>
                    <div><label>거래처</label><input value="{get_client_company_name(employee.current_client_company_id)}" disabled></div>
                    <div><label>퇴사일</label><input type="date" name="retirement_date" value="{employee.retirement_date or today_str()}" required></div>
                    <div><label>퇴사사유</label><select name="retirement_reason" required>{''.join(reason_options)}</select></div>
                    <div>
                        <label>재연락 대상</label>
                        <div class="actions" style="gap:14px;">
                            <label style="display:flex; gap:6px; align-items:center;"><input type="radio" name="recontact_target" value="Y" {checked_yes}> 예</label>
                            <label style="display:flex; gap:6px; align-items:center;"><input type="radio" name="recontact_target" value="N" {checked_no}> 아니오</label>
                        </div>
                    </div>
                    <div><label>다음 연락일</label><input type="date" name="next_contact_date" value="{employee.next_contact_date or ''}"></div>
                    <div style="grid-column:1 / -1;"><label>메모</label><textarea name="retirement_note" rows="4" placeholder="재입사 가능 시기, 연락 포인트, 희망 근무지 등을 적어두세요.">{employee.retirement_note or ''}</textarea></div>
                </div>
                <div class="actions">
                    <button class="btn btn-primary" type="submit">퇴사처리 저장</button>
                    <a class="btn btn-white" href="/employees/{employee.id}">취소</a>
                </div>
            </form>
        </div>
    </div>
    '''
    quick = [{"label": "사원목록", "href": "/employees", "active": False}, {"label": "퇴사처리", "href": f"/employees/{employee.id}/retire", "active": True}]
    return render_page("퇴사처리", "employees", content, quick)


@employees_bp.route("/employees/<int:employee_id>/reactivate", methods=["POST"])
def employee_reactivate(employee_id: int):
    employee = get_employee(employee_id)
    if not employee:
        return "인력을 찾을 수 없습니다.", 404

    employee.status = "active"
    employee.updated_at = today_str()
    db.session.commit()
    flash("직원이 재입사 처리되어 재직 상태로 전환되었습니다.", "success")
    return redirect(request.referrer or url_for("employees.employee_detail", employee_id=employee_id))


@employees_bp.route("/employees/<int:employee_id>/delete", methods=["POST"])
def employee_delete(employee_id: int):
    employee = get_employee(employee_id)
    if not employee:
        return "인력을 찾을 수 없습니다.", 404

    attendance_count = AttendanceRecord.query.filter_by(employee_id=employee_id).count()
    document_count = EmployeeDocument.query.filter_by(employee_id=employee_id).count()
    if attendance_count or document_count:
        flash("근태 기록 또는 문서가 있어 직원을 삭제할 수 없습니다. 퇴사처리 후 관리해 주세요.", "error")
        return redirect(request.referrer or url_for("employees.employee_detail", employee_id=employee_id))

    db.session.delete(employee)
    db.session.commit()
    flash("직원이 삭제되었습니다.", "success")
    return redirect(url_for("employees.employees_page"))


@employees_bp.route("/employees/<int:employee_id>", methods=["GET", "POST"])
def employee_detail(employee_id: int) -> str:
    employee = get_employee(employee_id)
    if not employee:
        return "인력을 찾을 수 없습니다.", 404

    if request.method == "POST":
        file_name = request.form.get("file_name", "").strip() or "unnamed.pdf"
        doc = EmployeeDocument(
            employee_id=employee_id,
            document_type=request.form.get("document_type", "other"),
            file_name=file_name,
            file_path=f"/uploads/{file_name}",
            file_mime_type=request.form.get("file_mime_type", "application/pdf"),
            is_sensitive=request.form.get("is_sensitive", "Y") == "Y",
            uploaded_by="super_admin",
            created_at=today_str(),
        )
        db.session.add(doc)
        db.session.commit()
        flash("문서가 등록되었습니다.", "success")
        return redirect(url_for("employees.employee_detail", employee_id=employee_id))

    attendance_rows = ""
    employee_records = AttendanceRecord.query.filter_by(employee_id=employee_id).order_by(AttendanceRecord.work_date.desc()).all()
    for index, record in enumerate(employee_records, start=1):
        attendance_rows += f'''
        <tr>
            <td>{index}</td>
            <td>{record.work_date}</td>
            <td>{get_work_type_name(record.work_type_id)}</td>
            <td>{record.check_in_at or '-'}</td>
            <td>{record.check_out_at or '-'}</td>
            <td>{status_badge(record.status)}</td>
            <td>{record.reason or '-'}</td>
        </tr>
        '''

    document_rows = ""
    for index, document in enumerate(get_employee_documents(employee_id), start=1):
        document_rows += f'''
        <tr>
            <td>{index}</td>
            <td>{DOCUMENT_TYPE_LABELS.get(document.document_type, document.document_type)}</td>
            <td>{document.file_name}</td>
            <td>{document.file_mime_type}</td>
            <td>{'민감' if document.is_sensitive else '일반'}</td>
            <td>{document.created_at}</td>
        </tr>
        '''

    retirement_panel = ""
    if employee.status != "active" or employee.retirement_date or employee.retirement_reason or employee.retirement_note:
        retirement_panel = f'''
        <div class="panel" style="margin-bottom:18px;">
            <div class="panel-head"><h2>퇴사 / 재연락 관리</h2><p>재입사 가능 인력 추적 정보</p></div>
            <div class="panel-body">
                <table>
                    <tr><th style="width:220px;">퇴사일</th><td>{employee.retirement_date or '-'}</td></tr>
                    <tr><th>퇴사사유</th><td>{employee.retirement_reason or '-'}</td></tr>
                    <tr><th>재연락 대상</th><td>{status_badge(_retirement_ready_label(employee))}</td></tr>
                    <tr><th>다음 연락일</th><td>{employee.next_contact_date or '-'}</td></tr>
                    <tr><th>메모</th><td>{employee.retirement_note or '-'}</td></tr>
                </table>
            </div>
        </div>
        '''

    content = f'''
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-head"><h2>직원 관리 액션</h2><p>{employee.name}</p></div>
        <div class="panel-body">
            {_employee_action_forms(employee)}
        </div>
    </div>
    <div class="two-col">
        <div class="side-box" style="padding:14px;">
            <h3 style="margin:0 0 12px;">인력 사진</h3>
            <div class="photo-box">사진 등록 영역</div>
            <div class="actions"><button class="btn btn-primary" type="button">사진 등록</button><button class="btn btn-white" type="button">사진 변경</button></div>
        </div>
        <div>
            <div class="panel" style="margin-bottom:18px;">
                <div class="panel-head"><h2>인력상세</h2><p>기본정보 / 문서 / 출퇴근 기록</p></div>
                <div class="panel-body">
                    <table>
                        <tr><th style="width:220px;">이름</th><td>{employee.name}</td></tr>
                        <tr><th>국적</th><td>{employee.nationality}</td></tr>
                        <tr><th>사업자</th><td>{get_our_business_name(employee.our_business_id)}</td></tr>
                        <tr><th>거래처</th><td>{get_client_company_name(employee.current_client_company_id)}</td></tr>
                        <tr><th>근무타입</th><td>{get_work_type_name(employee.work_type_id)}</td></tr>
                        <tr><th>연락처</th><td>{employee.phone or '-'}</td></tr>
                        <tr><th>입사일</th><td>{employee.hire_date}</td></tr>
                        <tr><th>급여형태</th><td>{PAY_TYPE_LABELS.get(employee.pay_type, '-')}</td></tr>
                        <tr><th>재직상태</th><td>{_employee_status_badge(employee)}</td></tr>
                        <tr><th>오늘 상태</th><td>{status_badge(get_today_status(employee_id))}</td></tr>
                    </table>
                </div>
            </div>
            {retirement_panel}
            <div class="panel">
                <div class="panel-head"><h2>문서 등록</h2><p>파일 메타데이터 저장</p></div>
                <div class="panel-body">
                    <form method="post">
                        <div class="form-grid">
                            <div><label>문서종류</label><select name="document_type"><option value="id_card">신분증</option><option value="passport">여권</option><option value="other">기타 문서</option></select></div>
                            <div><label>파일명</label><input name="file_name" placeholder="예: passport_kim.pdf"></div>
                            <div><label>MIME 타입</label><input name="file_mime_type" value="application/pdf"></div>
                            <div><label>민감정보</label><select name="is_sensitive"><option value="Y">민감</option><option value="N">일반</option></select></div>
                        </div>
                        <div class="actions"><button class="btn btn-primary" type="submit">문서 등록</button></div>
                    </form>
                </div>
            </div>
            <div class="panel" style="margin-top:18px;">
                <div class="panel-head"><h2>등록 문서</h2><p>첨부 문서 메타데이터</p></div>
                <div class="panel-body">
                    <table>
                        <thead><tr><th>번호</th><th>종류</th><th>파일명</th><th>MIME</th><th>등급</th><th>등록일</th></tr></thead>
                        <tbody>{document_rows or '<tr><td colspan="6">문서가 없습니다.</td></tr>'}</tbody>
                    </table>
                </div>
            </div>
            <div class="panel" style="margin-top:18px;">
                <div class="panel-head"><h2>출퇴근 기록</h2><p>최근 이력</p></div>
                <div class="panel-body">
                    <table>
                        <thead><tr><th>번호</th><th>근무일</th><th>근무타입</th><th>출근</th><th>퇴근</th><th>상태</th><th>사유</th></tr></thead>
                        <tbody>{attendance_rows or '<tr><td colspan="7">출퇴근 기록이 없습니다.</td></tr>'}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    '''
    quick = [{"label": "사원목록", "href": "/employees", "active": False}, {"label": "인력상세", "href": f"/employees/{employee.id}", "active": True}]
    return render_page("인력상세", "employees", content, quick)
