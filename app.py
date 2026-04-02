from flask import Flask, request, redirect, url_for, render_template_string
from datetime import datetime

app = Flask(__name__)

records = []

HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>테스트용 사원관리 프로그램</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            background: #f7f7f7;
        }
        h1 {
            margin-bottom: 10px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        input, select, button {
            padding: 10px;
            margin: 5px 0;
            width: 100%;
            box-sizing: border-box;
        }
        button {
            cursor: pointer;
            border: none;
            border-radius: 6px;
        }
        .btn-checkin {
            background: #16a34a;
            color: white;
        }
        .btn-checkout {
            background: #2563eb;
            color: white;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        th, td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: center;
        }
        th {
            background: #e5e7eb;
        }
        .muted {
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <h1>테스트용 사원관리 / 출퇴근 프로그램</h1>
    <p class="muted">Render 배포 테스트용 간단 버전</p>

    <div class="card">
        <form method="post" action="/checkin">
            <label>회사명</label>
            <input type="text" name="company" placeholder="예: 그린시스템" required>

            <label>사원명</label>
            <input type="text" name="employee" placeholder="예: 홍길동" required>

            <button type="submit" class="btn-checkin">출근</button>
        </form>
    </div>

    <div class="card">
        <form method="post" action="/checkout">
            <label>퇴근할 사원명</label>
            <input type="text" name="employee" placeholder="예: 홍길동" required>

            <button type="submit" class="btn-checkout">퇴근</button>
        </form>
    </div>

    <div class="card">
        <h2>출퇴근 기록</h2>
        <table>
            <thead>
                <tr>
                    <th>번호</th>
                    <th>회사명</th>
                    <th>사원명</th>
                    <th>출근시간</th>
                    <th>퇴근시간</th>
                    <th>상태</th>
                </tr>
            </thead>
            <tbody>
                {% for row in records %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ row.company }}</td>
                    <td>{{ row.employee }}</td>
                    <td>{{ row.checkin }}</td>
                    <td>{{ row.checkout if row.checkout else "-" }}</td>
                    <td>{{ row.status }}</td>
                </tr>
                {% endfor %}
                {% if not records %}
                <tr>
                    <td colspan="6">아직 기록이 없습니다.</td>
                </tr>
                {% endif %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML, records=records)

@app.route("/checkin", methods=["POST"])
def checkin():
    company = request.form["company"].strip()
    employee = request.form["employee"].strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    records.append({
        "company": company,
        "employee": employee,
        "checkin": now,
        "checkout": "",
        "status": "근무중"
    })
    return redirect(url_for("index"))

@app.route("/checkout", methods=["POST"])
def checkout():
    employee = request.form["employee"].strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for row in reversed(records):
        if row["employee"] == employee and not row["checkout"]:
            row["checkout"] = now
            row["status"] = "퇴근완료"
            break

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
