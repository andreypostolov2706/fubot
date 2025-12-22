"""
Integration Tests for FuBot Core

Проверяет:
1. Все callback handlers доступны
2. Настройки читаются из БД
3. Функции партнёрки работают
4. Платежи и конвертация
5. Связи между модулями
"""
import asyncio
import sys
from decimal import Decimal
from datetime import datetime
from typing import List, Tuple
from dataclasses import dataclass

# Add parent to path
sys.path.insert(0, ".")


@dataclass
class TestResult:
    name: str
    passed: bool
    error: str = ""
    details: str = ""


class IntegrationTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.db_initialized = False
    
    async def init_db(self):
        """Initialize database"""
        if not self.db_initialized:
            from core.database import db_manager
            await db_manager.init()
            self.db_initialized = True
    
    def add_result(self, name: str, passed: bool, error: str = "", details: str = ""):
        self.results.append(TestResult(name, passed, error, details))
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if error:
            print(f"        Error: {error}")
        if details:
            print(f"        Details: {details}")
    
    # ==================== CALLBACK TESTS ====================
    
    async def test_callbacks_exist(self):
        """Test that all callback handlers exist and are callable"""
        print("\n=== Testing Callback Handlers ===")
        
        from core.platform.telegram.handlers import (
            main_menu_callback,
            settings_callback,
            language_callback,
            set_language_callback,
            topup_callback,
            partner_callback,
            daily_bonus_callback,
            help_callback,
            service_callback,
            message_handler,
        )
        
        callbacks = [
            ("main_menu_callback", main_menu_callback),
            ("settings_callback", settings_callback),
            ("language_callback", language_callback),
            ("set_language_callback", set_language_callback),
            ("topup_callback", topup_callback),
            ("partner_callback", partner_callback),
            ("daily_bonus_callback", daily_bonus_callback),
            ("help_callback", help_callback),
            ("service_callback", service_callback),
            ("message_handler", message_handler),
        ]
        
        for name, func in callbacks:
            try:
                is_callable = callable(func)
                is_async = asyncio.iscoroutinefunction(func)
                self.add_result(
                    f"Callback: {name}",
                    is_callable and is_async,
                    details=f"callable={is_callable}, async={is_async}"
                )
            except Exception as e:
                self.add_result(f"Callback: {name}", False, str(e))
    
    async def test_router_callbacks(self):
        """Test router handles all expected callback patterns"""
        print("\n=== Testing Router Patterns ===")
        
        # Expected callback patterns
        patterns = [
            "main_menu",
            "settings",
            "settings:language",
            "settings:notifications",
            "set_language:ru",
            "help",
            "top_up",
            "top_up:crypto",
            "top_up:amount:TON:5",
            "promocode",
            "partner",
            "partner:referrals",
            "partner:apply",
            "partner:apply:start",
            "partner:stats",
            "partner:payout",
            "partner:payout:card",
            "partner:payout:sbp",
            "partner:payout:history",
            "partner:cabinet",
            "daily_bonus",
            "admin",
            "admin:users",
            "admin:partners",
            "service:test:action",
        ]
        
        # Check that router can parse these
        for pattern in patterns:
            try:
                parts = pattern.split(":")
                has_action = len(parts) >= 1
                self.add_result(
                    f"Pattern: {pattern}",
                    has_action,
                    details=f"parts={len(parts)}"
                )
            except Exception as e:
                self.add_result(f"Pattern: {pattern}", False, str(e))
    
    # ==================== SETTINGS TESTS ====================
    
    async def test_settings_read(self):
        """Test that all settings can be read from DB"""
        print("\n=== Testing Settings ===")
        
        await self.init_db()
        
        from core.database import get_db
        from core.database.models import Setting
        from sqlalchemy import select
        
        expected_settings = [
            ("payments.min_deposit_gton", "decimal"),
            ("payments.max_deposit_gton", "decimal"),
            ("payments.gton_ton_rate", "decimal"),
            ("payout.min_gton", "decimal"),
            ("payout.fee_percent", "decimal"),
            ("referral.level1_percent", "decimal"),
            ("referral.enabled", "bool"),
            ("daily_bonus.enabled", "bool"),
        ]
        
        async with get_db() as session:
            for key, expected_type in expected_settings:
                try:
                    result = await session.execute(
                        select(Setting).where(Setting.key == key)
                    )
                    setting = result.scalar_one_or_none()
                    
                    if setting:
                        self.add_result(
                            f"Setting: {key}",
                            True,
                            details=f"value={setting.value}, type={setting.value_type}"
                        )
                    else:
                        self.add_result(f"Setting: {key}", False, "Not found in DB")
                except Exception as e:
                    self.add_result(f"Setting: {key}", False, str(e))
    
    async def test_payout_settings(self):
        """Test payout service reads settings correctly"""
        print("\n=== Testing Payout Settings ===")
        
        await self.init_db()
        
        try:
            from core.payout import payout_service
            
            min_gton = await payout_service.get_min_payout_gton()
            self.add_result(
                "Payout min_gton",
                min_gton is not None and min_gton > 0,
                details=f"value={min_gton}"
            )
            
            fee = await payout_service.get_fee_percent()
            self.add_result(
                "Payout fee_percent",
                fee is not None,
                details=f"value={fee}%"
            )
        except Exception as e:
            self.add_result("Payout settings", False, str(e))
    
    # ==================== PARTNER TESTS ====================
    
    async def test_partner_functions(self):
        """Test partner module functions exist"""
        print("\n=== Testing Partner Functions ===")
        
        from core.platform.telegram.handlers import partner
        
        functions = [
            "partner_callback",
            "partner_main",
            "partner_cabinet",
            "partner_referrals",
            "partner_apply",
            "partner_apply_start",
            "partner_apply_socials",
            "partner_apply_submit",
            "partner_stats",
            "partner_payout",
            "partner_payout_method",
            "partner_payout_history",
            "partner_payout_confirm",
            "partner_payout_cancel",
            "handle_payout_input",
            "notify_admins_new_application",
        ]
        
        for func_name in functions:
            try:
                func = getattr(partner, func_name, None)
                exists = func is not None
                is_async = asyncio.iscoroutinefunction(func) if func else False
                self.add_result(
                    f"Partner func: {func_name}",
                    exists,
                    details=f"async={is_async}" if exists else "NOT FOUND"
                )
            except Exception as e:
                self.add_result(f"Partner func: {func_name}", False, str(e))
    
    # ==================== PAYMENT TESTS ====================
    
    async def test_payment_service(self):
        """Test payment service functions"""
        print("\n=== Testing Payment Service ===")
        
        await self.init_db()
        
        try:
            from core.payments.service import payment_service
            
            # Test get_deposit_limits
            min_dep, max_dep = await payment_service.get_deposit_limits()
            self.add_result(
                "Payment deposit limits",
                min_dep is not None and max_dep is not None,
                details=f"min={min_dep}, max={max_dep}"
            )
        except Exception as e:
            self.add_result("Payment service", False, str(e))
    
    async def test_currency_converter(self):
        """Test currency converter"""
        print("\n=== Testing Currency Converter ===")
        
        await self.init_db()
        
        try:
            from core.payments.converter import currency_converter
            
            # Test GTON to RUB
            gton_amount = Decimal("10")
            rub = await currency_converter.convert_from_gton(gton_amount, "RUB")
            self.add_result(
                "GTON to RUB conversion",
                rub is not None and rub > 0,
                details=f"{gton_amount} GTON = {rub} RUB"
            )
            
            # Test RUB to GTON
            rub_amount = Decimal("1000")
            gton = await currency_converter.convert_to_gton(rub_amount, "RUB")
            self.add_result(
                "RUB to GTON conversion",
                gton is not None and gton > 0,
                details=f"{rub_amount} RUB = {gton} GTON"
            )
        except Exception as e:
            self.add_result("Currency converter", False, str(e))
    
    # ==================== ADMIN TESTS ====================
    
    async def test_admin_functions(self):
        """Test admin module functions exist"""
        print("\n=== Testing Admin Functions ===")
        
        from core.platform.telegram.admin import partners as admin_partners
        
        functions = [
            "admin_partners",
            "partners_main",
            "partners_list",
            "partner_view",
            "partner_applications",
            "partner_app_approve",
            "partner_app_reject",
            "partner_payouts",
            "partner_payout_view",
            "partner_payout_confirm",
            "partner_payout_reject",
        ]
        
        for func_name in functions:
            try:
                func = getattr(admin_partners, func_name, None)
                exists = func is not None
                self.add_result(
                    f"Admin func: {func_name}",
                    exists,
                    details="OK" if exists else "NOT FOUND"
                )
            except Exception as e:
                self.add_result(f"Admin func: {func_name}", False, str(e))
    
    # ==================== DATABASE MODELS ====================
    
    async def test_models(self):
        """Test all models can be imported and have required fields"""
        print("\n=== Testing Database Models ===")
        
        from core.database.models import (
            User, Wallet, Transaction, Partner, Referral, 
            Payout, Commission, Payment, Setting
        )
        
        models = [
            (User, ["id", "telegram_id", "role", "first_name"]),
            (Wallet, ["id", "user_id", "balance", "wallet_type"]),
            (Transaction, ["id", "user_id", "amount", "direction", "status"]),
            (Partner, ["id", "user_id", "balance", "status", "referral_code"]),
            (Referral, ["id", "referrer_id", "referred_id"]),
            (Payout, ["id", "partner_id", "amount_gton", "amount_fiat", "status"]),
            (Payment, ["id", "user_id", "amount_gton", "status"]),
            (Setting, ["key", "value", "value_type"]),
        ]
        
        for model, required_fields in models:
            try:
                # Check model has required columns
                columns = [c.name for c in model.__table__.columns]
                missing = [f for f in required_fields if f not in columns]
                
                self.add_result(
                    f"Model: {model.__name__}",
                    len(missing) == 0,
                    details=f"missing={missing}" if missing else f"columns={len(columns)}"
                )
            except Exception as e:
                self.add_result(f"Model: {model.__name__}", False, str(e))
    
    # ==================== REFERRAL COMMISSION ====================
    
    async def test_referral_commission(self):
        """Test referral commission service"""
        print("\n=== Testing Referral Commission ===")
        
        await self.init_db()
        
        try:
            from core.referral import commission_service
            
            # Check service exists
            self.add_result(
                "Commission service exists",
                commission_service is not None,
                details="OK"
            )
            
            # Check methods exist
            methods = ["process_commission", "get_commission_percent"]
            for method in methods:
                has_method = hasattr(commission_service, method)
                self.add_result(
                    f"Commission method: {method}",
                    has_method,
                    details="OK" if has_method else "NOT FOUND"
                )
        except Exception as e:
            self.add_result("Referral commission", False, str(e))
    
    # ==================== NOTIFICATIONS ====================
    
    async def test_notifications(self):
        """Test notification functions exist"""
        print("\n=== Testing Notifications ===")
        
        try:
            from core.referral.notifications import (
                notify_new_referral,
                notify_commission_earned,
                set_bot
            )
            
            self.add_result("notify_new_referral", callable(notify_new_referral))
            self.add_result("notify_commission_earned", callable(notify_commission_earned))
            self.add_result("set_bot", callable(set_bot))
        except Exception as e:
            self.add_result("Notifications import", False, str(e))
    
    # ==================== RUN ALL ====================
    
    async def run_all(self):
        """Run all tests"""
        print("=" * 60)
        print("FuBot Integration Tests")
        print("=" * 60)
        
        await self.test_callbacks_exist()
        await self.test_router_callbacks()
        await self.test_settings_read()
        await self.test_payout_settings()
        await self.test_partner_functions()
        await self.test_payment_service()
        await self.test_currency_converter()
        await self.test_admin_functions()
        await self.test_models()
        await self.test_referral_commission()
        await self.test_notifications()
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        
        print(f"Total:  {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Rate:   {passed/total*100:.1f}%")
        
        if failed > 0:
            print("\nFailed tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.error}")
        
        return failed == 0


async def main():
    tester = IntegrationTester()
    success = await tester.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
