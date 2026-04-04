
from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, redirect, render_template_string, request, url_for
from werkzeug.utils import secure_filename

from models import AttendanceRecord, ClientCompany, Employee, EmployeeDocument, OurBusiness, db
from services.document_ai import extract_document_data
from utils import (
    DOCUMENT_TYPE_LABELS,
    PAY_TYPE_LABELS,
    get_client_company_name,
    get_employee,
    get_employee_documents,
    get_our_business_name,
    get_today_status,
    get_work_type_name,
    render_client_company_options,
    render_our_business_options,
    render_page,
    render_work_type_options,
    status_badge,
    today_str,
)

employees_bp = Blueprint("employees", __name__)

ALLOWED_UPLOAD_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}


def _employee_base_query(status: str = "active"):
    query = Employee.query
    if status == "active":
        query = query.filter(Employee.status != "retired")
    elif status == "retired":
        query = query.filter_by(status="retired")
    return query


def _employee_action_buttons(employee: Employee) -> str:
    retire_button = ""
    if employee.status == "retired":
        retire_button = f"""
        <form method="post" action="/employees/{employee.id}/reactivate" onsubmit="return confirm('재직 상태로 복귀할까요?');">
            <button class="btn btn-white" type="submit">재직복귀</button>
        </form>
        """
    else:
        retire_button = f"""
        <form method="post" action="/employees/{employee.id}/retire" onsubmit="return confirm('퇴사처리할까요?');">
            <button class="btn btn-white" type="submit">퇴사처리</button>
        </form>
        """
    return f"""
    <div class="actions" style="margin:0; gap:8px; flex-wrap:wrap;">
        <a class="btn btn-white" href="/employees/{employee.id}/edit">수정</a>
        {retire_button}
        <form method="post" action="/employees/{employee.id}/delete" onsubmit="return confirm('삭제할까요? 근태나 문서가 있으면 삭제되지 않습니다.');">
            <button class="btn btn-danger" type="submit">삭제</button>
        </form>
    </div>
    """


def _employee_filters() -> tuple[int | None, str]:
    client_company_raw = request.args.get("client_company_id", "")
    client_company_id = int(client_company_raw) if client_company_raw.isdigit() else None
    keyword = request.args.get("keyword", "").strip()
    return client_company_id, keyword


def _employee_rows(status: str) -> tuple[str, int | None, str]:
    client_company_id, keyword = _employee_filters()
    query = _employee_base_query(status)
    if client_company_id is not None:
        query = query.filter_by(current_client_company_id=client_company_id)
    if keyword:
        query = query.filter(Employee.name.contains(keyword))
    rows = ""
    for employee in query.order_by(Employee.id.asc()).all():
        state_text = "퇴사" if employee.status == "retired" else status_badge(get_today_status(employee.id))
        rows += f"""
        <tr>
            <td>{employee.id}</td>
            <td><a href="/employees/{employee.id}">{employee.name}</a></td>
            <td>{employee.nationality or '-'}</td>
            <td>{get_our_business_name(employee.our_business_id)}</td>
            <td>{get_client_company_name(employee.current_client_company_id)}</td>
            <td>{get_work_type_name(employee.work_type_id)}</td>
            <td>{PAY_TYPE_LABELS.get(employee.pay_type, "-")}</td>
            <td>{state_text}</td>
            <td>{_employee_action_buttons(employee)}</td>
        </tr>
        """
    return rows, client_company_id, keyword


def _employee_filter_form(client_company_id: int | None, keyword: str) -> str:
    filter_options = ['<option value="">전체 거래처</option>']
    for item in ClientCompany.query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if item.id == client_company_id else ""
        filter_options.append(f'<option value="{item.id}" {selected}>{item.name}</option>')
    return f"""
    <div class="panel" style="margin-bottom:18px;">
        <div class="panel-body">
            <form method="get" class="actions" style="margin-top:0;">
                <div style="min-width:240px;"><label>이름 검색</label><input name="keyword" value="{keyword}" placeholder="이름 검색"></div>
                <div style="min-width:260px;"><label>거래처 필터</label><select name="client_company_id">{"".join(filter_options)}</select></div>
                <div><button class="btn btn-white" type="submit">조회</button></div>
                <div><a class="btn btn-white" href="{request.path}">초기화</a></div>
            </form>
        </div>
    </div>
    """


def _employee_quick(active_key: str) -> list[dict[str, str | bool]]:
    return [
        {"label": "사원목록", "href": "/employees", "active": active_key == "list"},
        {"label": "퇴사자관리", "href": "/employees/retired", "active": active_key == "retired"},
    ]


