"""
FastAPI 메인 애플리케이션
"""
import os
import secrets
import random
from fastapi import FastAPI, HTTPException, Request, Depends, Form, Query
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Any
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from data_loader import SurveyDataLoader
from scoring import ScoringEngine
from analysis_engine import run_combined_analysis, calculate_combined_sbi
from models import BrainWaveMetrics
from eeg_provider import MockEEGProvider
from report_generator import generate_report, report_to_dict
from email_coupon import build_coupon_email_for_result, COUPON_EMAIL_THRESHOLD

# 세션 비밀키 (배포 시 환경변수로 설정 권장)
SECRET_KEY = os.environ.get("SESSION_SECRET", secrets.token_hex(32))
# 데모용 사용자 (이메일 -> 비밀번호). 배포 시 DB 등으로 교체.
USERS_DEMO = {"user@test.com": "pass1234", "admin@test.com": "admin"}

app = FastAPI(
    title="Startup Brain Index : SBI 창업가 뇌 지수 측정",
    description="상상을 현실로, '새로이 창조하는 일'의 셀프 역량 리포트 · 설문 + 뇌파 결합 분석 API",
    version="1.1.0"
)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=86400 * 7)

# 모바일/모든 기기 접속 허용 (User-Agent 차단 없음). 응답 헤더로 명시.
@app.middleware("http")
async def allow_mobile_and_all_devices(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Allow-Mobile"] = "1"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 전역 데이터 로더 및 채점 엔진 초기화
data_loader = SurveyDataLoader()
scoring_engine = ScoringEngine(data_loader)


def get_current_user(request: Request) -> Optional[Dict]:
    """세션에서 로그인 사용자 반환. 없으면 None."""
    return request.session.get("user")


class SurveyResponse(BaseModel):
    """설문 응답 모델"""
    responses: Dict[int, int] = Field(
        ...,
        description="전체순번을 키로 하고 1~5점 점수를 값으로 하는 딕셔너리",
        example={1: 5, 2: 4, 3: 5, 4: 3, 5: 5}
    )
    excluded_sequences: Optional[List[int]] = Field(
        default=[],
        description="제외할 문항 순번 리스트 (예: [1, 2, 3])",
        example=[]
    )
    
    @field_validator('responses')
    @classmethod
    def validate_scores(cls, v):
        """점수 범위 검증 (1~5점)"""
        for seq, score in v.items():
            if not isinstance(seq, int) or not isinstance(score, int):
                raise ValueError(f"응답 데이터 형식이 올바르지 않습니다: {seq}: {score}")
            if not (1 <= score <= 5):
                raise ValueError(f"점수는 1~5점 사이여야 합니다. 순번 {seq}의 점수: {score}")
        return v

    @field_validator('excluded_sequences')
    @classmethod
    def validate_excluded_sequences(cls, v):
        """제외 순번 검증"""
        if v:
            for seq in v:
                if not isinstance(seq, int) or not (1 <= seq <= 96):
                    raise ValueError(f"제외할 순번은 1~96 사이의 정수여야 합니다: {seq}")
        return v


class SurveyResultResponse(BaseModel):
    """설문 결과 응답 모델"""
    전체평균: float
    영역별점수: List[Dict]
    사용된_문항수: int
    제외된_순번: List[int]
    메시지: str


# --- Step 2: 뇌파 결합 분석 API ---

class BrainWaveInput(BaseModel):
    """뇌파(EEG) 요약 지표 입력 (모두 선택사항)"""
    alpha: Optional[float] = None
    beta: Optional[float] = None
    theta: Optional[float] = None
    delta: Optional[float] = None
    engagement: Optional[float] = Field(None, ge=0, le=100, description="참여도 0~100")
    focus: Optional[float] = Field(None, ge=0, le=100, description="집중도 0~100")


class CombinedAnalysisRequest(BaseModel):
    """설문 + 뇌파 결합 분석 요청"""
    responses: Dict[int, int] = Field(..., description="설문 응답 {전체순번: 1~5점}")
    excluded_sequences: Optional[List[int]] = Field(default=[], description="제외 문항 순번")
    brainwave: Optional[BrainWaveInput] = Field(default=None, description="뇌파 지표 (없으면 설문만 사용)")
    survey_weight: float = Field(default=0.6, ge=0, le=1, description="설문 가중치")
    eeg_weight: float = Field(default=0.4, ge=0, le=1, description="뇌파 가중치")

    @field_validator('responses')
    @classmethod
    def validate_scores(cls, v):
        for seq, score in v.items():
            if not (1 <= score <= 5):
                raise ValueError(f"점수는 1~5 사이: 순번 {seq}")
        return v


class CombinedAnalysisResponse(BaseModel):
    """설문+뇌파 결합 분석 응답"""
    survey_sbi_score: float
    survey_sbi_normalized: float
    eeg_engagement: Optional[float] = None
    eeg_focus: Optional[float] = None
    combined_index: float
    영역별점수: List[Dict]
    사용된_문항수: int
    제외된_순번: List[int]
    message: str


# --- Step 2: SBI 통합 지수 (/analyze-sbi) ---

class AnalyzeSBIRequest(BaseModel):
    """설문 응답만 받아 가상 뇌파와 결합 분석 (동일 스키마)"""
    responses: Dict[int, int] = Field(..., description="설문 응답 {전체순번: 1~5점}")
    excluded_sequences: Optional[List[int]] = Field(default=[], description="제외 문항 순번")
    survey_mode: Optional[str] = Field(default="all", description="all=전체 96문항, selected=선택 71문항 기준")
    customer_name: Optional[str] = Field(default="고객", description="할인권 이메일 수신자 이름 (점수 이하 시 자동 발송용)")

    @field_validator("responses", mode="before")
    @classmethod
    def validate_scores(cls, v):
        # JSON에서 키가 문자열로 오는 경우 정수로 변환
        out = {}
        for seq, score in v.items():
            k = int(seq) if isinstance(seq, str) else seq
            s = int(score) if isinstance(score, str) else score
            if not (1 <= s <= 5):
                raise ValueError(f"점수는 1~5: 순번 {k}")
            out[k] = s
        return out


class DomainCombinedScoreDto(BaseModel):
    영역명: str
    survey_score: float
    survey_normalized: float
    eeg_score: float
    combined_score: float
    weight_survey: float
    weight_eeg: float
    inconsistency: bool


class AnalyzeSBIResponse(BaseModel):
    """SBI 통합 지수 산출 결과 (설문 + 가상 뇌파) + concept.md 기반 리포트"""
    survey_전체평균: float
    survey_정규화_0_100: float
    eeg_영역별: Dict[str, float]  # motivation, resilience, innovation, responsibility
    영역별_통합점수: List[DomainCombinedScoreDto]
    하위역량별_점수: Optional[List[Dict[str, Any]]] = None  # 파일 순서대로 { 하위역량, 점수_0_100 }
    통합지수_0_100: float
    inconsistency_flag: bool
    사용된_문항수: int
    제외된_순번: List[int]
    message: str
    리포트: Optional[Dict[str, Any]] = None  # concept.md 용어·로직 반영 해석
    할인권_이메일: Optional[Dict[str, Any]] = None  # 점수 이하 시: 발송_대상, 이메일_HTML, 할인코드, 추천_블로그, 추천_유튜브
    # 선택 문항 구분: 총 응답수·분석 구분
    survey_mode: Optional[str] = None
    선택_사용된_문항수: Optional[int] = None
    선택_메시지: Optional[str] = None
    전체_사용된_문항수: Optional[int] = None
    전체_메시지: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    occupation: Optional[str] = None
    nationality: Optional[str] = None
    sleep_hours: Optional[Any] = None  # str 또는 number (수면시간/레이블)
    sleep_quality: Optional[str] = None
    meal_habit: Optional[str] = None
    bowel_habit: Optional[str] = None
    exercise_habit: Optional[str] = None


@app.post("/api/register")
async def api_register(body: RegisterRequest):
    """회원 가입. 이메일·비밀번호·프로필(이름·성별·연령·직업·국적·수면·식사·배변·운동) 필수. 이메일 중복 시 400. DB 실패 시 503."""
    try:
        from user_storage import register
        out = register(
            body.email.strip(),
            body.password,
            name=body.name,
            gender=body.gender,
            age=body.age,
            occupation=body.occupation,
            nationality=body.nationality,
            sleep_hours=body.sleep_hours,
            sleep_quality=body.sleep_quality,
            meal_habit=body.meal_habit,
            bowel_habit=body.bowel_habit,
            exercise_habit=body.exercise_habit,
        )
        return {"ok": True, "email": out["email"], "created_at": out["created_at"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=_db_error_message(e))


@app.post("/api/login")
async def api_login(request: Request, body: LoginRequest):
    """로그인 (세션에 사용자 저장). 데모 계정 우선, 없으면 등록 회원 조회. DB 연결 실패 시 503."""
    email = body.email.strip().lower()
    pw = USERS_DEMO.get(email)
    if pw is None:
        try:
            from user_storage import verify_password
            if not verify_password(email, body.password):
                raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        except ImportError:
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        except Exception as e:
            raise HTTPException(status_code=503, detail=_db_error_message(e))
    elif pw != body.password:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    request.session["user"] = {"email": email, "name": email.split("@")[0]}
    return {"ok": True, "email": email}


@app.get("/api/logout")
async def api_logout(request: Request):
    """로그아웃 후 로그인 페이지로 리다이렉트"""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/api/check-email")
async def api_check_email(email: Optional[str] = Query(None)):
    """회원가입 전 이메일 검사: 형식·일회용 도메인·중복. valid, available, message, reason 반환. DB 오류 시에도 JSON으로 응답해 프론트에서 정상/경고 구분 가능."""
    try:
        from user_storage import check_email_for_register
        return check_email_for_register(email or "")
    except Exception as e:
        # DB 연결 실패 등: 200으로 응답하되 available=False, 서버 점검 안내 (신규 이메일인데 경고로 보이지 않도록)
        return {
            "valid": False,
            "available": False,
            "reason": "error",
            "message": "일시적으로 확인할 수 없습니다. 잠시 후 다시 시도하거나 관리자에게 문의해 주세요.",
        }


@app.get("/api/me")
async def api_me(request: Request):
    """현재 로그인 사용자 정보. 없으면 401. is_admin 필드 포함."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return {**user, "is_admin": is_admin(user)}


@app.get("/")
async def root(request: Request):
    """루트: 초기 화면(index). 미로그인 시 index, 로그인 시에도 초기 화면 표시 후 시작하기로 로그인 이동."""
    path_index = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.isfile(path_index):
        return FileResponse(path_index, media_type="text/html")
    raise HTTPException(status_code=404, detail="index.html not found")


@app.get("/login")
async def login_page():
    """로그인 페이지"""
    path = os.path.join(os.path.dirname(__file__), "static", "login.html")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="login.html not found")
    return FileResponse(path, media_type="text/html")


@app.get("/register")
async def register_page():
    """회원가입 페이지"""
    path = os.path.join(os.path.dirname(__file__), "static", "register.html")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="register.html not found")
    return FileResponse(path, media_type="text/html")


@app.post("/login")
async def login_submit(
    request: Request,
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    next_url: Optional[str] = Form(None, alias="next"),
):
    """폼 로그인: 세션 설정 후 next 파라미터 있으면 해당 URL로, 없으면 /dashboard로 리다이렉트."""
    email = (email or "").strip().lower()
    pw = USERS_DEMO.get(email)
    if pw is None:
        try:
            from user_storage import verify_password
            if not email or not verify_password(email, password or ""):
                return RedirectResponse(url="/login?error=1", status_code=302)
        except ImportError:
            return RedirectResponse(url="/login?error=1", status_code=302)
    elif not email or pw != (password or ""):
        return RedirectResponse(url="/login?error=1", status_code=302)
    request.session["user"] = {"email": email, "name": email.split("@")[0]}
    # 관리자 화면에서 들어온 경우( next=/admin )이고 관리자 계정이면 /admin으로
    dest = (next_url or "").strip() or "/dashboard"
    if dest.startswith("/admin") and email == "admin@test.com":
        return RedirectResponse(url="/admin", status_code=302)
    if dest.startswith("/") and not dest.startswith("//"):
        return RedirectResponse(url=dest, status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/dashboard")
async def dashboard_page(request: Request):
    """대시보드 (로그인 필요). 미로그인 시 로그인으로 리다이렉트"""
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=302)
    path = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="dashboard.html not found")
    return FileResponse(path, media_type="text/html")


def is_admin(user: Optional[Dict]) -> bool:
    return user and (user.get("email") or "").lower() == "admin@test.com"


@app.get("/admin")
async def admin_page(request: Request):
    """관리자 화면. 로그인 필요. 미로그인 시 로그인 페이지로(next=admin)."""
    if not get_current_user(request):
        return RedirectResponse(url="/login?next=/admin", status_code=302)
    path = os.path.join(os.path.dirname(__file__), "static", "admin.html")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="admin.html not found")
    return FileResponse(path, media_type="text/html")


# 회원 목록 응답용: SQL 테이블 users 컬럼명 (리스트 보기 시 변수명 노출)
USERS_TABLE_COLUMNS = ["id", "email", "created_at", "remarks"]


@app.get("/api/admin/users")
async def api_admin_users(request: Request):
    """회원 목록 (데모 계정 + 등록 회원). 관리자만. SQL 테이블 변수명(columns) 포함."""
    user = get_current_user(request)
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="관리자만 조회할 수 있습니다.")
    demo = [
        {"id": None, "email": e, "created_at": "-", "remarks": "데모", "is_demo": True}
        for e in USERS_DEMO
    ]
    try:
        from user_storage import list_users
        registered = [
            {"id": u["id"], "email": u["email"], "created_at": u.get("created_at") or "-", "remarks": "가입회원", "is_demo": False}
            for u in list_users()
        ]
    except Exception:
        registered = []
    return {
        "table": "users",
        "columns": USERS_TABLE_COLUMNS,
        "items": demo + registered,
    }


class AdminDeleteUserRequest(BaseModel):
    email: str


@app.post("/api/admin/users/delete")
async def api_admin_delete_user(request: Request, body: AdminDeleteUserRequest):
    """등록 회원 삭제. 관리자만. 데모 계정은 삭제 불가."""
    user = get_current_user(request)
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="관리자만 삭제할 수 있습니다.")
    email = (body.email or "").strip().lower()
    if email in USERS_DEMO:
        raise HTTPException(status_code=400, detail="데모 계정은 삭제할 수 없습니다.")
    try:
        from user_storage import delete_user
        if not delete_user(email):
            raise HTTPException(status_code=404, detail="해당 회원을 찾을 수 없습니다.")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AdminResetPasswordRequest(BaseModel):
    email: str
    new_password: str


@app.post("/api/admin/users/reset-password")
async def api_admin_reset_password(request: Request, body: AdminResetPasswordRequest):
    """등록 회원 비밀번호 재설정. 관리자만. 데모 계정은 변경 불가."""
    _admin_only(request)
    email = (body.email or "").strip().lower()
    if email in USERS_DEMO:
        raise HTTPException(status_code=400, detail="데모 계정 비밀번호는 이 API로 변경할 수 없습니다.")
    pw = (body.new_password or "").strip()
    if len(pw) < 4:
        raise HTTPException(status_code=400, detail="비밀번호는 4자 이상이어야 합니다.")
    try:
        from user_storage import update_password
        if not update_password(email, pw):
            raise HTTPException(status_code=404, detail="해당 회원을 찾을 수 없습니다.")
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 관리자 DB 테이블 조회/삭제/수정 (관리자만) ---
ALLOWED_ADMIN_TABLES = ("survey_saves", "chat_saves", "board", "eeg_saves", "indicator_formulas")


def _admin_only(request: Request):
    user = get_current_user(request)
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="관리자만 이용할 수 있습니다.")
    return user


@app.get("/api/admin/tables/{table_name}")
async def api_admin_table_list(request: Request, table_name: str):
    """관리자: 테이블 전체 목록 (survey_saves, chat_saves, board, eeg_saves, indicator_formulas). DB 미연결 시 200 + 빈 목록 + 안내 메시지."""
    _admin_only(request)
    if table_name not in ALLOWED_ADMIN_TABLES:
        raise HTTPException(status_code=400, detail="허용된 테이블이 아닙니다.")
    try:
        from db import get_conn, execute_all
        with get_conn() as conn:
            if table_name == "survey_saves":
                rows = execute_all(conn, "SELECT id, user_email, title, update_count, created_at FROM survey_saves ORDER BY id DESC LIMIT 500", ())
            elif table_name == "chat_saves":
                rows = execute_all(conn, "SELECT id, user_email, summary_title, created_at FROM chat_saves ORDER BY id DESC LIMIT 500", ())
            elif table_name == "board":
                rows = execute_all(conn, "SELECT id, type, title, content, created_at, updated_at FROM board ORDER BY id DESC LIMIT 500", ())
            elif table_name == "eeg_saves":
                rows = execute_all(conn, "SELECT id, user_email, title, created_at FROM eeg_saves ORDER BY id DESC LIMIT 500", ())
            elif table_name == "indicator_formulas":
                rows = execute_all(conn, "SELECT id, title, content, sort_order, created_at, updated_at FROM indicator_formulas ORDER BY sort_order, id LIMIT 500", ())
            else:
                rows = []
        return {"items": rows or [], "table": table_name}
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={"items": [], "table": table_name, "message": _db_error_message(e)},
        )


@app.delete("/api/admin/tables/{table_name}/{item_id:int}")
async def api_admin_table_delete(request: Request, table_name: str, item_id: int):
    """관리자: 테이블 행 삭제."""
    _admin_only(request)
    if table_name not in ALLOWED_ADMIN_TABLES:
        raise HTTPException(status_code=400, detail="허용된 테이블이 아닙니다.")
    try:
        from db import get_conn, execute_update_delete
        with get_conn() as conn:
            n = execute_update_delete(conn, f"DELETE FROM {table_name} WHERE id = %s", (item_id,))
        if n == 0:
            raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AdminBoardUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class AdminTitleUpdate(BaseModel):
    """제목만 수정 (survey_saves, eeg_saves)"""
    title: Optional[str] = None


class AdminChatTitleUpdate(BaseModel):
    summary_title: Optional[str] = None


@app.put("/api/admin/tables/survey_saves/{item_id:int}")
async def api_admin_survey_update(request: Request, item_id: int, body: AdminTitleUpdate):
    """관리자: 설문 저장 제목 수정."""
    _admin_only(request)
    if not (body.title and body.title.strip()):
        raise HTTPException(status_code=400, detail="title이 필요합니다.")
    try:
        from db import get_conn, execute_update_delete
        with get_conn() as conn:
            n = execute_update_delete(conn, "UPDATE survey_saves SET title = %s WHERE id = %s", (body.title.strip()[:512], item_id))
        if n == 0:
            raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
        return {"ok": True, "title": body.title.strip()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/admin/tables/chat_saves/{item_id:int}")
async def api_admin_chat_update(request: Request, item_id: int, body: AdminChatTitleUpdate):
    """관리자: 대화 저장 제목 수정."""
    _admin_only(request)
    if not (body.summary_title and body.summary_title.strip()):
        raise HTTPException(status_code=400, detail="summary_title이 필요합니다.")
    try:
        from db import get_conn, execute_update_delete
        with get_conn() as conn:
            n = execute_update_delete(conn, "UPDATE chat_saves SET summary_title = %s WHERE id = %s", (body.summary_title.strip()[:512], item_id))
        if n == 0:
            raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
        return {"ok": True, "summary_title": body.summary_title.strip()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/admin/tables/eeg_saves/{item_id:int}")
async def api_admin_eeg_update(request: Request, item_id: int, body: AdminTitleUpdate):
    """관리자: 뇌파 저장 제목 수정."""
    _admin_only(request)
    if not (body.title and body.title.strip()):
        raise HTTPException(status_code=400, detail="title이 필요합니다.")
    try:
        from db import get_conn, execute_update_delete
        with get_conn() as conn:
            n = execute_update_delete(conn, "UPDATE eeg_saves SET title = %s WHERE id = %s", (body.title.strip()[:512], item_id))
        if n == 0:
            raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
        return {"ok": True, "title": body.title.strip()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/admin/tables/board/{item_id:int}")
async def api_admin_board_update(request: Request, item_id: int, body: AdminBoardUpdate):
    """관리자: 게시판 항목 수정 저장."""
    _admin_only(request)
    try:
        import board_storage
        item = board_storage.get_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
        updated = board_storage.update_item(item_id, title=body.title, content=body.content)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 지표 산출식 (관리자 전용: 목록·조회·저장·수정·삭제) ---
class AdminIndicatorFormulaBody(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    sort_order: Optional[int] = None


@app.get("/api/admin/indicator-formulas/{item_id:int}")
async def api_admin_indicator_formula_get(request: Request, item_id: int):
    """관리자: 지표 산출식 한 건 조회."""
    _admin_only(request)
    try:
        from db import get_conn, execute_one
        with get_conn() as conn:
            row = execute_one(conn, "SELECT id, title, content, sort_order, created_at, updated_at FROM indicator_formulas WHERE id = %s", (item_id,))
        if not row:
            raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
        return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/indicator-formulas")
async def api_admin_indicator_formula_create(request: Request, body: AdminIndicatorFormulaBody):
    """관리자: 지표 산출식 새로 저장."""
    _admin_only(request)
    title = (body.title or "").strip()
    content = (body.content or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title이 필요합니다.")
    try:
        from db import get_conn, execute_insert
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sort_order = body.sort_order if body.sort_order is not None else 0
        with get_conn() as conn:
            lid = execute_insert(conn, "INSERT INTO indicator_formulas (title, content, sort_order, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)", (title[:256], content, sort_order, now, now))
        return {"ok": True, "id": lid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 지표 산출식 기본 문구 (이미지 내용)
INDICATOR_FORMULA_DEFAULT = """**설문 1~5점 → 0~100 정규화**
S_norm = (점수 − 1) ÷ 4 × 100

**영역별 통합 점수 (박사 논문 수식)**
영역점수 = (S_norm × w_s) + (E × w_e)
단, S_norm=설문 정규화(0~100), E=뇌파 지표(0~100)

**4대 영역 가중치**
· 창업공감·동기부여: w_s=0.7, w_e=0.3 → (S_norm×0.7)+(E×0.3)
· 창업위기감수·극복: w_s=0.5, w_e=0.5 → (S_norm×0.5)+(E×0.5)
· 창업두뇌활용·계발: w_s=0.6, w_e=0.4 → (S_norm×0.6)+(E×0.4)
· 주체적·창업의식: w_s=0.8, w_e=0.2 → (S_norm×0.8)+(E×0.2)

**통합 지수 (0~100)**
영역별 통합점수의 평균. 뇌파 미사용 시 설문 정규화값만 사용.

**뇌파 단일 사용 시**
combined = (survey_weight×S_norm + eeg_weight×eeg_score) ÷ (survey_weight + eeg_weight), 기본 0.6/0.4

4대 영역 (정식 명칭) 뇌파 지표 (0~100), 하위역량 12가지 점수 (파일 순서)
"""


@app.get("/api/admin/survey-diagnosis-list")
async def api_admin_survey_diagnosis_list(
    request: Request,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    q: Optional[str] = None,
):
    """관리자: 설문 저장 목록 연월일 검색 조회. DB 미연결 시 200 + 빈 목록 + 안내 메시지."""
    _admin_only(request)
    try:
        from survey_storage import list_saved_all
        items = list_saved_all(date_from=date_from, date_to=date_to, q=q)
        return {"items": items}
    except Exception as e:
        return JSONResponse(status_code=200, content={"items": [], "message": _db_error_message(e)})


@app.post("/api/admin/indicator-formulas/seed")
async def api_admin_indicator_formula_seed(request: Request):
    """관리자: 지표 산출식 기본 내용 한 건 삽입 (이미 있으면 스킵)."""
    _admin_only(request)
    try:
        from db import get_conn, execute_one, execute_insert
        from datetime import datetime
        with get_conn() as conn:
            row = execute_one(conn, "SELECT id FROM indicator_formulas LIMIT 1", ())
            if row:
                return {"ok": True, "message": "이미 항목이 있습니다.", "id": row["id"]}
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lid = execute_insert(
                conn,
                "INSERT INTO indicator_formulas (title, content, sort_order, created_at, updated_at) VALUES (%s, %s, 0, %s, %s)",
                ("지표 산출식 (기본)", INDICATOR_FORMULA_DEFAULT, now, now),
            )
        return {"ok": True, "id": lid, "message": "기본 내용이 삽입되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/admin/indicator-formulas/{item_id:int}")
async def api_admin_indicator_formula_update(request: Request, item_id: int, body: AdminIndicatorFormulaBody):
    """관리자: 지표 산출식 수정 저장."""
    _admin_only(request)
    title = (body.title or "").strip() if body.title is not None else None
    content = (body.content or "").strip() if body.content is not None else None
    sort_order = body.sort_order
    try:
        from db import get_conn, execute_one, execute_update_delete
        from datetime import datetime
        with get_conn() as conn:
            row = execute_one(conn, "SELECT id, title, content, sort_order FROM indicator_formulas WHERE id = %s", (item_id,))
            if not row:
                raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            t = title if title is not None else (row.get("title") or "")
            c = content if content is not None else (row.get("content") or "")
            so = sort_order if sort_order is not None else (row.get("sort_order") or 0)
            execute_update_delete(conn, "UPDATE indicator_formulas SET title = %s, content = %s, sort_order = %s, updated_at = %s WHERE id = %s", (t[:256], c, so, now, item_id))
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class GeneratePdfRequest(BaseModel):
    responses: Dict[int, int]
    excluded_sequences: Optional[List[int]] = []
    ai_consultation_notes: Optional[List[str]] = None


@app.post("/api/generate-pdf")
async def api_generate_pdf(body: GeneratePdfRequest):
    """설문 응답으로 PDF 보고서 생성 후 파일 반환"""
    try:
        from pipeline import run_full_pipeline
        import time
        result = run_full_pipeline(
            responses=body.responses,
            exclude_sequences=body.excluded_sequences or [],
            output_pdf_name=f"sbi_report_{int(time.time())}.pdf",
            ai_consultation_notes=body.ai_consultation_notes,
        )
        if not result.success or not result.pdf_path or not os.path.isfile(result.pdf_path):
            raise HTTPException(status_code=500, detail=result.error or "PDF 생성 실패")
        return FileResponse(result.pdf_path, media_type="application/pdf", filename="sbi_report.pdf")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ConsultRequest(BaseModel):
    """AI 상담 RAG 요청"""
    question: str = Field(..., min_length=1, description="사용자 질문")
    report_context: Optional[Dict[str, Any]] = Field(default=None, description="진단 결과(리포트, 영역별_통합점수) - 있으면 답변에 반영")


@app.post("/api/consult")
async def api_consult(body: ConsultRequest):
    """질문 추천 선택 또는 자유 질문에 대한 RAG 기반 응답. 지식 DB 검색 + 진단 결과 컨텍스트로 답변 생성."""
    try:
        from knowledge_db import init_db, search_knowledge
        init_db()
        query = (body.question or "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="질문을 입력해 주세요.")

        # RAG: 질문으로 지식 DB 검색 (TF-IDF 기반)
        retrieved = search_knowledge(query, top_k=5)
        report = (body.report_context or {}).get("리포트") or {}
        domains = (body.report_context or {}).get("영역별_통합점수") or []

        # 답변 구성: 공감·동기부여 도입 + 진단 요약 + 풍부한 안내 + 격려 마무리
        parts = []
        parts.append("감사합니다. 귀하의 관심과 질문에 진심으로 응답드리겠습니다.")
        if report.get("요약"):
            parts.append("【진단 요약】 " + (report.get("요약") or "")[:300])
        if domains:
            low = [d for d in domains if (d.get("combined_score") or 0) < 55]
            high = [d for d in domains if (d.get("combined_score") or 0) >= 65]
            if high:
                names_high = [d.get("영역명") or d.get("영역") or "" for d in high[:2] if d.get("영역명") or d.get("영역")]
                if names_high:
                    parts.append("현재 강점으로 보이는 역량은 " + ", ".join(names_high) + " 등입니다. 이 강점을 일상에서 의식적으로 활용해 보시길 권합니다.")
            if low:
                names = [d.get("영역명") or d.get("영역") or "" for d in low[:2]]
                names = [n for n in names if n]
                if names:
                    parts.append("보강이 권장되는 역량은 " + ", ".join(names) + "입니다. 뇌교육 5단계와 BOS 5법칙 중 해당 역량에 맞는 단계·법칙을 소개해 드리겠습니다.")

        if retrieved:
            parts.append("【참고 자료 기반 안내】")
            for i, row in enumerate(retrieved[:4], 1):
                snippet = (row.content or "")[:280].replace("\n", " ")
                if snippet:
                    parts.append(f"{i}. {row.title or '제목 없음'}: {snippet}…")
            parts.append("아래 역량·뇌파 시각화 패널에서 통계와 도표를 함께 보시면 이해에 도움이 됩니다. 추가로 궁금한 점이 있으시면 편하게 질문해 주세요.")
        else:
            역량별 = report.get("역량별") or []
            if 역량별:
                parts.append("【진단 해석】")
                for s in 역량별[:3]:
                    parts.append(f"· {s.get('영역명', '')}: {(s.get('해석') or '')[:150]}…")
                parts.append("진단 결과를 바탕으로 꾸준히 실천하시면 역량 지수가 점차 향상될 수 있습니다. 블로그·유튜브 링크도 참고해 주세요.")
            else:
                parts.append("귀하의 질문에 대해 진단 결과를 바탕으로 1:1 상담을 권장드립니다. 뇌교육·BOS 실천 과제는 concept.md 가이드를 참고해 주세요.")

        parts.append("앞으로도 창의·혁신·개방·공생의 마음으로 성장하시길 응원합니다.")
        answer = "\n\n".join(parts)
        sources = [{"title": r.title, "url": r.url, "snippet": (r.content or "")[:200]} for r in retrieved[:5]]
        return {"answer": answer, "sources": sources}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ChatSaveRequest(BaseModel):
    """대화 저장 요청"""
    messages: List[Dict[str, str]] = Field(..., description="[{ role, text }, ...]")
    ai_consultation_notes: Optional[List[str]] = Field(default=None)
    summary_title: Optional[str] = Field(default=None, max_length=100)


@app.post("/api/chat-save")
async def api_chat_save(request: Request, body: ChatSaveRequest):
    """대화 내용 저장. 로그인 필요. 저장 기간 6개월 한정."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        from chat_storage import save_chat
        out = save_chat(
            user_email=user.get("email", ""),
            messages=body.messages,
            ai_consultation_notes=body.ai_consultation_notes,
            summary_title=body.summary_title,
        )
        return {"saved_ok": True, **out}
    except Exception as e:
        raise HTTPException(status_code=503, detail=_db_error_message(e))


@app.get("/api/chat-saved-list")
async def api_chat_saved_list(request: Request, all_users: Optional[str] = None):
    """저장된 요약 목록 (6개월 이내). DB 미연결 시 200 + 빈 목록 + 안내 메시지."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        from chat_storage import list_saved, list_saved_all
        if is_admin(user) and all_users == "1":
            items = list_saved_all()
            return {"items": items, "retention_months": 6}
        items = list_saved(user.get("email", ""))
        return {"items": items, "retention_months": 6}
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={"items": [], "retention_months": 6, "message": _db_error_message(e)},
        )


@app.get("/api/chat-saved/{save_id:int}")
async def api_chat_saved_get(request: Request, save_id: int):
    """저장된 요약 한 건 불러오기 (6개월 이내). 로그인 필요. 관리자는 타 사용자 저장도 조회 가능."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        from chat_storage import get_saved
        data = get_saved(
            user.get("email", ""),
            save_id,
            skip_user_check=is_admin(user),
        )
        if not data:
            raise HTTPException(status_code=404, detail="저장된 내용이 없거나 보관 기간(6개월)이 지났습니다.")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=_db_error_message(e))


class SurveySaveRequest(BaseModel):
    """설문 응답 저장 요청. save_id 없이 보내면 항상 새 행 추가. title 있으면 해당 제목으로 저장."""
    responses: Dict[int, int] = Field(..., description="설문 응답 {전체순번: 1~5점}")
    required_sequences: List[int] = Field(..., description="필수 문항 순번 목록")
    excluded_sequences: Optional[List[int]] = Field(default=None)
    save_id: Optional[int] = Field(default=None, description="(미사용 권장) 있으면 기존 행 수정")
    survey_type: Optional[str] = Field(default=None, description="full=전체설문, short_random=간편설문랜덤")
    title: Optional[str] = Field(default=None, description="저장 제목. 없으면 이메일+일시 또는 survey_type 머리말")


@app.post("/api/survey-save")
async def api_survey_save(request: Request, body: SurveySaveRequest):
    """설문 응답 저장. 신규 시 제목=이메일+저장일시. 수정 시 제목에 수정일시+(자동순번)."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        email = user.get("email", "")
        excluded = body.excluded_sequences or []
        if body.save_id:
            from survey_storage import update_survey
            out = update_survey(
                save_id=body.save_id,
                user_email=email,
                responses=body.responses,
                required_sequences=body.required_sequences,
                excluded_sequences=excluded,
            )
            return {"saved_ok": True, **out}
        else:
            from survey_storage import save_survey
            out = save_survey(
                user_email=email,
                responses=body.responses,
                required_sequences=body.required_sequences,
                excluded_sequences=excluded,
                title=body.title if (body.title and body.title.strip()) else None,
                survey_type=body.survey_type if body.survey_type in ("full", "short_random") else None,
            )
        return {"saved_ok": True, **out}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=_db_error_message(e))


@app.get("/api/survey-saved-list")
async def api_survey_saved_list(
    request: Request,
    q: Optional[str] = None,
    all_users: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """저장된 설문 목록 (6개월 이내). DB 미연결 시 200 + 빈 목록 + 안내 메시지."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        from survey_storage import list_saved, list_saved_all
        email = user.get("email", "")
        if is_admin(user) and (all_users == "1" or date_from or date_to):
            items = list_saved_all(date_from=date_from, date_to=date_to, q=q)
            return {"items": items, "retention_months": 6}
        items = list_saved(email, q=q)
        return {"items": items, "retention_months": 6}
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={"items": [], "retention_months": 6, "message": _db_error_message(e)},
        )


