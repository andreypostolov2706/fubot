"""
Callback Router - Routes callbacks to handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from .handlers import (
    main_menu_callback,
    settings_callback,
    language_callback,
    set_language_callback,
    topup_callback,
    partner_callback,
    daily_bonus_callback,
    help_callback,
    service_callback,
)
from .handlers.settings import notifications_callback
from .handlers.promocode import promocode_callback
from .handlers.global_settings import global_settings_callback, global_settings_edit_callback
from .admin import admin_callback


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route callbacks to appropriate handlers"""
    query = update.callback_query
    data = query.data
    logger.info(f"Callback router received: {data}")
    
    # Route based on callback data prefix
    if data == "main_menu":
        await main_menu_callback(update, context)
    
    elif data == "settings" or data.startswith("settings:"):
        if data == "settings:language":
            await language_callback(update, context)
        elif data == "settings:notifications":
            await notifications_callback(update, context)
        else:
            await settings_callback(update, context)
    
    elif data.startswith("set_language:"):
        await set_language_callback(update, context)
    
    elif data == "help":
        await help_callback(update, context)
    
    elif data == "top_up" or data.startswith("top_up:"):
        await topup_callback(update, context)
    
    elif data == "promocode" or data.startswith("promocode:"):
        await promocode_callback(update, context)
    
    elif data == "partner" or data.startswith("partner:"):
        await partner_callback(update, context)
    
    elif data == "daily_bonus" or data.startswith("daily_bonus:"):
        await daily_bonus_callback(update, context)
    
    elif data == "admin" or data.startswith("admin:"):
        await admin_callback(update, context)
    
    elif data == "global_settings":
        await global_settings_callback(update, context)
    
    elif data.startswith("global_settings:edit:"):
        await global_settings_edit_callback(update, context)
    
    elif data.startswith("service:"):
        await service_callback(update, context)
    
    else:
        await query.answer("Unknown action", show_alert=True)
