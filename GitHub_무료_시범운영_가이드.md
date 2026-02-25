# GitHub + 무료 호스팅으로 MVP 전체 기능 테스트·시범 운영하기

GitHub 저장소에 코드를 올리고, **무료 티어** 호스팅(Render 권장)에 연결해 인터넷에서 누구나 접속해 회원가입·설문·PDF까지 **전체 기능**을 시범 테스트할 수 있는 방법입니다.

---

## 전체 흐름 요약

1. **GitHub**에 프로젝트 저장소 생성 및 코드 푸시  
2. **Render**(무료)에서 GitHub 저장소 연결 → 웹 서비스 배포  
3. 환경변수로 **DB=SQLite** 사용 (MySQL 없이 무료로 동작)  
4. 배포된 URL로 접속해 회원가입·설문·PDF 등 **전체 기능** 테스트

---

## 1단계: GitHub 저장소 준비

### 1-1. 제외할 파일 확인

다음은 **저장소에 올리지 마세요** (이미 `.gitignore`에 있을 수 있음).

- `db_config.json` (DB 비밀번호 등)
- `*.db` (SQLite DB 파일)
- `venv/`, `__pycache__/`, `.env`
- `output/` (PDF 생성 파일, 선택)

`.gitignore` 예시가 프로젝트에 있으면 그대로 사용하면 됩니다.

### 1-2. 저장소 생성 및 푸시

1. GitHub 로그인 → **New repository**  
   - 이름 예: `StartupBrainIndex-MVP`  
   - Public, README 없이 생성해도 됨

2. 로컬에서 프로젝트 폴더로 이동 후:

```bash
cd c:\vibeTest\project2_StartupBrainIndex

git init
git add .
git commit -m "MVP: FastAPI SBI 시범운영용"
git branch -M main
git remote add origin https://github.com/본인아이디/StartupBrainIndex-MVP.git
git push -u origin main
```

(이미 `git init` 되어 있으면 `git add .` 부터만 실행)

- **비밀번호/토큰**: GitHub이 비밀번호 로그인을 막으면 **Personal Access Token**을 비밀번호 대신 사용합니다.

---

## 2단계: Render에서 무료 웹 서비스 배포

### 2-1. Render 가입 및 서비스 생성

1. https://render.com 가입 (GitHub 계정 연동 권장)
2. **Dashboard** → **New +** → **Web Service**
3. **Connect a repository** → GitHub에서 `StartupBrainIndex-MVP` (또는 만든 저장소 이름) 선택 후 **Connect**

### 2-2. 설정 입력

| 항목 | 값 |
|------|-----|
| **Name** | `sbi-mvp` (원하는 이름) |
| **Region** | Singapore 또는 가까운 지역 |
| **Branch** | `main` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | **Free** |

### 2-3. 환경 변수 (Environment Variables)

**Environment** 탭에서 다음 변수 추가:

| Key | Value | 비고 |
|-----|--------|------|
| `PORT` | (비워 둠) | Render가 자동으로 넣어 줌 |
| `SESSION_SECRET` | 아무 랜덤 문자열 (예: `openssl rand -hex 32` 결과) | 세션 암호화용 |
| `DB_ENGINE` | `sqlite` | MySQL 없이 DB 사용 |
| `DB_NAME` | `sbi.db` | SQLite 파일 이름 (경로는 프로젝트 루트 기준) |

- `SESSION_SECRET` 없으면 앱이 만들어 주는 값으로 동작하지만, 배포 환경에서는 **반드시 직접 설정**하는 것이 좋습니다.

### 2-4. 배포 실행

- **Create Web Service** 클릭  
- 자동으로 빌드 후 배포됩니다.  
- 완료되면 **URL**이 부여됩니다. 예: `https://sbi-mvp.onrender.com`

---

## 3단계: 시범 운영 확인

1. 위 URL로 접속 → 첫 화면(시작하기) 확인  
2. **회원가입** → 로그인 → **설문 진단** → 제출 → **결과/PDF**  
3. **AI 상담**, **게시판** 등 나머지 메뉴도 동작 확인  

이렇게 하면 **MVP 전체 기능**을 무료 버전으로 시범 테스트할 수 있습니다.

---

## 시범운영 중 재배포해도 데이터 유지 (닷홈 MySQL 등)

수시로 재배포해도 **회원·설문·대화 등 데이터가 사라지지 않게** 하려면, DB를 Render와 분리해 두어야 합니다.

- **닷홈(leejee5.dothome.co.kr) 무료 계정**의 MySQL을 사용하거나
- 닷홈 MySQL 원격 접속이 불가하면 **무료 외부 MySQL**(PlanetScale, Railway 등)을 사용

**자세한 설정**: 프로젝트의 **`닷홈_연동_재배포시_데이터유지_가이드.md`** 를 참고하세요.  
(환경변수 `DB_ENGINE=mysql`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` 설정 및 테이블 생성 방법 포함)

---

## 무료 티어 제한·주의사항 (Render)

| 항목 | 내용 |
|------|------|
| **Cold Start** | 15분 동안 요청이 없으면 슬립 → 다음 접속 시 수십 초 정도 지연 가능 |
| **월 750시간** | 한 서비스가 24/7 켜져 있어도 무료 한도 내 |
| **메모리** | 무료 인스턴스 메모리 제한 있음 (무거운 동시 요청 많으면 오류 가능) |
| **디스크** | SQLite DB·PDF는 **서버 로컬 디스크**에 저장되며, **재배포·재시작 시 초기화**될 수 있음 (시범용으로는 보통 허용) |

- **데이터를 오래 유지**하려면 나중에 Render PostgreSQL 등 외부 DB를 붙이고, 앱을 MySQL/PostgreSQL 모드로 전환하면 됩니다.

---

## Python 버전 지정 (선택)

Render가 사용할 Python 버전을 고정하려면 프로젝트 **루트**에 `runtime.txt` 파일을 만듭니다.

```
python-3.11.7
```

(필요에 따라 `3.10.x`, `3.12.x` 등으로 변경 가능)

---

## 요약 체크리스트

- [ ] GitHub 저장소 생성 후 코드 푸시 (비밀·설정 파일 제외)
- [ ] Render 웹 서비스 생성, GitHub 저장소 연결
- [ ] Build: `pip install -r requirements.txt`
- [ ] Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] 환경변수: `SESSION_SECRET`, `DB_ENGINE=sqlite`, `DB_NAME=sbi.db`
- [ ] 배포 URL로 접속해 회원가입·설문·PDF 등 전체 기능 테스트

이 구성을 따라가면 **무료 버전으로 GitHub에 올리고, Render에서 시범 운영**할 수 있습니다.
