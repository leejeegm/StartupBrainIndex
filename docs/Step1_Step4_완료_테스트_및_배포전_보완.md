# Step 1~4 완료 테스트 3회 및 배포 전 보완

## Step 3·Step 4 반영 현황

### Step 3: 뇌파·시각화

| 항목 | 상태 | 비고 |
|------|------|------|
| 뇌파 원천 데이터: 엑셀·텍스트 형식 추가 | ✅ | `.xlsx`, `.xls`, `.txt` 지원. SheetJS로 엑셀 파싱. |
| 불러오기 시 한글 깨짐 방지 | ✅ | `eeg-korean-font` 클래스 (Noto Sans KR, 맑은고딕 등). 미리보기·저장 목록 내용에 적용. |
| 저장 버튼 클릭 시 형식 선택 | ✅ | 서버에 저장 / CSV 다운로드 / **엑셀 다운로드** / 텍스트 다운로드 선택 가능. |
| 저장된 리스트 제목 클릭 시 내용 표시 | ✅ | 목록에서 제목(행) 클릭 시 `eeg-saved-detail`에 내용 표시. |
| 적용·시각화 결과 → PDF 보고서에 추가 | ✅ | "PDF 보고서에 추가" 버튼 + "그 결과가 반영되었습니다." 메시지. |
| 위로가기 버튼 | ✅ | Step 3 패널 하단에 "↑ 위로 가기" (data-goto-top). |

### Step 4: AI 상담

| 항목 | 상태 | 비고 |
|------|------|------|
| AI 상담 결과 보기 화면을 전송 버튼 아래로 이동 | ✅ | 입력창·전송 버튼 → 바로 아래 `chat-messages`(결과) 배치. |
| AI 상담 요약 → PDF 결과 보고서에 추가 | ✅ | "AI 상담 요약을 PDF 결과 보고서에 추가" 버튼 + 반영 메시지. |
| 위로가기 버튼 | ✅ | Step 4 패널 하단에 "↑ 위로 가기". |

---

## Step 1~4 통합 테스트 3회 실행 방법

**사전 조건:** 서버 실행 중 (예: `uvicorn main:app --host 0.0.0.0 --port 8000`)

```bash
# 터미널 1: 서버 기동
cd project2_StartupBrainIndex
uvicorn main:app --host 127.0.0.1 --port 8000

# 터미널 2: 테스트 3회 실행
python test_admin_dashboard_integration.py
python test_admin_dashboard_integration.py
python test_admin_dashboard_integration.py
```

- 테스트 스크립트의 `BASE`가 `http://127.0.0.1:8000`이면 포트 8000 기준.
- 서버를 다른 포트(예: 8001)로 띄운 경우 `test_admin_dashboard_integration.py` 상단 `BASE`를 해당 주소로 수정 후 실행.

**테스트 3회 결과 확인:**

- 3회 모두 "Login OK", Step1~관리자 API 항목 통과 시 정상.
- 1회라도 실패 시: 터미널 출력의 실패 원인(401 로그인, 503 DB 등) 확인 후 수정.

---

## 배포 전 보완 체크리스트

| 순서 | 항목 | 확인 |
|------|------|------|
| 1 | **환경 변수** | `SESSION_SECRET`, `DB_ENGINE`, `DATABASE_URL`(postgres 시) 설정. `.env.example` 참고. |
| 2 | **관리자 비밀번호** | 운영 시 `USERS_DEMO` 대신 DB/환경변수 기반 인증 전환 권장. (현재 데모: admin@test.com / sunkim5AD@#) |
| 3 | **DB** | Render 등에서는 `DB_ENGINE=postgres`, `DATABASE_URL` 연결 권장. 재배포 시 데이터 유지. |
| 4 | **의존성** | `pip install -r requirements.txt` 후 `runtime.txt`(Python 버전) 확인. |
| 5 | **빌드/시작** | Build: `pip install -r requirements.txt` / Start: `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| 6 | **Step 1~4 수동 점검** | 로그인 → 설문(96/71·간편)·불러오기·진단 결과 보기 → Step2 PDF → Step3 뇌파 불러오기·저장 형식·목록 제목 클릭·PDF 추가 → Step4 전송·결과·PDF 추가 동작 확인. |
| 7 | **한글/엑셀** | 뇌파 미리보기·저장 목록 한글, 엑셀 업로드/다운로드 동작 확인. |

---

## 오류 발생 시 참고

- **로그인 401**  
  - 관리자 비밀번호가 `main.py`의 `USERS_DEMO`와 테스트 스크립트의 `ADMIN_PW` 동일한지 확인.
- **DB 503**  
  - `DB_ENGINE`, `DATABASE_URL`(또는 MySQL 설정) 및 DB 서버 접속 가능 여부 확인.
- **PDF 생성 실패**  
  - `reportlab`, 한글 폰트 경로(`fonts/` 또는 시스템 폰트) 확인.
- **엑셀 업로드 실패**  
  - 브라우저 콘솔에서 SheetJS CDN 로드 여부 확인.

---

**정리:** Step 3·4 요청 사항은 모두 반영되어 있습니다. 위 방법으로 테스트 3회 실행 후, 배포 전 체크리스트만 확인하면 배포 가능합니다.
