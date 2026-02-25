-- Startup Brain Index - PostgreSQL (Supabase) 테이블
-- 사용법: Supabase Dashboard → SQL Editor에서 본 스크립트 실행

-- 1) 회원
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
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
    exercise_habit VARCHAR(32) DEFAULT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2) 설문 저장
CREATE TABLE IF NOT EXISTS survey_saves (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    title VARCHAR(512) NOT NULL,
    update_count INT NOT NULL DEFAULT 0,
    responses_json TEXT NOT NULL,
    required_sequences_json TEXT NOT NULL,
    excluded_sequences_json TEXT,
    created_at VARCHAR(32) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_survey_user ON survey_saves(user_email);
CREATE INDEX IF NOT EXISTS idx_survey_created ON survey_saves(created_at);
CREATE INDEX IF NOT EXISTS idx_survey_title ON survey_saves(title);

-- 3) 대화/상담 저장
CREATE TABLE IF NOT EXISTS chat_saves (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    summary_title VARCHAR(512) NOT NULL,
    messages_json TEXT NOT NULL,
    ai_notes_json TEXT,
    created_at VARCHAR(32) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_saves(user_email);
CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_saves(created_at);

-- 4) 게시판
CREATE TABLE IF NOT EXISTS board (
    id SERIAL PRIMARY KEY,
    type VARCHAR(32) NOT NULL,
    title VARCHAR(256) NOT NULL,
    content TEXT,
    created_at VARCHAR(32) NOT NULL,
    updated_at VARCHAR(32) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_board_type ON board(type);

-- 5) 뇌파 저장
CREATE TABLE IF NOT EXISTS eeg_saves (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    title VARCHAR(512) NOT NULL,
    data_json TEXT NOT NULL,
    created_at VARCHAR(32) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_eeg_user ON eeg_saves(user_email);
CREATE INDEX IF NOT EXISTS idx_eeg_created ON eeg_saves(created_at);

-- 6) 지표 산출식
CREATE TABLE IF NOT EXISTS indicator_formulas (
    id SERIAL PRIMARY KEY,
    title VARCHAR(256) NOT NULL,
    content TEXT NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    created_at VARCHAR(32) NOT NULL,
    updated_at VARCHAR(32) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_indicator_sort ON indicator_formulas(sort_order);
