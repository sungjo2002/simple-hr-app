from flask import Blueprint

from utils import render_page

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
def settings_page() -> str:
    content = """
    <div class="panel">
        <div class="panel-head"><h2>설정</h2><p>권한 / 문서 / 운영 기준</p></div>
        <div class="panel-body">
            <table>
                <tr><th style="width:220px;">저장 방식</th><td>SQLite DB 파일 저장</td></tr>
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
    return render_page("설정", "settings", content)
