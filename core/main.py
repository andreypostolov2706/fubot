"""
FuBot Core - Main Entry Point
"""
import asyncio
import signal
import sys

from loguru import logger

from core.config import config
from core.database import db_manager, get_db
from core.database.models import *  # Import all models
from core.plugins.registry import service_registry
from core.platform.telegram import telegram_bot
from core.tasks import process_triggers, set_trigger_bot, update_rates_task, init_rates, payment_checker_task, set_payment_bot


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    level=config.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    "logs/fubot_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)


async def init_default_settings():
    """Initialize default settings"""
    from core.database import get_db
    from core.database.models import Setting
    
    DEFAULT_SETTINGS = {
        # General
        ("general.bot_name", "FuBot", "string", "general", "Bot name"),
        ("general.support_username", "@support", "string", "general", "Support username"),
        ("general.default_language", "ru", "string", "general", "Default language"),
        
        # Payments & GTON
        ("payments.gton_ton_rate", "1.530000", "string", "payments", "1 GTON = X TON"),
        ("payments.fiat_rates_ttl", "86400", "int", "payments", "Fiat rates TTL (seconds)"),
        ("payments.crypto_rates_ttl", "600", "int", "payments", "Crypto rates TTL (seconds)"),
        ("payments.min_deposit_gton", "1.000000", "string", "payments", "Minimum deposit in GTON"),
        ("payments.max_deposit_gton", "100000.000000", "string", "payments", "Maximum deposit in GTON"),
        ("payments.fee_percent", "0.00", "string", "payments", "Global fee percent"),
        ("payments.payment_timeout_minutes", "30", "int", "payments", "Payment timeout"),
        ("payments.welcome_bonus_gton", "0.000000", "string", "payments", "Welcome bonus in GTON"),
        
        # Referral & Commissions
        ("referral.enabled", "true", "bool", "referral", "Referral enabled"),
        ("referral.commission_enabled", "true", "bool", "referral", "Auto commission on deduct"),
        ("referral.level1_percent", "10", "float", "referral", "Level 1 commission % (regular)"),
        ("referral.partner_level1_percent", "20", "float", "referral", "Level 1 commission % (partner)"),
        ("referral.level2_enabled", "false", "bool", "referral", "Level 2 enabled"),
        ("referral.level2_percent", "5", "float", "referral", "Level 2 commission %"),
        
        # Payout settings (GTON)
        ("payout.min_gton", "5.0", "string", "payout", "Minimum payout in GTON"),
        ("payout.fee_percent", "0", "string", "payout", "Payout fee %"),
        ("payout.methods", '["card", "sbp"]', "json", "payout", "Enabled payout methods"),
        
        # Daily Bonus (in GTON)
        ("daily_bonus.enabled", "true", "bool", "daily_bonus", "Daily bonus enabled"),
        ("daily_bonus.rewards", "[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 5.0]", "json", "daily_bonus", "Rewards by day (GTON)"),
        
        # Moderation
        ("moderation.warnings_before_ban", "3", "int", "moderation", "Warnings before auto-ban"),
        ("moderation.auto_ban_duration_days", "7", "int", "moderation", "Auto-ban duration"),
        
        # Localization
        ("localization.default_language", "ru", "string", "localization", "Default language"),
        ("localization.enabled_languages", '["ru", "en"]', "json", "localization", "Enabled languages"),
        
        # Notifications (short keys to fit 64 byte callback limit)
        ("notif.new_users", "true", "bool", "notifications", "Notify on new users"),
        ("notif.payments", "true", "bool", "notifications", "Notify on payments"),
        ("notif.errors", "true", "bool", "notifications", "Notify on errors"),
        ("notif.channel", "", "string", "notifications", "Notification channel ID"),
        ("notif.quiet_start", "23", "int", "notifications", "Quiet hours start"),
        ("notif.quiet_end", "8", "int", "notifications", "Quiet hours end"),
    }
    
    async with get_db() as session:
        from sqlalchemy import select
        
        for key, value, value_type, category, description in DEFAULT_SETTINGS:
            result = await session.execute(
                select(Setting).where(Setting.key == key)
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                setting = Setting(
                    key=key,
                    value=value,
                    value_type=value_type,
                    category=category,
                    description=description
                )
                session.add(setting)
                logger.debug(f"Created setting: {key}")
    
    logger.info("Default settings initialized")


async def init_default_triggers():
    """Initialize default broadcast triggers"""
    from core.database import get_db
    from core.database.models import BroadcastTrigger, User
    from sqlalchemy import select, func
    
    # Get admin user id (first user or id=1)
    async with get_db() as session:
        result = await session.execute(select(User.id).limit(1))
        admin_id = result.scalar() or 1
    
    DEFAULT_TRIGGERS = [
        {
            "name": "Низкий баланс",
            "trigger_type": "low_balance",
            "text": "💰 Привет, {name}!\n\nТвой баланс: {balance}₽\n\nПополни баланс, чтобы продолжить пользоваться сервисом!",
            "conditions": {"balance_less_than": 100},
            "is_active": False,
        },
        {
            "name": "Истекает подписка",
            "trigger_type": "subscription_expiring",
            "text": "⏰ {name}, твоя подписка истекает через {days} дней!\n\nПродли подписку, чтобы не потерять доступ.",
            "conditions": {"days_before_expiry": 3},
            "is_active": False,
        },
        {
            "name": "Подписка истекла",
            "trigger_type": "subscription_expired",
            "text": "⭐ {name}, твоя подписка закончилась!\n\nВозобнови подписку, чтобы вернуть доступ ко всем функциям.",
            "conditions": {"hours_after_expiry": 1},
            "is_active": False,
        },
        {
            "name": "Неактивность 7 дней",
            "trigger_type": "inactive",
            "text": "😴 Привет, {name}!\n\nМы заметили, что тебя не было {days} дней.\n\nЗаходи — у нас много интересного!",
            "conditions": {"inactive_days": 7, "exclude_new_users_days": 3},
            "is_active": False,
        },
        {
            "name": "Приветствие",
            "trigger_type": "welcome",
            "text": "🆕 Привет, {name}!\n\nДобро пожаловать! Рады видеть тебя в нашем сервисе.\n\nЕсли есть вопросы — пиши в поддержку!",
            "conditions": {"hours_after_registration": 24, "only_if_inactive": True},
            "is_active": False,
        },
        {
            "name": "После пополнения",
            "trigger_type": "after_deposit",
            "text": "💳 Спасибо за пополнение на {amount}₽, {name}!\n\nТеперь ты можешь пользоваться всеми возможностями сервиса.",
            "conditions": {"min_amount": 0, "first_deposit_only": False},
            "is_active": False,
        },
    ]
    
    async with get_db() as session:
        # Check if triggers already exist
        result = await session.execute(select(func.count(BroadcastTrigger.id)))
        count = result.scalar()
        
        if count == 0:
            for trigger_data in DEFAULT_TRIGGERS:
                trigger = BroadcastTrigger(
                    name=trigger_data["name"],
                    trigger_type=trigger_data["trigger_type"],
                    text=trigger_data["text"],
                    conditions=trigger_data["conditions"],
                    is_active=trigger_data["is_active"],
                    created_by=admin_id,
                )
                session.add(trigger)
                logger.debug(f"Created trigger: {trigger_data['name']}")
            
            logger.info("Default triggers initialized")
        else:
            logger.debug(f"Triggers already exist: {count}")


async def sync_admin_roles():
    """Sync admin roles from config.ADMIN_IDS to database"""
    from core.database.models import User
    from sqlalchemy import select
    
    if not config.ADMIN_IDS:
        return
    
    async with get_db() as session:
        for admin_telegram_id in config.ADMIN_IDS:
            result = await session.execute(
                select(User).where(User.telegram_id == admin_telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user and user.role != "admin":
                user.role = "admin"
                logger.info(f"Set admin role for user {user.telegram_id} ({user.first_name})")
    
    logger.debug(f"Admin roles synced for {len(config.ADMIN_IDS)} users from ADMIN_IDS")


async def startup():
    """Application startup"""
    logger.info("=" * 50)
    logger.info("FuBot Core Starting...")
    logger.info("=" * 50)
    
    # Validate config
    if not config.validate():
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    # Initialize database
    await db_manager.init()
    await db_manager.create_tables()
    
    # Initialize default settings
    await init_default_settings()
    
    # Initialize default triggers
    await init_default_triggers()
    
    # Sync admin roles from ADMIN_IDS
    await sync_admin_roles()
    
    # Initialize service registry
    await service_registry.init()
    
    # Initialize Telegram bot
    await telegram_bot.init()
    
    # Initialize exchange rates
    await init_rates()
    
    logger.info("FuBot Core initialized successfully")


async def shutdown():
    """Application shutdown"""
    logger.info("Shutting down FuBot Core...")
    
    # Stop Telegram bot
    await telegram_bot.stop()
    
    # Close database
    await db_manager.close()
    
    logger.info("FuBot Core stopped")


async def main():
    """Main function"""
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    stop_event = asyncio.Event()
    
    def signal_handler():
        stop_event.set()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            signal.signal(sig, lambda s, f: signal_handler())
    
    try:
        # Startup
        await startup()
        
        # Start bot
        await telegram_bot.start()
        
        # Set bot for trigger processor
        set_trigger_bot(telegram_bot.application.bot)
        
        # Set bot for payment notifications
        set_payment_bot(telegram_bot.application.bot)
        
        # Set bot for referral/partner notifications
        from core.referral.notifications import set_bot as set_referral_bot
        set_referral_bot(telegram_bot.application.bot)
        
        # Start trigger processor as background task
        trigger_task = asyncio.create_task(process_triggers())
        
        # Start exchange rates updater as background task
        rates_task = asyncio.create_task(update_rates_task())
        
        # Start payment checker as background task
        payment_task = asyncio.create_task(payment_checker_task())
        
        # Start daily horoscope sender as background task
        horoscope_task = None
        try:
            from services.astrology.tasks import send_daily_horoscopes
            from core.plugins.core_api import CoreAPI
            core_api = CoreAPI("astrology")
            
            async def daily_horoscope_loop():
                while True:
                    try:
                        await send_daily_horoscopes(telegram_bot.application.bot, core_api)
                        await asyncio.sleep(60)  # Check every minute
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Error in daily horoscope task: {e}")
                        await asyncio.sleep(60)
            
            horoscope_task = asyncio.create_task(daily_horoscope_loop())
            logger.info("Daily horoscope task started")
        except Exception as e:
            logger.error(f"Failed to start daily horoscope task: {e}")
        
        logger.info("FuBot Core is running. Press Ctrl+C to stop.")
        
        # Wait for stop signal
        await stop_event.wait()
        
        # Cancel background tasks
        trigger_task.cancel()
        rates_task.cancel()
        payment_task.cancel()
        if horoscope_task:
            horoscope_task.cancel()
        
        try:
            await trigger_task
        except asyncio.CancelledError:
            pass
        try:
            await rates_task
        except asyncio.CancelledError:
            pass
        try:
            await payment_task
        except asyncio.CancelledError:
            pass
        if horoscope_task:
            try:
                await horoscope_task
            except asyncio.CancelledError:
                pass
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        # Shutdown
        await shutdown()


if __name__ == "__main__":
    asyncio.run(main())
