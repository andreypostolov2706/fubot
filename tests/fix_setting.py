import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import db_manager, get_db
from core.database.models import Setting
from sqlalchemy import select

async def fix():
    await db_manager.init()
    async with get_db() as s:
        result = await s.execute(select(Setting).where(Setting.key == "payments.gton_ton_rate"))
        setting = result.scalar_one_or_none()
        if setting:
            # Fix comma to dot
            old_value = setting.value
            new_value = old_value.replace(",", ".")
            setting.value = new_value
            print(f"Fixed: {old_value} -> {new_value}")
        else:
            print("Setting not found")

asyncio.run(fix())
