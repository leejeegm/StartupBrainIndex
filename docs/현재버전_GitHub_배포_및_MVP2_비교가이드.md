# 현재 버전(Git/GitHub) 배포 테스트 → MVP2 비교 가이드

**목표**: 지금 Python(FastAPI) 버전을 GitHub에 올리고 배포 테스트한 뒤, 나중에 MVP2와 성능·안정성을 비교할 수 있도록 정리합니다.

---

## 1. 지금부터 할 일 (순서)

### Step 1: Git 초기화 및 첫 커밋

프로젝트 루트(`project2_StartupBrainIndex`)에서:

```bash
# 1) Git 초기화
git init

# 2) .gitignore 확인 (이미 있음: db_config.json, .env, venv, __pycache__, *.db, output/)
# 비밀번호·DB 설정이 커밋되지 않도록 확인

# 3) 전체 추가 후 커밋
git add .
git status   # db_config.json, .env, venv 등이 빠져 있는지 확인
git commit -m "Initial commit: SBI FastAPI + static dashboard/admin"
```

**주의**: `db_config.json`, `.env`에는 DB 비밀번호 등이 들어갈 수 있으므로 반드시 `.gitignore`에 포함되어 있어야 합니다. 이미 포함되어 있습니다.

---

### Step 2: GitHub 저장소 생성 및 푸시

1. **GitHub** 접속 → **New repository**
   - 이름 예: `StartupBrainIndex` 또는 `sbi-mvp1`
   - Public/Private 선택
   - **README, .gitignore 추가하지 말고** 빈 저장소로 생성 (이미 로컬에 있음)

2. **로컬에서 원격 연결 후 푸시** (GitHub에서 안내하는 URL 사용):

```bash
git remote add origin https://github.com/YOUR_USERNAME/StartupBrainIndex.git
git branch -M main
git push -u origin main
```

---

### Step 3: 배포 테스트 (현재 버전) — **Render 사용**

배포는 **Render**로 진행합니다. (무료·안정성·가성비 기준)

- **상세 절차**: [docs/Render_배포_가이드.md](Render_배포_가이드.md) 참고
- **설정 요약**:
  - **Build**: `pip install -r requirements.txt`
  - **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
  - **환경 변수**: `SESSION_SECRET`(필수), `DB_ENGINE`, `DB_NAME` (대시보드에서 설정)
- 루트의 `render.yaml`은 Blueprint 사용 시 참고용입니다 (수동 설정만 해도 됨).

**배포 후 확인**:
- [ ] 루트 `/` 접속
- [ ] `/login` → 로그인 → `/dashboard` 진입
- [ ] Step 1 설문 제출
- [ ] `/admin` (관리자 계정으로) 접속·탭 동작
- [ ] PDF 다운로드 등 핵심 기능 동작

이 결과를 **“현재 버전 기준”**으로 기록해 두면, 나중에 MVP2와 비교할 때 유리합니다.

---

### Step 4: (나중에) MVP2 전환 후 비교

MVP2(Next.js + Supabase + Vercel)를 같은 기능으로 구축한 뒤, 아래 항목으로 비교하면 됩니다.

| 비교 항목 | 현재 버전 (기록) | MVP2 (나중에 기록) |
|-----------|------------------|---------------------|
| 배포 난이도 | (Railway/Render 등 설정 단계 수) | Vercel 연결·env 설정 |
| 빌드/시작 시간 | (초 단위) | (초 단위) |
| 로그인→대시보드 체감 속도 | (빠름/보통/느림) | (빠름/보통/느림) |
| 설문 제출·저장 응답 | (ms 또는 체감) | (ms 또는 체감) |
| 관리자 탭 전환·목록 로딩 | (체감) | (체감) |
| 모바일 반응형 | (동작 여부) | (동작 여부) |
| 운영 비용(월) | (무료 티어 또는 금액) | (Vercel/Supabase 무료 티어 등) |

문서는 `docs/MVP2_개발프로세스_및_바이브코딩_프롬프트.md`의 Phase 0~6을 따라 진행하면 됩니다.

---

## 2. 요약

1. **지금**: `git init` → `git add .` → `git commit` → GitHub 저장소 생성 → `git push`
2. **이어서**: Railway/Render/Fly.io 중 하나로 현재 버전 배포 → 위 체크리스트로 배포 테스트
3. **나중에**: MVP2 구축 후 같은 체크리스트 + 비교 표로 **현재 버전 vs MVP2** 성능·안정성·운영 난이도 비교

이렇게 하면 “현재 버전 기준선”이 있어서 MVP2 전환 효과를 객관적으로 볼 수 있습니다.
