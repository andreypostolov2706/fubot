"""
Partner Notifications - Уведомления для партнёров и рефереров
"""
from decimal import Decimal
from loguru import logger

from core.database import get_db
from core.database.models import User
from sqlalchemy import select

# Bot instance for sending notifications
_bot = None


def set_bot(bot):
    """Set bot instance for notifications"""
    global _bot
    _bot = bot


async def notify_new_referral(referrer_id: int, referred_user: dict, is_partner: bool = False):
    """
    Notify referrer about new referral registration.
    
    Args:
        referrer_id: User ID of the referrer
        referred_user: Dict with referred user info (username, first_name)
        is_partner: Whether referrer is a partner
    """
    global _bot
    
    if not _bot:
        logger.warning("Bot not set, cannot send referral notification")
        return
    
    try:
        # Get referrer's telegram_id
        async with get_db() as session:
            result = await session.execute(
                select(User.telegram_id).where(User.id == referrer_id)
            )
            telegram_id = result.scalar_one_or_none()
        
        if not telegram_id:
            logger.warning(f"Telegram ID not found for referrer {referrer_id}")
            return
        
        # Format user info
        username = referred_user.get("username")
        first_name = referred_user.get("first_name", "Пользователь")
        
        if username:
            user_str = f"@{username}"
        else:
            user_str = first_name
        
        # Different messages for partner and regular referrer
        if is_partner:
            text = (
                f"🎉 <b>Новый реферал!</b>\n\n"
                f"👤 {user_str} зарегистрировался по вашей партнёрской ссылке.\n\n"
                f"Вы будете получать комиссию с его покупок! 💰"
            )
        else:
            text = (
                f"🎉 <b>Новый реферал!</b>\n\n"
                f"👤 {user_str} присоединился по вашей ссылке.\n\n"
                f"Вы будете получать 10% с его покупок! 💰"
            )
        
        await _bot.send_message(
            chat_id=telegram_id,
            text=text,
            parse_mode="HTML"
        )
        
        logger.info(f"New referral notification sent to user {referrer_id}")
        
    except Exception as e:
        logger.error(f"Failed to send referral notification: {e}")


async def notify_commission_earned(
    referrer_id: int, 
    commission_amount: Decimal,
    commission_percent: Decimal,
    referred_user_id: int,
    is_partner: bool = False
):
    """
    Notify referrer about commission earned.
    
    Args:
        referrer_id: User ID of the referrer
        commission_amount: Amount of commission in GTON
        commission_percent: Commission percentage
        referred_user_id: User ID who made the purchase
        is_partner: Whether referrer is a partner
    """
    global _bot
    
    if not _bot:
        logger.warning("Bot not set, cannot send commission notification")
        return
    
    try:
        # Get referrer's telegram_id and referred user info
        async with get_db() as session:
            # Referrer telegram_id
            result = await session.execute(
                select(User.telegram_id).where(User.id == referrer_id)
            )
            telegram_id = result.scalar_one_or_none()
            
            # Referred user info
            result = await session.execute(
                select(User.username, User.first_name).where(User.id == referred_user_id)
            )
            referred_info = result.one_or_none()
        
        if not telegram_id:
            logger.warning(f"Telegram ID not found for referrer {referrer_id}")
            return
        
        # Format user info
        if referred_info:
            username, first_name = referred_info
            if username:
                user_str = f"@{username}"
            else:
                user_str = first_name or "реферала"
        else:
            user_str = "реферала"
        
        # Format amount
        amount_str = f"{commission_amount:.4f}".rstrip('0').rstrip('.')
        
        # Get fiat equivalent
        from core.payments.converter import currency_converter
        fiat_amount = await currency_converter.convert_from_gton(commission_amount, "RUB")
        
        if fiat_amount:
            fiat_str = f" (~{fiat_amount:.0f} ₽)"
        else:
            fiat_str = ""
        
        # Message
        if is_partner:
            text = (
                f"💰 <b>Комиссия начислена!</b>\n\n"
                f"➕ <b>{amount_str} GTON</b>{fiat_str}\n"
                f"📊 {commission_percent}% от покупки {user_str}\n\n"
                f"Баланс обновлён в партнёрском кабинете 📈"
            )
        else:
            text = (
                f"💰 <b>Реферальный бонус!</b>\n\n"
                f"➕ <b>{amount_str} GTON</b>{fiat_str}\n"
                f"📊 {commission_percent}% от покупки {user_str}"
            )
        
        await _bot.send_message(
            chat_id=telegram_id,
            text=text,
            parse_mode="HTML"
        )
        
        logger.info(f"Commission notification sent to user {referrer_id}: {commission_amount} GTON")
        
    except Exception as e:
        logger.error(f"Failed to send commission notification: {e}")
