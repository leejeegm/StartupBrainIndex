# Render 환경 변수 설정 방법

## 1. Render 대시보드에서 Environment 들어가기

1. 브라우저에서 **https://dashboard.render.com** 접속 후 로그인
2. 왼쪽 메뉴 또는 **Dashboard**에서 **해당 Web Service**(SBI 앱) 클릭
3. 상단 탭에서 **Environment** 클릭
4. **Add Environment Variable** 버튼이 보이면 여기서 아래 변수들을 추가합니다.

---

## 2. 변수별 설정 방법

### 2-1. DB_ENGINE

- **Key**: `DB_ENGINE`
- **Value**: 
  - **PostgreSQL 사용(권장)**: `postgres` 입력
  - **SQLite 사용**: `sqlite` 입력

**입력 예**: `postgres`

---

### 2-2. DATABASE_URL (Postgres 사용할 때만)

**PostgreSQL을 쓰는 경우에만** 설정합니다. (`DB_ENGINE=postgres`일 때)

#### A) Render에서 PostgreSQL을 새로 만든 경우

1. Render 대시보드에서 **New +** → **PostgreSQL** 선택
2. 이름(예: `sbi-db`), 리전 선택 후 **Create PostgreSQL** 클릭
3. 생성된 DB 페이지에서 **Info** 탭 클릭
4. **Connection** 섹션에서 **Internal Database URL** 옆 **복사** 클릭  
   (형식: `postgresql://...` 또는 `postgres://...`)
5. Web Service **Environment**로 돌아가서:
   - **Key**: `DATABASE_URL`
   - **Value**: (복사한 URL 그대로 붙여넣기)

**주의**: URL에 비밀번호가 포함되어 있으므로 다른 사람과 공유하거나 저장소에 올리지 마세요.

#### B) 이미 만든 PostgreSQL이 있는 경우

- 해당 DB의 **Info** → **Internal Database URL**을 복사해서  
  Web Service **Environment**에 **Key**: `DATABASE_URL`, **Value**: (복사한 URL) 로 추가하면 됩니다.

**SQLite만 쓸 때** (`DB_ENGINE=sqlite`): `DATABASE_URL`은 **설정하지 않아도** 됩니다.

---

### 2-3. SESSION_SECRET (권장)

- **Key**: `SESSION_SECRET`
- **Value**: **랜덤 문자열** (32바이트 이상 권장)

#### 랜덤 문자열 만드는 방법

**로컬 PC에서 한 번만 실행:**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

- 터미널(또는 CMD/PowerShell)에서 위 명령 실행
- 화면에 나온 긴 문자열(예: `a1b2c3d4e5...`) **전부 복사**
- Render **Environment**에서:
  - **Key**: `SESSION_SECRET`
  - **Value**: (방금 복사한 문자열 붙여넣기)

**설정하지 않으면**: 앱이 재시작될 때마다 세션이 초기화되어, 사용자가 다시 로그인해야 할 수 있습니다.

---

## 3. 설정 후 저장

- 각 변수 입력 후 **Add** 또는 **Save** 클릭
- **Environment** 탭에서 **Save Changes** 버튼이 있으면 **한 번 더 클릭**
- 저장하면 Render가 자동으로 재배포를 시작할 수 있습니다. (설정에 따라 다름)

---

## 4. 요약 표

| Key | Value | 필수 여부 |
|-----|--------|-----------|
| `DB_ENGINE` | `postgres` 또는 `sqlite` | ✅ 필수 |
| `DATABASE_URL` | PostgreSQL 연결 URL | ✅ Postgres 사용 시 필수 |
| `SESSION_SECRET` | 랜덤 문자열 (예: `secrets.token_hex(32)` 결과) | ⭐ 권장 |

---

## 5. 확인

- **Environment** 탭에 위 변수들이 **Key–Value** 형태로 보이면 설정이 반영된 것입니다.
- 배포가 끝난 뒤 **Logs**에서 앱이 정상 시작하는지 확인하고, 로그인·가입이 되는지 브라우저에서 테스트하면 됩니다.
