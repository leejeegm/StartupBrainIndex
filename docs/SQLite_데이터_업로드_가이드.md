# 로컬 SQLite 데이터를 배포 DB에 업로드하기

배포된 서비스(Render 등)의 DB가 비어 있을 때, 로컬에서 채워 둔 **SQLite(sbi.db)** 데이터를 한 번에 올리는 방법입니다.

---

## 전제

- **배포 쪽 DB**는 SQLite가 아니라 **PostgreSQL(Supabase)** 또는 **MySQL**을 사용하는 것을 권장합니다.  
  Render 무료 플랜에서는 SQLite 파일이 재배포 시 사라지므로, 데이터를 유지하려면 외부 DB를 쓰세요.
- 배포 DB에는 이미 **테이블이 생성**되어 있어야 합니다.  
  - Postgres: Supabase 대시보드에서 `supabase_schema.sql` 실행  
  - MySQL: `create_tables_mysql.sql` 실행

---

## 1. Postgres(Supabase)로 업로드

1. **Supabase**에서 DB 연결 정보 확인  
   - Project Settings → Database → **Connection string** (URI) 복사  
   - 예: `postgresql://postgres.xxxx:비밀번호@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres`

2. **로컬 PC**에서 환경 변수 설정 후 스크립트 실행:
   ```bash
   # Windows (cmd)
   set SUPABASE_DB_URL=postgresql://postgres.xxxx:비밀번호@...pooler.supabase.com:5432/postgres
   python upload_sqlite_to_remote.py

   # Windows (PowerShell)
   $env:SUPABASE_DB_URL="postgresql://..."
   python upload_sqlite_to_remote.py

   # Mac/Linux
   export SUPABASE_DB_URL="postgresql://..."
   python upload_sqlite_to_remote.py
   ```
   `DATABASE_URL`을 써도 됩니다. 둘 다 없으면 스크립트가 안내 메시지를 띄웁니다.

3. **Render** 환경 변수에 같은 DB URL 설정  
   - 서비스 → **Environment** → `DATABASE_URL` 또는 `SUPABASE_DB_URL` 에 위와 같은 URL 입력  
   - `DB_ENGINE=postgres` 로 설정해 두면 앱이 이 DB를 사용합니다.

이렇게 하면 로컬 `sbi.db` 내용이 Supabase(배포 DB)로 복사되고, 배포된 앱은 그 데이터를 사용합니다.

---

## 2. MySQL로 업로드

1. 배포에서 사용할 **MySQL** 호스트/계정/DB 이름 확인.

2. 로컬에서 환경 변수 설정 후 실행:
   ```bash
   set TARGET_DB_ENGINE=mysql
   set TARGET_DB_HOST=your-mysql-host
   set TARGET_DB_USER=your-user
   set TARGET_DB_PASSWORD=your-password
   set TARGET_DB_NAME=your-database
   python upload_sqlite_to_remote.py
   ```

3. Render에서는 `DB_ENGINE=mysql`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` 를 같은 값으로 설정.

---

## 3. SQLite 파일 경로

- 기본: 프로젝트 루트의 **sbi.db** 를 읽습니다.
- 다른 파일을 쓰려면:
  ```bash
  set SQLITE_DB_PATH=C:\path\to\your\sbi.db
  python upload_sqlite_to_remote.py
  ```

---

## 4. 요약

| 목적 | 작업 |
|------|------|
| 배포 DB가 비어 있을 때 | 로컬에서 `upload_sqlite_to_remote.py` 한 번 실행 |
| 대상 DB | `SUPABASE_DB_URL` 또는 `DATABASE_URL`(Postgres) / MySQL용 TARGET_DB_* |
| 소스 | 로컬 `sbi.db` (또는 `SQLITE_DB_PATH`) |

배포 환경에서는 **DB_ENGINE=postgres**(또는 mysql)와 해당 연결 정보를 설정해 두면, 이후 재배포해도 데이터가 유지됩니다.
