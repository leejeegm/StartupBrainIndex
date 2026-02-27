"""
DB 연결 (MySQL, SQLite, PostgreSQL/Supabase).
- engine: "mysql"(기본) | "sqlite" | "postgres"
- MySQL: 환경변수 / db_config.json 의 host, user, password, database 사용.
- SQLite: MySQL 연결이 불가한 환경에서 사용. database 경로에 .db 파일 생성.
- postgres: Supabase 등. 환경변수 DATABASE_URL 또는 SUPABASE_DB_URL (postgresql://...)
"""
import os
import json
import sqlite3
from typing import Any, List, Tuple, Optional
from contextlib import contextmanager

_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "db_config.json")

# SQLite 테이블 생성 (MySQL 스키마와 동일 구조)
_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    name TEXT,
    gender TEXT,
    age INTEGER,
    occupation TEXT,
    nationality TEXT,
    sleep_hours TEXT,
    sleep_hours_label TEXT,
    sleep_quality TEXT,
    meal_habit TEXT,
    bowel_habit TEXT,
    exercise_habit TEXT
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS survey_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    title TEXT NOT NULL,
    update_count INTEGER NOT NULL DEFAULT 0,
    responses_json TEXT NOT NULL,
    required_sequences_json TEXT NOT NULL,
    excluded_sequences_json TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_survey_user ON survey_saves(user_email);
CREATE INDEX IF NOT EXISTS idx_survey_created ON survey_saves(created_at);

CREATE TABLE IF NOT EXISTS chat_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    summary_title TEXT NOT NULL,
    messages_json TEXT NOT NULL,
    ai_notes_json TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_saves(user_email);
CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_saves(created_at);

