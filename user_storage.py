"""
회원 등록 저장. MySQL: users (id, email, password_hash, created_at, name, gender, age, occupation, sleep_hours, meal_habit, bowel_habit, exercise_habit)
"""
import hashlib
import sqlite3
from datetime import datetime
import re
from typing import List, Dict, Any, Optional, Union

import pymysql
from db import get_conn, execute_one, execute_all, execute_insert, execute_update_delete

SALT = "sbi_user_salt_v1"

# 이메일 형식 정규식 (일반적인 형식)
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# 일회용·가상 이메일 도메인 (소문자, @ 뒤 부분 매칭)
_DISPOSABLE_DOMAINS = frozenset([
    "tempmail.com", "temp-mail.org", "guerrillamail.com", "guerrillamail.info",
    "10minutemail.com", "10minutemail.net", "mailinator.com", "throwaway.email",
    "fakeinbox.com", "yopmail.com", "getnada.com", "trashmail.com",
    "mailnesia.com", "sharklasers.com", "grr.la", "guerrillamail.org",
    "tmpeml.com", "dispostable.com", "maildrop.cc", "tempail.com",
])


def _validate_email(email: str) -> None:
    """이메일 형식 및 가상/일회용 여부 검사. 문제 시 ValueError."""
    e = (email or "").strip().lower()
    if not e:
        raise ValueError("이메일을 입력해 주세요.")
    if len(e) > 254:
        raise ValueError("이메일 주소가 너무 깁니다.")
    if not _EMAIL_RE.match(e):
        raise ValueError("올바른 이메일 형식이 아닙니다. 예: name@example.com")
    domain = e.split("@")[-1] if "@" in e else ""
    if domain in _DISPOSABLE_DOMAINS:
        raise ValueError("일회용·가상 이메일은 사용할 수 없습니다. 실제 사용 중인 이메일 주소를 입력해 주세요.")


PROFILE_KEYS = ("name", "gender", "age", "occupation", "nationality", "sleep_hours", "sleep_hours_label", "sleep_quality", "meal_habit", "bowel_habit", "exercise_habit")


def _hash_password(password: str) -> str:
    return hashlib.sha256((SALT + password).encode()).hexdigest()


def init_user_db():
    """테이블은 create_tables_mysql.sql 로 생성. 필요 시 여기서 CREATE TABLE IF NOT EXISTS 호출 가능."""
    pass


