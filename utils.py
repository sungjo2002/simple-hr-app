from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from typing import Any

from flask import Response, render_template_string, request, url_for

from models import AttendanceRecord, ClientCompany, ClientCompanyPayrollSetting, ClientCompanySetting, ClientCompanyWorkType, Employee, EmployeeDocument, OurBusiness, db

ATTENDANCE_STATUS = {
    "before_work": "출근전",
    "working": "근무중",
    "completed": "퇴근완료",
    "hospital": "병원",
    "vacation": "휴가",
    "absent": "결근",
}

DOCUMENT_TYPE_LABELS = {
    "id_card": "신분증",
    "passport": "여권",
    "other": "기타 문서",
}

PAY_TYPE_LABELS = {
    "monthly": "월급제",
    "daily": "일급제",
    "hourly": "시급제",
}


SECTION_META = {
    "home": {"label": "홈", "href": "/"},
    "employees": {"label": "직원관리", "href": "/employees"},
    "attendance": {"label": "근태관리", "href": "/attendance"},
    "client_companies": {"label": "거래처관리", "href": "/client-companies"},
    "our_businesses": {"label": "사업자관리", "href": "/our-businesses"},
    "records": {"label": "기록조회", "href": "/records"},
    "payroll": {"label": "급여관리", "href": "/payroll"},
    "settings": {"label": "설정", "href": "/settings"},
}


def build_breadcrumbs(title: str, active: str) -> list[dict[str, str | bool]]:
    section = SECTION_META.get(active)
    breadcrumbs: list[dict[str, str | bool]] = [{"label": "홈", "href": "/", "current": active == "home"}]
    if section and active != "home":
        breadcrumbs.append({"label": str(section["label"]), "href": str(section["href"]), "current": title == section["label"]})
    if not section:
        breadcrumbs.append({"label": title, "href": "", "current": True})
    elif title != section["label"]:
        breadcrumbs.append({"label": title, "href": "", "current": True})
    return breadcrumbs


def build_page_status(title: str, active: str) -> list[str]:
    status_items: list[str] = []

    if request.args.get("q"):
        status_items.append(f"검색: {request.args.get('q', '').strip()}")
    if request.args.get("sort"):
        direction_label = "오름차순" if request.args.get("direction", "asc") == "asc" else "내림차순"
        status_items.append(f"정렬: {request.args.get('sort')} · {direction_label}")
    if request.args.get("page"):
        status_items.append(f"페이지: {request.args.get('page')}")
    if request.args.get("work_date"):
        status_items.append(f"기준일: {request.args.get('work_date')}")
    if request.args.get("month"):
        status_items.append(f"기준월: {request.args.get('month')}")
    if request.args.get("client_company_id"):
        status_items.append("거래처 필터 적용")
    if request.args.get("export"):
        status_items.append(f"내보내기: {request.args.get('export').upper()}")

    if not status_items:
        section = SECTION_META.get(active)
        if section and title != section["label"]:
            status_items.append(str(section["label"]))
        status_items.append(f"현재 화면: {title}")
    return status_items


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_time_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def parse_month(value: str) -> tuple[int, int]:
    year_str, month_str = value.split("-")
    return int(year_str), int(month_str)


def month_str_default() -> str:
    return datetime.now().strftime("%Y-%m")



