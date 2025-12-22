"""
Settings Handler
"""
from telegram import Update
from telegram.ext import ContextTypes

from core.locales import t, get_language_info, get_available_languages
from core.database import get_db
from core.platform.telegram.utils import (
    get_or_create_user, 
    get_user_language,
    build_keyboard
)


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings callback"""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    lang = await get_user_language(user_id)
    
    lang_info = get_language_info(lang)
    
    text = t(lang, "SETTINGS.title") + "\n\n"
    text += t(lang, "SETTINGS.language_current", language=lang_info["name"])
    
    keyboard = [
        [{"text": t(lang, "SETTINGS.language"), "callback_data": "settings:language"}],
        [{"text": t(lang, "SETTINGS.notifications"), "callback_data": "settings:notifications"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "main_menu"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection"""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    lang = await get_user_language(user_id)
    
    languages = get_available_languages()
    
    text = t(lang, "SETTINGS.language_select")
    
    keyboard = []
    for lang_info in languages:
        btn_text = f"{lang_info['flag']} {lang_info['name']}"
        if lang_info['code'] == lang:
            btn_text += " ✓"
        keyboard.append([{
            "text": btn_text, 
            "callback_data": f"set_language:{lang_info['code']}"
        }])
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "settings"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle set language callback"""
    query = update.callback_query
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    
    # Extract language code
    new_lang = query.data.split(":")[1]
    
    # Update user language
    from core.database.models import User
    async with get_db() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.language = new_lang
    
    lang_info = get_language_info(new_lang)
    
    await query.answer(
        t(new_lang, "SETTINGS.language_changed", language=lang_info["name"]),
        show_alert=True
    )
    
    # Refresh settings
    await settings_callback(update, context)


async def notifications_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notifications settings"""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    lang = await get_user_language(user_id)
    
    text = t(lang, "SETTINGS.notifications_title") + "\n\n"
    text += t(lang, "SETTINGS.notifications_description")
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": "settings"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
