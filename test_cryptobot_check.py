"""
Test CryptoBot payment status check
"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\Andrey\Desktop\Program\FuBot — Базовая версия")

from core.config import config
from core.payments.providers.cryptobot import CryptoBotProvider

async def test_payment_check():
    """Test checking payment status"""
    
    provider = CryptoBotProvider({
        "api_token": config.CRYPTOBOT_API_TOKEN,
        "testnet": config.CRYPTOBOT_TESTNET
    })
    
    # Check recent payment IDs
    payment_ids = [794307, 794275, 794270, 794265]
    
    for payment_id in payment_ids:
        try:
            print(f"=== Checking payment {payment_id} ===")
            status = await provider.check_payment(payment_id)
            print(f"Status: {status}")
            
            # Also get invoice info
            invoice = await provider.get_invoice(payment_id)
            print(f"Invoice: {invoice}")
            
        except Exception as e:
            print(f"Error: {e}")
        print("---")

if __name__ == "__main__":
    asyncio.run(test_payment_check())
