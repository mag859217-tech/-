from telebot import types

class Keyboards:
    @staticmethod
    def main_menu():
        """Главное меню с основными действиями"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [
            '➕ Записать день',
            '📊 Статистика',
            '📜 История',
            '⚙️ Настройки',
            '❓ Помощь'
        ]
        keyboard.add(*[types.KeyboardButton(text) for text in buttons])
        return keyboard
        
    @staticmethod
    def mood_keyboard():
        """Клавиатура для выбора настроения"""
        keyboard = types.InlineKeyboardMarkup(row_width=5)
        buttons = [
            types.InlineKeyboardButton("1 😞", callback_data="mood_1"),
            types.InlineKeyboardButton("2 😐", callback_data="mood_2"),
            types.InlineKeyboardButton("3 🙂", callback_data="mood_3"),
            types.InlineKeyboardButton("4 😊", callback_data="mood_4"),
            types.InlineKeyboardButton("5 🤩", callback_data="mood_5")
        ]
        keyboard.add(*buttons)
        return keyboard
        
    @staticmethod
    def work_hours_keyboard():
        """Клавиатура для выбора часов работы"""
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        buttons = [
            types.InlineKeyboardButton("0.5 ч", callback_data="work_0.5"),
            types.InlineKeyboardButton("1 ч", callback_data="work_1"),
            types.InlineKeyboardButton("2 ч", callback_data="work_2"),
            types.InlineKeyboardButton("4 ч", callback_data="work_4"),
            types.InlineKeyboardButton("6 ч", callback_data="work_6"),
            types.InlineKeyboardButton("8 ч", callback_data="work_8"),
            types.InlineKeyboardButton("Другое...", callback_data="work_other")
        ]
        keyboard.add(*buttons)
        return keyboard
        
    @staticmethod
    def sleep_hours_keyboard():
        """Клавиатура для выбора часов сна"""
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        buttons = [
            types.InlineKeyboardButton("5 ч", callback_data="sleep_5"),
            types.InlineKeyboardButton("6 ч", callback_data="sleep_6"),
            types.InlineKeyboardButton("7 ч", callback_data="sleep_7"),
            types.InlineKeyboardButton("8 ч", callback_data="sleep_8"),
            types.InlineKeyboardButton("9 ч", callback_data="sleep_9"),
            types.InlineKeyboardButton("10 ч", callback_data="sleep_10"),
            types.InlineKeyboardButton("Другое...", callback_data="sleep_other")
        ]
        keyboard.add(*buttons)
        return keyboard
        
    @staticmethod
    def stats_menu():
        """Меню статистики"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("📅 За неделю", callback_data="stats_week"),
            types.InlineKeyboardButton("🗓 За месяц", callback_data="stats_month"),
            types.InlineKeyboardButton("🔍 Мои инсайты", callback_data="stats_insights"),
            types.InlineKeyboardButton("📉 График", callback_data="stats_chart")
        ]
        keyboard.add(*buttons)
        return keyboard
        
    @staticmethod
    def skip_comment_keyboard():
        """Клавиатура для пропуска комментария"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Пропустить ➡️", callback_data="skip_comment"))
        return keyboard
        
    @staticmethod
    def confirm_clear_keyboard():
        """Клавиатура подтверждения очистки данных"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("✅ Да, удалить", callback_data="clear_confirm"),
            types.InlineKeyboardButton("❌ Отмена", callback_data="clear_cancel")
        ]
        keyboard.add(*buttons)
        return keyboard