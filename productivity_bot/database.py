import asyncpg
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(**DB_CONFIG, min_size=1, max_size=10)
            print("✅ Подключение к PostgreSQL установлено!")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            return False

    async def save_daily_log(self, user_id, user_name, log_date, mood, productive_hours, sleep_hours):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO daily_logs (user_id, user_name, log_date, mood, productive_hours, sleep_hours)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id, log_date) DO UPDATE SET
                    mood = EXCLUDED.mood,
                    productive_hours = EXCLUDED.productive_hours,
                    sleep_hours = EXCLUDED.sleep_hours
            """, user_id, user_name, log_date, mood, productive_hours, sleep_hours)
            print(f"✅ Данные сохранены")

    async def get_stats(self, user_id, days=30):
        async with self.pool.acquire() as conn:
            averages = await conn.fetchrow("""
                SELECT 
                    COALESCE(AVG(mood), 0) as avg_mood,
                    COALESCE(AVG(productive_hours), 0) as avg_productivity,
                    COALESCE(AVG(sleep_hours), 0) as avg_sleep,
                    COUNT(*) as total_days
                FROM daily_logs
                WHERE user_id = $1 AND log_date >= CURRENT_DATE - $2::interval
            """, user_id, f'{days} days')
            
            best_days = await conn.fetch("""
                SELECT log_date, mood, productive_hours, sleep_hours
                FROM daily_logs
                WHERE user_id = $1 AND log_date >= CURRENT_DATE - $2::interval
                ORDER BY mood DESC
                LIMIT 5
            """, user_id, f'{days} days')
            
            return averages, best_days

    async def get_correlation(self, user_id):
        async with self.pool.acquire() as conn:
            correlation = await conn.fetchval("""
                SELECT CORR(sleep_hours, productive_hours) 
                FROM daily_logs
                WHERE user_id = $1 
                  AND sleep_hours IS NOT NULL 
                  AND productive_hours IS NOT NULL
            """, user_id)
            return correlation if correlation else 0

db = Database()