CREATE TABLE IF NOT EXISTS board (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_board_type ON board(type);

CREATE TABLE IF NOT EXISTS eeg_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    title TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_eeg_user ON eeg_saves(user_email);
CREATE INDEX IF NOT EXISTS idx_eeg_created ON eeg_saves(created_at);

CREATE TABLE IF NOT EXISTS indicator_formulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_indicator_sort ON indicator_formulas(sort_order);
"""

# PostgreSQL 스키마 (재배포 시에도 데이터 유지용 외부 DB)
_POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    name TEXT,
    gender TEXT,
    age INTEGER,
    occupation TEXT,
    nationality TEXT,
    sleep_hours TEXT,
    sleep_hours_label TEXT,
    sleep_quality TEXT,
    meal_habit TEXT,
    bowel_habit TEXT,
    exercise_habit TEXT
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS survey_saves (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    update_count INTEGER NOT NULL DEFAULT 0,
    responses_json TEXT NOT NULL,
    required_sequences_json TEXT NOT NULL,
    excluded_sequences_json TEXT,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_survey_user ON survey_saves(user_email);
CREATE INDEX IF NOT EXISTS idx_survey_created ON survey_saves(created_at);

CREATE TABLE IF NOT EXISTS chat_saves (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    summary_title TEXT NOT NULL,
    messages_json TEXT NOT NULL,
    ai_notes_json TEXT,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_saves(user_email);
CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_saves(created_at);

CREATE TABLE IF NOT EXISTS board (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_board_type ON board(type);

CREATE TABLE IF NOT EXISTS eeg_saves (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_eeg_user ON eeg_saves(user_email);
CREATE INDEX IF NOT EXISTS idx_eeg_created ON eeg_saves(created_at);

CREATE TABLE IF NOT EXISTS indicator_formulas (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_indicator_sort ON indicator_formulas(sort_order);
"""


def _init_postgres(conn) -> None:
    """PostgreSQL 테이블 생성 (없을 때만). 한 번 연결 시 자동 실행."""
    with conn.cursor() as cur:
        cur.execute(_POSTGRES_SCHEMA)
    conn.commit()
    # users 프로필 컬럼 추가 (기존 DB 호환)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users' AND table_schema = 'public'
        """)
        cols = [row["column_name"] for row in cur.fetchall()]
    for col, ctype in [
        ("name", "TEXT"), ("gender", "TEXT"), ("age", "INTEGER"), ("occupation", "TEXT"), ("nationality", "TEXT"),
        ("sleep_hours", "TEXT"), ("sleep_hours_label", "TEXT"), ("sleep_quality", "TEXT"),
        ("meal_habit", "TEXT"), ("bowel_habit", "TEXT"), ("exercise_habit", "TEXT"),
    ]:
        if col not in cols:
            try:
                with conn.cursor() as cur:
                    cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {ctype}")
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass


def _load_db_config() -> dict:
    """환경변수 우선, 없으면 db_config.json, 없으면 기본값. engine 추가."""
    defaults = {
        "engine": "mysql",
        "host": "localhost",
        "user": "leejee5",
        "password": "",
        "database": "leejee5",
    }
    if os.path.isfile(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                file_cfg = json.load(f)
            for k in defaults:
                if k in file_cfg and file_cfg[k] is not None:
                    v = file_cfg[k]
                    defaults[k] = v if k == "engine" else str(v).strip()
        except Exception:
            pass
    if os.environ.get("DB_ENGINE"):
        defaults["engine"] = os.environ.get("DB_ENGINE", "").strip().lower()
    if os.environ.get("DB_HOST"):
        defaults["host"] = os.environ.get("DB_HOST", "").strip()
    if os.environ.get("DB_USER"):
        defaults["user"] = os.environ.get("DB_USER", "").strip()
    if os.environ.get("DB_PASSWORD") is not None:
        defaults["password"] = os.environ.get("DB_PASSWORD", "")
    if os.environ.get("DB_NAME"):
        defaults["database"] = os.environ.get("DB_NAME", "").strip()
    return defaults


_raw_config = _load_db_config()
DB_ENGINE = (_raw_config.get("engine") or "mysql").strip().lower()
if DB_ENGINE not in ("mysql", "sqlite", "postgres"):
    DB_ENGINE = "mysql"

# PostgreSQL (Supabase): DATABASE_URL 또는 SUPABASE_DB_URL
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL") or ""

# MySQL용 설정 (sqlite/postgres일 때는 사용 안 함)
import pymysql
DB_CONFIG = {
    "host": _raw_config["host"],
    "user": _raw_config["user"],
    "password": _raw_config["password"],
    "database": _raw_config["database"],
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False,
}

# SQLite DB 파일 경로 (엔진이 sqlite일 때)
if DB_ENGINE == "sqlite":
    _sqlite_path = _raw_config.get("database", "sbi.db").strip()
    if not _sqlite_path.endswith(".db"):
        _sqlite_path = _sqlite_path + ".db"
    if not os.path.isabs(_sqlite_path):
        _sqlite_path = os.path.join(_CONFIG_DIR, _sqlite_path)
    SQLITE_DB_PATH = _sqlite_path


def _init_sqlite(conn: sqlite3.Connection) -> None:
    conn.executescript(_SQLITE_SCHEMA)
    # 기존 users 테이블에 프로필 컬럼 추가 (없으면)
    cur = conn.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cur.fetchall()]
    for col, ctype in [
        ("name", "TEXT"), ("gender", "TEXT"), ("age", "INTEGER"), ("occupation", "TEXT"), ("nationality", "TEXT"),
        ("sleep_hours", "TEXT"), ("sleep_hours_label", "TEXT"), ("sleep_quality", "TEXT"), ("meal_habit", "TEXT"), ("bowel_habit", "TEXT"), ("exercise_habit", "TEXT"),
    ]:
        if col not in cols:
            try:
                conn.execute("ALTER TABLE users ADD COLUMN " + col + " " + ctype)
            except Exception:
                pass
    conn.commit()


def _sqlite_row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()} if row else None


@contextmanager
def get_conn():
    """DB 연결 컨텍스트. MySQL, SQLite, 또는 PostgreSQL(Supabase)."""
    if DB_ENGINE == "sqlite":
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            _init_sqlite(conn)
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    elif DB_ENGINE == "postgres":
        import psycopg2
        from psycopg2.extras import RealDictCursor
        url = DATABASE_URL
        if not url:
            raise RuntimeError("DB_ENGINE=postgres 이면 DATABASE_URL 또는 SUPABASE_DB_URL 환경 변수가 필요합니다.")
        if url.startswith("postgres://"):
            url = "postgresql://" + url[11:]
        conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
        try:
            _init_postgres(conn)
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = pymysql.connect(**DB_CONFIG)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def _convert_sql_for_sqlite(sql: str) -> str:
    """MySQL %s 플레이스홀더를 SQLite ? 로 변환."""
    return sql.replace("%s", "?")


def execute_one(conn, sql: str, args: Optional[Tuple] = None) -> Optional[dict]:
    """SELECT 한 건. dict 반환."""
    args = args or ()
    if DB_ENGINE == "sqlite":
        sql = _convert_sql_for_sqlite(sql)
        cur = conn.execute(sql, args)
        row = cur.fetchone()
        return _sqlite_row_to_dict(row)
    if DB_ENGINE == "postgres":
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchone()


def execute_all(conn, sql: str, args: Optional[Tuple] = None) -> List[dict]:
    """SELECT 여러 건."""
    args = args or ()
    if DB_ENGINE == "sqlite":
        sql = _convert_sql_for_sqlite(sql)
        cur = conn.execute(sql, args)
        return [_sqlite_row_to_dict(row) for row in cur.fetchall()]
    if DB_ENGINE == "postgres":
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()


def execute_insert(conn, sql: str, args: Tuple) -> int:
    """INSERT 후 lastrowid 반환."""
    if DB_ENGINE == "sqlite":
        sql = _convert_sql_for_sqlite(sql)
        cur = conn.execute(sql, args)
        return cur.lastrowid
    if DB_ENGINE == "postgres":
        with conn.cursor() as cur:
            cur.execute(sql, args)
            cur.execute("SELECT lastval()")
            row = cur.fetchone()
            return int(row["lastval"]) if row else 0
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.lastrowid


def execute_update_delete(conn, sql: str, args: Tuple) -> int:
    """UPDATE/DELETE 후 rowcount 반환."""
    if DB_ENGINE == "sqlite":
        sql = _convert_sql_for_sqlite(sql)
        cur = conn.execute(sql, args)
        return cur.rowcount
    if DB_ENGINE == "postgres":
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.rowcount
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.rowcount
