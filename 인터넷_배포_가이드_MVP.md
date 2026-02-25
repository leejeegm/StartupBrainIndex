# 인터넷 배포 가이드 — 어디서든 회원가입·실전 테스트 (MVP)

MVP를 인터넷에 열어 **어디서든 회원가입하고 사용**할 수 있게 하는 방법을 정리했습니다.  
(1만 명 동시 접속은 현재 구조로는 불가하며, 별도 확장이 필요합니다. → `MVP_성능한계_테스트보고.md` 참고)

---

## 방법 1: ngrok으로 PC 서버 임시 공개 (가장 빠름)

개인 PC에서 서버를 띄운 뒤, 터널로 인터넷에 URL 하나 열어줍니다.

### 1. ngrok 가입 및 설치

1. https://ngrok.com 가입 후 로그인
2. 다운로드: https://ngrok.com/download  
   또는 Chocolatey: `choco install ngrok`
3. 로그인 토큰 설정:  
   `ngrok config add-authtoken 본인토큰`

### 2. 서버 실행 후 터널 열기

```bash
# 터미널 1: SBI 서버 실행
cd c:\vibeTest\project2_StartupBrainIndex
python main.py

# 터미널 2: 터널 (서버 포트가 8000일 때)
ngrok http 8000
```

콘솔에 나오는 **Forwarding URL** (예: `https://xxxx.ngrok-free.app`) 이 **인터넷 공개 주소**입니다.  
이 주소를 모바일·다른 PC에서 열면 회원가입·로그인·설문 등이 가능합니다.

### 3. 주의사항

- PC와 서버를 끄면 URL도 접속 불가
- 무료 플랜은 URL이 재시작 시 바뀜
- 실전 테스트·데모용으로 적합, 장기 상시 서비스에는 클라우드 배포 권장

---

## 방법 2: 공유기 포트포워딩 (집 PC를 고정 공인 IP처럼 쓰기)

집 PC를 “작은 서버”로 두고, 공유기에서 8000 포트를 PC로 연결하는 방식입니다.

1. **PC 고정 IP(내부)**  
   공유기 관리 페이지 → DHCP 예약/고정 IP → PC MAC 주소에 192.168.x.x 고정 부여

2. **포트포워딩**  
   공유기 관리 페이지 → 포트포워딩/가상 서버:
   - 외부 포트: **8000**
   - 내부 IP: **PC 고정 IP**
   - 내부 포트: **8000**
   - 프로토콜: **TCP**

3. **PC에서 서버 실행**  
   `run_server.bat` 또는 `python main.py` (0.0.0.0으로 이미 바인딩됨)

4. **접속 주소**  
   `http://(공인IP):8000/`  
   공인 IP: 공유기 관리 페이지 또는 “내 IP” 검색

5. **보안**  
   관리자/회원 비밀번호 강화, 가능하면 관리자 페이지는 IP 제한 등 추가 권장.

---

## 방법 3: 클라우드에 배포 (실전·부하 테스트용)

“어디서든 연중무휴” + 나중에 동시 접속 늘리기에 적합합니다.

### 3-1. Render (무료 티어 있음)

1. https://render.com 가입
2. New → Web Service → 저장소 연결 (GitHub 등)
3. 설정 예:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment: `PORT`(자동), MySQL 쓰면 `DB_HOST`, `DB_USER` 등 추가

4. DB가 MySQL인 경우: Render PostgreSQL 또는 외부 MySQL URL을 환경변수로 지정

배포 후 `https://서비스이름.onrender.com` 형태로 접속 가능.

### 3-2. Railway

1. https://railway.app 가입
2. New Project → Deploy from GitHub (또는 로컬 업로드)
3. 루트에 `Procfile`:  
   `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Variables에 `PORT`(자동), `SESSION_SECRET`, DB 관련 변수 설정

### 3-3. Fly.io

1. https://fly.io 가입, `flyctl` 설치
2. 프로젝트 폴더에서:  
   `fly launch`  
   `fly deploy`
3. `fly.toml` 에서 포트·환경변수 설정

---

## 방법 4: 서버가 인터넷에서 접속 가능한지 확인

- **로컬만**: `http://127.0.0.1:8000` → 같은 PC에서만
- **같은 Wi‑Fi**: `http://(PC의 IPv4):8000` → 같은 LAN
- **인터넷**: ngrok URL, `http://공인IP:8000`, 또는 클라우드 URL

배포 후 **다른 네트워크(휴대폰 데이터 등)** 에서 위 주소로 접속해 보면 “어디서든” 동작 여부를 확인할 수 있습니다.

---

## 요약

| 목적 | 추천 |
|------|------|
| 빠르게 전 세계에서 접속 가능하게 (데모·소규모 실전 테스트) | **ngrok** (방법 1) |
| 집 PC를 고정 주소처럼 쓰기 | **포트포워딩** (방법 2) |
| 상시 서비스·나중에 1만 명급 확장 | **클라우드 배포** (방법 3) |

동시 접속 1만 명은 현재 MVP 한 대로는 불가하므로, 실전 테스트는 **소규모(수십 명)** 로 진행하고, 성능 한계는 `MVP_성능한계_테스트보고.md` 및 `load_test.py` 재측정으로 확인하는 것을 권장합니다.

---

## 티스토리 등 블로그에서 사용자 테스트 유도하기

**앱 전체를 블로그 글 안에 HTML로 넣어 실행하는 것은 불가능합니다.**  
SBI는 서버(로그인, DB, API, PDF 생성)가 필요한 웹 앱이라, 블로그는 정적 HTML만 허용하기 때문입니다.

**가능한 방법**: 블로그에는 **「참여하기」 버튼(링크)** 만 넣고, 클릭 시 **배포해 둔 SBI 주소**로 이동시키면 됩니다.

1. SBI를 먼저 인터넷에 공개합니다 (ngrok, 포트포워딩, Render 등).
2. 프로젝트 폴더의 **`tistory_삽입용_HTML.html`** 을 열어, `YOUR_SBI_URL` 을 위에서 만든 주소로 바꿉니다.
3. 티스토리 글쓰기 → **HTML** 모드 → 해당 HTML 코드를 붙여넣기 → 저장/발행.

이렇게 하면 글을 읽는 사람이 버튼을 눌러 **새 탭에서 SBI 사이트**로 이동해 회원가입·설문·사용자 테스트를 할 수 있습니다.
