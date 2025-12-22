"""
Debug payment check issue
"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\Andrey\Desktop\Program\FuBot — Базовая версия")

from core.database import get_db, db_manager
from core.database.models import Payment, Wallet
from core.payments.providers.manager import provider_manager
from sqlalchemy import select

async def debug_payment_issue():
    """Debug payment check issue"""
    await db_manager.init()
    
    # Get user balance
    async with get_db() as session:
        result = await session.execute(
            select(Wallet).where(Wallet.user_id == 5, Wallet.wallet_type == "main")
        )
        wallet = result.scalar_one()
        print(f"User 5 balance: {wallet.balance} GTON")
        
        # Get all pending payments for user 5
        result = await session.execute(
            select(Payment)
            .where(Payment.user_id == 5, Payment.status == "pending")
            .order_by(Payment.created_at.desc())
        )
        payments = result.scalars().all()
        
        print(f"\nFound {len(payments)} pending payments for user 5")
        
        for payment in payments:
            print(f"\n=== Payment {payment.uuid} ===")
            print(f"Amount: {payment.amount_gton} GTON")
            print(f"Provider ID: {payment.provider_payment_id}")
            print(f"Created: {payment.created_at}")
            
            # Check via CryptoBot
            provider = provider_manager.get_provider(payment.provider)
            if provider:
                try:
                    status = await provider.check_payment(payment.provider_payment_id)
                    print(f"CryptoBot status: {status}")
                    
                    if status.name == "COMPLETED":
                        print("✅ This payment should be confirmed!")
                        
                except Exception as e:
                    print(f"Error checking: {e}")

if __name__ == "__main__":
    asyncio.run(debug_payment_issue())
