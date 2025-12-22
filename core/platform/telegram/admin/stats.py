"""
Admin Statistics — Статистика в GTON
"""
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_

from core.locales import t
from core.database import get_db
from core.platform.telegram.utils import build_keyboard, format_gton
from core.payments.converter import currency_converter


# Period keys for localization
PERIOD_KEYS = ["today", "week", "month", "all"]


def get_period_label(lang: str, period: str) -> str:
    """Get localized period label"""
    return t(lang, f"ADMIN.period_{period}")


def get_period_dates(period: str) -> tuple[datetime, datetime]:
    """Get start and end dates for period"""
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if period == "today":
        return today, now
    elif period == "week":
        return today - timedelta(days=7), now
    elif period == "month":
        return today - timedelta(days=30), now
    else:  # all
        return datetime(2020, 1, 1), now


async def admin_stats(query, lang: str, action: str = None, params: str = None):
    """Admin statistics router"""
    if action == "users":
        period = params or "week"
        await stats_users(query, lang, period)
    elif action == "finance":
        period = params or "month"
        await stats_finance(query, lang, period)
    elif action == "bonus":
        period = params or "week"
        await stats_daily_bonus(query, lang, period)
    elif action == "referrals":
        period = params or "month"
        await stats_referrals(query, lang, period)
    elif action == "analytics":
        period = params or "week"
        await stats_analytics(query, lang, period)
    else:
        await stats_main(query, lang)