def _store_uploaded_file(employee_id: int):
    file = request.files.get("document_file")
    if not file or not file.filename:
        return None, "파일을 선택하세요."
    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        return None, "PNG, JPG, WEBP, PDF만 업로드할 수 있습니다."

    safe_name = secure_filename(file.filename) or f"employee_{employee_id}{extension}"
    save_dir = Path(current_app.config["UPLOAD_FOLDER"]) / "employee_documents" / str(employee_id)
    save_dir.mkdir(parents=True, exist_ok=True)
    save_name = f"{uuid4().hex}_{safe_name}"
    save_path = save_dir / save_name
    file.save(save_path)
    return save_path, ""


def _apply_extracted_data_to_employee(
    employee: Employee,
    document_type: str,
    extraction,
    *,
    overwrite: bool = False,
) -> None:
    def assign_if_allowed(field_name: str, value: str) -> None:
        if not value:
            return
        current_value = getattr(employee, field_name, "") or ""
        if overwrite or not current_value:
            setattr(employee, field_name, value)

    assign_if_allowed("name", extraction.name)
    assign_if_allowed("english_name", extraction.english_name)
    assign_if_allowed("local_name", extraction.local_name)
    assign_if_allowed("nationality", extraction.nationality)
    assign_if_allowed("birth_date", extraction.birth_date)
    assign_if_allowed("gender", extraction.gender)

    if extraction.document_number:
        if document_type == "passport":
            assign_if_allowed("passport_number", extraction.document_number)
        elif document_type == "id_card":
            assign_if_allowed("id_card_number", extraction.document_number)

    assign_if_allowed("profile_photo_path", extraction.photo_path)
    employee.updated_at = today_str()





def _save_document_record(
    employee: Employee,
    *,
    saved_path: Path,
    document_type: str,
    file_name: str,
    file_mime_type: str,
    is_sensitive: bool,
) -> str:
    extraction = extract_document_data(
        file_path=str(saved_path),
        employee_id=employee.id,
        document_type=document_type,
        upload_root=current_app.config["UPLOAD_FOLDER"],
    )
    relative_file_path = f"/uploads/employee_documents/{employee.id}/{saved_path.name}"
    document = EmployeeDocument(
        employee_id=employee.id,
        document_type=document_type,
        file_name=file_name.strip() or saved_path.name,
        file_path=relative_file_path,
        preview_photo_path=extraction.photo_path,
        extracted_text=extraction.text,
        extracted_name=extraction.name,
        extracted_english_name=extraction.english_name,
        extracted_local_name=extraction.local_name,
        extracted_nationality=extraction.nationality,
        extracted_document_number=extraction.document_number,
        extracted_birth_date=extraction.birth_date,
        extracted_gender=extraction.gender,
        file_mime_type=file_mime_type or "application/octet-stream",
        is_sensitive=is_sensitive,
        uploaded_by="super_admin",
        created_at=today_str(),
    )
    db.session.add(document)
    _apply_extracted_data_to_employee(
        employee,
        document_type,
        extraction,
        overwrite=request.form.get("apply_to_employee", "Y") == "Y",
    )
    db.session.commit()
    return {
        "ocr_success": "문서를 업로드하고 자동 인식했습니다.",
        "ocr_unavailable": "문서는 저장됐지만 OCR 엔진이 없어 자동 인식은 건너뛰었습니다.",
        "ocr_empty": "문서는 저장됐지만 인식된 텍스트가 적어 자동 입력이 제한되었습니다.",
        "pdf_stored_only": "PDF는 저장만 완료했습니다. OCR/사진 추출은 이미지 업로드에서 더 잘 동작합니다.",
        "stored": "문서를 저장했습니다.",
    }.get(extraction.status, "문서를 저장했습니다.")


def _finalize_temp_document(
    employee: Employee,
    *,
    temp_relative_path: str,
    document_type: str,
    file_name: str,
    file_mime_type: str,
    is_sensitive: bool,
) -> str:
    if not temp_relative_path.startswith("/uploads/"):
        return ""
    source_path = Path(current_app.root_path) / temp_relative_path.lstrip("/")
    if not source_path.exists():
        return ""
    employee_dir = Path(current_app.config["UPLOAD_FOLDER"]) / "employee_documents" / str(employee.id)
    employee_dir.mkdir(parents=True, exist_ok=True)
    target_path = employee_dir / source_path.name
    if source_path.resolve() != target_path.resolve():
        target_path.write_bytes(source_path.read_bytes())
    return _save_document_record(
        employee,
        saved_path=target_path,
        document_type=document_type,
        file_name=file_name,
        file_mime_type=file_mime_type,
        is_sensitive=is_sensitive,
    )


def _save_temp_upload(document_file) -> tuple[str, str]:
    suffix = Path(document_file.filename).suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        return "", "PNG, JPG, WEBP, PDF 파일만 업로드할 수 있습니다."
    temp_dir = Path(current_app.config["UPLOAD_FOLDER"]) / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    filename = f"tmp_{uuid4().hex}{suffix}"
    saved_path = temp_dir / secure_filename(filename)
    document_file.save(saved_path)
    return f"/uploads/tmp/{saved_path.name}", ""


