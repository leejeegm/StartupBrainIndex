# 관리자 메뉴 정상 작동 및 DB 연결 조치 방안

## 적용한 수정 사항

### 1. 메뉴 클릭 시 500/503 오류 제거

- **원인**: 설문저장, 대화저장, 게시판, 뇌파저장, 지표 산출식, 설문진단 조회 등은 모두 MySQL을 사용하는데, MySQL이 실행되지 않으면 연결 오류로 500/503이 발생했습니다.
- **수정**: DB 연결 실패 시에도 **HTTP 200**을 반환하고, **빈 목록(`items: []`) + 안내 메시지**를 내려주도록 변경했습니다.
  - `GET /api/admin/tables/{table_name}` (설문저장, 대화저장, 게시판, 뇌파저장, 지표 산출식)
  - `GET /api/admin/survey-diagnosis-list` (설문진단 조회)
  - `GET /api/survey-saved-list`, `/api/chat-saved-list`, `/api/eeg-saved-list`, `/api/board-list`
- **결과**: 모든 메뉴를 클릭해도 500/503이 나오지 않고, 빈 테이블과 함께 "데이터베이스에 연결할 수 없습니다. MySQL 서버가 실행 중인지, DB 호스트 설정(환경변수 DB_HOST)이 맞는지 확인해 주세요." 같은 안내가 표시됩니다.

### 2. 관리자 화면(admin.html) 메시지 표시

- API가 반환한 `message`가 있으면 해당 문구를 노란색 안내 영역으로 표시합니다.
- 설문진단 조회에서도 DB 오류 메시지가 있으면 같은 방식으로 표시합니다.

### 3. Pydantic 경고 제거

- `@validator`를 Pydantic V2 방식인 `@field_validator` + `@classmethod`로 변경해, 터미널에 나오던 `PydanticDeprecatedSince20` 경고가 발생하지 않도록 수정했습니다.

---

## DB 연결 시 정상 데이터를 보려면 (조치 방안)

1. **MySQL 서버 실행**  
   - 로컬에서 사용하는 경우: MySQL 서비스를 시작합니다.  
   - Windows: 서비스에서 MySQL 시작 또는 `net start MySQL`  
   - Mac/Linux: `sudo service mysql start` 또는 `brew services start mysql` 등

2. **DB 설정 확인**  
   - `db.py`의 `DB_CONFIG` 또는 환경변수 사용:
     - `DB_HOST`: 기본값 `localhost` (원격 DB 사용 시 해당 호스트로 설정)
     - `DB_USER`, `DB_PASSWORD`, `DB_NAME`: 필요 시 설정
   - 호스팅(예: dothome)에서 DB가 별도 호스트로 제공되면, 해당 호스트를 `DB_HOST`에 넣습니다.

3. **테이블 생성**  
   - `create_tables_mysql.sql`로 필요한 테이블(users, survey_saves, chat_saves, board, eeg_saves, indicator_formulas 등)이 생성되어 있는지 확인합니다.

4. **서버 재시작**  
   - MySQL을 켠 뒤 `python main.py`(또는 uvicorn)으로 서버를 다시 띄우면, 관리자 메뉴에서 실제 데이터가 조회·수정·삭제됩니다.

---

## 요약

- **지금 상태**: MySQL이 없어도 관리자 메뉴를 클릭하면 오류 없이 열리고, 빈 목록 + DB 연결 안내 메시지가 표시됩니다.
- **데이터가 보이게 하려면**: 위 1~4에 따라 MySQL을 실행하고 DB 설정을 맞춘 뒤 서버를 재시작하면 됩니다.
