"""
Test payment confirmation
"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\Andrey\Desktop\Program\FuBot — Базовая версия")

from core.database import get_db, db_manager
from core.database.models import Payment
from core.payments.service import payment_service
from sqlalchemy import select

async def test_confirm_payment():
    """Test confirming a payment"""
    await db_manager.init()
    
    # Get first pending payment
    async with get_db() as session:
        result = await session.execute(
            select(Payment)
            .where(Payment.status == "pending")
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        payment = result.scalar_one_or_none()
    
    if not payment:
        print("No pending payments found")
        return
    
    print(f"Found payment: {payment.uuid}")
    print(f"Status: {payment.status}")
    print(f"Amount: {payment.amount_gton} GTON")
    print(f"Provider: {payment.provider}")
    print(f"Provider Payment ID: {payment.provider_payment_id}")
    
    # Try to confirm
    try:
        success = await payment_service.confirm_payment(
            payment_uuid=payment.uuid,
            provider_payment_id=payment.provider_payment_id
        )
        print(f"Confirmation result: {success}")
        
        # Check updated status
        async with get_db() as session:
            result = await session.execute(
                select(Payment).where(Payment.uuid == payment.uuid)
            )
            updated = result.scalar_one()
            print(f"Updated status: {updated.status}")
            
    except Exception as e:
        print(f"Error confirming payment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_confirm_payment())
