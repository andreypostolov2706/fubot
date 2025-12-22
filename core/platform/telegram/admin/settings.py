"""
Admin Settings - Full UI for bot configuration
"""
from sqlalchemy import select
from loguru import logger

from core.locales import t
from core.database import get_db
from core.platform.telegram.utils import build_keyboard


async def get_user_id_by_telegram_id(telegram_id: int) -> int:
    """Get user_id by telegram_id"""
    from core.database.models import User
    async with get_db() as session:
        result = await session.execute(
            select(User.id).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


# Settings configuration with types only (labels from localization)
# Keys must match DB keys (category.key format in DB, just key here)
SETTINGS_CONFIG = {
    "general": {
        "icon": "🤖",
        "settings": {
            "general.bot_name": {"label_key": "setting_bot_name", "type": "text"},
            "general.support_username": {"label_key": "setting_support", "type": "text"},
            "general.default_language": {"label_key": "setting_default_language", "type": "text"},
        }
    },
    "payments": {
        "icon": "💰",
        "settings": {
            "payments.gton_ton_rate": {"label_key": "setting_gton_ton_rate", "type": "text"},
            "payments.min_deposit_gton": {"label_key": "setting_min_deposit", "type": "text"},
            "payments.max_deposit_gton": {"label_key": "setting_max_deposit", "type": "text"},
            "payments.fee_percent": {"label_key": "setting_fee_deposit", "type": "text"},
            "payout.min_gton": {"label_key": "setting_min_payout", "type": "text"},
            "payout.fee_percent": {"label_key": "setting_fee_payout", "type": "text"},
            "payments.welcome_bonus_gton": {"label_key": "setting_welcome_bonus", "type": "text"},
            "payments.stars_enabled": {"label_key": "setting_stars_enabled", "type": "bool"},
            "payments.stars_rub_rate": {"label_key": "setting_stars_rate", "type": "text"},
            "payments.stars_min_amount": {"label_key": "setting_stars_min", "type": "number"},
            "payments.stars_max_amount": {"label_key": "setting_stars_max", "type": "number"},
        }
    },
    "referral": {
        "icon": "👥",
        "settings": {
            "referral.enabled": {"label_key": "setting_referral_enabled", "type": "bool"},
            "referral.commission_enabled": {"label_key": "setting_commission_enabled", "type": "bool"},
            "referral.level1_percent": {"label_key": "setting_level1", "type": "number"},
            "referral.partner_level1_percent": {"label_key": "setting_partner_level1", "type": "number"},
            "referral.level2_enabled": {"label_key": "setting_level2_enabled", "type": "bool"},
            "referral.level2_percent": {"label_key": "setting_level2", "type": "number"},
        }
    },
    "moderation": {
        "icon": "🛡",
        "settings": {
            "moderation.warnings_before_ban": {"label_key": "setting_warnings_before_ban", "type": "number"},
            "moderation.auto_ban_duration_days": {"label_key": "setting_ban_duration", "type": "number"},
        }
    },
    "daily_bonus": {
        "icon": "🎁",
        "settings": {
            "daily_bonus.enabled": {"label_key": "setting_daily_enabled", "type": "bool"},
            "daily_bonus.rewards": {"label_key": "setting_daily_rewards", "type": "json"},
        }
    },
    "notifications": {
        "icon": "🔔",
        "settings": {
            "notif.new_users": {"label_key": "setting_notif_new_users", "type": "bool"},
            "notif.payments": {"label_key": "setting_notif_payments", "type": "bool"},
            "notif.errors": {"label_key": "setting_notif_errors", "type": "bool"},
            "notif.channel": {"label_key": "setting_notif_channel", "type": "text"},
            "notif.quiet_start": {"label_key": "setting_quiet_start", "type": "number"},
            "notif.quiet_end": {"label_key": "setting_quiet_end", "type": "number"},
        }
    },
}


def get_setting_label(lang: str, label_key: str) -> str:
    """Get localized setting label"""
    return t(lang, f"ADMIN.{label_key}")


async def _get_rates_block() -> str:
    """Get current exchange rates block for display"""
    from core.payments.rates import rates_manager
    from core.payments.converter import currency_converter
    from decimal import Decimal
    
    text = "📊 <b>Текущие курсы:</b>\n"
    
    try:
        rates = await rates_manager.get_all_rates()
        gton_rates = await currency_converter.get_gton_rates()
        
        # GTON rates
        gton_ton = rates.get("GTON_TON", Decimal("1.53"))
        gton_usd = gton_rates.get("USD", Decimal("0"))
        gton_rub = gton_rates.get("RUB", Decimal("0"))
        
        text += f"  1 GTON = {gton_ton} TON\n"
        text += f"  1 GTON = {float(gton_usd):.4f} USD\n"
        text += f"  1 GTON = {float(gton_rub):.2f} RUB\n"
        text += "\n"
        
        # Source rates
        ton_usd = rates.get("TON_USD", Decimal("0"))
        usd_rub = rates.get("USD_RUB", Decimal("0"))
        
        text += "📈 <b>Источники:</b>\n"
        text += f"  TON/USD: {ton_usd} <i>(CoinGecko)</i>\n"
        text += f"  USD/RUB: {float(usd_rub):.2f} <i>(ExchangeRate)</i>\n"
        text += "\n"
        
    except Exception as e:
        logger.error(f"Error getting rates block: {e}")
        text += f"  ❌ Ошибка загрузки курсов\n\n"
    
    return text


async def admin_settings(query, lang: str, action: str = None, params: str = None):
    """Admin settings handler"""
    if action == "category":
        await settings_category(query, lang, params)
    elif action == "edit":
        # params: category:key
        if params and ":" in params:
            category, key = params.split(":", 1)
            await settings_edit(query, lang, category, key)
    elif action == "toggle":
        # params: category:key
        if params and ":" in params:
            category, key = params.split(":", 1)
            await settings_toggle(query, lang, category, key)
    else:
        await settings_main(query, lang)


async def settings_main(query, lang: str):
    """Settings main menu with all categories"""
    text = t(lang, "ADMIN.settings_title") + "\n\n"
    text += t(lang, "ADMIN.settings_select_category")
    
    # Localized category names
    cat_labels = {
        "general": t(lang, "ADMIN.settings_general"),
        "tokens": t(lang, "ADMIN.settings_tokens"),
        "referral": t(lang, "ADMIN.settings_referral"),
        "moderation": t(lang, "ADMIN.settings_moderation"),
        "daily_bonus": t(lang, "ADMIN.settings_daily_bonus"),
        "notifications": t(lang, "ADMIN.settings_notifications"),
    }
    
    keyboard = []
    for cat_key, cat_info in SETTINGS_CONFIG.items():
        label = cat_labels.get(cat_key, cat_key.title())
        keyboard.append([{
            "text": f"{cat_info['icon']} {label}",
            "callback_data": f"admin:settings:category:{cat_key}"
        }])
    
    # Add languages link
    keyboard.append([{"text": t(lang, "ADMIN.menu_languages"), "callback_data": "admin:languages"}])
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def settings_category(query, lang: str, category: str):
    """Show settings for a specific category"""
    from core.database.models import Setting
    
    if category not in SETTINGS_CONFIG:
        await query.answer(t(lang, "ADMIN.setting_category_not_found"), show_alert=True)
        return
    
    cat_info = SETTINGS_CONFIG[category]
    
    # Category labels from localization
    cat_labels = {
        "general": t(lang, "ADMIN.settings_general"),
        "payments": t(lang, "ADMIN.settings_payments"),
        "referral": t(lang, "ADMIN.settings_referral"),
        "moderation": t(lang, "ADMIN.settings_moderation"),
        "daily_bonus": t(lang, "ADMIN.settings_daily_bonus"),
        "notifications": t(lang, "ADMIN.settings_notifications"),
    }
    cat_label = cat_labels.get(category, category)
    
    # Get current values from DB - settings keys are like "category.key"
    async with get_db() as session:
        result = await session.execute(select(Setting))
        db_settings = {s.key: s.value for s in result.scalars().all()}
    
    text = f"{cat_info['icon']} <b>{cat_label}</b>\n\n"
    
    # Add exchange rates block for payments category
    if category == "payments":
        text += await _get_rates_block()
    
    keyboard = []
    for key, info in cat_info["settings"].items():
        value = db_settings.get(key, "—")
        label = get_setting_label(lang, info["label_key"])
        
        # Format value for display
        if info["type"] == "bool":
            display_value = "✅" if value in (True, "true", "1", 1) else "❌"
            text += f"{label}: {display_value}\n"
            # Toggle button
            keyboard.append([{
                "text": f"{'✅' if display_value == '✅' else '❌'} {label}",
                "callback_data": f"admin:settings:toggle:{category}:{key}"
            }])
        else:
            text += f"{label}: <code>{value}</code>\n"
            # Edit button
            keyboard.append([{
                "text": f"✏️ {label}",
                "callback_data": f"admin:settings:edit:{category}:{key}"
            }])
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:settings"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def settings_toggle(query, lang: str, category: str, key: str):
    """Toggle boolean setting"""
    from core.database.models import Setting
    from core.settings import settings as settings_manager
    
    async with get_db() as session:
        result = await session.execute(
            select(Setting).where(Setting.key == key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            # Toggle value
            current = setting.value in (True, "true", "1", 1)
            setting.value = "true" if not current else "false"
        else:
            # Create new setting
            setting = Setting(
                category=category,
                key=key,
                value="true",
                value_type="bool"
            )
            session.add(setting)
    
    # Invalidate cache so changes apply immediately
    settings_manager.invalidate(key)
    
    await query.answer("✅ Изменено")
    await settings_category(query, lang, category)


async def settings_edit(query, lang: str, category: str, key: str):
    """Start editing a setting value"""
    from core.database.models import Setting
    from core.plugins.core_api import CoreAPI
    
    admin_id = await get_user_id_by_telegram_id(query.from_user.id)
    core_api = CoreAPI("core")
    
    # Set state for input
    await core_api.set_user_state(admin_id, "admin_settings_edit", {
        "category": category,
        "key": key
    })
    
    # Get current value
    async with get_db() as session:
        result = await session.execute(
            select(Setting).where(Setting.key == key)
        )
        setting = result.scalar_one_or_none()
    
    current_value = setting.value if setting else "—"
    
    # Get label
    cat_info = SETTINGS_CONFIG.get(category, {})
    key_info = cat_info.get("settings", {}).get(key, {})
    label = get_setting_label(lang, key_info.get("label_key", key))
    value_type = key_info.get("type", "text")
    
    text = t(lang, "ADMIN.trigger_edit_param", label=label, value=current_value)
    
    if value_type == "number":
        text += "\n\n" + t(lang, "ADMIN.settings_enter_number")
    elif value_type == "json":
        text += "\n\n" + t(lang, "ADMIN.settings_enter_json")
    else:
        text += "\n\n" + t(lang, "ADMIN.settings_enter_value")
    
    keyboard = [[{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:settings:category:{category}"}]]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_settings_edit(update, context, admin_id: int, lang: str, category: str, key: str):
    """Handle setting value input"""
    from core.database.models import Setting
    from core.plugins.core_api import CoreAPI
    import json
    
    core_api = CoreAPI("core")
    value_text = update.message.text.strip()
    
    # Get type info
    cat_info = SETTINGS_CONFIG.get(category, {})
    key_info = cat_info.get("settings", {}).get(key, {})
    value_type = key_info.get("type", "text")
    label = key_info.get("label", key)
    
    # Parse value based on type
    if value_type == "number":
        try:
            value = float(value_text) if "." in value_text else int(value_text)
        except ValueError:
            await update.message.reply_text("❌ Введите число")
            return
    elif value_type == "json":
        try:
            value = json.loads(value_text)
        except json.JSONDecodeError:
            await update.message.reply_text("❌ Неверный формат JSON")
            return
    else:
        value = value_text
    
    # Save to DB
    async with get_db() as session:
        result = await session.execute(
            select(Setting).where(Setting.key == key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
        else:
            setting = Setting(
                category=category,
                key=key,
                value=value,
                value_type=value_type
            )
            session.add(setting)
    
    # Invalidate cache so changes apply immediately
    from core.settings import settings as settings_manager
    settings_manager.invalidate(key)
    
    await core_api.clear_user_state(admin_id)
    
    keyboard = [[{"text": "← Назад", "callback_data": f"admin:settings:category:{category}"}]]
    
    await update.message.reply_text(
        f"✅ Настройка сохранена\n\n{label}: <code>{value}</code>",
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