def register(
    email: str,
    password: str,
    name: Optional[str] = None,
    gender: Optional[str] = None,
    age: Optional[int] = None,
    occupation: Optional[str] = None,
    nationality: Optional[str] = None,
    sleep_hours: Optional[Union[float, str]] = None,
    sleep_quality: Optional[str] = None,
    meal_habit: Optional[str] = None,
    bowel_habit: Optional[str] = None,
    exercise_habit: Optional[str] = None,
) -> Dict[str, Any]:
    """회원 등록. 이메일 중복 시 예외. 프로필(이름·성별·연령·직업·국적·수면·수면질·식사·배변·운동) 필수."""
    email = email.strip().lower()
    _validate_email(email)
    if not password:
        raise ValueError("비밀번호를 입력하세요.")
    if len(password) < 4:
        raise ValueError("비밀번호는 4자 이상이어야 합니다.")
    # 프로필 필수 검증
    if not (name or "").strip():
        raise ValueError("사용자 이름을 입력하세요.")
    if not (gender or "").strip():
        raise ValueError("성별을 선택하세요.")
    if age is None:
        raise ValueError("연령을 입력하세요.")
    if not (occupation or "").strip():
        raise ValueError("직업을 입력하세요.")
    if not (nationality or "").strip():
        raise ValueError("국적을 선택하세요.")
    sleep_val = sleep_hours
    sleep_label = (sleep_hours if isinstance(sleep_hours, str) else None) or None
    sleep_num = sleep_hours if isinstance(sleep_hours, (int, float)) else None
    if not sleep_label and sleep_num is None:
        raise ValueError("수면시간을 선택하세요.")
    if not (sleep_quality or "").strip():
        raise ValueError("수면의 질을 선택하세요.")
    if not (meal_habit or "").strip():
        raise ValueError("식사습관을 선택하세요.")
    if not (bowel_habit or "").strip():
        raise ValueError("배변습관을 선택하세요.")
    if not (exercise_habit or "").strip():
        raise ValueError("운동습관을 선택하세요.")
    pw_hash = _hash_password(password)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        try:
            row_id = execute_insert(
                conn,
                """INSERT INTO users (email, password_hash, created_at, name, gender, age, occupation, nationality, sleep_hours, sleep_hours_label, sleep_quality, meal_habit, bowel_habit, exercise_habit)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    email, pw_hash, now,
                    (name or "").strip() or None,
                    (gender or "").strip() or None,
                    age if age is not None else None,
                    (occupation or "").strip() or None,
                    (nationality or "").strip() or None,
                    sleep_num,
                    (sleep_label or "").strip() or None,
                    (sleep_quality or "").strip() or None,
                    (meal_habit or "").strip() or None,
                    (bowel_habit or "").strip() or None,
                    (exercise_habit or "").strip() or None,
                ),
            )
            return {"id": row_id, "email": email, "created_at": now}
        except (pymysql.IntegrityError, sqlite3.IntegrityError):
            raise ValueError("이미 등록된 이메일입니다.")
        except Exception as e:
            if "UNIQUE constraint" in str(e) or "Duplicate entry" in str(e):
                raise ValueError("이미 등록된 이메일입니다.")
            if "no such column" in str(e).lower() or "unknown column" in str(e).lower():
                try:
                    row_id = execute_insert(
                        conn,
                        "INSERT INTO users (email, password_hash, created_at, name, gender, age, occupation, sleep_hours, meal_habit, bowel_habit, exercise_habit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (email, pw_hash, now, (name or "").strip() or None, (gender or "").strip() or None, age, (occupation or "").strip() or None, sleep_num, (meal_habit or "").strip() or None, (bowel_habit or "").strip() or None, (exercise_habit or "").strip() or None),
                    )
                    return {"id": row_id, "email": email, "created_at": now}
                except Exception:
                    row_id = execute_insert(conn, "INSERT INTO users (email, password_hash, created_at) VALUES (%s, %s, %s)", (email, pw_hash, now))
                    return {"id": row_id, "email": email, "created_at": now}
            raise


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """이메일로 회원 조회. 없으면 None. 프로필 컬럼 있으면 포함."""
    email = email.strip().lower()
    with get_conn() as conn:
        try:
            row = execute_one(
                conn,
                """SELECT id, email, password_hash, created_at, name, gender, age, occupation, nationality, sleep_hours, sleep_hours_label, sleep_quality, meal_habit, bowel_habit, exercise_habit
                   FROM users WHERE email = %s""",
                (email,),
            )
        except Exception:
            try:
                row = execute_one(conn, "SELECT id, email, password_hash, created_at, name, gender, age, occupation, sleep_hours, sleep_hours_label, sleep_quality, meal_habit, bowel_habit, exercise_habit FROM users WHERE email = %s", (email,))
            except Exception:
                row = execute_one(conn, "SELECT id, email, password_hash, created_at FROM users WHERE email = %s", (email,))
    if not row:
        return None
    return _row_to_user_dict(row)


def _row_to_user_dict(row: dict) -> dict:
    out = {"id": row["id"], "email": row["email"], "password_hash": row.get("password_hash"), "created_at": row.get("created_at")}
    for k in PROFILE_KEYS:
        if k in row:
            out[k] = row[k]
    # API/프론트에는 sleep_hours 하나로: 레이블 우선
    if row.get("sleep_hours_label"):
        out["sleep_hours"] = row["sleep_hours_label"]
    return out


def get_user_detail_for_admin(email: str) -> Optional[Dict[str, Any]]:
    """관리자용: 로그인 정보 + 회원 프로필 전체. password_hash 제외하고 반환."""
    u = get_user_by_email(email)
    if not u:
        return None
    u.pop("password_hash", None)
    return u


def check_email_for_register(email: str) -> Dict[str, Any]:
    """가입 전 이메일 검사: 형식·가상 여부·중복. 반환: valid(형식/가상 통과), available(미가입), message(안내문)."""
    e = (email or "").strip().lower()
    if not e:
        return {"valid": False, "available": False, "message": "이메일을 입력해 주세요."}
    try:
        _validate_email(e)
    except ValueError as err:
        return {"valid": False, "available": False, "message": str(err)}
    if get_user_by_email(e):
        return {"valid": True, "available": False, "message": "이미 등록된 이메일입니다. 로그인하거나 다른 주소를 사용하세요."}
    return {"valid": True, "available": True, "message": "사용 가능한 이메일입니다."}


def verify_password(email: str, password: str) -> bool:
    """등록 회원 비밀번호 확인."""
    u = get_user_by_email(email)
    if not u:
        return False
    return u["password_hash"] == _hash_password(password)


def list_users() -> List[Dict[str, Any]]:
    """전체 등록 회원 목록 (관리자용). name 있으면 포함."""
    with get_conn() as conn:
        try:
            rows = execute_all(conn, "SELECT id, email, created_at, name FROM users ORDER BY created_at DESC")
        except Exception:
            rows = execute_all(conn, "SELECT id, email, created_at FROM users ORDER BY created_at DESC")
    out = []
    for r in rows:
        item = {"id": r["id"], "email": r["email"], "created_at": r["created_at"]}
        if r.get("name") is not None:
            item["name"] = r["name"]
        out.append(item)
    return out


def delete_user(email: str) -> bool:
    """회원 삭제. 성공 시 True."""
    email = email.strip().lower()
    with get_conn() as conn:
        deleted = execute_update_delete(conn, "DELETE FROM users WHERE email = %s", (email,))
    return deleted > 0


def update_password(email: str, new_password: str) -> bool:
    """회원 비밀번호 변경 (가입 회원만). 성공 시 True."""
    email = email.strip().lower()
    if not new_password or len(new_password) < 4:
        raise ValueError("비밀번호는 4자 이상이어야 합니다.")
    pw_hash = _hash_password(new_password)
    with get_conn() as conn:
        n = execute_update_delete(conn, "UPDATE users SET password_hash = %s WHERE email = %s", (pw_hash, email))
    return n > 0