def _render_employee_new_page(
    *,
    selected_our_business_id: int,
    selected_client_company_id: int,
    form_values: dict[str, str],
    preview_path: str = "",
    extraction_message: str = "",
    extraction_status: str = "",
) -> str:
    business_options = render_our_business_options(selected_our_business_id)
    client_options = render_client_company_options(selected_client_company_id, selected_our_business_id)
    work_type_options = render_work_type_options(selected_client_company_id, int(form_values.get("work_type_id") or 0))
    extraction_tone = "#eff6ff" if extraction_status == "success" else "#fff7ed" if extraction_status == "warn" else "#f8fafc"
    extraction_text = extraction_message or "파일 선택 후 자동추출을 누르면 아래 입력칸과 사진칸이 자동으로 채워집니다."
    preview_html = ""
    if preview_path:
        preview_html = f'<img src="{preview_path}" alt="추출 사진 미리보기" style="width:100%; height:100%; object-fit:cover; display:block;">'
    else:
        preview_html = '<div style="display:flex; align-items:center; justify-content:center; width:100%; height:100%; color:#64748b; font-weight:700;">사진 미리보기</div>'
    fill_notice = ""
    if extraction_status:
        fill_notice = f'<div style="margin-bottom:14px; padding:12px 14px; border:1px solid #dbe4ef; border-radius:12px; background:{extraction_tone}; color:#0f172a;">{extraction_text}</div>'

    def v(key: str) -> str:
        return (form_values.get(key) or "").replace('"', '&quot;')

    content = f"""
    <div class="panel">
        <div class="panel-head"><h2>사원등록</h2><p>파일 선택 후 자동추출을 누르면 아래 입력값과 사진칸에 자동 반영됩니다.</p></div>
        <div class="panel-body">
            <form method="get" class="panel" style="box-shadow:none; border-radius:14px; margin-bottom:16px;">
                <div class="panel-body">
                    <div class="form-grid">
                        <div><label>사업자</label><select name="our_business_id" onchange="this.form.submit()">{business_options}</select></div>
                        <div><label>거래처</label><select name="client_company_id" onchange="this.form.submit()">{client_options}</select></div>
                    </div>
                </div>
            </form>
            <form method="post" enctype="multipart/form-data">
                <input type="hidden" name="our_business_id" value="{selected_our_business_id}">
                <input type="hidden" name="client_company_id" value="{selected_client_company_id}">
                <input type="hidden" name="temp_file_path" value="{v('temp_file_path')}">
                <input type="hidden" name="existing_document_file_name" value="{v('existing_document_file_name')}">
                <input type="hidden" name="existing_document_mime_type" value="{v('existing_document_mime_type')}">

                <div style="display:grid; grid-template-columns:260px minmax(0,1fr); gap:18px; align-items:start; margin-bottom:18px;">
                    <div class="panel" style="box-shadow:none; border-radius:16px; overflow:hidden;">
                        <div class="panel-head"><h2 style="font-size:18px;">사진 미리보기</h2><p>자동 추출된 사진</p></div>
                        <div class="panel-body">
                            <div style="width:100%; aspect-ratio:3 / 4; border:1px dashed #c7d3e3; border-radius:18px; overflow:hidden; background:#f8fafc;">
                                {preview_html}
                            </div>
                            <div class="helper-text" style="margin-top:10px; color:#64748b;">사진은 박스 안에만 표시되며 저장 후 상세 사진칸에 반영됩니다.</div>
                        </div>
                    </div>

                    <div class="panel" style="box-shadow:none; border-radius:16px; background:#f8fbff;">
                        <div class="panel-head"><h2 style="font-size:18px;">문서 업로드 / OCR 자동입력</h2><p>문서 업로드 후 자동추출을 누르면 아래 입력칸이 채워집니다.</p></div>
                        <div class="panel-body">
                            {fill_notice}
                            <div class="form-grid">
                                <div>
                                    <label>문서 유형</label>
                                    <select name="document_type">
                                        <option value="passport" {"selected" if v("document_type") == "passport" else ""}>여권</option>
                                        <option value="id_card" {"selected" if v("document_type") == "id_card" else ""}>ID 카드</option>
                                        <option value="other" {"selected" if v("document_type") == "other" else ""}>기타 문서</option>
                                    </select>
                                </div>
                                <div>
                                    <label>문서 파일</label>
                                    <input type="file" name="document_file" accept=".png,.jpg,.jpeg,.webp,.pdf">
                                </div>
                                <div>
                                    <label>문서명</label>
                                    <input name="file_name" value="{v('file_name')}" placeholder="예: 여권 앞면">
                                </div>
                                <div>
                                    <label>민감 문서 여부</label>
                                    <select name="is_sensitive">
                                        <option value="Y" {"selected" if v("is_sensitive") != "N" else ""}>민감</option>
                                        <option value="N" {"selected" if v("is_sensitive") == "N" else ""}>일반</option>
                                    </select>
                                </div>
                            </div>
                            <div class="actions" style="margin-top:14px;">
                                <button class="btn btn-white" type="submit" name="action" value="autoextract">자동추출</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-grid">
                    <div><label>사업자</label><input value="{get_our_business_name(selected_our_business_id)}" disabled></div>
                    <div><label>거래처</label><input value="{get_client_company_name(selected_client_company_id)}" disabled></div>
                    <div><label>이름</label><input name="name" value="{v('name')}" required></div>
                    <div><label>영문이름</label><input name="english_name" value="{v('english_name')}"></div>
                    <div><label>현지이름</label><input name="local_name" value="{v('local_name')}"></div>
                    <div><label>국적</label><input name="nationality" value="{v('nationality')}" required></div>
                    <div><label>여권번호</label><input name="passport_number" value="{v('passport_number')}"></div>
                    <div><label>ID번호</label><input name="id_card_number" value="{v('id_card_number')}"></div>
                    <div><label>생년월일</label><input type="date" name="birth_date" value="{v('birth_date')}"></div>
                    <div><label>성별</label>
                        <select name="gender">
                            <option value="">선택</option>
                            <option value="남" {"selected" if v("gender") == "남" else ""}>남</option>
                            <option value="여" {"selected" if v("gender") == "여" else ""}>여</option>
                        </select>
                    </div>
                    <div><label>연락처</label><input name="phone" value="{v('phone')}"></div>
                    <div><label>입사일</label><input type="date" name="hire_date" value="{v('hire_date') or today_str()}"></div>
                    <div><label>급여형태</label>
                        <select name="pay_type">
                            <option value="monthly" {"selected" if v("pay_type") in {"", "monthly"} else ""}>월급제</option>
                            <option value="daily" {"selected" if v("pay_type") == "daily" else ""}>일급제</option>
                            <option value="hourly" {"selected" if v("pay_type") == "hourly" else ""}>시급제</option>
                        </select>
                    </div>
                    <div><label>근무타입</label><select name="work_type_id">{work_type_options}</select></div>
                </div>
                <div class="actions">
                    <button class="btn btn-primary" type="submit" name="action" value="save">저장</button>
                    <a class="btn btn-white" href="/employees">취소</a>
                </div>
            </form>
        </div>
    </div>
    """
    return render_page("사원등록", "employees", content, _employee_quick("list"))
