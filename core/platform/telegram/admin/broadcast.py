"""
Admin Broadcast - Full Implementation
"""
import asyncio
import html
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc, and_, or_

from core.locales import t
from core.database import get_db
from core.platform.telegram.utils import build_keyboard

# Bot instance for sending
_bot = None

# Pagination
ITEMS_PER_PAGE = 10


async def get_user_id_by_telegram_id(telegram_id: int) -> int:
    """Get user_id by telegram_id"""
    from core.database.models import User
    async with get_db() as session:
        result = await session.execute(
            select(User.id).where(User.telegram_id == telegram_id)
        )
        return result.scalar()

# Target audience keys
AUDIENCE_KEYS = ["all", "active_7d", "active_30d", "with_balance", "with_subscription", "new_week", "inactive_30d"]


def get_audiences(lang: str) -> dict:
    """Get localized target audiences"""
    return {
        "all": (t(lang, "ADMIN.audience_all"), None),
        "active_7d": (t(lang, "ADMIN.audience_active_7d"), 7),
        "active_30d": (t(lang, "ADMIN.audience_active_30d"), 30),
        "with_balance": (t(lang, "ADMIN.audience_with_balance"), None),
        "with_subscription": (t(lang, "ADMIN.audience_with_subscription"), None),
        "new_week": (t(lang, "ADMIN.audience_new_week"), None),
        "inactive_30d": (t(lang, "ADMIN.audience_inactive_30d"), None),
    }

# Trigger types with default conditions (keys only, labels from localization)
TRIGGER_TYPES_CONFIG = {
    "low_balance": {
        "default_conditions": {"balance_less_than": 100},
        "condition_keys": ["balance_less_than"],
    },
    "subscription_expiring": {
        "default_conditions": {"days_before_expiry": 3},
        "condition_keys": ["days_before_expiry"],
    },
    "subscription_expired": {
        "default_conditions": {"hours_after_expiry": 1},
        "condition_keys": ["hours_after_expiry"],
    },
    "inactive": {
        "default_conditions": {"inactive_days": 7, "exclude_new_users_days": 3},
        "condition_keys": ["inactive_days", "exclude_new_users_days"],
    },
    "welcome": {
        "default_conditions": {"hours_after_registration": 24, "only_if_inactive": True},
        "condition_keys": ["hours_after_registration", "only_if_inactive"],
    },
    "after_deposit": {
        "default_conditions": {"min_amount": 0, "first_deposit_only": False},
        "condition_keys": ["min_amount", "first_deposit_only"],
    },
}


def get_trigger_type_info(trigger_type: str, lang: str = "ru") -> dict:
    """Get localized trigger type info"""
    config = TRIGGER_TYPES_CONFIG.get(trigger_type, {})
    
    # Localized labels
    type_labels = {
        "low_balance": t(lang, "ADMIN.trigger_type_low_balance"),
        "subscription_expiring": t(lang, "ADMIN.trigger_type_subscription_expiring"),
        "subscription_expired": t(lang, "ADMIN.trigger_type_subscription_expired"),
        "inactive": t(lang, "ADMIN.trigger_type_inactive"),
        "welcome": t(lang, "ADMIN.trigger_type_welcome"),
        "after_deposit": t(lang, "ADMIN.trigger_type_after_deposit"),
    }
    
    type_descs = {
        "low_balance": t(lang, "ADMIN.trigger_type_low_balance_desc"),
        "subscription_expiring": t(lang, "ADMIN.trigger_type_subscription_expiring_desc"),
        "subscription_expired": t(lang, "ADMIN.trigger_type_subscription_expired_desc"),
        "inactive": t(lang, "ADMIN.trigger_type_inactive_desc"),
        "welcome": t(lang, "ADMIN.trigger_type_welcome_desc"),
        "after_deposit": t(lang, "ADMIN.trigger_type_after_deposit_desc"),
    }
    
    # Condition labels
    cond_labels = {
        "balance_less_than": t(lang, "ADMIN.cond_balance_less_than"),
        "days_before_expiry": t(lang, "ADMIN.cond_days_before_expiry"),
        "hours_after_expiry": t(lang, "ADMIN.cond_hours_after_expiry"),
        "inactive_days": t(lang, "ADMIN.cond_inactive_days"),
        "exclude_new_users_days": t(lang, "ADMIN.cond_exclude_new_users_days"),
        "hours_after_registration": t(lang, "ADMIN.cond_hours_after_registration"),
        "only_if_inactive": t(lang, "ADMIN.cond_only_if_inactive"),
        "min_amount": t(lang, "ADMIN.cond_min_amount"),
        "first_deposit_only": t(lang, "ADMIN.cond_first_deposit_only"),
    }
    
    return {
        "label": type_labels.get(trigger_type, trigger_type),
        "description": type_descs.get(trigger_type, ""),
        "default_conditions": config.get("default_conditions", {}),
        "condition_labels": {k: cond_labels.get(k, k) for k in config.get("condition_keys", [])},
    }


def set_bot(bot):
    """Set bot instance for sending"""
    global _bot
    _bot = bot


async def admin_broadcast(query, lang: str, action: str = None, params: str = None):
    """Admin broadcast handler"""
    if action == "create":
        await broadcast_create(query, lang)
    elif action == "target":
        await broadcast_select_target(query, lang, params)
    elif action == "preview":
        await broadcast_preview(query, lang, params)
    elif action == "send":
        await broadcast_send(query, lang, int(params) if params else None)
    elif action == "schedule":
        await broadcast_schedule(query, lang, int(params) if params else None)
    elif action == "ab_test":
        await broadcast_ab_setup(query, lang, int(params) if params else None)
    elif action == "add_button":
        await broadcast_add_button(query, lang, int(params) if params else None)
    elif action == "add_media":
        await broadcast_add_media(query, lang, int(params) if params else None)
    elif action == "history":
        page = int(params) if params and params.isdigit() else 0
        await broadcast_history(query, lang, page)
    elif action == "view":
        await broadcast_view(query, lang, int(params) if params else None)
    elif action == "pause":
        await broadcast_pause(query, lang, int(params) if params else None)
    elif action == "resume":
        await broadcast_resume(query, lang, int(params) if params else None)
    elif action == "cancel":
        await broadcast_cancel(query, lang, int(params) if params else None)
    elif action == "triggers":
        await triggers_main(query, lang)
    elif action == "trigger_create":
        await trigger_create(query, lang, params)
    elif action == "trigger_view":
        await trigger_view(query, lang, int(params) if params else None)
    elif action == "trigger_toggle":
        await trigger_toggle(query, lang, int(params) if params else None)
    elif action == "trigger_delete":
        await trigger_delete(query, lang, int(params) if params else None)
    elif action == "trigger_edit":
        # params format: trigger_id:field (e.g., "1:text", "1:conditions")
        if params and ":" in params:
            trigger_id, field = params.split(":", 1)
            await trigger_edit(query, lang, int(trigger_id), field)
        else:
            await trigger_view(query, lang, int(params) if params else None)
    elif action == "trigger_cond":
        # params format: trigger_id:param_name (e.g., "1:balance_less_than")
        if params and ":" in params:
            trigger_id, param = params.split(":", 1)
            await trigger_edit_condition(query, lang, int(trigger_id), param)
    elif action == "trigger_behavior":
        # params format: trigger_id:param_name
        if params and ":" in params:
            trigger_id, param = params.split(":", 1)
            await trigger_edit_behavior(query, lang, int(trigger_id), param)
    elif action == "trigger_send":
        await trigger_send_now(query, lang, int(params) if params else None)
    elif action == "coming_soon":
        await query.answer(t(lang, "ADMIN.broadcast_coming_soon"), show_alert=True)
    else:
        await broadcast_main(query, lang)


