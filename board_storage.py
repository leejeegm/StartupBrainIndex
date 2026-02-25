"""
게시판·자료실 저장. MySQL: board (id, type, title, content, created_at, updated_at)
"""
from datetime import datetime
from typing import List, Dict, Any, Optional

from db import get_conn, execute_one, execute_all, execute_insert, execute_update_delete


def list_items(type_filter: Optional[str] = None, q: Optional[str] = None) -> List[Dict[str, Any]]:
    """목록. type_filter: board | resource, q: 제목/내용 검색."""
    with get_conn() as conn:
        if type_filter and type_filter in ("board", "resource"):
            if q and q.strip():
                search = f"%{q.strip()}%"
                rows = execute_all(
                    conn,
                    "SELECT id, type, title, content, created_at, updated_at FROM board WHERE type = %s AND (title LIKE %s OR content LIKE %s) ORDER BY updated_at DESC",
                    (type_filter, search, search),
                )
            else:
                rows = execute_all(
                    conn,
                    "SELECT id, type, title, content, created_at, updated_at FROM board WHERE type = %s ORDER BY updated_at DESC",
                    (type_filter,),
                )
        else:
            if q and q.strip():
                search = f"%{q.strip()}%"
                rows = execute_all(
                    conn,
                    "SELECT id, type, title, content, created_at, updated_at FROM board WHERE title LIKE %s OR content LIKE %s ORDER BY updated_at DESC",
                    (search, search),
                )
            else:
                rows = execute_all(
                    conn,
                    "SELECT id, type, title, content, created_at, updated_at FROM board ORDER BY updated_at DESC",
                    (),
                )
    return [
        {
            "id": r["id"],
            "type": r["type"],
            "title": r["title"],
            "content": r["content"] or "",
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


def get_item(item_id: int) -> Optional[Dict[str, Any]]:
    """한 건 조회."""
    with get_conn() as conn:
        row = execute_one(
            conn,
            "SELECT id, type, title, content, created_at, updated_at FROM board WHERE id = %s",
            (item_id,),
        )
    if not row:
        return None
    return {
        "id": row["id"],
        "type": row["type"],
        "title": row["title"],
        "content": row["content"] or "",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_item(type_name: str, title: str, content: str = "") -> Dict[str, Any]:
    """등록. 반환: 생성된 항목 dict."""
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with get_conn() as conn:
        row_id = execute_insert(
            conn,
            "INSERT INTO board (type, title, content, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
            (type_name, title, content, now, now),
        )
    return {
        "id": row_id,
        "type": type_name,
        "title": title,
        "content": content,
        "created_at": now,
        "updated_at": now,
    }


def update_item(item_id: int, title: Optional[str] = None, content: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """수정. 반환: 수정된 항목 또는 None."""
    item = get_item(item_id)
    if not item:
        return None
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    new_title = title if title is not None else item["title"]
    new_content = content if content is not None else item["content"]
    with get_conn() as conn:
        execute_update_delete(
            conn,
            "UPDATE board SET title = %s, content = %s, updated_at = %s WHERE id = %s",
            (new_title, new_content, now, item_id),
        )
    return {
        "id": item_id,
        "type": item["type"],
        "title": new_title,
        "content": new_content,
        "created_at": item["created_at"],
        "updated_at": now,
    }


def delete_item(item_id: int) -> bool:
    """삭제. 성공 시 True."""
    with get_conn() as conn:
        n = execute_update_delete(conn, "DELETE FROM board WHERE id = %s", (item_id,))
    return n > 0
