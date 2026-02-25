# SBI 업그레이드 순서 (최신 기능 위주)

코드를 **가볍고 순차적으로** 유지하기 위한 기능 적용 순서입니다.

---

## 1단계: 코어 (필수)
- **인증**: 로그인·회원가입·세션 (`core.py`, `routers/auth.py`)
- **페이지**: 초기·로그인·가입·대시보드·관리자·설문 (`routers/pages.py`)
- **설문**: 문항 로드 `/items`, 제출·분석 `/analyze-sbi` (`main.py` + `data_loader`, `scoring`, `analysis_engine`)
- **DB**: SQLite 우선 (`db_config.json` → `engine: "sqlite"`, `database: "sbi.db"`)

## 2단계: 결과·PDF
- 설문 제출 후 결과 화면 (Step 2)
- `/api/generate-pdf` — 리포트 PDF 생성 (`report_generator`)

## 3단계: 저장·불러오기
- 설문 저장/목록/불러오기 (`survey_storage`, `/api/survey-save`, `survey-saved-list`, `survey-saved/{id}`)
- 대화 저장/목록/불러오기 (`chat_storage`, `/api/chat-save`, `chat-saved-list`, `chat-saved/{id}`)
- 뇌파 저장/목록/불러오기 (`eeg_storage`)

## 4단계: 관리자
- 회원 목록·삭제·비밀번호 재설정 (`/api/admin/users` 등)
- 테이블별 목록·삭제·수정 (`/api/admin/tables/*`)
- 설문진단 조회·지표 산출식 (`/api/admin/survey-diagnosis-list`, `indicator-formulas`)

## 5단계: 게시판·AI·기타
- 게시판/자료실 CRUD (`board_storage`, `/api/board-list` 등)
- AI 상담 `/api/consult` (knowledge_db, pipeline)
- 이메일 할인권 등 (`email_coupon`)

---

## 디렉터리 구조 (경량화 후)

```
main.py          # 앱 생성, 미들웨어, static, 라우터 등록, 설문·API·관리자 라우트
core.py          # get_current_user, is_admin, db_error_message, USERS_DEMO
routers/
  auth.py        # /api/register, /api/login, /api/logout, /api/me, POST /login
  pages.py       # /, /login, /register, /dashboard, /admin, /survey
db.py            # DB 연결 (SQLite/MySQL), execute_*
*_storage.py     # survey, chat, eeg, board, user_storage
data_loader.py   # 설문 CSV 로드
scoring.py       # 설문 채점
analysis_engine.py
report_generator.py
```

새 기능 추가 시 위 단계 순서를 따르면 유지보수가 수월합니다.
