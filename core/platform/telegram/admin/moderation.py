"""
Admin Moderation
"""
from datetime import datetime, timedelta
from sqlalchemy import select, desc, func

from core.locales import t
from core.database import get_db
from core.platform.telegram.utils import build_keyboard

# Bot instance for notifications (set from outside)
_bot = None

# Pagination
USERS_PER_PAGE = 10

# Moderation reason keys
MODERATION_REASON_KEYS = ["spam", "abuse", "fraud", "terms_violation", "other"]


def get_moderation_reasons(lang: str) -> dict:
    """Get localized moderation reasons"""
    return {
        "spam": t(lang, "ADMIN.reason_spam"),
        "abuse": t(lang, "ADMIN.reason_abuse"),
        "fraud": t(lang, "ADMIN.reason_fraud"),
        "terms_violation": t(lang, "ADMIN.reason_terms_violation"),
        "other": t(lang, "ADMIN.reason_other")
    }


def set_bot(bot):
    """Set bot instance for notifications"""
    global _bot
    _bot = bot


async def notify_user(telegram_id: int, text: str):
    """Send notification to user"""
    global _bot
    if not _bot:
        return False
    try:
        await _bot.send_message(
            chat_id=telegram_id,
            text=text,
            parse_mode="HTML"
        )
        return True
    except Exception:
        return False


async def check_expired_bans():
    """Check and unban users with expired bans (called periodically)"""
    from core.database.models import User, UserBan
    
    async with get_db() as session:
        now = datetime.utcnow()
        
        # Find users with expired temporary bans
        result = await session.execute(
            select(User).where(
                User.is_blocked == True,
                User.block_type == "temporary",
                User.block_expires_at <= now
            )
        )
        expired_users = result.scalars().all()
        
        for user in expired_users:
            user.is_blocked = False
            user.block_type = None
            user.block_reason = None
            user.block_expires_at = None
            
            # Update ban record
            result = await session.execute(
                select(UserBan).where(
                    UserBan.user_id == user.id,
                    UserBan.is_active == True
                )
            )
            bans = result.scalars().all()
            for ban in bans:
                ban.is_active = False
                ban.unbanned_at = now
            
            # Notify user
            await notify_user(user.telegram_id, t(user.language or "ru", "ADMIN.notify_unban_auto"))
        
        return len(expired_users)


