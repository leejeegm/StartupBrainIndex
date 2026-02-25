#!/usr/bin/env python3
"""
로컬 SQLite(sbi.db) 데이터를 배포 DB(PostgreSQL/Supabase 또는 MySQL)로 업로드하는 일회성 스크립트.

사용법 (Postgres/Supabase):
  1. 배포 DB의 연결 URL을 환경변수로 설정:
     set SUPABASE_DB_URL=postgresql://user:pass@host:5432/dbname   (Windows)
     export SUPABASE_DB_URL=postgresql://...                        (Mac/Linux)
  2. Supabase 대시보드에서 supabase_schema.sql 로 테이블 생성해 두기.
  3. 로컬에서 실행:
     python upload_sqlite_to_remote.py

사용법 (MySQL):
  1. TARGET_DB_ENGINE=mysql, TARGET_DB_HOST, TARGET_DB_USER, TARGET_DB_PASSWORD, TARGET_DB_NAME 설정
  2. create_tables_mysql.sql 로 테이블 생성해 두기.
  3. python upload_sqlite_to_remote.py

로컬 SQLite 파일 경로:
  환경변수 SQLITE_DB_PATH 가 없으면 프로젝트 루트의 sbi.db 사용.
"""
import os
import sys
import sqlite3

# 프로젝트 루트
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_SQLITE = os.path.join(_SCRIPT_DIR, "sbi.db")

# 업로드할 테이블 및 컬럼 (SQLite와 동일 순서)
_TABLES = [
    (
        "users",
        ["id", "email", "password_hash", "created_at", "name", "gender", "age", "occupation",
         "nationality", "sleep_hours", "sleep_hours_label", "sleep_quality", "meal_habit", "bowel_habit", "exercise_habit"],
    ),
    (
        "survey_saves",
        ["id", "user_email", "title", "update_count", "responses_json", "required_sequences_json",
         "excluded_sequences_json", "created_at"],
    ),
    (
        "chat_saves",
        ["id", "user_email", "summary_title", "messages_json", "ai_notes_json", "created_at"],
    ),
    (
        "board",
        ["id", "type", "title", "content", "created_at", "updated_at"],
    ),
    (
        "eeg_saves",
        ["id", "user_email", "title", "data_json", "created_at"],
    ),
    (
        "indicator_formulas",
        ["id", "title", "content", "sort_order", "created_at", "updated_at"],
    ),
]


def get_sqlite_path():
    return os.environ.get("SQLITE_DB_PATH", "").strip() or _DEFAULT_SQLITE


def connect_sqlite(path: str):
    if not os.path.isfile(path):
        print(f"SQLite 파일 없음: {path}")
        sys.exit(1)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def upload_to_postgres(sqlite_path: str):
    import psycopg2
    from psycopg2.extras import execute_batch

    url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL") or ""
    if not url.strip():
        print("Postgres 연결을 위해 DATABASE_URL 또는 SUPABASE_DB_URL 환경변수를 설정하세요.")
        sys.exit(1)
    if url.startswith("postgres://"):
        url = "postgresql://" + url[11:]

    sqlite_conn = connect_sqlite(sqlite_path)
    pg_conn = psycopg2.connect(url)

    try:
        with sqlite_conn, pg_conn:
            cur = pg_conn.cursor()
            for table, columns in _TABLES:
                # SQLite에서 읽기 (테이블 없으면 건너뜀)
                try:
                    c = sqlite_conn.execute(f"SELECT {', '.join(columns)} FROM {table}")
                    rows = [tuple(row) for row in c.fetchall()]
                except sqlite3.OperationalError as e:
                    print(f"  {table}: 건너뜀 (SQLite에 없음: {e})")
                    continue
                if not rows:
                    print(f"  {table}: 건너뜀 (데이터 없음)")
                    continue
                placeholders = ", ".join(["%s"] * len(columns))
                cols_str = ", ".join(columns)
                sql = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
                try:
                    sql_on_conflict = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"
                    execute_batch(cur, sql_on_conflict, rows, page_size=100)
                    pg_conn.commit()
                    print(f"  {table}: {len(rows)}행 업로드")
                except (psycopg2.ProgrammingError, psycopg2.IntegrityError):
                    pg_conn.rollback()
                    inserted = 0
                    for row in rows:
                        try:
                            cur.execute(sql, row)
                            inserted += 1
                        except psycopg2.IntegrityError:
                            pass
                    pg_conn.commit()
                    print(f"  {table}: {inserted}/{len(rows)}행 업로드")
                # 시퀀스 보정 (SERIAL)
                try:
                    cur.execute(
                        f"SELECT setval(pg_get_serial_sequence(%s, 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1))",
                        (table,),
                    )
                    pg_conn.commit()
                except Exception:
                    pass
    finally:
        sqlite_conn.close()
        pg_conn.close()
    print("Postgres 업로드 완료.")


def upload_to_mysql(sqlite_path: str):
    import pymysql

    host = os.environ.get("TARGET_DB_HOST", "localhost")
    user = os.environ.get("TARGET_DB_USER", "")
    password = os.environ.get("TARGET_DB_PASSWORD", "")
    database = os.environ.get("TARGET_DB_NAME", "")
    if not user or not database:
        print("MySQL 업로드: TARGET_DB_USER, TARGET_DB_NAME 환경변수를 설정하세요.")
        sys.exit(1)

    sqlite_conn = connect_sqlite(sqlite_path)
    mysql_conn = pymysql.connect(
        host=host, user=user, password=password, database=database,
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor, autocommit=False
    )

    try:
        with sqlite_conn, mysql_conn:
            cur = mysql_conn.cursor()
            for table, columns in _TABLES:
                c = sqlite_conn.execute(f"SELECT {', '.join(columns)} FROM {table}")
                rows = [tuple(row) for row in c.fetchall()]
                if not rows:
                    print(f"  {table}: 건너뜀 (데이터 없음)")
                    continue
                placeholders = ", ".join(["%s"] * len(columns))
                cols_str = ", ".join(columns)
                sql = f"INSERT IGNORE INTO {table} ({cols_str}) VALUES ({placeholders})"
                cur.executemany(sql, rows)
                mysql_conn.commit()
                print(f"  {table}: {len(rows)}행 업로드")
    finally:
        sqlite_conn.close()
        mysql_conn.close()
    print("MySQL 업로드 완료.")


def main():
    sqlite_path = get_sqlite_path()
    print(f"소스 SQLite: {sqlite_path}")

    target = (os.environ.get("TARGET_DB_ENGINE") or "").strip().lower()
    if not target:
        if os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL"):
            target = "postgres"
        else:
            print("대상 DB: TARGET_DB_ENGINE=postgres 또는 mysql 설정, 또는 DATABASE_URL/SUPABASE_DB_URL 설정")
            sys.exit(1)

    if target == "postgres":
        upload_to_postgres(sqlite_path)
    elif target == "mysql":
        upload_to_mysql(sqlite_path)
    else:
        print("TARGET_DB_ENGINE 은 postgres 또는 mysql 이어야 합니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
