"""
Test payment check directly
"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\Andrey\Desktop\Program\FuBot — Базовая версия")

from core.database import get_db, db_manager
from core.database.models import Payment
from sqlalchemy import select

async def check_recent_payments():
    """Check recent payments"""
    await db_manager.init()
    
    async with get_db() as session:
        result = await session.execute(
            select(Payment)
            .order_by(Payment.created_at.desc())
            .limit(5)
        )
        payments = result.scalars().all()
        
        print("=== Recent Payments ===")
        for payment in payments:
            print(f"UUID: {payment.uuid}")
            print(f"User ID: {payment.user_id}")
            print(f"Status: {payment.status}")
            print(f"Amount: {payment.amount_gton} GTON")
            print(f"Provider: {payment.provider}")
            print(f"Provider Payment ID: {payment.provider_payment_id}")
            print(f"Created: {payment.created_at}")
            print("---")

if __name__ == "__main__":
    asyncio.run(check_recent_payments())
