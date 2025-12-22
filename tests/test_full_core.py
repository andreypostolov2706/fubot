"""
Full Core Test — Комплексный тест всего функционала ядра FuBot

Запуск: python tests/test_full_core.py
"""
import asyncio
import os
import sys
from decimal import Decimal
from datetime import datetime, timedelta, date
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set test database BEFORE imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# Test results
PASSED = []
FAILED = []


async def setup_database():
    """Setup test database"""
    from core.database import db_manager
    
    # Import all models to register them
    from core.database.models import (
        User, Wallet, Transaction, Partner, Referral, Payout,
        Service, UserService, PromoCode, PromoCodeActivation,
        DailyBonusHistory, Setting, Event, Broadcast, BroadcastTrigger,
        UserWarning, UserBan, ModerationLog, Commission
    )
    
    await db_manager.init()
    await db_manager.create_tables()
    
    return db_manager


async def cleanup_database(db_manager):
    """Cleanup test database"""
    if db_manager:
        await db_manager.drop_tables()
        await db_manager.close()


def test_result(name: str, passed: bool, error: str = None):
    """Record test result"""
    if passed:
        PASSED.append(name)
        print(f"  [OK] {name}")
    else:
        FAILED.append((name, error))
        print(f"  [FAIL] {name}: {error}")


# ==================== TESTS ====================

async def test_01_models():
    """Test all models are importable"""
    try:
        from core.database.models import (
            User, Wallet, Transaction, Partner, Referral, Payout,
            Service, UserService, PromoCode, PromoCodeActivation,
            DailyBonusHistory, Setting, Event, Broadcast, BroadcastTrigger,
            UserWarning, UserBan, ModerationLog, Commission
        )
        
        models = [
            User, Wallet, Transaction, Partner, Referral, Payout,
            Service, UserService, PromoCode, PromoCodeActivation,
            DailyBonusHistory, Setting, Event, Broadcast, BroadcastTrigger,
            UserWarning, UserBan, ModerationLog, Commission
        ]
        
        for model in models:
            assert model.__tablename__ is not None
        
        test_result(f"Models ({len(models)} total)", True)
    except Exception as e:
        test_result("Models", False, str(e))


async def test_02_user_creation():
    """Test user creation"""
    try:
        from core.database import get_db
        from core.database.models import User, Wallet
        from sqlalchemy import select
        
        async with get_db() as session:
            user = User(
                telegram_id=123456789,
                telegram_username="testuser",
                first_name="Test",
                language="ru",
                role="user"
            )
            session.add(user)
            await session.flush()
            
            wallet = Wallet(
                user_id=user.id,
                wallet_type="main",
                balance=Decimal("0")
            )
            session.add(wallet)
        
        async with get_db() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == 123456789)
            )
            user = result.scalar_one()
            assert user.telegram_username == "testuser"
        
        test_result("User creation", True)
    except Exception as e:
        test_result("User creation", False, str(e))


async def test_03_gton_balance():
    """Test GTON balance operations"""
    try:
        from core.database import get_db
        from core.database.models import User, Wallet, Transaction
        from sqlalchemy import select
        
        async with get_db() as session:
            user = User(telegram_id=111111111, language="ru", role="user")
            session.add(user)
            await session.flush()
            user_id = user.id
            
            wallet = Wallet(
                user_id=user_id,
                wallet_type="main",
                balance=Decimal("0")
            )
            session.add(wallet)
        
        # Add balance
        async with get_db() as session:
            result = await session.execute(
                select(Wallet).where(Wallet.user_id == user_id)
            )
            wallet = result.scalar_one()
            wallet.balance = Decimal("100.5")
            
            tx = Transaction(
                user_id=user_id,
                wallet_id=wallet.id,
                type="credit",
                amount=Decimal("100.5"),
                direction="credit"
            )
            session.add(tx)
        
        # Verify
        async with get_db() as session:
            result = await session.execute(
                select(Wallet).where(Wallet.user_id == user_id)
            )
            wallet = result.scalar_one()
            assert wallet.balance == Decimal("100.5")
        
        test_result("GTON balance operations", True)
    except Exception as e:
        test_result("GTON balance operations", False, str(e))


