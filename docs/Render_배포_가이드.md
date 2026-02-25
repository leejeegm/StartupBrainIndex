# Render 배포 가이드 (SBI FastAPI)

GitHub에 올린 현재 버전(SBI FastAPI)을 **Render**에서 무료 Web Service로 배포하는 방법입니다.

---

## 1. 준비 (이미 되어 있음)

- [x] GitHub 저장소: `https://github.com/leejeegm/StartupBrainIndex`
- [x] `requirements.txt`, `runtime.txt` (Python 3.11)
- [x] 시작 명령: `uvicorn main:app --host 0.0.0.0 --port $PORT`

---

## 2. Render에서 할 일 (순서)

### ① Render 가입 및 로그인

1. [render.com](https://render.com) 접속
2. **Get Started for Free** → GitHub 계정으로 로그인
3. GitHub 권한 허용 (Render가 저장소 목록에 접근)

---

### ② 새 Web Service 생성

1. 대시보드에서 **New +** → **Web Service** 선택
2. **Connect a repository** 에서 `leejeegm/StartupBrainIndex` 선택 (또는 연결 후 해당 저장소 선택)
3. **Connect** 클릭

---

### ③ 설정 입력

| 항목 | 값 |
|------|-----|
| **Name** | `sbi-startup-brain-index` (원하면 변경 가능) |
| **Region** | **Singapore** (한국과 가까움) 또는 Oregon |
| **Branch** | `main` |
| **Runtime** | **Python 3** |
| **Build Command** | `pip install -r requirements.txt && pip install itsdangerous==2.1.2` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

- **Advanced** 펼치면 **Docker** 등 다른 옵션이 있음. 여기서는 기본(Python)만 사용.

---

### ④ 환경 변수 (Environment Variables)

**Environment** 탭 또는 설정 화면에서 **Add Environment Variable** 로 아래 추가:

| Key | Value | 비고 |
|-----|-------|------|
| `PYTHON_VERSION` | `3.11.7` | **필수**. Python 3.14 사용 시 pandas 빌드 실패함. 3.11로 고정 |
| `SESSION_SECRET` | 영문·숫자 랜덤 문자열 (예: 32자) | **필수**. 세션 암호화용. Render에서 "Generate" 가능 |
| `DB_ENGINE` | `sqlite` | 기본값. SQLite 사용 시 |
| `DB_NAME` | `sbi.db` | SQLite 파일 이름 (기본) |

**참고**:
- 무료 플랜에서는 디스크가 **휘발성**이라, 재배포·재시작 시 SQLite 데이터가 **사라질 수 있음**. 테스트용으로만 사용 권장.
- MySQL 등 외부 DB를 쓰면 `DB_ENGINE=mysql`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` 를 추가해 설정.

---

### ⑤ 배포 실행

1. **Create Web Service** 클릭
2. 자동으로 빌드 시작 (몇 분 소요)
3. **Logs** 탭에서 `pip install` → `uvicorn` 시작 로그 확인
4. 상단 **URL** (예: `https://sbi-startup-brain-index.onrender.com`) 로 접속

---

## 3. 배포 후 확인

- [ ] `https://본인서비스이름.onrender.com/` 접속
- [ ] `/login` → 로그인 (데모 계정: user@test.com / pass1234)
- [ ] `/dashboard` 진입, Step 1 설문
- [ ] `/admin` (관리자: admin@test.com / admin)
- [ ] PDF 다운로드 등

**첫 접속이 느린 이유**: 무료 플랜은 15분 미사용 시 **슬립** → 깨우는데 30초~1분 걸릴 수 있음.

---

## 4. 문제 해결

| 현상 | 확인·조치 |
|------|-----------|
| **pandas 빌드 실패** (Python 3.14, `_PyLong_AsByteArray` 등) | Render가 Python 3.14를 써서 발생. **Environment**에 `PYTHON_VERSION` = `3.11.7` 추가 후 **Manual Deploy** 또는 재배포 |
| 빌드 실패 | Logs에서 에러 확인. `requirements.txt` 버전 충돌 시 로컬에서 `pip install -r requirements.txt` 먼저 테스트 |
| 503 / Application failed | Start Command가 `uvicorn main:app --host 0.0.0.0 --port $PORT` 인지 확인. `main.py` 가 루트에 있는지 확인 |
| 로그인 안 됨 | `SESSION_SECRET` 이 설정됐는지 확인. 값이 비어 있으면 세션 오류 발생 가능 |
| DB 오류 | SQLite 사용 시 Render 디스크 휘발성 참고. MySQL 쓰면 환경 변수(DB_HOST 등) 확인 |

---

## 5. 요약

1. Render 가입 → **New Web Service** → 저장소 `StartupBrainIndex` 연결  
2. **Build**: `pip install -r requirements.txt`  
3. **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`  
4. **Env**: `SESSION_SECRET` (필수), `DB_ENGINE`, `DB_NAME`  
5. Create 후 URL로 접속해 동작 확인  

이렇게 하면 현재 버전이 Render에서 배포됩니다. 나중에 MVP2는 Vercel로 비교 배포하면 됩니다.
