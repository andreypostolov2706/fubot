"""
Test remaining payments
"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\Andrey\Desktop\Program\FuBot — Базовая версия")

from core.database import get_db, db_manager
from core.database.models import Payment
from core.payments.providers.manager import provider_manager
from sqlalchemy import select

async def test_remaining():
    """Test remaining pending payments"""
    await db_manager.init()
    
    async with get_db() as session:
        result = await session.execute(
            select(Payment)
            .where(Payment.status == "pending")
            .order_by(Payment.created_at.desc())
        )
        payments = result.scalars().all()
    
    print(f"Found {len(payments)} pending payments")
    
    for payment in payments:
        print(f"\n=== Payment {payment.uuid} ===")
        provider = provider_manager.get_provider(payment.provider)
        if provider:
            try:
                status = await provider.check_payment(payment.provider_payment_id)
                print(f"Status: {status}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_remaining())