async def test_04_referral():
    """Test referral creation"""
    try:
        from core.database import get_db
        from core.database.models import User, Referral
        from sqlalchemy import select
        
        async with get_db() as session:
            referrer = User(telegram_id=222222222, referral_code="REF123", language="ru", role="user")
            session.add(referrer)
            await session.flush()
            referrer_id = referrer.id
            
            referred = User(telegram_id=333333333, language="ru", role="user")
            session.add(referred)
            await session.flush()
            referred_id = referred.id
            
            referral = Referral(
                referrer_id=referrer_id,
                referred_id=referred_id,
                level=1,
                is_active=True
            )
            session.add(referral)
        
        async with get_db() as session:
            result = await session.execute(
                select(Referral).where(Referral.referred_id == referred_id)
            )
            ref = result.scalar_one()
            assert ref.referrer_id == referrer_id
        
        test_result("Referral creation", True)
    except Exception as e:
        test_result("Referral creation", False, str(e))


async def test_05_partner():
    """Test partner creation and balance"""
    try:
        from core.database import get_db
        from core.database.models import User, Partner
        from sqlalchemy import select
        
        async with get_db() as session:
            user = User(telegram_id=444444444, language="ru", role="user")
            session.add(user)
            await session.flush()
            
            partner = Partner(
                user_id=user.id,
                referral_code="PARTNER123",
                status="active",
                level1_percent=20,
                balance=Decimal("100"),
                frozen_balance=Decimal("30"),
                total_earned=Decimal("100"),
                total_withdrawn=Decimal("0")
            )
            session.add(partner)
            await session.flush()
            partner_id = partner.id
        
        async with get_db() as session:
            result = await session.execute(
                select(Partner).where(Partner.id == partner_id)
            )
            partner = result.scalar_one()
            
            assert partner.balance == Decimal("100")
            assert partner.frozen_balance == Decimal("30")
            assert partner.available_balance == Decimal("70")
        
        test_result("Partner (balance: 100, frozen: 30, available: 70)", True)
    except Exception as e:
        test_result("Partner", False, str(e))


async def test_06_payout():
    """Test payout model"""
    try:
        from core.database import get_db
        from core.database.models import User, Partner, Payout
        from sqlalchemy import select
        
        async with get_db() as session:
            user = User(telegram_id=555555555, language="ru", role="user")
            session.add(user)
            await session.flush()
            
            partner = Partner(
                user_id=user.id,
                referral_code="PAYOUT_TEST",
                status="active",
                balance=Decimal("50"),
                frozen_balance=Decimal("0")
            )
            session.add(partner)
            await session.flush()
            
            payout = Payout(
                partner_id=partner.id,
                amount_gton=Decimal("30"),
                fee_gton=Decimal("0"),
                amount_fiat=Decimal("3000"),
                currency="RUB",
                gton_rate=Decimal("100"),
                method="card",
                status="pending",
                details={"card": "4276****1234"}
            )
            session.add(payout)
        
        async with get_db() as session:
            result = await session.execute(
                select(Payout).where(Payout.status == "pending")
            )
            payout = result.scalar_one()
            assert payout.amount_gton == Decimal("30")
            assert payout.amount_fiat == Decimal("3000")
        
        test_result("Payout (30 GTON -> 3000 RUB)", True)
    except Exception as e:
        test_result("Payout", False, str(e))


async def test_07_promocode():
    """Test promocode"""
    try:
        from core.database import get_db
        from core.database.models import PromoCode
        from sqlalchemy import select
        
        async with get_db() as session:
            promo = PromoCode(
                code="TEST50",
                reward_type="gton",
                reward_value=50.0,  # Float for SQLite
                max_activations=100,
                current_activations=0,
                is_active=True
            )
            session.add(promo)
        
        async with get_db() as session:
            result = await session.execute(
                select(PromoCode).where(PromoCode.code == "TEST50")
            )
            promo = result.scalar_one()
            assert promo.reward_value == 50.0
            assert promo.is_active == True
        
        test_result("Promocode (TEST50: 50 GTON)", True)
    except Exception as e:
        test_result("Promocode", False, str(e))


