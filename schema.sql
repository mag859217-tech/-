-- Создание базы данных
CREATE DATABASE mood_tracker;

-- Подключение к базе данных
\c mood_tracker;

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC+3',
    notification_time TIME DEFAULT '21:00:00',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица ежедневных записей
CREATE TABLE IF NOT EXISTS daily_entries (
    entry_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    entry_date DATE NOT NULL,
    mood_score INTEGER NOT NULL CHECK (mood_score >= 1 AND mood_score <= 5),
    work_hours DECIMAL(4,1) NOT NULL CHECK (work_hours >= 0 AND work_hours <= 24),
    sleep_hours DECIMAL(4,1) NOT NULL CHECK (sleep_hours >= 0 AND sleep_hours <= 24),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(user_id, entry_date)
);

-- Индексы для оптимизации запросов
CREATE INDEX idx_entries_user_date ON daily_entries(user_id, entry_date);
CREATE INDEX idx_entries_date ON daily_entries(entry_date);
CREATE INDEX idx_entries_mood ON daily_entries(mood_score);

-- Таблица для хранения инсайтов
CREATE TABLE IF NOT EXISTS insights (
    insight_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    insight_text TEXT NOT NULL,
    insight_type VARCHAR(50),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Таблица для настроек пользователя
CREATE TABLE IF NOT EXISTS user_settings (
    setting_id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    language VARCHAR(10) DEFAULT 'ru',
    theme VARCHAR(20) DEFAULT 'default',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);