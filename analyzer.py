import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import io
from db import DatabaseHandler

class MoodAnalyzer:
    def __init__(self, db: DatabaseHandler):
        self.db = db
        
    def generate_insights(self, user_id: int) -> List[str]:
        """Генерация инсайтов на основе данных пользователя"""
        df = self.db.get_entries_dataframe(user_id, days=30)
        
        if len(df) < 3:
            return ["📊 Недостаточно данных для анализа. Нужно минимум 3 записи."]
            
        insights = []
        
        # Анализ сна и настроения
        sleep_mood_corr = df['sleep_hours'].corr(df['mood_score'])
        if abs(sleep_mood_corr) > 0.3:
            if sleep_mood_corr > 0:
                insights.append(f"💡 Сон и настроение связаны положительно (r={sleep_mood_corr:.2f}). "
                              f"Больше сна = лучше настроение!")
            else:
                insights.append(f"🤔 Обнаружена обратная связь между сном и настроением")
                
        # Анализ работы и настроения
        work_mood_corr = df['work_hours'].corr(df['mood_score'])
        if abs(work_mood_corr) > 0.3:
            if work_mood_corr < 0:
                insights.append(f"⚠️ Длительная работа может снижать настроение (r={work_mood_corr:.2f})")
            else:
                insights.append(f"💪 Продуктивная работа повышает настроение (r={work_mood_corr:.2f})")
                
        # Поиск оптимального режима
        high_mood_df = df[df['mood_score'] >= 4]
        if len(high_mood_df) > 0:
            avg_sleep_good = high_mood_df['sleep_hours'].mean()
            insights.append(f"😊 В дни с хорошим настроением вы спали в среднем {avg_sleep_good:.1f} часов")
            
        # Дни недели
        df['day_of_week'] = pd.to_datetime(df['entry_date']).dt.day_name()
        day_mood = df.groupby('day_of_week')['mood_score'].mean()
        best_day = day_mood.idxmax()
        worst_day = day_mood.idxmin()
        
        day_names_ru = {
            'Monday': 'Понедельник',
            'Tuesday': 'Вторник',
            'Wednesday': 'Среда',
            'Thursday': 'Четверг',
            'Friday': 'Пятница',
            'Saturday': 'Суббота',
            'Sunday': 'Воскресенье'
        }
        
        insights.append(f"📅 Лучший день недели: {day_names_ru.get(best_day, best_day)} "
                       f"(среднее настроение: {day_mood[best_day]:.1f})")
        insights.append(f"😕 Самый сложный день: {day_names_ru.get(worst_day, worst_day)} "
                       f"(среднее настроение: {day_mood[worst_day]:.1f})")
        
        return insights
        
    def create_mood_chart(self, user_id: int) -> io.BytesIO:
        """Создание графика настроения"""
        df = self.db.get_entries_dataframe(user_id, days=14)
        
        plt.figure(figsize=(10, 6))
        
        # График настроения
        plt.subplot(2, 1, 1)
        plt.plot(df['entry_date'], df['mood_score'], 'b-o', linewidth=2, markersize=8)
        plt.fill_between(df['entry_date'], df['mood_score'], alpha=0.3)
        plt.title('Динамика настроения', fontsize=14)
        plt.ylabel('Настроение (1-5)')
        plt.grid(True, alpha=0.3)
        
        # График работы и сна
        plt.subplot(2, 1, 2)
        plt.plot(df['entry_date'], df['work_hours'], 'g-o', label='Работа', linewidth=2)
        plt.plot(df['entry_date'], df['sleep_hours'], 'purple', linestyle='--', 
                marker='s', label='Сон', linewidth=2)
        plt.title('Часы работы и сна', fontsize=14)
        plt.ylabel('Часы')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf
        
    def get_weekly_summary(self, user_id: int) -> str:
        """Формирование недельной сводки"""
        stats = self.db.get_week_stats(user_id)
        
        if not stats or stats['avg_mood'] is None:
            return "📊 Нет данных за последнюю неделю"
            
        summary = (
            f"📊 <b>Статистика за неделю</b>\n\n"
            f"😊 Среднее настроение: {stats['avg_mood']:.1f}/5\n"
            f"💼 Среднее время работы: {stats['avg_work']:.1f} ч/день\n"
            f"😴 Среднее время сна: {stats['avg_sleep']:.1f} ч/день\n"
            f"📈 Всего отработано: {stats['total_work']:.1f} ч\n"
            f"🎯 Лучшее настроение: {stats['best_mood']}/5\n"
            f"📉 Худшее настроение: {stats['worst_mood']}/5"
        )
        
        return summary