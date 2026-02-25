-- Startup Brain Index - MySQL 테이블 생성 (dothome.co.kr / localhost)
-- 사용법: MySQL에 DB leejee5 생성 후, 해당 DB에서 본 스크립트 실행.
-- DB: leejee5, 사용자: leejee5, 비밀번호: sunkim5do#

-- 1) 회원 (로그인 정보, 가입 회원 + 프로필)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at VARCHAR(32) NOT NULL,
    name VARCHAR(128) DEFAULT NULL,
    gender VARCHAR(16) DEFAULT NULL,
    age INT DEFAULT NULL,
    occupation VARCHAR(256) DEFAULT NULL,
    nationality VARCHAR(128) DEFAULT NULL,
    sleep_hours DECIMAL(4,1) DEFAULT NULL,
    sleep_hours_label VARCHAR(64) DEFAULT NULL,
    sleep_quality VARCHAR(32) DEFAULT NULL,
    meal_habit VARCHAR(32) DEFAULT NULL,
    bowel_habit VARCHAR(32) DEFAULT NULL,
    exercise_habit VARCHAR(32) DEFAULT NULL,
    UNIQUE KEY uk_email (email),
    KEY idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2) 설문 저장 (데이터 입력/수정/저장)
CREATE TABLE IF NOT EXISTS survey_saves (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    title VARCHAR(512) NOT NULL,
    update_count INT NOT NULL DEFAULT 0,
    responses_json LONGTEXT NOT NULL,
    required_sequences_json TEXT NOT NULL,
    excluded_sequences_json TEXT,
    created_at VARCHAR(32) NOT NULL,
    KEY idx_survey_user (user_email),
    KEY idx_survey_created (created_at),
    KEY idx_survey_title (title(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3) 대화/상담 저장 (생성 콘텐츠)
CREATE TABLE IF NOT EXISTS chat_saves (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    summary_title VARCHAR(512) NOT NULL,
    messages_json LONGTEXT NOT NULL,
    ai_notes_json TEXT,
    created_at VARCHAR(32) NOT NULL,
    KEY idx_chat_user (user_email),
    KEY idx_chat_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4) 게시판 및 자료실
CREATE TABLE IF NOT EXISTS board (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(32) NOT NULL,
    title VARCHAR(256) NOT NULL,
    content TEXT,
    created_at VARCHAR(32) NOT NULL,
    updated_at VARCHAR(32) NOT NULL,
    KEY idx_board_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5) Step3 뇌파 원천데이터 저장
CREATE TABLE IF NOT EXISTS eeg_saves (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    title VARCHAR(512) NOT NULL,
    data_json LONGTEXT NOT NULL,
    created_at VARCHAR(32) NOT NULL,
    KEY idx_eeg_user (user_email),
    KEY idx_eeg_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6) 지표 산출식 (관리자용 목록·수정·삭제·저장)
CREATE TABLE IF NOT EXISTS indicator_formulas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(256) NOT NULL,
    content LONGTEXT NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    created_at VARCHAR(32) NOT NULL,
    updated_at VARCHAR(32) NOT NULL,
    KEY idx_sort (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
