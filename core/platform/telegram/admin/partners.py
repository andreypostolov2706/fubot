"""
Admin Partners Management
"""
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc

from core.locales import t
from core.database import get_db
from core.platform.telegram.utils import build_keyboard

# Filters and pagination
PARTNER_FILTERS = ["all", "active", "pending", "rejected"]
PARTNERS_PER_PAGE = 15

# Bot instance for notifications
_bot = None


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
        await _bot.send_message(chat_id=telegram_id, text=text, parse_mode="HTML")
        return True
    except Exception:
        return False


async def admin_partners(query, lang: str, action: str = None, params: str = None):
    """Admin partners handler"""
    if action == "list":
        # Parse filter and page
        parts = params.rsplit("_", 1) if params and "_" in params and params.rsplit("_", 1)[-1].isdigit() else [params or "all"]
        filter_type = parts[0] if parts else "all"
        page = int(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 0
        await partners_list(query, lang, filter_type, page)
    elif action == "view" and params:
        await partner_view(query, lang, int(params))
    elif action == "applications":
        await partner_applications(query, lang)
    elif action == "app_review" and params:
        await partner_app_review(query, lang, int(params))
    elif action == "app_approve" and params:
        # params: partner_id_commission
        parts = params.split("_")
        if len(parts) >= 2:
            await partner_app_approve(query, lang, int(parts[0]), int(parts[1]))
    elif action == "app_custom" and params:
        await partner_app_custom(query, lang, int(params))
    elif action == "app_reject" and params:
        await partner_app_reject(query, lang, int(params))
    elif action == "payouts":
        await partner_payouts(query, lang)
    elif action == "payout_view" and params:
        await partner_payout_view(query, lang, int(params))
    elif action == "payout_confirm" and params:
        await partner_payout_confirm(query, lang, int(params))
    elif action == "payout_reject" and params:
        await partner_payout_reject(query, lang, int(params))
    elif action == "commission" and params:
        await partner_commission_menu(query, lang, int(params))
    elif action == "set_commission" and params:
        parts = params.split("_")
        if len(parts) >= 2:
            await partner_set_commission(query, lang, int(parts[0]), int(parts[1]))
    elif action == "history" and params:
        await partner_history(query, lang, int(params))
    elif action == "referrals" and params:
        await partner_referrals(query, lang, int(params))
    elif action == "deactivate" and params:
        await partner_deactivate(query, lang, int(params))
    elif action == "activate" and params:
        await partner_activate(query, lang, int(params))
    elif action == "stats":
        await partners_stats(query, lang)
    else:
        await partners_main(query, lang)


async def partners_main(query, lang: str):
    """Partners main menu"""
    from core.database.models import Partner, Payout
    
    async with get_db() as session:
        # Total partners
        result = await session.execute(select(func.count(Partner.id)))
        total_partners = result.scalar() or 0
        
        # Active partners
        result = await session.execute(
            select(func.count(Partner.id)).where(Partner.status == "active")
        )
        active_partners = result.scalar() or 0
        
        # Pending applications
        result = await session.execute(
            select(func.count(Partner.id)).where(Partner.status == "pending")
        )
        pending = result.scalar() or 0
        
        # Pending payouts
        result = await session.execute(
            select(func.count(Payout.id)).where(Payout.status == "pending")
        )
        pending_payouts = result.scalar() or 0
    
    text = t(lang, "ADMIN.partners_title") + "\n\n"
    text += t(lang, "ADMIN.partners_total", count=total_partners) + " | "
    text += t(lang, "ADMIN.partners_active", count=active_partners) + "\n"
    text += t(lang, "ADMIN.partners_pending", count=pending) + " | "
    text += t(lang, "ADMIN.partners_payouts_pending", count=pending_payouts) + "\n"
    
    keyboard = [
        [{"text": t(lang, "ADMIN.partners_list"), "callback_data": "admin:partners:list:all"}],
        [{"text": t(lang, "ADMIN.partners_applications", count=pending), "callback_data": "admin:partners:applications"}],
        [{"text": t(lang, "ADMIN.partners_payouts", count=pending_payouts), "callback_data": "admin:partners:payouts"}],
        [{"text": t(lang, "ADMIN.partners_stats"), "callback_data": "admin:partners:stats"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partners_list(query, lang: str, filter_type: str = "all", page: int = 0):
    """Show partners list with filters and pagination"""
    from core.database.models import Partner, User
    
    async with get_db() as session:
        # Base query
        base_query = select(Partner, User).join(User, Partner.user_id == User.id)
        count_query = select(func.count(Partner.id))
        
        # Apply filter
        if filter_type == "active":
            base_query = base_query.where(Partner.status == "active")
            count_query = count_query.where(Partner.status == "active")
        elif filter_type == "pending":
            base_query = base_query.where(Partner.status == "pending")
            count_query = count_query.where(Partner.status == "pending")
        elif filter_type == "rejected":
            base_query = base_query.where(Partner.status == "rejected")
            count_query = count_query.where(Partner.status == "rejected")
        
        # Count
        result = await session.execute(count_query)
        total_count = result.scalar() or 0
        
        # Pagination
        total_pages = max(1, (total_count + PARTNERS_PER_PAGE - 1) // PARTNERS_PER_PAGE)
        page = max(0, min(page, total_pages - 1))
        offset = page * PARTNERS_PER_PAGE
        
        # Get partners
        result = await session.execute(
            base_query.order_by(desc(Partner.created_at)).offset(offset).limit(PARTNERS_PER_PAGE)
        )
        partners = result.all()
    
    text = t(lang, "ADMIN.partners_list_title") + "\n\n"
    
    if total_pages > 1:
        text += t(lang, "ADMIN.page_info", current=page + 1, total=total_pages) + "\n\n"
    
    if not partners:
        text += t(lang, "ADMIN.partners_empty") + "\n"
    else:
        for partner, user in partners:
            status_key = f"partner_status_{partner.status}"
            status = t(lang, f"ADMIN.{status_key}")
            username = f"@{user.telegram_username}" if user.telegram_username else "-"
            
            text += f"{status} <code>{partner.id}</code> | {username}\n"
            if partner.status == "active":
                text += f"   👥 {partner.total_referrals or 0} реф. | 💰 {partner.total_earned or 0} ₽\n"
    
    # Filter buttons
    filter_buttons = []
    for f in PARTNER_FILTERS:
        label = t(lang, f"ADMIN.partners_filter_{f}")
        if f == filter_type:
            label = f"• {label} •"
        filter_buttons.append({"text": label, "callback_data": f"admin:partners:list:{f}"})
    
    keyboard = [filter_buttons[:2], filter_buttons[2:]]
    
    # Partner view buttons
    if partners:
        for partner, user in partners[:5]:
            name = user.display_name[:20]
            keyboard.append([{
                "text": f"👤 #{partner.id} {name}",
                "callback_data": f"admin:partners:view:{partner.id}"
            }])
    
    # Pagination
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append({"text": t(lang, "ADMIN.page_prev"), "callback_data": f"admin:partners:list:{filter_type}_{page - 1}"})
        if page < total_pages - 1:
            pagination.append({"text": t(lang, "ADMIN.page_next"), "callback_data": f"admin:partners:list:{filter_type}_{page + 1}"})
        if pagination:
            keyboard.append(pagination)
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:partners"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_view(query, lang: str, partner_id: int):
    """View partner details"""
    from core.database.models import Partner, User, Referral, Payout
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner, User).join(User, Partner.user_id == User.id).where(Partner.id == partner_id)
        )
        row = result.one_or_none()
        
        if not row:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        partner, user = row
        
        # Count referrals
        result = await session.execute(
            select(func.count(Referral.id)).where(Referral.partner_id == partner_id)
        )
        total_referrals = result.scalar() or 0
        
        # Active referrals (active in last 30 days)
        month_ago = datetime.utcnow() - timedelta(days=30)
        result = await session.execute(
            select(func.count(Referral.id)).where(
                Referral.partner_id == partner_id,
                Referral.is_active == True
            )
        )
        active_referrals = result.scalar() or 0
        
        # Total withdrawn
        result = await session.execute(
            select(func.sum(Payout.amount_gton)).where(
                Payout.partner_id == partner_id,
                Payout.status == "completed"
            )
        )
        total_withdrawn = result.scalar() or 0
    
    # Build text
    text = t(lang, "ADMIN.partner_card_title", id=partner.id) + "\n\n"
    
    if user.telegram_username:
        text += f"📱 @{user.telegram_username}\n"
    text += t(lang, "ADMIN.partner_user", name=user.display_name) + "\n"
    
    if partner.approved_at:
        text += t(lang, "ADMIN.partner_since", date=partner.approved_at.strftime("%d.%m.%Y")) + "\n"
    
    status_text = t(lang, f"ADMIN.partner_status_text_{partner.status}")
    text += t(lang, "ADMIN.partner_status", status=status_text) + "\n\n"
    
    # Finance
    text += t(lang, "ADMIN.partner_finance_title") + "\n"
    text += f"├── " + t(lang, "ADMIN.partner_balance", amount=f"{partner.balance or 0:,}") + "\n"
    text += f"├── " + t(lang, "ADMIN.partner_total_earned", amount=f"{partner.total_earned or 0:,}") + "\n"
    text += f"└── " + t(lang, "ADMIN.partner_withdrawn", amount=f"{total_withdrawn:,}") + "\n\n"
    
    # Referrals
    text += t(lang, "ADMIN.partner_referrals_title") + "\n"
    text += f"├── " + t(lang, "ADMIN.partner_referrals_total", count=total_referrals) + "\n"
    text += f"├── " + t(lang, "ADMIN.partner_referrals_active", count=active_referrals) + "\n"
    text += f"└── " + t(lang, "ADMIN.partner_referrals_earned", amount=f"{partner.total_earned or 0:,}") + "\n\n"
    
    text += t(lang, "ADMIN.partner_commission", percent=partner.level1_percent or 20) + "\n"
    
    # Keyboard
    keyboard = []
    
    if partner.status == "active":
        keyboard.append([
            {"text": t(lang, "ADMIN.partner_action_payout"), "callback_data": f"admin:partners:payout_manual:{partner.id}"},
            {"text": t(lang, "ADMIN.partner_action_commission"), "callback_data": f"admin:partners:commission:{partner.id}"}
        ])
        keyboard.append([
            {"text": t(lang, "ADMIN.partner_action_referrals"), "callback_data": f"admin:partners:referrals:{partner.id}"},
            {"text": t(lang, "ADMIN.partner_action_history"), "callback_data": f"admin:partners:history:{partner.id}"}
        ])
        keyboard.append([{"text": t(lang, "ADMIN.partner_action_deactivate"), "callback_data": f"admin:partners:deactivate:{partner.id}"}])
    elif partner.status == "inactive":
        keyboard.append([{"text": t(lang, "ADMIN.partner_action_activate"), "callback_data": f"admin:partners:activate:{partner.id}"}])
        keyboard.append([{"text": t(lang, "ADMIN.partner_action_history"), "callback_data": f"admin:partners:history:{partner.id}"}])
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:partners:list:all"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_applications(query, lang: str):
    """Show pending partner applications"""
    from core.database.models import Partner, User, Referral, Transaction
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner, User).join(
                User, Partner.user_id == User.id
            ).where(Partner.status == "pending").order_by(desc(Partner.applied_at))
        )
        applications = result.all()
        
        # Get stats for each application
        app_stats = []
        for partner, user in applications:
            # Referrals count
            result = await session.execute(
                select(func.count(Referral.id)).where(Referral.referrer_id == user.id)
            )
            ref_count = result.scalar() or 0
            
            # Referrals spent
            result = await session.execute(
                select(func.sum(Referral.total_payments)).where(Referral.referrer_id == user.id)
            )
            ref_spent = result.scalar() or 0
            
            app_stats.append((partner, user, ref_count, ref_spent))
    
    text = t(lang, "ADMIN.partners_apps_title") + "\n\n"
    text += t(lang, "ADMIN.partners_apps_pending", count=len(applications)) + "\n\n"
    
    if not applications:
        text += t(lang, "ADMIN.partners_apps_empty")
    else:
        for i, (partner, user, ref_count, ref_spent) in enumerate(app_stats, 1):
            # Time ago
            if partner.applied_at:
                diff = datetime.utcnow() - partner.applied_at
                if diff.days > 0:
                    time_ago = f"{diff.days} дн."
                elif diff.seconds > 3600:
                    time_ago = f"{diff.seconds // 3600} ч."
                else:
                    time_ago = f"{diff.seconds // 60} мин."
            else:
                time_ago = "-"
            
            username = f"@{user.telegram_username}" if user.telegram_username else user.display_name
            text += f"{i}. {username} — {time_ago}\n"
            text += f"   " + t(lang, "ADMIN.partner_app_referrals", count=ref_count) + " | "
            text += t(lang, "ADMIN.partner_app_spent", amount=f"{ref_spent:,}") + "\n\n"
    
    keyboard = []
    for partner, user, _, _ in app_stats[:10]:
        name = user.display_name[:20]
        keyboard.append([{
            "text": f"{t(lang, 'ADMIN.partner_app_review')} #{partner.id}",
            "callback_data": f"admin:partners:app_review:{partner.id}"
        }])
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:partners"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_app_review(query, lang: str, partner_id: int):
    """Review partner application"""
    from core.database.models import Partner, User, Referral, Transaction
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner, User).join(User, Partner.user_id == User.id).where(Partner.id == partner_id)
        )
        row = result.one_or_none()
        
        if not row:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        partner, user = row
        
        # User stats
        result = await session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_id == user.id)
        )
        ref_count = result.scalar() or 0
        
        result = await session.execute(
            select(func.sum(Referral.total_payments)).where(Referral.referrer_id == user.id)
        )
        ref_spent = result.scalar() or 0
        
        # Own spending
        result = await session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user.id,
                Transaction.type == "usage"
            )
        )
        own_spent = result.scalar() or 0
    
    text = t(lang, "ADMIN.partner_review_title") + "\n\n"
    
    username = f"@{user.telegram_username}" if user.telegram_username else "-"
    text += f"📱 {username}\n"
    text += t(lang, "ADMIN.partner_user", name=user.display_name) + "\n"
    
    if partner.applied_at:
        text += t(lang, "ADMIN.partner_review_submitted", date=partner.applied_at.strftime("%d.%m.%Y %H:%M")) + "\n\n"
    
    text += t(lang, "ADMIN.partner_review_user_stats") + "\n"
    text += f"├── " + t(lang, "ADMIN.partner_review_member_since", date=user.created_at.strftime("%d.%m.%Y")) + "\n"
    text += f"├── " + t(lang, "ADMIN.partner_app_referrals", count=ref_count) + "\n"
    text += f"├── " + t(lang, "ADMIN.partner_app_spent", amount=f"{ref_spent:,}") + "\n"
    text += f"└── " + t(lang, "ADMIN.partner_review_own_spent", amount=f"{own_spent:,}") + "\n"
    
    keyboard = [
        [{"text": t(lang, "ADMIN.partner_review_approve", percent=20), "callback_data": f"admin:partners:app_approve:{partner_id}_20"}],
        [{"text": t(lang, "ADMIN.partner_review_approve", percent=25), "callback_data": f"admin:partners:app_approve:{partner_id}_25"}],
        [{"text": t(lang, "ADMIN.partner_review_approve", percent=30), "callback_data": f"admin:partners:app_approve:{partner_id}_30"}],
        [{"text": "✏️ Свой процент", "callback_data": f"admin:partners:app_custom:{partner_id}"}],
        [{"text": t(lang, "ADMIN.partner_review_reject"), "callback_data": f"admin:partners:app_reject:{partner_id}"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:partners:applications"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_app_approve(query, lang: str, partner_id: int, commission: int):
    """Approve partner application"""
    from core.database.models import Partner, User
    
    target_telegram_id = None
    target_lang = "ru"
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner, User).join(User, Partner.user_id == User.id).where(Partner.id == partner_id)
        )
        row = result.one_or_none()
        
        if not row:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        partner, user = row
        target_telegram_id = user.telegram_id
        target_lang = user.language or "ru"
        
        partner.status = "active"
        partner.level1_percent = commission
        partner.approved_at = datetime.utcnow()
    
    # Notify user
    if target_telegram_id:
        notify_text = t(target_lang, "ADMIN.notify_partner_approved", percent=commission)
        await notify_user(target_telegram_id, notify_text)
    
    await query.answer("✅ Заявка одобрена!", show_alert=True)
    await partner_applications(query, lang)


async def partner_app_custom(query, lang: str, partner_id: int):
    """Ask admin to enter custom commission percent"""
    from core.plugins.core_api import CoreAPI
    
    # Get admin user_id
    admin_telegram_id = query.from_user.id
    async with get_db() as session:
        from core.database.models import User
        result = await session.execute(
            select(User.id).where(User.telegram_id == admin_telegram_id)
        )
        admin_id = result.scalar_one_or_none()
    
    if not admin_id:
        await query.answer("Ошибка", show_alert=True)
        return
    
    # Set state for input
    core_api = CoreAPI("core")
    await core_api.set_user_state(admin_id, "admin_partner_custom_percent", {
        "partner_id": partner_id
    })
    
    text = "✏️ <b>Введите процент комиссии</b>\n\n"
    text += "Укажите процент, который партнёр будет получать с покупок рефералов.\n\n"
    text += "Например: <code>15</code> или <code>22.5</code>"
    
    keyboard = [
        [{"text": "❌ Отмена", "callback_data": f"admin:partners:app_view:{partner_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_partner_custom_percent(update, context, admin_id: int, lang: str, partner_id: int):
    """Handle custom percent input from admin"""
    from core.database.models import Partner, User
    from core.plugins.core_api import CoreAPI
    
    core_api = CoreAPI("core")
    text_input = update.message.text.strip()
    
    # Parse percent
    try:
        # Replace comma with dot for decimal
        text_input = text_input.replace(",", ".")
        commission = float(text_input)
        
        if commission <= 0 or commission > 100:
            await update.message.reply_text("❌ Процент должен быть от 0 до 100")
            return
    except ValueError:
        await update.message.reply_text("❌ Введите число (например: 15 или 22.5)")
        return
    
    # Approve partner with custom percent
    target_telegram_id = None
    target_lang = "ru"
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner, User).join(User, Partner.user_id == User.id).where(Partner.id == partner_id)
        )
        row = result.one_or_none()
        
        if not row:
            await update.message.reply_text("❌ Заявка не найдена")
            await core_api.clear_user_state(admin_id)
            return
        
        partner, user = row
        target_telegram_id = user.telegram_id
        target_lang = user.language or "ru"
        
        partner.status = "active"
        partner.level1_percent = commission
        partner.approved_at = datetime.utcnow()
    
    # Clear state
    await core_api.clear_user_state(admin_id)
    
    # Notify user
    if target_telegram_id:
        notify_text = t(target_lang, "ADMIN.notify_partner_approved", percent=commission)
        await notify_user(target_telegram_id, notify_text)
    
    keyboard = [
        [{"text": "← К заявкам", "callback_data": "admin:partners:applications"}]
    ]
    
    await update.message.reply_text(
        f"✅ Партнёр одобрен с комиссией <b>{commission}%</b>",
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_app_reject(query, lang: str, partner_id: int):
    """Reject partner application"""
    from core.database.models import Partner, User
    
    target_telegram_id = None
    target_lang = "ru"
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner, User).join(User, Partner.user_id == User.id).where(Partner.id == partner_id)
        )
        row = result.one_or_none()
        
        if not row:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        partner, user = row
        target_telegram_id = user.telegram_id
        target_lang = user.language or "ru"
        
        partner.status = "rejected"
        partner.rejected_at = datetime.utcnow()
    
    # Notify user
    if target_telegram_id:
        notify_text = t(target_lang, "ADMIN.notify_partner_rejected")
        await notify_user(target_telegram_id, notify_text)
    
    await query.answer("❌ Заявка отклонена", show_alert=True)
    await partner_applications(query, lang)


async def partner_payouts(query, lang: str):
    """Show pending payouts — GTON"""
    from decimal import Decimal
    from core.database.models import Payout, Partner, User
    from core.platform.telegram.utils import format_gton
    
    async with get_db() as session:
        result = await session.execute(
            select(Payout, Partner, User).join(
                Partner, Payout.partner_id == Partner.id
            ).join(
                User, Partner.user_id == User.id
            ).where(Payout.status == "pending").order_by(desc(Payout.created_at))
        )
        payouts = result.all()
        
        # Total sum GTON
        result = await session.execute(
            select(func.sum(Payout.amount_gton)).where(Payout.status == "pending")
        )
        total_gton = Decimal(str(result.scalar() or 0))
        
        # Total fiat
        result = await session.execute(
            select(func.sum(Payout.amount_fiat)).where(Payout.status == "pending")
        )
        total_fiat = Decimal(str(result.scalar() or 0))
    
    text = t(lang, "ADMIN.partners_payouts_title") + "\n\n"
    text += f"⏳ Ожидает: {len(payouts)} заявок\n"
    text += f"💰 Сумма: {format_gton(total_gton)} GTON (~{total_fiat:,.0f} ₽)\n\n"
    
    if not payouts:
        text += "Нет заявок на вывод."
    else:
        for i, (payout, partner, user) in enumerate(payouts, 1):
            username = f"@{user.telegram_username}" if user.telegram_username else user.display_name
            gton = Decimal(str(payout.amount_gton))
            fiat = Decimal(str(payout.amount_fiat))
            text += f"{i}. {username}\n"
            text += f"   💰 {format_gton(gton)} GTON → {fiat:,.0f} ₽\n"
            text += f"   📱 {payout.method.upper()}\n\n"
    
    keyboard = []
    for payout, partner, user in payouts[:10]:
        keyboard.append([{
            "text": f"{t(lang, 'ADMIN.partner_payout_process')} #{payout.id}",
            "callback_data": f"admin:partners:payout_view:{payout.id}"
        }])
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:partners"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_payout_view(query, lang: str, payout_id: int):
    """View payout details — GTON"""
    from decimal import Decimal
    from core.database.models import Payout, Partner, User
    from core.platform.telegram.utils import format_gton
    
    async with get_db() as session:
        result = await session.execute(
            select(Payout, Partner, User).join(
                Partner, Payout.partner_id == Partner.id
            ).join(
                User, Partner.user_id == User.id
            ).where(Payout.id == payout_id)
        )
        row = result.one_or_none()
        
        if not row:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        payout, partner, user = row
    
    gton = Decimal(str(payout.amount_gton))
    fiat = Decimal(str(payout.amount_fiat))
    fee = Decimal(str(payout.fee_gton or 0))
    
    username = f"@{user.telegram_username}" if user.telegram_username else user.display_name
    details_str = ""
    if payout.details:
        if isinstance(payout.details, dict):
            details_str = payout.details.get("card") or payout.details.get("phone") or str(payout.details)
        else:
            details_str = str(payout.details)
    
    text = "💸 <b>Заявка на вывод</b>\n\n"
    text += f"👤 Партнёр: {username}\n"
    text += f"🆔 ID: {partner.id}\n\n"
    text += f"💰 Сумма: {format_gton(gton)} GTON\n"
    if fee > 0:
        text += f"💸 Комиссия: {format_gton(fee)} GTON\n"
    text += f"💵 К выплате: {fiat:,.0f} ₽\n"
    text += f"💱 Курс: 1 GTON = {payout.gton_rate:,.2f} ₽\n\n"
    text += f"📱 Метод: {payout.method.upper()}\n"
    text += f"📝 Реквизиты: {details_str}\n"
    
    keyboard = [
        [{"text": t(lang, "ADMIN.partner_payout_confirm"), "callback_data": f"admin:partners:payout_confirm:{payout_id}"}],
        [{"text": t(lang, "ADMIN.partner_payout_reject"), "callback_data": f"admin:partners:payout_reject:{payout_id}"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:partners:payouts"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_payout_confirm(query, lang: str, payout_id: int):
    """Confirm payout — использует PayoutService"""
    from decimal import Decimal
    from core.database.models import Payout, Partner, User
    from core.payout import payout_service
    from core.platform.telegram.utils import format_gton, get_or_create_user
    
    # Get admin user_id
    admin_telegram_id = query.from_user.id
    admin_user_id = await get_or_create_user(admin_telegram_id, query.from_user)
    
    # Approve via service
    result = await payout_service.approve_payout(payout_id, admin_user_id)
    
    if not result.success:
        await query.answer(f"❌ {result.error}", show_alert=True)
        return
    
    # Get payout details for notification
    async with get_db() as session:
        res = await session.execute(
            select(Payout, Partner, User).join(
                Partner, Payout.partner_id == Partner.id
            ).join(
                User, Partner.user_id == User.id
            ).where(Payout.id == payout_id)
        )
        row = res.one_or_none()
        
        if row:
            payout, partner, user = row
            target_telegram_id = user.telegram_id
            target_lang = user.language or "ru"
            
            # Notify user
            if target_telegram_id:
                gton_str = format_gton(Decimal(str(payout.amount_gton)))
                fiat_str = f"{payout.amount_fiat:,.0f}"
                notify_text = f"✅ Вывод одобрен!\n\n💰 {gton_str} GTON → {fiat_str} ₽\n📱 {payout.method.upper()}"
                await notify_user(target_telegram_id, notify_text)
    
    await query.answer("✅ Вывод одобрен!", show_alert=True)
    await partner_payouts(query, lang)


async def partner_payout_reject(query, lang: str, payout_id: int):
    """Reject payout — использует PayoutService (размораживает средства)"""
    from decimal import Decimal
    from core.database.models import Payout, Partner, User
    from core.payout import payout_service
    from core.platform.telegram.utils import format_gton, get_or_create_user
    
    # Get admin user_id
    admin_telegram_id = query.from_user.id
    admin_user_id = await get_or_create_user(admin_telegram_id, query.from_user)
    
    # Get payout details before rejection
    async with get_db() as session:
        res = await session.execute(
            select(Payout, Partner, User).join(
                Partner, Payout.partner_id == Partner.id
            ).join(
                User, Partner.user_id == User.id
            ).where(Payout.id == payout_id)
        )
        row = res.one_or_none()
        
        if not row:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        payout, partner, user = row
        target_telegram_id = user.telegram_id
        gton_amount = Decimal(str(payout.amount_gton))
    
    # Reject via service (unfreezes funds)
    result = await payout_service.reject_payout(payout_id, admin_user_id, "Отклонено администратором")
    
    if not result.success:
        await query.answer(f"❌ {result.error}", show_alert=True)
        return
    
    # Notify user
    if target_telegram_id:
        gton_str = format_gton(gton_amount)
        notify_text = f"❌ Заявка на вывод отклонена\n\n💰 {gton_str} GTON возвращены на баланс"
        await notify_user(target_telegram_id, notify_text)
    
    await query.answer("❌ Заявка отклонена, средства разморожены", show_alert=True)
    await partner_payouts(query, lang)


async def partner_commission_menu(query, lang: str, partner_id: int):
    """Show commission change menu"""
    from core.database.models import Partner
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner).where(Partner.id == partner_id)
        )
        partner = result.scalar_one_or_none()
        
        if not partner:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
    
    text = t(lang, "ADMIN.partner_commission_title") + "\n\n"
    text += t(lang, "ADMIN.partner_commission_current", percent=partner.level1_percent or 20) + "\n\n"
    text += t(lang, "ADMIN.partner_commission_select")
    
    commissions = [15, 20, 25, 30, 35, 40]
    keyboard = []
    row = []
    for c in commissions:
        label = f"• {c}% •" if c == partner.level1_percent else f"{c}%"
        row.append({"text": label, "callback_data": f"admin:partners:set_commission:{partner_id}_{c}"})
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": f"admin:partners:view:{partner_id}"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_set_commission(query, lang: str, partner_id: int, commission: int):
    """Set partner commission"""
    from core.database.models import Partner
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner).where(Partner.id == partner_id)
        )
        partner = result.scalar_one_or_none()
        
        if not partner:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        partner.level1_percent = commission
    
    await query.answer(t(lang, "ADMIN.partner_commission_success", percent=commission), show_alert=True)
    await partner_view(query, lang, partner_id)


