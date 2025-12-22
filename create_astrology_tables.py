"""
Скрипт для создания таблиц астрологии в БД
"""
import asyncio
from sqlalchemy import text
from core.database.connection import DatabaseManager

async def create_tables():
    db = DatabaseManager()
    await db.init()
    async with db._engine.begin() as conn:
        # Таблица профилей астрологии
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS astrology_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                birth_date DATE NOT NULL,
                birth_time TIME NOT NULL,
                birth_time_unknown BOOLEAN DEFAULT FALSE,
                birth_city VARCHAR(200),
                birth_lat FLOAT,
                birth_lng FLOAT,
                birth_tz VARCHAR(50),
                sun_sign VARCHAR(20),
                moon_sign VARCHAR(20),
                ascendant_sign VARCHAR(20),
                chart_data JSON,
                svg_path VARCHAR(500),
                has_referral_bonus BOOLEAN DEFAULT FALSE,
                free_horoscope_used BOOLEAN DEFAULT FALSE,
                max_saved_charts INTEGER DEFAULT 10,
                subscription_type VARCHAR(20),
                subscription_until DATETIME,
                subscription_plan VARCHAR(50),
                subscription_send_time TIME,
                subscription_tz VARCHAR(50),
                subscription_auto_renew BOOLEAN DEFAULT TRUE,
                subscription_notified BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        
        # Таблица сохранённых карт
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS astrology_saved_charts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                profile_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                relation VARCHAR(50),
                birth_date DATE NOT NULL,
                birth_time TIME NOT NULL,
                birth_time_unknown BOOLEAN DEFAULT FALSE,
                birth_city VARCHAR(200),
                birth_lat FLOAT,
                birth_lng FLOAT,
                birth_tz VARCHAR(50),
                sun_sign VARCHAR(20),
                moon_sign VARCHAR(20),
                ascendant_sign VARCHAR(20),
                chart_data JSON,
                svg_path VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (profile_id) REFERENCES astrology_profiles(id) ON DELETE CASCADE
            )
        """))
        
        # Таблица чтений/интерпретаций
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS astrology_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                profile_id INTEGER,
                chart_id INTEGER,
                second_chart_id INTEGER,
                reading_type VARCHAR(50) NOT NULL,
                reading_subtype VARCHAR(50),
                interpretation TEXT,
                is_free BOOLEAN DEFAULT FALSE,
                gton_cost DECIMAL(10, 2) DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (profile_id) REFERENCES astrology_profiles(id) ON DELETE SET NULL,
                FOREIGN KEY (chart_id) REFERENCES saved_charts(id) ON DELETE SET NULL
            )
        """))
        
        # Таблица логов ежедневных гороскопов
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS daily_horoscope_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                profile_id INTEGER NOT NULL,
                sent_date DATE NOT NULL,
                horoscope_text TEXT,
                tokens_used INTEGER DEFAULT 0,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (profile_id) REFERENCES astrology_profiles(id) ON DELETE CASCADE
            )
        """))
        
        print("✅ Таблицы астрологии созданы успешно!")

if __name__ == "__main__":
    asyncio.run(create_tables())
