"""
Admin Languages
"""
from sqlalchemy import select

from core.locales import t, get_available_languages
from core.database import get_db
from core.platform.telegram.utils import build_keyboard


async def admin_languages(query, lang: str, action: str = None, params: str = None):
    """Admin languages handler"""
    if action == "set":
        await set_admin_language(query, lang, params)
    else:
        await languages_main(query, lang)


async def languages_main(query, lang: str):
    """Languages main menu"""
    languages = get_available_languages()
    
    # Get current admin language from available languages
    current_lang_info = next((l for l in languages if l['code'] == lang), None)
    current_flag = current_lang_info['flag'] if current_lang_info else "🌐"
    current_name = current_lang_info['name'] if current_lang_info else lang
    
    text = t(lang, "ADMIN.languages_title") + "\n\n"
    text += t(lang, "ADMIN.languages_current", flag=current_flag, name=current_name) + "\n\n"
    text += t(lang, "ADMIN.languages_select")
    
    keyboard = []
    for lang_info in languages:
        # Mark current language
        if lang_info['code'] == lang:
            btn_text = f"✅ {lang_info['flag']} {lang_info['name']}"
        else:
            btn_text = f"{lang_info['flag']} {lang_info['name']}"
        
        keyboard.append([{
            "text": btn_text,
            "callback_data": f"admin:languages:set:{lang_info['code']}"
        }])
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def set_admin_language(query, current_lang: str, new_lang: str):
    """Set admin's language"""
    from core.database.models import User
    
    telegram_id = query.from_user.id
    
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.language = new_lang
    
    await query.answer(t(new_lang, "ADMIN.languages_changed"), show_alert=False)
    
    # Refresh menu with new language
    await languages_main(query, new_lang)
