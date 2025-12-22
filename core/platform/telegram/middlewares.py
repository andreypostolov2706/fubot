"""
Telegram Middlewares
"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from core.config import config
from core.database import get_db
from .utils import get_or_create_user


async def check_user_banned(user_id: int) -> dict | None:
    """
    Check if user is banned.
    
    Returns:
        None if not banned, or dict with ban info
    """
    from core.database.models import User
    from datetime import datetime
    
    async with get_db() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_blocked:
            return None
        
        # Check if temporary ban expired
        if user.block_type == "temporary" and user.block_expires_at:
            if user.block_expires_at < datetime.utcnow():
                # Unban
                user.is_blocked = False
                user.block_type = None
                user.block_reason = None
                user.block_expires_at = None
                return None
        
        return {
            "type": user.block_type,
            "reason": user.block_reason,
            "expires_at": user.block_expires_at
        }


def is_admin(telegram_id: int) -> bool:
    """Check if user is admin"""
    return config.is_admin(telegram_id)


async def admin_required(update: Update) -> bool:
    """
    Check admin access.
    
    Returns:
        True if admin, False otherwise (and sends error)
    """
    telegram_user = update.effective_user
    
    if not is_admin(telegram_user.id):
        query = update.callback_query
        if query:
            await query.answer("⛔ Доступ запрещён", show_alert=True)
        return False
    
    return True
