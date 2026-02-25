-- 회원 프로필 컬럼 추가 (기존 MySQL DB 적용용)
-- 사용법: 이미 생성된 DB에서 실행. 컬럼이 이미 있으면 오류 나므로 한 번만 실행.
-- SQLite는 db.py 초기화 시 자동 반영됨.

ALTER TABLE users ADD COLUMN name VARCHAR(128) DEFAULT NULL;
ALTER TABLE users ADD COLUMN gender VARCHAR(16) DEFAULT NULL;
ALTER TABLE users ADD COLUMN age INT DEFAULT NULL;
ALTER TABLE users ADD COLUMN occupation VARCHAR(256) DEFAULT NULL;
ALTER TABLE users ADD COLUMN sleep_hours DECIMAL(4,1) DEFAULT NULL;
ALTER TABLE users ADD COLUMN meal_habit VARCHAR(32) DEFAULT NULL;
ALTER TABLE users ADD COLUMN bowel_habit VARCHAR(32) DEFAULT NULL;
ALTER TABLE users ADD COLUMN exercise_habit VARCHAR(32) DEFAULT NULL;

-- 수면 구간·수면의 질 (기존 DB에 없으면 추가)
 ALTER TABLE users ADD COLUMN sleep_hours_label VARCHAR(64) DEFAULT NULL;
 ALTER TABLE users ADD COLUMN sleep_quality VARCHAR(32) DEFAULT NULL;
