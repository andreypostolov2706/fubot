"""
Referral System Test - Полный тест реферальной программы

Тестирует:
1. Создание реферальной связи (ref_XXX)
2. Создание партнёрской связи (partner_XXX)
3. Начисление комиссий при списании
4. Статистика рефералов
5. Партнёрский баланс
6. Вывод средств партнёра

Запуск: python tests/test_referral_system.py
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import db_manager, get_db
from core.database.models import (
    User, Wallet, Transaction, Partner, Referral, 
    Commission, Payout, Setting
)
from sqlalchemy import select, delete


PASSED = []
FAILED = []


def test_result(name: str, passed: bool, error: str = None):
    if passed:
        PASSED.append(name)
        print(f"  [OK] {name}")
    else:
        FAILED.append((name, error))
        print(f"  [FAIL] {name}: {error}")


async def cleanup():
    """Clean up test data"""
    async with get_db() as session:
        # Delete test users (telegram_id starts with 9999)
        await session.execute(delete(Commission).where(Commission.referrer_id >= 100))
        await session.execute(delete(Payout))
        await session.execute(delete(Referral))
        await session.execute(delete(Partner))
        await session.execute(delete(Transaction))
        await session.execute(delete(Wallet))
        await session.execute(delete(User).where(User.telegram_id >= 999900000))


async def create_test_user(telegram_id: int, username: str) -> tuple[int, str]:
    """Create test user and return (user_id, referral_code)"""
    import secrets
    
    async with get_db() as session:
        ref_code = secrets.token_urlsafe(8)
        user = User(
            telegram_id=telegram_id,
            telegram_username=username,
            first_name=username,
            language="ru",
            referral_code=ref_code
        )
        session.add(user)
        await session.flush()
        
        wallet = Wallet(user_id=user.id, wallet_type="main", balance=Decimal("100"))
        session.add(wallet)
        
        return user.id, ref_code


async def create_test_partner(user_id: int, code: str) -> int:
    """Create test partner and return partner_id"""
    async with get_db() as session:
        partner = Partner(
            user_id=user_id,
            referral_code=code,
            status="active",
            level1_percent=Decimal("15"),  # 15% commission
            balance=Decimal("0"),
            frozen_balance=Decimal("0"),
            total_earned=Decimal("0"),
            total_withdrawn=Decimal("0"),
            total_referrals=0
        )
        session.add(partner)
        await session.flush()
        return partner.id


async def test_01_user_referral():
    """Test regular user referral (ref_XXX)"""
    try:
        from core.platform.telegram.handlers.start import process_referral
        
        # Create referrer (User A)
        user_a_id, user_a_code = await create_test_user(999900001, "user_a")
        
        # Create referred user (User B)
        user_b_id, _ = await create_test_user(999900002, "user_b")
        
        # Process referral
        result = await process_referral(user_b_id, f"ref_{user_a_code}")
        
        assert result == True, "Referral should be created"
        
        # Verify referral exists
        async with get_db() as session:
            ref = await session.execute(
                select(Referral).where(
                    Referral.referrer_id == user_a_id,
                    Referral.referred_id == user_b_id
                )
            )
            referral = ref.scalar_one_or_none()
            
            assert referral is not None, "Referral record should exist"
            assert referral.level == 1
            assert referral.is_active == True
            assert referral.partner_id is None  # Not a partner referral
        
        test_result("User referral (ref_XXX)", True)
        return user_a_id, user_b_id
        
    except Exception as e:
        test_result("User referral (ref_XXX)", False, str(e))
        return None, None


async def test_02_partner_referral():
    """Test partner referral (partner_XXX)"""
    try:
        from core.platform.telegram.handlers.start import process_referral
        
        # Create partner user (User C)
        user_c_id, _ = await create_test_user(999900003, "partner_c")
        partner_id = await create_test_partner(user_c_id, "PARTNER123")
        
        # Create referred user (User D)
        user_d_id, _ = await create_test_user(999900004, "user_d")
        
        # Process partner referral
        result = await process_referral(user_d_id, "partner_PARTNER123")
        
        assert result == True, "Partner referral should be created"
        
        # Verify referral exists with partner_id
        async with get_db() as session:
            ref = await session.execute(
                select(Referral).where(
                    Referral.referrer_id == user_c_id,
                    Referral.referred_id == user_d_id
                )
            )
            referral = ref.scalar_one_or_none()
            
            assert referral is not None, "Referral record should exist"
            assert referral.partner_id == partner_id, "Should have partner_id"
            
            # Check partner stats updated
            p = await session.execute(select(Partner).where(Partner.id == partner_id))
            partner = p.scalar_one()
            assert partner.total_referrals == 1, "Partner should have 1 referral"
        
        test_result("Partner referral (partner_XXX)", True)
        return user_c_id, user_d_id, partner_id
        
    except Exception as e:
        test_result("Partner referral (partner_XXX)", False, str(e))
        return None, None, None


async def test_03_duplicate_referral():
    """Test that duplicate referral is rejected"""
    try:
        from core.platform.telegram.handlers.start import process_referral
        
        # Create users
        user_e_id, user_e_code = await create_test_user(999900005, "user_e")
        user_f_id, user_f_code = await create_test_user(999900006, "user_f")
        
        # First referral - should succeed
        result1 = await process_referral(user_f_id, f"ref_{user_e_code}")
        assert result1 == True
        
        # Second referral - should fail (already has referrer)
        result2 = await process_referral(user_f_id, f"ref_{user_e_code}")
        assert result2 == False, "Duplicate referral should be rejected"
        
        test_result("Duplicate referral rejected", True)
        
    except Exception as e:
        test_result("Duplicate referral rejected", False, str(e))


async def test_04_self_referral():
    """Test that self-referral is rejected"""
    try:
        from core.platform.telegram.handlers.start import process_referral
        
        # Create user
        user_g_id, user_g_code = await create_test_user(999900007, "user_g")
        
        # Try self-referral
        result = await process_referral(user_g_id, f"ref_{user_g_code}")
        assert result == False, "Self-referral should be rejected"
        
        test_result("Self-referral rejected", True)
        
    except Exception as e:
        test_result("Self-referral rejected", False, str(e))


async def test_05_commission_on_deduct():
    """Test commission is credited when referred user spends GTON"""
    try:
        from core.platform.telegram.handlers.start import process_referral
        from core.plugins.core_api import CoreAPI
        
        # Create referrer
        referrer_id, referrer_code = await create_test_user(999900010, "referrer")
        
        # Create referred user with balance
        referred_id, _ = await create_test_user(999900011, "referred")
        
        # Create referral link
        await process_referral(referred_id, f"ref_{referrer_code}")
        
        # Get referrer balance before
        async with get_db() as session:
            w = await session.execute(
                select(Wallet).where(
                    Wallet.user_id == referrer_id,
                    Wallet.wallet_type == "main"
                )
            )
            referrer_wallet = w.scalar_one()
            balance_before = Decimal(str(referrer_wallet.balance))
        
        # Deduct from referred user (triggers commission)
        api = CoreAPI("test_service")
        result = await api.deduct_balance(
            user_id=referred_id,
            amount=Decimal("10"),
            action="test_purchase",
            reason="Test purchase"
        )
        
        assert result.success, f"Deduct should succeed: {result.error}"
        
        # Check referrer received commission (10% default)
        async with get_db() as session:
            w = await session.execute(
                select(Wallet).where(
                    Wallet.user_id == referrer_id,
                    Wallet.wallet_type == "main"
                )
            )
            referrer_wallet = w.scalar_one()
            balance_after = Decimal(str(referrer_wallet.balance))
            
            expected_commission = Decimal("1.0")  # 10% of 10 GTON
            actual_commission = balance_after - balance_before
            
            assert actual_commission == expected_commission, \
                f"Expected {expected_commission}, got {actual_commission}"
            
            # Check Commission record exists
            c = await session.execute(
                select(Commission).where(
                    Commission.referrer_id == referrer_id,
                    Commission.referred_id == referred_id
                )
            )
            commission = c.scalar_one_or_none()
            assert commission is not None, "Commission record should exist"
            assert commission.commission_amount == expected_commission
            assert commission.commission_percent == Decimal("10")
        
        test_result("Commission on deduct (10%)", True)
        
    except Exception as e:
        test_result("Commission on deduct (10%)", False, str(e))


async def test_06_partner_commission():
    """Test partner gets custom commission rate"""
    try:
        from core.platform.telegram.handlers.start import process_referral
        from core.plugins.core_api import CoreAPI
        
        # Create partner with 15% commission
        partner_user_id, _ = await create_test_user(999900020, "partner_user")
        partner_id = await create_test_partner(partner_user_id, "TESTPARTNER")
        
        # Create referred user
        referred_id, _ = await create_test_user(999900021, "partner_referred")
        
        # Create partner referral
        await process_referral(referred_id, "partner_TESTPARTNER")
        
        # Get partner balance before
        async with get_db() as session:
            p = await session.execute(select(Partner).where(Partner.id == partner_id))
            partner = p.scalar_one()
            partner_balance_before = Decimal(str(partner.balance))
        
        # Deduct from referred user
        api = CoreAPI("test_service")
        await api.deduct_balance(
            user_id=referred_id,
            amount=Decimal("20"),
            action="test_purchase"
        )
        
        # Check partner received 15% commission
        async with get_db() as session:
            p = await session.execute(select(Partner).where(Partner.id == partner_id))
            partner = p.scalar_one()
            partner_balance_after = Decimal(str(partner.balance))
            
            expected_commission = Decimal("3.0")  # 15% of 20 GTON
            actual_commission = partner_balance_after - partner_balance_before
            
            assert actual_commission == expected_commission, \
                f"Expected {expected_commission}, got {actual_commission}"
            
            # Check total_earned updated
            assert partner.total_earned >= expected_commission
        
        test_result("Partner commission (15%)", True)
        
    except Exception as e:
        test_result("Partner commission (15%)", False, str(e))


async def test_07_referral_stats():
    """Test referral statistics are updated"""
    try:
        from core.platform.telegram.handlers.start import process_referral
        from core.plugins.core_api import CoreAPI
        
        # Create referrer
        referrer_id, referrer_code = await create_test_user(999900030, "stats_referrer")
        
        # Create referred user
        referred_id, _ = await create_test_user(999900031, "stats_referred")
        await process_referral(referred_id, f"ref_{referrer_code}")
        
        # Make multiple purchases
        api = CoreAPI("test_service")
        await api.deduct_balance(referred_id, Decimal("5"), action="purchase1")
        await api.deduct_balance(referred_id, Decimal("10"), action="purchase2")
        await api.deduct_balance(referred_id, Decimal("15"), action="purchase3")
        
        # Check referral stats
        async with get_db() as session:
            r = await session.execute(
                select(Referral).where(Referral.referred_id == referred_id)
            )
            referral = r.scalar_one()
            
            expected_payments = Decimal("30")  # 5 + 10 + 15
            expected_commission = Decimal("3")  # 10% of 30
            
            assert referral.total_payments == expected_payments, \
                f"Expected payments {expected_payments}, got {referral.total_payments}"
            assert referral.total_commission == expected_commission, \
                f"Expected commission {expected_commission}, got {referral.total_commission}"
            assert referral.first_payment_at is not None
            assert referral.last_payment_at is not None
        
        test_result("Referral stats updated", True)
        
    except Exception as e:
        test_result("Referral stats updated", False, str(e))


async def test_08_payout_request():
    """Test partner payout request"""
    try:
        from core.payout.service import PayoutService
        
        # Create partner with balance
        partner_user_id, _ = await create_test_user(999900040, "payout_partner")
        
        async with get_db() as session:
            partner = Partner(
                user_id=partner_user_id,
                referral_code="PAYOUTTEST",
                status="active",
                level1_percent=Decimal("10"),
                balance=Decimal("50"),  # Has 50 GTON
                frozen_balance=Decimal("0"),
                total_earned=Decimal("50"),
                total_withdrawn=Decimal("0"),
                total_referrals=5
            )
            session.add(partner)
            await session.flush()
            partner_id = partner.id
        
        # Request payout
        payout_service = PayoutService()
        result = await payout_service.create_payout_request(
            partner_id=partner_id,
            amount_gton=Decimal("30"),
            method="card",
            details={"card": "4276****1234"},
            currency="RUB"
        )
        
        assert result.success, f"Payout request should succeed: {result.error}"
        
        # Check payout created
        async with get_db() as session:
            p = await session.execute(
                select(Payout).where(Payout.partner_id == partner_id)
            )
            payout = p.scalar_one_or_none()
            
            assert payout is not None, "Payout should exist"
            assert payout.status == "pending"
            assert payout.amount_gton == Decimal("30")
            
            # Check balance frozen
            partner_result = await session.execute(
                select(Partner).where(Partner.id == partner_id)
            )
            partner = partner_result.scalar_one()
            assert partner.frozen_balance == Decimal("30"), "Balance should be frozen"
        
        test_result("Payout request created", True)
        
    except Exception as e:
        test_result("Payout request created", False, str(e))


async def run_all_tests():
    """Run all referral system tests"""
    print("\n" + "=" * 60)
    print("REFERRAL SYSTEM TEST")
    print("=" * 60 + "\n")
    
    await db_manager.init()
    
    print("[*] Cleaning up test data...\n")
    await cleanup()
    
    print("[*] Testing referral creation...\n")
    await test_01_user_referral()
    await test_02_partner_referral()
    await test_03_duplicate_referral()
    await test_04_self_referral()
    
    print("\n[*] Testing commissions...\n")
    await test_05_commission_on_deduct()
    await test_06_partner_commission()
    await test_07_referral_stats()
    
    print("\n[*] Testing payouts...\n")
    await test_08_payout_request()
    
    print("\n[*] Cleaning up...\n")
    await cleanup()
    
    await db_manager.close()
    
    # Summary
    print("=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"\nPassed: {len(PASSED)}")
    print(f"Failed: {len(FAILED)}")
    
    if FAILED:
        print("\nFailed tests:")
        for name, error in FAILED:
            print(f"   - {name}: {error}")
    
    print("\n" + "=" * 60)
    if not FAILED:
        print("ALL TESTS PASSED!")
    else:
        print(f"{len(FAILED)} test(s) failed")
    print("=" * 60 + "\n")
    
    return len(FAILED) == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