@app.get("/api/survey-saved/{save_id:int}")
async def api_survey_saved_get(request: Request, save_id: int):
    """저장된 설문 한 건 불러오기. 로그인 필요. 관리자는 타 사용자 저장도 불러오기 가능."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        from survey_storage import get_saved
        data = get_saved(
            user.get("email", ""),
            save_id,
            skip_user_check=is_admin(user),
        )
        if not data:
            raise HTTPException(status_code=404, detail="저장된 설문이 없거나 보관 기간(6개월)이 지났습니다.")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=_db_error_message(e))


# --- Step3 뇌파 원천데이터 저장 (MySQL eeg_saves, 로그인 필요) ---
class EegSaveRequest(BaseModel):
    """뇌파 데이터 저장"""
    data: Dict[str, Any] = Field(..., description="뇌파 지표 객체 (motivation, resilience, innovation, responsibility 등)")
    title: Optional[str] = Field(default=None, max_length=500)


@app.post("/api/eeg-save")
async def api_eeg_save(request: Request, body: EegSaveRequest):
    """뇌파 원천데이터 저장. 로그인 필요."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        from eeg_storage import save_eeg
        out = save_eeg(user.get("email", ""), body.data, title=body.title)
        return {"saved_ok": True, **out}
    except Exception as e:
        raise HTTPException(status_code=503, detail=_db_error_message(e))


