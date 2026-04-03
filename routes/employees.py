from flask import Blueprint, flash, redirect, request, url_for

from models import ClientCompany, Employee, EmployeeDocument, db
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
        ]

    sort_funcs = {
        "id": lambda employee: employee.id,
        "name": lambda employee: employee.name.lower(),
        "nationality": lambda employee: employee.nationality.lower(),
        "our_business": lambda employee: get_our_business_name(employee.our_business_id).lower(),
        "client_company": lambda employee: get_client_company_name(employee.current_client_company_id).lower(),
        "work_type": lambda employee: get_work_type_name(employee.work_type_id).lower(),
        "pay_type": lambda employee: PAY_TYPE_LABELS.get(employee.pay_type, "-"),
        "status": lambda employee: get_today_status(employee.id),
    }
    items = sort_items(items, sort, sort_funcs, direction)

    export_headers = ["번호", "이름", "국적", "사업자", "거래처", "근무타입", "급여형태", "오늘 상태"]
    export_rows = [
        [
            employee.id,
            employee.name,
            employee.nationality,
            get_our_business_name(employee.our_business_id),
            get_client_company_name(employee.current_client_company_id),
            get_work_type_name(employee.work_type_id),
            PAY_TYPE_LABELS.get(employee.pay_type, "-"),
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
        rows += f"""
        <tr>
            <td>{employee.id}</td>
            <td><a href="/employees/{employee.id}">{employee.name}</a></td>
            <td>{employee.nationality}</td>
            <td>{get_our_business_name(employee.our_business_id)}</td>
            <td>{get_client_company_name(employee.current_client_company_id)}</td>
            <td>{get_work_type_name(employee.work_type_id)}</td>
            <td>{PAY_TYPE_LABELS.get(employee.pay_type, "-")}</td>
            <td>{status_badge(get_today_status(employee.id))}</td>
        </tr>
        """

    filter_options = ['<option value="">전체 거래처</option>']
    for item in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if item.id == client_company_id else ""
        filter_options.append(f'<option value="{item.id}" {selected}>{item.name}</option>')

    current_params = {"client_company_id": client_company_raw, "q": q, "sort": sort, "direction": direction}
    toolbar = render_table_toolbar(
        base_path="/employees",
        current_params=current_params,
        search_placeholder="이름, 국적, 사업자, 거래처, 근무타입 검색",
        search_value=q,
        sort_options=[("id", "번호"), ("name", "이름"), ("nationality", "국적"), ("our_business", "사업자"), ("client_company", "거래처"), ("work_type", "근무타입"), ("pay_type", "급여형태"), ("status", "오늘 상태")],
        current_sort=sort,
        current_direction=direction,
        create_href="/employees/new",
        create_label="인력등록",
        reset_href="/employees",
    ).replace('<input type="hidden" name="page" value="1">', f'<input type="hidden" name="page" value="1"><input type="hidden" name="client_company_id" value="{client_company_raw}">')

    pagination = render_pagination("/employees", current_params, page, total_pages, total_count)
    content = f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <div style="min-width:260px;"><label>거래처 필터</label><select name="client_company_id">{''.join(filter_options)}</select></div>
                <input type="hidden" name="q" value="{q}">
                <input type="hidden" name="sort" value="{sort}">
                <input type="hidden" name="direction" value="{direction}">
                <div><button class="btn btn-white" type="submit">조회</button></div>
                <div><a class="btn btn-white" href="/employees">초기화</a></div>
            </form>
        </div>
    </div>
    <div class="panel">
        <div class="panel-head"><h2>인력목록</h2><p>사업자 / 거래처 / 근무타입 기준 관리</p></div>
        <div class="panel-body">
            {toolbar}
            <table>
                <thead><tr><th>번호</th><th>이름</th><th>국적</th><th>사업자</th><th>거래처</th><th>근무타입</th><th>급여형태</th><th>오늘 상태</th></tr></thead>
                <tbody>{rows or '<tr><td colspan="8">인력이 없습니다.</td></tr>'}</tbody>
            </table>
            {pagination}
        </div>
    </div>
    """
    quick = [{"label": "사원목록", "href": "/employees", "active": True}, {"label": "사원등록", "href": "/employees/new", "active": False}]
    return render_page("직원관리", "employees", content, quick)


@employees_bp.route("/employees/new", methods=["GET", "POST"])
def employee_new() -> str:
    from models import ClientCompany, OurBusiness
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

    content = f"""
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
                    <div><label>급여형태</label><select name="pay_type"><option value="monthly">월급제</option><option value="daily">일급제</option><option value="hourly">시급제</option></select></div>
                    <div><label>근무타입</label><select name="work_type_id">{work_type_options}</select></div>
                </div>
                <div class="actions"><button class="btn btn-primary" type="submit">저장</button><a class="btn btn-white" href="/employees">취소</a></div>
            </form>
        </div>
    </div>
    """
    quick = [{"label": "사원목록", "href": "/employees", "active": False}, {"label": "사원등록", "href": "/employees/new", "active": True}]
    return render_page("직원등록", "employees", content, quick)


@employees_bp.route("/employees/<int:employee_id>", methods=["GET", "POST"])
def employee_detail(employee_id: int) -> str:
    from models import AttendanceRecord
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
        attendance_rows += f"""
        <tr>
            <td>{index}</td>
            <td>{record.work_date}</td>
            <td>{get_work_type_name(record.work_type_id)}</td>
            <td>{record.check_in_at or '-'}</td>
            <td>{record.check_out_at or '-'}</td>
            <td>{status_badge(record.status)}</td>
            <td>{record.reason or '-'}</td>
        </tr>
        """

    document_rows = ""
    for index, document in enumerate(get_employee_documents(employee_id), start=1):
        document_rows += f"""
        <tr>
            <td>{index}</td>
            <td>{DOCUMENT_TYPE_LABELS.get(document.document_type, document.document_type)}</td>
            <td>{document.file_name}</td>
            <td>{document.file_mime_type}</td>
            <td>{'민감' if document.is_sensitive else '일반'}</td>
            <td>{document.created_at}</td>
        </tr>
        """

    content = f"""
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
                        <tr><th>오늘 상태</th><td>{status_badge(get_today_status(employee_id))}</td></tr>
                    </table>
                </div>
            </div>
            <div class="panel">
                <div class="panel-head"><h2>문서 등록</h2><p>파일 메타데이터 저장</p></div>
                <div class="panel-body">
                    <form method="post">
                        <div class="form-grid">
                            <div><label>문서종류</label><select name="document_type"><option value="id_card">신분증</option><option value="passport">여권</option><option value="other">기타 문서</option></select></div>
                            <div><label>파일명</label><input name="file_name" placeholder="예: passport.pdf"></div>
                            <div><label>MIME 타입</label><select name="file_mime_type"><option value="application/pdf">application/pdf</option><option value="image/jpeg">image/jpeg</option><option value="image/png">image/png</option></select></div>
                            <div><label>민감 문서 여부</label><select name="is_sensitive"><option value="Y">민감</option><option value="N">일반</option></select></div>
                        </div>
                        <div class="actions"><button class="btn btn-primary" type="submit">문서 저장</button></div>
                    </form>
                </div>
            </div>
        </div>
    </div>
    <div class="panel" style="margin-top:18px;">
        <div class="panel-head"><h2>등록 문서 목록</h2><p>민감 문서는 최고관리자만 열람 가능 정책</p></div>
        <div class="panel-body">
            <table><thead><tr><th>번호</th><th>종류</th><th>파일명</th><th>MIME</th><th>권한</th><th>등록일</th></tr></thead><tbody>{document_rows or '<tr><td colspan="6">등록된 문서가 없습니다.</td></tr>'}</tbody></table>
        </div>
    </div>
    <div class="panel" style="margin-top:18px;">
        <div class="panel-head"><h2>출퇴근 기록</h2><p>관리자가 직접 처리한 1일 1레코드 기록</p></div>
        <div class="panel-body">
            <table><thead><tr><th>번호</th><th>날짜</th><th>근무타입</th><th>출근</th><th>퇴근</th><th>상태</th><th>사유</th></tr></thead><tbody>{attendance_rows or '<tr><td colspan="7">기록이 없습니다.</td></tr>'}</tbody></table>
        </div>
    </div>
    """
    quick = [{"label": "사원목록", "href": "/employees", "active": True}, {"label": "사원등록", "href": "/employees/new", "active": False}]
    return render_page("직원상세", "employees", content, quick)
