import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://example.com")
# Укажи свой Telegram ID сюда или вынеси в .env файл
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0")) 

DB_NAME = "lifecoach.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def register_user_in_db(telegram_id: int, username: str, full_name: str):
    """Регистрирует пользователя в БД или обновляет его данные"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Проверяем, является ли пользователь администратором
    is_admin = 1 if telegram_id == ADMIN_TELEGRAM_ID else 0

    cursor.execute("""
        INSERT INTO users (telegram_id, username, full_name, is_admin)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
        username = excluded.username,
        full_name = excluded.full_name
    """, (telegram_id, username, full_name, is_admin))
    
    conn.commit()
    conn.close()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    # Регистрируем пользователя при старте бота
    register_user_in_db(user.id, user.username, user.full_name)
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Открыть Life Coach",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ]
        ]
    )
    
    # Проверяем, админ ли это, чтобы выдать приветствие с правами
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE telegram_id = ?", (user.id,))
    res = cursor.fetchone()
    conn.close()
    
    is_admin = res[0] if res else 0
    admin_text = "\n🛡 **Режим администратора активен**" if is_admin else ""

    await message.answer(
        f"Привет, {user.first_name}! Нажми на кнопку ниже, чтобы открыть Mini App:{admin_text}",
        reply_markup=kb,
        parse_mode="Markdown"
    )

async def main():
    print("Бот запущен и подключен к базе данных!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())