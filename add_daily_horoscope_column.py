"""
Скрипт для добавления колонки daily_horoscope_enabled в таблицу astrology_profiles
"""
import asyncio
from sqlalchemy import text
from core.database.connection import DatabaseManager

async def migrate():
    db = DatabaseManager()
    await db.init()
    
    async with db._engine.begin() as conn:
        # Проверяем, есть ли уже колонка
        result = await conn.execute(text("PRAGMA table_info(astrology_profiles)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'daily_horoscope_enabled' in columns:
            print("✅ Колонка daily_horoscope_enabled уже существует")
            return
        
        # Добавляем колонку
        await conn.execute(text("""
            ALTER TABLE astrology_profiles ADD COLUMN daily_horoscope_enabled BOOLEAN DEFAULT 0
        """))
        
        print("✅ Колонка daily_horoscope_enabled добавлена!")

if __name__ == "__main__":
    asyncio.run(migrate())
