"""
설문 응답 저장 및 시계열 불러오기. 저장 기간 6개월 한정.
MySQL: survey_saves (id, user_email, title, update_count, responses_json, ...)
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from db import get_conn, execute_one, execute_all, execute_insert, execute_update_delete

RETENTION_MONTHS = 6


def init_survey_db():
    """테이블은 create_tables_mysql.sql 로 생성."""
    pass


def _retention_cutoff() -> str:
    t = datetime.utcnow() - timedelta(days=RETENTION_MONTHS * 31)
    return t.strftime("%Y-%m-%d %H:%M:%S")


def save_survey(
    user_email: str,
    responses: Dict[int, int],
    required_sequences: List[int],
    excluded_sequences: Optional[List[int]] = None,
    title: Optional[str] = None,
    survey_type: Optional[str] = None,
) -> Dict[str, Any]:
    """설문 응답 저장. title 없으면 [전체설문] 또는 [간편설문랜덤] + 이메일 + 저장일시. 반환: { id, saved_at, title }"""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    if not title or not title.strip():
        prefix = "[전체설문] " if survey_type == "full" else "[간편설문랜덤] "
        title = f"{prefix}{user_email.strip().lower()} {now}"
    else:
        title = title.strip()
    responses_json = json.dumps({str(k): v for k, v in responses.items()}, ensure_ascii=False)
    required_sequences_json = json.dumps(required_sequences, ensure_ascii=False)
    excluded_sequences_json = json.dumps(excluded_sequences or [], ensure_ascii=False)
    user = user_email.strip().lower()

    with get_conn() as conn:
        row_id = execute_insert(
            conn,
            """INSERT INTO survey_saves (user_email, title, update_count, responses_json, required_sequences_json, excluded_sequences_json, created_at)
               VALUES (%s, %s, 0, %s, %s, %s, %s)""",
            (user, title, responses_json, required_sequences_json, excluded_sequences_json, now),
        )
    return {"id": row_id, "saved_at": now, "title": title}


def update_survey(
    save_id: int,
    user_email: str,
    responses: Dict[int, int],
    required_sequences: List[int],
    excluded_sequences: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """불러온 설문 수정 후 저장. 제목에 수정일시 + (자동순번) 추가. 반환: { id, saved_at, title }"""
    user_email = user_email.strip().lower()
    with get_conn() as conn:
        row = execute_one(
            conn,
            "SELECT title, update_count FROM survey_saves WHERE id = %s AND user_email = %s",
            (save_id, user_email),
        )
        if not row:
            raise ValueError("해당 저장 항목을 찾을 수 없거나 권한이 없습니다.")
        old_title = (row["title"] or "").strip()
        update_count = (row["update_count"] or 0) + 1

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    new_title = f"{old_title} [수정 {now}] ({update_count})"
    responses_json = json.dumps({str(k): v for k, v in responses.items()}, ensure_ascii=False)
    required_sequences_json = json.dumps(required_sequences, ensure_ascii=False)
    excluded_sequences_json = json.dumps(excluded_sequences or [], ensure_ascii=False)

    with get_conn() as conn:
        execute_update_delete(
            conn,
            """UPDATE survey_saves SET title = %s, update_count = %s, responses_json = %s, required_sequences_json = %s, excluded_sequences_json = %s, created_at = %s
               WHERE id = %s AND user_email = %s""",
            (new_title, update_count, responses_json, required_sequences_json, excluded_sequences_json, now, save_id, user_email),
        )
    return {"id": save_id, "saved_at": now, "title": new_title}


def list_saved(user_email: str, q: Optional[str] = None) -> List[Dict[str, Any]]:
    """6개월 이내 저장 목록. q 있으면 title LIKE %q% 필터. [{ id, saved_at, title }, ...] 최신순."""
    cutoff = _retention_cutoff()
    user = user_email.strip().lower()
    with get_conn() as conn:
        if q and q.strip():
            search = f"%{q.strip()}%"
            rows = execute_all(
                conn,
                "SELECT id, created_at, title FROM survey_saves WHERE user_email = %s AND created_at >= %s AND title LIKE %s ORDER BY created_at DESC",
                (user, cutoff, search),
            )
        else:
            rows = execute_all(
                conn,
                "SELECT id, created_at, title FROM survey_saves WHERE user_email = %s AND created_at >= %s ORDER BY created_at DESC",
                (user, cutoff),
            )
    return [{"id": r["id"], "saved_at": r["created_at"], "title": (r.get("title") or "").strip()} for r in rows]


def _survey_diagnosis_conditions(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    q: Optional[str] = None,
    user_email: Optional[str] = None,
) -> tuple:
    """설문진단 조회 공통 조건. (conditions 리스트, args 리스트) 반환."""
    conditions = ["1=1"]
    args: List[Any] = []
    if date_from:
        conditions.append("created_at >= %s")
        args.append(date_from + " 00:00:00")
    if date_to:
        conditions.append("created_at <= %s")
        args.append(date_to + " 23:59:59")
    if q and q.strip():
        conditions.append("title LIKE %s")
        args.append(f"%{q.strip()}%")
    if user_email and user_email.strip():
        conditions.append("user_email LIKE %s")
        args.append(f"%{user_email.strip()}%")
    return conditions, args


def list_saved_all(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    q: Optional[str] = None,
    user_email: Optional[str] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    """전체 사용자 설문 저장 목록 (관리자용). date_from, date_to: 'YYYY-MM-DD' 형식. user_email: 사용자 아이디(이메일) 필터."""
    conditions, args = _survey_diagnosis_conditions(date_from, date_to, q, user_email)
    args.append(limit)
    with get_conn() as conn:
        sql = f"""SELECT id, user_email, title, created_at FROM survey_saves
                  WHERE {' AND '.join(conditions)} ORDER BY created_at DESC LIMIT %s"""
        rows = execute_all(conn, sql, tuple(args))
    return [
        {"id": r["id"], "user_email": r.get("user_email"), "title": (r.get("title") or "").strip(), "created_at": r.get("created_at")}
        for r in rows
    ]


def get_survey_diagnosis_stats(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    q: Optional[str] = None,
    user_email: Optional[str] = None,
) -> Dict[str, int]:
    """설문진단 통계: 현재 조건 총 건수, 최근 7일 진단 건수. 반환: { total_count, last_7_days_count }."""
    from datetime import datetime, timedelta
    conditions, args = _survey_diagnosis_conditions(date_from, date_to, q, user_email)
    cutoff_7 = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        sql_total = f"SELECT COUNT(*) AS cnt FROM survey_saves WHERE {' AND '.join(conditions)}"
        row_total = execute_one(conn, sql_total, tuple(args))
        conditions_7 = conditions + ["created_at >= %s"]
        args_7 = args + [cutoff_7]
        sql_7 = f"SELECT COUNT(*) AS cnt FROM survey_saves WHERE {' AND '.join(conditions_7)}"
        row_7 = execute_one(conn, sql_7, tuple(args_7))
    return {
        "total_count": row_total["cnt"] if row_total else 0,
        "last_7_days_count": row_7["cnt"] if row_7 else 0,
    }


def get_saved(user_email: str, save_id: int, *, skip_user_check: bool = False) -> Optional[Dict[str, Any]]:
    """한 건 조회. 반환: { responses, required_sequences, excluded_sequences, saved_at, title }.
    skip_user_check=True 시 관리자용으로 user_email 무시하고 id만으로 조회."""
    cutoff = _retention_cutoff()
    user = (user_email or "").strip().lower()
    with get_conn() as conn:
        if skip_user_check:
            row = execute_one(
                conn,
                "SELECT responses_json, required_sequences_json, excluded_sequences_json, created_at, title FROM survey_saves WHERE id = %s AND created_at >= %s",
                (save_id, cutoff),
            )
        else:
            row = execute_one(
                conn,
                "SELECT responses_json, required_sequences_json, excluded_sequences_json, created_at, title FROM survey_saves WHERE id = %s AND user_email = %s AND created_at >= %s",
                (save_id, user, cutoff),
            )
    if not row:
        return None
    try:
        responses_raw = json.loads(row["responses_json"]) if row["responses_json"] else {}
        responses = {int(k): v for k, v in responses_raw.items()}
        required_sequences = json.loads(row["required_sequences_json"]) if row["required_sequences_json"] else []
        excluded_sequences = json.loads(row["excluded_sequences_json"]) if row["excluded_sequences_json"] else []
    except Exception:
        responses = {}
        required_sequences = []
        excluded_sequences = []
    title = (row.get("title") or "").strip()
    return {
        "responses": responses,
        "required_sequences": required_sequences,
        "excluded_sequences": excluded_sequences,
        "saved_at": row["created_at"],
        "title": title,
    }
