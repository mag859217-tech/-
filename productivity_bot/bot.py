import asyncio
from datetime import date
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import BOT_TOKEN
from database import db

# Состояния для опроса
class DailySurvey(StatesGroup):
    mood = State()
    productive = State()
    sleep = State()

# Клавиатура
def get_main_keyboard():
    buttons = [
        [KeyboardButton(text="📊 Моя статистика")],
        [KeyboardButton(text="🔍 Аналитика"), KeyboardButton(text="📝 Заполнить сегодня")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Инициализация
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🌟 Привет! Я бот для отслеживания продуктивности!\n\n"
        "Команды:\n"
        "/track - начать опрос\n"
        "/stats - моя статистика\n"
        "/insights - анализ данных\n"
        "/help - помощь",
        reply_markup=get_main_keyboard()
    )

# Команда /track
@dp.message(Command("track"))
@dp.message(F.text == "📝 Заполнить сегодня")
async def start_survey(message: types.Message, state: FSMContext):
    await state.set_state(DailySurvey.mood)
    await message.answer(
        "🎭 Какое у тебя настроение?\n"
        "Отправь число от 1 до 5:\n"
        "1 = очень плохое | 5 = отличное",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(DailySurvey.mood)
async def process_mood(message: types.Message, state: FSMContext):
    try:
        mood = int(message.text)
        if 1 <= mood <= 5:
            await state.update_data(mood=mood)
            await state.set_state(DailySurvey.productive)
            await message.answer("💻 Сколько часов ты продуктивно работал/учился? (0-24)")
        else:
            await message.answer("Введи число от 1 до 5")
    except ValueError:
        await message.answer("Введи целое число от 1 до 5")

@dp.message(DailySurvey.productive)
async def process_productive(message: types.Message, state: FSMContext):
    try:
        hours = float(message.text)
        if 0 <= hours <= 24:
            await state.update_data(productive=hours)
            await state.set_state(DailySurvey.sleep)
            await message.answer("😴 Сколько часов ты спал? (0-24)")
        else:
            await message.answer("Введи число от 0 до 24")
    except ValueError:
        await message.answer("Введи число (например: 7.5)")

@dp.message(DailySurvey.sleep)
async def process_sleep(message: types.Message, state: FSMContext):
    try:
        sleep = float(message.text)
        if 0 <= sleep <= 24:
            data = await state.get_data()
            
            await db.save_daily_log(
                user_id=message.from_user.id,
                user_name=message.from_user.full_name,
                log_date=date.today(),
                mood=data['mood'],
                productive_hours=data['productive'],
                sleep_hours=sleep
            )
            
            await state.clear()
            await message.answer(
                f"✅ Данные сохранены!\n\n"
                f"Настроение: {data['mood']}/5\n"
                f"Продуктивность: {data['productive']}ч\n"
                f"Сон: {sleep}ч\n\n"
                f"Спасибо! 🎉",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer("Введи число от 0 до 24")
    except ValueError:
        await message.answer("Введи число (например: 7.5)")

# Команда /stats
@dp.message(Command("stats"))
@dp.message(F.text == "📊 Моя статистика")
async def show_stats(message: types.Message):
    averages, best_days = await db.get_stats(message.from_user.id)
    
    if averages['total_days'] == 0:
        await message.answer("📭 Нет данных. Используй /track")
        return
    
    response = f"📊 Статистика за 30 дней:\n\n"
    response += f"😊 Настроение: {averages['avg_mood']:.1f}/5\n"
    response += f"💪 Продуктивность: {averages['avg_productivity']:.1f}ч\n"
    response += f"😴 Сон: {averages['avg_sleep']:.1f}ч\n"
    response += f"📆 Дней: {averages['total_days']}\n"
    
    await message.answer(response)

# Команда /insights
@dp.message(Command("insights"))
@dp.message(F.text == "🔍 Аналитика")
async def show_insights(message: types.Message):
    averages, _ = await db.get_stats(message.from_user.id)
    
    if averages['total_days'] < 3:
        await message.answer("📭 Нужно больше данных (минимум 3 дня)")
        return
    
    correlation = await db.get_correlation(message.from_user.id)
    
    response = "🔍 Аналитика:\n\n"
    
    if correlation > 0.5:
        response += f"📈 Сильная связь сна и продуктивности ({correlation:.2f})\n"
        response += "→ Чем больше спишь, тем продуктивнее!\n"
    elif correlation > 0.2:
        response += f"📈 Слабая связь сна и продуктивности ({correlation:.2f})\n"
    elif correlation < -0.3:
        response += f"⚠️ Отрицательная связь ({correlation:.2f})\n"
    else:
        response += "❓ Связи между сном и продуктивностью не найдено\n"
    
    await message.answer(response)

# Команда /help
@dp.message(Command("help"))
@dp.message(F.text == "❓ Помощь")
async def show_help(message: types.Message):
    help_text = """
📖 Команды:
/track - заполнить данные за сегодня
/stats - посмотреть статистику
/insights - анализ данных
/help - эта справка

📝 Что отслеживаем:
• Настроение (1-5)
• Часы продуктивной работы
• Часы сна

💡 Чем больше данных, тем точнее аналитика!
    """
    await message.answer(help_text)

# Запуск
async def main():
    await db.connect()
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())