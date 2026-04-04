from flask import Blueprint, redirect, request, url_for

from models import ClientCompany, OurBusiness, db
from utils import render_page, today_str

businesses_bp = Blueprint("businesses", __name__)


@businesses_bp.route("/our-businesses")
def our_businesses_page() -> str:
    rows = ""
    for item in OurBusiness.query.order_by(OurBusiness.id.asc()).all():
        rows += f"""
        <tr>
            <td>{item.id}</td>
            <td><a href="/our-businesses/{item.id}">{item.name}</a></td>
            <td>{item.business_number}</td>
            <td>{item.phone}</td>
            <td>{"사용" if item.is_active else "미사용"}</td>
        </tr>
        """
    content = f"""
    <div class="panel">
        <div class="panel-head"><h2>사업자목록</h2><p>우리측 운영 사업자 관리</p></div>
        <div class="panel-body">
            <div class="actions" style="margin-top:0; margin-bottom:16px;"><a class="btn btn-primary" href="/our-businesses/new">+ 사업자등록</a></div>
            <table>
                <thead><tr><th>번호</th><th>사업자명</th><th>사업자등록번호</th><th>대표전화</th><th>사용여부</th></tr></thead>
                <tbody>{rows or '<tr><td colspan="5">데이터가 없습니다.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    quick = [{"label": "사업자목록", "href": "/our-businesses", "active": True}, {"label": "사업자등록", "href": "/our-businesses/new", "active": False}]
    return render_page("사업자관리", "our_businesses", content, quick)


@businesses_bp.route("/our-businesses/new", methods=["GET", "POST"])
def our_business_new() -> str:
    if request.method == "POST":
        item = OurBusiness(
            name=request.form["name"].strip(),
            ceo_name=request.form["ceo_name"].strip(),
            business_number=request.form["business_number"].strip(),
            phone=request.form["phone"].strip(),
            address=request.form["address"].strip(),
            business_type=request.form.get("business_type", "").strip(),
            business_item=request.form.get("business_item", "").strip(),
            email=request.form.get("email", "").strip(),
            is_active=request.form.get("is_active", "Y") == "Y",
            memo=request.form.get("memo", "").strip(),
            created_at=today_str(),
            updated_at=today_str(),
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for("businesses.our_businesses_page"))

    content = """
    <div class="panel">
        <div class="panel-head"><h2>사업자등록</h2><p>우리측 운영 사업자 등록</p></div>
        <div class="panel-body">
            <form method="post">
                <div class="form-grid">
                    <div><label>사업자명</label><input name="name" required></div>
                    <div><label>대표자명</label><input name="ceo_name" required></div>
                    <div><label>사업자등록번호</label><input name="business_number" required></div>
                    <div><label>대표전화</label><input name="phone" required></div>
                    <div><label>주소</label><input name="address" required></div>
                    <div><label>업태</label><input name="business_type"></div>
                    <div><label>종목</label><input name="business_item"></div>
                    <div><label>이메일</label><input name="email"></div>
                    <div><label>사용여부</label><select name="is_active"><option value="Y">사용</option><option value="N">미사용</option></select></div>
                    <div style="grid-column:1 / -1;"><label>메모</label><textarea name="memo"></textarea></div>
                </div>
                <div class="actions"><button class="btn btn-primary" type="submit">저장</button><a class="btn btn-white" href="/our-businesses">취소</a></div>
            </form>
        </div>
    </div>
    """
    quick = [{"label": "사업자목록", "href": "/our-businesses", "active": False}, {"label": "사업자등록", "href": "/our-businesses/new", "active": True}]
    return render_page("사업자등록", "our_businesses", content, quick)


@businesses_bp.route("/our-businesses/<int:our_business_id>")
def our_business_detail(our_business_id: int) -> str:
    item = OurBusiness.query.get_or_404(our_business_id)
    client_count = ClientCompany.query.filter_by(our_business_id=our_business_id).count()
    content = f"""
    <div class="panel">
        <div class="panel-head"><h2>사업자상세</h2><p>{item.name}</p></div>
        <div class="panel-body">
            <table>
                <tr><th style="width:220px;">사업자명</th><td>{item.name}</td></tr>
                <tr><th>대표자명</th><td>{item.ceo_name}</td></tr>
                <tr><th>사업자등록번호</th><td>{item.business_number}</td></tr>
                <tr><th>대표전화</th><td>{item.phone}</td></tr>
                <tr><th>주소</th><td>{item.address}</td></tr>
                <tr><th>업태</th><td>{item.business_type or '-'}</td></tr>
                <tr><th>종목</th><td>{item.business_item or '-'}</td></tr>
                <tr><th>이메일</th><td>{item.email or '-'}</td></tr>
                <tr><th>사용여부</th><td>{"사용" if item.is_active else "미사용"}</td></tr>
                <tr><th>거래처 수</th><td>{client_count}</td></tr>
                <tr><th>메모</th><td>{item.memo or '-'}</td></tr>
            </table>
        </div>
    </div>
    """
    quick = [{"label": "사업자목록", "href": "/our-businesses", "active": True}, {"label": "사업자등록", "href": "/our-businesses/new", "active": False}]
    return render_page("사업자상세", "our_businesses", content, quick)