async def test_08_daily_bonus():
    """Test daily bonus"""
    try:
        from core.database import get_db
        from core.database.models import User, DailyBonus, DailyBonusHistory
        from sqlalchemy import select
        
        async with get_db() as session:
            user = User(telegram_id=666666666, language="ru", role="user")
            session.add(user)
            await session.flush()
            
            # Create DailyBonus first
            daily_bonus = DailyBonus(
                user_id=user.id,
                current_streak=7,
                max_streak=7,
                total_claims=7,
                total_tokens=21
            )
            session.add(daily_bonus)
            await session.flush()
            
            bonus_history = DailyBonusHistory(
                user_id=user.id,
                daily_bonus_id=daily_bonus.id,
                day_number=7,
                tokens=5,
                streak=7
            )
            session.add(bonus_history)
        
        async with get_db() as session:
            result = await session.execute(
                select(DailyBonusHistory).where(DailyBonusHistory.day_number == 7)
            )
            bonus = result.scalar_one()
            assert bonus.tokens == 5
        
        test_result("Daily bonus (Day 7: 5 tokens)", True)
    except Exception as e:
        test_result("Daily bonus", False, str(e))


async def test_09_settings():
    """Test settings"""
    try:
        from core.database import get_db
        from core.database.models import Setting
        from sqlalchemy import select
        
        async with get_db() as session:
            setting = Setting(
                key="test.setting",
                value="100",
                value_type="int",
                category="test"
            )
            session.add(setting)
        
        async with get_db() as session:
            result = await session.execute(
                select(Setting).where(Setting.key == "test.setting")
            )
            setting = result.scalar_one()
            assert setting.get_typed_value() == 100
        
        test_result("Settings (typed value)", True)
    except Exception as e:
        test_result("Settings", False, str(e))


async def test_10_commission():
    """Test commission model"""
    try:
        from core.database import get_db
        from core.database.models import User, Commission
        from sqlalchemy import select
        
        async with get_db() as session:
            referrer = User(telegram_id=777777777, language="ru", role="user")
            session.add(referrer)
            await session.flush()
            
            referred = User(telegram_id=888888888, language="ru", role="user")
            session.add(referred)
            await session.flush()
            
            commission = Commission(
                referrer_id=referrer.id,
                referred_id=referred.id,
                commission_amount=Decimal("10"),
                commission_percent=Decimal("10"),
                source_amount=Decimal("100"),
                action="purchase"
            )
            session.add(commission)
        
        async with get_db() as session:
            result = await session.execute(
                select(Commission).where(Commission.commission_amount == Decimal("10"))
            )
            comm = result.scalar_one()
            assert comm.commission_percent == Decimal("10")
        
        test_result("Commission (10% of 100 = 10 GTON)", True)
    except Exception as e:
        test_result("Commission", False, str(e))


