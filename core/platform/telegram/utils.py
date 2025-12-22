"""
Telegram Utils - Helper functions
"""
from decimal import Decimal
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from core.database import get_db


async def get_or_create_user(telegram_id: int, telegram_user) -> int:
    """Get or create user, returns user_id"""
    from core.database.models import User, Wallet, Setting, Transaction
    
    async with get_db() as session:
        from sqlalchemy import select
        
        # Find existing
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update activity
            from datetime import datetime
            user.last_activity_at = datetime.utcnow()
            if telegram_user.username:
                user.telegram_username = telegram_user.username
            return user.id
        
        # Create new user
        import secrets
        user = User(
            telegram_id=telegram_id,
            telegram_username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language="ru",
            referral_code=secrets.token_urlsafe(8)
        )
        session.add(user)
        await session.flush()
        
        # Get welcome bonus amount
        bonus_result = await session.execute(
            select(Setting.value).where(Setting.key == "payments.welcome_bonus_gton")
        )
        bonus_value = bonus_result.scalar_one_or_none()
        welcome_bonus = Decimal(bonus_value.replace(",", ".")) if bonus_value else Decimal("0")
        
        # Create main wallet with welcome bonus
        wallet = Wallet(user_id=user.id, wallet_type="main", balance=welcome_bonus)
        session.add(wallet)
        await session.flush()
        
        # Create welcome bonus transaction if bonus > 0
        if welcome_bonus > 0:
            tx = Transaction(
                user_id=user.id,
                wallet_id=wallet.id,
                type="welcome_bonus",
                amount=welcome_bonus,
                direction="credit",
                balance_before=Decimal("0"),
                balance_after=welcome_bonus
            )
            session.add(tx)
            logger.info(f"Welcome bonus {welcome_bonus} GTON credited to user {user.id}")
        
        logger.info(f"New user created: {user.id} (@{telegram_user.username})")
        return user.id


async def get_user_language(user_id: int) -> str:
    """Get user language"""
    from core.database.models import User
    
    async with get_db() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User.language).where(User.id == user_id)
        )
        lang = result.scalar_one_or_none()
        return lang or "ru"


async def get_user_role(user_id: int) -> str:
    """Get user role (user/admin/moderator)"""
    from core.database.models import User
    
    async with get_db() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User.role).where(User.id == user_id)
        )
        role = result.scalar_one_or_none()
        return role or "user"


async def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    role = await get_user_role(user_id)
    return role == "admin"


async def get_user_balance(user_id: int) -> Decimal:
    """Get user main GTON balance"""
    from core.database.models import Wallet
    
    async with get_db() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Wallet.balance).where(
                Wallet.user_id == user_id,
                Wallet.wallet_type == "main"
            )
        )
        balance = result.scalar_one_or_none()
        return Decimal(str(balance)) if balance else Decimal("0")


async def get_user_balance_with_fiat(user_id: int, fiat: str = "RUB") -> tuple[Decimal, Optional[Decimal]]:
    """
    Get user GTON balance with fiat equivalent.
    
    Returns:
        (gton_balance, fiat_equivalent)
    """
    from core.payments.converter import currency_converter
    
    gton = await get_user_balance(user_id)
    fiat_amount = await currency_converter.convert_from_gton(gton, fiat)
    return gton, fiat_amount


def format_gton(amount: Decimal, precision: int = 2) -> str:
    """
    Format GTON amount for display.
    
    Args:
        amount: Amount in GTON
        precision: Decimal places to show (default 2)
        
    Returns:
        Formatted string like "10.5" or "0.123456"
    """
    if amount == 0:
        return "0"
    
    # Show more precision for small amounts
    if amount < Decimal("0.01"):
        precision = 6
    elif amount < Decimal("1"):
        precision = 4
    
    formatted = f"{amount:.{precision}f}".rstrip('0').rstrip('.')
    return formatted


def format_gton_with_fiat(gton: Decimal, fiat: Optional[Decimal], currency: str = "RUB") -> str:
    """
    Format GTON with fiat equivalent.
    
    Returns:
        "10.5 GTON (~1,085 ₽)"
    """
    gton_str = format_gton(gton)
    
    if fiat is not None:
        if currency == "RUB":
            fiat_str = f"{fiat:,.0f} ₽".replace(",", " ")
        elif currency == "USD":
            fiat_str = f"${fiat:,.2f}"
        else:
            fiat_str = f"{fiat:,.2f} {currency}"
        return f"{gton_str} GTON (~{fiat_str})"
    
    return f"{gton_str} GTON"


async def get_user_telegram_id(user_id: int) -> int | None:
    """Get telegram_id by user_id"""
    from core.database.models import User
    
    async with get_db() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User.telegram_id).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


def build_keyboard(items: list[list[dict]]) -> InlineKeyboardMarkup:
    """
    Build inline keyboard from list of dicts.
    
    Example:
        keyboard = [
            [{"text": "Button 1", "callback_data": "action1"}],
            [{"text": "Link", "url": "https://..."}],
        ]
    """
    keyboard = []
    for row in items:
        keyboard_row = []
        for item in row:
            if "url" in item:
                keyboard_row.append(
                    InlineKeyboardButton(item["text"], url=item["url"])
                )
            else:
                keyboard_row.append(
                    InlineKeyboardButton(
                        item["text"], 
                        callback_data=item.get("callback_data", item.get("callback", ""))
                    )
                )
        keyboard.append(keyboard_row)
    return InlineKeyboardMarkup(keyboard)


def back_button(callback: str = "main_menu", text: str = None) -> dict:
    """Create back button"""
    return {"text": text or "◀️ Назад", "callback_data": callback}