async def stats_main(query, lang: str):
    """Main statistics dashboard"""
    from core.database.models import User, Transaction, Wallet, DailyBonus, Referral
    
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    
    async with get_db() as session:
        # Users
        result = await session.execute(select(func.count(User.id)))
        total_users = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(User.id)).where(User.created_at >= today)
        )
        users_today = result.scalar() or 0
        
        # Revenue today
        result = await session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.type == "deposit",
                Transaction.status == "completed",
                Transaction.created_at >= today
            )
        )
        revenue_today = result.scalar() or 0
        
        # Daily bonus claims today
        result = await session.execute(
            select(func.count(DailyBonus.id)).where(
                DailyBonus.last_claim_at >= today
            )
        )
        bonus_today = result.scalar() or 0
        
        # New referrals today
        result = await session.execute(
            select(func.count(Referral.id)).where(Referral.created_at >= today)
        )
        referrals_today = result.scalar() or 0
    
    text = t(lang, "ADMIN.stats_title") + "\n\n"
    text += f"👥 {total_users:,} (+{users_today} {t(lang, 'ADMIN.period_today').lower()})\n"
    text += t(lang, "ADMIN.stats_revenue_today", amount=f"{revenue_today:,}") + "\n"
    text += t(lang, "ADMIN.stats_claims_today", count=bonus_today) + "\n"
    text += t(lang, "ADMIN.stats_referrals_period", count=referrals_today) + "\n"
    
    keyboard = [
        [{"text": t(lang, "ADMIN.stats_users_btn"), "callback_data": "admin:stats:users:week"}],
        [{"text": t(lang, "ADMIN.stats_finance_btn"), "callback_data": "admin:stats:finance:month"}],
        [{"text": t(lang, "ADMIN.stats_bonus_btn"), "callback_data": "admin:stats:bonus:week"}],
        [{"text": t(lang, "ADMIN.stats_referrals_btn"), "callback_data": "admin:stats:referrals:month"}],
        [{"text": t(lang, "ADMIN.stats_analytics_btn"), "callback_data": "admin:stats:analytics:week"}],
        [{"text": t(lang, "ADMIN.stats_refresh"), "callback_data": "admin:stats"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


def period_keyboard(base_callback: str, current: str, lang: str) -> list:
    """Generate period filter keyboard"""
    buttons = []
    for key in PERIOD_KEYS:
        label = get_period_label(lang, key)
        if key == current:
            label = f"• {label} •"
        buttons.append({"text": label, "callback_data": f"{base_callback}:{key}"})
    
    return [
        buttons[:2],
        buttons[2:],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:stats"}]
    ]


def get_day_name(lang: str, weekday: int) -> str:
    """Get localized day name"""
    days = ["day_mon", "day_tue", "day_wed", "day_thu", "day_fri", "day_sat", "day_sun"]
    return t(lang, f"ADMIN.{days[weekday]}")


async def stats_users(query, lang: str, period: str = "week"):
    """User statistics"""
    from core.database.models import User
    
    start_date, end_date = get_period_dates(period)
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    async with get_db() as session:
        # Total users
        result = await session.execute(select(func.count(User.id)))
        total_users = result.scalar() or 0
        
        # New in period
        result = await session.execute(
            select(func.count(User.id)).where(User.created_at >= start_date)
        )
        new_users = result.scalar() or 0
        
        # Today
        result = await session.execute(
            select(func.count(User.id)).where(User.created_at >= today)
        )
        users_today = result.scalar() or 0
        
        # This week
        result = await session.execute(
            select(func.count(User.id)).where(User.created_at >= week_ago)
        )
        users_week = result.scalar() or 0
        
        # This month
        result = await session.execute(
            select(func.count(User.id)).where(User.created_at >= month_ago)
        )
        users_month = result.scalar() or 0
        
        # Active 7d
        result = await session.execute(
            select(func.count(User.id)).where(User.last_activity_at >= week_ago)
        )
        active_7d = result.scalar() or 0
        
        # Active 30d
        result = await session.execute(
            select(func.count(User.id)).where(User.last_activity_at >= month_ago)
        )
        active_30d = result.scalar() or 0
        
        # Blocked
        result = await session.execute(
            select(func.count(User.id)).where(User.is_blocked == True)
        )
        blocked = result.scalar() or 0
        
        # Daily registrations for chart (last 7 days)
        daily_stats = []
        for i in range(6, -1, -1):
            day_start = today - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            result = await session.execute(
                select(func.count(User.id)).where(
                    and_(User.created_at >= day_start, User.created_at < day_end)
                )
            )
            count = result.scalar() or 0
            daily_stats.append((day_start, count))
    
    # Calculate percentages
    active_7d_pct = round(active_7d / total_users * 100) if total_users else 0
    active_30d_pct = round(active_30d / total_users * 100) if total_users else 0
    
    text = t(lang, "ADMIN.stats_users_title") + "\n\n"
    text += t(lang, "ADMIN.stats_users_total", count=f"{total_users:,}") + "\n"
    text += f"├── " + t(lang, "ADMIN.stats_users_today", count=users_today) + "\n"
    text += f"├── " + t(lang, "ADMIN.stats_users_week", count=users_week) + "\n"
    text += f"└── " + t(lang, "ADMIN.stats_users_month", count=users_month) + "\n\n"
    text += t(lang, "ADMIN.stats_activity") + "\n"
    text += f"├── " + t(lang, "ADMIN.stats_active_7d", count=f"{active_7d:,}", percent=active_7d_pct) + "\n"
    text += f"├── " + t(lang, "ADMIN.stats_active_30d", count=f"{active_30d:,}", percent=active_30d_pct) + "\n"
    text += f"└── " + t(lang, "ADMIN.stats_inactive", count=f"{total_users - active_30d:,}") + "\n\n"
    text += t(lang, "ADMIN.stats_blocked", count=blocked) + "\n\n"
    
    # Text chart
    text += t(lang, "ADMIN.stats_registrations") + "\n"
    max_count = max(c for _, c in daily_stats) if daily_stats else 1
    for day_date, count in daily_stats:
        day_name = get_day_name(lang, day_date.weekday())
        bar_len = int(count / max_count * 10) if max_count else 0
        bar = "█" * bar_len
        text += f"<code>{day_name} {bar.ljust(10)} {count}</code>\n"
    
    keyboard = period_keyboard("admin:stats:users", period, lang)
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def stats_finance(query, lang: str, period: str = "month"):
    """Financial statistics"""
    from core.database.models import Transaction, Wallet, User
    
    start_date, end_date = get_period_dates(period)
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    async with get_db() as session:
        # Total balance (GTON)
        result = await session.execute(
            select(func.sum(Wallet.balance)).where(Wallet.wallet_type == "main")
        )
        total_balance = Decimal(str(result.scalar() or 0))
        
        # Revenue in period (GTON from credit transactions)
        result = await session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.type == "credit",
                Transaction.source == "payment",
                Transaction.status == "completed",
                Transaction.created_at >= start_date
            )
        )
        revenue_period = Decimal(str(result.scalar() or 0))
        
        # Revenue today
        result = await session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.type == "credit",
                Transaction.source == "payment",
                Transaction.status == "completed",
                Transaction.created_at >= today
            )
        )
        revenue_today = Decimal(str(result.scalar() or 0))
        
        # Transactions count
        result = await session.execute(
            select(func.count(Transaction.id)).where(
                Transaction.type == "credit",
                Transaction.source == "payment",
                Transaction.status == "completed",
                Transaction.created_at >= start_date
            )
        )
        tx_count = result.scalar() or 0
        
        # Average check
        avg_check = revenue_period / tx_count if tx_count else Decimal("0")
        
        # Spending in period (debit transactions)
        result = await session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.type == "debit",
                Transaction.created_at >= start_date
            )
        )
        spending = Decimal(str(result.scalar() or 0))
        
        # Top spenders (by debit transactions)
        result = await session.execute(
            select(
                User.id,
                User.telegram_username,
                User.first_name,
                func.sum(Transaction.amount).label("total")
            ).join(
                Transaction, User.id == Transaction.user_id
            ).where(
                Transaction.type == "debit",
                Transaction.created_at >= start_date
            ).group_by(User.id).order_by(
                func.sum(Transaction.amount).desc()
            ).limit(5)
        )
        top_spenders = result.all()
    
    # Get fiat equivalents
    total_fiat = await currency_converter.convert_from_gton(total_balance, "RUB")
    revenue_fiat = await currency_converter.convert_from_gton(revenue_period, "RUB")
    
    period_label = get_period_label(lang, period)
    
    # Format amounts
    total_str = f"{format_gton(total_balance)} GTON"
    if total_fiat:
        total_str += f" (~{total_fiat:,.0f} ₽)"
    
    revenue_str = f"{format_gton(revenue_period)} GTON"
    if revenue_fiat:
        revenue_str += f" (~{revenue_fiat:,.0f} ₽)"
    
    text = f"📊 <b>Финансы</b> ({period_label})\n\n"
    text += f"💰 Общий баланс: {total_str}\n\n"
    text += "📈 Пополнения:\n"
    text += f"├── Сегодня: {format_gton(revenue_today)} GTON\n"
    text += f"└── За период: {revenue_str}\n\n"
    text += f"📊 Транзакций: {tx_count}\n"
    text += f"📉 Средний чек: {format_gton(avg_check)} GTON\n"
    text += f"💸 Потрачено: {format_gton(spending)} GTON\n\n"
    
    if top_spenders:
        text += "🏆 Топ по тратам:\n"
        for i, (uid, username, name, total) in enumerate(top_spenders, 1):
            display = f"@{username}" if username else name or f"#{uid}"
            total_gton = format_gton(Decimal(str(total)))
            text += f"{i}. {display}: {total_gton} GTON\n"
    
    keyboard = period_keyboard("admin:stats:finance", period, lang)
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def stats_daily_bonus(query, lang: str, period: str = "week"):
    """Daily bonus statistics"""
    from core.database.models import DailyBonus, DailyBonusHistory
    
    start_date, end_date = get_period_dates(period)
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    async with get_db() as session:
        # Claims today
        result = await session.execute(
            select(func.count(DailyBonus.id)).where(
                DailyBonus.last_claim_at >= today
            )
        )
        claims_today = result.scalar() or 0
        
        # Claims in period
        result = await session.execute(
            select(func.count(DailyBonusHistory.id)).where(
                DailyBonusHistory.claimed_at >= start_date
            )
        )
        claims_period = result.scalar() or 0
        
        # GTON given in period
        result = await session.execute(
            select(func.sum(DailyBonusHistory.tokens)).where(
                DailyBonusHistory.claimed_at >= start_date
            )
        )
        gton_given = Decimal(str(result.scalar() or 0))
        
        # Average streak
        result = await session.execute(
            select(func.avg(DailyBonus.current_streak))
        )
        avg_streak = round(result.scalar() or 0, 1)
        
        # Max streak
        result = await session.execute(
            select(func.max(DailyBonus.max_streak))
        )
        max_streak = result.scalar() or 0
        
        # Users with active streaks (claimed in last 2 days)
        two_days_ago = today - timedelta(days=2)
        result = await session.execute(
            select(func.count(DailyBonus.id)).where(
                DailyBonus.last_claim_at >= two_days_ago
            )
        )
        active_streaks = result.scalar() or 0
    
    period_label = get_period_label(lang, period)
    gton_str = format_gton(gton_given)
    
    text = f"🎁 <b>Ежедневный бонус</b> ({period_label})\n\n"
    text += f"📊 Получений сегодня: {claims_today}\n"
    text += f"📊 За период: {claims_period}\n\n"
    text += f"💰 Выдано: {gton_str} GTON\n\n"
    text += "🔥 Серии:\n"
    text += f"├── Средняя: {avg_streak} дней\n"
    text += f"├── Максимальная: {max_streak} дней\n"
    text += f"└── Активных: {active_streaks}\n"
    
    keyboard = period_keyboard("admin:stats:bonus", period, lang)
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def stats_referrals(query, lang: str, period: str = "month"):
    """Referral statistics"""
    from core.database.models import Referral, Partner, Transaction, User
    
    start_date, end_date = get_period_dates(period)
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    async with get_db() as session:
        # Total referrals
        result = await session.execute(select(func.count(Referral.id)))
        total_referrals = result.scalar() or 0
        
        # New in period
        result = await session.execute(
            select(func.count(Referral.id)).where(Referral.created_at >= start_date)
        )
        new_referrals = result.scalar() or 0
        
        # Active partners
        result = await session.execute(
            select(func.count(Partner.id)).where(Partner.status == "active")
        )
        active_partners = result.scalar() or 0
        
        # Commissions paid in period (from Commission model)
        from core.database.models import Commission
        result = await session.execute(
            select(func.sum(Commission.commission_amount)).where(
                Commission.created_at >= start_date
            )
        )
        commissions_paid = Decimal(str(result.scalar() or 0))
        
        # Top referrers
        result = await session.execute(
            select(
                User.id,
                User.telegram_username,
                User.first_name,
                func.count(Referral.id).label("count")
            ).join(
                Referral, User.id == Referral.referrer_id
            ).where(
                Referral.created_at >= start_date
            ).group_by(User.id).order_by(
                func.count(Referral.id).desc()
            ).limit(5)
        )
        top_referrers = result.all()
    
    period_label = get_period_label(lang, period)
    commissions_str = format_gton(commissions_paid)
    
    text = f"🤝 <b>Рефералы</b> ({period_label})\n\n"
    text += f"👥 Всего рефералов: {total_referrals:,}\n"
    text += f"📈 За период: +{new_referrals}\n\n"
    text += f"🏢 Активных партнёров: {active_partners}\n"
    text += f"💰 Выплачено комиссий: {commissions_str} GTON\n\n"
    
    if top_referrers:
        text += "🏆 Топ рефереров:\n"
        for i, (uid, username, name, count) in enumerate(top_referrers, 1):
            display = f"@{username}" if username else name or f"#{uid}"
            text += f"{i}. {display}: {count} рефералов\n"
    
    keyboard = period_keyboard("admin:stats:referrals", period, lang)
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def stats_analytics(query, lang: str, period: str = "week"):
    """Analytics statistics"""
    from core.database.models import Event
    
    start_date, end_date = get_period_dates(period)
    
    async with get_db() as session:
        # Total events
        result = await session.execute(
            select(func.count(Event.id)).where(Event.created_at >= start_date)
        )
        total_events = result.scalar() or 0
        
        # Unique users
        result = await session.execute(
            select(func.count(func.distinct(Event.user_id))).where(
                Event.created_at >= start_date
            )
        )
        unique_users = result.scalar() or 0
        
        # Top events
        result = await session.execute(
            select(
                Event.name,
                func.count(Event.id).label("count")
            ).where(
                Event.created_at >= start_date
            ).group_by(Event.name).order_by(
                func.count(Event.id).desc()
            ).limit(10)
        )
        top_events = result.all()
        
        # Top categories
        result = await session.execute(
            select(
                Event.category,
                func.count(Event.id).label("count")
            ).where(
                Event.created_at >= start_date,
                Event.category.isnot(None)
            ).group_by(Event.category).order_by(
                func.count(Event.id).desc()
            ).limit(5)
        )
        top_categories = result.all()
    
    period_label = get_period_label(lang, period)
    
    text = t(lang, "ADMIN.stats_analytics_title", period=period_label) + "\n\n"
    text += t(lang, "ADMIN.stats_events_total", count=f"{total_events:,}") + "\n"
    text += t(lang, "ADMIN.stats_unique_users", count=f"{unique_users:,}") + "\n\n"
    
    if top_categories:
        text += t(lang, "ADMIN.stats_categories") + "\n"
        for cat, count in top_categories:
            text += f"• {cat or 'other'}: {count:,}\n"
        text += "\n"
    
    if top_events:
        text += t(lang, "ADMIN.stats_popular_events") + "\n"
        for name, count in top_events[:7]:
            short_name = name[:25] + "..." if len(name) > 25 else name
            text += f"• {short_name}: {count:,}\n"
    
    keyboard = period_keyboard("admin:stats:analytics", period, lang)
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
