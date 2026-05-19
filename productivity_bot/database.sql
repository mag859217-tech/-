-- Таблица для ежедневных записей
CREATE TABLE IF NOT EXISTS daily_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    user_name VARCHAR(100),
    log_date DATE NOT NULL DEFAULT CURRENT_DATE,
    mood INTEGER CHECK (mood >= 1 AND mood <= 5),
    productive_hours DECIMAL(3,1) CHECK (productive_hours >= 0 AND productive_hours <= 24),
    sleep_hours DECIMAL(3,1) CHECK (sleep_hours >= 0 AND sleep_hours <= 24),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, log_date)
);

CREATE INDEX IF NOT EXISTS idx_user_id ON daily_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_log_date ON daily_logs(log_date);

-- Таблица для настроек
CREATE TABLE IF NOT EXISTS user_settings (
    user_id BIGINT PRIMARY KEY,
    reminder_time TIME DEFAULT '21:00:00',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT '✅ Таблицы созданы!' as status;