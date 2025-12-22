"""
Initialize CryptoBot payment provider in database
"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\Andrey\Desktop\Program\FuBot — Базовая версия")

from core.database import get_db, db_manager
from core.database.models import PaymentProvider
from sqlalchemy import select


async def init_cryptobot():
    """Add CryptoBot provider to database"""
    await db_manager.init()
    await db_manager.create_tables()
    
    async with get_db() as session:
        # Check if already exists
        result = await session.execute(
            select(PaymentProvider).where(PaymentProvider.id == "cryptobot")
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ CryptoBot provider already exists")
            print(f"   Active: {existing.is_active}")
            print(f"   Currencies: {existing.currencies}")
            return
        
        # Create provider
        provider = PaymentProvider(
            id="cryptobot",
            name="CryptoBot",
            icon="🤖",
            is_active=True,
            currencies=["TON", "USDT", "BTC", "ETH", "LTC", "BNB", "TRX", "USDC"],
            config={},  # Config is loaded from environment
            fee_percent=0,  # No additional fee
            min_amount=0.1,
            max_amount=10000,
            sort_order=1,
            description="Оплата криптовалютой через @CryptoBot"
        )
        session.add(provider)
        
        print("✅ CryptoBot provider created!")
        print(f"   ID: {provider.id}")
        print(f"   Currencies: {provider.currencies}")


async def test_connection():
    """Test CryptoBot API connection"""
    from core.config import config
    from core.payments.providers.cryptobot import CryptoBotProvider
    
    if not config.CRYPTOBOT_API_TOKEN:
        print("❌ CRYPTOBOT_API_TOKEN not set in environment")
        return False
    
    provider = CryptoBotProvider({
        "api_token": config.CRYPTOBOT_API_TOKEN,
        "testnet": config.CRYPTOBOT_TESTNET
    })
    
    try:
        me = await provider.get_me()
        print(f"✅ CryptoBot connected!")
        print(f"   App ID: {me.get('app_id')}")
        print(f"   Name: {me.get('name')}")
        
        # Get balance
        balance = await provider.get_balance()
        print(f"   Balance: {balance}")
        
        return True
    except Exception as e:
        print(f"❌ CryptoBot connection failed: {e}")
        return False


if __name__ == "__main__":
    print("=== CryptoBot Initialization ===\n")
    
    # Init provider in DB
    asyncio.run(init_cryptobot())
    
    print("\n=== Testing Connection ===\n")
    
    # Test connection
    asyncio.run(test_connection())
