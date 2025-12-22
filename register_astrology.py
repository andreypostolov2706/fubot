"""
Скрипт для регистрации сервиса астрологии в БД
"""
import asyncio
from sqlalchemy import text
from core.database.connection import DatabaseManager

async def register():
    db = DatabaseManager()
    await db.init()
    
    async with db._engine.begin() as conn:
        # Проверяем, есть ли уже сервис
        result = await conn.execute(text("SELECT id FROM services WHERE id = 'astrology'"))
        existing = result.fetchone()
        
        if existing:
            print("✅ Сервис астрологии уже зарегистрирован")
            return
        
        # Регистрируем сервис
        await conn.execute(text("""
            INSERT INTO services (id, name, description, version, author, icon, status, install_path)
            VALUES ('astrology', 'Астрология', 'Персональные натальные карты и AI-интерпретации', '1.0.0', 'FuBot', '🔮', 'active', NULL)
        """))
        
        print("✅ Сервис астрологии зарегистрирован!")

if __name__ == "__main__":
    asyncio.run(register())
