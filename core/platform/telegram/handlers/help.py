"""
Help Handler
"""
from telegram import Update
from telegram.ext import ContextTypes

from core.locales import t
from core.platform.telegram.utils import (
    get_or_create_user, 
    get_user_language,
    build_keyboard
)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    lang = await get_user_language(user_id)
    
    text = t(lang, "HELP.title") + "\n\n"
    text += t(lang, "HELP.description")
    
    keyboard = [
        [{"text": t(lang, "HELP.support"), "url": "https://t.me/support"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "main_menu"}]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help callback"""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    lang = await get_user_language(user_id)
    
    text = t(lang, "HELP.title") + "\n\n"
    text += t(lang, "HELP.description")
    
    keyboard = [
        [{"text": t(lang, "HELP.support"), "url": "https://t.me/support"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "main_menu"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
