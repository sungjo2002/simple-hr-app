from flask import Flask, request, redirect, url_for, render_template_string
from datetime import datetime

app = Flask(__name__)

today_str = datetime.now().strftime("%Y-%m-%d")

companies = [
    {
        "id": 1,
        "name": "그린시스템",
        "owner": "홍길동",
        "biz_no": "123-45-67890",
        "phone": "02-1234-5678",
        "address": "경북 경주시 예시로 101",
        "work_types": ["주간", "야간"],
    }
]

employees = [
    {"id": 1, "company_id": 1, "name": "성조", "nationality": "한국", "work_type": "주간", "status": "근무중"},
    {"id": 2, "company_id": 1, "name": "응우옌", "nationality": "베트남", "work_type": "야간", "status": "출근전"},
    {"id": 3, "company_id": 1, "name": "알리", "nationality": "우즈베키스탄", "work_type": "주간", "status": "퇴근완료"},
]

attendance_records = []

BASE = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<style>
    body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: #eef2f6;
        color: #111827;
    }
    .topbar {
        background: linear-gradient(180deg, #22354a, #1b2b3c);
        color: white;
        padding: 16px 24px;
        font-size: 28px;
        font-weight: bold;
    }
    .menu {
        background: #d8dde4;
        border-bottom: 1px solid #b8c1cb;
        padding: 10px 14px;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .menu a {
        text-decoration: none;
        color: #111827;
        background: white;
        border: 1px solid #bcc6d1;
        border-radius: 8px;
        padding: 10px 16px;
        font-weight: bold;
        font-size: 14px;
    }
    .menu a.active {
        background: #1f2937;
        color: white;
        border-color: #1f2937;
    }
    .quickbar {
        background: #f8fafc;
        border-bottom: 1px solid #d8dee6;
        padding: 10px 14px;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .quickbar a, .quickbar button {
        text-decoration: none;
        border: 1px solid #c8d0da;
        background: white;
        color: #111827;
        border-radius: 10px;
        padding: 10px 14px;
        font-weight: bold;
        font-size: 13px;
        cursor: pointer;
    }
    .wrap {
        max-width: 1350px;
        margin: 0 auto;
        padding: 20px;
    }
    .cards {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px;
        margin-bottom: 20px;
    }
    .card {
        background: white;
        border: 1px solid #d7dee7;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        padding: 18px;
    }
    .card .label {
        font-size: 13px;
        color: #6b7280;
        margin-bottom: 8px;
    }
    .card .value {
        font-size: 30px;
        font-weight: bold;
    }
    .content-grid {
        display: grid;
        grid-template-columns: 1.2fr 0.8fr;
        gap: 18px;
    }
    .panel {
        background: white;
        border: 1px solid #d7dee7;
        border-radius: 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        overflow: hidden;
    }
    .panel-head {
        padding: 16px 18px;
        border-bottom: 1px solid #e5e7eb;
    }
    .panel-head h2 {
        margin: 0;
        font-size: 22px;
    }
    .panel-head p {
        margin: 6px 0 0;
        font-size: 13px;
        color: #6b7280;
    }
    .panel-body {
        padding: 18px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        background: white;
    }
    th, td {
        border-top: 1px solid #edf1f5;
        padding: 12px 10px;
        text-align: left;
        font-size: 14px;
    }
    th {
        background: #f3f5f8;
        font-weight: bold;
        color: #374151;
    }
    .badge {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: bold;
    }
    .green { background: #dcfce7; color: #166534; }
    .blue { background: #dbeafe; color: #1d4ed8; }
    .yellow { background: #fef3c7; color: #92400e; }
    .gray { background: #e5e7eb; color: #374151; }
    .btn {
        display: inline-block;
        text-decoration: none;
        border: none;
        border-radius: 10px;
        padding: 11px 16px;
        font-weight: bold;
        cursor: pointer;
        font-size: 14px;
    }
    .btn-primary { background: #2563eb; color: white; }
    .btn-green { background: #16a34a; color: white; }
    .btn-sky { background: #0284c7; color: white; }
    .btn-gray { background: #4b5563; color: white; }
    .btn-white { background: white; color: #111827; border: 1px solid #c8d0da; }
    .form-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
    }
    .form-full {
        grid-column: 1 / -1;
    }
    label {
        display: block;
        font-size: 13px;
        font-weight: bold;
        margin-bottom: 6px;
        color: #374151;
    }
    input, select, textarea {
        width: 100%;
        box-sizing: border-box;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 14px;
        background: white;
    }
    textarea { min-height: 90px; resize: vertical; }
    .actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 18px;
    }
    .two-col {
        display: grid;
        grid-template-columns: 250px 1fr;
        gap: 18px;
    }
    .side-box {
        background: white;
        border: 1px solid #d7dee7;
        border-radius: 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        padding: 14px;
    }
    .side-box h3 {
        margin: 0 0 12px;
        font-size: 18px;
    }
    .side-box a {
        display: block;
        text-decoration: none;
        color: #111827;
        background: #f8fafc;
        border: 1px solid #d7dee7;
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 8px;
        font-size: 14px;
    }
    .photo-box {
        height: 220px;
        border: 2px dashed #cbd5e1;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f8fafc;
        color: #6b7280;
        font-weight: bold;
    }
    .subtabs {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 16px;
    }
    .subtabs a {
        text-decoration: none;
        padding: 10px 14px;
        border-radius: 10px;
        background: #f3f4f6;
        border: 1px solid #d1d5db;
        color: #111827;
        font-size: 13px;
        font-weight: bold;
    }
    .subtabs a.active {
        background: #111827;
        color: white;
        border-color: #111827;
    }
    @media (max-width: 1100px) {
        .cards { grid-template-columns: 1fr 1fr; }
        .content-grid, .two-col { grid-template-columns: 1fr; }
        .form-grid { grid-template-columns: 1fr; }
    }
</style>
</head>
<body>
    <div class="topbar">멀티회사 사원관리 · 출퇴근 시스템</div>

    <div class="menu">
        <a href="/" class="{{ 'active' if active=='home' else '' }}">메인</a>
        <a href="/companies" class="{{ 'active' if active=='companies' else '' }}">회사관리</a>
        <a href="/employees" class="{{ 'active' if active=='employees' else '' }}">사원관리</a>
        <a href="/attendance" class="{{ 'active' if active=='attendance' else '' }}">출퇴근관리</a>
        <a href="/records" class="{{ 'active' if active=='records' else '' }}">기록조회</a>
        <a href="/settings" class="{{ 'active' if active=='settings' else '' }}">설정</a>
    </div>

    {% if quick_links %}
    <div class="quickbar">
        {% for item in quick_links %}
            <a href="{{ item.href }}">{{ item.label }}</a>
        {% endfor %}
    </div>
    {% endif %}

    <div class="wrap">
        {{ content|safe }}
    </div>
</body>
</html>
"""

def render_page(title, active, content, quick_links=None):
    return render_template_string(
        BASE,
        title=title,
        active=active,
        content=content,
        quick_links=quick_links or [],
    )

def status_badge(status):
    if status == "근무중":
        return '<span class="badge green">근무중</span>'
    if status == "출근전":
        return '<span class="badge yellow">출근전</span>'
    if status == "퇴근완료":
        return '<span class="badge blue">퇴근완료</span>'
    return f'<span class="badge gray">{status}</span>'

@app.route("/")
def home():
    total = len(employees)
    day_count = len([e for e in employees if e["work_type"] == "주간" and e["status"] == "근무중"])
    night_count = len([e for e in employees if e["work_type"] == "야간" and e["status"] == "근무중"])
    before_count = len([e for e in employees if e["status"] == "출근전"])
    done_count = len([e for e in employees if e["status"] == "퇴근완료"])

    rows = ""
    for e in employees:
        rows += f"""
        <tr>
            <td>{e['id']}</td>
            <td><a href="/employees/{e['id']}">{e['name']}</a></td>
            <td>{e['nationality']}</td>
            <td>{e['work_type']}</td>
            <td>{status_badge(e['status'])}</td>
        </tr>
        """

    content = f"""
    <div class="cards">
        <div class="card"><div class="label">전체 사원</div><div class="value">{total}</div></div>
        <div class="card"><div class="label">오늘({today_str}) 주간 근무중</div><div class="value">{day_count}</div></div>
        <div class="card"><div class="label">오늘({today_str}) 야간 근무중</div><div class="value">{night_count}</div></div>
        <div class="card"><div class="label">출근전</div><div class="value">{before_count}</div></div>
        <div class="card"><div class="label">퇴근완료</div><div class="value">{done_count}</div></div>
    </div>

    <div class="content-grid">
        <div class="panel">
            <div class="panel-head">
                <h2>사원목록</h2>
                <p>이름 + 국적 중심 간단 구조</p>
            </div>
            <div class="panel-body">
                <table>
                    <thead>
                        <tr>
                            <th>사번</th>
                            <th>이름</th>
                            <th>국적</th>
                            <th>근무타입</th>
                            <th>상태</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>

        <div>
            <div class="panel" style="margin-bottom:18px;">
                <div class="panel-head">
                    <h2>빠른 작업</h2>
                    <p>관리자가 직접 처리</p>
                </div>
                <div class="panel-body">
                    <div class="actions">
                        <a class="btn btn-primary" href="/employees/new">사원등록</a>
                        <a class="btn btn-green" href="/attendance">출근처리</a>
                        <a class="btn btn-sky" href="/attendance">퇴근처리</a>
                        <a class="btn btn-gray" href="/records">기록조회</a>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-head">
                    <h2>회사별 설정</h2>
                    <p>회사마다 근무기준 다르게 적용</p>
                </div>
                <div class="panel-body">
                    <p><strong>그린시스템</strong></p>
                    <p>근무타입: 주간 / 야간</p>
                    <p>사업자번호: 123-45-67890</p>
                    <a class="btn btn-white" href="/companies/1/settings">회사별 설정 보기</a>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page("메인", "home", content)

@app.route("/companies")
def companies_page():
    rows = ""
    for c in companies:
        rows += f"""
        <tr>
            <td>{c['id']}</td>
            <td><a href="/companies/{c['id']}">{c['name']}</a></td>
            <td>{c['biz_no']}</td>
            <td>{c['phone']}</td>
            <td><a class="btn btn-white" href="/companies/{c['id']}/settings">설정</a></td>
        </tr>
        """

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>회사목록</h2>
            <p>회사등록에서 사업자 정보까지 입력</p>
        </div>
        <div class="panel-body">
            <div class="actions" style="margin-top:0; margin-bottom:16px;">
                <a class="btn btn-primary" href="/companies/new">+ 회사등록</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>번호</th>
                        <th>회사명</th>
                        <th>사업자등록번호</th>
                        <th>대표전화</th>
                        <th>관리</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "회사목록", "href": "/companies"},
        {"label": "회사등록", "href": "/companies/new"},
    ]
    return render_page("회사관리", "companies", content, quick)

@app.route("/companies/new", methods=["GET", "POST"])
def company_new():
    if request.method == "POST":
        new_id = max([c["id"] for c in companies], default=0) + 1
        companies.append({
            "id": new_id,
            "name": request.form["name"],
            "owner": request.form["owner"],
            "biz_no": request.form["biz_no"],
            "phone": request.form["phone"],
            "address": request.form["address"],
            "work_types": ["주간", "야간"],
        })
        return redirect(url_for("companies_page"))

    content = """
    <div class="panel">
        <div class="panel-head">
            <h2>회사등록</h2>
            <p>사업자등록증, 주소, 전화 등 기본 사업자 정보 입력</p>
        </div>
        <div class="panel-body">
            <form method="post">
                <div class="form-grid">
                    <div><label>회사명</label><input name="name" required></div>
                    <div><label>대표자명</label><input name="owner" required></div>

                    <div><label>사업자등록번호</label><input name="biz_no" placeholder="123-45-67890" required></div>
                    <div><label>대표전화</label><input name="phone" required></div>

                    <div class="form-full"><label>주소</label><input name="address" required></div>

                    <div><label>업태</label><input name="biz_type" placeholder="예: 서비스업"></div>
                    <div><label>종목</label><input name="biz_item" placeholder="예: 인력관리"></div>

                    <div><label>이메일</label><input name="email"></div>
                    <div><label>사용여부</label><select name="use_yn"><option>사용</option><option>미사용</option></select></div>

                    <div class="form-full"><label>메모</label><textarea name="memo"></textarea></div>
                </div>
                <div class="actions">
                    <button class="btn btn-primary" type="submit">저장</button>
                    <a class="btn btn-white" href="/companies">취소</a>
                </div>
            </form>
        </div>
    </div>
    """
    quick = [
        {"label": "회사목록", "href": "/companies"},
        {"label": "회사등록", "href": "/companies/new"},
    ]
    return render_page("회사등록", "companies", content, quick)

@app.route("/companies/<int:company_id>")
def company_detail(company_id):
    company = next((c for c in companies if c["id"] == company_id), None)
    if not company:
        return "회사를 찾을 수 없습니다.", 404

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>회사상세</h2>
            <p>{company['name']} 기본 정보</p>
        </div>
        <div class="panel-body">
            <table>
                <tr><th style="width:220px;">회사명</th><td>{company['name']}</td></tr>
                <tr><th>대표자명</th><td>{company['owner']}</td></tr>
                <tr><th>사업자등록번호</th><td>{company['biz_no']}</td></tr>
                <tr><th>대표전화</th><td>{company['phone']}</td></tr>
                <tr><th>주소</th><td>{company['address']}</td></tr>
            </table>
            <div class="actions">
                <a class="btn btn-white" href="/companies/{company_id}/settings">회사별 설정</a>
            </div>
        </div>
    </div>
    """
    quick = [
        {"label": "회사목록", "href": "/companies"},
        {"label": "회사등록", "href": "/companies/new"},
        {"label": "회사별 설정", "href": f"/companies/{company_id}/settings"},
    ]
    return render_page("회사상세", "companies", content, quick)

@app.route("/companies/<int:company_id>/settings")
def company_settings(company_id):
    company = next((c for c in companies if c["id"] == company_id), None)
    if not company:
        return "회사를 찾을 수 없습니다.", 404

    work_type_rows = ""
    for idx, wt in enumerate(company["work_types"], start=1):
        work_type_rows += f"<tr><td>{idx}</td><td>{wt}</td><td>사용</td></tr>"

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>회사별 설정</h2>
            <p>{company['name']} 기준 설정</p>
        </div>
        <div class="panel-body">
            <div class="subtabs">
                <a class="active" href="#">기본설정</a>
                <a href="#">근무타입설정</a>
                <a href="#">출퇴기준설정</a>
                <a href="#">문서설정</a>
                <a href="#">권한설정</a>
            </div>

            <div class="panel" style="box-shadow:none; border-radius:14px;">
                <div class="panel-head">
                    <h2 style="font-size:18px;">근무타입설정</h2>
                    <p>회사마다 근무 구분 기준이 다름</p>
                </div>
                <div class="panel-body">
                    <table>
                        <thead>
                            <tr>
                                <th>순서</th>
                                <th>근무타입명</th>
                                <th>사용여부</th>
                            </tr>
                        </thead>
                        <tbody>{work_type_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    """
    quick = [
        {"label": "회사목록", "href": "/companies"},
        {"label": "회사상세", "href": f"/companies/{company_id}"},
        {"label": "회사별 설정", "href": f"/companies/{company_id}/settings"},
    ]
    return render_page("회사별 설정", "companies", content, quick)

@app.route("/employees")
def employees_page():
    rows = ""
    for e in employees:
        company_name = next((c["name"] for c in companies if c["id"] == e["company_id"]), "-")
        rows += f"""
        <tr>
            <td>{e['id']}</td>
            <td><a href="/employees/{e['id']}">{e['name']}</a></td>
            <td>{e['nationality']}</td>
            <td>{company_name}</td>
            <td>{e['work_type']}</td>
            <td>{status_badge(e['status'])}</td>
        </tr>
        """
    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>사원목록</h2>
            <p>이름과 국적 중심</p>
        </div>
        <div class="panel-body">
            <div class="actions" style="margin-top:0; margin-bottom:16px;">
                <a class="btn btn-primary" href="/employees/new">사원등록</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>사번</th>
                        <th>이름</th>
                        <th>국적</th>
                        <th>회사</th>
                        <th>근무타입</th>
                        <th>상태</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "사원등록", "href": "/employees/new"},
        {"label": "사원목록", "href": "/employees"},
    ]
    return render_page("사원관리", "employees", content, quick)

@app.route("/employees/new", methods=["GET", "POST"])
def employee_new():
    if request.method == "POST":
        new_id = max([e["id"] for e in employees], default=0) + 1
        employees.append({
            "id": new_id,
            "company_id": int(request.form["company_id"]),
            "name": request.form["name"],
            "nationality": request.form["nationality"],
            "work_type": request.form["work_type"],
            "status": "출근전",
        })
        return redirect(url_for("employees_page"))

    company_options = "".join([f'<option value="{c["id"]}">{c["name"]}</option>' for c in companies])
    work_options = "".join([f'<option value="{w}">{w}</option>' for w in companies[0]["work_types"]])

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>사원등록</h2>
            <p>이름 + 국적 중심 구조</p>
        </div>
        <div class="panel-body">
            <form method="post">
                <div class="form-grid">
                    <div><label>회사</label><select name="company_id">{company_options}</select></div>
                    <div><label>이름</label><input name="name" placeholder="예: 성조" required></div>
                    <div><label>국적</label><input name="nationality" placeholder="예: 한국" required></div>
                    <div><label>근무타입</label><select name="work_type">{work_options}</select></div>
                </div>
                <div class="actions">
                    <button class="btn btn-primary" type="submit">저장</button>
                    <a class="btn btn-white" href="/employees">취소</a>
                </div>
            </form>
        </div>
    </div>
    """
    quick = [
        {"label": "사원등록", "href": "/employees/new"},
        {"label": "사원목록", "href": "/employees"},
    ]
    return render_page("사원등록", "employees", content, quick)

@app.route("/employees/<int:employee_id>")
def employee_detail(employee_id):
    employee = next((e for e in employees if e["id"] == employee_id), None)
    if not employee:
        return "사원을 찾을 수 없습니다.", 404

    records = [r for r in attendance_records if r["employee_id"] == employee_id]
    rec_rows = ""
    for idx, r in enumerate(records, start=1):
        rec_rows += f"""
        <tr>
            <td>{idx}</td>
            <td>{r['date']}</td>
            <td>{r['work_type']}</td>
            <td>{r['check_in'] or '-'}</td>
            <td>{r['check_out'] or '-'}</td>
            <td>{status_badge(r['status'])}</td>
        </tr>
        """
    if not rec_rows:
        rec_rows = '<tr><td colspan="6">기록이 없습니다.</td></tr>'

    company_name = next((c["name"] for c in companies if c["id"] == employee["company_id"]), "-")

    content = f"""
    <div class="two-col">
        <div class="side-box">
            <h3>사원 사진</h3>
            <div class="photo-box">사진 등록 영역</div>
            <div class="actions">
                <button class="btn btn-primary" type="button">사진 등록</button>
                <button class="btn btn-white" type="button">사진 변경</button>
            </div>
        </div>

        <div>
            <div class="panel" style="margin-bottom:18px;">
                <div class="panel-head">
                    <h2>사원상세</h2>
                    <p>선택한 사원 정보</p>
                </div>
                <div class="panel-body">
                    <table>
                        <tr><th style="width:220px;">이름</th><td>{employee['name']}</td></tr>
                        <tr><th>국적</th><td>{employee['nationality']}</td></tr>
                        <tr><th>회사</th><td>{company_name}</td></tr>
                        <tr><th>근무타입</th><td>{employee['work_type']}</td></tr>
                        <tr><th>현재상태</th><td>{status_badge(employee['status'])}</td></tr>
                    </table>
                </div>
            </div>

            <div class="panel">
                <div class="panel-head">
                    <h2>문서 등록</h2>
                    <p>PDF, JPG 등 다양한 파일 업로드 가능</p>
                </div>
                <div class="panel-body">
                    <div class="form-grid">
                        <div><label>문서종류</label><select><option>신분증</option><option>여권</option><option>기타 문서</option></select></div>
                        <div><label>파일명</label><input placeholder="예: passport.pdf"></div>
                    </div>
                    <div class="actions">
                        <button class="btn btn-primary" type="button">업로드</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="panel" style="margin-top:18px;">
        <div class="panel-head">
            <h2>출퇴근 기록</h2>
            <p>관리자가 직접 처리한 기록</p>
        </div>
        <div class="panel-body">
            <table>
                <thead>
                    <tr>
                        <th>번호</th>
                        <th>날짜</th>
                        <th>근무타입</th>
                        <th>출근</th>
                        <th>퇴근</th>
                        <th>상태</th>
                    </tr>
                </thead>
                <tbody>{rec_rows}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "사원등록", "href": "/employees/new"},
        {"label": "사원목록", "href": "/employees"},
    ]
    return render_page("사원상세", "employees", content, quick)

@app.route("/attendance", methods=["GET", "POST"])
def attendance_page():
    if request.method == "POST":
        employee_id = int(request.form["employee_id"])
        action_type = request.form["action_type"]

        emp = next((e for e in employees if e["id"] == employee_id), None)
        if emp:
            now = datetime.now().strftime("%H:%M:%S")
            date_now = datetime.now().strftime("%Y-%m-%d")

            if action_type == "checkin":
                attendance_records.append({
                    "employee_id": employee_id,
                    "date": date_now,
                    "work_type": emp["work_type"],
                    "check_in": now,
                    "check_out": "",
                    "status": "근무중",
                })
                emp["status"] = "근무중"

            if action_type == "checkout":
                for record in reversed(attendance_records):
                    if record["employee_id"] == employee_id and not record["check_out"]:
                        record["check_out"] = now
                        record["status"] = "퇴근완료"
                        emp["status"] = "퇴근완료"
                        break

        return redirect(url_for("attendance_page"))

    employee_options = "".join([f'<option value="{e["id"]}">{e["name"]} / {e["nationality"]} / {e["work_type"]}</option>' for e in employees])

    rows = ""
    for e in employees:
        rows += f"""
        <tr>
            <td>{e['name']}</td>
            <td>{e['nationality']}</td>
            <td>{e['work_type']}</td>
            <td>{status_badge(e['status'])}</td>
        </tr>
        """

    content = f"""
    <div class="content-grid">
        <div class="panel">
            <div class="panel-head">
                <h2>오늘 출퇴현황</h2>
                <p>관리자가 직접 처리</p>
            </div>
            <div class="panel-body">
                <table>
                    <thead>
                        <tr>
                            <th>이름</th>
                            <th>국적</th>
                            <th>근무타입</th>
                            <th>상태</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>

        <div class="panel">
            <div class="panel-head">
                <h2>출근 / 퇴근 처리</h2>
                <p>직원이 아니라 관리자가 처리</p>
            </div>
            <div class="panel-body">
                <form method="post">
                    <label>사원 선택</label>
                    <select name="employee_id">{employee_options}</select>

                    <label>처리 구분</label>
                    <select name="action_type">
                        <option value="checkin">출근처리</option>
                        <option value="checkout">퇴근처리</option>
                    </select>

                    <div class="actions">
                        <button class="btn btn-green" type="submit">저장</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    """
    quick = [
        {"label": "출퇴근관리", "href": "/attendance"},
        {"label": "기록조회", "href": "/records"},
    ]
    return render_page("출퇴근관리", "attendance", content, quick)

@app.route("/records")
def records_page():
    rows = ""
    for idx, r in enumerate(attendance_records, start=1):
        emp = next((e for e in employees if e["id"] == r["employee_id"]), None)
        name = emp["name"] if emp else "-"
        rows += f"""
        <tr>
            <td>{idx}</td>
            <td>{r['date']}</td>
            <td>{name}</td>
            <td>{r['work_type']}</td>
            <td>{r['check_in'] or '-'}</td>
            <td>{r['check_out'] or '-'}</td>
            <td>{status_badge(r['status'])}</td>
        </tr>
        """
    if not rows:
        rows = '<tr><td colspan="7">아직 기록이 없습니다.</td></tr>'

    content = f"""
    <div class="panel">
        <div class="panel-head">
            <h2>전체 출퇴기록</h2>
            <p>날짜 / 사원 / 근무타입 기준 조회</p>
        </div>
        <div class="panel-body">
            <table>
                <thead>
                    <tr>
                        <th>번호</th>
                        <th>날짜</th>
                        <th>사원명</th>
                        <th>근무타입</th>
                        <th>출근</th>
                        <th>퇴근</th>
                        <th>상태</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [
        {"label": "출퇴근관리", "href": "/attendance"},
        {"label": "기록조회", "href": "/records"},
    ]
    return render_page("기록조회", "records", content, quick)

@app.route("/settings")
def settings_page():
    content = """
    <div class="panel">
        <div class="panel-head">
            <h2>설정</h2>
            <p>권한 / 계정 / 시스템 설정</p>
        </div>
        <div class="panel-body">
            <table>
                <tr><th style="width:220px;">최고관리자</th><td>웹 사용 가능 / 앱 사용 가능</td></tr>
                <tr><th>부관리자</th><td>앱만 사용 가능</td></tr>
                <tr><th>문서 권한</th><td>민감 문서는 최고관리자만 열람</td></tr>
            </table>
        </div>
    </div>
    """
    return render_page("설정", "settings", content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
