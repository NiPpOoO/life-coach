import sqlite3

DB_NAME = "lifecoach.db"

# Твой Telegram ID как главного администратора (замени на реальный ID)
ADMIN_TELEGRAM_ID = 123456789  

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблица задач и привычек
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            title TEXT,
            date TEXT,
            done BOOLEAN DEFAULT 0,
            is_habit BOOLEAN DEFAULT 0,
            streak INTEGER DEFAULT 0,
            FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
        )
    """)

    # Таблица финансов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            title TEXT,
            amount REAL,
            date TEXT,
            FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
        )
    """)

    conn.commit()
    conn.close()
    print("База данных успешно инициализирована!")

# Функция для регистрации пользователя или проверки роли
def register_user(telegram_id, username, full_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Проверяем, админ ли это
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

if __name__ == "__main__":
    init_db()