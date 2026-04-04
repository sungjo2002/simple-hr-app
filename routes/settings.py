
from __future__ import annotations

import io
import os
import zipfile
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, send_file, url_for
from openpyxl import Workbook

from models import (
    AttendanceRecord,
    ClientCompany,
    ClientCompanyPayrollSetting,
    ClientCompanySetting,
    ClientCompanyWorkType,
    Employee,
    EmployeeDocument,
    OurBusiness,
    PayrollItem,
    PayrollRun,
)
from utils import render_page

settings_bp = Blueprint("settings", __name__)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _sheet_from_rows(sheet_name: str, rows: list[dict[str, object]]) -> Workbook:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name
    if not rows:
        worksheet.append(["데이터 없음"])
        return workbook

    headers = list(rows[0].keys())
    worksheet.append(headers)
    for row in rows:
        worksheet.append([row.get(header, "") for header in headers])

    for column_cells in worksheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter
        for cell in column_cells:
            value = "" if cell.value is None else str(cell.value)
            max_length = max(max_length, len(value))
        worksheet.column_dimensions[column_letter].width = min(max(max_length + 2, 12), 40)
    worksheet.freeze_panes = "A2"
    return workbook


def _workbook_bytes(sheet_name: str, rows: list[dict[str, object]]) -> io.BytesIO:
    workbook = _sheet_from_rows(sheet_name, rows)
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def _model_rows(items, columns: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in items:
        row = {}
        for column in columns:
            row[column] = getattr(item, column, "")
        rows.append(row)
    return rows


def _business_rows() -> list[dict[str, object]]:
    columns = [
        "id",
        "name",
        "ceo_name",
        "business_number",
        "phone",
        "address",
        "business_type",
        "business_item",
        "email",
        "is_active",
        "memo",
        "created_at",
        "updated_at",
    ]
    items = OurBusiness.query.order_by(OurBusiness.id.asc()).all()
    return _model_rows(items, columns)


def _client_rows() -> list[dict[str, object]]:
    columns = [
        "id",
        "our_business_id",
        "name",
        "ceo_name",
        "business_number",
        "phone",
        "address",
        "business_type",
        "business_item",
        "email",
        "is_active",
        "memo",
        "created_at",
        "updated_at",
    ]
    items = ClientCompany.query.order_by(ClientCompany.id.asc()).all()
    return _model_rows(items, columns)


def _employee_rows() -> list[dict[str, object]]:
    base_columns = [
        "id",
        "our_business_id",
        "current_client_company_id",
        "name",
        "nationality",
        "phone",
        "hire_date",
        "status",
        "work_type_id",
        "pay_type",
        "created_at",
        "updated_at",
    ]
    optional_columns = [
        "retired_at",
        "retirement_reason",
        "is_recontact_target",
        "next_contact_date",
        "retirement_note",
    ]
    columns = list(base_columns)
    if Employee.query.first() is not None:
        sample = Employee.query.first()
        for column in optional_columns:
            if hasattr(sample, column):
                columns.append(column)
    items = Employee.query.order_by(Employee.id.asc()).all()
    return _model_rows(items, columns)


def _all_backup_sets() -> list[tuple[str, str, list[dict[str, object]]]]:
    return [
        ("사업자", "businesses", _business_rows()),
        ("거래처", "clients", _client_rows()),
        ("직원", "employees", _employee_rows()),
    ]


def _db_file_path() -> Path | None:
    database_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not database_uri.startswith("sqlite:///"):
        return None
    relative_path = database_uri.replace("sqlite:///", "", 1)
    if os.path.isabs(relative_path):
        return Path(relative_path)
    return Path(current_app.root_path).parent / relative_path


@settings_bp.route("/settings")
def settings_page() -> str:
    backup_cards = f"""
    <div class="form-grid">
        <div class="panel panel-soft">
            <div class="panel-head"><h3>엑셀 백업</h3><p>사업자 / 거래처 / 직원 기준정보를 바로 내려받습니다.</p></div>
            <div class="panel-body">
                <div class="actions">
                    <a class="btn btn-white" href="{url_for('settings.download_business_backup')}">사업자 다운로드</a>
                    <a class="btn btn-white" href="{url_for('settings.download_client_backup')}">거래처 다운로드</a>
                    <a class="btn btn-white" href="{url_for('settings.download_employee_backup')}">직원 다운로드</a>
                    <a class="btn btn-primary" href="{url_for('settings.download_all_excel_backup')}">통합 ZIP 다운로드</a>
                </div>
            </div>
        </div>
        <div class="panel panel-soft">
            <div class="panel-head"><h3>시스템 백업</h3><p>현재 사용 중인 데이터베이스를 그대로 보관합니다.</p></div>
            <div class="panel-body">
                <div class="actions">
                    <a class="btn btn-primary" href="{url_for('settings.download_database_backup')}">전체 DB 백업 다운로드</a>
                </div>
                <p class="muted" style="margin-top:12px;">SQLite 사용 시 현재 DB 파일을 그대로 내려받습니다. PostgreSQL 환경이면 안내 파일이 다운로드됩니다.</p>
            </div>
        </div>
    </div>
    """

    content = f"""
    <div class="panel" id="backup-management">
        <div class="panel-head"><h2>백업관리</h2><p>중요 데이터는 설정에서 직접 다운로드해 보관할 수 있습니다.</p></div>
        <div class="panel-body">
            {backup_cards}
        </div>
    </div>
    <div class="panel" id="system-config">
        <div class="panel-head"><h2>설정</h2><p>권한 / 문서 / 운영 기준</p></div>
        <div class="panel-body">
            <table>
                <tr><th style="width:220px;">저장 방식</th><td>로컬 SQLite / 배포 PostgreSQL 연동</td></tr>
                <tr><th>최고관리자</th><td>웹 사용 가능 / 앱 사용 가능 / 민감 문서 열람 가능</td></tr>
                <tr><th>부관리자</th><td>앱만 사용 가능 / 출퇴근 처리 / 기록 조회</td></tr>
                <tr><th>직원</th><td>앱 조회 중심 / 직접 출퇴근 불가</td></tr>
                <tr><th>문서 권한</th><td>민감 문서는 최고관리자만 열람 가능</td></tr>
                <tr><th>출퇴근 정책</th><td>직원이 아니라 관리자가 직접 처리</td></tr>
                <tr><th>근무타입</th><td>거래처별 개별 설정, 공통 고정값 사용 안 함</td></tr>
            </table>
        </div>
    </div>
    """
    quick_links = [
        {"label": "백업관리", "href": "/settings#backup-management", "active": True},
        {"label": "시스템설정", "href": "/settings#system-config", "active": False},
    ]
    return render_page("설정", "settings", content, quick_links)


@settings_bp.route("/settings/backups/businesses.xlsx")
def download_business_backup():
    output = _workbook_bytes("사업자", _business_rows())
    filename = f"businesses_backup_{_timestamp()}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@settings_bp.route("/settings/backups/clients.xlsx")
def download_client_backup():
    output = _workbook_bytes("거래처", _client_rows())
    filename = f"client_companies_backup_{_timestamp()}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@settings_bp.route("/settings/backups/employees.xlsx")
def download_employee_backup():
    output = _workbook_bytes("직원", _employee_rows())
    filename = f"employees_backup_{_timestamp()}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@settings_bp.route("/settings/backups/all.zip")
def download_all_excel_backup():
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for sheet_name, slug, rows in _all_backup_sets():
            workbook_bytes = _workbook_bytes(sheet_name, rows)
            archive.writestr(f"{slug}_backup_{_timestamp()}.xlsx", workbook_bytes.getvalue())
        archive.writestr(
            "README.txt",
            "사업자, 거래처, 직원 기준정보 백업 파일입니다.\n설정 > 백업관리에서 다시 다운로드할 수 있습니다.\n",
        )
    output.seek(0)
    filename = f"master_backup_{_timestamp()}.zip"
    return send_file(output, as_attachment=True, download_name=filename, mimetype="application/zip")


@settings_bp.route("/settings/backups/database")
def download_database_backup():
    db_path = _db_file_path()
    if db_path and db_path.exists():
        return send_file(
            db_path,
            as_attachment=True,
            download_name=f"database_backup_{_timestamp()}{db_path.suffix or '.db'}",
            mimetype="application/octet-stream",
        )

    output = io.BytesIO()
    message = "\n".join(
        [
            "현재 환경에서는 직접 DB 파일 백업을 만들 수 없습니다.",
            "이 앱은 PostgreSQL 등 외부 데이터베이스를 사용할 수 있어 DB 파일이 로컬에 존재하지 않을 수 있습니다.",
            "대신 설정 > 백업관리에서 엑셀/ZIP 백업을 내려받아 보관하세요.",
        ]
    )
    output.write(message.encode("utf-8"))
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name=f"database_backup_notice_{_timestamp()}.txt",
        mimetype="text/plain; charset=utf-8",
    )