async def test_11_moderation():
    """Test moderation"""
    try:
        from core.database import get_db
        from core.database.models import User, UserWarning, UserBan
        from sqlalchemy import select
        
        async with get_db() as session:
            user = User(telegram_id=999999999, language="ru", role="user")
            session.add(user)
            await session.flush()
            
            warning = UserWarning(
                user_id=user.id,
                reason="Test warning",
                issued_by=1
            )
            session.add(warning)
            
            ban = UserBan(
                user_id=user.id,
                ban_type="temporary",
                reason="Test ban",
                banned_by=1,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(ban)
            
            user.is_blocked = True
        
        async with get_db() as session:
            result = await session.execute(
                select(UserWarning)
            )
            warnings = result.scalars().all()
            
            result = await session.execute(
                select(UserBan)
            )
            bans = result.scalars().all()
            
            assert len(warnings) >= 1
            assert len(bans) >= 1
        
        test_result("Moderation (warnings, bans)", True)
    except Exception as e:
        test_result("Moderation", False, str(e))


async def test_12_broadcast():
    """Test broadcast"""
    try:
        from core.database import get_db
        from core.database.models import Broadcast
        from sqlalchemy import select
        
        async with get_db() as session:
            broadcast = Broadcast(
                name="Test Broadcast",
                text="Hello, {name}!",
                status="draft",
                created_by=1
            )
            session.add(broadcast)
        
        async with get_db() as session:
            result = await session.execute(
                select(Broadcast).where(Broadcast.name == "Test Broadcast")
            )
            bc = result.scalar_one()
            assert bc.text == "Hello, {name}!"
        
        test_result("Broadcast", True)
    except Exception as e:
        test_result("Broadcast", False, str(e))


async def test_13_payment_constants():
    """Test payment constants"""
    try:
        from core.payments.constants import (
            ProviderId, Currency, PaymentStatus,
            TransactionType, TransactionSource, Limits, Fees
        )
        
        assert ProviderId.TON == "ton"
        assert ProviderId.YOOKASSA == "yookassa"
        assert Currency.GTON == "GTON"
        assert Currency.RUB == "RUB"
        assert TransactionType.CREDIT == "credit"
        assert TransactionType.DEBIT == "debit"
        assert Limits.MIN_DEPOSIT_GTON == Decimal("1.0")
        
        test_result("Payment constants", True)
    except Exception as e:
        test_result("Payment constants", False, str(e))


async def test_14_core_api():
    """Test CoreAPI"""
    try:
        from core.database import get_db
        from core.database.models import User, Wallet
        from core.plugins.core_api import CoreAPI
        from sqlalchemy import select
        
        async with get_db() as session:
            user = User(telegram_id=101010101, language="ru", role="user")
            session.add(user)
            await session.flush()
            user_id = user.id
            
            wallet = Wallet(
                user_id=user_id,
                wallet_type="main",
                balance=Decimal("100")
            )
            session.add(wallet)
        
        api = CoreAPI("test_service")
        
        # Test get_balance
        balance = await api.get_balance(user_id)
        assert balance == Decimal("100")
        
        # Test set_user_state
        await api.set_user_state(user_id, "test_state", {"key": "value"})
        
        # Test get_user_state
        state, data = await api.get_user_state(user_id)
        assert state == "test_state"
        
        # Test clear_user_state
        await api.clear_user_state(user_id)
        state, data = await api.get_user_state(user_id)
        assert state is None
        
        test_result("CoreAPI (balance, state)", True)
    except Exception as e:
        test_result("CoreAPI", False, str(e))


async def test_15_gton_conversion():
    """Test GTON conversion"""
    try:
        from core.payments.converter import currency_converter
        
        # Test format
        from core.platform.telegram.utils import format_gton
        
        result = format_gton(Decimal("123.456789"))
        assert "123.46" in result or "123.45" in result
        
        test_result("GTON formatting", True)
    except Exception as e:
        test_result("GTON formatting", False, str(e))


# ==================== MAIN ====================

async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("FuBot Core - Full Test Suite")
    print("="*60 + "\n")
    
    # Setup
    print("[*] Setting up database...")
    db_manager = await setup_database()
    print()
    
    # Run tests
    print("[*] Running tests...\n")
    
    await test_01_models()
    await test_02_user_creation()
    await test_03_gton_balance()
    await test_04_referral()
    await test_05_partner()
    await test_06_payout()
    await test_07_promocode()
    await test_08_daily_bonus()
    await test_09_settings()
    await test_10_commission()
    await test_11_moderation()
    await test_12_broadcast()
    await test_13_payment_constants()
    await test_14_core_api()
    await test_15_gton_conversion()
    
    # Cleanup
    print("\n[*] Cleaning up...")
    await cleanup_database(db_manager)
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"\nPassed: {len(PASSED)}")
    print(f"Failed: {len(FAILED)}")
    
    if FAILED:
        print("\nFailed tests:")
        for name, error in FAILED:
            print(f"   - {name}: {error}")
    
    print("\n" + "="*60)
    if not FAILED:
        print("ALL TESTS PASSED!")
    else:
        print(f"{len(FAILED)} test(s) failed")
    print("="*60 + "\n")
    
    return len(FAILED) == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