async def partner_history(query, lang: str, partner_id: int):
    """Show partner payout history"""
    from core.database.models import Payout, Partner
    
    async with get_db() as session:
        result = await session.execute(
            select(Payout).where(Payout.partner_id == partner_id).order_by(desc(Payout.created_at)).limit(20)
        )
        payouts = result.scalars().all()
    
    text = t(lang, "ADMIN.partner_history_title", id=partner_id) + "\n\n"
    
    if not payouts:
        text += t(lang, "ADMIN.partner_history_empty")
    else:
        for payout in payouts:
            if payout.status == "completed":
                status = t(lang, "ADMIN.partner_history_paid")
            elif payout.status == "rejected":
                status = t(lang, "ADMIN.partner_history_rejected")
            else:
                status = t(lang, "ADMIN.partner_history_pending")
            
            date = payout.created_at.strftime("%d.%m.%Y")
            text += f"{status} {payout.amount_fiat:,.0f} ₽ — {date}\n"
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:partners:view:{partner_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_referrals(query, lang: str, partner_id: int):
    """Show partner referrals"""
    from core.database.models import Referral, User, Partner
    
    async with get_db() as session:
        result = await session.execute(
            select(Referral, User).join(
                User, Referral.referred_id == User.id
            ).where(Referral.partner_id == partner_id).order_by(desc(Referral.created_at)).limit(20)
        )
        referrals = result.all()
    
    text = t(lang, "ADMIN.partner_referrals_title") + f" #{partner_id}\n\n"
    
    if not referrals:
        text += "—"
    else:
        text += f"{len(referrals)}\n\n"
        for ref, user in referrals:
            status = "✅" if ref.is_active else "❌"
            name = user.display_name
            text += f"{status} {name}\n"
            text += f"   💰 {ref.total_payments or 0} ₽\n"
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:partners:view:{partner_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_deactivate(query, lang: str, partner_id: int):
    """Deactivate partner"""
    from core.database.models import Partner, User
    
    target_telegram_id = None
    target_lang = "ru"
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner, User).join(User, Partner.user_id == User.id).where(Partner.id == partner_id)
        )
        row = result.one_or_none()
        
        if not row:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        partner, user = row
        target_telegram_id = user.telegram_id
        target_lang = user.language or "ru"
        
        partner.status = "inactive"
        partner.deactivated_at = datetime.utcnow()
    
    # Notify user
    if target_telegram_id:
        notify_text = t(target_lang, "ADMIN.notify_partner_deactivated")
        await notify_user(target_telegram_id, notify_text)
    
    await query.answer("🔴 Партнёр деактивирован", show_alert=True)
    await partner_view(query, lang, partner_id)


