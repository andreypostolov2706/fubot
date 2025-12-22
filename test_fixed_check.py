"""
Test fixed payment check
"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\Andrey\Desktop\Program\FuBot — Базовая версия")

from core.database import get_db, db_manager
from core.database.models import Payment
from core.payments.service import payment_service
from core.payments.providers.manager import provider_manager
from sqlalchemy import select

async def test_fixed_check():
    """Test fixed payment check"""
    await db_manager.init()
    
    # Get a pending payment
    async with get_db() as session:
        result = await session.execute(
            select(Payment)
            .where(Payment.status == "pending")
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        payment = result.scalar_one_or_none()
    
    if not payment:
        print("No pending payments")
        return
    
    print(f"Checking payment: {payment.uuid}")
    
    # Check with provider
    provider = provider_manager.get_provider(payment.provider)
    if not provider:
        print("Provider not found")
        return
    
    try:
        status = await provider.check_payment(payment.provider_payment_id)
        print(f"Provider status: {status}")
        
        if status.name == "COMPLETED":
            print("Payment is completed, confirming...")
            try:
                success = await payment_service.confirm_payment(
                    payment_uuid=payment.uuid,
                    provider_payment_id=payment.provider_payment_id
                )
                print(f"Confirmation success: {success}")
            except Exception as e:
                print(f"Confirmation error: {e}")
                # Try to update status only
                async with get_db() as session:
                    result = await session.execute(
                        select(Payment).where(Payment.uuid == payment.uuid)
                    )
                    p = result.scalar_one()
                    p.status = "completed"
                    await session.commit()
                    print("Status updated to completed")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_fixed_check())
