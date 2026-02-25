# DB 연결·SQL 검토 및 데모 저장·불러오기 테스트 보고

## 1. DB 연결 정보 확인

| 항목 | 설정값 | 파일 위치 |
|------|--------|-----------|
| host | localhost | db.py `DB_CONFIG` |
| database | leejee5 | db.py |
| user | leejee5 | db.py |
| password | sunkim5do# | db.py |

- **결과**: `db.py`에 위와 같이 설정되어 있으며, 요청하신 값과 일치합니다.

---

## 2. SQL 문 검토 결과

### 2.1 create_tables_mysql.sql

- **문법**: 문제 없음. 괄호 균형, 컬럼·키 정의 정상.
- **테이블 6개**: `users`, `survey_saves`, `chat_saves`, `board`, `eeg_saves`, `indicator_formulas`
- **charset**: utf8mb4, InnoDB 사용.

### 2.2 저장 모듈별 SQL 대조

| 테이블 | 모듈 | INSERT 컬럼 | SELECT 컬럼 | 비고 |
|--------|------|-------------|-------------|------|
| users | user_storage | email, password_hash, created_at | id, email, password_hash, created_at | 일치 |
| survey_saves | survey_storage | user_email, title, update_count, responses_json, required_sequences_json, excluded_sequences_json, created_at | 동일 + created_at 조건 | 일치 |
| chat_saves | chat_storage | user_email, summary_title, messages_json, ai_notes_json, created_at | id, summary_title, created_at / get: summary_title, messages_json, ai_notes_json, created_at | 일치 (컬럼명 ai_notes_json) |
| board | board_storage | type, title, content, created_at, updated_at | id, type, title, content, created_at, updated_at | 일치 (날짜 형식 %Y-%m-%dT%H:%M:%SZ, 20자) |
| eeg_saves | eeg_storage | user_email, title, data_json, created_at | id, title, created_at / get: title, data_json, created_at | 일치 |

- **날짜 형식**:  
  - users, survey_saves, chat_saves, eeg_saves: `%Y-%m-%d %H:%M:%S` (19자)  
  - board: `%Y-%m-%dT%H:%M:%SZ` (20자)  
  - 모두 VARCHAR(32) 이내로 사용 가능.

**결론**: SQL 문 오류 없음. 테이블 정의와 각 저장 모듈의 INSERT/SELECT가 일치합니다.

---

## 3. 데모 저장·불러오기 테스트

### 3.1 테스트 스크립트

- **파일**: `test_db_demo_save_load.py`
- **내용**:  
  - DB 연결 및 테이블 존재 확인 (SHOW TABLES)  
  - 회원: 가입(데모 이메일) → 조회 → 비밀번호 확인  
  - 설문: 저장 → 목록 → 한 건 불러오기  
  - 대화: 저장 → 목록 → 한 건 불러오기  
  - 게시판: 등록 → 한 건 조회 → 목록  
  - 뇌파: 저장 → 목록 → 한 건 불러오기  

### 3.2 실행 결과 (본 테스트 환경)

- **실행**: `python test_db_demo_save_load.py`
- **결과**: DB 연결 단계에서 실패  
  - 오류: `(2003, "Can't connect to MySQL server on 'localhost' ...")`  
  - **원인**: 테스트를 실행한 환경에서 MySQL 서버가 기동되어 있지 않거나, localhost에서 접근 불가한 상태였음.

※ 사용자 측에서 “DB는 localhost, leejee5, 잘 작동 중”이라고 하신 경우, 해당 PC에서 MySQL이 실행 중일 때 아래 절차로 다시 확인하시면 됩니다.

### 3.3 MySQL 기동 후 재테스트 방법

1. MySQL 서버 기동 (localhost).
2. DB `leejee5` 생성 및 사용자 `leejee5` / 비밀번호 `sunkim5do#` 권한 확인.
3. `create_tables_mysql.sql` 실행하여 위 6개 테이블 생성.
4. 프로젝트 디렉터리에서:
   ```text
   python test_db_demo_save_load.py
   ```
5. 출력에서 모든 항목이 `[OK]`이면 데모 저장·불러오기 정상.

---

## 4. 요약

| 항목 | 결과 |
|------|------|
| DB 설정 (localhost, leejee5, leejee5, sunkim5do#) | 코드와 일치 |
| SQL 문 오류 | 없음 (테이블·저장 모듈 일치) |
| 데모 데이터 저장·불러오기 테스트 | 스크립트 제공 완료. MySQL 기동 후 `test_db_demo_save_load.py` 실행으로 확인 가능 |

데이터가 DB에 생성되지 않는 경우, 다음을 순서대로 확인하는 것을 권장합니다.

1. MySQL 서비스 실행 여부  
2. `create_tables_mysql.sql` 실행 여부 (테이블 존재 여부)  
3. 방화벽/보안 소프트웨어로 localhost:3306 차단 여부  
4. 위 조건을 만족한 뒤 `test_db_demo_save_load.py` 재실행으로 저장·불러오기 검증  