async def partner_activate(query, lang: str, partner_id: int):
    """Activate partner"""
    from core.database.models import Partner, User
    
    target_telegram_id = None
    target_lang = "ru"
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner, User).join(User, Partner.user_id == User.id).where(Partner.id == partner_id)
        )
        row = result.one_or_none()
        
        if not row:
            await query.answer(t(lang, "COMMON.not_found"), show_alert=True)
            return
        
        partner, user = row
        target_telegram_id = user.telegram_id
        target_lang = user.language or "ru"
        
        partner.status = "active"
    
    # Notify user
    if target_telegram_id:
        notify_text = t(target_lang, "ADMIN.notify_partner_activated")
        await notify_user(target_telegram_id, notify_text)
    
    await query.answer("✅ Партнёр активирован", show_alert=True)
    await partner_view(query, lang, partner_id)


async def partners_stats(query, lang: str):
    """Show partners statistics"""
    from core.database.models import Partner, Referral, Payout, User
    
    month_ago = datetime.utcnow() - timedelta(days=30)
    
    async with get_db() as session:
        # Total partners
        result = await session.execute(select(func.count(Partner.id)))
        total_partners = result.scalar() or 0
        
        # Active partners
        result = await session.execute(
            select(func.count(Partner.id)).where(Partner.status == "active")
        )
        active_partners = result.scalar() or 0
        
        # Total referrals
        result = await session.execute(select(func.count(Referral.id)))
        total_referrals = result.scalar() or 0
        
        # Paid this month
        result = await session.execute(
            select(func.sum(Payout.amount_fiat)).where(
                Payout.status == "completed",
                Payout.processed_at >= month_ago
            )
        )
        paid_month = result.scalar() or 0
        
        # Paid total
        result = await session.execute(
            select(func.sum(Payout.amount_fiat)).where(Payout.status == "completed")
        )
        paid_total = result.scalar() or 0
        
        # Top partners
        result = await session.execute(
            select(Partner, User).join(
                User, Partner.user_id == User.id
            ).where(Partner.status == "active").order_by(desc(Partner.total_earned)).limit(5)
        )
        top_partners = result.all()
    
    text = t(lang, "ADMIN.partners_stats_title") + "\n\n"
    text += t(lang, "ADMIN.partners_stats_total", count=total_partners) + "\n"
    text += t(lang, "ADMIN.partners_stats_active", count=active_partners) + "\n"
    text += t(lang, "ADMIN.partners_stats_referrals", count=total_referrals) + "\n\n"
    text += t(lang, "ADMIN.partners_stats_paid_month", amount=f"{paid_month:,}") + "\n"
    text += t(lang, "ADMIN.partners_stats_paid_total", amount=f"{paid_total:,}") + "\n\n"
    
    if top_partners:
        text += t(lang, "ADMIN.partners_stats_top") + "\n"
        for i, (partner, user) in enumerate(top_partners, 1):
            name = user.display_name
            text += f"{i}. {name}: {partner.total_earned or 0:,} ₽\n"
    
    keyboard = [
        [{"text": t(lang, "ADMIN.stats_refresh"), "callback_data": "admin:partners:stats"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:partners"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