async def admin_moderation(query, lang: str, action: str = None, params: str = None):
    """Admin moderation handler"""
    if action == "user" and params:
        await moderation_user(query, lang, int(params))
    elif action == "warn" and params:
        await warn_user_menu(query, lang, int(params))
    elif action == "warn_confirm":
        parts = params.split("_") if params else []
        if len(parts) >= 2:
            await warn_user_confirm(query, lang, int(parts[0]), parts[1])
    elif action == "warn_revoke" and params:
        await warn_revoke(query, lang, int(params))
    elif action == "ban" and params:
        await ban_user_menu(query, lang, int(params))
    elif action == "ban_temp":
        parts = params.split("_") if params else []
        if len(parts) >= 2:
            await ban_user_temp(query, lang, int(parts[0]), int(parts[1]))
    elif action == "ban_perm" and params:
        await ban_user_perm(query, lang, int(params))
    elif action == "unban" and params:
        await unban_user(query, lang, int(params))
    elif action == "history" and params:
        await moderation_history(query, lang, int(params))
    elif action == "banned":
        # Parse filter and page
        filter_type = "all"
        page = 0
        if params:
            parts = params.rsplit("_", 1)
            filter_type = parts[0] if parts else "all"
            page = int(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 0
        await banned_list(query, lang, filter_type, page)
    elif action == "warnings":
        page = int(params) if params and params.isdigit() else 0
        await warnings_list(query, lang, page)
    elif action == "log":
        filter_type = "all"
        page = 0
        if params:
            parts = params.rsplit("_", 1)
            filter_type = parts[0] if parts else "all"
            page = int(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 0
        await moderation_log(query, lang, filter_type, page)
    elif action == "search":
        await moderation_search(query, lang)
    else:
        await moderation_main(query, lang)


async def moderation_main(query, lang: str):
    """Moderation main menu"""
    from core.database.models import User, UserWarning, ModerationLog
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    async with get_db() as session:
        # Banned users count (temporary)
        result = await session.execute(
            select(func.count(User.id)).where(
                User.is_blocked == True,
                User.block_type == "temporary"
            )
        )
        temp_banned = result.scalar() or 0
        
        # Banned users count (permanent)
        result = await session.execute(
            select(func.count(User.id)).where(
                User.is_blocked == True,
                User.block_type == "permanent"
            )
        )
        perm_banned = result.scalar() or 0
        
        # Users with active warnings
        result = await session.execute(
            select(func.count(func.distinct(UserWarning.user_id))).where(
                UserWarning.is_active == True
            )
        )
        users_with_warnings = result.scalar() or 0
        
        # Actions today
        result = await session.execute(
            select(func.count(ModerationLog.id)).where(
                ModerationLog.created_at >= today
            )
        )
        actions_today = result.scalar() or 0
    
    total_banned = temp_banned + perm_banned
    
    text = t(lang, "ADMIN.moderation_title") + "\n\n"
    text += t(lang, "ADMIN.moderation_stats") + "\n"
    text += f"├── " + t(lang, "ADMIN.moderation_banned", count=total_banned) + "\n"
    text += f"│   ├── " + t(lang, "ADMIN.moderation_banned_temp", count=temp_banned) + "\n"
    text += f"│   └── " + t(lang, "ADMIN.moderation_banned_perm", count=perm_banned) + "\n"
    text += f"├── " + t(lang, "ADMIN.moderation_warnings", count=users_with_warnings) + "\n"
    text += f"└── " + t(lang, "ADMIN.moderation_actions_today", count=actions_today) + "\n"
    
    keyboard = [
        [{"text": t(lang, "ADMIN.moderation_search"), "callback_data": "admin:moderation:search"}],
        [{"text": t(lang, "ADMIN.moderation_banned_list", count=total_banned), "callback_data": "admin:moderation:banned:all"}],
        [{"text": t(lang, "ADMIN.moderation_warnings_list", count=users_with_warnings), "callback_data": "admin:moderation:warnings"}],
        [{"text": t(lang, "ADMIN.moderation_log"), "callback_data": "admin:moderation:log:all"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin"}]
    ]
    
    try:
        await query.edit_message_text(
            text,
            reply_markup=build_keyboard(keyboard),
            parse_mode="HTML"
        )
    except Exception:
        pass


async def moderation_search(query, lang: str):
    """Search user for moderation"""
    from core.plugins.core_api import CoreAPI
    from core.database.models import User
    
    core_api = CoreAPI("core")
    
    # Get admin user_id
    async with get_db() as session:
        result = await session.execute(
            select(User.id).where(User.telegram_id == query.from_user.id)
        )
        admin_id = result.scalar()
    
    # Set state for search input
    await core_api.set_user_state(admin_id, "admin_moderation_search")
    
    text = t(lang, "ADMIN.moderation_search_prompt") + "\n\n"
    text += t(lang, "ADMIN.moderation_search_hint")
    
    keyboard = [
        [{"text": t(lang, "COMMON.cancel"), "callback_data": "admin:moderation"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def banned_list(query, lang: str, filter_type: str = "all", page: int = 0):
    """Show banned users list"""
    from core.database.models import User
    
    async with get_db() as session:
        # Base query
        base_query = select(User).where(User.is_blocked == True)
        count_query = select(func.count(User.id)).where(User.is_blocked == True)
        
        # Apply filter
        if filter_type == "temp":
            base_query = base_query.where(User.block_type == "temporary")
            count_query = count_query.where(User.block_type == "temporary")
        elif filter_type == "perm":
            base_query = base_query.where(User.block_type == "permanent")
            count_query = count_query.where(User.block_type == "permanent")
        
        # Count
        result = await session.execute(count_query)
        total_count = result.scalar() or 0
        
        # Pagination
        total_pages = max(1, (total_count + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
        page = max(0, min(page, total_pages - 1))
        offset = page * USERS_PER_PAGE
        
        # Get users
        result = await session.execute(
            base_query.order_by(desc(User.blocked_at)).offset(offset).limit(USERS_PER_PAGE)
        )
        users = result.scalars().all()
    
    text = t(lang, "ADMIN.moderation_banned_title") + "\n\n"
    text += t(lang, "ADMIN.moderation_banned_count", count=total_count) + "\n\n"
    
    if total_pages > 1:
        text += t(lang, "ADMIN.page_info", current=page + 1, total=total_pages) + "\n\n"
    
    if not users:
        text += t(lang, "ADMIN.moderation_banned_empty")
    else:
        for user in users:
            icon = "🔴" if user.block_type == "permanent" else "🟡"
            username = f"@{user.telegram_username}" if user.telegram_username else user.display_name
            
            if user.block_type == "permanent":
                expires = t(lang, "ADMIN.moderation_ban_forever")
            elif user.block_expires_at:
                expires = t(lang, "ADMIN.moderation_ban_until", date=user.block_expires_at.strftime("%d.%m.%Y"))
            else:
                expires = "-"
            
            text += f"{icon} {username} — {expires}\n"
            if user.block_reason:
                text += f"   └── {user.block_reason[:30]}\n"
    
    # Filter buttons
    filters = [
        ("all", t(lang, "ADMIN.filter_all")),
        ("temp", t(lang, "ADMIN.moderation_filter_temp")),
        ("perm", t(lang, "ADMIN.moderation_filter_perm"))
    ]
    filter_buttons = []
    for f, label in filters:
        if f == filter_type:
            label = f"• {label} •"
        filter_buttons.append({"text": label, "callback_data": f"admin:moderation:banned:{f}"})
    
    keyboard = [filter_buttons]
    
    # User buttons
    for user in users[:5]:
        name = user.display_name[:20]
        keyboard.append([{
            "text": f"👤 {name}",
            "callback_data": f"admin:moderation:user:{user.id}"
        }])
    
    # Pagination
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append({"text": t(lang, "ADMIN.page_prev"), "callback_data": f"admin:moderation:banned:{filter_type}_{page - 1}"})
        if page < total_pages - 1:
            pagination.append({"text": t(lang, "ADMIN.page_next"), "callback_data": f"admin:moderation:banned:{filter_type}_{page + 1}"})
        if pagination:
            keyboard.append(pagination)
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:moderation"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def warnings_list(query, lang: str, page: int = 0):
    """Show users with active warnings"""
    from core.database.models import User, UserWarning
    
    async with get_db() as session:
        # Get users with warnings, sorted by warning count
        subquery = select(
            UserWarning.user_id,
            func.count(UserWarning.id).label("warn_count")
        ).where(
            UserWarning.is_active == True
        ).group_by(UserWarning.user_id).subquery()
        
        result = await session.execute(
            select(func.count()).select_from(subquery)
        )
        total_count = result.scalar() or 0
        
        # Pagination
        total_pages = max(1, (total_count + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
        page = max(0, min(page, total_pages - 1))
        offset = page * USERS_PER_PAGE
        
        # Get users with warning counts
        result = await session.execute(
            select(User, subquery.c.warn_count).join(
                subquery, User.id == subquery.c.user_id
            ).order_by(desc(subquery.c.warn_count)).offset(offset).limit(USERS_PER_PAGE)
        )
        users_with_warnings = result.all()
    
    text = t(lang, "ADMIN.moderation_warnings_title") + "\n\n"
    text += t(lang, "ADMIN.moderation_warnings_count", count=total_count) + "\n\n"
    
    if total_pages > 1:
        text += t(lang, "ADMIN.page_info", current=page + 1, total=total_pages) + "\n\n"
    
    if not users_with_warnings:
        text += t(lang, "ADMIN.moderation_warnings_empty")
    else:
        for user, warn_count in users_with_warnings:
            username = f"@{user.telegram_username}" if user.telegram_username else user.display_name
            text += f"⚠️ {warn_count}/3 — {username}\n"
    
    keyboard = []
    
    # User buttons
    for user, warn_count in users_with_warnings[:5]:
        name = user.display_name[:20]
        keyboard.append([{
            "text": f"⚠️ {warn_count}/3 — {name}",
            "callback_data": f"admin:moderation:user:{user.id}"
        }])
    
    # Pagination
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append({"text": t(lang, "ADMIN.page_prev"), "callback_data": f"admin:moderation:warnings:{page - 1}"})
        if page < total_pages - 1:
            pagination.append({"text": t(lang, "ADMIN.page_next"), "callback_data": f"admin:moderation:warnings:{page + 1}"})
        if pagination:
            keyboard.append(pagination)
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:moderation"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def moderation_log(query, lang: str, filter_type: str = "all", page: int = 0):
    """Show moderation log"""
    from core.database.models import ModerationLog, User
    
    async with get_db() as session:
        # Base query
        base_query = select(ModerationLog, User).join(User, ModerationLog.admin_id == User.id)
        count_query = select(func.count(ModerationLog.id))
        
        # Apply filter
        if filter_type == "bans":
            base_query = base_query.where(ModerationLog.action.in_(["ban_temporary", "ban_permanent"]))
            count_query = count_query.where(ModerationLog.action.in_(["ban_temporary", "ban_permanent"]))
        elif filter_type == "unbans":
            base_query = base_query.where(ModerationLog.action == "unban")
            count_query = count_query.where(ModerationLog.action == "unban")
        elif filter_type == "warns":
            base_query = base_query.where(ModerationLog.action.in_(["warn", "warn_revoke"]))
            count_query = count_query.where(ModerationLog.action.in_(["warn", "warn_revoke"]))
        
        # Count
        result = await session.execute(count_query)
        total_count = result.scalar() or 0
        
        # Pagination
        total_pages = max(1, (total_count + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
        page = max(0, min(page, total_pages - 1))
        offset = page * USERS_PER_PAGE
        
        # Get logs
        result = await session.execute(
            base_query.order_by(desc(ModerationLog.created_at)).offset(offset).limit(USERS_PER_PAGE)
        )
        logs = result.all()
    
    action_icons = {
        "warn": "⚠️",
        "warn_revoke": "↩️",
        "ban_temporary": "🚫",
        "ban_permanent": "⛔",
        "unban": "✅"
    }
    
    text = t(lang, "ADMIN.moderation_log_title") + "\n\n"
    
    if total_pages > 1:
        text += t(lang, "ADMIN.page_info", current=page + 1, total=total_pages) + "\n\n"
    
    if not logs:
        text += t(lang, "ADMIN.moderation_log_empty")
    else:
        for log, admin in logs:
            icon = action_icons.get(log.action, "📋")
            time = log.created_at.strftime("%d.%m %H:%M")
            admin_name = admin.display_name[:15]
            text += f"{icon} {time} — {admin_name}\n"
            text += f"   └── ID: {log.target_user_id}"
            if log.duration_days:
                text += f" ({log.duration_days}д)"
            text += "\n"
    
    # Filter buttons
    filters = [
        ("all", t(lang, "ADMIN.filter_all")),
        ("bans", t(lang, "ADMIN.moderation_filter_bans")),
        ("unbans", t(lang, "ADMIN.moderation_filter_unbans")),
        ("warns", t(lang, "ADMIN.moderation_filter_warns"))
    ]
    filter_buttons = []
    for f, label in filters:
        if f == filter_type:
            label = f"• {label} •"
        filter_buttons.append({"text": label, "callback_data": f"admin:moderation:log:{f}"})
    
    keyboard = [filter_buttons[:2], filter_buttons[2:]]
    
    # Pagination
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append({"text": t(lang, "ADMIN.page_prev"), "callback_data": f"admin:moderation:log:{filter_type}_{page - 1}"})
        if page < total_pages - 1:
            pagination.append({"text": t(lang, "ADMIN.page_next"), "callback_data": f"admin:moderation:log:{filter_type}_{page + 1}"})
        if pagination:
            keyboard.append(pagination)
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:moderation"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def moderation_user(query, lang: str, user_id: int):
    """Show moderation options for user"""
    from core.database.models import User, UserWarning, ModerationLog
    
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        # Count active warnings
        result = await session.execute(
            select(func.count(UserWarning.id)).where(
                UserWarning.user_id == user_id,
                UserWarning.is_active == True
            )
        )
        warnings = result.scalar() or 0
        
        # Last activity
        result = await session.execute(
            select(ModerationLog).where(
                ModerationLog.target_user_id == user_id
            ).order_by(desc(ModerationLog.created_at)).limit(3)
        )
        recent_logs = result.scalars().all()
    
    status = t(lang, "ADMIN.moderation_status_banned") if user.is_blocked else t(lang, "ADMIN.moderation_status_active")
    
    text = t(lang, "ADMIN.moderation_user_title", id=user_id) + "\n\n"
    
    username = f"@{user.telegram_username}" if user.telegram_username else "-"
    text += f"📱 {username}\n"
    text += t(lang, "ADMIN.moderation_user_name", name=user.display_name) + "\n"
    text += f"🆔 TG: <code>{user.telegram_id}</code>\n"
    text += t(lang, "ADMIN.moderation_user_registered", date=user.created_at.strftime("%d.%m.%Y")) + "\n\n"
    
    text += t(lang, "ADMIN.moderation_user_status_title") + "\n"
    text += f"├── {status}\n"
    text += f"├── " + t(lang, "ADMIN.moderation_user_warnings", current=warnings, max=3) + "\n"
    
    if user.last_activity_at:
        diff = datetime.utcnow() - user.last_activity_at
        if diff.days > 0:
            last_active = t(lang, "ADMIN.moderation_user_last_active_days", days=diff.days)
        elif diff.seconds > 3600:
            last_active = t(lang, "ADMIN.moderation_user_last_active_hours", hours=diff.seconds // 3600)
        else:
            last_active = t(lang, "ADMIN.moderation_user_last_active_minutes", minutes=max(1, diff.seconds // 60))
        text += f"└── {last_active}\n"
    
    if user.is_blocked:
        text += "\n" + t(lang, "ADMIN.moderation_user_ban_info") + "\n"
        text += f"├── " + t(lang, "ADMIN.moderation_user_ban_reason", reason=user.block_reason or "-") + "\n"
        if user.block_type == "permanent":
            text += f"└── " + t(lang, "ADMIN.moderation_ban_forever") + "\n"
        elif user.block_expires_at:
            text += f"└── " + t(lang, "ADMIN.moderation_ban_until", date=user.block_expires_at.strftime("%d.%m.%Y %H:%M")) + "\n"
    
    # Recent history
    if recent_logs:
        action_names = {
            "warn": "⚠️",
            "warn_revoke": "↩️",
            "ban_temporary": "🚫",
            "ban_permanent": "⛔",
            "unban": "✅"
        }
        text += "\n" + t(lang, "ADMIN.moderation_user_recent") + "\n"
        for log in recent_logs:
            icon = action_names.get(log.action, "📋")
            date = log.created_at.strftime("%d.%m")
            text += f"├── {icon} {date}\n"
    
    keyboard = []
    
    if not user.is_blocked:
        keyboard.append([
            {"text": t(lang, "ADMIN.moderation_action_warn"), "callback_data": f"admin:moderation:warn:{user_id}"},
            {"text": t(lang, "ADMIN.moderation_action_ban"), "callback_data": f"admin:moderation:ban:{user_id}"}
        ])
        keyboard.append([{
            "text": t(lang, "ADMIN.moderation_action_ban_perm"),
            "callback_data": f"admin:moderation:ban_perm:{user_id}"
        }])
        if warnings > 0:
            keyboard.append([{
                "text": t(lang, "ADMIN.moderation_action_revoke_warn"),
                "callback_data": f"admin:moderation:warn_revoke:{user_id}"
            }])
    else:
        keyboard.append([{
            "text": t(lang, "ADMIN.moderation_action_unban"),
            "callback_data": f"admin:moderation:unban:{user_id}"
        }])
    
    keyboard.append([{
        "text": t(lang, "ADMIN.moderation_action_history"),
        "callback_data": f"admin:moderation:history:{user_id}"
    }])
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:moderation"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def warn_revoke(query, lang: str, user_id: int):
    """Revoke one warning from user"""
    from core.database.models import User, UserWarning, ModerationLog
    
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        # Get admin
        admin_telegram_id = query.from_user.id
        result = await session.execute(
            select(User.id).where(User.telegram_id == admin_telegram_id)
        )
        admin_id = result.scalar()
        
        # Find latest active warning
        result = await session.execute(
            select(UserWarning).where(
                UserWarning.user_id == user_id,
                UserWarning.is_active == True
            ).order_by(desc(UserWarning.created_at)).limit(1)
        )
        warning = result.scalar_one_or_none()
        
        if not warning:
            await query.answer(t(lang, "ADMIN.moderation_no_warnings"), show_alert=True)
            return
        
        # Revoke warning
        warning.is_active = False
        warning.revoked_at = datetime.utcnow()
        warning.revoked_by = admin_id
        
        # Update user warnings count
        user.warnings_count = max(0, (user.warnings_count or 0) - 1)
        
        # Log
        log = ModerationLog(
            admin_id=admin_id,
            target_user_id=user_id,
            action="warn_revoke"
        )
        session.add(log)
    
    await query.answer(t(lang, "ADMIN.moderation_warn_revoked"), show_alert=True)
    await moderation_user(query, lang, user_id)


async def warn_user_menu(query, lang: str, user_id: int):
    """Show warning reasons menu"""
    text = t(lang, "ADMIN.moderation_select_reason") + "\n"
    
    reasons = get_moderation_reasons(lang)
    keyboard = []
    for reason_code in MODERATION_REASON_KEYS:
        reason_text = reasons.get(reason_code, reason_code)
        keyboard.append([{
            "text": reason_text,
            "callback_data": f"admin:moderation:warn_confirm:{user_id}_{reason_code}"
        }])
    
    keyboard.append([{
        "text": t(lang, "COMMON.cancel"),
        "callback_data": f"admin:moderation:user:{user_id}"
    }])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def warn_user_confirm(query, lang: str, user_id: int, reason: str):
    """Confirm and issue warning"""
    from core.database.models import User, UserWarning, UserBan, ModerationLog
    from sqlalchemy import func
    
    target_telegram_id = None
    target_lang = "ru"
    warnings_count = 0
    auto_banned = False
    
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await query.answer(t(lang, "ADMIN.mod_user_not_found"), show_alert=True)
            return
        
        target_telegram_id = user.telegram_id
        target_lang = user.language or "ru"
        
        # Get admin user_id
        admin_telegram_id = query.from_user.id
        result = await session.execute(
            select(User.id).where(User.telegram_id == admin_telegram_id)
        )
        admin_id = result.scalar()
        
        # Create warning
        warning = UserWarning(
            user_id=user_id,
            reason=reason,
            issued_by=admin_id
        )
        session.add(warning)
        
        # Update user warnings count
        user.warnings_count = (user.warnings_count or 0) + 1
        user.last_warning_at = datetime.utcnow()
        warnings_count = user.warnings_count
        
        # Check for auto-ban (3 warnings)
        if user.warnings_count >= 3:
            user.is_blocked = True
            user.block_type = "temporary"
            user.block_reason = t(lang, "ADMIN.mod_reason_3_warnings")
            user.block_expires_at = datetime.utcnow() + timedelta(days=7)
            user.blocked_at = datetime.utcnow()
            user.blocked_by = admin_id
            
            warning.resulted_in_ban = True
            auto_banned = True
            
            # Create ban record
            ban = UserBan(
                user_id=user_id,
                ban_type="warning",
                reason="auto_ban",
                description="Auto-ban: 3 warnings",
                duration_days=7,
                expires_at=user.block_expires_at,
                banned_by=admin_id
            )
            session.add(ban)
        
        # Log action
        log = ModerationLog(
            admin_id=admin_id,
            target_user_id=user_id,
            action="warn",
            reason=reason
        )
        session.add(log)
    
    reasons = get_moderation_reasons(target_lang)
    reason_text = reasons.get(reason, reason)
    
    # Notify user
    if target_telegram_id:
        if auto_banned:
            notify_text = t(target_lang, "ADMIN.notify_warning_autoban", max=3, days=7)
        else:
            notify_text = t(target_lang, "ADMIN.notify_warning", 
                          reason=reason_text, current=warnings_count, max=3)
        await notify_user(target_telegram_id, notify_text)
    
    reasons_admin = get_moderation_reasons(lang)
    reason_text_admin = reasons_admin.get(reason, reason)
    
    if auto_banned:
        text = t(lang, "ADMIN.moderation_warned") + "\n\n"
        text += t(lang, "ADMIN.mod_autoban_info", days=7) + "\n"
        text += t(lang, "ADMIN.mod_autoban_reason")
    else:
        text = t(lang, "ADMIN.moderation_warned") + "\n\n"
        text += t(lang, "ADMIN.mod_reason", reason=reason_text_admin) + "\n"
        text += t(lang, "ADMIN.mod_warnings_count", count=warnings_count)
    
    keyboard = [
        [{"text": t(lang, "ADMIN.user_action_to_user"), "callback_data": f"admin:moderation:user:{user_id}"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:users"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def ban_user_menu(query, lang: str, user_id: int):
    """Show ban duration options"""
    text = "🚫 <b>Выберите срок бана:</b>\n"
    
    durations = [
        (1, "1 день"),
        (3, "3 дня"),
        (7, "7 дней"),
        (14, "14 дней"),
        (30, "30 дней"),
    ]
    
    keyboard = []
    for days, label in durations:
        keyboard.append([{
            "text": label,
            "callback_data": f"admin:moderation:ban_temp:{user_id}_{days}"
        }])
    
    keyboard.append([{
        "text": t(lang, "COMMON.cancel"),
        "callback_data": f"admin:moderation:user:{user_id}"
    }])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def ban_user_temp(query, lang: str, user_id: int, days: int):
    """Ban user temporarily"""
    from core.database.models import User, UserBan, ModerationLog
    
    target_telegram_id = None
    target_lang = "ru"
    expires_at = None
    
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await query.answer(t(lang, "ADMIN.mod_user_not_found"), show_alert=True)
            return
        
        target_telegram_id = user.telegram_id
        target_lang = user.language or "ru"
        
        # Get admin
        admin_telegram_id = query.from_user.id
        result = await session.execute(
            select(User.id).where(User.telegram_id == admin_telegram_id)
        )
        admin_id = result.scalar()
        
        # Ban user
        expires_at = datetime.utcnow() + timedelta(days=days)
        
        user.is_blocked = True
        user.block_type = "temporary"
        user.block_reason = t(lang, "ADMIN.mod_temp_ban_reason")
        user.block_expires_at = expires_at
        user.blocked_at = datetime.utcnow()
        user.blocked_by = admin_id
        
        # Create ban record
        ban = UserBan(
            user_id=user_id,
            ban_type="temporary",
            reason="admin_ban",
            duration_days=days,
            expires_at=expires_at,
            banned_by=admin_id
        )
        session.add(ban)
        
        # Log
        log = ModerationLog(
            admin_id=admin_id,
            target_user_id=user_id,
            action="ban_temporary",
            duration_days=days
        )
        session.add(log)
    
    # Notify user
    if target_telegram_id:
        notify_text = t(target_lang, "ADMIN.notify_ban_temp", 
                       days=days, reason=t(target_lang, "ADMIN.mod_rules_violation"), 
                       until=expires_at.strftime("%d.%m.%Y"))
        await notify_user(target_telegram_id, notify_text)
    
    text = t(lang, "ADMIN.moderation_banned") + f" ({days}d)\n"
    text += t(lang, "ADMIN.mod_until", date=expires_at.strftime('%d.%m.%Y %H:%M'))
    
    keyboard = [
        [{"text": "👤 К пользователю", "callback_data": f"admin:moderation:user:{user_id}"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:users"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def ban_user_perm(query, lang: str, user_id: int):
    """Ban user permanently"""
    from core.database.models import User, UserBan, ModerationLog
    
    target_telegram_id = None
    target_lang = "ru"
    
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await query.answer(t(lang, "ADMIN.mod_user_not_found"), show_alert=True)
            return
        
        target_telegram_id = user.telegram_id
        target_lang = user.language or "ru"
        
        # Get admin
        admin_telegram_id = query.from_user.id
        result = await session.execute(
            select(User.id).where(User.telegram_id == admin_telegram_id)
        )
        admin_id = result.scalar()
        
        # Ban user
        user.is_blocked = True
        user.block_type = "permanent"
        user.block_reason = t(lang, "ADMIN.mod_perm_ban_reason")
        user.block_expires_at = None
        user.blocked_at = datetime.utcnow()
        user.blocked_by = admin_id
        
        # Create ban record
        ban = UserBan(
            user_id=user_id,
            ban_type="permanent",
            reason="admin_ban",
            banned_by=admin_id
        )
        session.add(ban)
        
        # Log
        log = ModerationLog(
            admin_id=admin_id,
            target_user_id=user_id,
            action="ban_permanent"
        )
        session.add(log)
    
    # Notify user
    if target_telegram_id:
        notify_text = t(target_lang, "ADMIN.notify_ban_perm", reason=t(target_lang, "ADMIN.mod_rules_violation"))
        await notify_user(target_telegram_id, notify_text)
    
    text = t(lang, "ADMIN.moderation_banned") + " (permanent)"
    
    keyboard = [
        [{"text": "👤 К пользователю", "callback_data": f"admin:moderation:user:{user_id}"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:users"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def unban_user(query, lang: str, user_id: int):
    """Unban user"""
    from core.database.models import User, UserBan, ModerationLog
    
    target_telegram_id = None
    target_lang = "ru"
    
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await query.answer(t(lang, "ADMIN.mod_user_not_found"), show_alert=True)
            return
        
        target_telegram_id = user.telegram_id
        target_lang = user.language or "ru"
        
        # Get admin
        admin_telegram_id = query.from_user.id
        result = await session.execute(
            select(User.id).where(User.telegram_id == admin_telegram_id)
        )
        admin_id = result.scalar()
        
        # Unban
        user.is_blocked = False
        user.block_type = None
        user.block_reason = None
        user.block_expires_at = None
        
        # Update active bans
        result = await session.execute(
            select(UserBan).where(
                UserBan.user_id == user_id,
                UserBan.is_active == True
            )
        )
        bans = result.scalars().all()
        
        for ban in bans:
            ban.is_active = False
            ban.unbanned_at = datetime.utcnow()
            ban.unbanned_by = admin_id
        
        # Log
        log = ModerationLog(
            admin_id=admin_id,
            target_user_id=user_id,
            action="unban"
        )
        session.add(log)
    
    # Notify user
    if target_telegram_id:
        notify_text = t(target_lang, "ADMIN.notify_unban")
        await notify_user(target_telegram_id, notify_text)
    
    text = "✅ Пользователь разбанен"
    
    keyboard = [
        [{"text": "👤 К пользователю", "callback_data": f"admin:moderation:user:{user_id}"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:users"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def moderation_history(query, lang: str, user_id: int):
    """Show moderation history for user"""
    from core.database.models import ModerationLog, User
    
    async with get_db() as session:
        result = await session.execute(
            select(ModerationLog, User).join(
                User, ModerationLog.admin_id == User.id
            ).where(
                ModerationLog.target_user_id == user_id
            ).order_by(desc(ModerationLog.created_at)).limit(10)
        )
        logs = result.all()
    
    text = f"📋 <b>История модерации #{user_id}</b>\n\n"
    
    if not logs:
        text += t(lang, "ADMIN.mod_no_history")
    else:
        action_names = {
            "warn": "⚠️ Предупреждение",
            "warn_revoke": "↩️ Снято предупреждение",
            "ban_temporary": "🚫 Временный бан",
            "ban_permanent": "⛔ Перманентный бан",
            "unban": "✅ Разбан"
        }
        
        for log, admin in logs:
            action_text = action_names.get(log.action, log.action)
            text += f"{action_text}\n"
            text += f"   👤 {admin.display_name}\n"
            text += f"   📅 {log.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:moderation:user:{user_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_moderation_search(update, context, admin_id: int, lang: str):
    """Handle moderation search input"""
    from core.database.models import User
    from core.plugins.core_api import CoreAPI
    
    core_api = CoreAPI("core")
    query_text = update.message.text.strip()
    
    # Clear state
    await core_api.clear_user_state(admin_id)
    
    async with get_db() as session:
        user = None
        
        # Try to find by ID
        if query_text.isdigit():
            result = await session.execute(
                select(User).where(User.id == int(query_text))
            )
            user = result.scalar_one_or_none()
            
            # Try telegram_id if not found
            if not user:
                result = await session.execute(
                    select(User).where(User.telegram_id == int(query_text))
                )
                user = result.scalar_one_or_none()
        
        # Try by username
        elif query_text.startswith("@"):
            username = query_text[1:]
            result = await session.execute(
                select(User).where(User.telegram_username.ilike(username))
            )
            user = result.scalar_one_or_none()
        
        # Try by name
        else:
            result = await session.execute(
                select(User).where(
                    (User.first_name.ilike(f"%{query_text}%")) |
                    (User.last_name.ilike(f"%{query_text}%")) |
                    (User.telegram_username.ilike(f"%{query_text}%"))
                ).limit(1)
            )
            user = result.scalar_one_or_none()
    
    if user:
        # Show full moderation card with all buttons
        from core.database.models import UserWarning
        
        # Get warnings count
        async with get_db() as session:
            result = await session.execute(
                select(func.count(UserWarning.id)).where(
                    UserWarning.user_id == user.id,
                    UserWarning.is_active == True
                )
            )
            warnings = result.scalar() or 0
        
        text = t(lang, "ADMIN.moderation_user_title", id=user.id) + "\n\n"
        
        username = f"@{user.telegram_username}" if user.telegram_username else "-"
        text += f"📱 {username}\n"
        text += t(lang, "ADMIN.moderation_user_name", name=user.display_name) + "\n"
        text += f"🆔 TG: <code>{user.telegram_id}</code>\n"
        
        status = t(lang, "ADMIN.moderation_status_banned") if user.is_blocked else t(lang, "ADMIN.moderation_status_active")
        text += f"\n📊 {status}\n"
        text += t(lang, "ADMIN.moderation_user_warnings", current=warnings, max=3)
        
        keyboard = []
        
        if not user.is_blocked:
            keyboard.append([
                {"text": t(lang, "ADMIN.moderation_action_warn"), "callback_data": f"admin:moderation:warn:{user.id}"},
                {"text": t(lang, "ADMIN.moderation_action_ban"), "callback_data": f"admin:moderation:ban:{user.id}"}
            ])
            keyboard.append([{
                "text": t(lang, "ADMIN.moderation_action_ban_perm"),
                "callback_data": f"admin:moderation:ban_perm:{user.id}"
            }])
            if warnings > 0:
                keyboard.append([{
                    "text": t(lang, "ADMIN.moderation_action_revoke_warn"),
                    "callback_data": f"admin:moderation:warn_revoke:{user.id}"
                }])
        else:
            keyboard.append([{
                "text": t(lang, "ADMIN.moderation_action_unban"),
                "callback_data": f"admin:moderation:unban:{user.id}"
            }])
        
        keyboard.append([{
            "text": t(lang, "ADMIN.moderation_action_history"),
            "callback_data": f"admin:moderation:history:{user.id}"
        }])
        keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:moderation"}])
        
        await update.message.reply_text(
            text,
            reply_markup=build_keyboard(keyboard),
            parse_mode="HTML"
        )
    else:
        text = t(lang, "ADMIN.users_search_not_found")
        keyboard = [
            [{"text": t(lang, "ADMIN.moderation_search"), "callback_data": "admin:moderation:search"}],
            [{"text": t(lang, "COMMON.back"), "callback_data": "admin:moderation"}]
        ]
        
        await update.message.reply_text(
            text,
            reply_markup=build_keyboard(keyboard),
            parse_mode="HTML"
        )