def _save_employee_document(employee: Employee, *, document_type: str) -> str:
    save_path, error_message = _store_uploaded_file(employee.id)
    if error_message:
        return error_message
    assert save_path is not None
    document_file = request.files.get("document_file")
    return _save_document_record(
        employee,
        saved_path=save_path,
        document_type=document_type,
        file_name=request.form.get("file_name", "").strip() or save_path.name,
        file_mime_type=(document_file.mimetype if document_file else "") or "application/octet-stream",
        is_sensitive=request.form.get("is_sensitive", "Y") == "Y",
    )

def _profile_photo(employee: Employee) -> str:
    if employee.profile_photo_path:
        return f'<img src="{employee.profile_photo_path}" alt="직원 사진" style="width:100%; max-width:220px; border-radius:18px; border:1px solid #dbe4ef; object-fit:cover;">'
    return '<div class="photo-box">사진이 없습니다</div>'


def _document_extraction_summary(document: EmployeeDocument) -> str:
    rows = []
    if document.extracted_name:
        rows.append(f"<tr><th>이름</th><td>{document.extracted_name}</td></tr>")
    if document.extracted_english_name:
        rows.append(f"<tr><th>영문이름</th><td>{document.extracted_english_name}</td></tr>")
    if document.extracted_nationality:
        rows.append(f"<tr><th>국적</th><td>{document.extracted_nationality}</td></tr>")
    if document.extracted_document_number:
        rows.append(f"<tr><th>문서번호</th><td>{document.extracted_document_number}</td></tr>")
    if document.extracted_birth_date:
        rows.append(f"<tr><th>생년월일</th><td>{document.extracted_birth_date}</td></tr>")
    if document.extracted_gender:
        rows.append(f"<tr><th>성별</th><td>{document.extracted_gender}</td></tr>")
    if not rows:
        return "<p style='margin:0; color:#64748b;'>추출된 문서 정보가 없습니다. 이미지 품질이 낮거나 OCR이 준비되지 않았을 수 있습니다.</p>"
    photo_html = ""
    if document.preview_photo_path:
        photo_html = f'<div style="margin-bottom:12px;"><img src="{document.preview_photo_path}" alt="추출 사진" style="width:160px; border-radius:14px; border:1px solid #dbe4ef;"></div>'
    return f"{photo_html}<table>{''.join(rows)}</table>"


