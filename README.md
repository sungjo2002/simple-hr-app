# simple-hr-app

배포용 전체 프로젝트 파일입니다.

- Flask + SQLAlchemy 기반
- Render 배포용 `requirements.txt`, `render.yaml` 포함
- `templates/`, `static/` 폴더 포함
- `__pycache__`, `*.pyc` 제외

현재 프로젝트는 `utils.py`의 `render_template_string()` 기반으로 화면을 렌더링하므로
`templates/`, `static/`는 구조 유지 및 향후 확장용으로 포함되어 있습니다.