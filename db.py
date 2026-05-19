import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date, timedelta
from config import DB_CONFIG
import pandas as pd
from typing import Optional, List, Dict, Any

class DatabaseHandler:
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Установка соединения с базой данных"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("✅ Успешное подключение к базе данных")
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            raise
            
    def disconnect(self):
        """Закрытие соединения"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str):
        """Добавление нового пользователя"""
        query = """
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                updated_at = CURRENT_TIMESTAMP
        """
        self.cursor.execute(query, (user_id, username, first_name, last_name))
        self.conn.commit()
        
    def add_entry(self, user_id: int, mood_score: int, work_hours: float, 
                  sleep_hours: float, comment: Optional[str] = None):
        """Добавление ежедневной записи"""
        today = date.today()
        query = """
            INSERT INTO daily_entries (user_id, entry_date, mood_score, work_hours, sleep_hours, comment)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, entry_date) DO UPDATE
            SET mood_score = EXCLUDED.mood_score,
                work_hours = EXCLUDED.work_hours,
                sleep_hours = EXCLUDED.sleep_hours,
                comment = EXCLUDED.comment
        """
        self.cursor.execute(query, (user_id, today, mood_score, work_hours, sleep_hours, comment))
        self.conn.commit()
        
    def get_week_stats(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики за неделю"""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        query = """
            SELECT 
                AVG(mood_score) as avg_mood,
                AVG(work_hours) as avg_work,
                AVG(sleep_hours) as avg_sleep,
                MAX(mood_score) as best_mood,
                MIN(mood_score) as worst_mood,
                SUM(work_hours) as total_work
            FROM daily_entries
            WHERE user_id = %s AND entry_date BETWEEN %s AND %s
        """
        self.cursor.execute(query, (user_id, start_date, end_date))
        return self.cursor.fetchone()
        
    def get_month_stats(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики за месяц"""
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        query = """
            SELECT 
                AVG(mood_score) as avg_mood,
                AVG(work_hours) as avg_work,
                AVG(sleep_hours) as avg_sleep,
                MAX(mood_score) as best_mood,
                MIN(mood_score) as worst_mood,
                SUM(work_hours) as total_work,
                COUNT(*) as total_days
            FROM daily_entries
            WHERE user_id = %s AND entry_date BETWEEN %s AND %s
        """
        self.cursor.execute(query, (user_id, start_date, end_date))
        return self.cursor.fetchone()
        
    def get_entries_dataframe(self, user_id: int, days: int = 30) -> pd.DataFrame:
        """Получение данных в виде DataFrame для анализа"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = """
            SELECT entry_date, mood_score, work_hours, sleep_hours, comment
            FROM daily_entries
            WHERE user_id = %s AND entry_date BETWEEN %s AND %s
            ORDER BY entry_date
        """
        self.cursor.execute(query, (user_id, start_date, end_date))
        data = self.cursor.fetchall()
        return pd.DataFrame(data)
        
    def get_last_entries(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получение последних записей"""
        query = """
            SELECT entry_date, mood_score, work_hours, sleep_hours, comment
            FROM daily_entries
            WHERE user_id = %s
            ORDER BY entry_date DESC
            LIMIT %s
        """
        self.cursor.execute(query, (user_id, limit))
        return self.cursor.fetchall()
        
    def clear_user_data(self, user_id: int):
        """Очистка всех данных пользователя"""
        query = "DELETE FROM daily_entries WHERE user_id = %s"
        self.cursor.execute(query, (user_id,))
        self.conn.commit()
        
    def save_insight(self, user_id: int, insight_text: str, insight_type: str):
        """Сохранение инсайта"""
        query = """
            INSERT INTO insights (user_id, insight_text, insight_type)
            VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (user_id, insight_text, insight_type))
        self.conn.commit()
        
    def update_settings(self, user_id: int, notifications: bool = None, 
                        notification_time: str = None):
        """Обновление настроек пользователя"""
        if notifications is not None:
            query = "UPDATE users SET notifications_enabled = %s WHERE user_id = %s"
            self.cursor.execute(query, (notifications, user_id))
        if notification_time:
            query = "UPDATE users SET notification_time = %s WHERE user_id = %s"
            self.cursor.execute(query, (notification_time, user_id))
        self.conn.commit()