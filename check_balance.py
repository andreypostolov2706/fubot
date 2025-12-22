import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')

from core.database import get_db, db_manager
from core.database.models import Wallet
from sqlalchemy import select

async def check():
    await db_manager.init()
    async with get_db() as session:
        result = await session.execute(select(Wallet).where(Wallet.user_id == 5))
        wallet = result.scalar_one_or_none()
        if wallet:
            print(f"User 5 balance: {wallet.balance} GTON")
        else:
            print("Wallet not found")

asyncio.run(check())