@app.get("/api/eeg-saved-list")
async def api_eeg_saved_list(request: Request, all_users: Optional[str] = None):
    """저장된 뇌파 목록. DB 미연결 시 200 + 빈 목록 + 안내 메시지."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        from eeg_storage import list_saved, list_saved_all
        if is_admin(user) and all_users == "1":
            items = list_saved_all()
            return {"items": items}
        items = list_saved(user.get("email", ""))
        return {"items": items}
    except Exception as e:
        return JSONResponse(status_code=200, content={"items": [], "message": _db_error_message(e)})


@app.get("/api/eeg-saved/{save_id:int}")
async def api_eeg_saved_get(request: Request, save_id: int):
    """저장된 뇌파 한 건 불러오기. 로그인 필요. 관리자는 타 사용자 저장도 조회 가능."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        from eeg_storage import get_saved
        data = get_saved(
            user.get("email", ""),
            save_id,
            skip_user_check=is_admin(user),
        )
        if not data:
            raise HTTPException(status_code=404, detail="저장된 뇌파 데이터가 없습니다.")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=_db_error_message(e))


# --- 게시판 및 자료실 (MySQL board 테이블, 로그인 필요) ---
import board_storage


def _db_error_message(e: Exception) -> str:
    """MySQL 등 DB 연결 오류 시 사용자 안내 문구. (2003), localhost 찾을 수 없음 등 모두 안내로 치환."""
    s = str(e)
    msg = s.lower()
    if (
        "2003" in s or "10061" in msg or "winerror" in msg
        or "connect" in msg or "connection" in msg or "refused" in msg
        or "mysql" in msg or "operationalerror" in msg
        or "localhost" in msg or "찾을 수 없" in s or "cannot find" in msg or "could not connect" in msg
    ):
        return "데이터베이스에 연결할 수 없습니다. MySQL 서버가 실행 중인지, DB 호스트 설정(환경변수 DB_HOST)이 맞는지 확인해 주세요."
    return s[:200]


