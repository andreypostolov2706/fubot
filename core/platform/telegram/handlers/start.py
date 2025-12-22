"""
Start Handler
"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from sqlalchemy import select

from core.locales import t
from core.locales.user_texts import USER_TEXTS
from core.database import get_db
from core.platform.telegram.utils import (
    get_or_create_user, 
    get_user_language, 
    get_user_balance_with_fiat,
    format_gton,
    is_admin,
)
from core.platform.telegram.keyboards import main_menu_kb


async def get_daily_horoscope_info(user_id: int) -> tuple[bool, int]:
    """Получить статус подписки и цену ежедневного гороскопа"""
    try:
        async with get_db() as session:
            # Получаем статус подписки
            from services.astrology.models import UserAstrologyProfile
            result = await session.execute(
                select(UserAstrologyProfile.daily_horoscope_enabled)
                .where(UserAstrologyProfile.user_id == user_id)
            )
            enabled = result.scalar_one_or_none()
            daily_enabled = enabled if enabled is not None else False
            
            # Получаем цену подписки
            from core.database.models import Service
            result = await session.execute(
                select(Service.config).where(Service.id == "astrology")
            )
            config = result.scalar_one_or_none()
            daily_price = 0
            if config and isinstance(config, dict):
                prices = config.get("prices", {})
                daily_price = prices.get("daily", 5)
            
            return daily_enabled, daily_price
    except Exception as e:
        logger.error(f"Error getting daily horoscope info: {e}")
        return False, 5


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    lang = await get_user_language(user_id)
    
    # Check for referral code
    if context.args:
        ref_code = context.args[0]
        await process_referral(user_id, ref_code)
    
    # Build menu with GTON balance and fiat equivalent
    gton, fiat = await get_user_balance_with_fiat(user_id)
    
    # Получаем информацию о подписке на ежедневный гороскоп
    daily_enabled, daily_price = await get_daily_horoscope_info(user_id)
    daily_status = "✅ включена" if daily_enabled else "❌ выключена"
    
    # Используем тексты из user_texts.py
    text = USER_TEXTS["main_menu"]["title"] + "\n"
    text += USER_TEXTS["main_menu"]["description"].format(
        daily_status=daily_status,
        daily_price=daily_price
    ) + "\n"
    
    if fiat is not None:
        fiat_str = f"{fiat:,.0f}".replace(",", " ")
        text += USER_TEXTS["main_menu"]["balance_with_fiat"].format(balance=format_gton(gton), fiat=fiat_str)
    else:
        text += USER_TEXTS["main_menu"]["balance"].format(balance=format_gton(gton))
    
    keyboard = await main_menu_kb(user_id, lang)
    
    await update.message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main_menu callback"""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    lang = await get_user_language(user_id)
    
    # Build menu with GTON balance and fiat equivalent
    gton, fiat = await get_user_balance_with_fiat(user_id)
    
    # Получаем информацию о подписке на ежедневный гороскоп
    daily_enabled, daily_price = await get_daily_horoscope_info(user_id)
    daily_status = "✅ включена" if daily_enabled else "❌ выключена"
    
    # Используем тексты из user_texts.py
    text = USER_TEXTS["main_menu"]["title"] + "\n"
    text += USER_TEXTS["main_menu"]["description"].format(
        daily_status=daily_status,
        daily_price=daily_price
    ) + "\n"
    
    if fiat is not None:
        fiat_str = f"{fiat:,.0f}".replace(",", " ")
        text += USER_TEXTS["main_menu"]["balance_with_fiat"].format(balance=format_gton(gton), fiat=fiat_str)
    else:
        text += USER_TEXTS["main_menu"]["balance"].format(balance=format_gton(gton))
    
    keyboard = await main_menu_kb(user_id, lang)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def process_referral(user_id: int, ref_code: str) -> bool:
    """
    Process referral code and create referral relationship.
    
    Supports:
    - ref_XXXXX — regular user referral (User.referral_code)
    - partner_XXXXX — partner referral (Partner.referral_code)
    
    Returns:
        True if referral was created, False otherwise
    """
    from sqlalchemy import select
    from core.database.models import User, Partner, Referral
    
    # Parse referral code
    if ref_code.startswith("ref_"):
        code = ref_code[4:]  # Remove "ref_" prefix
        is_partner = False
    elif ref_code.startswith("partner_"):
        code = ref_code[8:]  # Remove "partner_" prefix
        is_partner = True
    else:
        # Unknown format
        return False
    
    async with get_db() as session:
        # Check if user already has a referrer
        result = await session.execute(
            select(Referral).where(Referral.referred_id == user_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # User already has a referrer
            logger.debug(f"User {user_id} already has referrer {existing.referrer_id}")
            return False
        
        referrer_id = None
        partner_id = None
        
        if is_partner:
            # Find partner by referral code
            result = await session.execute(
                select(Partner).where(
                    Partner.referral_code == code,
                    Partner.status == "active"
                )
            )
            partner = result.scalar_one_or_none()
            
            if partner:
                referrer_id = partner.user_id
                partner_id = partner.id
                
                # Update partner stats
                partner.total_referrals = (partner.total_referrals or 0) + 1
        else:
            # Find user by referral code
            result = await session.execute(
                select(User).where(User.referral_code == code)
            )
            referrer = result.scalar_one_or_none()
            
            if referrer:
                referrer_id = referrer.id
        
        if not referrer_id:
            logger.warning(f"Referrer not found for code: {ref_code}")
            return False
        
        # Don't allow self-referral
        if referrer_id == user_id:
            logger.warning(f"Self-referral attempt: user {user_id}")
            return False
        
        # Create referral relationship
        referral = Referral(
            referrer_id=referrer_id,
            referred_id=user_id,
            partner_id=partner_id,
            level=1,
            is_active=True
        )
        session.add(referral)
        
        # Get referred user info for notification
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        referred_user = result.scalar_one_or_none()
        
        logger.info(
            f"Referral created: referrer={referrer_id}, referred={user_id}, "
            f"partner_id={partner_id}, code={ref_code}"
        )
    
    # Send notification to referrer (outside of session)
    try:
        from core.referral.notifications import notify_new_referral
        
        referred_info = {
            "username": referred_user.username if referred_user else None,
            "first_name": referred_user.first_name if referred_user else None,
        }
        await notify_new_referral(referrer_id, referred_info, is_partner=is_partner)
    except Exception as e:
        logger.error(f"Failed to send referral notification: {e}")
    
    return True


async def get_service_prices_rub() -> dict:
    """
    Получить полную информацию о ценах сервисов для админа.
    Включает: закупка (USD), с маржой (USD), GTON, TON, RUB.
    Маржа берётся из конфига каждого сервиса в БД.
    """
    from decimal import Decimal
    from core.payments.converter import currency_converter
    from core.database import get_db
    from core.database.models import Service
    from sqlalchemy import select
    
    # Базовые цены закупки в USD (себестоимость)
    service_configs = {
        "nano_banano": {"cost": 0.04, "default_margin": 0.3},
        "gpt_image": {"cost": 0.007, "default_margin": 0.3},
        "veo": {"cost": 2.50, "default_margin": 0.3},
        "kling": {"cost": 0.35, "default_margin": 0.3},
    }
    
    prices = {}
    
    try:
        # Получаем курс USD/RUB для конвертации закупки
        from core.payments.rates import rates_manager
        usd_rub_rate = await rates_manager.get_rate("USD", "RUB")
        if not usd_rub_rate:
            usd_rub_rate = Decimal("100")  # fallback
        
        # Получаем маржу из БД для каждого сервиса
        async with get_db() as session:
            for service_id, config in service_configs.items():
                cost_usd = config["cost"]
                margin = config["default_margin"]
                
                # Пробуем получить маржу из БД
                result = await session.execute(
                    select(Service.config).where(Service.id == service_id)
                )
                db_config = result.scalar_one_or_none()
                if db_config and isinstance(db_config, dict):
                    margin = db_config.get("margin_multiplier", margin)
                
                # Цена с маржой в USD
                price_usd = cost_usd * (1 + margin)
                
                # Закупка в рублях
                cost_rub = float(Decimal(str(cost_usd)) * usd_rub_rate)
                
                # Конвертация USD -> GTON (возвращает ConversionResult)
                conv_result = await currency_converter.convert_to_gton(Decimal(str(price_usd)), "USD")
                if conv_result.success:
                    gton_float = float(conv_result.gton_amount)
                    ton_float = float(conv_result.ton_amount)
                else:
                    gton_float = 0
                    ton_float = 0
                
                # Конвертация GTON -> RUB
                rub = await currency_converter.convert_from_gton(Decimal(str(gton_float)), "RUB")
                rub_float = float(rub) if rub else 0
                
                # Заполняем все поля
                prices[f"{service_id}_cost"] = f"{cost_usd:.3f}"
                prices[f"{service_id}_cost_rub"] = f"{cost_rub:.2f}"
                prices[f"{service_id}_margin"] = f"{int(margin * 100)}"
                prices[f"{service_id}_usd"] = f"{price_usd:.3f}"
                prices[f"{service_id}_gton"] = f"{gton_float:.4f}"
                prices[f"{service_id}_ton"] = f"{ton_float:.6f}"
                prices[f"{service_id}_rub"] = f"{rub_float:.2f}"
            
    except Exception as e:
        logger.error(f"Error calculating prices: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Fallback - примерные значения
        for service in ["nano_banano", "gpt_image", "veo", "kling"]:
            prices[f"{service}_cost"] = "0.00"
            prices[f"{service}_cost_rub"] = "0.00"
            prices[f"{service}_margin"] = "0"
            prices[f"{service}_usd"] = "0.00"
            prices[f"{service}_gton"] = "0.00"
            prices[f"{service}_ton"] = "0.00"
            prices[f"{service}_rub"] = "0.00"
    
    return prices
