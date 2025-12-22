"""
Скрипт для сброса статуса сервиса астрологии
"""
import asyncio
from sqlalchemy import text
from core.database.connection import DatabaseManager

async def fix():
    db = DatabaseManager()
    await db.init()
    
    async with db._engine.begin() as conn:
        # Сбрасываем статус на active
        await conn.execute(text("""
            UPDATE services SET status = 'active', last_error = NULL, error_count = 0
            WHERE id = 'astrology'
        """))
        
        # Проверяем результат
        result = await conn.execute(text("SELECT id, status, last_error FROM services WHERE id = 'astrology'"))
        row = result.fetchone()
        if row:
            print(f"✅ Сервис: {row[0]}, статус: {row[1]}, ошибка: {row[2]}")
        else:
            print("❌ Сервис не найден")

if __name__ == "__main__":
    asyncio.run(fix())