class BoardItemCreate(BaseModel):
    """게시판/자료실 등록"""
    type: str = Field(..., description="board | resource")
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(default="", max_length=10000)


class BoardItemUpdate(BaseModel):
    """게시판/자료실 수정"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, max_length=10000)


@app.get("/api/board-list")
async def api_board_list(request: Request, type: Optional[str] = None, q: Optional[str] = None):
    """게시판·자료실 목록. DB 미연결 시 200 + 빈 목록 + 안내 메시지."""
    if not get_current_user(request):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        items = board_storage.list_items(type_filter=type, q=q)
        return {"items": items}
    except Exception as e:
        return JSONResponse(status_code=200, content={"items": [], "message": _db_error_message(e)})


@app.get("/api/board/{item_id:int}")
async def api_board_get(request: Request, item_id: int):
    """게시판·자료실 한 건 조회. 로그인 필요."""
    if not get_current_user(request):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        item = board_storage.get_item(item_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=_db_error_message(e))
    if not item:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    return item


@app.post("/api/board")
async def api_board_create(request: Request, body: BoardItemCreate):
    """게시판·자료실 등록. 로그인 필요."""
    if not get_current_user(request):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    if body.type not in ("board", "resource"):
        raise HTTPException(status_code=400, detail="type은 board 또는 resource여야 합니다.")
    try:
        item = board_storage.create_item(body.type, body.title, body.content or "")
        return item
    except Exception as e:
        raise HTTPException(status_code=503, detail=_db_error_message(e))


@app.put("/api/board/{item_id:int}")
async def api_board_update(request: Request, item_id: int, body: BoardItemUpdate):
    """게시판·자료실 수정. 로그인 필요."""
    if not get_current_user(request):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        item = board_storage.update_item(item_id, title=body.title, content=body.content)
    except Exception as e:
        raise HTTPException(status_code=503, detail=_db_error_message(e))
    if not item:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    return item


@app.delete("/api/board/{item_id:int}")
async def api_board_delete(request: Request, item_id: int):
    """게시판·자료실 삭제. 로그인 필요."""
    if not get_current_user(request):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        ok = board_storage.delete_item(item_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=_db_error_message(e))
    if not ok:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    return {"ok": True}


@app.get("/survey")
async def survey_page():
    """96문항 설문 페이지 (프로그레스 바 + 결과 대시보드)"""
    path = os.path.join(os.path.dirname(__file__), "static", "survey.html")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="survey.html not found")
    return FileResponse(path, media_type="text/html")


@app.get("/health")
async def health_check():
    """시스템 상태 확인"""
    validation = data_loader.validate_sequences()
    return {
        "status": "healthy",
        "total_items": len(data_loader.items),
        "validation": validation
    }


def _item_to_dict(item) -> dict:
    return {
        "전체순번": item.전체순번,
        "영역": item.영역,
        "하위역량": item.하위역량,
        "하위요소": item.하위요소,
        "문항보정": item.문항보정,
        "예시문항": item.예시문항,
    }


@app.get("/items")
async def get_items(order: Optional[str] = "sequence", short: Optional[int] = 0):
    """
    문항 목록 조회.
    - order: sequence(번호순, 기본) | random_domain(역량별 랜덤)
    - short: 0(전체) | 1(간편 설문: 하위요소당 2문항 랜덤)
    """
    raw = list(data_loader.items)
    if short == 1:
        # 하위요소(영역+하위역량+하위요소)별로 그룹, 그룹당 2문항 랜덤
        key_fn = lambda i: (i.영역, i.하위역량, i.하위요소)
        groups: Dict[tuple, List] = {}
        for item in raw:
            k = key_fn(item)
            if k not in groups:
                groups[k] = []
            groups[k].append(item)
        chosen = []
        for group_items in groups.values():
            if len(group_items) <= 2:
                chosen.extend(group_items)
            else:
                chosen.extend(random.sample(group_items, 2))
        chosen.sort(key=lambda x: (x.영역, x.하위역량, x.하위요소, x.전체순번))
        items_data = [_item_to_dict(i) for i in chosen]
        required_sequences = [i["전체순번"] for i in items_data]
        return {
            "total_items": len(items_data),
            "items": items_data,
            "required_sequences": required_sequences,
        }
    if order == "random_domain":
        by_domain: Dict[str, List] = {}
        for item in raw:
            d = item.영역 or "기타"
            if d not in by_domain:
                by_domain[d] = []
            by_domain[d].append(item)
        domains = list(by_domain.keys())
        random.shuffle(domains)
        out = []
        for d in domains:
            lst = list(by_domain[d])
            random.shuffle(lst)
            out.extend(lst)
        items_data = [_item_to_dict(i) for i in out]
    else:
        items_data = [_item_to_dict(i) for i in sorted(raw, key=lambda x: x.전체순번)]
    return {
        "total_items": len(items_data),
        "items": items_data,
    }


@app.post("/submit-survey", response_model=SurveyResultResponse)
async def submit_survey(survey_response: SurveyResponse):
    """
    설문 응답 제출 및 점수 계산
    
    - responses: {전체순번: 점수} 형태의 응답 딕셔너리
    - excluded_sequences: 제외할 문항 순번 리스트 (선택사항)
    """
    try:
        # 점수 계산
        result = scoring_engine.calculate_score(
            responses=survey_response.responses,
            excluded_sequences=survey_response.excluded_sequences
        )
        
        # 응답 형식 변환
        domain_scores_dict = []
        for domain_score in result.영역별점수:
            domain_scores_dict.append({
                "영역명": domain_score.영역명,
                "평균점수": domain_score.평균점수,
                "문항수": domain_score.문항수,
                "포함된_순번": domain_score.포함된_순번
            })
        
        return SurveyResultResponse(
            전체평균=result.전체평균,
            영역별점수=domain_scores_dict,
            사용된_문항수=result.사용된_문항수,
            제외된_순번=result.제외된_순번,
            메시지=f"총 {result.사용된_문항수}개 문항으로 점수 계산 완료"
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"점수 계산 중 오류 발생: {str(e)}")


@app.post("/analyze-combined", response_model=CombinedAnalysisResponse)
async def analyze_combined(body: CombinedAnalysisRequest):
    """
    설문(SBI) 응답과 뇌파(EEG) 데이터를 결합하여 통합 지수를 산출합니다.
    brainwave를 생략하면 설문 점수만으로 종합 지수(0~100)를 반환합니다.
    """
    try:
        survey_result = scoring_engine.calculate_score(
            responses=body.responses,
            excluded_sequences=body.excluded_sequences or [],
        )
        brainwave = None
        if body.brainwave:
            brainwave = BrainWaveMetrics(
                alpha=body.brainwave.alpha,
                beta=body.brainwave.beta,
                theta=body.brainwave.theta,
                delta=body.brainwave.delta,
                engagement=body.brainwave.engagement,
                focus=body.brainwave.focus,
            )
        combined = run_combined_analysis(
            survey_result,
            brainwave=brainwave,
            survey_weight=body.survey_weight,
            eeg_weight=body.eeg_weight,
        )
        domain_dicts = [
            {
                "영역명": d.영역명,
                "평균점수": d.평균점수,
                "문항수": d.문항수,
                "포함된_순번": d.포함된_순번,
            }
            for d in combined.domain_scores
        ]
        return CombinedAnalysisResponse(
            survey_sbi_score=combined.survey_sbi_score,
            survey_sbi_normalized=combined.survey_sbi_normalized,
            eeg_engagement=combined.eeg_engagement,
            eeg_focus=combined.eeg_focus,
            combined_index=combined.combined_index,
            영역별점수=domain_dicts,
            사용된_문항수=survey_result.사용된_문항수,
            제외된_순번=survey_result.제외된_순번,
            message=combined.message,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"결합 분석 오류: {str(e)}")


@app.post("/analyze-sbi", response_model=AnalyzeSBIResponse)
async def analyze_sbi(body: AnalyzeSBIRequest):
    """
    설문 응답을 받으면 즉시 가상 뇌파 데이터를 매칭해
    영역별 가중치(S·E) 적용 통합 결과(JSON)를 반환합니다.
    설문-뇌파 차이 20% 이상 역량이 있으면 inconsistency_flag=True.
    """
    try:
        survey_result = scoring_engine.calculate_score(
            responses=body.responses,
            excluded_sequences=body.excluded_sequences or [],
        )
        eeg_metrics = MockEEGProvider().get_metrics()
        combined = calculate_combined_sbi(survey_result, eeg_metrics)

        eeg_dict = {
            "motivation": eeg_metrics.motivation,
            "resilience": eeg_metrics.resilience,
            "innovation": eeg_metrics.innovation,
            "responsibility": eeg_metrics.responsibility,
        }
        excluded_set = set(body.excluded_sequences or [])
        all_items = sorted(data_loader.items, key=lambda x: x.전체순번)
        seen_sub = {}
        order_sub = []
        for it in all_items:
            key = (it.하위역량 or "").strip()
            if key and key not in seen_sub:
                seen_sub[key] = True
                order_sub.append(key)
        하위역량별_점수 = []
        for sub_name in order_sub:
            group_items = [it for it in all_items if (it.하위역량 or "").strip() == sub_name and it.전체순번 not in excluded_set]
            scores = [body.responses[it.전체순번] for it in group_items if it.전체순번 in body.responses and 1 <= body.responses[it.전체순번] <= 5]
            if scores:
                avg = sum(scores) / len(scores)
                점수_0_100 = round((avg - 1) / 4 * 100, 1)
            else:
                점수_0_100 = None
            하위역량별_점수.append({"하위역량": sub_name, "점수_0_100": 점수_0_100})
        domain_dtos = [
            DomainCombinedScoreDto(
                영역명=d.영역명,
                survey_score=d.survey_score,
                survey_normalized=d.survey_normalized,
                eeg_score=d.eeg_score,
                combined_score=d.combined_score,
                weight_survey=d.weight_survey,
                weight_eeg=d.weight_eeg,
                inconsistency=d.inconsistency,
            )
            for d in combined.영역별_통합점수
        ]

        # concept.md 기반 리포트 생성 (지수 해석, 뇌교육 단계·BOS 처방, 불일치 해석)
        report = generate_report(combined.영역별_통합점수, combined.inconsistency_flag)
        report_dict = report_to_dict(report)

        # 선택 문항 기준 / 전체 문항 기준 총 응답수 구분 (분석 결과 안내용)
        excluded_seqs = data_loader.get_excluded_sequences()
        excluded_for_selected = list(excluded_seqs) + [s for s in range(1, 97) if s not in body.responses]
        result_selected = scoring_engine.calculate_score(responses=body.responses, excluded_sequences=excluded_for_selected)
        선택_사용된_문항수 = result_selected.사용된_문항수 if result_selected.사용된_문항수 > 0 else None
        선택_메시지 = f"선택 문항 기준: 총 {result_selected.사용된_문항수}개 문항으로 계산" if 선택_사용된_문항수 else None
        excluded_for_all = [s for s in range(1, 97) if s not in body.responses]
        result_all = scoring_engine.calculate_score(responses=body.responses, excluded_sequences=excluded_for_all)
        전체_사용된_문항수 = result_all.사용된_문항수 if result_all.사용된_문항수 > 0 else None
        전체_메시지 = f"전체 문항 기준: 총 {result_all.사용된_문항수}개 문항으로 계산" if 전체_사용된_문항수 else None
        survey_mode = (body.survey_mode or "all").strip().lower() if body.survey_mode else None
        msg_combined = combined.message
        if 전체_메시지 and 선택_메시지:
            msg_combined = f"{전체_메시지}. {선택_메시지}."
        elif 선택_메시지:
            msg_combined = f"{combined.message} ({선택_메시지})"

        # 진단 점수 이하 시 1:1 상담 할인권 이메일 템플릿 생성 (블로그/유튜브 추천 + 할인코드)
        customer_name = (body.customer_name or "고객").strip() or "고객"
        coupon_payload = build_coupon_email_for_result(
            customer_name=customer_name,
            영역별_통합점수=combined.영역별_통합점수,
            통합지수_0_100=combined.통합지수_0_100,
        )
        할인권_이메일 = None
        if coupon_payload.get("발송_대상"):
            할인권_이메일 = {
                "발송_대상": True,
                "이메일_HTML": coupon_payload.get("이메일_HTML"),
                "할인코드": coupon_payload.get("할인코드"),
                "추천_블로그": coupon_payload.get("추천_블로그"),
                "추천_유튜브": coupon_payload.get("추천_유튜브"),
                "기준_점수_이하": COUPON_EMAIL_THRESHOLD,
            }

        return AnalyzeSBIResponse(
            survey_전체평균=combined.survey_전체평균,
            survey_정규화_0_100=combined.survey_정규화_0_100,
            eeg_영역별=eeg_dict,
            영역별_통합점수=domain_dtos,
            하위역량별_점수=하위역량별_점수,
            통합지수_0_100=combined.통합지수_0_100,
            inconsistency_flag=combined.inconsistency_flag,
            사용된_문항수=combined.사용된_문항수,
            제외된_순번=combined.제외된_순번,
            message=msg_combined,
            리포트=report_dict,
            할인권_이메일=할인권_이메일,
            survey_mode=survey_mode if survey_mode in ("all", "selected") else None,
            선택_사용된_문항수=선택_사용된_문항수,
            선택_메시지=선택_메시지,
            전체_사용된_문항수=전체_사용된_문항수,
            전체_메시지=전체_메시지,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SBI 통합 분석 오류: {str(e)}")


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
