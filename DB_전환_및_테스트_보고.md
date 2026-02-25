# DB 전환 및 기능 테스트 보고

## 1. 완료된 작업 요약

### 1) MySQL 전환
- **`create_tables_mysql.sql`**: 테이블 생성 스크립트 작성
  - `users` (회원/로그인)
  - `survey_saves` (설문 저장)
  - `chat_saves` (대화/상담 저장)
  - `board` (게시판·자료실)
- **`db.py`**: MySQL 연결 모듈 추가 (localhost, DB: leejee5, 사용자: leejee5, 비밀번호: sunkim5do#)
- **`requirements.txt`**: PyMySQL 추가
- **스토리지 MySQL 전환**
  - `user_storage.py` → MySQL `users` 테이블
  - `survey_storage.py` → MySQL `survey_saves` 테이블
  - `chat_storage.py` → MySQL `chat_saves` 테이블
  - `board_storage.py` 신규 추가 → MySQL `board` 테이블
- **`main.py`**: 게시판 API가 in-memory `BOARD_STORE` 대신 `board_storage`(MySQL) 사용하도록 수정

### 2) 기존 반영 사항 (대화 요약 기준)
- 설문 저장 제목: `[전체설문]` / `[간편설문랜덤]` 표시
- 설문 불러오기: 목록 스크롤, 제목(머리말) 검색
- 초기·로그인 화면: 맨 밑 "처음으로 가기" 버튼 삭제됨
- 관리자 화면: 회원관리(목록/삭제) 포함

---

## 2. 오류 테스트 결과

### 2.1 코드/임포트 테스트
- **결과**: 통과
- `db`, `user_storage`, `survey_storage`, `chat_storage`, `board_storage` 임포트 정상.
- MySQL 미실행 환경에서 `list_items()` 호출 시 `ConnectionRefusedError` 발생 → 설정된 localhost 연결 시도 확인됨.

### 2.2 MySQL 연결 전제조건
- **localhost**에서 MySQL 서버 실행 필요.
- DB **leejee5** 생성 후 `create_tables_mysql.sql` 실행 필요.
- 사용자 **leejee5** / 비밀번호 **sunkim5do#** 로 해당 DB 접속 가능해야 함.

### 2.3 관리자·회원관리
- **API**: `GET /api/admin/users`, `POST /api/admin/users/delete` 존재.
- **admin.html**: `/api/admin/users` 호출로 회원 목록 로드, 삭제 시 `/api/admin/users/delete` 호출.
- 로그인 세션 기반 관리자 인증은 기존대로 유지.

### 2.4 예상 오류 및 대응
| 상황 | 현상 | 조치 |
|------|------|------|
| MySQL 미실행 | `ConnectionRefusedError` / `OperationalError (2003)` | MySQL 서비스 기동, dothome 호스팅이면 DB 생성·테이블 스크립트 실행 |
| 테이블 없음 | `ProgrammingError` (테이블/컬럼 없음) | `create_tables_mysql.sql` 실행 |
| 이메일 중복 가입 | `ValueError("이미 등록된 이메일입니다.")` | `user_storage`에서 `pymysql.IntegrityError` 처리함 |

---

## 3. 배포 시 체크리스트 (dothome)

1. MySQL에서 DB `leejee5` 생성.
2. `create_tables_mysql.sql` 내용을 해당 DB에서 실행해 테이블 생성.
3. 사용자 `leejee5`에 DB `leejee5` 권한 부여, 비밀번호 `sunkim5do#` 설정.
4. 앱 서버가 MySQL에 **localhost**로 접속하는지 확인 (dothome이 동일 서버에서 DB 제공 시 localhost 사용).

---

## 4. 파일 변경 목록

| 파일 | 변경 내용 |
|------|-----------|
| `create_tables_mysql.sql` | 신규. MySQL 테이블 4개 생성 |
| `db.py` | 신규. MySQL 연결·헬퍼 |
| `requirements.txt` | PyMySQL 추가 |
| `user_storage.py` | SQLite 제거, MySQL 사용 |
| `survey_storage.py` | SQLite 제거, MySQL 사용 |
| `chat_storage.py` | SQLite 제거, MySQL 사용 |
| `board_storage.py` | 신규. board 테이블 CRUD |
| `main.py` | BOARD_STORE 제거, board_storage 사용 |