async def broadcast_main(query, lang: str):
    """Broadcast main menu"""
    from core.database.models import User, Broadcast, BroadcastTrigger
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    async with get_db() as session:
        # Total users
        result = await session.execute(
            select(func.count(User.id)).where(User.is_blocked == False)
        )
        total_users = result.scalar() or 0
        
        # Sent today
        result = await session.execute(
            select(func.sum(Broadcast.sent_count)).where(
                Broadcast.started_at >= today,
                Broadcast.status == "completed"
            )
        )
        sent_today = result.scalar() or 0
        
        # Delivered today
        result = await session.execute(
            select(func.sum(Broadcast.delivered_count)).where(
                Broadcast.started_at >= today,
                Broadcast.status == "completed"
            )
        )
        delivered_today = result.scalar() or 0
        
        # Active triggers
        result = await session.execute(
            select(func.count(BroadcastTrigger.id)).where(BroadcastTrigger.is_active == True)
        )
        active_triggers = result.scalar() or 0
        
        # Scheduled broadcasts
        result = await session.execute(
            select(func.count(Broadcast.id)).where(Broadcast.status == "scheduled")
        )
        scheduled_count = result.scalar() or 0
    
    delivery_rate = (delivered_today / sent_today * 100) if sent_today > 0 else 0
    
    text = t(lang, "ADMIN.broadcast_title") + "\n\n"
    text += t(lang, "ADMIN.broadcast_stats") + "\n"
    text += f"├── " + t(lang, "ADMIN.broadcast_sent_today", count=sent_today) + "\n"
    text += f"├── " + t(lang, "ADMIN.broadcast_delivered", count=delivered_today, percent=f"{delivery_rate:.0f}") + "\n"
    text += f"├── " + t(lang, "ADMIN.broadcast_triggers_active", count=active_triggers) + "\n"
    text += f"└── " + t(lang, "ADMIN.broadcast_scheduled", count=scheduled_count) + "\n"
    
    keyboard = [
        [{"text": t(lang, "ADMIN.broadcast_create"), "callback_data": "admin:broadcast:create"}],
        [{"text": t(lang, "ADMIN.broadcast_history"), "callback_data": "admin:broadcast:history"}],
        [{"text": t(lang, "ADMIN.broadcast_triggers"), "callback_data": "admin:broadcast:triggers"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def broadcast_create(query, lang: str):
    """Start creating broadcast - enter text"""
    from core.plugins.core_api import CoreAPI
    
    admin_id = await get_user_id_by_telegram_id(query.from_user.id)
    core_api = CoreAPI("core")
    await core_api.set_user_state(admin_id, "admin_broadcast_text")
    
    text = t(lang, "ADMIN.broadcast_create_title") + "\n\n"
    text += t(lang, "ADMIN.broadcast_create_prompt") + "\n\n"
    text += t(lang, "ADMIN.broadcast_create_hint")
    
    keyboard = [
        [{"text": t(lang, "COMMON.cancel"), "callback_data": "admin:broadcast"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def broadcast_select_target(query, lang: str, broadcast_id: str):
    """Select target audience"""
    from core.database.models import User, Wallet, Subscription
    
    broadcast_id = int(broadcast_id) if broadcast_id else None
    
    async with get_db() as session:
        counts = {}
        now = datetime.utcnow()
        
        # All users
        result = await session.execute(
            select(func.count(User.id)).where(User.is_blocked == False)
        )
        counts["all"] = result.scalar() or 0
        
        # Active 7 days
        result = await session.execute(
            select(func.count(User.id)).where(
                User.is_blocked == False,
                User.last_activity_at >= now - timedelta(days=7)
            )
        )
        counts["active_7d"] = result.scalar() or 0
        
        # Active 30 days
        result = await session.execute(
            select(func.count(User.id)).where(
                User.is_blocked == False,
                User.last_activity_at >= now - timedelta(days=30)
            )
        )
        counts["active_30d"] = result.scalar() or 0
        
        # With balance
        result = await session.execute(
            select(func.count(func.distinct(Wallet.user_id))).where(Wallet.balance > 0)
        )
        counts["with_balance"] = result.scalar() or 0
        
        # With subscription
        result = await session.execute(
            select(func.count(func.distinct(Subscription.user_id))).where(
                Subscription.is_active == True,
                Subscription.expires_at > now
            )
        )
        counts["with_subscription"] = result.scalar() or 0
        
        # New this week
        result = await session.execute(
            select(func.count(User.id)).where(
                User.is_blocked == False,
                User.created_at >= now - timedelta(days=7)
            )
        )
        counts["new_week"] = result.scalar() or 0
        
        # Inactive 30+ days
        result = await session.execute(
            select(func.count(User.id)).where(
                User.is_blocked == False,
                User.last_activity_at < now - timedelta(days=30)
            )
        )
        counts["inactive_30d"] = result.scalar() or 0
    
    text = t(lang, "ADMIN.broadcast_select_target") + "\n\n"
    text += t(lang, "ADMIN.broadcast_select_target_hint")
    
    audiences = get_audiences(lang)
    keyboard = []
    for key in AUDIENCE_KEYS:
        label, _ = audiences.get(key, (key, None))
        count = counts.get(key, 0)
        keyboard.append([{
            "text": f"{label} ({count:,})",
            "callback_data": f"admin:broadcast:preview:{broadcast_id}_{key}"
        }])
    
    keyboard.append([{"text": t(lang, "COMMON.cancel"), "callback_data": "admin:broadcast"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def broadcast_preview(query, lang: str, params):
    """Preview broadcast before sending"""
    from core.database.models import Broadcast, User
    
    # Parse params: broadcast_id_target
    if isinstance(params, str) and "_" in params:
        parts = params.rsplit("_", 1)
        broadcast_id = int(parts[0])
        target = parts[1]
    else:
        broadcast_id = params
        target = "all"
    
    async with get_db() as session:
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
        
        if not broadcast:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        # Update target
        broadcast.target = target
        
        # Count recipients
        recipients = await get_audience_count(session, target)
        broadcast.total_recipients = recipients
    
    text = t(lang, "ADMIN.broadcast_preview_title") + "\n\n"
    text += t(lang, "ADMIN.broadcast_preview_text") + "\n"
    text += "─" * 20 + "\n"
    text += broadcast.text[:500]
    if len(broadcast.text) > 500:
        text += "..."
    text += "\n" + "─" * 20 + "\n\n"
    
    audiences = get_audiences(lang)
    audience_label = audiences.get(target, (target, None))[0]
    text += t(lang, "ADMIN.broadcast_preview_target", target=audience_label) + "\n"
    text += t(lang, "ADMIN.broadcast_preview_recipients", count=recipients) + "\n"
    
    if broadcast.media_type:
        text += t(lang, "ADMIN.broadcast_preview_media", type=broadcast.media_type) + "\n"
    
    if broadcast.buttons:
        text += t(lang, "ADMIN.broadcast_preview_buttons", count=len(broadcast.buttons)) + "\n"
    
    keyboard = [
        [{"text": t(lang, "ADMIN.broadcast_send_now"), "callback_data": f"admin:broadcast:send:{broadcast_id}"}],
        [
            {"text": t(lang, "ADMIN.broadcast_schedule"), "callback_data": f"admin:broadcast:schedule:{broadcast_id}"},
            {"text": t(lang, "ADMIN.broadcast_ab_test"), "callback_data": "admin:broadcast:coming_soon"}
        ],
        [
            {"text": t(lang, "ADMIN.broadcast_add_button"), "callback_data": f"admin:broadcast:add_button:{broadcast_id}"},
            {"text": t(lang, "ADMIN.broadcast_add_media"), "callback_data": f"admin:broadcast:add_media:{broadcast_id}"}
        ],
        [{"text": t(lang, "COMMON.cancel"), "callback_data": "admin:broadcast"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def broadcast_send(query, lang: str, broadcast_id: int):
    """Start sending broadcast"""
    from core.database.models import Broadcast
    
    async with get_db() as session:
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
        
        if not broadcast:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        broadcast.status = "sending"
        broadcast.started_at = datetime.utcnow()
    
    await query.answer(t(lang, "ADMIN.broadcast_started"), show_alert=True)
    
    # Start sending in background
    asyncio.create_task(send_broadcast(broadcast_id))
    
    await broadcast_view(query, lang, broadcast_id)


async def send_broadcast(broadcast_id: int):
    """Background task to send broadcast"""
    from core.database.models import Broadcast, User, BroadcastRecipient
    
    global _bot
    if not _bot:
        return
    
    async with get_db() as session:
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
        
        if not broadcast or broadcast.status != "sending":
            return
        
        # Get recipients
        users = await get_audience_users(session, broadcast.target)
        
        for user in users:
            if broadcast.status == "paused":
                break
            
            try:
                # Build keyboard if buttons exist
                reply_markup = None
                if broadcast.buttons:
                    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
                    keyboard = []
                    for row in broadcast.buttons:
                        btn_row = []
                        for btn in row:
                            if "url" in btn:
                                btn_row.append(InlineKeyboardButton(text=btn["text"], url=btn["url"]))
                            elif "callback_data" in btn:
                                btn_row.append(InlineKeyboardButton(text=btn["text"], callback_data=btn["callback_data"]))
                        keyboard.append(btn_row)
                    reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Personalize text
                text = broadcast.text
                text = text.replace("{name}", user.display_name)
                text = text.replace("{username}", f"@{user.telegram_username}" if user.telegram_username else "")
                
                # Send based on media type
                if broadcast.media_type == "photo":
                    await _bot.send_photo(
                        chat_id=user.telegram_id,
                        photo=broadcast.media_file_id,
                        caption=text,
                        parse_mode=broadcast.parse_mode,
                        reply_markup=reply_markup
                    )
                elif broadcast.media_type == "video":
                    await _bot.send_video(
                        chat_id=user.telegram_id,
                        video=broadcast.media_file_id,
                        caption=text,
                        parse_mode=broadcast.parse_mode,
                        reply_markup=reply_markup
                    )
                elif broadcast.media_type == "animation":
                    await _bot.send_animation(
                        chat_id=user.telegram_id,
                        animation=broadcast.media_file_id,
                        caption=text,
                        parse_mode=broadcast.parse_mode,
                        reply_markup=reply_markup
                    )
                else:
                    await _bot.send_message(
                        chat_id=user.telegram_id,
                        text=text,
                        parse_mode=broadcast.parse_mode,
                        reply_markup=reply_markup
                    )
                
                broadcast.sent_count += 1
                broadcast.delivered_count += 1
                
            except Exception as e:
                broadcast.sent_count += 1
                broadcast.failed_count += 1
            
            # Rate limiting
            await asyncio.sleep(1 / broadcast.send_rate)
        
        # Complete
        if broadcast.status == "sending":
            broadcast.status = "completed"
            broadcast.completed_at = datetime.utcnow()


async def get_audience_count(session, target: str) -> int:
    """Get count of users in target audience"""
    from core.database.models import User, Wallet, Subscription
    
    now = datetime.utcnow()
    
    if target == "all":
        result = await session.execute(
            select(func.count(User.id)).where(User.is_blocked == False)
        )
    elif target == "active_7d":
        result = await session.execute(
            select(func.count(User.id)).where(
                User.is_blocked == False,
                User.last_activity_at >= now - timedelta(days=7)
            )
        )
    elif target == "active_30d":
        result = await session.execute(
            select(func.count(User.id)).where(
                User.is_blocked == False,
                User.last_activity_at >= now - timedelta(days=30)
            )
        )
    elif target == "with_balance":
        result = await session.execute(
            select(func.count(func.distinct(Wallet.user_id))).where(Wallet.balance > 0)
        )
    elif target == "with_subscription":
        result = await session.execute(
            select(func.count(func.distinct(Subscription.user_id))).where(
                Subscription.is_active == True,
                Subscription.expires_at > now
            )
        )
    elif target == "new_week":
        result = await session.execute(
            select(func.count(User.id)).where(
                User.is_blocked == False,
                User.created_at >= now - timedelta(days=7)
            )
        )
    elif target == "inactive_30d":
        result = await session.execute(
            select(func.count(User.id)).where(
                User.is_blocked == False,
                User.last_activity_at < now - timedelta(days=30)
            )
        )
    else:
        result = await session.execute(
            select(func.count(User.id)).where(User.is_blocked == False)
        )
    
    return result.scalar() or 0


async def get_audience_users(session, target: str):
    """Get users in target audience"""
    from core.database.models import User, Wallet, Subscription
    
    now = datetime.utcnow()
    
    if target == "all":
        result = await session.execute(
            select(User).where(User.is_blocked == False)
        )
    elif target == "active_7d":
        result = await session.execute(
            select(User).where(
                User.is_blocked == False,
                User.last_activity_at >= now - timedelta(days=7)
            )
        )
    elif target == "active_30d":
        result = await session.execute(
            select(User).where(
                User.is_blocked == False,
                User.last_activity_at >= now - timedelta(days=30)
            )
        )
    elif target == "new_week":
        result = await session.execute(
            select(User).where(
                User.is_blocked == False,
                User.created_at >= now - timedelta(days=7)
            )
        )
    elif target == "inactive_30d":
        result = await session.execute(
            select(User).where(
                User.is_blocked == False,
                User.last_activity_at < now - timedelta(days=30)
            )
        )
    else:
        result = await session.execute(
            select(User).where(User.is_blocked == False)
        )
    
    return result.scalars().all()


async def broadcast_history(query, lang: str, page: int = 0):
    """Broadcast history with pagination"""
    from core.database.models import Broadcast
    
    async with get_db() as session:
        # Count
        result = await session.execute(
            select(func.count(Broadcast.id))
        )
        total = result.scalar() or 0
        
        total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        page = max(0, min(page, total_pages - 1))
        
        # Get broadcasts
        result = await session.execute(
            select(Broadcast).order_by(desc(Broadcast.created_at))
            .offset(page * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE)
        )
        broadcasts = result.scalars().all()
    
    status_icons = {
        "completed": "✅",
        "sending": "📤",
        "paused": "⏸",
        "scheduled": "📅",
        "cancelled": "❌",
        "draft": "📝"
    }
    
    text = t(lang, "ADMIN.broadcast_history_title") + "\n\n"
    
    if total_pages > 1:
        text += t(lang, "ADMIN.page_info", current=page + 1, total=total_pages) + "\n\n"
    
    if not broadcasts:
        text += t(lang, "ADMIN.broadcast_history_empty")
    else:
        for bc in broadcasts:
            icon = status_icons.get(bc.status, "❓")
            date = bc.created_at.strftime("%d.%m %H:%M")
            name = bc.name or bc.text[:30] + "..."
            
            delivery = f"{bc.delivered_count}/{bc.sent_count}" if bc.sent_count > 0 else "-"
            text += f"{icon} {date} — {name}\n"
            text += f"   📤 {delivery}\n"
    
    keyboard = []
    
    # Broadcast buttons
    for bc in broadcasts[:5]:
        name = bc.name or bc.text[:20] + "..."
        keyboard.append([{
            "text": f"📋 {name}",
            "callback_data": f"admin:broadcast:view:{bc.id}"
        }])
    
    # Pagination
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append({"text": t(lang, "ADMIN.page_prev"), "callback_data": f"admin:broadcast:history:{page - 1}"})
        if page < total_pages - 1:
            pagination.append({"text": t(lang, "ADMIN.page_next"), "callback_data": f"admin:broadcast:history:{page + 1}"})
        if pagination:
            keyboard.append(pagination)
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:broadcast"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def broadcast_view(query, lang: str, broadcast_id: int):
    """View broadcast details"""
    from core.database.models import Broadcast
    
    async with get_db() as session:
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
    
    if not broadcast:
        await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
        return
    
    status_key = f"broadcast_status_{broadcast.status}"
    status_text = t(lang, f"ADMIN.{status_key}")
    
    text = t(lang, "ADMIN.broadcast_view_title", id=broadcast.id) + "\n\n"
    text += t(lang, "ADMIN.broadcast_status", status=status_text) + "\n"
    text += t(lang, "ADMIN.broadcast_created_at", date=broadcast.created_at.strftime('%d.%m.%Y %H:%M')) + "\n"
    
    if broadcast.started_at:
        text += t(lang, "ADMIN.broadcast_started_at", date=broadcast.started_at.strftime('%d.%m.%Y %H:%M')) + "\n"
    
    if broadcast.completed_at:
        text += t(lang, "ADMIN.broadcast_completed_at", date=broadcast.completed_at.strftime('%d.%m.%Y %H:%M')) + "\n"
    
    text += "\n" + t(lang, "ADMIN.broadcast_sent_count", sent=broadcast.sent_count, total=broadcast.total_recipients) + "\n"
    text += t(lang, "ADMIN.broadcast_delivered_count", count=broadcast.delivered_count) + "\n"
    text += t(lang, "ADMIN.broadcast_failed_count", count=broadcast.failed_count) + "\n"
    
    if broadcast.sent_count > 0:
        rate = broadcast.delivered_count / broadcast.sent_count * 100
        text += t(lang, "ADMIN.broadcast_delivery_rate", rate=f"{rate:.1f}") + "\n"
    
    text += "\n" + t(lang, "ADMIN.broadcast_text_preview") + f"\n{broadcast.text[:200]}..."
    
    keyboard = []
    
    if broadcast.status == "sending":
        keyboard.append([{"text": t(lang, "ADMIN.broadcast_pause"), "callback_data": f"admin:broadcast:pause:{broadcast.id}"}])
    elif broadcast.status == "paused":
        keyboard.append([
            {"text": t(lang, "ADMIN.broadcast_resume"), "callback_data": f"admin:broadcast:resume:{broadcast.id}"},
            {"text": t(lang, "ADMIN.broadcast_cancel"), "callback_data": f"admin:broadcast:cancel:{broadcast.id}"}
        ])
    elif broadcast.status == "scheduled":
        keyboard.append([{"text": t(lang, "ADMIN.broadcast_cancel"), "callback_data": f"admin:broadcast:cancel:{broadcast.id}"}])
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:broadcast:history"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def broadcast_pause(query, lang: str, broadcast_id: int):
    """Pause sending broadcast"""
    from core.database.models import Broadcast
    
    async with get_db() as session:
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
        
        if broadcast and broadcast.status == "sending":
            broadcast.status = "paused"
    
    await query.answer(t(lang, "ADMIN.broadcast_paused"), show_alert=True)
    await broadcast_view(query, lang, broadcast_id)


async def broadcast_resume(query, lang: str, broadcast_id: int):
    """Resume paused broadcast"""
    from core.database.models import Broadcast
    
    async with get_db() as session:
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
        
        if broadcast and broadcast.status == "paused":
            broadcast.status = "sending"
    
    asyncio.create_task(send_broadcast(broadcast_id))
    
    await query.answer(t(lang, "ADMIN.broadcast_resumed"), show_alert=True)
    await broadcast_view(query, lang, broadcast_id)


async def broadcast_cancel(query, lang: str, broadcast_id: int):
    """Cancel broadcast"""
    from core.database.models import Broadcast
    
    async with get_db() as session:
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
        
        if broadcast:
            broadcast.status = "cancelled"
    
    await query.answer(t(lang, "ADMIN.broadcast_cancelled"), show_alert=True)
    await broadcast_history(query, lang)


async def broadcast_schedule(query, lang: str, broadcast_id: int):
    """Schedule broadcast for later"""
    from core.plugins.core_api import CoreAPI
    
    admin_id = await get_user_id_by_telegram_id(query.from_user.id)
    core_api = CoreAPI("core")
    await core_api.set_user_state(admin_id, "admin_broadcast_schedule", {"broadcast_id": broadcast_id})
    
    text = t(lang, "ADMIN.broadcast_schedule_title") + "\n\n"
    text += t(lang, "ADMIN.broadcast_schedule_prompt") + "\n\n"
    text += t(lang, "ADMIN.broadcast_schedule_format")
    
    keyboard = [
        [{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:broadcast:preview:{broadcast_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def broadcast_ab_setup(query, lang: str, broadcast_id: int):
    """Setup A/B test"""
    from core.plugins.core_api import CoreAPI
    
    admin_id = await get_user_id_by_telegram_id(query.from_user.id)
    core_api = CoreAPI("core")
    await core_api.set_user_state(admin_id, "admin_broadcast_ab_text", {"broadcast_id": broadcast_id})
    
    text = t(lang, "ADMIN.broadcast_ab_title") + "\n\n"
    text += t(lang, "ADMIN.broadcast_ab_prompt")
    
    keyboard = [
        [{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:broadcast:preview:{broadcast_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def broadcast_add_button(query, lang: str, broadcast_id: int):
    """Add button to broadcast"""
    from core.plugins.core_api import CoreAPI
    
    admin_id = await get_user_id_by_telegram_id(query.from_user.id)
    core_api = CoreAPI("core")
    await core_api.set_user_state(admin_id, "admin_broadcast_button", {"broadcast_id": broadcast_id})
    
    text = t(lang, "ADMIN.broadcast_button_title") + "\n\n"
    text += t(lang, "ADMIN.broadcast_button_prompt") + "\n\n"
    text += t(lang, "ADMIN.broadcast_button_format")
    
    keyboard = [
        [{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:broadcast:preview:{broadcast_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def broadcast_add_media(query, lang: str, broadcast_id: int):
    """Add media to broadcast"""
    from core.plugins.core_api import CoreAPI
    
    admin_id = await get_user_id_by_telegram_id(query.from_user.id)
    core_api = CoreAPI("core")
    await core_api.set_user_state(admin_id, "admin_broadcast_media", {"broadcast_id": broadcast_id})
    
    text = t(lang, "ADMIN.broadcast_media_title") + "\n\n"
    text += t(lang, "ADMIN.broadcast_media_prompt")
    
    keyboard = [
        [{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:broadcast:preview:{broadcast_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


# ==================== TRIGGERS ====================


async def triggers_main(query, lang: str):
    """Triggers main menu"""
    from core.database.models import BroadcastTrigger
    
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).order_by(desc(BroadcastTrigger.created_at))
        )
        triggers = result.scalars().all()
    
    text = t(lang, "ADMIN.triggers_title") + "\n\n"
    
    if not triggers:
        text += t(lang, "ADMIN.triggers_empty") + "\n\n"
        text += t(lang, "ADMIN.triggers_auto_desc")
    else:
        active_count = sum(1 for tr in triggers if tr.is_active)
        text += t(lang, "ADMIN.triggers_stats", total=len(triggers), active=active_count) + "\n\n"
        
        for trigger in triggers[:10]:
            status = "✅" if trigger.is_active else "⏸"
            type_info = get_trigger_type_info(trigger.trigger_type, lang)
            # Use localized type label instead of stored name
            display_name = type_info['label']
            text += f"{status} <b>{display_name}</b>\n"
            text += f"    {t(lang, 'ADMIN.trigger_stats_sent')}: {trigger.total_sent}\n"
    
    keyboard = []
    
    # Trigger buttons - use localized type labels
    for trigger in triggers[:8]:
        status = "✅" if trigger.is_active else "⏸"
        type_info = get_trigger_type_info(trigger.trigger_type, lang)
        display_name = type_info['label']
        keyboard.append([{
            "text": f"{status} {display_name[:30]}",
            "callback_data": f"admin:broadcast:trigger_view:{trigger.id}"
        }])
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:broadcast"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def trigger_create(query, lang: str, trigger_type: str = None):
    """Create new trigger"""
    if not trigger_type:
        # Show trigger type selection
        text = t(lang, "ADMIN.trigger_select_type") + "\n\n"
        
        keyboard = []
        for key in TRIGGER_TYPES_CONFIG.keys():
            type_info = get_trigger_type_info(key, lang)
            keyboard.append([{
                "text": type_info["label"],
                "callback_data": f"admin:broadcast:trigger_create:{key}"
            }])
        
        keyboard.append([{"text": t(lang, "COMMON.cancel"), "callback_data": "admin:broadcast:triggers"}])
        
        await query.edit_message_text(
            text,
            reply_markup=build_keyboard(keyboard),
            parse_mode="HTML"
        )
    else:
        # Start creating trigger
        from core.plugins.core_api import CoreAPI
        
        admin_id = await get_user_id_by_telegram_id(query.from_user.id)
        core_api = CoreAPI("core")
        await core_api.set_user_state(admin_id, "admin_trigger_name", {"trigger_type": trigger_type})
        
        type_info = get_trigger_type_info(trigger_type, lang)
        
        text = t(lang, "ADMIN.trigger_create_title", type=type_info['label']) + "\n\n"
        text += f"📝 {type_info['description']}\n\n"
        text += t(lang, "ADMIN.trigger_enter_name")
        
        keyboard = [
            [{"text": t(lang, "COMMON.cancel"), "callback_data": "admin:broadcast:triggers"}]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=build_keyboard(keyboard),
            parse_mode="HTML"
        )


async def trigger_send_now(query, lang: str, trigger_id: int):
    """Send trigger immediately to matching users"""
    from core.database.models import BroadcastTrigger, User, Wallet
    from core.tasks.triggers import find_matching_users, send_trigger_message
    
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
    
    if not trigger:
        await query.answer(t(lang, "ADMIN.trigger_not_found"), show_alert=True)
        return
    
    await query.answer("🔄...")
    
    # Find matching users
    matching_users = await find_matching_users(trigger)
    
    if not matching_users:
        keyboard = [[{"text": t(lang, "COMMON.back"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}]]
        await query.edit_message_text(
            t(lang, "ADMIN.trigger_no_matching", name=html.escape(trigger.name)),
            reply_markup=build_keyboard(keyboard),
            parse_mode="HTML"
        )
        return
    
    # Send to all matching users
    sent = 0
    failed = 0
    
    for user in matching_users:
        try:
            success = await send_trigger_message(trigger, user, skip_delay=True)
            if success:
                sent += 1
            else:
                failed += 1
        except Exception:
            failed += 1
    
    # Update trigger stats
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
        if trigger:
            trigger.total_sent = (trigger.total_sent or 0) + sent
            trigger.total_delivered = (trigger.total_delivered or 0) + sent
            trigger.last_run_at = datetime.utcnow()
    
    keyboard = [[{"text": t(lang, "COMMON.back"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}]]
    
    await query.edit_message_text(
        t(lang, "ADMIN.trigger_send_complete", name=html.escape(trigger.name), sent=sent, failed=failed),
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def trigger_view(query, lang: str, trigger_id: int):
    """View trigger details with full edit options"""
    from core.database.models import BroadcastTrigger
    
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
    
    if not trigger:
        await query.answer(t(lang, "ADMIN.trigger_not_found"), show_alert=True)
        return
    
    type_info = get_trigger_type_info(trigger.trigger_type, lang)
    status_icon = "✅" if trigger.is_active else "⏸"
    status_text = t(lang, "ADMIN.trigger_status_active") if trigger.is_active else t(lang, "ADMIN.trigger_status_disabled")
    
    # Use localized type label as title
    display_name = type_info['label']
    text = f"⚙️ <b>{display_name}</b>\n\n"
    text += f"📌 {t(lang, 'ADMIN.triggers_type', type=type_info['label'])}\n"
    text += t(lang, "ADMIN.trigger_view_status", status=f"{status_icon} {status_text}") + "\n\n"
    
    # Conditions
    text += f"🎯 <b>{t(lang, 'ADMIN.trigger_conditions')}:</b>\n"
    conditions = trigger.conditions or {}
    condition_labels = type_info.get("condition_labels", {})
    
    for key, value in conditions.items():
        label = condition_labels.get(key, key)
        if isinstance(value, bool):
            value_str = t(lang, "ADMIN.trigger_yes") if value else t(lang, "ADMIN.trigger_no")
        else:
            value_str = str(value)
        text += f"  • {label}: <code>{value_str}</code>\n"
    
    if not conditions:
        text += "  • —\n"
    
    # Behavior
    text += f"\n🔄 <b>{t(lang, 'ADMIN.trigger_edit_behavior_current')}:</b>\n"
    text += f"  • {t(lang, 'ADMIN.behavior_max_sends')}: {trigger.max_sends_per_user or '∞'}\n"
    if trigger.repeat_interval_days > 0:
        text += f"  • {t(lang, 'ADMIN.behavior_repeat_days')}: {trigger.repeat_interval_days}\n"
    else:
        text += f"  • {t(lang, 'ADMIN.behavior_repeat_days')}: —\n"
    text += f"  • {t(lang, 'ADMIN.behavior_send_time')}: {trigger.send_start_hour:02d}:00 - {trigger.send_end_hour:02d}:00\n"
    if trigger.delay_minutes > 0:
        text += f"  • {t(lang, 'ADMIN.behavior_delay')}: {trigger.delay_minutes} min\n"
    
    # Stats
    text += f"\n📈 <b>{t(lang, 'ADMIN.trigger_stats_title')}:</b>\n"
    text += f"  • {t(lang, 'ADMIN.trigger_stats_sent')}: {trigger.total_sent}\n"
    text += f"  • {t(lang, 'ADMIN.trigger_stats_delivered')}: {trigger.total_delivered}"
    if trigger.total_sent > 0:
        rate = trigger.total_delivered / trigger.total_sent * 100
        text += f" ({rate:.1f}%)"
    text += "\n"
    
    # Content preview
    text += f"\n📝 <b>{t(lang, 'ADMIN.trigger_message')}:</b>\n"
    preview = trigger.text[:150].replace("<", "&lt;").replace(">", "&gt;")
    if len(trigger.text) > 150:
        preview += "..."
    text += f"<i>{preview}</i>\n"
    
    if trigger.media_type:
        text += f"\n📎 {t(lang, 'ADMIN.trigger_media')}: {trigger.media_type}\n"
    
    if trigger.buttons:
        text += f"🔘 {t(lang, 'ADMIN.trigger_buttons')}: {len(trigger.buttons)}\n"
    
    # Keyboard
    keyboard = [
        [
            {"text": t(lang, "ADMIN.trigger_btn_text"), "callback_data": f"admin:broadcast:trigger_edit:{trigger_id}:text"},
            {"text": t(lang, "ADMIN.trigger_btn_media"), "callback_data": f"admin:broadcast:trigger_edit:{trigger_id}:media"},
        ],
        [
            {"text": t(lang, "ADMIN.trigger_btn_buttons"), "callback_data": f"admin:broadcast:trigger_edit:{trigger_id}:buttons"},
        ],
        [
            {"text": t(lang, "ADMIN.trigger_btn_conditions"), "callback_data": f"admin:broadcast:trigger_edit:{trigger_id}:conditions"},
            {"text": t(lang, "ADMIN.trigger_btn_behavior"), "callback_data": f"admin:broadcast:trigger_edit:{trigger_id}:behavior"},
        ],
    ]
    
    if trigger.is_active:
        keyboard.append([{"text": t(lang, "ADMIN.trigger_btn_disable"), "callback_data": f"admin:broadcast:trigger_toggle:{trigger_id}"}])
    else:
        keyboard.append([{"text": t(lang, "ADMIN.trigger_btn_enable"), "callback_data": f"admin:broadcast:trigger_toggle:{trigger_id}"}])
    
    keyboard.append([{"text": t(lang, "ADMIN.trigger_send_now"), "callback_data": f"admin:broadcast:trigger_send:{trigger_id}"}])
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:broadcast:triggers"}])
    
    try:
        await query.edit_message_text(
            text,
            reply_markup=build_keyboard(keyboard),
            parse_mode="HTML"
        )
    except Exception:
        pass  # Message not modified


async def trigger_edit(query, lang: str, trigger_id: int, field: str):
    """Edit trigger field"""
    from core.database.models import BroadcastTrigger
    from core.plugins.core_api import CoreAPI
    
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
    
    if not trigger:
        await query.answer(t(lang, "ADMIN.trigger_not_found"), show_alert=True)
        return
    
    type_info = get_trigger_type_info(trigger.trigger_type, lang)
    
    if field == "text":
        admin_id = await get_user_id_by_telegram_id(query.from_user.id)
        core_api = CoreAPI("core")
        await core_api.set_user_state(admin_id, "admin_trigger_edit_text", {"trigger_id": trigger_id})
        
        text = t(lang, "ADMIN.trigger_edit_text_title", name=html.escape(trigger.name))
        text += t(lang, "ADMIN.trigger_edit_text_current")
        text += f"<i>{html.escape(trigger.text[:500])}</i>\n\n"
        text += t(lang, "ADMIN.trigger_edit_text_prompt")
        
        keyboard = [[{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}]]
        
    elif field == "media":
        admin_id = await get_user_id_by_telegram_id(query.from_user.id)
        core_api = CoreAPI("core")
        await core_api.set_user_state(admin_id, "admin_trigger_edit_media", {"trigger_id": trigger_id})
        
        text = t(lang, "ADMIN.trigger_edit_media_title", name=html.escape(trigger.name))
        if trigger.media_type:
            text += t(lang, "ADMIN.trigger_edit_media_current", type=trigger.media_type)
        else:
            text += t(lang, "ADMIN.trigger_edit_media_none")
        text += t(lang, "ADMIN.trigger_edit_media_prompt")
        
        keyboard = [
            [{"text": "🗑 " + t(lang, "ADMIN.trigger_media_removed"), "callback_data": f"admin:broadcast:trigger_edit:{trigger_id}:remove_media"}],
            [{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}]
        ]
        
    elif field == "remove_media":
        async with get_db() as session:
            result = await session.execute(
                select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
            )
            trigger = result.scalar_one_or_none()
            if trigger:
                trigger.media_type = None
                trigger.media_file_id = None
        
        await query.answer(t(lang, "ADMIN.trigger_media_removed"), show_alert=True)
        await trigger_view(query, lang, trigger_id)
        return
        
    elif field == "buttons":
        admin_id = await get_user_id_by_telegram_id(query.from_user.id)
        core_api = CoreAPI("core")
        await core_api.set_user_state(admin_id, "admin_trigger_edit_button", {"trigger_id": trigger_id})
        
        text = t(lang, "ADMIN.trigger_edit_buttons_title", name=html.escape(trigger.name))
        
        if trigger.buttons:
            text += t(lang, "ADMIN.trigger_edit_buttons_current")
            for row in trigger.buttons:
                for btn in row:
                    text += f"  • {btn.get('text', '?')}\n"
        else:
            text += t(lang, "ADMIN.trigger_edit_buttons_none")
        
        text += "\n<code>Text | https://url.com</code>"
        
        keyboard = [
            [{"text": "🗑 " + t(lang, "ADMIN.trigger_buttons_removed"), "callback_data": f"admin:broadcast:trigger_edit:{trigger_id}:remove_buttons"}],
            [{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}]
        ]
        
    elif field == "remove_buttons":
        async with get_db() as session:
            result = await session.execute(
                select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
            )
            trigger = result.scalar_one_or_none()
            if trigger:
                trigger.buttons = None
        
        await query.answer(t(lang, "ADMIN.trigger_buttons_removed"), show_alert=True)
        await trigger_view(query, lang, trigger_id)
        return
        
    elif field == "conditions":
        text = t(lang, "ADMIN.trigger_edit_cond_title", name=html.escape(trigger.name), type=type_info['label'])
        
        conditions = trigger.conditions or {}
        condition_labels = type_info.get("condition_labels", {})
        
        text += t(lang, "ADMIN.trigger_edit_cond_current")
        for key, value in conditions.items():
            label = condition_labels.get(key, key)
            text += f"  • {label}: <code>{value}</code>\n"
        
        keyboard = []
        for key in type_info.get("default_conditions", {}).keys():
            label = condition_labels.get(key, key)
            current = conditions.get(key, "—")
            keyboard.append([{
                "text": f"{label}: {current}",
                "callback_data": f"admin:broadcast:trigger_cond:{trigger_id}:{key}"
            }])
        
        keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}])
        
    elif field == "behavior":
        text = t(lang, "ADMIN.trigger_edit_behavior_title", name=html.escape(trigger.name))
        
        text += t(lang, "ADMIN.trigger_edit_behavior_current")
        text += f"  • {t(lang, 'ADMIN.behavior_max_sends')}: {trigger.max_sends_per_user}\n"
        text += f"  • {t(lang, 'ADMIN.behavior_repeat_days')}: {trigger.repeat_interval_days}\n"
        text += f"  • {t(lang, 'ADMIN.behavior_send_time')}: {trigger.send_start_hour:02d}:00 - {trigger.send_end_hour:02d}:00\n"
        text += f"  • {t(lang, 'ADMIN.behavior_delay')}: {trigger.delay_minutes} min\n"
        
        keyboard = [
            [{"text": f"📊 {t(lang, 'ADMIN.behavior_max_sends')}: {trigger.max_sends_per_user}", "callback_data": f"admin:broadcast:trigger_behavior:{trigger_id}:max_sends"}],
            [{"text": f"🔁 {t(lang, 'ADMIN.behavior_repeat_days')}: {trigger.repeat_interval_days}", "callback_data": f"admin:broadcast:trigger_behavior:{trigger_id}:repeat"}],
            [{"text": f"🕐 {t(lang, 'ADMIN.behavior_send_time')}: {trigger.send_start_hour:02d}-{trigger.send_end_hour:02d}", "callback_data": f"admin:broadcast:trigger_behavior:{trigger_id}:time"}],
            [{"text": f"⏱ {t(lang, 'ADMIN.behavior_delay')}: {trigger.delay_minutes}", "callback_data": f"admin:broadcast:trigger_behavior:{trigger_id}:delay"}],
            [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}]
        ]
    else:
        await trigger_view(query, lang, trigger_id)
        return
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def trigger_edit_condition(query, lang: str, trigger_id: int, param: str):
    """Edit specific condition parameter"""
    from core.plugins.core_api import CoreAPI
    
    admin_id = await get_user_id_by_telegram_id(query.from_user.id)
    core_api = CoreAPI("core")
    await core_api.set_user_state(admin_id, "admin_trigger_edit_cond", {
        "trigger_id": trigger_id,
        "param": param
    })
    
    from core.database.models import BroadcastTrigger
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
    
    type_info = get_trigger_type_info(trigger.trigger_type)
    label = type_info.get("condition_labels", {}).get(param, param)
    current = (trigger.conditions or {}).get(param, "—")
    
    text = t(lang, "ADMIN.trigger_edit_param", label=label, value=current)
    
    keyboard = [[{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:broadcast:trigger_edit:{trigger_id}:conditions"}]]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def trigger_edit_behavior(query, lang: str, trigger_id: int, param: str):
    """Edit behavior parameter"""
    from core.plugins.core_api import CoreAPI
    
    admin_id = await get_user_id_by_telegram_id(query.from_user.id)
    core_api = CoreAPI("core")
    await core_api.set_user_state(admin_id, "admin_trigger_edit_behavior", {
        "trigger_id": trigger_id,
        "param": param
    })
    
    from core.database.models import BroadcastTrigger
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
    
    if param == "max_sends":
        label = t(lang, "ADMIN.behavior_max_sends")
        current = trigger.max_sends_per_user
        hint = "0 = ∞"
    elif param == "repeat":
        label = t(lang, "ADMIN.behavior_repeat_days")
        current = trigger.repeat_interval_days
        hint = "0 = —"
    elif param == "time":
        label = t(lang, "ADMIN.behavior_send_time")
        current = f"{trigger.send_start_hour:02d}:00 - {trigger.send_end_hour:02d}:00"
        hint = t(lang, "ADMIN.behavior_send_time_hint")
    elif param == "delay":
        label = t(lang, "ADMIN.behavior_delay")
        current = trigger.delay_minutes
        hint = t(lang, "ADMIN.behavior_delay_hint")
    else:
        await trigger_view(query, lang, trigger_id)
        return
    
    text = t(lang, "ADMIN.trigger_edit_param", label=label, value=current)
    text += f"\n\n💡 {hint}"
    
    keyboard = [[{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:broadcast:trigger_edit:{trigger_id}:behavior"}]]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def trigger_toggle(query, lang: str, trigger_id: int):
    """Toggle trigger active state"""
    from core.database.models import BroadcastTrigger
    
    status = ""
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
        
        if trigger:
            trigger.is_active = not trigger.is_active
            status = t(lang, "ADMIN.trigger_status_active") if trigger.is_active else t(lang, "ADMIN.trigger_status_disabled")
    
    await query.answer(t(lang, "ADMIN.trigger_toggled", status=status), show_alert=True)
    await trigger_view(query, lang, trigger_id)


async def trigger_delete(query, lang: str, trigger_id: int):
    """Delete trigger"""
    from core.database.models import BroadcastTrigger
    
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
        
        if trigger:
            await session.delete(trigger)
    
    await query.answer(t(lang, "ADMIN.trigger_deleted"), show_alert=True)
    await triggers_main(query, lang)


# ==================== MESSAGE HANDLERS ====================

async def handle_broadcast_text(update, context, admin_id: int, lang: str):
    """Handle broadcast text input"""
    from core.database.models import Broadcast, User
    from core.plugins.core_api import CoreAPI
    core_api = CoreAPI("core")
    
    text = update.message.text
    
    # Get admin user id
    async with get_db() as session:
        result = await session.execute(
            select(User.id).where(User.telegram_id == update.effective_user.id)
        )
        user_id = result.scalar()
        
        # Create broadcast
        broadcast = Broadcast(
            text=text,
            created_by=user_id,
            status="draft"
        )
        session.add(broadcast)
        await session.flush()
        broadcast_id = broadcast.id
    
    await core_api.clear_user_state(admin_id)
    
    # Show target selection
    audiences = get_audiences(lang)
    keyboard = []
    for key in AUDIENCE_KEYS:
        label, _ = audiences.get(key, (key, None))
        keyboard.append([{
            "text": label,
            "callback_data": f"admin:broadcast:preview:{broadcast_id}_{key}"
        }])
    
    keyboard.append([{"text": t(lang, "COMMON.cancel"), "callback_data": "admin:broadcast"}])
    
    await update.message.reply_text(
        t(lang, "ADMIN.broadcast_select_target") + "\n\n" + t(lang, "ADMIN.broadcast_select_target_hint"),
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_broadcast_button(update, context, admin_id: int, lang: str, broadcast_id: int):
    """Handle button input for broadcast"""
    from core.database.models import Broadcast
    from core.plugins.core_api import CoreAPI
    core_api = CoreAPI("core")
    
    text = update.message.text
    
    # Parse: Button Text | https://url.com
    if "|" not in text:
        await update.message.reply_text(
            t(lang, "ADMIN.broadcast_button_error"),
            parse_mode="HTML"
        )
        return
    
    parts = text.split("|", 1)
    btn_text = parts[0].strip()
    btn_url = parts[1].strip()
    
    async with get_db() as session:
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
        
        if broadcast:
            buttons = broadcast.buttons or []
            buttons.append([{"text": btn_text, "url": btn_url}])
            broadcast.buttons = buttons
    
    await core_api.clear_user_state(admin_id)
    
    # Show preview with updated buttons
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:broadcast:preview:{broadcast_id}"}]
    ]
    
    await update.message.reply_text(
        t(lang, "ADMIN.broadcast_button_added"),
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_broadcast_media(update, context, admin_id: int, lang: str, broadcast_id: int):
    """Handle media input for broadcast"""
    from core.database.models import Broadcast
    from core.plugins.core_api import CoreAPI
    core_api = CoreAPI("core")
    
    message = update.message
    media_type = None
    file_id = None
    
    if message.photo:
        media_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        file_id = message.video.file_id
    elif message.animation:
        media_type = "animation"
        file_id = message.animation.file_id
    elif message.document:
        media_type = "document"
        file_id = message.document.file_id
    
    if not media_type:
        await message.reply_text(
            t(lang, "ADMIN.broadcast_media_error"),
            parse_mode="HTML"
        )
        return
    
    async with get_db() as session:
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
        
        if broadcast:
            broadcast.media_type = media_type
            broadcast.media_file_id = file_id
    
    await core_api.clear_user_state(admin_id)
    
    # Show preview with updated media
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:broadcast:preview:{broadcast_id}"}]
    ]
    
    await message.reply_text(
        t(lang, "ADMIN.broadcast_media_added", type=media_type),
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_broadcast_schedule(update, context, admin_id: int, lang: str, broadcast_id: int):
    """Handle schedule date/time input"""
    from core.database.models import Broadcast
    from core.plugins.core_api import CoreAPI
    core_api = CoreAPI("core")
    
    text = update.message.text
    
    # Parse date/time: DD.MM.YYYY HH:MM or DD.MM HH:MM
    try:
        if len(text.split()) == 2:
            date_part, time_part = text.split()
            
            # Parse date
            if date_part.count(".") == 2:
                day, month, year = date_part.split(".")
            else:
                day, month = date_part.split(".")
                year = datetime.now().year
            
            # Parse time
            hour, minute = time_part.split(":")
            
            scheduled_at = datetime(
                int(year), int(month), int(day),
                int(hour), int(minute)
            )
            
            if scheduled_at <= datetime.now():
                await update.message.reply_text(
                    t(lang, "ADMIN.broadcast_schedule_past"),
                    parse_mode="HTML"
                )
                return
        else:
            raise ValueError("Invalid format")
    except Exception:
        await update.message.reply_text(
            t(lang, "ADMIN.broadcast_schedule_error"),
            parse_mode="HTML"
        )
        return
    
    async with get_db() as session:
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
        
        if broadcast:
            broadcast.scheduled_at = scheduled_at
            broadcast.status = "scheduled"
    
    await core_api.clear_user_state(admin_id)
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:broadcast"}]
    ]
    
    await update.message.reply_text(
        t(lang, "ADMIN.broadcast_scheduled_success", time=scheduled_at.strftime("%d.%m.%Y %H:%M")),
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_trigger_name(update, context, admin_id: int, lang: str, trigger_type: str):
    """Handle trigger name input"""
    from core.plugins.core_api import CoreAPI
    core_api = CoreAPI("core")
    
    name = update.message.text
    
    await core_api.set_user_state(
        admin_id,
        "admin_trigger_text",
        {"trigger_type": trigger_type, "name": name}
    )
    
    await update.message.reply_text(
        t(lang, "ADMIN.trigger_enter_text"),
        parse_mode="HTML"
    )


async def handle_trigger_text(update, context, admin_id: int, lang: str, trigger_type: str, name: str):
    """Handle trigger text input and create trigger"""
    from core.database.models import BroadcastTrigger, User
    from core.plugins.core_api import CoreAPI
    core_api = CoreAPI("core")
    
    text = update.message.text
    
    async with get_db() as session:
        result = await session.execute(
            select(User.id).where(User.telegram_id == update.effective_user.id)
        )
        user_id = result.scalar()
        
        # Get default conditions from TRIGGER_TYPES
        type_info = get_trigger_type_info(trigger_type)
        conditions = type_info.get("default_conditions", {}).copy()
        
        trigger = BroadcastTrigger(
            name=name,
            trigger_type=trigger_type,
            text=text,
            conditions=conditions,
            created_by=user_id,
            is_active=True
        )
        session.add(trigger)
    
    await core_api.clear_user_state(admin_id)
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:broadcast:triggers"}]
    ]
    
    await update.message.reply_text(
        t(lang, "ADMIN.trigger_created"),
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


# ==================== TRIGGER EDIT HANDLERS ====================

async def handle_trigger_edit_text(update, context, admin_id: int, lang: str, trigger_id: int):
    """Handle trigger text edit"""
    from core.database.models import BroadcastTrigger
    from core.plugins.core_api import CoreAPI
    core_api = CoreAPI("core")
    
    new_text = update.message.text
    
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
        
        if trigger:
            trigger.text = new_text
    
    await core_api.clear_user_state(admin_id)
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}]
    ]
    
    await update.message.reply_text(
        t(lang, "ADMIN.trigger_text_updated"),
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_trigger_edit_media(update, context, admin_id: int, lang: str, trigger_id: int):
    """Handle trigger media edit"""
    from core.database.models import BroadcastTrigger
    from core.plugins.core_api import CoreAPI
    core_api = CoreAPI("core")
    
    message = update.message
    media_type = None
    file_id = None
    
    if message.photo:
        media_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        file_id = message.video.file_id
    elif message.animation:
        media_type = "animation"
        file_id = message.animation.file_id
    elif message.document:
        media_type = "document"
        file_id = message.document.file_id
    
    if not media_type:
        await message.reply_text(
            t(lang, "ADMIN.trigger_media_invalid"),
            parse_mode="HTML"
        )
        return
    
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
        
        if trigger:
            trigger.media_type = media_type
            trigger.media_file_id = file_id
    
    await core_api.clear_user_state(admin_id)
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}]
    ]
    
    await message.reply_text(
        t(lang, "ADMIN.trigger_media_added", type=media_type),
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_trigger_edit_button(update, context, admin_id: int, lang: str, trigger_id: int):
    """Handle trigger button edit"""
    from core.database.models import BroadcastTrigger
    from core.plugins.core_api import CoreAPI
    core_api = CoreAPI("core")
    
    text = update.message.text
    
    # Parse: Button Text | https://url.com
    if "|" not in text:
        await update.message.reply_text(
            t(lang, "ADMIN.trigger_button_format_error"),
            parse_mode="HTML"
        )
        return
    
    parts = text.split("|", 1)
    btn_text = parts[0].strip()
    btn_url = parts[1].strip()
    
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
        
        if trigger:
            buttons = list(trigger.buttons or [])
            buttons.append([{"text": btn_text, "url": btn_url}])
            trigger.buttons = buttons
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(trigger, "buttons")
    
    await core_api.clear_user_state(admin_id)
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}]
    ]
    
    await update.message.reply_text(
        t(lang, "ADMIN.trigger_button_added"),
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_trigger_edit_cond(update, context, admin_id: int, lang: str, trigger_id: int, param: str):
    """Handle trigger condition edit"""
    from core.database.models import BroadcastTrigger
    from core.plugins.core_api import CoreAPI
    core_api = CoreAPI("core")
    
    value_text = update.message.text.strip()
    
    # Parse value
    if value_text.lower() in ("true", "да", "yes", "1"):
        value = True
    elif value_text.lower() in ("false", "нет", "no", "0"):
        value = False
    else:
        try:
            value = int(value_text)
        except ValueError:
            try:
                value = float(value_text)
            except ValueError:
                value = value_text
    
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
        
        if trigger:
            conditions = dict(trigger.conditions or {})
            conditions[param] = value
            trigger.conditions = conditions
            # Mark as modified for SQLAlchemy to detect change
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(trigger, "conditions")
    
    await core_api.clear_user_state(admin_id)
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}]
    ]
    
    await update.message.reply_text(
        t(lang, "ADMIN.trigger_cond_updated", param=param, value=value),
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_trigger_edit_behavior(update, context, admin_id: int, lang: str, trigger_id: int, param: str):
    """Handle trigger behavior edit"""
    from core.database.models import BroadcastTrigger
    from core.plugins.core_api import CoreAPI
    core_api = CoreAPI("core")
    
    value_text = update.message.text.strip()
    
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
        
        if trigger:
            if param == "max_sends":
                try:
                    trigger.max_sends_per_user = int(value_text)
                except ValueError:
                    await update.message.reply_text(t(lang, "ADMIN.trigger_error_number"))
                    return
                    
            elif param == "repeat":
                try:
                    trigger.repeat_interval_days = int(value_text)
                except ValueError:
                    await update.message.reply_text(t(lang, "ADMIN.trigger_error_number"))
                    return
                    
            elif param == "time":
                # Format: 9-21
                try:
                    parts = value_text.replace(" ", "").split("-")
                    trigger.send_start_hour = int(parts[0])
                    trigger.send_end_hour = int(parts[1])
                except (ValueError, IndexError):
                    await update.message.reply_text(t(lang, "ADMIN.trigger_error_time_format"))
                    return
                    
            elif param == "delay":
                try:
                    trigger.delay_minutes = int(value_text)
                except ValueError:
                    await update.message.reply_text(t(lang, "ADMIN.trigger_error_minutes"))
                    return
    
    await core_api.clear_user_state(admin_id)
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:broadcast:trigger_view:{trigger_id}"}]
    ]
    
    await update.message.reply_text(
        t(lang, "ADMIN.trigger_behavior_updated"),
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
