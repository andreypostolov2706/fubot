"""
Force confirm all paid payments
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

async def force_confirm_payments():
    """Force confirm all paid payments"""
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
        print(f"\n=== Processing {payment.uuid} ===")
        
        # Check via provider
        provider = provider_manager.get_provider(payment.provider)
        if provider:
            try:
                status = await provider.check_payment(payment.provider_payment_id)
                print(f"Provider status: {status}")
                
                if status.name == "COMPLETED":
                    print("Confirming payment...")
                    try:
                        success = await payment_service.confirm_payment(
                            payment_uuid=payment.uuid,
                            provider_payment_id=payment.provider_payment_id
                        )
                        print(f"Confirmation result: {success}")
                        
                        if success:
                            # Check updated status
                            async with get_db() as session:
                                result = await session.execute(
                                    select(Payment).where(Payment.uuid == payment.uuid)
                                )
                                updated = result.scalar_one()
                                print(f"Updated status: {updated.status}")
                        
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
                
                elif status.name == "EXPIRED":
                    print("Marking as expired...")
                    async with get_db() as session:
                        result = await session.execute(
                            select(Payment).where(Payment.uuid == payment.uuid)
                        )
                        p = result.scalar_one()
                        p.status = "expired"
                        await session.commit()
                        print("Status updated to expired")
                        
            except Exception as e:
                print(f"Error checking payment: {e}")

if __name__ == "__main__":
    asyncio.run(force_confirm_payments())
