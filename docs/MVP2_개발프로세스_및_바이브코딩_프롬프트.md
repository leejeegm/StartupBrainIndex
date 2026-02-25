# MVP2 개발 프로세스 및 Cursor 바이브코딩 프롬프트 완성본

Startup Brain Index(SBI) MVP를 **Next.js 14 + Supabase + Vercel** 스택의 MVP2로 전환할 때 사용하는 **단계별 개발 프로세스**와 **Cursor 바이브코딩용 프롬프트**를 정리한 문서입니다.  
각 단계별 **주의사항**, **오류 체크·확인 사항**, **대응방안**을 포함합니다.

---

## 목차

1. [최적의 개발 프로세스 개요](#1-최적의-개발-프로세스-개요)
2. [Phase 0: 준비 및 명세 고정](#phase-0-준비-및-명세-고정)
3. [Phase 1: 프로젝트 셋업](#phase-1-프로젝트-셋업)
4. [Phase 2: DB 스키마 및 인증](#phase-2-db-스키마-및-인증)
5. [Phase 3: 사용자 플로우 (로그인·대시보드·Step 1~5)](#phase-3-사용자-플로우-로그인대시보드step-15)
6. [Phase 4: 관리자 플로우](#phase-4-관리자-플로우)
7. [Phase 5: 부가 기능 및 마무리](#phase-5-부가-기능-및-마무리)
8. [Phase 6: 배포 및 검증](#phase-6-배포-및-검증)

---

## 1. 최적의 개발 프로세스 개요

| Phase | 목표 | 산출물 |
|-------|------|--------|
| **0** | 명세·스택 확정 | 기능·화면 명세, 스택 체크리스트 |
| **1** | Next.js + Supabase + 저장소 준비 | `package.json`, `.env.local.example`, README |
| **2** | DB·인증 | Supabase migrations, RLS, 로그인/회원가입 |
| **3** | 사용자 플로우 | 로그인, 대시보드, Step 1~5, 저장·불러오기 |
| **4** | 관리자 플로우 | `/admin` 탭 6개, 목록·상세·수정·삭제 |
| **5** | PDF·AI·다국어·반응형 | PDF 다운로드, AI 상담, ko/en, 모바일 |
| **6** | 배포·검증 | Vercel 배포, E2E 체크리스트 |

**원칙**: UI/UX(메뉴·플로우)는 현재 SBI와 동일하게 유지하고, 구현만 Next.js/Supabase에 맞게 새로 작성합니다.

---

## Phase 0: 준비 및 명세 고정

### 목표

- MVP2 폴더·저장소 준비
- 현재 SBI의 화면·API·DB를 문서로 정리
- 기술 스택 확정

### 단계

| 단계 | 내용 | 산출물 |
|------|------|--------|
| 0-1 | MVP2 전용 폴더 생성(예: `StartupBrainIndex-MVP2`), GitHub 저장소 생성 | 빈 저장소 |
| 0-2 | 현재 SBI의 페이지·메뉴·API·테이블 목록 정리 | `docs/기능_화면_명세.md` |
| 0-3 | 기술 스택 확정 및 문서화 | 스택 체크리스트 |

### Cursor 바이브코딩 프롬프트 (Phase 0)

```
[역할]
당신은 Next.js 14(App Router) + Supabase + Vercel 스택으로 웹 앱을 만드는 시니어 개발자입니다.

[배경]
기존 프로젝트 경로: c:\vibeTest\project2_StartupBrainIndex
- FastAPI + SQLite/MySQL + 정적 HTML의 "Startup Brain Index(SBI)" MVP입니다.
- 이를 새 폴더 "StartupBrainIndex-MVP2"에서 Next.js 14 + Supabase + Vercel로 재구현하려 합니다.
- UI/UX(사용자 로그인→대시보드 Step 1~5·저장·게시판, 관리자 /admin 탭)는 유지하고 기술 스택만 이전합니다.

[참고 파일]
- static/dashboard.html: 헤더, 좌측 사이드바(Step 1 설문 진단, Step 2 결과/PDF, Step 3 뇌파·시각화, Step 4 AI 상담, 저장·불러오기, Step 5 게시판)
- static/admin.html: 탭(로그인·회원, 설문저장·진단, 대화저장, 게시판, 뇌파저장, 지표 산출식)
- create_tables_mysql.sql: users, survey_saves, chat_saves, board, eeg_saves, indicator_formulas
- main.py: API 라우트(/api/login, /api/register, /api/me, /dashboard, /admin, /api/admin/*, /api/survey/*, /api/chat/* 등)

[요청]
1) 현재 SBI 프로젝트를 기준으로 "기능·화면 명세"를 마크다운으로 작성해 주세요.
   - 페이지/라우트: /, /login, /register, /dashboard, /admin
   - 사용자 대시보드: 헤더(로고, 사용자명, 홈·로그아웃), 좌측 사이드바(Step 1~5, 저장·불러오기), 메인 영역
   - 관리자: /admin 탭 6개(로그인·회원, 설문저장·진단, 대화저장, 게시판, 뇌파저장, 지표 산출식)
   - 기존 DB 테이블 6개와 각 컬럼 요약
   - 주요 API 엔드포인트 목록(인증, 설문, 채팅, 게시판, PDF, 관리자)
2) MVP2 기술 스택을 한 줄로 정리한 문단을 추가하세요.
   (Next.js 14 App Router, TypeScript, Tailwind CSS, Supabase DB + Auth, Vercel 배포)
3) 이 내용을 docs/기능_화면_명세.md 로 저장해 주세요.
```

### 예시: 명세 문서 구조

```markdown
# SBI 기능·화면 명세 (MVP2 기준)

## 라우트
| 경로 | 설명 | 인증 |
|------|------|------|
| / | 랜딩 | - |
| /login | 로그인 | - |
| /register | 회원가입 | - |
| /dashboard | 사용자 대시보드 | 필요 |
| /admin | 관리자 | 관리자만 |

## 사용자 대시보드
- 헤더: Startup Brain Index, 사용자명, 홈, 로그아웃
- 사이드바: Step 1 설문 진단, Step 2 결과/PDF, Step 3 뇌파·시각화, Step 4 AI 상담, 저장·불러오기, Step 5 게시판
...
```

### 단계별 변경 시 주의사항 (Phase 0)

- **경로**: Cursor에서 열린 워크스페이스가 **현재 SBI 프로젝트**인지 확인. MVP2 폴더는 0-1에서 새로 만들므로, 명세는 현재 폴더 기준으로 작성.
- **참조 일관성**: `create_tables_mysql.sql`, `main.py`, `static/dashboard.html`, `static/admin.html` 등 실제 파일명·경로와 맞게 명세에 기재.

### 오류 체크·확인 사항 (Phase 0)

| 확인 항목 | 방법 | 통과 기준 |
|-----------|------|-----------|
| 명세에 모든 라우트 포함 | docs/기능_화면_명세.md 검토 | /, /login, /register, /dashboard, /admin 존재 |
| 사이드바 메뉴 6개 반영 | 명세의 "사용자 대시보드" 섹션 | Step 1~5 + 저장·불러오기 |
| 관리자 탭 6개 반영 | 명세의 "관리자" 섹션 | 로그인·회원, 설문저장·진단, 대화저장, 게시판, 뇌파저장, 지표 산출식 |
| DB 테이블 6개 | 명세의 테이블 목록 | users, survey_saves, chat_saves, board, eeg_saves, indicator_formulas |

### 대응방안 (Phase 0)

| 문제 | 원인 | 대응 |
|------|------|------|
| 명세에 API가 빠짐 | main.py 라우트 수 많음 | grep으로 @app\.(get\|post\|put\|delete) 또는 router 검색 후 목록 보완 |
| 테이블 컬럼 불일치 | SQL과 db.py 사용처 상이 | create_tables_mysql.sql 우선, 필요 시 user_storage.py 등에서 참조 컬럼 추가 |
| MVP2 폴더를 아직 안 만듦 | Phase 1에서 생성 예정 | Phase 0에서는 명세만 작성. 0-1은 수동으로 폴더/저장소 생성 가능 |

---

## Phase 1: 프로젝트 셋업

### 목표

- Next.js 14 프로젝트 생성
- Supabase·Vercel 연동을 위한 env 예시 및 README 정리

### 단계

| 단계 | 내용 | 산출물 |
|------|------|--------|
| 1-1 | Next.js 14 생성 (App Router, TypeScript, Tailwind, ESLint) | `package.json`, `app/`, `tailwind.config.*` |
| 1-2 | `.env.local.example` 작성 (Supabase URL/Key 등) | `.env.local.example` |
| 1-3 | `.gitignore`에 `.env.local` 포함, README에 로컬 실행·배포 한 줄 | README.md |

### Cursor 바이브코딩 프롬프트 (Phase 1)

```
[역할·배경]
StartupBrainIndex-MVP2를 Next.js 14 + Supabase + Vercel로 구축합니다.
Phase 0에서 작성한 docs/기능_화면_명세.md 를 기준으로 합니다.

[요청]
1) **새 폴더** "StartupBrainIndex-MVP2"를 현재 워크스페이스 상위 또는 동일 레벨에 만들고,
   그 안에 Next.js 14 프로젝트를 생성해 주세요.
   - create-next-app 사용: App Router, TypeScript, Tailwind CSS, ESLint, src directory 사용 여부는 팀 컨벤션에 맞게.
   - 만약 이미 MVP2 폴더가 있고 그 안에 Next 프로젝트가 있다면, 2)·3)만 진행하세요.
2) StartupBrainIndex-MVP2 루트에 .env.local.example 파일을 생성하고, 다음 변수와 설명을 넣어 주세요.
   - NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
   - NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   - (선택) SUPABASE_SERVICE_ROLE_KEY=  # 관리자 API용
   - (선택) ADMIN_EMAIL=admin@test.com   # 관리자 이메일 (쉼표로 여러 개 가능)
3) .gitignore에 .env.local, .env 가 포함되어 있는지 확인하고,
   README.md에 다음을 추가해 주세요.
   - "로컬 실행: npm install 후 .env.local 을 복사해 채우고 npm run dev"
   - "배포: Vercel 연결 후 환경 변수 설정"
```

### 예시: .env.local.example

```env
# Supabase (필수)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 관리자 (선택)
ADMIN_EMAIL=admin@test.com
# SUPABASE_SERVICE_ROLE_KEY=  # 관리자 전용 API 사용 시
```

### 예시: Phase 1 후 생성·수정되는 파일

| 파일/폴더 | 설명 |
|-----------|------|
| `StartupBrainIndex-MVP2/package.json` | Next 14, React, TypeScript 의존성 |
| `StartupBrainIndex-MVP2/app/layout.tsx`, `app/page.tsx` | App Router 기본 페이지 |
| `StartupBrainIndex-MVP2/.env.local.example` | 위 env 예시 내용 |
| `StartupBrainIndex-MVP2/README.md` | 로컬 실행·배포 한 줄 추가 |
| `StartupBrainIndex-MVP2/.gitignore` | `.env.local`, `.env` 포함 확인 |

### 단계별 변경 시 주의사항 (Phase 1)

- **워크스페이스**: MVP2를 **별도 Cursor 창**으로 열지, 현재 SBI 프로젝트 하위에 넣을지 결정. 상위 레벨에 두면 `c:\vibeTest\StartupBrainIndex-MVP2` 같은 경로가 됨.
- **Node 버전**: Next.js 14는 Node 18.17 이상 권장. `node -v`로 확인.
- **이미 존재하는 폴더**: 이미 MVP2가 있으면 create-next-app으로 덮어쓰지 말고, 기존 파일 유지한 채 env·README만 보완.

### 오류 체크·확인 사항 (Phase 1)

| 확인 항목 | 방법 | 통과 기준 |
|-----------|------|-----------|
| Next 앱 실행 | MVP2 폴더에서 `npm run dev` | localhost:3000 접속 시 기본 페이지 표시 |
| TypeScript 에러 없음 | `npm run build` 또는 IDE 체크 | 빌드 성공 또는 0 error |
| .env.local 미커밋 | `git status` (MVP2가 git init 된 경우) | .env.local 이 untracked 또는 .gitignore에 있음 |
| README에 실행 방법 있음 | README.md 내용 확인 | "npm run dev" 및 env 설명 포함 |

### 대응방안 (Phase 1)

| 문제 | 원인 | 대응 |
|------|------|------|
| create-next-app 실패 (존재하는 폴더) | 폴더가 비어 있지 않음 | 빈 폴더에만 생성하거나, npx create-next-app@14 . --yes 로 현재 폴더에 생성 |
| Module not found 'react' | node_modules 미설치 | `npm install` 재실행 |
| Port 3000 in use | 다른 앱이 3000 사용 중 | `npm run dev -- -p 3001` 또는 해당 프로세스 종료 |
| .env.local.example 이 적용 안 됨 | Next는 .env.local 만 로드 | 사용자가 .env.local.example 을 복사해 .env.local 로 저장하고 값 채우기 안내 |

---

## Phase 2: DB 스키마 및 인증

### 목표

- 기존 MySQL 스키마를 PostgreSQL(Supabase)용으로 마이그레이션
- RLS 정책 초안
- 로그인/회원가입 방식 결정 및 문서화

### 단계

| 단계 | 내용 | 산출물 |
|------|------|--------|
| 2-1 | Supabase용 SQL 마이그레이션 작성 (6개 테이블) | `supabase/migrations/001_initial_schema.sql` |
| 2-2 | RLS 정책 초안 (users 본인, survey/chat 본인, board/eeg/indicator 관리자) | `002_rls.sql` 또는 001에 포함 |
| 2-3 | 인증 방식 결정: Supabase Auth vs users 테이블만 | docs/phase2-auth.md 또는 README |

### Cursor 바이브코딩 프롬프트 (Phase 2)

```
[역할·배경]
StartupBrainIndex-MVP2는 Next.js 14 + Supabase + Vercel입니다.
기존 SBI의 DB 스키마(create_tables_mysql.sql)를 Supabase(PostgreSQL)로 이전합니다.

[참고 스키마 - 기존 MySQL]
- users: id, email, password_hash, created_at, name, gender, age, occupation, nationality,
  sleep_hours, sleep_hours_label, sleep_quality, meal_habit, bowel_habit, exercise_habit
- survey_saves: id, user_email, title, update_count, responses_json, required_sequences_json, excluded_sequences_json, created_at
- chat_saves: id, user_email, summary_title, messages_json, ai_notes_json, created_at
- board: id, type, title, content, created_at, updated_at
- eeg_saves: id, user_email, title, data_json, created_at
- indicator_formulas: id, title, content, sort_order, created_at, updated_at

[요청]
1) supabase/migrations 폴더를 만들고 001_initial_schema.sql 을 작성해 주세요.
   - 위 6개 테이블을 PostgreSQL 문법으로 정의 (SERIAL/BIGSERIAL, TEXT/VARCHAR, JSONB, timestamptz).
   - created_at, updated_at 은 timestamptz DEFAULT now() 사용.
   - LONGTEXT -> TEXT, VARCHAR(255) -> VARCHAR(255) 또는 TEXT 유지.
2) 002_rls.sql 을 작성해 주세요.
   - users: RLS 활성화, 본인 행만 SELECT/UPDATE (email = auth.jwt() ->> 'email' 또는 커스텀 claims).
   - survey_saves, chat_saves: user_email 기준 본인만 SELECT/INSERT/UPDATE/DELETE.
   - board: 모든 사용자 SELECT, INSERT/UPDATE/DELETE는 관리자만 (예: admin 이메일 화이트리스트 또는 role).
   - eeg_saves: 본인만 SELECT/INSERT/UPDATE/DELETE.
   - indicator_formulas: 모든 사용자 SELECT, INSERT/UPDATE/DELETE는 관리자만.
   - Supabase Auth를 쓰지 않고 users 테이블만 쓸 경우, RLS는 "서비스 역할로 API에서 제어"라고 주석 처리하고 정책은 나중에 연동 시 추가.
3) docs/phase2-auth.md 를 만들고, 다음 중 하나를 명시해 주세요.
   - "Supabase Auth 사용: 로그인/회원가입은 signInWithPassword, signUp. auth.users 와 users 테이블 동기화(트리거 또는 Edge Function) 예정."
   - "커스텀 users 테이블만 사용: Next API Route에서 비밀번호 검증 후 쿠키/세션 발급. Supabase는 DB만 사용."
```

### 예시: 001_initial_schema.sql (일부)

```sql
-- users
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  name VARCHAR(128),
  gender VARCHAR(16),
  age INT,
  occupation VARCHAR(256),
  nationality VARCHAR(128),
  sleep_hours DECIMAL(4,1),
  sleep_hours_label VARCHAR(64),
  sleep_quality VARCHAR(32),
  meal_habit VARCHAR(32),
  bowel_habit VARCHAR(32),
  exercise_habit VARCHAR(32)
);

-- survey_saves
CREATE TABLE IF NOT EXISTS survey_saves (
  id BIGSERIAL PRIMARY KEY,
  user_email VARCHAR(255) NOT NULL,
  title VARCHAR(512) NOT NULL,
  update_count INT NOT NULL DEFAULT 0,
  responses_json TEXT NOT NULL,
  required_sequences_json TEXT NOT NULL,
  excluded_sequences_json TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- ... 나머지 테이블
```

### 예시: Phase 2 후 생성되는 파일

| 파일 | 설명 |
|------|------|
| `supabase/migrations/001_initial_schema.sql` | users, survey_saves, chat_saves, board, eeg_saves, indicator_formulas 6개 테이블 |
| `supabase/migrations/002_rls.sql` | RLS 활성화 및 테이블별 정책(본인/관리자) |
| `docs/phase2-auth.md` | "Supabase Auth 사용" 또는 "커스텀 users 테이블만 사용" 명시 |

### 단계별 변경 시 주의사항 (Phase 2)

- **Supabase 대시보드**: 마이그레이션은 Supabase CLI로 적용하거나, SQL Editor에 붙여 넣어 실행. 실행 순서(001 → 002) 준수.
- **RLS와 서비스 역할**: 서비스 역할 키는 RLS를 우회하므로, 서버 전용 API에서만 사용하고 클라이언트에는 anon 키만 사용.
- **기존 데이터**: MySQL에 이미 데이터가 있으면 별도 ETL 스크립트 필요. 이 문서는 스키마만 정의.

### 오류 체크·확인 사항 (Phase 2)

| 확인 항목 | 방법 | 통과 기준 |
|-----------|------|-----------|
| 001 실행 성공 | Supabase SQL Editor에서 001 실행 | 에러 없이 테이블 6개 생성 |
| 002 RLS 실행 | 002 실행 | RLS 활성화 및 정책 생성, 에러 없음 |
| 타입 호환 | 기존 API의 JSON 필드 사용 방식 | responses_json, messages_json 등 TEXT/JSONB로 쿼리 가능 |

### 대응방안 (Phase 2)

| 문제 | 원인 | 대응 |
|------|------|------|
| relation "users" already exists | 001 재실행 | CREATE TABLE IF NOT EXISTS 사용했는지 확인. 이미 있으면 DROP 후 재실행(개발 환경만) 또는 마이그레이션 버전 관리 |
| RLS 정책으로 인해 조회 안 됨 | 정책 조건이 너무 엄격 | 임시로 RLS 비활성화해 테스트 후, 정책 조건 수정(예: auth.uid() 대신 request 헤더의 user_id 사용) |
| auth.jwt()가 null | Supabase Auth 미사용 | 커스텀 users 테이블 방식이면 RLS 대신 API Route에서 user_email 검증 후 Supabase 클라이언트는 service role 사용 |

---

## Phase 3: 사용자 플로우 (로그인·대시보드·Step 1~5)

### 목표

- 로그인/회원가입 페이지 및 API
- 대시보드 레이아웃(헤더 + 사이드바 + 메인)
- Step 1 설문, Step 2~5 및 저장·불러오기 골격

### 단계

| 단계 | 내용 | 산출물 |
|------|------|--------|
| 3-1 | 로그인 페이지, 로그인 API, /dashboard 리다이렉트 | app/login/page.tsx, API 또는 Server Action |
| 3-2 | 대시보드 레이아웃(헤더, 사이드바, 메인) | app/dashboard/layout.tsx, 사이드바 컴포넌트 |
| 3-3 | Step 1 설문 (문항 로드, 제출, 저장) | app/dashboard/step-1 또는 단일 페이지 내 패널 |
| 3-4 | Step 2~5 placeholder, 저장·불러오기 모달·API | Step 2~5 페이지/패널, 저장 목록 API |

### Cursor 바이브코딩 프롬프트 (Phase 3)

```
[역할·배경]
StartupBrainIndex-MVP2의 사용자 플로우를 구현합니다.
UI/UX는 기존 SBI(static/dashboard.html)와 동일하게 유지합니다.

[참고]
- dashboard.html: 헤더(Startup Brain Index, 사용자명, 홈·로그아웃), 좌측 사이드바(Step 1~5, 저장·불러오기), data-step="1"~"5" 로 패널 전환
- 기존 API: POST /api/login, GET /api/me, GET /dashboard (세션 필요), 설문 문항은 survey_items.csv 또는 get_items

[요청]
1) 로그인 페이지를 구현해 주세요.
   - app/(auth)/login/page.tsx 또는 app/login/page.tsx
   - 이메일, 비밀번호 입력, "로그인" 버튼
   - 데모 계정(user@test.com / pass1234)은 환경 변수 DEMO_PASSWORD 또는 하드코드 처리
   - 로그인 성공 시 /dashboard 로 리다이렉트. next=/admin 이면 /admin 으로
   - Supabase Auth 사용 시: signInWithPassword 후 router.push; 커스텀 users 테이블이면 API Route POST /api/auth/login 에서 세션 쿠키 설정
2) 대시보드 레이아웃을 구현해 주세요.
   - app/dashboard/layout.tsx: 헤더(로고/타이틀 "Startup Brain Index", 사용자명, 홈(/), 로그아웃), 좌측 사이드바(반응형: 1024px 미만에서 햄버거 토글)
   - 사이드바 메뉴: Step 1 설문 진단, Step 2 결과/PDF, Step 3 뇌파·시각화, Step 4 AI 상담, "저장·불러오기" 버튼, Step 5 게시판
   - 메인: children으로 각 Step 라우트 또는 단일 페이지 내 step state로 패널 전환
3) Step 1(설문 진단)을 구현해 주세요.
   - 설문 문항: 기존 survey_items.csv 구조를 참고해 Supabase 테이블 또는 JSON/API로 로드 (1~96 전체순번, 1~5점)
   - 진행률 표시, "제출" 버튼. 제출 시 API 또는 Server Action으로 응답 저장 후 Step 2에서 결과 사용 가능하도록
4) Step 2는 "결과 요약 + PDF 다운로드 버튼" placeholder. Step 3·4·5는 제목만 있는 placeholder.
5) "저장·불러오기": 설문 저장 목록·대화 저장 목록을 Supabase에서 조회하는 API와 모달 UI 골격(목록 표시, 선택 시 불러오기)을 만들어 주세요.
```

### 예시: 사이드바 메뉴 구조 (유지)

```tsx
// 대시보드 사이드바에 넣을 링크/버튼
const steps = [
  { step: 1, label: 'Step 1: 설문 진단', path: '/dashboard?step=1' },
  { step: 2, label: 'Step 2: 결과 / PDF', path: '/dashboard?step=2' },
  { step: 3, label: 'Step 3: 뇌파·시각화', path: '/dashboard?step=3' },
  { step: 4, label: 'Step 4: AI 상담', path: '/dashboard?step=4' },
];
// + 저장·불러오기 버튼
// + Step 5: 게시판 및 자료실
```

### 단계별 변경 시 주의사항 (Phase 3)

- **세션 vs Supabase Auth**: 쿠키 세션을 쓰면 미들웨어에서 `/dashboard` 접근 시 로그인 여부 체크. Supabase Auth면 `getSession()`으로 체크.
- **설문 문항 소스**: MVP에서는 `survey_items.csv`를 JSON으로 변환해 `public/` 또는 API로 제공해도 됨. Supabase 테이블로 옮기면 나중에 관리자에서 수정 가능.
- **저장·불러오기**: survey_saves, chat_saves 테이블과 연동. user_email은 세션 또는 Auth에서 가져오기.

### 오류 체크·확인 사항 (Phase 3)

| 확인 항목 | 방법 | 통과 기준 |
|-----------|------|-----------|
| 비로그인 시 /dashboard 접근 | 브라우저에서 /dashboard 직접 입력 | 로그인 페이지로 리다이렉트 |
| 로그인 후 대시보드 진입 | user@test.com / pass1234 로 로그인 | 헤더에 사용자명, 사이드바에 Step 1~5 표시 |
| Step 1 설문 제출 | 1~5점 입력 후 제출 | 200 응답 또는 결과 화면으로 전환 |
| 저장·불러오기 모달 | 버튼 클릭 | 목록 API 호출, 모달에 목록 표시(빈 목록이어도 됨) |
| 모바일 햄버거 | 1024px 미만에서 메뉴 열기 | 사이드바 토글, 백드롭 클릭 시 닫힘 |

### 대응방안 (Phase 3)

| 문제 | 원인 | 대응 |
|------|------|------|
| 로그인 후 무한 리다이렉트 | 세션/쿠키 미설정 또는 미들웨어 조건 오류 | 쿠키 설정 path/, sameSite, secure 확인. 미들웨어에서 /dashboard 요청 시만 로그인 체크 |
| Step 1 제출 시 401/403 | API에서 user_email 미전달 또는 RLS | API Route에서 세션/Auth로 user_email 확보 후 Supabase insert 시 전달. RLS면 anon이 아닌 서버 역할 또는 정책 조건 확인 |
| 설문 문항이 안 나옴 | CSV 경로 또는 API 경로 오류 | public/survey_items.json 등 정적 파일 배치 또는 getItems API 경로 확인 |
| 저장 목록이 비어 있음 | RLS로 본인 데이터만 보이는데 테스트 계정에 데이터 없음 | 정상. 설문 저장 한 번 한 뒤 다시 불러오기 테스트 |

---

## Phase 4: 관리자 플로우

### 목표

- /admin 라우트, 관리자만 접근
- 탭 6개: 로그인·회원, 설문저장·진단, 대화저장, 게시판, 뇌파저장, 지표 산출식
- 탭별 목록·상세·수정·삭제 골격

### 단계

| 단계 | 내용 | 산출물 |
|------|------|--------|
| 4-1 | /admin 레이아웃, 관리자 체크(미들웨어 또는 layout) | app/admin/layout.tsx |
| 4-2 | 탭 UI 및 탭별 섹션 | admin 페이지 + 탭 state 또는 URL 쿼리 |
| 4-3 | 로그인·회원: users 목록·상세 | API + 테이블 + 상세 모달 |
| 4-4 | 설문저장·진단, 대화저장: 목록·보기·수정·삭제 | API + 목록 + 모달 |
| 4-5 | 게시판, 뇌파저장, 지표 산출식: 목록·보기·수정·삭제 골격 | 동일 패턴 |

### Cursor 바이브코딩 프롬프트 (Phase 4)

```
[역할·배경]
StartupBrainIndex-MVP2의 관리자 플로우를 구현합니다.
기존 SBI의 static/admin.html과 동일한 탭 구성을 유지합니다.

[참고]
- admin.html: data-tab="login"|"survey_saves"|"chat_saves"|"board"|"eeg_saves"|"indicator_formulas"
- 기존 API: /api/admin/users, /api/admin/table/list/:table_name, /api/admin/table/delete/:table_name/:id, /api/admin/survey/update 등
- 관리자 판별: main.py is_admin(user) -> user["email"] in ["admin@test.com"] 또는 ADMIN_EMAIL 환경변수

[요청]
1) app/admin/layout.tsx를 구현해 주세요.
   - 관리자만 접근: 미들웨어에서 /admin 요청 시 세션/Auth의 이메일이 ADMIN_EMAIL(환경변수)에 포함되는지 확인. 아니면 /login?next=/admin 리다이렉트 또는 "관리자 전용" 메시지
   - 헤더: "관리자 화면", 홈(/), 대시보드(/dashboard), 로그아웃
2) 관리자 탭 UI: 로그인·회원, 설문저장·진단, 대화저장, 게시판, 뇌파저장, 지표 산출식. 탭 클릭 시 해당 섹션만 표시
3) "로그인·회원" 탭: users 테이블 목록(이메일, created_at 등)을 Supabase에서 조회해 테이블로 표시. 행 클릭 시 상세 모달(프로필 필드 읽기 전용)
4) "설문저장·진단", "대화저장" 탭: survey_saves, chat_saves 목록 조회, "보기" 버튼으로 상세 모달, 수정·삭제 버튼은 API 연동 골격
5) "게시판", "뇌파저장", "지표 산출식" 탭: 목록 조회 + 보기/수정/삭제 골격. RLS 또는 API에서 관리자만 쓰기 가능하도록 주석 명시
```

### 단계별 변경 시 주의사항 (Phase 4)

- **관리자 판별**: 클라이언트만 믿지 말고, 목록/삭제/수정 API는 서버에서 한 번 더 관리자 여부 체크.
- **테이블명**: Supabase는 소문자 스네이크. `survey_saves`, `chat_saves` 등.
- **대용량 목록**: list API에 limit/offset 또는 페이지네이션 추가 권장.

### 오류 체크·확인 사항 (Phase 4)

| 확인 항목 | 방법 | 통과 기준 |
|-----------|------|-----------|
| 일반 사용자로 /admin 접근 | user@test.com 로 로그인 후 /admin | 리다이렉트 또는 "관리자 전용" 메시지 |
| 관리자로 /admin 접근 | admin@test.com 로 로그인 후 /admin | 탭 6개 표시, 로그인·회원 탭에 users 목록 |
| 탭 전환 | 각 탭 클릭 | 해당 섹션만 보임, 목록 API 호출 |
| 회원 상세 | users 행 클릭 | 모달에 이메일·프로필 필드 표시 |

### 대응방안 (Phase 4)

| 문제 | 원인 | 대응 |
|------|------|------|
| /admin 접근 시 403 또는 빈 화면 | RLS가 admin 조회 차단 | 관리자 API는 서버 측에서 SUPABASE_SERVICE_ROLE_KEY 사용해 RLS 우회. 클라이언트는 anon으로 목록 조회하지 않거나, 전용 API Route에서만 조회 |
| 탭 전환해도 목록 안 나옴 | API 경로 또는 테이블명 오류 | Network 탭에서 요청 URL·응답 확인. Supabase 테이블명·RLS 정책 확인 |
| 회원 삭제/비밀번호 재설정 401 | API에서 관리자 체크 실패 | 쿠키/세션에 이메일 포함 여부, 서버의 ADMIN_EMAIL 파싱(쉼표 구분) 확인 |

---

## Phase 5: 부가 기능 및 마무리

### 목표

- PDF 보고서 생성·다운로드
- AI 상담(Step 4) 입력·저장·목록
- 다국어(ko/en) 토글
- 반응형·접근성(햄버거, 터치 44px, 위로가기)

### 단계

| 단계 | 내용 | 산출물 |
|------|------|--------|
| 5-1 | PDF: 설문 결과·프로필 반영, 다운로드 | jsPDF 또는 서버 API, "PDF 다운로드" 버튼 |
| 5-2 | AI 상담: 메시지 입력·전송·목록 표시, chat_saves 저장 | Step 4 UI + API |
| 5-3 | 다국어: 메뉴·버튼 문구 ko/en 객체, 언어 전환 버튼 | 훅 또는 컨텍스트 + 버튼 |
| 5-4 | 반응형: 햄버거, 터치 영역, 위로가기 | CSS·이벤트 |

### Cursor 바이브코딩 프롬프트 (Phase 5)

```
[역할·배경]
StartupBrainIndex-MVP2의 부가 기능을 마무리합니다.
기존 SBI의 PDF(report_generator.py, pdf_report.py), AI 상담(api_consult), 다국어(대시보드·관리자 lang-switch), 반응형(dashboard.html 스타일)을 동일 수준으로 유지합니다.

[요청]
1) PDF 보고서: 설문 제출 결과와 사용자 프로필을 반영한 PDF를 생성해 주세요.
   - 클라이언트: jsPDF 또는 @react-pdf/renderer 사용
   - 또는 API Route에서 서버 측 PDF 생성 후 blob 반환
   - "PDF 다운로드" 버튼 클릭 시 파일 다운로드
2) AI 상담(Step 4): 입력창 + 전송 버튼, 대화 목록 표시. 메시지는 Supabase chat_saves 또는 messages 테이블에 저장. 기존 RAG/지식 DB 로직이 있으면 API Route로 이식하거나 "AI 응답 placeholder"로 대체 후 주석
3) 다국어: 대시보드·관리자 화면의 "메뉴", "설문 진단", "로그아웃" 등 주요 문구를 { ko: {...}, en: {...} } 객체로 두고, 언어 전환 버튼으로 토글
4) 반응형: 대시보드 사이드바 1024px 미만에서 햄버거로 열기, 백드롭 클릭 시 닫기. 버튼·입력 필드 min-height 44px. 각 페이지 하단 "위로 가기" 버튼
```

### 단계별 변경 시 주의사항 (Phase 5)

- **PDF 폰트**: 한글 사용 시 jsPDF에 한글 폰트 등록 필요. 또는 서버에서 ReportLab 등으로 생성하면 폰트 경로만 맞추면 됨.
- **AI 응답**: 실제 LLM 연동은 API 키·비용 이슈가 있으므로, MVP에서는 고정 문구 또는 간단한 키워드 응답으로 대체 가능.
- **다국어**: 전체 페이지를 i18n 라이브러리로 바꿀지, 핵심 문구만 객체로 할지 선택. 문서에서는 "핵심 문구만 객체"로 명시.

### 오류 체크·확인 사항 (Phase 5)

| 확인 항목 | 방법 | 통과 기준 |
|-----------|------|-----------|
| PDF 다운로드 | Step 2에서 결과 본 뒤 PDF 버튼 클릭 | 파일 다운로드, 한글 깨지지 않음(또는 영문만) |
| Step 4 메시지 저장 | 메시지 입력 후 전송 | chat_saves에 저장, 목록에 표시 |
| 언어 전환 | EN 버튼 클릭 | 메뉴·버튼 문구가 영문으로 변경 |
| 모바일 터치 | 작은 화면에서 버튼 클릭 | 버튼이 작지 않음(44px 이상), 햄버거 동작 |

### 대응방안 (Phase 5)

| 문제 | 원인 | 대응 |
|------|------|------|
| PDF 한글 깨짐 | jsPDF 기본 폰트에 한글 없음 | Noto Sans KR 등 base64 폰트 추가 또는 서버 측 PDF 생성 |
| AI 상담 저장 시 403 | RLS가 insert 차단 | chat_saves RLS에서 user_email = auth 또는 request로 전달되는지 확인. 서버 API로 insert 시 service role 사용 |
| 언어 전환 후 일부 문구만 영문 | 누락된 키 추가 안 됨 | 공통 객체에 모든 노출 문구 키 추가 후 컴포넌트에서 t('key') 사용 |

---

## Phase 6: 배포 및 검증

### 목표

- Vercel 배포, 환경 변수 설정
- E2E 검증 체크리스트 작성 및 실행

### 단계

| 단계 | 내용 | 산출물 |
|------|------|--------|
| 6-1 | Vercel 프로젝트 연결, 환경 변수 설정, Production 배포 | 배포 URL |
| 6-2 | 회원가입·로그인·설문·결과·PDF·관리자 탭 전 흐름 검증 | 체크리스트 결과 |
| 6-3 | README 최종화(로컬·Supabase·Vercel·관리자 계정) | README.md |

### Cursor 바이브코딩 프롬프트 (Phase 6)

```
[역할·배경]
StartupBrainIndex-MVP2를 Vercel에 배포하고 전체 흐름을 검증합니다.

[요청]
1) README.md를 완성해 주세요.
   - 프로젝트 한 줄 설명
   - 기술 스택: Next.js 14, Tailwind, Supabase, Vercel
   - 로컬 실행: npm install, .env.local 설정, npm run dev
   - Supabase: migrations 실행 순서(001, 002), RLS 요약
   - Vercel 배포: GitHub 연결, 환경 변수(NEXT_PUBLIC_SUPABASE_*, ADMIN_EMAIL 등), Deploy
   - (선택) 관리자 계정: admin@test.com 또는 ADMIN_EMAIL
2) .env.local.example에 배포 시 필요한 모든 변수명과 짧은 설명을 넣어 주세요.
3) docs/checklist.md 또는 README 내 검증 체크리스트를 추가해 주세요.
   - [ ] 회원가입 → 로그인 → 대시보드 진입
   - [ ] Step 1 설문 제출 → Step 2 결과·PDF 다운로드
   - [ ] Step 4 AI 상담 입력·저장
   - [ ] Step 5 게시판 목록·상세
   - [ ] /admin 관리자 로그인 → 탭별 목록·보기
   - [ ] 모바일 반응형(햄버거 메뉴, 터치)
```

### 단계별 변경 시 주의사항 (Phase 6)

- **환경 변수**: Vercel 대시보드에서 NEXT_PUBLIC_* 는 빌드 시 주입. 변경 후 재배포 필요.
- **Supabase URL**: 프로덕션과 개발이 같은 Supabase 프로젝트면 URL 동일. 다르면 env 별도 설정.

### 오류 체크·확인 사항 (Phase 6)

| 확인 항목 | 방법 | 통과 기준 |
|-----------|------|-----------|
| Vercel 빌드 성공 | Push 후 자동 빌드 | Build completed, 배포 URL 접속 가능 |
| 로그인·대시보드 | 배포 URL에서 로그인 | 세션 유지, 대시보드 표시 |
| Supabase 연동 | 설문 제출·저장 | DB에 행 추가됨 |
| 관리자 /admin | admin 계정으로 로그인 후 /admin | 탭 목록·데이터 표시 |

### 대응방안 (Phase 6)

| 문제 | 원인 | 대응 |
|------|------|------|
| Vercel 빌드 실패 | TypeScript/ESLint 에러 또는 env 누락 | 로컬에서 npm run build 재현. NEXT_PUBLIC_* 누락 시 Vercel에 추가 후 재배포 |
| 배포 후 로그인 안 됨 | 쿠키 sameSite/secure | Vercel은 HTTPS이므로 secure=true. 도메인 일치 확인 |
| CORS 또는 Supabase 오류 | Supabase URL/Key 잘못됨 | Vercel 환경 변수 철자·값 확인. Supabase 대시보드에서 URL/anon key 복사 |

---

## 요약: 단계별 진행 순서와 프롬프트 사용법

1. **Phase 0**: 위 "Cursor 바이브코딩 프롬프트 (Phase 0)"를 Cursor에 붙여 넣고 실행 → `docs/기능_화면_명세.md` 생성·확인.
2. **Phase 1**: MVP2 폴더 생성 후 Phase 1 프롬프트 실행 → Next 앱·env 예시·README.
3. **Phase 2** ~ **6**: 순서대로 각 Phase 프롬프트를 복사해 Cursor에 붙여 넣고, 생성·수정된 코드를 확인한 뒤 **해당 Phase의 주의사항·오류 체크·대응방안**으로 검증.

각 단계에서 **변경 시 주의사항**을 지키고, **오류 체크** 항목으로 확인한 뒤 문제가 있으면 **대응방안**을 참고해 수정하면 됩니다.

---

## 프롬프트 사용법 요약 (Cursor에서 실행 예시)

1. **Cursor 채팅**을 연다.
2. 해당 Phase의 **"Cursor 바이브코딩 프롬프트"** 블록 **전체**를 복사해 붙여 넣는다.
3. **전송** 후 AI가 생성·수정한 파일을 연다. (예: `docs/기능_화면_명세.md`, `app/dashboard/layout.tsx`)
4. 해당 Phase의 **오류 체크·확인 사항** 표를 보고 로컬에서 한 번씩 확인한다.
5. 문제가 있으면 **대응방안** 표에서 유사한 현상을 찾아 적용한 뒤, 필요 시 프롬프트에 "오류: ~ 가 발생했다. 대응방안대로 수정해 줘." 처럼 추가 요청한다.

**예시 (Phase 3 실행 후):**

- "로그인 후 /dashboard 들어가면 헤더에 사용자명이 안 나와."  
  → Phase 3 대응방안 "로그인 후 무한 리다이렉트" 외에, 레이아웃에서 세션/Auth에서 사용자명을 가져오는 부분이 있는지 확인하라고 프롬프트 보완 요청.
- "Step 1 제출 시 401이 나와."  
  → Phase 3 대응방안 "Step 1 제출 시 401/403" 참고 후, "API Route에서 세션의 user_email을 Supabase insert 시 넣어 주세요"라고 구체적으로 요청.

---

## 추가로 검토할 내용

문서와 실제 작업 전·후에 아래 항목을 한 번씩 점검하면 누락과 오류를 줄일 수 있습니다.

### 1. 문서·명세 vs 실제 코드 일치

| 검토 항목 | 확인 방법 | 비고 |
|-----------|-----------|------|
| API 엔드포인트 목록 | `main.py` 또는 라우터에서 실제 경로 grep | 명세에 없는 POST/GET이 있으면 명세 보완 |
| DB 컬럼명 | `create_tables_mysql.sql` vs Phase 2 마이그레이션 | PostgreSQL로 옮길 때 타입·이름 매핑 일치 |
| 설문 문항 수·순번 | `survey_items.csv` 또는 `data_loader.py` (1~96) | MVP2에서 동일 소스(JSON/테이블) 사용 여부 |
| 관리자 판별 조건 | `main.py`의 `is_admin()` 또는 환경변수 | MVP2에서 `ADMIN_EMAIL`과 동일 로직인지 |

### 2. 참조 레포·자산

| 검토 항목 | 확인 방법 | 비고 |
|-----------|-----------|------|
| awakening-1s 레포 | Next 14 + Supabase + Vercel 구조 참고 | 로그인/대시보드/미들웨어 패턴 재사용 가능 |
| 지표 산출식 시드 데이터 | `api_admin_indicator_formula_seed` 호출 시 삽입되는 데이터 | MVP2 DB 마이그레이션 또는 시드 스크립트에 반영 |
| 정적 자산 | `static/` (로고, mobile-common.css 등) | MVP2 `public/` 또는 Next 정적 파일로 복사 경로 정리 |

### 3. 보안·환경

| 검토 항목 | 확인 방법 | 비고 |
|-----------|-----------|------|
| 비밀번호 저장 | 기존 `user_storage._hash_password` (bcrypt 등) | Supabase Auth 사용 시 Supabase가 처리. 커스텀 users면 동일 알고리즘 유지 |
| 세션/쿠키 | HttpOnly, SameSite, Secure (배포 시) | Phase 3·6 대응방안과 함께 점검 |
| 환경 변수 노출 | `NEXT_PUBLIC_*` 만 클라이언트 노출 | 서비스 역할 키·비밀번호는 서버 전용 |

### 4. 테스트·품질

| 검토 항목 | 확인 방법 | 비고 |
|-----------|-----------|------|
| 기존 테스트 스크립트 | `test_*.py`, `run_5cycle_test.py` 등 | MVP2에서는 Playwright/Cypress 또는 수동 체크리스트로 대체 가능 |
| Phase 6 체크리스트 | 문서 내 "검증 체크리스트" | 실제 배포 후 한 번씩 실행해 기록 |
| TypeScript/ESLint | MVP2에서 `npm run build`, `npm run lint` | Phase 1 이후 각 Phase 완료 시 빌드 통과 여부 확인 |

### 5. 문서 자체

| 검토 항목 | 확인 방법 | 비고 |
|-----------|-----------|------|
| 프롬프트 내 경로 | "기존 프로젝트 경로", "StartupBrainIndex-MVP2" | 실제 사용하는 경로/폴더명과 일치하는지 |
| Phase 순서 의존성 | Phase 2 → 3 → 4 | DB/인증(2) 완료 후 사용자(3)·관리자(4) 진행. 순서 바꾸지 않기 |
| 버전/날짜 | 문서 상단 또는 푸터 | "최종 검토: YYYY-MM-DD" 등 필요 시 추가 |

---

## 다음 단계 (실행 순서)

지금 문서까지 준비된 상태에서의 권장 진행 순서입니다.

### 즉시 할 일 (문서 기준)

1. **Phase 0 실행**
   - 현재 워크스페이스(`project2_StartupBrainIndex`)에서 Cursor 채팅에 **Phase 0 프롬프트** 붙여 넣고 실행.
   - 생성된 `docs/기능_화면_명세.md`를 열어 **추가 검토** 표의 "문서·명세 vs 실제 코드" 항목으로 한 번 검증.
2. **MVP2 폴더·저장소 결정**
   - `StartupBrainIndex-MVP2` 폴더를 **어디에** 둘지 결정 (현재 프로젝트 상위 vs 별도 경로).
   - 필요 시 GitHub 저장소 생성 후 MVP2 폴더를 해당 저장소와 연결.
3. **Phase 1 실행**
   - **새 Cursor 창**에서 MVP2 폴더를 열거나, 현재 프로젝트 하위에 MVP2를 두었다면 해당 폴더를 루트로 작업.
   - Phase 1 프롬프트 실행 → Next 앱 생성, `.env.local.example`, README 확인.
   - `npm install` → `npm run dev` 로 기본 페이지 동작 확인.

### 그다음 (Phase 2 ~ 6)

4. **Phase 2**: Supabase 프로젝트 생성 → 마이그레이션(001, 002) 실행 → `docs/phase2-auth.md` 확인.  
5. **Phase 3**: 로그인·대시보드·Step 1~5·저장·불러오기 순으로 구현 후, 오류 체크 표로 검증.  
6. **Phase 4**: `/admin` 접근 제한·탭 6개·목록·상세·수정·삭제 구현 후 검증.  
7. **Phase 5**: PDF, AI 상담, 다국어, 반응형 적용 후 검증.  
8. **Phase 6**: Vercel 연결, 환경 변수 설정, 배포 후 **체크리스트 전 항목** 실행.

### 문서 유지

- Phase를 진행하면서 **실제로 달라진 점**(예: API 경로 변경, 테이블 추가)이 있으면 이 문서와 `docs/기능_화면_명세.md`를 함께 수정.
- "추가로 검토할 내용" 표는 Phase 0 완료 시점, Phase 3 완료 시점, Phase 6 완료 시점에 한 번씩 돌아가며 점검하면 좋습니다.
