"""
Telegram Platform Test - Проверка всей структуры Telegram платформы

Проверяет:
1. Все хендлеры существуют и импортируются
2. Все callbacks роутятся правильно
3. Все кнопки меню имеют обработчики
4. Все локализации существуют
5. Структура админ-панели
6. Обработка состояний (FSM)

Запуск: python tests/test_telegram_platform.py
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import ast
import re

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test results
PASSED = []
FAILED = []
WARNINGS = []


def test_result(name: str, passed: bool, error: str = None):
    """Record test result"""
    if passed:
        PASSED.append(name)
        print(f"  [OK] {name}")
    else:
        FAILED.append((name, error))
        print(f"  [FAIL] {name}: {error}")


def warning(msg: str):
    """Record warning"""
    WARNINGS.append(msg)
    print(f"  [WARN] {msg}")


# ==================== 1. HANDLERS ====================

def test_01_handlers_exist():
    """Test all handler files exist"""
    handlers_dir = PROJECT_ROOT / "core" / "platform" / "telegram" / "handlers"
    
    required_handlers = [
        "__init__.py",
        "start.py",
        "messages.py",
        "settings.py",
        "topup.py",
        "partner.py",
        "daily_bonus.py",
        "promocode.py",
        "help.py",
        "service.py",
    ]
    
    missing = []
    for handler in required_handlers:
        if not (handlers_dir / handler).exists():
            missing.append(handler)
    
    if missing:
        test_result("Handler files", False, f"Missing: {missing}")
    else:
        test_result(f"Handler files ({len(required_handlers)} files)", True)


def test_02_handlers_import():
    """Test all handlers can be imported"""
    try:
        from core.platform.telegram.handlers import (
            start_command,
            main_menu_callback,
            settings_callback,
            language_callback,
            set_language_callback,
            topup_callback,
            partner_callback,
            daily_bonus_callback,
            help_command,
            help_callback,
            service_callback,
            message_handler,
        )
        test_result("Handler imports (12 functions)", True)
    except ImportError as e:
        test_result("Handler imports", False, str(e))


def test_03_admin_handlers_exist():
    """Test admin handler files exist"""
    admin_dir = PROJECT_ROOT / "core" / "platform" / "telegram" / "admin"
    
    required_admin = [
        "__init__.py",
        "main.py",
        "users.py",
        "stats.py",
        "partners.py",
        "settings.py",
        "broadcast.py",
        "moderation.py",
        "promocodes.py",
        "services.py",
        "languages.py",
    ]
    
    missing = []
    for handler in required_admin:
        if not (admin_dir / handler).exists():
            missing.append(handler)
    
    if missing:
        test_result("Admin files", False, f"Missing: {missing}")
    else:
        test_result(f"Admin files ({len(required_admin)} files)", True)


def test_04_admin_import():
    """Test admin handlers can be imported"""
    try:
        from core.platform.telegram.admin import admin_callback
        from core.platform.telegram.admin.main import (
            admin_callback,
            admin_main,
        )
        from core.platform.telegram.admin.users import admin_users
        from core.platform.telegram.admin.stats import admin_stats
        from core.platform.telegram.admin.partners import admin_partners
        from core.platform.telegram.admin.settings import admin_settings
        from core.platform.telegram.admin.broadcast import admin_broadcast
        from core.platform.telegram.admin.moderation import admin_moderation
        from core.platform.telegram.admin.promocodes import admin_promocodes
        from core.platform.telegram.admin.services import admin_services
        from core.platform.telegram.admin.languages import admin_languages
        
        test_result("Admin imports (11 modules)", True)
    except ImportError as e:
        test_result("Admin imports", False, str(e))


# ==================== 2. ROUTER ====================

def test_05_router_callbacks():
    """Test router handles all required callbacks"""
    router_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "router.py"
    
    with open(router_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_callbacks = [
        "main_menu",
        "settings",
        "settings:language",
        "settings:notifications",
        "set_language:",
        "help",
        "top_up",
        "promocode",
        "partner",
        "daily_bonus",
        "admin",
        "service:",
    ]
    
    missing = []
    for callback in required_callbacks:
        # Check if callback is handled in router
        if callback not in content:
            missing.append(callback)
    
    if missing:
        test_result("Router callbacks", False, f"Missing: {missing}")
    else:
        test_result(f"Router callbacks ({len(required_callbacks)} routes)", True)


# ==================== 3. MAIN MENU ====================

def test_06_main_menu_buttons():
    """Test main menu has all required buttons"""
    menu_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "keyboards" / "main_menu.py"
    
    with open(menu_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_buttons = [
        ("daily_bonus", "MAIN_MENU.daily_bonus"),
        ("top_up", "MAIN_MENU.top_up"),
        ("promocode", "MAIN_MENU.promocode"),
        ("partner", "MAIN_MENU.partner"),
        ("settings", "MAIN_MENU.settings"),
        ("help", "MAIN_MENU.help"),
    ]
    
    missing = []
    for callback, locale_key in required_buttons:
        if f'callback="{callback}"' not in content:
            missing.append(callback)
    
    if missing:
        test_result("Main menu buttons", False, f"Missing: {missing}")
    else:
        test_result(f"Main menu buttons ({len(required_buttons)} buttons)", True)


# ==================== 4. LOCALIZATION ====================

def test_07_localization_keys():
    """Test all required localization keys exist"""
    ru_file = PROJECT_ROOT / "core" / "locales" / "ru.py"
    
    with open(ru_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_keys = [
        # Main menu
        "MAIN_MENU",
        '"title"',
        '"balance"',
        '"top_up"',
        '"promocode"',
        '"settings"',
        '"help"',
        '"partner"',
        '"daily_bonus"',
        
        # Settings
        "SETTINGS",
        '"language"',
        '"notifications"',
        
        # Partner
        "PARTNER",
        
        # Top up
        "TOP_UP",
        
        # Help
        "HELP",
        
        # Promocode
        "PROMOCODE",
        
        # Daily bonus
        "DAILY_BONUS",
        
        # Admin
        "ADMIN",
        
        # Common
        "COMMON",
        '"back"',
        '"cancel"',
    ]
    
    missing = []
    for key in required_keys:
        if key not in content:
            missing.append(key)
    
    if missing:
        test_result("Localization keys", False, f"Missing: {missing}")
    else:
        test_result(f"Localization keys ({len(required_keys)} keys)", True)


# ==================== 5. PARTNER MENU ====================

def test_08_partner_callbacks():
    """Test partner handler has all sub-actions"""
    partner_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "handlers" / "partner.py"
    
    with open(partner_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_actions = [
        "partner_main",
        "partner_cabinet",
        "partner_referrals",
        "partner_apply",
        "partner_stats",
        "partner_payout",
        "partner_payout_method",
        "partner_payout_history",
        "partner_payout_confirm",
        "partner_payout_cancel",
    ]
    
    missing = []
    for action in required_actions:
        if f"async def {action}" not in content:
            missing.append(action)
    
    if missing:
        test_result("Partner functions", False, f"Missing: {missing}")
    else:
        test_result(f"Partner functions ({len(required_actions)} functions)", True)


# ==================== 6. ADMIN MENU ====================

def test_09_admin_menu_structure():
    """Test admin menu has all sections"""
    admin_main_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "admin" / "main.py"
    
    with open(admin_main_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_sections = [
        "admin:stats",
        "admin:users",
        "admin:partners",
        "admin:moderation",
        "admin:promocodes",
        "admin:services",
        "admin:broadcast",
        "admin:settings",
        "admin:languages",
    ]
    
    missing = []
    for section in required_sections:
        if section not in content:
            missing.append(section)
    
    if missing:
        test_result("Admin menu sections", False, f"Missing: {missing}")
    else:
        test_result(f"Admin menu sections ({len(required_sections)} sections)", True)


def test_10_admin_routing():
    """Test admin router handles all actions"""
    admin_main_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "admin" / "main.py"
    
    with open(admin_main_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_routes = [
        'action == "stats"',
        'action == "users"',
        'action == "partners"',
        'action == "services"',
        'action == "settings"',
        'action == "languages"',
        'action == "broadcast"',
        'action == "moderation"',
        'action == "promocodes"',
    ]
    
    missing = []
    for route in required_routes:
        if route not in content:
            missing.append(route)
    
    if missing:
        test_result("Admin routing", False, f"Missing: {missing}")
    else:
        test_result(f"Admin routing ({len(required_routes)} routes)", True)


# ==================== 7. MESSAGE HANDLER ====================

def test_11_message_states():
    """Test message handler handles all states"""
    messages_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "handlers" / "messages.py"
    
    with open(messages_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_states = [
        "promocode_input",
        "partner_payout_card",
        "partner_payout_sbp",
    ]
    
    missing = []
    for state in required_states:
        if state not in content:
            missing.append(state)
    
    if missing:
        test_result("Message states", False, f"Missing: {missing}")
    else:
        test_result(f"Message states ({len(required_states)} states)", True)


# ==================== 8. DAILY BONUS ====================

def test_12_daily_bonus_flow():
    """Test daily bonus handler"""
    bonus_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "handlers" / "daily_bonus.py"
    
    with open(bonus_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_functions = [
        "daily_bonus_callback",
        "claim_bonus",
        "DEFAULT_REWARDS",
    ]
    
    missing = []
    for func in required_functions:
        if func not in content:
            missing.append(func)
    
    if missing:
        test_result("Daily bonus", False, f"Missing: {missing}")
    else:
        test_result(f"Daily bonus ({len(required_functions)} items)", True)


# ==================== 9. PROMOCODE ====================

def test_13_promocode_flow():
    """Test promocode handler"""
    promo_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "handlers" / "promocode.py"
    
    with open(promo_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_functions = [
        "promocode_callback",
        "handle_promocode_input",
        "activate_promocode",
        "set_promocode_state",
        "clear_promocode_state",
    ]
    
    missing = []
    for func in required_functions:
        if func not in content:
            missing.append(func)
    
    if missing:
        test_result("Promocode", False, f"Missing: {missing}")
    else:
        test_result(f"Promocode ({len(required_functions)} functions)", True)


# ==================== 10. SETTINGS ====================

def test_14_settings_flow():
    """Test settings handler"""
    settings_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "handlers" / "settings.py"
    
    with open(settings_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_functions = [
        "settings_callback",
        "language_callback",
        "set_language_callback",
        "notifications_callback",
    ]
    
    missing = []
    for func in required_functions:
        if f"async def {func}" not in content:
            missing.append(func)
    
    if missing:
        test_result("Settings", False, f"Missing: {missing}")
    else:
        test_result(f"Settings ({len(required_functions)} functions)", True)


# ==================== 11. TOPUP ====================

def test_15_topup_flow():
    """Test topup handler"""
    topup_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "handlers" / "topup.py"
    
    with open(topup_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_items = [
        "topup_callback",
        "top_up:100",
        "top_up:500",
        "top_up:1000",
        "GTON",
    ]
    
    missing = []
    for item in required_items:
        if item not in content:
            missing.append(item)
    
    if missing:
        test_result("Topup", False, f"Missing: {missing}")
    else:
        test_result(f"Topup ({len(required_items)} items)", True)


# ==================== 12. START & REFERRAL ====================

def test_16_start_referral():
    """Test start handler with referral processing"""
    start_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "handlers" / "start.py"
    
    with open(start_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_items = [
        "start_command",
        "main_menu_callback",
        "process_referral",
        "ref_",
        "partner_",
    ]
    
    missing = []
    for item in required_items:
        if item not in content:
            missing.append(item)
    
    if missing:
        test_result("Start & Referral", False, f"Missing: {missing}")
    else:
        test_result(f"Start & Referral ({len(required_items)} items)", True)


# ==================== 13. UTILS ====================

def test_17_utils():
    """Test utils functions exist"""
    utils_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "utils.py"
    
    with open(utils_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_functions = [
        "get_or_create_user",
        "get_user_language",
        "get_user_balance_with_fiat",
        "format_gton",
        "build_keyboard",
    ]
    
    missing = []
    for func in required_functions:
        if func not in content:
            missing.append(func)
    
    if missing:
        test_result("Utils", False, f"Missing: {missing}")
    else:
        test_result(f"Utils ({len(required_functions)} functions)", True)


# ==================== 14. CALLBACK COVERAGE ====================

def test_18_callback_coverage():
    """Test all menu callbacks have handlers"""
    
    # All callbacks from menus
    all_callbacks = {
        # Main menu
        "main_menu": "router.py",
        "daily_bonus": "router.py",
        "top_up": "router.py",
        "promocode": "router.py",
        "partner": "router.py",
        "settings": "router.py",
        "help": "router.py",
        "admin": "router.py",
        
        # Settings submenu
        "settings:language": "router.py",
        "settings:notifications": "router.py",
        
        # Partner submenu
        "partner:referrals": "partner.py",
        "partner:apply": "partner.py",
        "partner:stats": "partner.py",
        "partner:payout": "partner.py",
        "partner:cabinet": "partner.py",
        
        # Daily bonus
        "daily_bonus:claim": "daily_bonus.py",
        
        # Promocode
        "promocode:cancel": "promocode.py",
    }
    
    router_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "router.py"
    partner_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "handlers" / "partner.py"
    bonus_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "handlers" / "daily_bonus.py"
    promo_file = PROJECT_ROOT / "core" / "platform" / "telegram" / "handlers" / "promocode.py"
    
    with open(router_file, "r", encoding="utf-8") as f:
        router_content = f.read()
    with open(partner_file, "r", encoding="utf-8") as f:
        partner_content = f.read()
    with open(bonus_file, "r", encoding="utf-8") as f:
        bonus_content = f.read()
    with open(promo_file, "r", encoding="utf-8") as f:
        promo_content = f.read()
    
    missing = []
    for callback, handler_file in all_callbacks.items():
        if handler_file == "router.py":
            # Check main callback prefix in router
            prefix = callback.split(":")[0]
            if prefix not in router_content:
                missing.append(callback)
        elif handler_file == "partner.py":
            action = callback.split(":")[1] if ":" in callback else callback
            if action not in partner_content:
                missing.append(callback)
        elif handler_file == "daily_bonus.py":
            if "claim" not in bonus_content:
                missing.append(callback)
        elif handler_file == "promocode.py":
            if "cancel" not in promo_content:
                missing.append(callback)
    
    if missing:
        test_result("Callback coverage", False, f"Missing handlers: {missing}")
    else:
        test_result(f"Callback coverage ({len(all_callbacks)} callbacks)", True)


# ==================== 15. ADMIN SUBMENUS ====================

def test_19_admin_submenus():
    """Test admin submenus exist"""
    
    admin_files = {
        "users.py": ["view_user", "user_balance", "user_transactions"],
        "stats.py": ["stats_main", "stats_finance", "stats_users"],
        "partners.py": ["partners_main", "partner_view", "partner_payouts"],
        "broadcast.py": ["broadcast_main", "broadcast_view"],
        "moderation.py": ["moderation_main", "user_warnings"],
        "promocodes.py": ["promocodes_main", "view_promocode"],
    }
    
    admin_dir = PROJECT_ROOT / "core" / "platform" / "telegram" / "admin"
    
    missing = []
    for filename, functions in admin_files.items():
        filepath = admin_dir / filename
        if not filepath.exists():
            missing.append(f"{filename} (file)")
            continue
            
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        for func in functions:
            if func not in content:
                missing.append(f"{filename}:{func}")
    
    if missing:
        test_result("Admin submenus", False, f"Missing: {missing}")
    else:
        total = sum(len(funcs) for funcs in admin_files.values())
        test_result(f"Admin submenus ({total} functions)", True)


# ==================== SUMMARY ====================

def print_menu_structure():
    """Print full menu structure"""
    print("\n" + "="*60)
    print("TELEGRAM MENU STRUCTURE")
    print("="*60)
    
    structure = """