@employees_bp.route("/employees")
def employees_page() -> str:
    rows, client_company_id, keyword = _employee_rows("active")
    content = f"""
    {_employee_filter_form(client_company_id, keyword)}
    <div class="panel">
        <div class="panel-head"><h2>사원목록</h2><p>재직 중인 인력 관리</p></div>
        <div class="panel-body">
            <div class="actions" style="margin-top:0; margin-bottom:16px;"><a class="btn btn-primary" href="/employees/new">사원등록</a></div>
            <table>
                <thead><tr><th>번호</th><th>이름</th><th>국적</th><th>사업자</th><th>거래처</th><th>근무타입</th><th>급여형태</th><th>오늘 상태</th><th>관리</th></tr></thead>
                <tbody>{rows or '<tr><td colspan="9">인력이 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    return render_page("직원관리", "employees", content, _employee_quick("list"))


@employees_bp.route("/employees/retired")
def retired_employees_page() -> str:
    rows, client_company_id, keyword = _employee_rows("retired")
    content = f"""
    {_employee_filter_form(client_company_id, keyword)}
    <div class="panel">
        <div class="panel-head"><h2>퇴사자관리</h2><p>퇴사 처리된 인력만 별도 관리</p></div>
        <div class="panel-body">
            <table>
                <thead><tr><th>번호</th><th>이름</th><th>국적</th><th>사업자</th><th>거래처</th><th>근무타입</th><th>급여형태</th><th>상태</th><th>관리</th></tr></thead>
                <tbody>{rows or '<tr><td colspan="9">퇴사자가 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    return render_page("퇴사자관리", "employees", content, _employee_quick("retired"))


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

    form_values = {
        "document_type": request.values.get("document_type", "passport"),
        "file_name": request.values.get("file_name", ""),
        "is_sensitive": request.values.get("is_sensitive", "Y"),
        "name": request.values.get("name", ""),
        "english_name": request.values.get("english_name", ""),
        "local_name": request.values.get("local_name", ""),
        "nationality": request.values.get("nationality", ""),
        "passport_number": request.values.get("passport_number", ""),
        "id_card_number": request.values.get("id_card_number", ""),
        "birth_date": request.values.get("birth_date", ""),
        "gender": request.values.get("gender", ""),
        "phone": request.values.get("phone", ""),
        "hire_date": request.values.get("hire_date", today_str()),
        "pay_type": request.values.get("pay_type", "monthly"),
        "work_type_id": request.values.get("work_type_id", ""),
        "temp_file_path": request.values.get("temp_file_path", ""),
        "existing_document_file_name": request.values.get("existing_document_file_name", ""),
        "existing_document_mime_type": request.values.get("existing_document_mime_type", ""),
    }
    if not form_values["work_type_id"]:
        form_values["work_type_id"] = str(getattr(clients[0], "default_work_type_id", "") or "")

    preview_path = ""
    extraction_message = ""
    extraction_status = ""

    if request.method == "POST":
        action = request.form.get("action", "save")
        if action == "autoextract":
            document_file = request.files.get("document_file")
            if not document_file or not document_file.filename:
                extraction_message = "자동추출할 문서 파일을 먼저 선택하세요."
                extraction_status = "warn"
            else:
                temp_relative_path, error_message = _save_temp_upload(document_file)
                if error_message:
                    extraction_message = error_message
                    extraction_status = "warn"
                else:
                    source_path = Path(current_app.root_path) / temp_relative_path.lstrip("/")
                    extraction = extract_document_data(
                        file_path=str(source_path),
                        employee_id=0,
                        document_type=form_values["document_type"],
                        upload_root=current_app.config["UPLOAD_FOLDER"],
                    )
                    preview_path = extraction.photo_path or temp_relative_path
                    form_values["temp_file_path"] = temp_relative_path
                    form_values["existing_document_file_name"] = document_file.filename
                    form_values["existing_document_mime_type"] = document_file.mimetype or "application/octet-stream"
                    if extraction.name and not form_values["name"]:
                        form_values["name"] = extraction.name
                    if extraction.english_name:
                        form_values["english_name"] = extraction.english_name
                    if extraction.local_name:
                        form_values["local_name"] = extraction.local_name
                    if extraction.nationality:
                        form_values["nationality"] = extraction.nationality
                    if form_values["document_type"] == "passport":
                        if extraction.document_number:
                            form_values["passport_number"] = extraction.document_number
                    elif extraction.document_number:
                        form_values["id_card_number"] = extraction.document_number
                    if extraction.birth_date:
                        form_values["birth_date"] = extraction.birth_date
                    if extraction.gender:
                        form_values["gender"] = extraction.gender
                    extraction_message = {
                        "ocr_success": "자동추출이 완료됐습니다. 아래 입력칸과 사진칸을 확인한 뒤 저장하세요.",
                        "ocr_empty": "이미지는 읽었지만 값이 적습니다. 아래 값을 직접 보완하세요.",
                        "ocr_unavailable": "OCR 엔진이 없어 자동추출이 제한됩니다. 사진만 미리보기에 표시했습니다.",
                        "pdf_stored_only": "PDF는 저장용에 적합합니다. 이미지 업로드가 더 잘 동작합니다.",
                        "stored": "문서를 읽지 못했지만 업로드는 완료됐습니다.",
                    }.get(extraction.status, "자동추출을 완료했습니다.")
                    extraction_status = "success" if extraction.status == "ocr_success" else "warn"
            return _render_employee_new_page(
                selected_our_business_id=selected_our_business_id,
                selected_client_company_id=selected_client_company_id,
                form_values=form_values,
                preview_path=preview_path,
                extraction_message=extraction_message,
                extraction_status=extraction_status,
            )

        item = Employee(
            our_business_id=int(request.form["our_business_id"]),
            current_client_company_id=int(request.form["client_company_id"]),
            name=request.form["name"].strip(),
            english_name=request.form.get("english_name", "").strip(),
            local_name=request.form.get("local_name", "").strip(),
            nationality=request.form.get("nationality", "").strip(),
            passport_number=request.form.get("passport_number", "").strip(),
            id_card_number=request.form.get("id_card_number", "").strip(),
            birth_date=request.form.get("birth_date", "").strip(),
            gender=request.form.get("gender", "").strip(),
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

        upload_message = ""
        if request.files.get("document_file") and request.files["document_file"].filename:
            upload_message = _save_employee_document(
                item,
                document_type=request.form.get("document_type", "other"),
            )
        elif request.form.get("temp_file_path"):
            upload_message = _finalize_temp_document(
                item,
                temp_relative_path=request.form.get("temp_file_path", ""),
                document_type=request.form.get("document_type", "other"),
                file_name=request.form.get("existing_document_file_name", "").strip() or request.form.get("file_name", "").strip(),
                file_mime_type=request.form.get("existing_document_mime_type", ""),
                is_sensitive=request.form.get("is_sensitive", "Y") == "Y",
            )

        if upload_message:
            return redirect(url_for("employees.employee_detail", employee_id=item.id, upload_message=upload_message))
        return redirect(url_for("employees.employees_page"))

    return _render_employee_new_page(
        selected_our_business_id=selected_our_business_id,
        selected_client_company_id=selected_client_company_id,
        form_values=form_values,
    )


@employees_bp.route("/employees/<int:employee_id>", methods=["GET", "POST"])
def employee_detail(employee_id: int) -> str:
    employee = get_employee(employee_id)
    if not employee:
        return "인력을 찾을 수 없습니다.", 404

    upload_message = request.args.get("upload_message", "").strip()

    if request.method == "POST":
        upload_message = _save_employee_document(
            employee,
            document_type=request.form.get("document_type", "other"),
        )
        return redirect(url_for("employees.employee_detail", employee_id=employee_id, upload_message=upload_message))

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
    documents = get_employee_documents(employee_id)
    latest_document = documents[0] if documents else None
    for index, document in enumerate(documents, start=1):
        preview_link = f'<a href="{document.preview_photo_path}" target="_blank">추출사진</a>' if document.preview_photo_path else '-'
        document_rows += f"""
        <tr>
            <td>{index}</td>
            <td>{DOCUMENT_TYPE_LABELS.get(document.document_type, document.document_type)}</td>
            <td><a href="{document.file_path}" target="_blank">{document.file_name}</a></td>
            <td>{document.file_mime_type}</td>
            <td>{'민감' if document.is_sensitive else '일반'}</td>
            <td>{preview_link}</td>
            <td>{document.created_at}</td>
        </tr>
        """

    latest_extract_block = ""
    if latest_document:
        latest_extract_block = f"""
        <div class="panel" style="margin-top:18px;">
            <div class="panel-head"><h2>최근 문서 자동 인식 결과</h2><p>최신 업로드 문서 기준</p></div>
            <div class="panel-body">
                {_document_extraction_summary(latest_document)}
            </div>
        </div>
        """

    upload_notice = f'<div class="panel" style="margin-bottom:18px; background:#f8fbff;"><div class="panel-body" style="padding:14px 18px;">{upload_message}</div></div>' if upload_message else ""

    content = f"""
    {upload_notice}
    <div class="two-col">
        <div class="side-box" style="padding:14px;">
            <h3 style="margin:0 0 12px;">인력 사진</h3>
            {_profile_photo(employee)}
            <div style="margin-top:12px; color:#64748b; font-size:13px;">여권/ID 카드 이미지 업로드 시 사진 영역을 자동으로 잘라서 여기에 보여줍니다.</div>
        </div>
        <div>
            <div class="panel" style="margin-bottom:18px;">
                <div class="panel-head"><h2>인력상세</h2><p>기본정보 / 문서 / 출퇴근 기록</p></div>
                <div class="panel-body">
                    <div class="actions" style="margin-top:0; margin-bottom:16px;">{_employee_action_buttons(employee)}</div>
                    <table>
                        <tr><th style="width:220px;">이름</th><td>{employee.name}</td></tr>
                        <tr><th>영문이름</th><td>{employee.english_name or '-'}</td></tr>
                        <tr><th>현지이름</th><td>{employee.local_name or '-'}</td></tr>
                        <tr><th>국적</th><td>{employee.nationality or '-'}</td></tr>
                        <tr><th>여권번호</th><td>{employee.passport_number or '-'}</td></tr>
                        <tr><th>ID번호</th><td>{employee.id_card_number or '-'}</td></tr>
                        <tr><th>생년월일</th><td>{employee.birth_date or '-'}</td></tr>
                        <tr><th>성별</th><td>{employee.gender or '-'}</td></tr>
                        <tr><th>사업자</th><td>{get_our_business_name(employee.our_business_id)}</td></tr>
                        <tr><th>거래처</th><td>{get_client_company_name(employee.current_client_company_id)}</td></tr>
                        <tr><th>근무타입</th><td>{get_work_type_name(employee.work_type_id)}</td></tr>
                        <tr><th>연락처</th><td>{employee.phone or '-'}</td></tr>
                        <tr><th>입사일</th><td>{employee.hire_date}</td></tr>
                        <tr><th>급여형태</th><td>{PAY_TYPE_LABELS.get(employee.pay_type, '-')}</td></tr>
                        <tr><th>상태</th><td>{"퇴사" if employee.status == "retired" else status_badge(get_today_status(employee_id))}</td></tr>
                    </table>
                </div>
            </div>
            <div class="panel">
                <div class="panel-head"><h2>문서 등록</h2><p>이미지 업로드 시 OCR 자동입력과 사진 추출을 시도합니다.</p></div>
                <div class="panel-body">
                    <form method="post" enctype="multipart/form-data">
                        <div class="form-grid">
                            <div><label>문서종류</label><select name="document_type"><option value="id_card">신분증</option><option value="passport">여권</option><option value="other">기타 문서</option></select></div>
                            <div><label>표시 파일명</label><input name="file_name" placeholder="비워두면 실제 파일명을 사용"></div>
                            <div><label>문서 파일</label><input type="file" name="document_file" accept=".png,.jpg,.jpeg,.webp,.pdf" required></div>
                            <div><label>MIME 타입</label><select name="file_mime_type"><option value="image/jpeg">image/jpeg</option><option value="image/png">image/png</option><option value="image/webp">image/webp</option><option value="application/pdf">application/pdf</option></select></div>
                            <div><label>민감 문서 여부</label><select name="is_sensitive"><option value="Y">민감</option><option value="N">일반</option></select></div>
                            <div><label>직원 정보에 자동 반영</label><select name="apply_to_employee"><option value="Y">예</option><option value="N">아니오</option></select></div>
                        </div>
                        <div class="actions"><button class="btn btn-primary" type="submit">문서 업로드</button></div>
                    </form>
                </div>
            </div>
            {latest_extract_block}
        </div>
    </div>
    <div class="panel" style="margin-top:18px;">
        <div class="panel-head"><h2>등록 문서 목록</h2><p>민감 문서는 최고관리자만 열람 가능 정책</p></div>
        <div class="panel-body">
            <table><thead><tr><th>번호</th><th>종류</th><th>파일명</th><th>MIME</th><th>권한</th><th>추출사진</th><th>등록일</th></tr></thead><tbody>{document_rows or '<tr><td colspan="7">등록된 문서가 없습니다.</td></tr>'}</tbody></table>
        </div>
    </div>
    <div class="panel" style="margin-top:18px;">
        <div class="panel-head"><h2>출퇴근 기록</h2><p>관리자가 직접 처리한 1일 1레코드 기록</p></div>
        <div class="panel-body">
            <table><thead><tr><th>번호</th><th>날짜</th><th>근무타입</th><th>출근</th><th>퇴근</th><th>상태</th><th>사유</th></tr></thead><tbody>{attendance_rows or '<tr><td colspan="7">기록이 없습니다.</td></tr>'}</tbody></table>
        </div>
    </div>
    """
    active_key = "retired" if employee.status == "retired" else "list"
    return render_page("직원상세", "employees", content, _employee_quick(active_key))


@employees_bp.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
def employee_edit(employee_id: int) -> str:
    employee = get_employee(employee_id)
    if not employee:
        return "인력을 찾을 수 없습니다.", 404

    selected_our_business_raw = request.values.get("our_business_id", str(employee.our_business_id))
    selected_our_business_id = int(selected_our_business_raw) if selected_our_business_raw.isdigit() else employee.our_business_id
    selected_client_raw = request.values.get("client_company_id", str(employee.current_client_company_id or ""))
    selected_client_company_id = int(selected_client_raw) if selected_client_raw.isdigit() else (employee.current_client_company_id or 0)

    if request.method == "POST":
        employee.our_business_id = int(request.form["our_business_id"])
        employee.current_client_company_id = int(request.form["client_company_id"])
        employee.name = request.form["name"].strip()
        employee.english_name = request.form.get("english_name", "").strip()
        employee.local_name = request.form.get("local_name", "").strip()
        employee.nationality = request.form.get("nationality", "").strip()
        employee.passport_number = request.form.get("passport_number", "").strip()
        employee.id_card_number = request.form.get("id_card_number", "").strip()
        employee.birth_date = request.form.get("birth_date", "").strip()
        employee.gender = request.form.get("gender", "").strip()
        employee.phone = request.form.get("phone", "").strip()
        employee.hire_date = request.form.get("hire_date", today_str())
        employee.pay_type = request.form.get("pay_type", "monthly")
        employee.work_type_id = int(request.form["work_type_id"])
        employee.updated_at = today_str()
        db.session.commit()
        return redirect(url_for("employees.employee_detail", employee_id=employee_id))

    business_options = render_our_business_options(selected_our_business_id)
    client_options = render_client_company_options(selected_client_company_id, selected_our_business_id)
    work_type_options = render_work_type_options(selected_client_company_id)

    content = f"""
    <div class="panel">
        <div class="panel-head"><h2>사원수정</h2><p>{employee.name}</p></div>
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
                    <div><label>이름</label><input name="name" value="{employee.name}" required></div>
                    <div><label>영문이름</label><input name="english_name" value="{employee.english_name or ''}"></div>
                    <div><label>현지이름</label><input name="local_name" value="{employee.local_name or ''}"></div>
                    <div><label>국적</label><input name="nationality" value="{employee.nationality or ''}" required></div>
                    <div><label>여권번호</label><input name="passport_number" value="{employee.passport_number or ''}"></div>
                    <div><label>ID번호</label><input name="id_card_number" value="{employee.id_card_number or ''}"></div>
                    <div><label>생년월일</label><input type="date" name="birth_date" value="{employee.birth_date or ''}"></div>
                    <div><label>성별</label><select name="gender"><option value="" {"selected" if not employee.gender else ""}>선택</option><option value="남" {"selected" if employee.gender == "남" else ""}>남</option><option value="여" {"selected" if employee.gender == "여" else ""}>여</option></select></div>
                    <div><label>연락처</label><input name="phone" value="{employee.phone or ''}"></div>
                    <div><label>입사일</label><input type="date" name="hire_date" value="{employee.hire_date}"></div>
                    <div><label>급여형태</label><select name="pay_type"><option value="monthly" {"selected" if employee.pay_type == "monthly" else ""}>월급제</option><option value="daily" {"selected" if employee.pay_type == "daily" else ""}>일급제</option><option value="hourly" {"selected" if employee.pay_type == "hourly" else ""}>시급제</option></select></div>
                    <div><label>근무타입</label><select name="work_type_id">{work_type_options}</select></div>
                </div>
                <div class="actions"><button class="btn btn-primary" type="submit">저장</button><a class="btn btn-white" href="/employees/{employee.id}">취소</a></div>
            </form>
        </div>
    </div>
    """
    active_key = "retired" if employee.status == "retired" else "list"
    return render_page("사원수정", "employees", content, _employee_quick(active_key))


@employees_bp.route("/employees/<int:employee_id>/retire", methods=["POST"])
def employee_retire(employee_id: int):
    employee = get_employee(employee_id)
    if not employee:
        return "인력을 찾을 수 없습니다.", 404
    employee.status = "retired"
    employee.updated_at = today_str()
    db.session.commit()
    return redirect(request.referrer or url_for("employees.employees_page"))


@employees_bp.route("/employees/<int:employee_id>/reactivate", methods=["POST"])
def employee_reactivate(employee_id: int):
    employee = get_employee(employee_id)
    if not employee:
        return "인력을 찾을 수 없습니다.", 404
    employee.status = "active"
    employee.updated_at = today_str()
    db.session.commit()
    return redirect(request.referrer or url_for("employees.retired_employees_page"))


@employees_bp.route("/employees/<int:employee_id>/delete", methods=["POST"])
def employee_delete(employee_id: int):
    employee = get_employee(employee_id)
    if not employee:
        return "인력을 찾을 수 없습니다.", 404
    has_attendance = AttendanceRecord.query.filter_by(employee_id=employee_id).count() > 0
    has_documents = EmployeeDocument.query.filter_by(employee_id=employee_id).count() > 0
    if not has_attendance and not has_documents:
        db.session.delete(employee)
        db.session.commit()
    return redirect(url_for("employees.retired_employees_page" if employee.status == "retired" else "employees.employees_page"))
