"""
Admin Main Handler
"""
from telegram import Update
from telegram.ext import ContextTypes

from core.locales import t
from core.platform.telegram.utils import get_or_create_user, get_user_language, build_keyboard
from core.platform.telegram.middlewares import admin_required

from .stats import admin_stats
from .users import admin_users
from .partners import admin_partners
from .services import admin_services
from .settings import admin_settings
from .languages import admin_languages
from .broadcast import admin_broadcast
from .moderation import admin_moderation
from .promocodes import admin_promocodes


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callback"""
    query = update.callback_query
    
    # Check admin access
    if not await admin_required(update):
        return
    
    await query.answer()
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    lang = await get_user_language(user_id)
    
    # Parse action
    data = query.data
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else "main"
    sub_action = parts[2] if len(parts) > 2 else None
    # Join all remaining parts as params (for nested data like trigger_id:field)
    params = ":".join(parts[3:]) if len(parts) > 3 else None
    
    # Route to handler
    if action == "main" or data == "admin":
        await admin_main(query, lang)
    elif action == "stats":
        await admin_stats(query, lang, sub_action, params)
    elif action == "users":
        await admin_users(query, lang, sub_action, params)
    elif action == "partners":
        await admin_partners(query, lang, sub_action, params)
    elif action == "services":
        await admin_services(query, lang, sub_action, params)
    elif action == "settings":
        await admin_settings(query, lang, sub_action, params)
    elif action == "languages":
        await admin_languages(query, lang, sub_action, params)
    elif action == "broadcast":
        await admin_broadcast(query, lang, sub_action, params)
    elif action == "moderation":
        await admin_moderation(query, lang, sub_action, params)
    elif action == "promocodes":
        await admin_promocodes(query, lang, sub_action, params)
    else:
        await query.answer("Coming soon", show_alert=True)


async def admin_main(query, lang: str):
    """Admin main menu"""
    text = t(lang, "ADMIN.title")
    
    keyboard = [
        [{"text": t(lang, "ADMIN.menu_stats"), "callback_data": "admin:stats"}],
        [{"text": t(lang, "ADMIN.menu_users"), "callback_data": "admin:users"}],
        [{"text": t(lang, "ADMIN.menu_partners"), "callback_data": "admin:partners"}],
        [{"text": t(lang, "ADMIN.menu_moderation"), "callback_data": "admin:moderation"}],
        [{"text": t(lang, "ADMIN.menu_promocodes"), "callback_data": "admin:promocodes"}],
        [{"text": t(lang, "ADMIN.menu_services"), "callback_data": "admin:services"}],
        [{"text": t(lang, "ADMIN.menu_broadcast"), "callback_data": "admin:broadcast"}],
        [{"text": t(lang, "ADMIN.menu_settings"), "callback_data": "admin:settings"}],
        [{"text": t(lang, "ADMIN.menu_languages"), "callback_data": "admin:languages"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "main_menu"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
