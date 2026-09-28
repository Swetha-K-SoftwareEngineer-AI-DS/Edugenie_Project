-- =====================================================================
-- EduGenie Database Schema (MySQL 8.0+)
-- =====================================================================
-- Instructions:
-- 1. Log in to MySQL client or phpMyAdmin:
--    mysql -u root -p
-- 2. Execute this script:
--    SOURCE path/to/schema.sql;
-- =====================================================================

-- 1. Create Database if not exists
CREATE DATABASE IF NOT EXISTS edugenie_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE edugenie_db;

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Chat History Table
CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    explanation TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_chat_user (user_id),
    INDEX idx_chat_created (created_at),
    CONSTRAINT fk_chat_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Quiz Attempts Table
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    topic VARCHAR(255) NOT NULL,
    difficulty VARCHAR(50) NOT NULL DEFAULT 'beginner',
    question_count INT NOT NULL DEFAULT 5,
    score INT NOT NULL DEFAULT 0,
    feedback TEXT NULL,
    quiz_data JSON NULL,
    user_answers JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_quiz_user (user_id),
    INDEX idx_quiz_created (created_at),
    CONSTRAINT fk_quiz_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Learning Paths Table
CREATE TABLE IF NOT EXISTS learning_paths (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    topic VARCHAR(255) NOT NULL,
    level VARCHAR(50) NOT NULL DEFAULT 'beginner',
    goal VARCHAR(255) NOT NULL,
    daily_time INT NOT NULL DEFAULT 60,
    duration VARCHAR(100) NOT NULL DEFAULT '4 weeks',
    roadmap_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_lp_user (user_id),
    INDEX idx_lp_created (created_at),
    CONSTRAINT fk_lp_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Summaries Table
CREATE TABLE IF NOT EXISTS summaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    title VARCHAR(255) NULL,
    original_text TEXT NOT NULL,
    summary TEXT NOT NULL,
    key_points JSON NULL,
    important_terms JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_summary_user (user_id),
    INDEX idx_summary_created (created_at),
    CONSTRAINT fk_summary_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Optional sample user (Password: student123 - bcrypt hash placeholder)
-- INSERT IGNORE INTO users (id, name, email, password_hash) 
-- VALUES (1, 'Demo Student', 'student@edugenie.local', '$2b$12$KIXeJ1o6xK6rL4k7z/Yq/uQcK2eG1w3yK8mD6z5X8yL6z5X8yL6z5');
