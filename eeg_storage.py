"""
Step3 뇌파 원천데이터 저장. MySQL: eeg_saves (id, user_email, title, data_json, created_at)
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from db import get_conn, execute_one, execute_all, execute_insert


def save_eeg(user_email: str, data: Dict[str, Any], title: Optional[str] = None) -> Dict[str, Any]:
    """뇌파 데이터 저장. title 없으면 '뇌파 데이터 저장일시' 형식. 반환: { id, saved_at, title }"""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    title = (title or "").strip() or f"뇌파 데이터 {user_email.strip().lower()} {now}"
    data_json = json.dumps(data, ensure_ascii=False)
    user = user_email.strip().lower()
    with get_conn() as conn:
        row_id = execute_insert(
            conn,
            "INSERT INTO eeg_saves (user_email, title, data_json, created_at) VALUES (%s, %s, %s, %s)",
            (user, title, data_json, now),
        )
    return {"id": row_id, "saved_at": now, "title": title}


def list_saved(user_email: str) -> List[Dict[str, Any]]:
    """저장 목록. [{ id, title, saved_at }, ...] 최신순."""
    user = user_email.strip().lower()
    with get_conn() as conn:
        rows = execute_all(
            conn,
            "SELECT id, title, created_at FROM eeg_saves WHERE user_email = %s ORDER BY created_at DESC",
            (user,),
        )
    return [{"id": r["id"], "title": r["title"], "saved_at": r["created_at"]} for r in rows]


def list_saved_all(limit: int = 500) -> List[Dict[str, Any]]:
    """전체 사용자 뇌파 저장 목록 (관리자용). [{ id, user_email, title, saved_at }, ...] 최신순."""
    with get_conn() as conn:
        rows = execute_all(
            conn,
            "SELECT id, user_email, title, created_at FROM eeg_saves ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
    return [
        {"id": r["id"], "user_email": r.get("user_email"), "title": r["title"], "saved_at": r["created_at"]}
        for r in rows
    ]


def get_saved(user_email: str, save_id: int, *, skip_user_check: bool = False) -> Optional[Dict[str, Any]]:
    """한 건 조회. skip_user_check=True 시 관리자용 id만으로 조회. 반환: { data, title, saved_at }."""
    user = (user_email or "").strip().lower()
    with get_conn() as conn:
        if skip_user_check:
            row = execute_one(
                conn,
                "SELECT title, data_json, created_at FROM eeg_saves WHERE id = %s",
                (save_id,),
            )
        else:
            row = execute_one(
                conn,
                "SELECT title, data_json, created_at FROM eeg_saves WHERE id = %s AND user_email = %s",
                (save_id, user),
            )
    if not row:
        return None
    try:
        data = json.loads(row["data_json"]) if row["data_json"] else {}
    except Exception:
        data = {}
    return {"data": data, "title": row["title"], "saved_at": row["created_at"]}
