"""
Telegram Platform
"""
from .bot import TelegramBot, telegram_bot
from .setup import setup_handlers

__all__ = ["TelegramBot", "telegram_bot", "setup_handlers"]
