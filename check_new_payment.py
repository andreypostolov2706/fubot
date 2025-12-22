"""
Check specific payment
"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\Andrey\Desktop\Program\FuBot — Базовая версия")

from core.payments.providers.manager import provider_manager

async def check_specific_payment():
    """Check specific payment status"""
    
    provider = provider_manager.get_provider("cryptobot")
    if not provider:
        print("CryptoBot provider not found")
        return
    
    # Check the newest payment
    payment_id = 794308
    
    try:
        status = await provider.check_payment(payment_id)
        print(f"Payment {payment_id} status: {status}")
        
        # Get invoice details
        invoice = await provider.get_invoice(payment_id)
        print(f"Invoice details: {invoice}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_specific_payment())
