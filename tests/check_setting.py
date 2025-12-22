import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import db_manager, get_db
from core.database.models import Setting
from sqlalchemy import select

async def check():
    await db_manager.init()
    async with get_db() as s:
        result = await s.execute(select(Setting).where(Setting.key == "payments.gton_ton_rate"))
        setting = result.scalar_one_or_none()
        if setting:
            print(f"Key: {setting.key}")
            print(f"Value: {repr(setting.value)}")
            print(f"Type: {type(setting.value)}")
        else:
            print("Setting not found")

asyncio.run(check())
