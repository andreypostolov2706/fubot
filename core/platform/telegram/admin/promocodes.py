"""
Admin Promocodes Management - Full Featured
"""
import random
import string
import html
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc

from core.locales import t
from core.database import get_db
from core.platform.telegram.utils import build_keyboard


# Reward type icons
REWARD_ICONS = {
    "tokens": "🪙",
    "subscription": "⭐", 
    "discount": "💸"
}


def generate_promo_code(length: int = 8) -> str:
    """Generate random promo code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def get_reward_label(reward_type: str, lang: str) -> str:
    """Get localized reward type label"""
    labels = {
        "tokens": t(lang, "ADMIN.promo_type_tokens"),
        "subscription": t(lang, "ADMIN.promo_type_subscription"),
        "discount": t(lang, "ADMIN.promo_type_discount")
    }
    return labels.get(reward_type, reward_type)


async def get_user_id_by_telegram_id(telegram_id: int) -> int:
    """Get user ID by telegram ID"""
    from core.database.models import User
    async with get_db() as session:
        result = await session.execute(
            select(User.id).where(User.telegram_id == telegram_id)
        )
        return result.scalar()


async def admin_promocodes(query, lang: str, action: str = None, params: str = None):
    """Admin promocodes handler"""
    if action == "list":
        filter_type = params.split("_")[0] if params else "all"
        page = int(params.split("_")[-1]) if params and "_" in params else 0
        await promocodes_list(query, lang, filter_type, page)
    elif action == "view" and params:
        await view_promocode(query, lang, int(params))
    elif action == "create":
        await create_promocode_menu(query, lang)
    elif action == "create_type" and params:
        await create_promocode_type(query, lang, params)
    elif action == "create_value" and params:
        parts = params.split("_")
        await create_promocode_value(query, lang, parts[0], int(parts[1]) if len(parts) > 1 else None)
    elif action == "create_code" and params:
        parts = params.split("_", 1)
        await create_promocode_code(query, lang, parts[0], int(parts[1]))
    elif action == "create_limits" and params:
        await create_promocode_limits(query, lang, int(params))
    elif action == "set_limit" and params:
        parts = params.split("_")
        await set_promocode_limit(query, lang, int(parts[0]), parts[1], int(parts[2]) if len(parts) > 2 else None)
    elif action == "create_dates" and params:
        await create_promocode_dates(query, lang, int(params))
    elif action == "set_date" and params:
        parts = params.split("_")
        await set_promocode_date(query, lang, int(parts[0]), parts[1])
    elif action == "create_binding" and params:
        await create_promocode_binding(query, lang, int(params))
    elif action == "set_binding" and params:
        parts = params.split("_", 1)  # Split only on first underscore
        await set_promocode_binding(query, lang, int(parts[0]), parts[1] if len(parts) > 1 else None)
    elif action == "create_confirm" and params:
        await create_promocode_confirm(query, lang, int(params))
    elif action == "edit" and params:
        parts = params.split("_")
        await edit_promocode(query, lang, int(parts[0]), parts[1] if len(parts) > 1 else None)
    elif action == "history" and params:
        await promocode_history(query, lang, int(params))
    elif action == "stats":
        await promocodes_stats(query, lang)
    elif action == "toggle" and params:
        await toggle_promocode(query, lang, int(params))
    elif action == "delete" and params:
        await delete_promocode(query, lang, int(params))
    elif action == "delete_confirm" and params:
        await delete_promocode_confirm(query, lang, int(params))
    else:
        await promocodes_main(query, lang)


async def promocodes_main(query, lang: str):
    """Promocodes main menu"""
    from core.database.models import PromoCode, PromoCodeActivation
    
    async with get_db() as session:
        # Active promocodes
        result = await session.execute(
            select(func.count(PromoCode.id)).where(PromoCode.is_active == True)
        )
        active_count = result.scalar() or 0
        
        # Total activations
        result = await session.execute(
            select(func.count(PromoCodeActivation.id))
        )
        total_activations = result.scalar() or 0
    
    text = t(lang, "ADMIN.promocodes_title") + "\n\n"
    text += t(lang, "ADMIN.promocodes_active", count=active_count) + "\n"
    text += t(lang, "ADMIN.promocodes_total_activations", count=total_activations) + "\n"
    
    keyboard = [
        [{"text": t(lang, "ADMIN.promocodes_create"), "callback_data": "admin:promocodes:create"}],
        [{"text": t(lang, "ADMIN.promocodes_list"), "callback_data": "admin:promocodes:list"}],
        [{"text": t(lang, "ADMIN.promocodes_stats"), "callback_data": "admin:promocodes:stats"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def promocodes_list(query, lang: str, filter_type: str = "all", page: int = 0):
    """Show promocodes list with filters"""
    from core.database.models import PromoCode
    
    per_page = 8
    now = datetime.utcnow()
    
    async with get_db() as session:
        # Base query
        base_query = select(PromoCode)
        count_query = select(func.count(PromoCode.id))
        
        # Apply filters
        if filter_type == "tokens":
            base_query = base_query.where(PromoCode.reward_type == "tokens")
            count_query = count_query.where(PromoCode.reward_type == "tokens")
        elif filter_type == "subscription":
            base_query = base_query.where(PromoCode.reward_type == "subscription")
            count_query = count_query.where(PromoCode.reward_type == "subscription")
        elif filter_type == "discount":
            base_query = base_query.where(PromoCode.reward_type == "discount")
            count_query = count_query.where(PromoCode.reward_type == "discount")
        elif filter_type == "active":
            base_query = base_query.where(PromoCode.is_active == True)
            count_query = count_query.where(PromoCode.is_active == True)
        elif filter_type == "inactive":
            base_query = base_query.where(PromoCode.is_active == False)
            count_query = count_query.where(PromoCode.is_active == False)
        elif filter_type == "expired":
            base_query = base_query.where(PromoCode.expires_at < now)
            count_query = count_query.where(PromoCode.expires_at < now)
        
        # Get total count
        result = await session.execute(count_query)
        total = result.scalar() or 0
        
        # Get promocodes
        result = await session.execute(
            base_query.order_by(desc(PromoCode.created_at))
            .offset(page * per_page).limit(per_page)
        )
        promocodes = result.scalars().all()
    
    text = t(lang, "ADMIN.promo_list_title") + "\n\n"
    
    if not promocodes:
        text += t(lang, "ADMIN.promocodes_empty")
    else:
        for promo in promocodes:
            icon = REWARD_ICONS.get(promo.reward_type, "🎁")
            status = "✅" if promo.is_active and promo.is_valid else "⏸" if not promo.is_active else "⏰"
            text += f"{status} <code>{promo.code}</code> — {icon} {promo.reward_value}\n"
            text += f"    {t(lang, 'ADMIN.promo_activations')}: {promo.current_activations}"
            if promo.max_activations:
                text += f"/{promo.max_activations}"
            text += "\n"
    
    # Filter buttons
    keyboard = [
        [
            {"text": t(lang, "ADMIN.filter_all") if filter_type != "all" else f"• {t(lang, 'ADMIN.filter_all')} •", 
             "callback_data": "admin:promocodes:list:all"},
            {"text": "🪙" if filter_type != "tokens" else "• 🪙 •", 
             "callback_data": "admin:promocodes:list:tokens"},
            {"text": "⭐" if filter_type != "subscription" else "• ⭐ •", 
             "callback_data": "admin:promocodes:list:subscription"},
            {"text": "💸" if filter_type != "discount" else "• 💸 •", 
             "callback_data": "admin:promocodes:list:discount"},
        ],
        [
            {"text": "✅" if filter_type != "active" else "• ✅ •", 
             "callback_data": "admin:promocodes:list:active"},
            {"text": "⏸" if filter_type != "inactive" else "• ⏸ •", 
             "callback_data": "admin:promocodes:list:inactive"},
            {"text": "⏰" if filter_type != "expired" else "• ⏰ •", 
             "callback_data": "admin:promocodes:list:expired"},
        ]
    ]
    
    # Promocode buttons
    for promo in promocodes:
        icon = REWARD_ICONS.get(promo.reward_type, "🎁")
        status = "✅" if promo.is_active else "⏸"
        keyboard.append([{
            "text": f"{status} {promo.code} — {icon}{promo.reward_value}",
            "callback_data": f"admin:promocodes:view:{promo.id}"
        }])
    
    # Pagination
    if total > per_page:
        nav = []
        if page > 0:
            nav.append({"text": "◀️", "callback_data": f"admin:promocodes:list:{filter_type}_{page-1}"})
        nav.append({"text": f"{page+1}/{(total-1)//per_page+1}", "callback_data": "noop"})
        if (page + 1) * per_page < total:
            nav.append({"text": "▶️", "callback_data": f"admin:promocodes:list:{filter_type}_{page+1}"})
        keyboard.append(nav)
    
    keyboard.append([
        {"text": t(lang, "ADMIN.promocodes_create"), "callback_data": "admin:promocodes:create"},
        {"text": t(lang, "COMMON.back"), "callback_data": "admin:promocodes"}
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def view_promocode(query, lang: str, promo_id: int):
    """View promocode details with full management"""
    from core.database.models import PromoCode, User
    
    async with get_db() as session:
        result = await session.execute(
            select(PromoCode).where(PromoCode.id == promo_id)
        )
        promo = result.scalar_one_or_none()
        
        bound_user = None
        if promo and promo.bound_user_id:
            result = await session.execute(
                select(User).where(User.id == promo.bound_user_id)
            )
            bound_user = result.scalar_one_or_none()
    
    if not promo:
        await query.answer(t(lang, "ADMIN.promocodes_not_found"), show_alert=True)
        return
    
    # Status
    if not promo.is_active:
        status = t(lang, "ADMIN.promo_status_disabled")
        status_icon = "⏸"
    elif promo.expires_at and promo.expires_at < datetime.utcnow():
        status = t(lang, "ADMIN.promo_status_expired")
        status_icon = "⏰"
    elif promo.max_activations and promo.current_activations >= promo.max_activations:
        status = t(lang, "ADMIN.promo_status_exhausted")
        status_icon = "🔴"
    else:
        status = t(lang, "ADMIN.promo_status_active")
        status_icon = "✅"
    
    icon = REWARD_ICONS.get(promo.reward_type, "🎁")
    reward_label = get_reward_label(promo.reward_type, lang)
    
    text = f"🎁 <b>{promo.code}</b>\n\n"
    text += f"📊 {t(lang, 'ADMIN.promo_view_status')}: {status_icon} {status}\n"
    text += f"🎯 {t(lang, 'ADMIN.promo_view_type')}: {reward_label}\n"
    text += f"💰 {t(lang, 'ADMIN.promo_view_value')}: {icon} {promo.reward_value}"
    if promo.reward_type == "tokens":
        text += f" {t(lang, 'ADMIN.tokens')}"
    elif promo.reward_type == "subscription":
        text += f" {t(lang, 'ADMIN.days')}"
    elif promo.reward_type == "discount":
        text += "%"
    text += "\n\n"
    
    # Activations
    text += f"📈 <b>{t(lang, 'ADMIN.promo_view_activations')}:</b>\n"
    text += f"├── {t(lang, 'ADMIN.promo_current')}: {promo.current_activations}"
    if promo.max_activations:
        text += f"/{promo.max_activations}"
    text += "\n"
    text += f"└── {t(lang, 'ADMIN.promo_per_user')}: {promo.max_per_user}\n\n"
    
    # Dates
    text += f"📅 <b>{t(lang, 'ADMIN.promo_view_dates')}:</b>\n"
    if promo.starts_at:
        text += f"├── {t(lang, 'ADMIN.promo_starts')}: {promo.starts_at.strftime('%d.%m.%Y %H:%M')}\n"
    if promo.expires_at:
        text += f"├── {t(lang, 'ADMIN.promo_expires')}: {promo.expires_at.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"└── {t(lang, 'ADMIN.promo_created')}: {promo.created_at.strftime('%d.%m.%Y')}\n\n"
    
    # Conditions
    conditions = []
    if promo.only_new_users:
        conditions.append(t(lang, "ADMIN.promo_only_new"))
    if promo.only_first_deposit:
        conditions.append(t(lang, "ADMIN.promo_first_deposit"))
    if promo.min_balance:
        conditions.append(t(lang, "ADMIN.promo_min_balance", amount=promo.min_balance))
    if bound_user:
        conditions.append(t(lang, "ADMIN.promo_bound_to", user=bound_user.display_name))
    
    if conditions:
        text += f"⚙️ <b>{t(lang, 'ADMIN.promo_view_conditions')}:</b>\n"
        for cond in conditions:
            text += f"├── {cond}\n"
        text = text[:-1] + text[-1].replace("├", "└")  # Fix last item
        text += "\n"
    
    # Keyboard
    keyboard = [
        [
            {"text": t(lang, "ADMIN.promo_edit_value"), "callback_data": f"admin:promocodes:edit:{promo_id}_value"},
            {"text": t(lang, "ADMIN.promo_edit_limits"), "callback_data": f"admin:promocodes:edit:{promo_id}_limits"},
        ],
        [
            {"text": t(lang, "ADMIN.promo_edit_dates"), "callback_data": f"admin:promocodes:edit:{promo_id}_dates"},
            {"text": t(lang, "ADMIN.promo_edit_binding"), "callback_data": f"admin:promocodes:edit:{promo_id}_binding"},
        ],
        [{"text": t(lang, "ADMIN.promo_history"), "callback_data": f"admin:promocodes:history:{promo_id}"}],
    ]
    
    if promo.is_active:
        keyboard.append([{"text": t(lang, "ADMIN.promo_disable"), "callback_data": f"admin:promocodes:toggle:{promo_id}"}])
    else:
        keyboard.append([{"text": t(lang, "ADMIN.promo_enable"), "callback_data": f"admin:promocodes:toggle:{promo_id}"}])
    
    keyboard.append([
        {"text": t(lang, "ADMIN.promo_delete"), "callback_data": f"admin:promocodes:delete:{promo_id}"},
        {"text": t(lang, "COMMON.back"), "callback_data": "admin:promocodes:list"}
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def toggle_promocode(query, lang: str, promo_id: int):
    """Toggle promocode active status"""
    from core.database.models import PromoCode
    
    async with get_db() as session:
        result = await session.execute(
            select(PromoCode).where(PromoCode.id == promo_id)
        )
        promo = result.scalar_one_or_none()
        
        if promo:
            promo.is_active = not promo.is_active
            new_status = t(lang, "ADMIN.promocodes_enabled") if promo.is_active else t(lang, "ADMIN.promocodes_disabled")
    
    await query.answer(t(lang, "ADMIN.promocodes_toggled", status=new_status), show_alert=True)
    await view_promocode(query, lang, promo_id)


async def create_promocode_menu(query, lang: str):
    """Create promocode menu"""
    text = t(lang, "ADMIN.promocodes_create") + "\n\n"
    text += t(lang, "ADMIN.promocodes_select_reward")
    
    keyboard = [
        [{"text": t(lang, "ADMIN.promo_type_tokens"), "callback_data": "admin:promocodes:create_type:tokens"}],
        [{"text": t(lang, "ADMIN.promo_type_subscription"), "callback_data": "admin:promocodes:create_type:subscription"}],
        [{"text": t(lang, "ADMIN.promo_type_discount"), "callback_data": "admin:promocodes:create_type:discount"}],
        [{"text": t(lang, "COMMON.cancel"), "callback_data": "admin:promocodes"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def promocodes_stats(query, lang: str):
    """Promocodes statistics"""
    from core.database.models import PromoCode, PromoCodeActivation
    from datetime import timedelta
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    
    async with get_db() as session:
        # Today activations
        result = await session.execute(
            select(func.count(PromoCodeActivation.id)).where(
                PromoCodeActivation.activated_at >= today
            )
        )
        today_count = result.scalar() or 0
        
        # Week activations
        result = await session.execute(
            select(func.count(PromoCodeActivation.id)).where(
                PromoCodeActivation.activated_at >= week_ago
            )
        )
        week_count = result.scalar() or 0
        
        # Total tokens given
        result = await session.execute(
            select(func.sum(PromoCodeActivation.reward_value)).where(
                PromoCodeActivation.reward_type == "tokens"
            )
        )
        total_tokens = result.scalar() or 0
        
        # Top promocodes
        result = await session.execute(
            select(PromoCode).order_by(
                desc(PromoCode.current_activations)
            ).limit(5)
        )
        top_promos = result.scalars().all()
    
    text = t(lang, "ADMIN.promo_stats_title") + "\n\n"
    text += t(lang, "ADMIN.promo_stats_today", count=today_count) + "\n"
    text += t(lang, "ADMIN.promo_stats_week", count=week_count) + "\n"
    text += t(lang, "ADMIN.promo_stats_tokens", count=total_tokens) + "\n\n"
    
    if top_promos:
        text += t(lang, "ADMIN.promo_stats_top") + "\n"
        for promo in top_promos:
            text += f"• <code>{promo.code}</code>: {promo.current_activations}\n"
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:promocodes"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


# ==================== CREATION WIZARD ====================

async def create_promocode_type(query, lang: str, reward_type: str):
    """Step 1: Select reward type - show value input"""
    from core.database.models import PromoCode
    
    admin_id = await get_user_id_by_telegram_id(query.from_user.id)
    
    async with get_db() as session:
        promo = PromoCode(
            code=generate_promo_code(),
            reward_type=reward_type,
            reward_value=0,
            created_by=admin_id,
            is_active=False
        )
        session.add(promo)
        await session.flush()
        promo_id = promo.id
    
    icon = REWARD_ICONS.get(reward_type, "🎁")
    text = t(lang, "ADMIN.promo_create_value_title", type=get_reward_label(reward_type, lang)) + "\n\n"
    
    if reward_type == "tokens":
        text += t(lang, "ADMIN.promo_create_value_tokens")
        values = [50, 100, 200, 500, 1000]
    elif reward_type == "subscription":
        text += t(lang, "ADMIN.promo_create_value_subscription")
        values = [3, 7, 14, 30, 90]
    else:
        text += t(lang, "ADMIN.promo_create_value_discount")
        values = [5, 10, 15, 20, 50]
    
    keyboard = []
    row = []
    for val in values:
        suffix = "%" if reward_type == "discount" else ""
        row.append({"text": f"{icon} {val}{suffix}", "callback_data": f"admin:promocodes:create_value:{reward_type}_{val}_{promo_id}"})
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:promocodes:delete_confirm:{promo_id}"}])
    
    await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")


async def create_promocode_value(query, lang: str, reward_type: str, value: int):
    """Step 2: Set value - show code options"""
    from core.database.models import PromoCode
    
    params = query.data.split(":")[-1]
    parts = params.split("_")
    promo_id = int(parts[-1])
    value = int(parts[1])
    
    async with get_db() as session:
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
        if promo:
            promo.reward_value = value
    
    icon = REWARD_ICONS.get(reward_type, "🎁")
    text = t(lang, "ADMIN.promo_create_code_title") + "\n\n"
    text += f"{t(lang, 'ADMIN.promo_view_type')}: {get_reward_label(reward_type, lang)}\n"
    text += f"{t(lang, 'ADMIN.promo_view_value')}: {icon} {value}\n\n"
    text += t(lang, "ADMIN.promo_create_code_prompt")
    
    keyboard = [
        [{"text": t(lang, "ADMIN.promo_code_generate"), "callback_data": f"admin:promocodes:create_code:auto_{promo_id}"}],
        [{"text": t(lang, "ADMIN.promo_code_custom"), "callback_data": f"admin:promocodes:create_code:custom_{promo_id}"}],
        [{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:promocodes:delete_confirm:{promo_id}"}]
    ]
    
    await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")


async def create_promocode_code(query, lang: str, code_type: str, promo_id: int):
    """Step 3: Set code"""
    from core.plugins.core_api import CoreAPI
    
    if code_type == "custom":
        core_api = CoreAPI("core")
        admin_id = await get_user_id_by_telegram_id(query.from_user.id)
        await core_api.set_user_state(admin_id, "admin_promo_custom_code", {"promo_id": promo_id})
        
        text = t(lang, "ADMIN.promo_enter_code")
        keyboard = [[{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:promocodes:create_limits:{promo_id}"}]]
        await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")
        return
    
    await create_promocode_limits(query, lang, promo_id)


async def create_promocode_limits(query, lang: str, promo_id: int):
    """Step 4: Set limits"""
    from core.database.models import PromoCode
    
    async with get_db() as session:
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
    
    if not promo:
        await query.answer(t(lang, "ADMIN.promocodes_not_found"), show_alert=True)
        return
    
    icon = REWARD_ICONS.get(promo.reward_type, "🎁")
    text = t(lang, "ADMIN.promo_create_limits_title") + "\n\n"
    text += f"📝 {t(lang, 'ADMIN.promo_code')}: <code>{promo.code}</code>\n"
    text += f"🎯 {get_reward_label(promo.reward_type, lang)}: {icon} {promo.reward_value}\n\n"
    
    max_act = promo.max_activations or "∞"
    per_user = promo.max_per_user or 1
    
    text += f"📊 {t(lang, 'ADMIN.promo_max_activations')}: {max_act}\n"
    text += f"👤 {t(lang, 'ADMIN.promo_per_user')}: {per_user}\n"
    
    keyboard = [
        [
            {"text": "10", "callback_data": f"admin:promocodes:set_limit:{promo_id}_total_10"},
            {"text": "50", "callback_data": f"admin:promocodes:set_limit:{promo_id}_total_50"},
            {"text": "100", "callback_data": f"admin:promocodes:set_limit:{promo_id}_total_100"},
            {"text": "∞", "callback_data": f"admin:promocodes:set_limit:{promo_id}_total_0"},
        ],
        [{"text": t(lang, "ADMIN.promo_next"), "callback_data": f"admin:promocodes:create_dates:{promo_id}"}],
        [{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:promocodes:delete_confirm:{promo_id}"}]
    ]
    
    await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")


async def set_promocode_limit(query, lang: str, promo_id: int, limit_type: str, value: int = None):
    """Set limit value"""
    from core.database.models import PromoCode
    
    if value is not None:
        async with get_db() as session:
            result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
            promo = result.scalar_one_or_none()
            if promo:
                if limit_type == "total":
                    promo.max_activations = value if value > 0 else None
                elif limit_type == "per_user":
                    promo.max_per_user = value if value > 0 else 1
    
    await create_promocode_limits(query, lang, promo_id)


async def create_promocode_dates(query, lang: str, promo_id: int):
    """Step 5: Set dates"""
    from core.database.models import PromoCode
    
    async with get_db() as session:
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
    
    if not promo:
        await query.answer(t(lang, "ADMIN.promocodes_not_found"), show_alert=True)
        return
    
    text = t(lang, "ADMIN.promo_create_dates_title") + "\n\n"
    expires = promo.expires_at.strftime('%d.%m.%Y') if promo.expires_at else t(lang, "ADMIN.promo_never")
    text += f"⏰ {t(lang, 'ADMIN.promo_expires')}: {expires}\n"
    
    keyboard = [
        [{"text": t(lang, "ADMIN.promo_no_expiry"), "callback_data": f"admin:promocodes:set_date:{promo_id}_never"}],
        [
            {"text": "7d", "callback_data": f"admin:promocodes:set_date:{promo_id}_7"},
            {"text": "14d", "callback_data": f"admin:promocodes:set_date:{promo_id}_14"},
            {"text": "30d", "callback_data": f"admin:promocodes:set_date:{promo_id}_30"},
            {"text": "90d", "callback_data": f"admin:promocodes:set_date:{promo_id}_90"},
        ],
        [{"text": t(lang, "ADMIN.promo_next"), "callback_data": f"admin:promocodes:create_binding:{promo_id}"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:promocodes:create_limits:{promo_id}"}]
    ]
    
    await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")


async def set_promocode_date(query, lang: str, promo_id: int, days_str: str):
    """Set expiry date"""
    from core.database.models import PromoCode
    
    async with get_db() as session:
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
        if promo:
            if days_str == "never":
                promo.expires_at = None
            else:
                promo.expires_at = datetime.utcnow() + timedelta(days=int(days_str))
    
    await create_promocode_dates(query, lang, promo_id)


async def create_promocode_binding(query, lang: str, promo_id: int):
    """Step 6: Set binding"""
    from core.database.models import PromoCode, Partner, User
    
    async with get_db() as session:
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
        
        partner_name = None
        if promo and promo.partner_id:
            result = await session.execute(
                select(Partner, User).join(User, Partner.user_id == User.id)
                .where(Partner.id == promo.partner_id)
            )
            row = result.first()
            if row:
                partner_name = row[1].display_name
    
    if not promo:
        await query.answer(t(lang, "ADMIN.promocodes_not_found"), show_alert=True)
        return
    
    text = t(lang, "ADMIN.promo_create_binding_title") + "\n\n"
    
    # Current settings
    new_users_icon = "✅" if promo.only_new_users else "⬜"
    text += f"{new_users_icon} {t(lang, 'ADMIN.promo_only_new_users')}\n"
    
    if partner_name:
        text += f"👥 {t(lang, 'ADMIN.promo_partner_bound', partner=partner_name)}\n"
    
    keyboard = [
        [{"text": f"{new_users_icon} {t(lang, 'ADMIN.promo_only_new_users')}", "callback_data": f"admin:promocodes:set_binding:{promo_id}_new_users"}],
        [{"text": t(lang, "ADMIN.promo_bind_partner"), "callback_data": f"admin:promocodes:set_binding:{promo_id}_bind_partner"}],
        [{"text": t(lang, "ADMIN.promo_finish"), "callback_data": f"admin:promocodes:create_confirm:{promo_id}"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:promocodes:create_dates:{promo_id}"}]
    ]
    
    await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")


async def set_promocode_binding(query, lang: str, promo_id: int, binding_type: str):
    """Set binding"""
    from core.database.models import PromoCode
    from core.plugins.core_api import CoreAPI
    
    if binding_type == "new_users":
        async with get_db() as session:
            result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
            promo = result.scalar_one_or_none()
            if promo:
                promo.only_new_users = not promo.only_new_users
                status = t(lang, "COMMON.enabled") if promo.only_new_users else t(lang, "COMMON.disabled")
        await query.answer(f"✅ {status}", show_alert=False)
        await create_promocode_binding(query, lang, promo_id)
        
    elif binding_type == "bind_partner":
        core_api = CoreAPI("core")
        admin_id = await get_user_id_by_telegram_id(query.from_user.id)
        await core_api.set_user_state(admin_id, "admin_promo_bind_partner", {"promo_id": promo_id})
        
        text = t(lang, "ADMIN.promo_enter_partner_id")
        keyboard = [[{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:promocodes:create_binding:{promo_id}"}]]
        await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")


async def create_promocode_confirm(query, lang: str, promo_id: int):
    """Final: Confirm and activate"""
    from core.database.models import PromoCode, User
    
    async with get_db() as session:
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
        
        bound_user = None
        if promo and promo.bound_user_id:
            result = await session.execute(select(User).where(User.id == promo.bound_user_id))
            bound_user = result.scalar_one_or_none()
        
        if promo:
            promo.is_active = True
    
    if not promo:
        await query.answer(t(lang, "ADMIN.promocodes_not_found"), show_alert=True)
        return
    
    icon = REWARD_ICONS.get(promo.reward_type, "🎁")
    text = t(lang, "ADMIN.promo_created_success") + "\n\n"
    text += f"🎁 <b>{promo.code}</b>\n\n"
    text += f"🎯 {get_reward_label(promo.reward_type, lang)}: {icon} {promo.reward_value}\n"
    text += f"📊 {t(lang, 'ADMIN.promo_max_activations')}: {promo.max_activations or '∞'}\n"
    
    if promo.expires_at:
        text += f"⏰ {t(lang, 'ADMIN.promo_expires')}: {promo.expires_at.strftime('%d.%m.%Y')}\n"
    if promo.only_new_users:
        text += f"🆕 {t(lang, 'ADMIN.promo_only_new')}\n"
    if bound_user:
        text += f"👤 {t(lang, 'ADMIN.promo_bound_to', user=bound_user.display_name)}\n"
    
    keyboard = [
        [{"text": t(lang, "ADMIN.promo_view"), "callback_data": f"admin:promocodes:view:{promo_id}"}],
        [{"text": t(lang, "ADMIN.promo_create_another"), "callback_data": "admin:promocodes:create"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:promocodes"}]
    ]
    
    await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")


# ==================== EDIT & DELETE ====================

async def edit_promocode(query, lang: str, promo_id: int, field: str = None):
    """Edit promocode"""
    if field == "limits":
        await create_promocode_limits(query, lang, promo_id)
    elif field == "dates":
        await create_promocode_dates(query, lang, promo_id)
    elif field == "binding":
        await create_promocode_binding(query, lang, promo_id)
    else:
        await view_promocode(query, lang, promo_id)


async def promocode_history(query, lang: str, promo_id: int):
    """Show activation history"""
    from core.database.models import PromoCode, PromoCodeActivation, User
    
    async with get_db() as session:
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
        
        result = await session.execute(
            select(PromoCodeActivation, User)
            .join(User, PromoCodeActivation.user_id == User.id)
            .where(PromoCodeActivation.promocode_id == promo_id)
            .order_by(desc(PromoCodeActivation.activated_at))
            .limit(20)
        )
        activations = result.all()
    
    if not promo:
        await query.answer(t(lang, "ADMIN.promocodes_not_found"), show_alert=True)
        return
    
    text = t(lang, "ADMIN.promo_history_title", code=promo.code) + "\n\n"
    
    if not activations:
        text += t(lang, "ADMIN.promo_no_activations")
    else:
        for activation, user in activations:
            date = activation.activated_at.strftime('%d.%m %H:%M')
            text += f"• {date} — {user.display_name}\n"
    
    keyboard = [[{"text": t(lang, "COMMON.back"), "callback_data": f"admin:promocodes:view:{promo_id}"}]]
    await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")


async def delete_promocode(query, lang: str, promo_id: int):
    """Confirm delete"""
    from core.database.models import PromoCode
    
    async with get_db() as session:
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
    
    if not promo:
        await query.answer(t(lang, "ADMIN.promocodes_not_found"), show_alert=True)
        return
    
    text = t(lang, "ADMIN.promo_delete_confirm", code=promo.code)
    keyboard = [
        [{"text": t(lang, "ADMIN.promo_delete_yes"), "callback_data": f"admin:promocodes:delete_confirm:{promo_id}"}],
        [{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:promocodes:view:{promo_id}"}]
    ]
    await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")


async def delete_promocode_confirm(query, lang: str, promo_id: int):
    """Delete promocode"""
    from core.database.models import PromoCode
    
    async with get_db() as session:
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
        if promo:
            await session.delete(promo)
    
    await query.answer(t(lang, "ADMIN.promo_deleted"), show_alert=True)
    await promocodes_main(query, lang)


# ==================== MESSAGE HANDLERS ====================

async def handle_promo_custom_code(update, context, admin_id: int, lang: str, promo_id: int):
    """Handle custom code input"""
    from core.database.models import PromoCode
    from core.plugins.core_api import CoreAPI
    
    core_api = CoreAPI("core")
    code = update.message.text.strip().upper()
    
    if len(code) < 3 or len(code) > 20:
        await update.message.reply_text(t(lang, "ADMIN.promo_code_invalid_length"))
        return
    
    async with get_db() as session:
        result = await session.execute(select(PromoCode).where(PromoCode.code == code, PromoCode.id != promo_id))
        if result.scalar_one_or_none():
            await update.message.reply_text(t(lang, "ADMIN.promo_code_exists"))
            return
        
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
        if promo:
            promo.code = code
    
    await core_api.clear_user_state(admin_id)
    keyboard = [[{"text": t(lang, "ADMIN.promo_continue"), "callback_data": f"admin:promocodes:create_limits:{promo_id}"}]]
    await update.message.reply_text(t(lang, "ADMIN.promo_code_set", code=code), reply_markup=build_keyboard(keyboard), parse_mode="HTML")


async def handle_promo_bind_user(update, context, admin_id: int, lang: str, promo_id: int):
    """Handle user binding"""
    from core.database.models import PromoCode, User
    from core.plugins.core_api import CoreAPI
    
    core_api = CoreAPI("core")
    user_input = update.message.text.strip()
    
    async with get_db() as session:
        user = None
        if user_input.isdigit():
            result = await session.execute(select(User).where(User.id == int(user_input)))
            user = result.scalar_one_or_none()
            if not user:
                result = await session.execute(select(User).where(User.telegram_id == int(user_input)))
                user = result.scalar_one_or_none()
        elif user_input.startswith("@"):
            result = await session.execute(select(User).where(User.telegram_username.ilike(user_input[1:])))
            user = result.scalar_one_or_none()
        
        if not user:
            await update.message.reply_text(t(lang, "ADMIN.promo_user_not_found"))
            return
        
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
        if promo:
            promo.bound_user_id = user.id
    
    await core_api.clear_user_state(admin_id)
    keyboard = [[{"text": t(lang, "ADMIN.promo_continue"), "callback_data": f"admin:promocodes:create_confirm:{promo_id}"}]]
    await update.message.reply_text(t(lang, "ADMIN.promo_user_bound", user=user.display_name), reply_markup=build_keyboard(keyboard), parse_mode="HTML")


async def handle_promo_bind_partner(update, context, admin_id: int, lang: str, promo_id: int):
    """Handle partner binding"""
    from core.database.models import PromoCode, Partner, User
    from core.plugins.core_api import CoreAPI
    
    core_api = CoreAPI("core")
    partner_input = update.message.text.strip()
    
    async with get_db() as session:
        partner = None
        partner_user = None
        
        if partner_input.isdigit():
            # Try partner ID first
            result = await session.execute(
                select(Partner, User).join(User, Partner.user_id == User.id)
                .where(Partner.id == int(partner_input))
            )
            row = result.first()
            if row:
                partner, partner_user = row
            
            # Try user ID
            if not partner:
                result = await session.execute(
                    select(Partner, User).join(User, Partner.user_id == User.id)
                    .where(User.id == int(partner_input))
                )
                row = result.first()
                if row:
                    partner, partner_user = row
            
            # Try telegram ID
            if not partner:
                result = await session.execute(
                    select(Partner, User).join(User, Partner.user_id == User.id)
                    .where(User.telegram_id == int(partner_input))
                )
                row = result.first()
                if row:
                    partner, partner_user = row
                    
        elif partner_input.startswith("@"):
            result = await session.execute(
                select(Partner, User).join(User, Partner.user_id == User.id)
                .where(User.telegram_username.ilike(partner_input[1:]))
            )
            row = result.first()
            if row:
                partner, partner_user = row
        
        if not partner:
            await update.message.reply_text(t(lang, "ADMIN.promo_partner_not_found"))
            return
        
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalar_one_or_none()
        if promo:
            promo.partner_id = partner.id
    
    await core_api.clear_user_state(admin_id)
    keyboard = [[{"text": t(lang, "ADMIN.promo_continue"), "callback_data": f"admin:promocodes:create_confirm:{promo_id}"}]]
    await update.message.reply_text(
        t(lang, "ADMIN.promo_partner_bound", partner=partner_user.display_name), 
        reply_markup=build_keyboard(keyboard), 
        parse_mode="HTML"
    )
