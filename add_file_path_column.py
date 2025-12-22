"""
Скрипт для добавления колонки file_path в таблицу astrology_readings
"""
import asyncio
from sqlalchemy import text
from core.database.connection import DatabaseManager

async def migrate():
    db = DatabaseManager()
    await db.init()
    
    async with db._engine.begin() as conn:
        # Проверяем, есть ли уже колонка
        result = await conn.execute(text("PRAGMA table_info(astrology_readings)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'file_path' in columns:
            print("✅ Колонка file_path уже существует")
            return
        
        # Добавляем колонку
        await conn.execute(text("""
            ALTER TABLE astrology_readings ADD COLUMN file_path VARCHAR(500)
        """))
        
        print("✅ Колонка file_path добавлена!")

if __name__ == "__main__":
    asyncio.run(migrate())