BASE_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<style>
    :root {
        --bg:#f4f7fb;
        --panel:#ffffff;
        --panel-soft:#f8fbff;
        --line:#dbe4ef;
        --line-strong:#c8d4e3;
        --text:#0f172a;
        --muted:#64748b;
        --primary:#1d4ed8;
        --primary-soft:#eff6ff;
        --primary-deep:#102a43;
        --green:#16a34a;
        --orange:#ea580c;
        --red:#dc2626;
        --sky:#0284c7;
        --yellow:#ca8a04;
        --shadow:0 18px 38px rgba(15, 23, 42, 0.08);
        --shadow-soft:0 10px 24px rgba(15, 23, 42, 0.05);
    }
    * { box-sizing:border-box; }
    html, body { height:100%; }
    body {
        margin:0;
        font-family:Arial,sans-serif;
        background:
            radial-gradient(circle at top left, rgba(59,130,246,.08), transparent 24%),
            linear-gradient(180deg, #eef4fb 0%, #f7f9fc 28%, #f4f7fb 100%);
        color:var(--text);
    }
    .topbar {
        background:linear-gradient(135deg,#10243a 0%,#173a63 52%,#1d4ed8 100%);
        color:white;
        padding:16px 20px 18px;
        box-shadow:0 16px 30px rgba(15, 23, 42, .18);
    }
    .topbar-inner {
        width:min(100%, 1280px);
        margin:0 auto;
        display:flex;
        flex-wrap:wrap;
        gap:14px;
        align-items:flex-end;
        justify-content:space-between;
    }
    .brand-kicker {
        font-size:12px;
        letter-spacing:.14em;
        text-transform:uppercase;
        color:rgba(255,255,255,.72);
        margin-bottom:8px;
        font-weight:700;
    }
    .brand-title {
        font-size:26px;
        line-height:1.15;
        font-weight:800;
        margin:0;
    }
    .brand-desc {
        margin:8px 0 0;
        font-size:14px;
        color:rgba(255,255,255,.82);
    }
    .topbar-meta {
        display:flex;
        flex-wrap:wrap;
        gap:10px;
        justify-content:flex-end;
    }
    .meta-pill {
        padding:10px 12px;
        border-radius:999px;
        border:1px solid rgba(255,255,255,.16);
        background:rgba(255,255,255,.10);
        backdrop-filter:blur(8px);
        font-size:13px;
        font-weight:700;
        color:#f8fbff;
    }
    .menu-shell {
        position:sticky;
        top:0;
        z-index:20;
        backdrop-filter: blur(12px);
        background:rgba(247,249,252,.82);
        border-bottom:1px solid rgba(203,213,225,.85);
    }
    .menu, .quickbar {
        width:min(100%,1280px);
        margin:0 auto;
        display:flex;
        flex-wrap:wrap;
        gap:14px;
        align-items:center;
        padding:14px 20px;
    }
    .menu a {
        text-decoration:none;
        color:#334155;
        font-weight:800;
        font-size:14px;
        padding:9px 12px;
        border-radius:12px;
        border:1px solid transparent;
        transition:color .15s ease, border-color .15s ease, background-color .15s ease, box-shadow .15s ease;
    }
    .menu a:hover {
        color:var(--primary);
        background:#f8fbff;
        border-color:#dbeafe;
    }
    .menu a.active {
        color:var(--primary);
        background:linear-gradient(180deg,#f8fbff 0%, #eff6ff 100%);
        border-color:#93c5fd;
        box-shadow:0 10px 18px rgba(37,99,235,.10);
    }
    .quickbar {
        gap:8px;
        padding-top:10px;
        padding-bottom:12px;
        border-top:1px solid rgba(219,228,239,.7);
    }
    .quickbar a, .section-chip {
        text-decoration:none;
        color:#0f172a;
        background:#fff;
        border:1px solid var(--line);
        border-radius:999px;
        padding:8px 12px;
        font-weight:700;
        font-size:12px;
        box-shadow:var(--shadow-soft);
        transition:background-color .15s ease, border-color .15s ease, color .15s ease, box-shadow .15s ease;
    }
    .quickbar a:hover {
        border-color:#bfdbfe;
        background:#f8fbff;
        color:var(--primary);
    }
    .quickbar a.active {
        background:linear-gradient(180deg,#eff6ff 0%, #dbeafe 100%);
        color:var(--primary);
        border-color:#93c5fd;
        box-shadow:0 10px 18px rgba(37,99,235,.10);
    }
    .section-chip {
        background:var(--primary-soft);
        color:var(--primary);
        border-color:#bfdbfe;
    }
    .wrap {
        width:min(100%,1220px);
        margin:0 auto;
        padding:clamp(14px,2vw,20px);
    }

    .page-meta {
        display:flex;
        flex-direction:column;
        gap:12px;
        margin-bottom:16px;
    }
    .breadcrumbs {
        display:flex;
        flex-wrap:wrap;
        gap:8px;
        align-items:center;
        color:var(--muted);
        font-size:13px;
        font-weight:700;
    }
    .breadcrumbs a {
        color:var(--muted);
        text-decoration:none;
    }
    .breadcrumbs a:hover {
        color:var(--primary);
    }
    .breadcrumb-sep {
        color:#94a3b8;
    }
    .breadcrumbs .current {
        color:var(--text);
    }
    .page-status {
        display:flex;
        flex-wrap:wrap;
        gap:8px;
    }
    .status-pill {
        display:inline-flex;
        align-items:center;
        gap:6px;
        padding:8px 12px;
        border-radius:999px;
        background:#fff;
        border:1px solid var(--line);
        color:#334155;
        font-size:12px;
        font-weight:800;
        box-shadow:var(--shadow-soft);
    }
    .toast-stack {
        position:fixed;
        right:18px;
        bottom:18px;
        z-index:60;
        display:flex;
        flex-direction:column;
        gap:10px;
        width:min(360px, calc(100vw - 32px));
    }
    .toast {
        display:flex;
        gap:10px;
        align-items:flex-start;
        padding:14px 16px;
        border-radius:16px;
        border:1px solid var(--line);
        background:#fff;
        box-shadow:0 18px 32px rgba(15, 23, 42, .14);
        animation:toast-in .22s ease;
    }
    .toast-success { border-color:rgba(22,163,74,.22); background:#f0fdf4; }
    .toast-error { border-color:rgba(220,38,38,.22); background:#fef2f2; }
    .toast-info { border-color:rgba(2,132,199,.22); background:#eff6ff; }
    .toast-icon {
        width:24px;
        height:24px;
        border-radius:999px;
        display:inline-flex;
        align-items:center;
        justify-content:center;
        font-size:12px;
        font-weight:800;
        flex:none;
    }
    .toast-success .toast-icon { background:#dcfce7; color:#166534; }
    .toast-error .toast-icon { background:#fee2e2; color:#991b1b; }
    .toast-info .toast-icon { background:#dbeafe; color:#1d4ed8; }
    .toast-text {
        display:flex;
        flex-direction:column;
        gap:4px;
    }
    .toast-title {
        font-size:13px;
        font-weight:800;
        color:var(--text);
    }
    .toast-message {
        font-size:13px;
        color:#475569;
        line-height:1.45;
    }
    .toast-close {
        margin-left:auto;
        border:0;
        background:transparent;
        color:#64748b;
        cursor:pointer;
        font-size:16px;
        line-height:1;
        padding:0;
    }
    @keyframes toast-in {
        from { opacity:0; transform:translateY(12px); }
        to { opacity:1; transform:translateY(0); }
    }
     .cards {
        display:grid;
        grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
        gap:16px;
        margin-bottom:20px;
    }
    .card,.panel,.side-box {
        background:var(--panel);
        border:1px solid var(--line);
        border-radius:20px;
        box-shadow:var(--shadow-soft);
        min-width:0;
    }
    .card {
        padding:16px;
    }
    .card-link {
        display:block;
        text-decoration:none;
        color:inherit;
        cursor:pointer;
        transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease, background-color .15s ease;
        position:relative;
        overflow:hidden;
    }
    .card-link::after {
        content:"";
        position:absolute;
        inset:auto -40px -52px auto;
        width:120px;
        height:120px;
        background:radial-gradient(circle, rgba(37,99,235,.13), transparent 70%);
        pointer-events:none;
    }
    .card-link:hover {
        transform:translateY(-3px);
        border-color:#93c5fd;
        box-shadow:0 18px 30px rgba(37,99,235,.12);
    }
    .card-link.active {
        border-color:#60a5fa;
        background:linear-gradient(180deg, #f8fbff 0%, #eff6ff 100%);
        box-shadow:0 18px 30px rgba(37,99,235,.14);
    }
    .label {
        font-size:13px;
        color:var(--muted);
        margin-bottom:10px;
        font-weight:700;
    }
    .value {
        font-size:30px;
        font-weight:800;
        letter-spacing:-0.03em;
    }
    .value-sub {
        font-size:12px;
        color:var(--muted);
        margin-top:8px;
    }
    .panel-head {
        padding:16px 18px;
        border-bottom:1px solid #e8eef5;
        display:flex;
        justify-content:space-between;
        align-items:flex-start;
        gap:12px;
    }
    .panel-head h2,.panel-head h3 {
        margin:0;
        font-size:22px;
        line-height:1.15;
    }
    .panel-head p {
        margin:7px 0 0;
        font-size:13px;
        color:var(--muted);
    }
    .panel-head-actions {
        display:flex;
        align-items:center;
        gap:10px;
        flex-wrap:wrap;
        justify-content:flex-end;
        margin-left:auto;
    }
    .head-control {
        display:flex;
        align-items:center;
        gap:8px;
        white-space:nowrap;
        font-size:13px;
        color:#475569;
        font-weight:700;
        background:#f8fbff;
        border:1px solid #dbe4ee;
        border-radius:14px;
        padding:8px 10px;
    }
    .head-control select {
        width:auto;
        min-width:88px;
        padding:8px 10px;
        border-radius:10px;
        background:#fff;
    }
    .head-count {
        font-size:12px;
        color:var(--muted);
        white-space:nowrap;
        font-weight:700;
    }
    .panel-body { padding:18px; }
    .home-grid { display:grid; grid-template-columns:minmax(290px,340px) minmax(0,1fr); gap:16px; align-items:start; }
    .content-grid { display:grid; grid-template-columns:minmax(0,1.3fr) minmax(300px,.8fr); gap:16px; align-items:start; }
    .two-col { display:grid; grid-template-columns:minmax(240px,280px) minmax(0,1fr); gap:18px; }
    .hero-panel {
        background:linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,251,255,.98));
        border:1px solid var(--line);
        border-radius:20px;
        padding:18px;
        margin-bottom:18px;
        box-shadow:var(--shadow);
    }
    .hero-grid {
        display:grid;
        grid-template-columns:minmax(0,1.4fr) minmax(280px,.8fr);
        gap:18px;
        align-items:center;
    }
    .hero-title {
        font-size:26px;
        line-height:1.15;
        font-weight:800;
        margin:0;
        letter-spacing:-0.03em;
    }
    .hero-copy {
        margin:10px 0 0;
        color:#475569;
        font-size:13px;
        line-height:1.6;
        max-width:920px;
    }
    .hero-metrics {
        display:grid;
        grid-template-columns:repeat(2,minmax(0,1fr));
        gap:12px;
    }
    .hero-metric {
        padding:14px;
        border-radius:18px;
        background:var(--panel-soft);
        border:1px solid #dbeafe;
    }
    .hero-metric-label {
        font-size:12px;
        color:#64748b;
        font-weight:700;
        margin-bottom:8px;
    }
    .hero-metric-value {
        font-size:22px;
        font-weight:800;
        color:#0f172a;
    }
    .hero-metric-note {
        font-size:12px;
        color:#64748b;
        margin-top:4px;
    }
    .form-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; }
    .actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:18px; align-items:end; }
    .subtabs { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; }
    .subtabs a,.subtabs span { text-decoration:none; padding:10px 14px; border-radius:12px; background:#fff; border:1px solid #d1dbe8; color:var(--text); font-size:13px; font-weight:800; box-shadow:var(--shadow-soft); }
    .subtabs a:hover { color:var(--primary); border-color:#bfdbfe; background:#f8fbff; }
    .subtabs .active { background:linear-gradient(180deg,#eff6ff 0%, #dbeafe 100%); color:var(--primary); border-color:#93c5fd; }
    label { display:block; margin-bottom:6px; font-size:13px; font-weight:700; color:#374151; }
    input,select,textarea {
        width:100%;
        border:1px solid var(--line-strong);
        border-radius:12px;
        padding:11px 12px;
        font-size:14px;
        background:white;
        color:#0f172a;
    }
    input:focus, select:focus, textarea:focus {
        outline:none;
        border-color:#60a5fa;
        box-shadow:0 0 0 4px rgba(59,130,246,.12);
    }
    textarea { min-height:90px; resize:vertical; }
    .btn {
        display:inline-block;
        text-decoration:none;
        border:1px solid transparent;
        border-radius:12px;
        padding:11px 16px;
        font-weight:800;
        cursor:pointer;
        font-size:14px;
        transition:transform .12s ease, box-shadow .12s ease, border-color .12s ease;
    }
    .btn:hover { transform:translateY(-1px); }
    .btn-primary { background:var(--primary); color:white; box-shadow:0 10px 18px rgba(37,99,235,.18); }
    .btn-primary:hover, .btn-primary:focus-visible { background:#1e40af; }
    .btn-green { background:var(--green); color:white; }
    .btn-green:hover, .btn-green:focus-visible { background:#15803d; }
    .btn-white { background:white; color:var(--text); border-color:#c8d0da; }
    .btn-white:hover, .btn-white:focus-visible { color:var(--primary); border-color:#93c5fd; background:#f8fbff; }
    .btn:active { transform:translateY(0); }
    .btn.is-active { background:linear-gradient(180deg,#eff6ff 0%, #dbeafe 100%); color:var(--primary); border-color:#93c5fd; }
    .photo-box { height:220px; border:2px dashed #cbd5e1; border-radius:16px; display:flex; align-items:center; justify-content:center; background:#f8fafc; color:var(--muted); font-weight:bold; }
    .table-scroll {
        overflow:auto;
        width:100%;
        scrollbar-width:thin;
        scrollbar-color:#94a3b8 #e2e8f0;
        cursor:grab;
        user-select:none;
        -webkit-user-select:none;
        border:1px solid #e8eef5;
        border-radius:16px;
        background:#fff;
    }
    .table-scroll.is-dragging { cursor:grabbing; }
    table { width:100%; border-collapse:collapse; table-layout:auto; min-width:780px; }
    th,td {
        border-top:1px solid #edf1f5;
        padding:13px 12px;
        text-align:left;
        font-size:14px;
        vertical-align:middle;
        white-space:nowrap;
    }
    tr:hover td { background:#fbfdff; }
    th {
        background:#f6f9fc;
        color:#334155;
        font-weight:800;
        position:sticky;
        top:0;
        z-index:1;
    }
    .badge { display:inline-block; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:800; white-space:nowrap; }
    .green { background:#dcfce7; color:#166534; } .blue { background:#dbeafe; color:#1d4ed8; } .yellow { background:#fef3c7; color:#92400e; } .orange { background:#ffedd5; color:#9a3412; } .sky { background:#e0f2fe; color:#0369a1; } .red { background:#fee2e2; color:#b91c1c; } .gray { background:#e5e7eb; color:#374151; }
    .muted { color:var(--muted); font-size:13px; }
    .notice {
        background:linear-gradient(180deg,#f8fbff,#eff6ff);
        color:#1e3a8a;
        border:1px solid #bfdbfe;
        border-radius:16px;
        padding:14px 16px;
        margin-bottom:16px;
        font-size:14px;
        box-shadow:var(--shadow-soft);
    }
    .score-box {
        display:grid;
        gap:14px;
        min-width:0;
        padding:18px;
        border-radius:18px;
        background:linear-gradient(180deg,#ffffff,#f8fbff);
        border:1px solid #e5edf7;
    }
    .score-header {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:12px;
        padding-bottom:4px;
        border-bottom:1px solid #e8eef5;
    }
    .score-title {
        font-size:18px;
        font-weight:800;
        margin:0;
    }
    .score-chip {
        display:inline-flex;
        align-items:center;
        gap:6px;
        padding:6px 10px;
        background:#eef6ff;
        border:1px solid #cfe2ff;
        border-radius:999px;
        color:#1d4ed8;
        font-size:12px;
        font-weight:800;
    }
    .score-summary {
        display:grid;
        grid-template-columns:repeat(3,minmax(0,1fr));
        gap:10px;
    }
    .score-summary-card {
        padding:14px;
        border-radius:16px;
        background:#fff;
        border:1px solid #e5edf7;
    }
    .score-summary-label {
        font-size:12px;
        color:#64748b;
        font-weight:700;
        margin-bottom:6px;
    }
    .score-summary-value {
        font-size:24px;
        font-weight:800;
        letter-spacing:-0.03em;
    }
    .score-row { display:grid; grid-template-columns:92px minmax(0,1fr) 52px; gap:10px; align-items:center; }
    .score-label { font-size:13px; font-weight:800; color:#334155; }
    .bar-wrap { width:100%; height:20px; background:#e5e7eb; border-radius:999px; overflow:hidden; position:relative; }
    .bar-fill { height:100%; border-radius:999px; }
    .bar-good { background:linear-gradient(90deg,#22c55e,#16a34a); } .bar-mid { background:linear-gradient(90deg,#60a5fa,#2563eb); } .bar-warn { background:linear-gradient(90deg,#fb923c,#ea580c); }
    .score-num { text-align:right; font-size:13px; font-weight:800; }
    .empty-score {
        padding:20px;
        border-radius:18px;
        background:#f8fafc;
        border:1px dashed #cbd5e1;
        color:#64748b;
        font-weight:700;
    }
    .legend-list {
        display:grid;
        grid-template-columns:repeat(2,minmax(0,1fr));
        gap:10px;
        margin-top:4px;
    }
    .legend-item {
        padding:12px;
        background:#fff;
        border-radius:14px;
        border:1px solid #e5edf7;
    }
    .legend-title {
        font-size:12px;
        color:#64748b;
        font-weight:700;
        margin-bottom:6px;
    }
    .legend-value {
        font-size:16px;
        font-weight:800;
    }
    .month-grid { overflow-x:auto; }
    .month-grid table th,.month-grid table td { text-align:center; min-width:42px; white-space:nowrap; }
    .month-grid table th.name-col,.month-grid table td.name-col { text-align:left; min-width:110px; position:sticky; left:0; background:white; z-index:2; }
    .month-grid table th.nation-col,.month-grid table td.nation-col { text-align:left; min-width:100px; position:sticky; left:110px; background:white; z-index:2; }
    @media (max-width:1280px) {
        .content-grid,.home-grid,.two-col,.hero-grid { grid-template-columns:1fr; }
    }
    @media (max-width:768px) {
        .wrap { padding:12px; }
        .menu,.quickbar { padding:10px 12px; gap:12px; }
        .menu a { font-size:14px; }
        .topbar { padding:16px 14px 18px; }
        .brand-title { font-size:24px; }
        th,td { font-size:13px; padding:10px 8px; }
        .score-row { grid-template-columns:76px minmax(0,1fr) 44px; }
        .score-summary { grid-template-columns:1fr; }
        .legend-list { grid-template-columns:1fr; }
        .panel-head { flex-direction:column; align-items:flex-start; }
        .panel-head-actions { width:100%; justify-content:flex-start; }
    }

    .list-toolbar {
        display:flex;
        gap:12px;
        justify-content:space-between;
        align-items:flex-end;
        flex-wrap:wrap;
        margin:0 0 16px;
        padding:14px;
        border:1px solid #dbe4ef;
        border-radius:16px;
        background:#f8fbff;
    }
    .toolbar-form {
        display:flex;
        gap:10px;
        flex-wrap:wrap;
        align-items:end;
        flex:1 1 720px;
    }
    .toolbar-form > div { min-width:140px; }
    .toolbar-search { flex:1 1 260px; min-width:220px; }
    .toolbar-actions, .toolbar-side-actions {
        display:flex;
        gap:8px;
        flex-wrap:wrap;
        align-items:center;
    }
    .toolbar-side-actions { justify-content:flex-end; }
    .pagination-wrap {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:12px;
        flex-wrap:wrap;
        margin-top:16px;
    }
    .pagination {
        display:flex;
        gap:8px;
        flex-wrap:wrap;
    }
    .pagination-link {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        min-width:38px;
        height:38px;
        border-radius:10px;
        border:1px solid var(--line);
        background:#fff;
        color:var(--text);
        text-decoration:none;
        font-weight:700;
    }
    .pagination-link.active {
        background:var(--primary);
        color:#fff;
        border-color:var(--primary);
    }
    .table-meta {
        font-size:13px;
        color:var(--muted);
        font-weight:700;
    }


.drilldown-panel{margin-top:18px;padding-top:16px;border-top:1px solid #e5e7eb;}
.drilldown-title{font-size:14px;font-weight:800;color:#0f172a;margin-bottom:8px;}
.drilldown-actions{display:flex;flex-wrap:wrap;gap:8px;}
.drilldown-hint{margin-top:8px;font-size:12px;color:#64748b;}
.drilldown-summary-row{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;}
.drill-actions-cell{white-space:nowrap;}
.table-mini-link{display:inline-flex;align-items:center;justify-content:center;padding:6px 10px;border-radius:999px;border:1px solid #dbe4f0;background:#fff;color:#1d4ed8;font-size:12px;font-weight:700;margin-right:6px;text-decoration:none;}
.table-mini-link:hover{background:#eff6ff;border-color:#bfdbfe;}
</style>
</head>
<body>
    <div class="topbar">
        <div class="topbar-inner">
            <div>
                <div class="brand-kicker">Workforce Operations Hub</div>
                <h1 class="brand-title">멀티사업자 인력·근태·급여 관리</h1>
                <p class="brand-desc">현장 운영, 출퇴근, 기록 조회, 급여 흐름을 한 화면에서 연결하는 웹 기반 관리 시스템</p>
            </div>
            <div class="topbar-meta">
                <div class="meta-pill">웹 기반 운영</div>
                <div class="meta-pill">실시간 현황 중심</div>
                <div class="meta-pill">다중 사업장 관리</div>
            </div>
        </div>
    </div>
    <div class="menu-shell">
        <div class="menu">
            <a href="/" class="{{ 'active' if active=='home' else '' }}">홈</a>
            <a href="/employees" class="{{ 'active' if active=='employees' else '' }}">직원관리</a>
            <a href="/attendance" class="{{ 'active' if active=='attendance' else '' }}">근태관리</a>
            <a href="/client-companies" class="{{ 'active' if active in ['client_companies', 'our_businesses'] else '' }}">회사관리</a>
            <a href="/payroll" class="{{ 'active' if active=='payroll' else '' }}">급여관리</a>
            <a href="/records" class="{{ 'active' if active=='records' else '' }}">기록조회</a>
            <a href="/settings" class="{{ 'active' if active=='settings' else '' }}">설정</a>
        </div>
        {% if active in ['client_companies', 'our_businesses'] %}
        <div class="quickbar">
            <a href="/our-businesses" class="{{ 'active' if active == 'our_businesses' else '' }}">사업자관리</a>
            <a href="/client-companies" class="{{ 'active' if active == 'client_companies' else '' }}">거래처관리</a>
        </div>
        {% elif quick_links %}
        <div class="quickbar">
            {% for item in quick_links %}
                <a href="{{ item.href }}" class="{{ 'active' if item.get('active') else '' }}">{{ item.label }}</a>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    <div class="wrap">
        {% if breadcrumbs or page_status %}
        <div class="page-meta">
            {% if breadcrumbs %}
            <nav class="breadcrumbs" aria-label="breadcrumb">
                {% for item in breadcrumbs %}
                    {% if not loop.first %}<span class="breadcrumb-sep">/</span>{% endif %}
                    {% if item.current %}
                        <span class="current">{{ item.label }}</span>
                    {% else %}
                        <a href="{{ item.href }}">{{ item.label }}</a>
                    {% endif %}
                {% endfor %}
            </nav>
            {% endif %}
            {% if page_status %}
            <div class="page-status">
                {% for item in page_status %}
                <span class="status-pill">{{ item }}</span>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        {% endif %}
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
            <div class="toast-stack" aria-live="polite" aria-atomic="true">
                {% for category, message in messages %}
                <div class="toast toast-{{ category if category in ['success', 'error', 'info'] else 'info' }}" data-toast>
                    <div class="toast-icon">
                        {{ '완료' if category == 'success' else '오류' if category == 'error' else '안내' }}
                    </div>
                    <div class="toast-text">
                        <div class="toast-title">
                            {{ '저장 완료' if category == 'success' else '오류 발생' if category == 'error' else '안내' }}
                        </div>
                        <div class="toast-message">{{ message }}</div>
                    </div>
                    <button class="toast-close" type="button" aria-label="닫기" data-toast-close>&times;</button>
                </div>
                {% endfor %}
            </div>
            {% endif %}
        {% endwith %}
        {{ content|safe }}</div>
<script>
(function () {
    function enableDragScroll(element) {
        if (!element) return;
        let isDown = false;
        let startX = 0;
        let startY = 0;
        let scrollLeft = 0;
        let scrollTop = 0;

        element.addEventListener("mousedown", function (event) {
            if (event.target.closest("a, button, input, select, textarea, label")) return;
            isDown = true;
            element.classList.add("is-dragging");
            startX = event.pageX - element.offsetLeft;
            startY = event.pageY - element.offsetTop;
            scrollLeft = element.scrollLeft;
            scrollTop = element.scrollTop;
        });

        window.addEventListener("mouseup", function () {
            isDown = false;
            element.classList.remove("is-dragging");
        });

        element.addEventListener("mouseleave", function () {
            isDown = false;
            element.classList.remove("is-dragging");
        });

        element.addEventListener("mousemove", function (event) {
            if (!isDown) return;
            event.preventDefault();
            const x = event.pageX - element.offsetLeft;
            const y = event.pageY - element.offsetTop;
            const walkX = x - startX;
            const walkY = y - startY;
            element.scrollLeft = scrollLeft - walkX;
            element.scrollTop = scrollTop - walkY;
        });
    }

    function enableKeepScroll() {
        const key = "simple-hr-scroll-y";
        document.querySelectorAll(".js-keep-scroll").forEach(function (element) {
            element.addEventListener("click", function () {
                try {
                    sessionStorage.setItem(key, String(window.scrollY));
                } catch (error) {}
            });
        });

        try {
            const saved = sessionStorage.getItem(key);
            if (saved !== null) {
                window.scrollTo(0, Number(saved));
                sessionStorage.removeItem(key);
            }
        } catch (error) {}
    }

    document.querySelectorAll(".js-drag-scroll").forEach(enableDragScroll);
    function enableToasts() {
        document.querySelectorAll("[data-toast]").forEach(function (toast) {
            const closeButton = toast.querySelector("[data-toast-close]");
            if (closeButton) {
                closeButton.addEventListener("click", function () {
                    toast.remove();
                });
            }
            window.setTimeout(function () {
                if (toast && toast.parentNode) {
                    toast.remove();
                }
            }, 3200);
        });
    }

    enableKeepScroll();
    enableToasts();
})();
</script>
</body>
</html>
"""


def render_page(
    title: str,
    active: str,
    content: str,
    quick_links: list[dict[str, str]] | None = None,
    breadcrumbs: list[dict[str, str | bool]] | None = None,
    page_status: list[str] | None = None,
) -> str:
    return render_template_string(
        BASE_HTML,
        title=title,
        active=active,
        content=content,
        quick_links=quick_links or [],
        breadcrumbs=breadcrumbs or build_breadcrumbs(title, active),
        page_status=page_status or build_page_status(title, active),
    )


def sort_items(items: list[Any], sort_key: str, sort_funcs: dict[str, Any], direction: str = "asc") -> list[Any]:
    key_func = sort_funcs.get(sort_key) or next(iter(sort_funcs.values()))
    reverse = direction == "desc"
    return sorted(items, key=key_func, reverse=reverse)


def paginate_items(items: list[Any], page: int, per_page: int) -> tuple[list[Any], int, int]:
    total_count = len(items)
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page = min(max(page, 1), total_pages)
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total_count, total_pages


def update_query_params(params: dict[str, Any], **changes: Any) -> str:
    merged = {key: value for key, value in params.items() if value not in (None, "", [])}
    for key, value in changes.items():
        if value in (None, ""):
            merged.pop(key, None)
        else:
            merged[key] = value
    from urllib.parse import urlencode
    query = urlencode(merged)
    return f"?{query}" if query else ""


def render_table_toolbar(
    *,
    base_path: str,
    current_params: dict[str, Any],
    search_placeholder: str,
    search_value: str,
    sort_options: list[tuple[str, str]],
    current_sort: str,
    current_direction: str,
    create_href: str | None = None,
    create_label: str | None = None,
    reset_href: str | None = None,
) -> str:
    sort_option_html = "".join(
        f'<option value="{value}" {"selected" if value == current_sort else ""}>{label}</option>'
        for value, label in sort_options
    )
    export_csv_href = f"{base_path}{update_query_params(current_params, export='csv', page=1)}"
    export_xlsx_href = f"{base_path}{update_query_params(current_params, export='xlsx', page=1)}"
    create_html = f'<a class="btn btn-primary" href="{create_href}">{create_label}</a>' if create_href and create_label else ""
    reset_html = f'<a class="btn btn-white" href="{reset_href or base_path}">초기화</a>'
    return f"""
    <div class="list-toolbar">
        <form method="get" class="toolbar-form">
            <div class="toolbar-search"><label>검색</label><input type="text" name="q" value="{search_value}" placeholder="{search_placeholder}"></div>
            <div><label>정렬</label><select name="sort">{sort_option_html}</select></div>
            <div><label>방향</label><select name="direction"><option value="asc" {"selected" if current_direction == "asc" else ""}>오름차순</option><option value="desc" {"selected" if current_direction == "desc" else ""}>내림차순</option></select></div>
            <input type="hidden" name="page" value="1">
            <div class="toolbar-actions"><button class="btn btn-white" type="submit">적용</button>{reset_html}</div>
        </form>
        <div class="toolbar-side-actions">
            <a class="btn btn-white" href="{export_csv_href}">CSV 내보내기</a>
            <a class="btn btn-white" href="{export_xlsx_href}">Excel 내보내기</a>
            {create_html}
        </div>
    </div>
    """


def render_pagination(base_path: str, current_params: dict[str, Any], page: int, total_pages: int, total_count: int) -> str:
    if total_pages <= 1:
        return f'<div class="table-meta">총 {total_count}건</div>'
    links: list[str] = []
    for target_page in range(1, total_pages + 1):
        css = "pagination-link active" if target_page == page else "pagination-link"
        href = f"{base_path}{update_query_params(current_params, page=target_page)}"
        links.append(f'<a class="{css}" href="{href}">{target_page}</a>')
    return f"""
    <div class="pagination-wrap">
        <div class="table-meta">총 {total_count}건 · {page}/{total_pages} 페이지</div>
        <div class="pagination">{''.join(links)}</div>
    </div>
    """


def build_csv_response(filename: str, headers: list[str], rows: list[list[Any]]) -> Response:
    import csv
    import io
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    data = buffer.getvalue()
    return Response(
        data,
        mimetype="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )


def build_excel_response(filename: str, sheet_name: str, headers: list[str], rows: list[list[Any]]) -> Response:
    from io import BytesIO
    from openpyxl import Workbook

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name[:31] or "Sheet1"
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'},
    )


def export_table(filename: str, sheet_name: str, headers: list[str], rows: list[list[Any]], export_format: str) -> Response | None:
    if export_format == "csv":
        return build_csv_response(filename, headers, rows)
    if export_format == "xlsx":
        return build_excel_response(filename, sheet_name, headers, rows)
    return None


def get_our_business(our_business_id: int) -> OurBusiness | None:
    return db.session.get(OurBusiness, our_business_id)


def get_our_business_name(our_business_id: int | None) -> str:
    if our_business_id is None:
        return "-"
    item = db.session.get(OurBusiness, our_business_id)
    return item.name if item else "-"


def get_client_company(client_company_id: int) -> ClientCompany | None:
    return db.session.get(ClientCompany, client_company_id)


def get_client_company_name(client_company_id: int | None) -> str:
    if client_company_id is None:
        return "-"
    item = db.session.get(ClientCompany, client_company_id)
    return item.name if item else "-"


def get_client_company_setting(client_company_id: int) -> ClientCompanySetting | None:
    return ClientCompanySetting.query.filter_by(client_company_id=client_company_id).first()


def get_client_company_payroll_setting(client_company_id: int) -> ClientCompanyPayrollSetting | None:
    return ClientCompanyPayrollSetting.query.filter_by(client_company_id=client_company_id).first()


def get_client_company_work_types(client_company_id: int) -> list[ClientCompanyWorkType]:
    return (
        ClientCompanyWorkType.query
        .filter_by(client_company_id=client_company_id, is_active=True)
        .order_by(ClientCompanyWorkType.id.asc())
        .all()
    )


def get_employee(employee_id: int) -> Employee | None:
    return db.session.get(Employee, employee_id)


def get_work_type(work_type_id: int | None) -> ClientCompanyWorkType | None:
    if work_type_id is None:
        return None
    return db.session.get(ClientCompanyWorkType, work_type_id)


def get_work_type_name(work_type_id: int | None) -> str:
    work_type = get_work_type(work_type_id)
    return work_type.name if work_type else "-"


def get_employee_documents(employee_id: int) -> list[EmployeeDocument]:
    return EmployeeDocument.query.filter_by(employee_id=employee_id).order_by(EmployeeDocument.id.desc()).all()


def get_attendance_record(employee_id: int, work_date: str) -> AttendanceRecord | None:
    return AttendanceRecord.query.filter_by(employee_id=employee_id, work_date=work_date).first()


def get_today_status(employee_id: int) -> str:
    record = get_attendance_record(employee_id, today_str())
    return record.status if record else "before_work"


def get_display_status(employee_id: int, work_date: str) -> str:
    record = get_attendance_record(employee_id, work_date)
    return record.status if record else "before_work"


def get_employees_by_client_company(client_company_id: int | None) -> list[Employee]:
    query = Employee.query
    if client_company_id is not None:
        query = query.filter_by(current_client_company_id=client_company_id)
    return query.order_by(Employee.id.asc()).all()


def count_status_for_client_company(client_company_id: int | None, work_date: str, status: str) -> int:
    return sum(
        1
        for employee in get_employees_by_client_company(client_company_id)
        if get_display_status(employee.id, work_date) == status
    )


def status_badge(status: str) -> str:
    label = ATTENDANCE_STATUS.get(status, status)
    mapping = {
        "before_work": "yellow",
        "working": "green",
        "completed": "blue",
        "hospital": "orange",
        "vacation": "sky",
        "absent": "red",
    }
    css = mapping.get(status, "gray")
    return f'<span class="badge {css}">{label}</span>'


def format_won(value: float | int) -> str:
    return f"{int(round(value)):,}"


def clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def score_bar_class(score: int) -> str:
    if score >= 80:
        return "bar-good"
    if score >= 50:
        return "bar-mid"
    return "bar-warn"


def calculate_employee_scorecard(employee_id: int | None) -> dict[str, Any]:
    if employee_id is None:
        return {"work_score": 0, "sincerity_score": 0, "stability_score": 0, "record_count": 0}

    employee = get_employee(employee_id)
    if not employee:
        return {"work_score": 0, "sincerity_score": 0, "stability_score": 0, "record_count": 0}

    records = AttendanceRecord.query.filter_by(employee_id=employee_id).order_by(AttendanceRecord.work_date.desc()).limit(60).all()
    if not records:
        return {"work_score": 50, "sincerity_score": 50, "stability_score": 50, "record_count": 0}

    completed_count = sum(1 for r in records if r.status == "completed")
    working_count = sum(1 for r in records if r.status == "working")
    hospital_count = sum(1 for r in records if r.status == "hospital")
    vacation_count = sum(1 for r in records if r.status == "vacation")
    absent_count = sum(1 for r in records if r.status == "absent")
    trouble_count = sum(1 for r in records if "무단" in (r.reason or "") or "말썽" in (r.reason or "") or "문제" in (r.reason or ""))

    total = len(records)
    productive_ratio = (completed_count + working_count * 0.7) / total
    sincerity_ratio = (completed_count + working_count + vacation_count * 0.8) / total
    stability_ratio = max(0.0, 1.0 - ((absent_count * 1.2 + trouble_count * 1.5 + hospital_count * 0.3) / total))

    overtime_bonus = min(10.0, sum(r.overtime_minutes for r in records) / 600.0)
    work_score = clamp_score(productive_ratio * 100 + overtime_bonus)
    sincerity_score = clamp_score(sincerity_ratio * 100 - absent_count * 8)
    stability_score = clamp_score(stability_ratio * 100)

    return {
        "work_score": work_score,
        "sincerity_score": sincerity_score,
        "stability_score": stability_score,
        "record_count": total,
    }


def ensure_attendance_record(employee: Employee, work_date: str) -> AttendanceRecord:
    record = get_attendance_record(employee.id, work_date)
    if record:
        return record

    record = AttendanceRecord(
        our_business_id=employee.our_business_id,
        client_company_id=employee.current_client_company_id or 0,
        employee_id=employee.id,
        work_date=work_date,
        work_type_id=employee.work_type_id,
        status="before_work",
        check_in_at="",
        check_out_at="",
        overtime_minutes=0,
        night_minutes=0,
        reason="",
        created_by="admin",
        updated_by="admin",
        created_at=today_str(),
        updated_at=today_str(),
    )
    db.session.add(record)
    db.session.commit()
    return record


def update_attendance(
    employee_id: int,
    work_date: str,
    action_type: str,
    reason: str = "",
    overtime_minutes: int = 0,
    night_minutes: int = 0,
) -> None:
    employee = get_employee(employee_id)
    if not employee or not employee.current_client_company_id:
        return

    record = ensure_attendance_record(employee, work_date)
    now_time = now_time_str()

    record.our_business_id = employee.our_business_id
    record.client_company_id = employee.current_client_company_id
    record.work_type_id = employee.work_type_id

    if action_type == "checkin":
        record.status = "working"
        record.check_in_at = record.check_in_at or now_time
        record.reason = ""
    elif action_type == "checkout":
        if not record.check_in_at:
            record.check_in_at = now_time
        record.status = "completed"
        record.check_out_at = now_time
    elif action_type == "hospital":
        record.status = "hospital"
        record.check_in_at = ""
        record.check_out_at = ""
        record.reason = reason or "병원 진료"
    elif action_type == "vacation":
        record.status = "vacation"
        record.check_in_at = ""
        record.check_out_at = ""
        record.reason = reason or "휴가"
    elif action_type == "absent":
        record.status = "absent"
        record.check_in_at = ""
        record.check_out_at = ""
        record.reason = reason or "결근"
    elif action_type == "reset":
        record.status = "before_work"
        record.check_in_at = ""
        record.check_out_at = ""
        record.reason = ""

    record.overtime_minutes = max(0, overtime_minutes)
    record.night_minutes = max(0, night_minutes)
    record.updated_by = "admin"
    record.updated_at = today_str()
    db.session.commit()


def get_month_attendance_map(employee_id: int, year: int, month: int) -> dict[int, AttendanceRecord]:
    result: dict[int, AttendanceRecord] = {}
    records = AttendanceRecord.query.filter_by(employee_id=employee_id).all()
    for record in records:
        dt = parse_date(record.work_date)
        if dt.year == year and dt.month == month:
            result[dt.day] = record
    return result


def get_day_mark(record: AttendanceRecord | None) -> str:
    if not record:
        return ""
    if record.status in {"working", "completed"}:
        return "O"
    if record.status == "hospital":
        return "H"
    if record.status == "absent":
        return "X"
    if record.status == "vacation":
        return "V"
    return ""


def calculate_payroll_for_employee(employee: Employee, year: int, month: int) -> dict[str, Any]:
    if not employee.current_client_company_id:
        return {"employee_id": employee.id, "work_days": 0, "hospital_days": 0, "absent_days": 0, "vacation_days": 0, "night_minutes": 0, "overtime_minutes": 0, "base_amount": 0, "allowance_amount": 0, "deduction_amount": 0, "final_amount": 0}

    payroll_setting = get_client_company_payroll_setting(employee.current_client_company_id)
    company_setting = get_client_company_setting(employee.current_client_company_id)
    if not payroll_setting or not company_setting:
        return {"employee_id": employee.id, "work_days": 0, "hospital_days": 0, "absent_days": 0, "vacation_days": 0, "night_minutes": 0, "overtime_minutes": 0, "base_amount": 0, "allowance_amount": 0, "deduction_amount": 0, "final_amount": 0}

    records = [r for r in AttendanceRecord.query.filter_by(employee_id=employee.id).all() if parse_date(r.work_date).year == year and parse_date(r.work_date).month == month]

    work_days = sum(1 for r in records if r.status in {"working", "completed"})
    hospital_days = sum(1 for r in records if r.status == "hospital")
    absent_days = sum(1 for r in records if r.status == "absent")
    vacation_days = sum(1 for r in records if r.status == "vacation")
    night_minutes = sum(r.night_minutes for r in records)
    overtime_minutes = sum(r.overtime_minutes for r in records)

    pay_type = employee.pay_type or payroll_setting.default_pay_type
    if pay_type == "monthly":
        base_amount = payroll_setting.base_salary
    elif pay_type == "daily":
        base_amount = work_days * payroll_setting.daily_wage
        if payroll_setting.hospital_pay_type == "paid":
            base_amount += hospital_days * payroll_setting.daily_wage
    else:
        standard_hours = company_setting.workday_standard_hours
        worked_hours = work_days * standard_hours
        if payroll_setting.hospital_pay_type == "paid":
            worked_hours += hospital_days * standard_hours
        base_amount = worked_hours * payroll_setting.hourly_wage

    night_hour_amount = (night_minutes / 60.0) * payroll_setting.hourly_wage * max(0.0, payroll_setting.night_allowance_rate - 1.0)
    overtime_hour_amount = (overtime_minutes / 60.0) * payroll_setting.hourly_wage * max(0.0, payroll_setting.overtime_allowance_rate - 1.0)
    allowance_amount = payroll_setting.meal_allowance + payroll_setting.transport_allowance + payroll_setting.position_allowance + night_hour_amount + overtime_hour_amount
    deduction_amount = absent_days * payroll_setting.absence_deduction_amount
    final_amount = base_amount + allowance_amount - deduction_amount

    return {
        "employee_id": employee.id,
        "work_days": work_days,
        "hospital_days": hospital_days,
        "absent_days": absent_days,
        "vacation_days": vacation_days,
        "night_minutes": night_minutes,
        "overtime_minutes": overtime_minutes,
        "base_amount": int(round(base_amount)),
        "allowance_amount": int(round(allowance_amount)),
        "deduction_amount": int(round(deduction_amount)),
        "final_amount": int(round(final_amount)),
    }


def render_our_business_options(selected_id: int | None = None) -> str:
    options = []
    for item in OurBusiness.query.order_by(OurBusiness.id.asc()).all():
        selected = "selected" if item.id == selected_id else ""
        use_label = "사용" if item.is_active else "미사용"
        options.append(f'<option value="{item.id}" {selected}>{item.name} ({use_label})</option>')
    return "".join(options)


def render_client_company_options(selected_id: int | None = None, our_business_id: int | None = None) -> str:
    query = ClientCompany.query
    if our_business_id is not None:
        query = query.filter_by(our_business_id=our_business_id)
    options = []
    for item in query.order_by(ClientCompany.id.asc()).all():
        selected = "selected" if item.id == selected_id else ""
        options.append(f'<option value="{item.id}" {selected}>{item.name}</option>')
    return "".join(options)


def render_work_type_options(client_company_id: int, selected_work_type_id: int | None = None) -> str:
    options = []
    for work_type in get_client_company_work_types(client_company_id):
        selected = "selected" if work_type.id == selected_work_type_id else ""
        options.append(f'<option value="{work_type.id}" {selected}>{work_type.name}</option>')
    return "".join(options)
