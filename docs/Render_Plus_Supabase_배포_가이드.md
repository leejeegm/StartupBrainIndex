# Render + Supabase 배포 가이드 (SBI FastAPI)

**Render**(앱) + **Supabase**(PostgreSQL DB) 구조로 재배포하면, **재배포·재시작 후에도 데이터가 유지**됩니다.  
둘 다 **무료 플랜**으로 사용 가능합니다.

---

## 1. 무료 플랜 요약

| 서비스 | 무료 플랜 |
|--------|-----------|
| **Render** | Web Service 1개, 15분 미사용 시 슬립(첫 요청 50초 내외 지연) |
| **Supabase** | PostgreSQL 500MB, 월 50K MAU 등. 직접 연결 또는 Pooler 사용 |

---

## 2. 순서

### ① Supabase 프로젝트 생성

1. [supabase.com](https://supabase.com) 가입(무료)
2. **New project** → 리전·DB 비밀번호 설정
3. 프로젝트 생성 후 **Settings** → **Database** 에서 **Connection string** 복사
   - **URI** (Transaction pooler 권장): `postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres`
   - 비밀번호는 프로젝트 생성 시 설정한 값. 필요 시 **Reset database password** 후 새로 복사

### ② Supabase에 테이블 생성

1. **SQL Editor** → **New query**
2. 프로젝트 루트의 **`supabase_schema.sql`** 내용 전체 붙여넣기 후 **Run**
3. 6개 테이블(users, survey_saves, chat_saves, board, eeg_saves, indicator_formulas) 생성 확인

### ③ Render 환경 변수 설정

기존 Render Web Service **Environment** 에서:

| Key | Value |
|-----|-------|
| `DB_ENGINE` | `postgres` |
| `DATABASE_URL` | Supabase에서 복사한 **Connection string (URI)** 전체 |

- **주의**: Connection string에 비밀번호가 들어 있으므로, Render에서는 **Encrypt** 또는 비공개 변수로 저장됩니다.
- Supabase가 `postgres://` 로 주면 Render/psycopg2 호환을 위해 앱에서 `postgresql://` 로 자동 변환합니다.

**기존 변수**  
- `PYTHON_VERSION`, `SESSION_SECRET` 은 그대로 두고  
- `DB_ENGINE` 만 `sqlite` → `postgres` 로,  
- `DATABASE_URL` 만 추가하면 됩니다.  
- SQLite용 `DB_NAME` 은 postgres에서는 사용하지 않습니다(무시해도 됨).

### ④ 재배포

1. **Manual Deploy** 또는 저장소 푸시로 재배포
2. Logs에서 `uvicorn` 시작까지 확인 후, 서비스 URL로 접속
3. 로그인·설문 저장 후 **재배포 한 번 더** 해 보면, 데이터가 그대로인지 확인

---

## 3. 연결 문자열 예시 (Supabase)

- **Transaction pooler (권장, 서버리스)**  
  `postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres`
- **Direct connection**  
  `postgresql://postgres:[YOUR-PASSWORD]@db.[project-ref].supabase.co:5432/postgres`

Render처럼 짧은 요청마다 연결했다 끊는 경우 **Pooler(6543)** 를 쓰는 것이 좋습니다.

---

## 4. 요약

1. Supabase에서 프로젝트 생성 → **Connection string(URI)** 복사  
2. **SQL Editor**에서 `supabase_schema.sql` 실행  
3. Render **Environment**: `DB_ENGINE`=postgres, `DATABASE_URL`=연결 문자열  
4. 재배포 후 동작·데이터 유지 확인  

이렇게 하면 **Render + Supabase** 구조로 재배포할 수 있고, 재배포 후에도 DB 데이터는 Supabase에 유지됩니다.
