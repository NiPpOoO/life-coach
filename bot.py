import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://example.com")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "8873481719"))

DB_NAME = "lifecoach.db"

# Инициализация бота и FastAPI
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# Разрешаем CORS, чтобы сайт с GitHub мог стучаться к нам на ПК
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def register_user_in_db(telegram_id: int, username: str, full_name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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

# --- Telegram Бот хендлеры ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
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

# --- FastAPI Эндпоинты (API для сайта) ---

class SyncDataModel(BaseModel):
    telegram_id: int
    tasks: list = []
    habits: list = []
    finances: list = []
    moodLog: dict = {}

@app.get("/api/get_data/{telegram_id}")
async def get_user_data(telegram_id: int):
    """Получение данных пользователя из базы на ПК"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Проверяем юзера и админку
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Загружаем задачи
    cursor.execute("SELECT * FROM tasks WHERE telegram_id = ?", (telegram_id,))
    tasks = [dict(row) for row in cursor.fetchall()]

    # Загружаем финансы
    cursor.execute("SELECT * FROM finances WHERE telegram_id = ?", (telegram_id,))
    finances = [dict(row) for row in cursor.fetchall()]

    conn.close()
    
    return {
        "user": {
            "name": user["full_name"],
            "xp": user["xp"],
            "level": user["level"],
            "is_admin": bool(user["is_admin"])
        },
        "tasks": tasks,
        "finances": finances
    }

@app.post("/api/save_data")
async def save_user_data(data: SyncDataModel):
    """Сохранение/синхронизация данных из Mini App в базу ПК"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Здесь в будущем зафиксируем сохранение приходящих задач/финансов
    conn.commit()
    conn.close()
    return {"status": "success"}

# --- Запуск одновременно бота и сервера ---
async def main():
    print("Бот и локальный API-сервер запускаются...")
    # Запускаем FastAPI на порту 8000 в фоновом режиме
    import uvicorn
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    await asyncio.gather(
        dp.start_polling(bot),
        server.serve()
    )

if __name__ == "__main__":
    asyncio.run(main())