/start
  |
  +-- Main Menu
      |
      +-- Daily Bonus [daily_bonus]
      |     +-- Claim [daily_bonus:claim]
      |
      +-- Top Up [top_up]
      |     +-- 100 RUB [top_up:100]
      |     +-- 500 RUB [top_up:500]
      |     +-- 1000 RUB [top_up:1000]
      |     +-- Promocode [promocode]
      |
      +-- Promocode [promocode]
      |     +-- Cancel [promocode:cancel]
      |
      +-- Partner [partner]
      |     +-- (Regular user)
      |     |     +-- My Referrals [partner:referrals]
      |     |     +-- Become Partner [partner:apply]
      |     |
      |     +-- (Partner)
      |           +-- Cabinet [partner:cabinet]
      |           +-- Stats [partner:stats]
      |           +-- Payout [partner:payout]
      |                 +-- Card [partner:payout:card]
      |                 +-- SBP [partner:payout:sbp]
      |                 +-- History [partner:payout:history]
      |
      +-- Settings [settings]
      |     +-- Language [settings:language]
      |     +-- Notifications [settings:notifications]
      |
      +-- Help [help]
      |
      +-- Admin Panel [admin] (admins only)
            +-- Stats [admin:stats]
            +-- Users [admin:users]
            +-- Partners [admin:partners]
            +-- Moderation [admin:moderation]
            +-- Promocodes [admin:promocodes]
            +-- Services [admin:services]
            +-- Broadcast [admin:broadcast]
            +-- Settings [admin:settings]
            +-- Languages [admin:languages]
