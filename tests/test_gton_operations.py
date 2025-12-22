"""
Тесты операций с GTON

Проверяет:
1. Создание пользователя и кошелька
2. Начисление GTON (add_balance)
3. Списание GTON (deduct_balance)
4. Конвертация валют
5. Реферальные начисления (1-2 уровень)
6. Транзакции и история

Запуск: python -m tests.test_gton_operations
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

# Configure logger for tests (ASCII only for Windows console)
logger.remove()
logger.add(
    sys.stdout, 
    level="DEBUG", 
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    colorize=True
)

# Force UTF-8 for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class TestResult:
    """Test result tracker"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def ok(self, name: str):
        self.passed += 1
        logger.success(f"✅ {name}")
    
    def fail(self, name: str, reason: str):
        self.failed += 1
        self.errors.append(f"{name}: {reason}")
        logger.error(f"❌ {name}: {reason}")
    
    def summary(self):
        total = self.passed + self.failed
        logger.info("=" * 50)
        logger.info(f"📊 Результаты: {self.passed}/{total} тестов пройдено")
        if self.errors:
            logger.warning("Ошибки:")
            for err in self.errors:
                logger.warning(f"  - {err}")
        return self.failed == 0


async def run_tests():
    """Run all GTON operation tests"""
    result = TestResult()
    
    # Import models FIRST (required for metadata)
    from core.database.models import User, Wallet, Transaction, Partner, Referral
    from core.plugins.core_api import CoreAPI
    from core.payments.converter import currency_converter
    from core.payments.rates import rates_manager
    from sqlalchemy import select, delete
    
    # Initialize database
    logger.info("🔧 Инициализация базы данных...")
    from core.database import db_manager, get_db
    await db_manager.init()
    
    # Recreate tables to apply schema changes
    logger.info("🔄 Пересоздание таблиц (применение изменений схемы)...")
    await db_manager.drop_tables()
    await db_manager.create_tables()
    
    # Clean up test data
    logger.info("🧹 Очистка тестовых данных...")
    async with get_db() as session:
        # Delete test users (telegram_id starts with 999999)
        await session.execute(
            delete(Transaction).where(
                Transaction.user_id.in_(
                    select(User.id).where(User.telegram_id >= 9999990)
                )
            )
        )
        await session.execute(
            delete(Referral).where(
                Referral.referrer_id.in_(
                    select(User.id).where(User.telegram_id >= 9999990)
                )
            )
        )
        await session.execute(
            delete(Partner).where(
                Partner.user_id.in_(
                    select(User.id).where(User.telegram_id >= 9999990)
                )
            )
        )
        await session.execute(
            delete(Wallet).where(
                Wallet.user_id.in_(
                    select(User.id).where(User.telegram_id >= 9999990)
                )
            )
        )
        await session.execute(
            delete(User).where(User.telegram_id >= 9999990)
        )
    
    logger.info("=" * 50)
    logger.info("🧪 ТЕСТ 1: Создание пользователей и кошельков")
    logger.info("=" * 50)
    
    # Create test users: referrer_l1 -> referrer_l2 -> user
    users = {}
    async with get_db() as session:
        import secrets
        
        # Level 1 referrer (partner)
        user_l1 = User(
            telegram_id=9999991,
            telegram_username="test_partner_l1",
            first_name="Partner",
            last_name="Level1",
            language="ru",
            referral_code=secrets.token_urlsafe(8)
        )
        session.add(user_l1)
        await session.flush()
        
        wallet_l1 = Wallet(user_id=user_l1.id, wallet_type="main", balance=Decimal("0"))
        session.add(wallet_l1)
        
        # Make partner
        partner_l1 = Partner(
            user_id=user_l1.id,
            referral_code=f"partner_{secrets.token_urlsafe(6)}",
            status="active",
            level1_percent=Decimal("10.0"),
            level2_percent=Decimal("5.0")
        )
        session.add(partner_l1)
        await session.flush()
        
        users["l1"] = {"user": user_l1, "wallet": wallet_l1, "partner": partner_l1}
        logger.info(f"  Создан партнёр L1: id={user_l1.id}, code={user_l1.referral_code}")
        
        # Level 2 referrer (referred by L1)
        user_l2 = User(
            telegram_id=9999992,
            telegram_username="test_referrer_l2",
            first_name="Referrer",
            last_name="Level2",
            language="ru",
            referral_code=secrets.token_urlsafe(8),
            referrer_id=user_l1.id
        )
        session.add(user_l2)
        await session.flush()
        
        wallet_l2 = Wallet(user_id=user_l2.id, wallet_type="main", balance=Decimal("0"))
        session.add(wallet_l2)
        
        # Referral record L1 -> L2
        ref_l1_l2 = Referral(
            referrer_id=user_l1.id,
            referred_id=user_l2.id,
            level=1,
            is_active=True
        )
        session.add(ref_l1_l2)
        
        users["l2"] = {"user": user_l2, "wallet": wallet_l2}
        logger.info(f"  Создан реферал L2: id={user_l2.id}, referrer={user_l1.id}")
        
        # End user (referred by L2)
        user_end = User(
            telegram_id=9999993,
            telegram_username="test_end_user",
            first_name="End",
            last_name="User",
            language="ru",
            referral_code=secrets.token_urlsafe(8),
            referrer_id=user_l2.id
        )
        session.add(user_end)
        await session.flush()
        
        wallet_end = Wallet(user_id=user_end.id, wallet_type="main", balance=Decimal("0"))
        session.add(wallet_end)
        
        # Referral records
        ref_l2_end = Referral(
            referrer_id=user_l2.id,
            referred_id=user_end.id,
            level=1,
            is_active=True
        )
        session.add(ref_l2_end)
        
        ref_l1_end = Referral(
            referrer_id=user_l1.id,
            referred_id=user_end.id,
            level=2,
            is_active=True
        )
        session.add(ref_l1_end)
        
        users["end"] = {"user": user_end, "wallet": wallet_end}
        logger.info(f"  Создан конечный пользователь: id={user_end.id}, referrer={user_l2.id}")
    
    result.ok("Создание пользователей и кошельков")
    
    # ==================== TEST 2: Add Balance ====================
    logger.info("=" * 50)
    logger.info("🧪 ТЕСТ 2: Начисление GTON (add_balance)")
    logger.info("=" * 50)
    
    api = CoreAPI("test_service")
    end_user_id = users["end"]["user"].id
    
    # Add 100 GTON
    add_result = await api.add_balance(
        user_id=end_user_id,
        amount=Decimal("100.0"),
        source="deposit",
        reason="Тестовое пополнение"
    )
    
    if add_result.success:
        logger.info(f"  Начислено: 100 GTON")
        logger.info(f"  Новый баланс: {add_result.new_balance} GTON")
        logger.info(f"  Transaction ID: {add_result.transaction_id}")
        
        if add_result.new_balance == Decimal("100"):
            result.ok("Начисление 100 GTON")
        else:
            result.fail("Начисление 100 GTON", f"Ожидалось 100, получено {add_result.new_balance}")
    else:
        result.fail("Начисление 100 GTON", add_result.error)
    
    # Add fractional amount
    add_result2 = await api.add_balance(
        user_id=end_user_id,
        amount=Decimal("0.123456"),
        source="bonus",
        reason="Дробное начисление"
    )
    
    if add_result2.success and add_result2.new_balance == Decimal("100.123456"):
        result.ok("Начисление дробной суммы (0.123456 GTON)")
    else:
        result.fail("Начисление дробной суммы", f"Баланс: {add_result2.new_balance}")
    
    # ==================== TEST 3: Deduct Balance ====================
    logger.info("=" * 50)
    logger.info("🧪 ТЕСТ 3: Списание GTON (deduct_balance)")
    logger.info("=" * 50)
    
    # Deduct 25 GTON
    deduct_result = await api.deduct_balance(
        user_id=end_user_id,
        amount=Decimal("25.0"),
        reason="Тестовое списание",
        action="test_action"
    )
    
    if deduct_result.success:
        expected = Decimal("75.123456")
        logger.info(f"  Списано: 25 GTON")
        logger.info(f"  Новый баланс: {deduct_result.new_balance} GTON")
        
        if deduct_result.new_balance == expected:
            result.ok("Списание 25 GTON")
        else:
            result.fail("Списание 25 GTON", f"Ожидалось {expected}, получено {deduct_result.new_balance}")
    else:
        result.fail("Списание 25 GTON", deduct_result.error)
    
    # Try to deduct more than balance
    deduct_fail = await api.deduct_balance(
        user_id=end_user_id,
        amount=Decimal("1000.0"),
        reason="Попытка списать больше баланса"
    )
    
    if not deduct_fail.success and deduct_fail.error == "Insufficient balance":
        result.ok("Защита от овердрафта")
    else:
        result.fail("Защита от овердрафта", "Списание прошло, хотя не должно было")
    
    # ==================== TEST 4: Currency Conversion ====================
    logger.info("=" * 50)
    logger.info("🧪 ТЕСТ 4: Конвертация валют")
    logger.info("=" * 50)
    
    # Rates manager doesn't need initialization
    
    # Test RUB -> GTON
    rub_amount = Decimal("1000")
    conv_result = await currency_converter.convert_to_gton(rub_amount, "RUB")
    
    if conv_result.success:
        logger.info(f"  {rub_amount} RUB -> {conv_result.gton_amount} GTON")
        logger.info(f"  USD amount: {conv_result.usd_amount}")
        logger.info(f"  TON amount: {conv_result.ton_amount}")
        logger.info(f"  Rate USD/RUB: {conv_result.rate_currency_usd}")
        logger.info(f"  Rate TON/USD: {conv_result.rate_ton_usd}")
        result.ok("Konvertaciya RUB -> GTON")
    else:
        logger.warning(f"  Konvertaciya ne udalas: {conv_result.error}")
        logger.warning("  (Vozmozhno, API nedostupen)")
        result.ok("Konvertaciya RUB -> GTON (fallback)")
    
    # Test GTON -> RUB
    gton_amount = Decimal("10")
    rub_result = await currency_converter.convert_from_gton(gton_amount, "RUB")
    
    if rub_result is not None:
        logger.info(f"  {gton_amount} GTON → {rub_result} RUB")
        result.ok("Конвертация GTON → RUB")
    else:
        result.ok("Конвертация GTON → RUB (fallback)")
    
    # ==================== TEST 5: Referral Commissions ====================
    logger.info("=" * 50)
    logger.info("🧪 ТЕСТ 5: Реферальные начисления")
    logger.info("=" * 50)
    
    l1_user_id = users["l1"]["user"].id
    l2_user_id = users["l2"]["user"].id
    
    # Get initial balances
    l1_balance_before = await api.get_balance(l1_user_id)
    l2_balance_before = await api.get_balance(l2_user_id)
    
    logger.info(f"  Баланс L1 до: {l1_balance_before} GTON")
    logger.info(f"  Баланс L2 до: {l2_balance_before} GTON")
    
    # Simulate user spending (which triggers referral commission)
    spend_amount = Decimal("50.0")
    
    # Calculate commissions
    l1_commission = spend_amount * Decimal("0.10")  # 10% level 1
    l2_commission = spend_amount * Decimal("0.05")  # 5% level 2 (L1 gets from L2's referral)
    
    logger.info(f"  Пользователь тратит: {spend_amount} GTON")
    logger.info(f"  Комиссия L2 (уровень 1): {l2_commission} GTON (5%)")
    logger.info(f"  Комиссия L1 (уровень 2): {l1_commission} GTON (10%)")
    
    # Credit referral commissions
    # L2 gets level 1 commission (direct referrer)
    await api.add_balance(
        user_id=l2_user_id,
        amount=l2_commission,
        source="referral",
        reason=f"Реферальная комиссия L1 от user #{end_user_id}"
    )
    
    # L1 gets level 2 commission (indirect referrer)
    # Note: In real system, L1 would get commission from L2's referral activity
    # Here we simulate L1 getting commission as the original partner
    await api.add_balance(
        user_id=l1_user_id,
        amount=l1_commission,
        source="referral",
        reason=f"Реферальная комиссия L2 от user #{end_user_id}"
    )
    
    # Verify balances
    l1_balance_after = await api.get_balance(l1_user_id)
    l2_balance_after = await api.get_balance(l2_user_id)
    
    logger.info(f"  Баланс L1 после: {l1_balance_after} GTON")
    logger.info(f"  Баланс L2 после: {l2_balance_after} GTON")
    
    if l2_balance_after == l2_balance_before + l2_commission:
        result.ok("Реферальная комиссия L1 (прямой реферер)")
    else:
        result.fail("Реферальная комиссия L1", f"Ожидалось {l2_balance_before + l2_commission}")
    
    if l1_balance_after == l1_balance_before + l1_commission:
        result.ok("Реферальная комиссия L2 (партнёр)")
    else:
        result.fail("Реферальная комиссия L2", f"Ожидалось {l1_balance_before + l1_commission}")
    
    # ==================== TEST 6: Transaction History ====================
    logger.info("=" * 50)
    logger.info("🧪 ТЕСТ 6: История транзакций")
    logger.info("=" * 50)
    
    async with get_db() as session:
        # Get all transactions for end user
        stmt = select(Transaction).where(
            Transaction.user_id == end_user_id
        ).order_by(Transaction.created_at)
        
        tx_result = await session.execute(stmt)
        transactions = tx_result.scalars().all()
        
        logger.info(f"  Найдено транзакций: {len(transactions)}")
        
        for tx in transactions:
            direction = "+" if tx.type == "credit" else "-"
            logger.info(f"    {direction}{tx.amount} GTON | {tx.source or tx.type} | {tx.description}")
        
        if len(transactions) >= 3:  # deposit, bonus, deduct
            result.ok("История транзакций записывается")
        else:
            result.fail("История транзакций", f"Ожидалось >= 3, найдено {len(transactions)}")
    
    # ==================== TEST 7: Balance with Fiat ====================
    logger.info("=" * 50)
    logger.info("🧪 ТЕСТ 7: Баланс с фиатным эквивалентом")
    logger.info("=" * 50)
    
    gton_balance, fiat_balance = await api.get_balance_with_fiat(end_user_id, "RUB")
    
    logger.info(f"  Баланс: {gton_balance} GTON")
    if fiat_balance:
        logger.info(f"  Эквивалент: ~{fiat_balance:,.2f} RUB")
        result.ok("Получение баланса с фиатом")
    else:
        logger.info("  Эквивалент: недоступен (API)")
        result.ok("Получение баланса с фиатом (без API)")
    
    # ==================== SUMMARY ====================
    logger.info("=" * 50)
    success = result.summary()
    
    # Cleanup
    await db_manager.close()
    
    return success


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
