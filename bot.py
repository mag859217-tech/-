import telebot
from telebot import types
from config import BOT_TOKEN
from db import DatabaseHandler
from analyzer import MoodAnalyzer
from keyboards import Keyboards
import re
from datetime import datetime

# Инициализация бота и базы данных
bot = telebot.TeleBot(BOT_TOKEN)
db = DatabaseHandler()
analyzer = MoodAnalyzer(db)
keyboards = Keyboards()

# Временное хранилище состояний пользователей
user_states = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветственное сообщение"""
    db.connect()
    db.add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    db.disconnect()
    
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот для отслеживания настроения и продуктивности. "
        "Буду помогать тебе находить закономерности между сном, работой и настроением.\n\n"
        "🎯 <b>Что я умею:</b>\n"
        "• Записывать ежедневные показатели\n"
        "• Анализировать твою статистику\n"
        "• Находить скрытые закономерности\n"
        "• Строить графики\n\n"
        "📝 Используй кнопки меню или команды:\n"
        "/add - записать данные за сегодня\n"
        "/stats - посмотреть статистику\n"
        "/history - история записей\n"
        "/settings - настройки\n"
        "/help - справка"
    )
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='HTML',
        reply_markup=keyboards.main_menu()
    )

@bot.message_handler(commands=['help'])
@bot.message_handler(func=lambda message: message.text == '❓ Помощь')
def send_help(message):
    """Справка по использованию"""
    help_text = (
        "📚 <b>Как пользоваться ботом:</b>\n\n"
        "1️⃣ <b>Запись данных:</b>\n"
        "Нажми '➕ Записать день' или /add\n"
        "• Оцени настроение от 1 до 5\n"
        "• Укажи часы работы/учебы\n"
        "• Укажи часы сна\n"
        "• Добавь комментарий (опционально)\n\n"
        "2️⃣ <b>Просмотр статистики:</b>\n"
        "Нажми '📊 Статистика' или /stats\n"
        "• Недельная сводка\n"
        "• Месячная сводка\n"
        "• Инсайты и закономерности\n"
        "• Графики\n\n"
        "3️⃣ <b>История:</b>\n"
        "Нажми '📜 История' или /history\n"
        "Просмотр последних записей\n\n"
        "💡 <b>Совет:</b> Заполняй данные каждый день, "
        "чтобы получить точные инсайты!"
    )
    
    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode='HTML'
    )

@bot.message_handler(commands=['add'])
@bot.message_handler(func=lambda message: message.text == '➕ Записать день')
def start_add_entry(message):
    """Начало процесса добавления записи"""
    user_states[message.from_user.id] = {'state': 'waiting_mood'}
    
    bot.send_message(
        message.chat.id,
        "Оцени свое настроение сегодня от 1 до 5:",
        reply_markup=keyboards.mood_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('mood_'))
def process_mood(call):
    """Обработка выбора настроения"""
    mood = int(call.data.split('_')[1])
    user_id = call.from_user.id
    
    if user_id in user_states:
        user_states[user_id]['mood'] = mood
        user_states[user_id]['state'] = 'waiting_work'
        
        bot.edit_message_text(
            f"✅ Настроение: {mood}/5\n\nСколько часов ты потратил на полезную работу/учебу?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.work_hours_keyboard()
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('work_'))
def process_work_hours(call):
    """Обработка выбора часов работы"""
    user_id = call.from_user.id
    
    if call.data == 'work_other':
        user_states[user_id]['state'] = 'waiting_work_manual'
        bot.edit_message_text(
            "Введите количество часов работы (например: 7.5):",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        work_hours = float(call.data.split('_')[1])
        user_states[user_id]['work_hours'] = work_hours
        user_states[user_id]['state'] = 'waiting_sleep'
        
        bot.edit_message_text(
            f"✅ Работа/учеба: {work_hours} ч\n\nСколько часов ты спал?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.sleep_hours_keyboard()
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('sleep_'))
def process_sleep_hours(call):
    """Обработка выбора часов сна"""
    user_id = call.from_user.id
    
    if call.data == 'sleep_other':
        user_states[user_id]['state'] = 'waiting_sleep_manual'
        bot.edit_message_text(
            "Введите количество часов сна (например: 7.5):",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        sleep_hours = float(call.data.split('_')[1])
        user_states[user_id]['sleep_hours'] = sleep_hours
        user_states[user_id]['state'] = 'waiting_comment'
        
        bot.edit_message_text(
            f"✅ Сон: {sleep_hours} ч\n\nХочешь добавить комментарий?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.skip_comment_keyboard()
        )

@bot.message_handler(func=lambda message: message.from_user.id in user_states)
def process_manual_input(message):
    """Обработка ручного ввода данных"""
    user_id = message.from_user.id
    state = user_states[user_id].get('state')
    
    if state == 'waiting_work_manual':
        try:
            work_hours = float(message.text.replace(',', '.'))
            if 0 <= work_hours <= 24:
                user_states[user_id]['work_hours'] = work_hours
                user_states[user_id]['state'] = 'waiting_sleep'
                bot.send_message(
                    message.chat.id,
                    f"✅ Работа/учеба: {work_hours} ч\n\nСколько часов ты спал?",
                    reply_markup=keyboards.sleep_hours_keyboard()
                )
            else:
                bot.send_message(message.chat.id, "❌ Введите число от 0 до 24")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Пожалуйста, введите число")
            
    elif state == 'waiting_sleep_manual':
        try:
            sleep_hours = float(message.text.replace(',', '.'))
            if 0 <= sleep_hours <= 24:
                user_states[user_id]['sleep_hours'] = sleep_hours
                user_states[user_id]['state'] = 'waiting_comment'
                bot.send_message(
                    message.chat.id,
                    f"✅ Сон: {sleep_hours} ч\n\nХочешь добавить комментарий?",
                    reply_markup=keyboards.skip_comment_keyboard()
                )
            else:
                bot.send_message(message.chat.id, "❌ Введите число от 0 до 24")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Пожалуйста, введите число")
            
    elif state == 'waiting_comment':
        # Сохраняем все данные
        save_entry(user_id, message.text)
        del user_states[user_id]

@bot.callback_query_handler(func=lambda call: call.data == 'skip_comment')
def skip_comment(call):
    """Пропуск комментария"""
    user_id = call.from_user.id
    save_entry(user_id, None)
    del user_states[user_id]
    
    bot.edit_message_text(
        "✅ Данные успешно сохранены!",
        call.message.chat.id,
        call.message.message_id
    )

def save_entry(user_id, comment):
    """Сохранение записи в базу данных"""
    data = user_states.get(user_id, {})
    try:
        db.connect()
        db.add_entry(
            user_id,
            data['mood'],
            data.get('work_hours', 0),
            data.get('sleep_hours', 0),
            comment
        )
        db.disconnect()
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

@bot.message_handler(commands=['stats'])
@bot.message_handler(func=lambda message: message.text == '📊 Статистика')
def show_stats_menu(message):
    """Показ меню статистики"""
    bot.send_message(
        message.chat.id,
        "📊 <b>Что хочешь узнать?</b>",
        parse_mode='HTML',
        reply_markup=keyboards.stats_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == 'stats_week')
def show_week_stats(call):
    """Показ недельной статистики"""
    try:
        db.connect()
        summary = analyzer.get_weekly_summary(call.from_user.id)
        db.disconnect()
        
        bot.edit_message_text(
            summary,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML',
            reply_markup=keyboards.stats_menu()
        )
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Ошибка получения статистики")

@bot.callback_query_handler(func=lambda call: call.data == 'stats_month')
def show_month_stats(call):
    """Показ месячной статистики"""
    try:
        db.connect()
        stats = db.get_month_stats(call.from_user.id)
        db.disconnect()
        
        if stats and stats['avg_mood']:
            summary = (
                f"📊 <b>Статистика за месяц</b>\n\n"
                f"📝 Всего записей: {stats['total_days']}\n"
                f"😊 Среднее настроение: {stats['avg_mood']:.1f}/5\n"
                f"💼 Среднее время работы: {stats['avg_work']:.1f} ч/день\n"
                f"😴 Среднее время сна: {stats['avg_sleep']:.1f} ч/день\n"
                f"📈 Всего отработано: {stats['total_work']:.1f} ч\n"
                f"🎯 Лучшее настроение: {stats['best_mood']}/5\n"
                f"📉 Худшее настроение: {stats['worst_mood']}/5"
            )
        else:
            summary = "📊 Нет данных за последний месяц"
            
        bot.edit_message_text(
            summary,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML',
            reply_markup=keyboards.stats_menu()
        )
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Ошибка получения статистики")

@bot.callback_query_handler(func=lambda call: call.data == 'stats_insights')
def show_insights(call):
    """Показ инсайтов"""
    try:
        db.connect()
        insights = analyzer.generate_insights(call.from_user.id)
        db.disconnect()
        
        insights_text = "🔍 <b>Мои инсайты</b>\n\n" + "\n\n".join(insights)
        
        bot.edit_message_text(
            insights_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML',
            reply_markup=keyboards.stats_menu()
        )
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Ошибка генерации инсайтов")

@bot.callback_query_handler(func=lambda call: call.data == 'stats_chart')
def show_chart(call):
    """Отправка графика"""
    try:
        bot.answer_callback_query(call.id, "📊 Генерирую график...")
        
        db.connect()
        chart = analyzer.create_mood_chart(call.from_user.id)
        db.disconnect()
        
        bot.send_photo(
            call.message.chat.id,
            chart,
            caption="📈 График за последние 2 недели"
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ Ошибка создания графика")

@bot.message_handler(commands=['history'])
@bot.message_handler(func=lambda message: message.text == '📜 История')
def show_history(message):
    """Показ истории записей"""
    try:
        db.connect()
        entries = db.get_last_entries(message.from_user.id, 10)
        db.disconnect()
        
        if not entries:
            bot.send_message(message.chat.id, "📜 История пуста. Начните записывать данные!")
            return
            
        history_text = "📜 <b>Последние записи:</b>\n\n"
        
        for entry in entries:
            date_str = entry['entry_date'].strftime('%d.%m.%Y')
            mood_emoji = ['', '😞', '😐', '🙂', '😊', '🤩'][entry['mood_score']]
            history_text += (
                f"📅 {date_str}\n"
                f"Настроение: {mood_emoji} ({entry['mood_score']}/5)\n"
                f"Работа: {entry['work_hours']} ч | Сон: {entry['sleep_hours']} ч\n"
            )
            if entry['comment']:
                history_text += f"💬 {entry['comment']}\n"
            history_text += "➖➖➖➖➖➖➖\n"
            
        bot.send_message(
            message.chat.id,
            history_text,
            parse_mode='HTML'
        )
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка получения истории")

@bot.message_handler(commands=['settings'])
@bot.message_handler(func=lambda message: message.text == '⚙️ Настройки')
def show_settings(message):
    """Показ настроек"""
    settings_text = (
        "⚙️ <b>Настройки</b>\n\n"
        "🔔 Уведомления: включены\n"
        "⏰ Время напоминания: 21:00\n\n"
        "Используйте команды:\n"
        "/clear - очистить все данные"
    )
    
    bot.send_message(
        message.chat.id,
        settings_text,
        parse_mode='HTML'
    )

@bot.message_handler(commands=['clear'])
def clear_data(message):
    """Запрос на очистку данных"""
    bot.send_message(
        message.chat.id,
        "⚠️ <b>Вы уверены, что хотите удалить все данные?</b>\n"
        "Это действие нельзя отменить!",
        parse_mode='HTML',
        reply_markup=keyboards.confirm_clear_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == 'clear_confirm')
def confirm_clear(call):
    """Подтверждение очистки данных"""
    try:
        db.connect()
        db.clear_user_data(call.from_user.id)
        db.disconnect()
        
        bot.edit_message_text(
            "✅ Все данные успешно удалены",
            call.message.chat.id,
            call.message.message_id
        )
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Ошибка очистки данных")

@bot.callback_query_handler(func=lambda call: call.data == 'clear_cancel')
def cancel_clear(call):
    """Отмена очистки данных"""
    bot.edit_message_text(
        "❌ Удаление данных отменено",
        call.message.chat.id,
        call.message.message_id
    )

# Запуск бота
if __name__ == '__main__':
    print("🤖 Бот запущен...")
    bot.infinity_polling()