"""
    print(structure)


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("Telegram Platform Test Suite")
    print("="*60 + "\n")
    
    print("[*] Testing handlers...\n")
    test_01_handlers_exist()
    test_02_handlers_import()
    test_03_admin_handlers_exist()
    test_04_admin_import()
    
    print("\n[*] Testing router...\n")
    test_05_router_callbacks()
    
    print("\n[*] Testing menus...\n")
    test_06_main_menu_buttons()
    test_08_partner_callbacks()
    test_09_admin_menu_structure()
    test_10_admin_routing()
    
    print("\n[*] Testing localization...\n")
    test_07_localization_keys()
    
    print("\n[*] Testing handlers flow...\n")
    test_11_message_states()
    test_12_daily_bonus_flow()
    test_13_promocode_flow()
    test_14_settings_flow()
    test_15_topup_flow()
    test_16_start_referral()
    test_17_utils()
    
    print("\n[*] Testing coverage...\n")
    test_18_callback_coverage()
    test_19_admin_submenus()
    
    # Print menu structure
    print_menu_structure()
    
    # Summary
    print("="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"\nPassed: {len(PASSED)}")
    print(f"Failed: {len(FAILED)}")
    print(f"Warnings: {len(WARNINGS)}")
    
    if FAILED:
        print("\nFailed tests:")
        for name, error in FAILED:
            print(f"   - {name}: {error}")
    
    if WARNINGS:
        print("\nWarnings:")
        for warn in WARNINGS:
            print(f"   - {warn}")
    
    print("\n" + "="*60)
    if not FAILED:
        print("ALL TESTS PASSED!")
    else:
        print(f"{len(FAILED)} test(s) failed")
    print("="*60 + "\n")
    
    return len(FAILED) == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
