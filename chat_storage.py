"""
대화 내용 저장 및 요약 불러오기. 저장 기간 6개월 한정.
MySQL: chat_saves (id, user_email, summary_title, messages_json, ai_notes_json, created_at)
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from db import get_conn, execute_one, execute_all, execute_insert

RETENTION_MONTHS = 6


def init_chat_db():
    """테이블은 create_tables_mysql.sql 로 생성."""
    pass


def _retention_cutoff() -> str:
    t = datetime.utcnow() - timedelta(days=RETENTION_MONTHS * 31)
    return t.strftime("%Y-%m-%d %H:%M:%S")


def save_chat(
    user_email: str,
    messages: List[Dict[str, str]],
    ai_consultation_notes: Optional[List[str]] = None,
    summary_title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    대화 저장. summary_title 없으면 첫 메시지 앞 30자 또는 '상담 요약 (날짜)' 사용.
    반환: { id, saved_at, summary_title }
    """
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    title = (summary_title or "").strip()
    if not title and messages:
        first_text = (messages[0].get("text") or "").strip()[:30]
        title = first_text + "…" if len((messages[0].get("text") or "")) > 30 else first_text or "상담 요약"
    if not title:
        title = "상담 요약 (" + now[:10] + ")"
    messages_json = json.dumps(messages, ensure_ascii=False)
    ai_notes_json = json.dumps(ai_consultation_notes or [], ensure_ascii=False)
    user = user_email.strip().lower()

    with get_conn() as conn:
        row_id = execute_insert(
            conn,
            "INSERT INTO chat_saves (user_email, summary_title, messages_json, ai_notes_json, created_at) VALUES (%s, %s, %s, %s, %s)",
            (user, title, messages_json, ai_notes_json, now),
        )
    return {"id": row_id, "saved_at": now, "summary_title": title}


def list_saved(user_email: str) -> List[Dict[str, Any]]:
    """6개월 이내 저장 목록. [{ id, summary_title, saved_at }, ...] 최신순."""
    cutoff = _retention_cutoff()
    user = user_email.strip().lower()
    with get_conn() as conn:
        rows = execute_all(
            conn,
            "SELECT id, summary_title, created_at FROM chat_saves WHERE user_email = %s AND created_at >= %s ORDER BY created_at DESC",
            (user, cutoff),
        )
    return [{"id": r["id"], "summary_title": r["summary_title"], "saved_at": r["created_at"]} for r in rows]


def list_saved_all(limit: int = 500) -> List[Dict[str, Any]]:
    """전체 사용자 대화 저장 목록 (관리자용). [{ id, user_email, summary_title, saved_at }, ...] 최신순."""
    cutoff = _retention_cutoff()
    with get_conn() as conn:
        rows = execute_all(
            conn,
            "SELECT id, user_email, summary_title, created_at FROM chat_saves WHERE created_at >= %s ORDER BY created_at DESC LIMIT %s",
            (cutoff, limit),
        )
    return [
        {"id": r["id"], "user_email": r.get("user_email"), "summary_title": r["summary_title"], "saved_at": r["created_at"]}
        for r in rows
    ]


def get_saved(user_email: str, save_id: int, *, skip_user_check: bool = False) -> Optional[Dict[str, Any]]:
    """한 건 조회. 6개월 초과 시 None. skip_user_check=True 시 관리자용 id만으로 조회. 반환: { messages, ai_consultation_notes, summary_title, saved_at }."""
    cutoff = _retention_cutoff()
    user = (user_email or "").strip().lower()
    with get_conn() as conn:
        if skip_user_check:
            row = execute_one(
                conn,
                "SELECT summary_title, messages_json, ai_notes_json, created_at FROM chat_saves WHERE id = %s AND created_at >= %s",
                (save_id, cutoff),
            )
        else:
            row = execute_one(
                conn,
                "SELECT summary_title, messages_json, ai_notes_json, created_at FROM chat_saves WHERE id = %s AND user_email = %s AND created_at >= %s",
                (save_id, user, cutoff),
            )
    if not row:
        return None
    try:
        messages = json.loads(row["messages_json"]) if row["messages_json"] else []
        ai_notes = json.loads(row["ai_notes_json"]) if row["ai_notes_json"] else []
    except Exception:
        messages = []
        ai_notes = []
    return {
        "messages": messages,
        "ai_consultation_notes": ai_notes,
        "summary_title": row["summary_title"],
        "saved_at": row["created_at"],
    }
