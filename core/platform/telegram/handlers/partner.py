"""
Partner Handler — Партнёрская программа

Партнёрский баланс хранится в рублях (комиссия от платежей).
Реферальные траты отображаются в GTON.
"""
from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select, func
from loguru import logger

from core.locales import t
from core.database import get_db
from core.platform.telegram.utils import (
    get_or_create_user, 
    get_user_language,
    format_gton,
    build_keyboard
)


async def partner_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle partner callback"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"Partner callback: {query.data}")
    
    try:
        telegram_user = update.effective_user
        user_id = await get_or_create_user(telegram_user.id, telegram_user)
        lang = await get_user_language(user_id)
        
        # Check sub-action
        data = query.data
        parts = data.split(":")
        
        if len(parts) >= 2:
            action = parts[1]
            sub_action = parts[2] if len(parts) > 2 else None
            
            if action == "referrals":
                await partner_referrals(query, user_id, lang)
                return
            elif action == "apply":
                if sub_action == "start":
                    await partner_apply_start(query, user_id, lang)
                else:
                    await partner_apply(query, user_id, lang, context)
                return
            elif action == "stats":
                await partner_stats(query, user_id, lang)
                return
            elif action == "payout":
                if sub_action == "card":
                    await partner_payout_method(query, user_id, lang, "card", context)
                    return
                elif sub_action == "sbp":
                    await partner_payout_method(query, user_id, lang, "sbp", context)
                    return
                elif sub_action == "history":
                    await partner_payout_history(query, user_id, lang)
                    return
                elif sub_action == "confirm":
                    await partner_payout_confirm(query, user_id, lang, context)
                    return
                elif sub_action == "cancel":
                    payout_id = int(parts[3]) if len(parts) > 3 else None
                    await partner_payout_cancel(query, user_id, lang, payout_id)
                    return
                else:
                    await partner_payout(query, user_id, lang)
                    return
            elif action == "cabinet":
                await partner_cabinet(query, user_id, lang, context)
                return
        
        # Check if user is a partner
        from core.database.models import Partner
        async with get_db() as session:
            result = await session.execute(
                select(Partner).where(
                    Partner.user_id == user_id,
                    Partner.status == "active"
                )
            )
            partner = result.scalar_one_or_none()
        
        if partner:
            await partner_cabinet(query, user_id, lang, context)
        else:
            await partner_main(query, user_id, lang, context)
    except Exception as e:
        logger.error(f"Partner callback error: {e}")
        await query.edit_message_text(f"Error: {e}")


async def partner_main(query, user_id: int, lang: str, context):
    """Main partner menu for regular users"""
    from core.database.models import User, Referral
    
    async with get_db() as session:
        # Get user referral code
        result = await session.execute(
            select(User.referral_code).where(User.id == user_id)
        )
        ref_code = result.scalar_one_or_none()
        
        # Count referrals
        result = await session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
        )
        referral_count = result.scalar() or 0
        
        # Total earned (from referral transactions)
        from core.database.models import Transaction
        result = await session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.type == "referral_commission"
            )
        )
        total_earned = result.scalar() or 0
    
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{ref_code}"
    
    text = t(lang, "PARTNER.title") + "\n\n"
    text += t(lang, "PARTNER.description", percent=20) + "\n\n"
    text += t(lang, "PARTNER.stats_title") + "\n"
    text += t(lang, "PARTNER.stats_referrals", count=referral_count) + "\n"
    text += t(lang, "PARTNER.stats_earned", amount=total_earned) + "\n\n"
    text += t(lang, "PARTNER.your_link") + "\n"
    text += f"<code>{ref_link}</code>"
    
    keyboard = [
        [{"text": t(lang, "PARTNER.my_referrals"), "callback_data": "partner:referrals"}],
        [{"text": t(lang, "PARTNER.become_partner"), "callback_data": "partner:apply"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "main_menu"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_cabinet(query, user_id: int, lang: str, context):
    """Partner cabinet for active partners — show in TON with RUB equivalent"""
    from core.database.models import Partner, Referral
    from core.payments.converter import currency_converter
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner).where(Partner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        
        if not partner:
            await partner_main(query, user_id, lang, context)
            return
        
        # Count referrals
        result = await session.execute(
            select(func.count(Referral.id)).where(Referral.partner_id == partner.id)
        )
        referral_count = result.scalar() or 0
    
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=partner_{partner.referral_code}"
    
    # Convert GTON to TON and RUB for partner display
    balance_gton = Decimal(str(partner.balance or 0))
    earned_gton = Decimal(str(partner.total_earned or 0))
    frozen_gton = Decimal(str(partner.frozen_balance or 0))
    available_gton = partner.available_balance
    
    # Get TON and RUB equivalents
    balance_ton = await currency_converter.gton_to_ton(balance_gton)
    earned_ton = await currency_converter.gton_to_ton(earned_gton)
    frozen_ton = await currency_converter.gton_to_ton(frozen_gton)
    available_ton = await currency_converter.gton_to_ton(available_gton)
    
    balance_rub = await currency_converter.convert_from_gton(balance_gton, "RUB")
    earned_rub = await currency_converter.convert_from_gton(earned_gton, "RUB")
    
    # Format: TON (~RUB)
    balance_str = f"{balance_ton:.4f} TON"
    if balance_rub:
        balance_str += f" (~{balance_rub:,.0f} ₽)"
    
    earned_str = f"{earned_ton:.4f} TON"
    if earned_rub:
        earned_str += f" (~{earned_rub:,.0f} ₽)"
    
    text = "╔══════════════════════════╗\n"
    text += "║   🤝 <b>ПАРТНЁРСКИЙ КАБИНЕТ</b>   ║\n"
    text += "╚══════════════════════════╝\n\n"
    
    text += f"💰 <b>Баланс</b>\n"
    text += f"     {balance_str}\n\n"
    
    if frozen_gton > 0:
        text += f"🔒 <b>Заморожено</b>\n"
        text += f"     {frozen_ton:.4f} TON\n"
        text += f"✅ <b>Доступно</b>\n"
        text += f"     {available_ton:.4f} TON\n\n"
    
    text += f"📊 <b>Доход</b>\n"
    text += f"     Всего заработано: {earned_str}\n\n"
    
    text += f"👥 <b>Команда</b>\n"
    text += f"     Рефералов: {referral_count}\n"
    text += f"     Активных: {partner.active_referrals}\n\n"
    
    text += "─────────────────────────────\n"
    text += f"🔗 <b>Ваша ссылка для приглашений:</b>\n"
    text += f"<code>{ref_link}</code>"
    
    keyboard = [
        [{"text": "📋 Мои рефералы", "callback_data": "partner:referrals"}],
        [{"text": "💸 Вывести средства", "callback_data": "partner:payout"}],
        [{"text": "📊 Статистика", "callback_data": "partner:stats"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "main_menu"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_referrals(query, user_id: int, lang: str):
    """Show user's referrals"""
    from core.database.models import Referral, User, Partner
    from core.payments.converter import currency_converter
    
    async with get_db() as session:
        # Check if partner
        result = await session.execute(
            select(Partner).where(Partner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        is_partner = partner is not None
        
        if partner:
            # Partner referrals
            result = await session.execute(
                select(Referral, User).join(
                    User, Referral.referred_id == User.id
                ).where(
                    Referral.partner_id == partner.id
                ).limit(20)
            )
        else:
            # Regular user referrals
            result = await session.execute(
                select(Referral, User).join(
                    User, Referral.referred_id == User.id
                ).where(
                    Referral.referrer_id == user_id
                ).limit(20)
            )
        
        referrals = result.all()
    
    text = "📋 <b>Мои рефералы</b>\n\n"
    
    if not referrals:
        text += "У вас пока нет рефералов.\n\n"
        text += "Поделитесь своей ссылкой с друзьями!"
    else:
        text += f"Всего: {len(referrals)}\n\n"
        for ref, user in referrals:
            status = "✅" if ref.is_active else "❌"
            name = user.first_name or f"User #{user.id}"
            spent_gton = Decimal(str(ref.total_payments or 0))
            
            if is_partner:
                # Partner sees TON with RUB
                spent_ton = await currency_converter.gton_to_ton(spent_gton)
                spent_rub = await currency_converter.convert_from_gton(spent_gton, "RUB")
                spent_str = f"{spent_ton:.4f} TON"
                if spent_rub:
                    spent_str += f" (~{spent_rub:,.0f} ₽)"
            else:
                # Regular user sees GTON
                spent_str = f"{format_gton(spent_gton)} GTON"
            
            text += f"{status} {name}\n"
            text += f"   💰 {spent_str}\n"
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": "partner"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def notify_admins_new_application(bot, user, partner_id: int, audience: str = None, socials: str = None):
    """Notify admins about new partner application"""
    from core.database.models import User
    from core.config import config
    from loguru import logger
    
    try:
        async with get_db() as session:
            # Get all admins from DB
            result = await session.execute(
                select(User).where(User.role == "admin")
            )
            db_admins = result.scalars().all()
            
            # Also get admins from config.ADMIN_IDS
            admin_telegram_ids = set(a.telegram_id for a in db_admins)
            for admin_id in config.ADMIN_IDS:
                if admin_id not in admin_telegram_ids:
                    result = await session.execute(
                        select(User).where(User.telegram_id == admin_id)
                    )
                    extra_admin = result.scalar_one_or_none()
                    if extra_admin:
                        db_admins.append(extra_admin)
                        admin_telegram_ids.add(admin_id)
            
            admins = db_admins
            logger.info(f"Found {len(admins)} admins to notify about partner application")
            
            # Build detailed user info
            text = f"📝 <b>Новая заявка на партнёрство</b>\n\n"
            
            # User info section
            text += f"<b>👤 Информация о пользователе:</b>\n"
            text += f"├ Имя: {user.full_name}\n"
            if user.telegram_username:
                text += f"├ Username: @{user.telegram_username}\n"
            text += f"├ Telegram ID: <code>{user.telegram_id}</code>\n"
            text += f"├ ID в системе: {user.id}\n"
            text += f"├ Язык: {user.language}\n"
            
            # Registration date
            if user.created_at:
                reg_date = user.created_at.strftime("%d.%m.%Y %H:%M")
                text += f"├ Регистрация: {reg_date}\n"
            
            # Last activity
            if user.last_activity_at:
                last_active = user.last_activity_at.strftime("%d.%m.%Y %H:%M")
                text += f"├ Последняя активность: {last_active}\n"
            
            # Referrer info
            if user.referrer_id:
                result = await session.execute(
                    select(User).where(User.id == user.referrer_id)
                )
                referrer = result.scalar_one_or_none()
                if referrer:
                    ref_name = f"@{referrer.telegram_username}" if referrer.telegram_username else referrer.first_name
                    text += f"├ Приглашён: {ref_name}\n"
            
            # Wallet balance
            from core.database.models import Wallet
            result = await session.execute(
                select(Wallet).where(
                    Wallet.user_id == user.id,
                    Wallet.wallet_type == "main"
                )
            )
            wallet = result.scalar_one_or_none()
            if wallet:
                text += f"└ Баланс: {wallet.balance:.2f} GTON\n"
            
            # Application data
            text += f"\n<b>📋 Данные заявки:</b>\n"
            if audience:
                text += f"├ Аудитория: {audience}\n"
            if socials:
                # Truncate if too long
                socials_preview = socials[:300] + "..." if len(socials) > 300 else socials
                text += f"└ Соцсети:\n{socials_preview}\n"
            
            text += f"\n🔗 <a href='tg://user?id={user.telegram_id}'>Открыть профиль</a>"
            text += f"\n\n📌 Рассмотреть: /admin → Партнёры → Заявки"
            
            for admin in admins:
                try:
                    await bot.send_message(
                        chat_id=admin.telegram_id,
                        text=text,
                        parse_mode="HTML"
                    )
                    logger.info(f"Partner application notification sent to admin {admin.telegram_id}")
                except Exception as e:
                    logger.error(f"Failed to send notification to admin {admin.telegram_id}: {e}")
    except Exception as e:
        logger.error(f"Error in notify_admins_new_application: {e}")


async def partner_apply(query, user_id: int, lang: str, context):
    """Partner application - start questionnaire"""
    from core.database.models import Partner, User, UserService
    
    # Check if already applied
    async with get_db() as session:
        result = await session.execute(
            select(Partner).where(Partner.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            if existing.status == "pending":
                text = "📝 <b>Заявка на рассмотрении</b>\n\n"
                text += "Ваша заявка уже отправлена и находится на рассмотрении.\n"
                text += "Мы уведомим вас о решении."
            elif existing.status == "active":
                text = "✅ Вы уже являетесь партнёром!"
            else:
                text = "❌ Ваша заявка была отклонена.\n\n"
                text += "Вы можете подать заявку повторно."
                # Allow re-application
                keyboard = [
                    [{"text": "📝 Подать заявку заново", "callback_data": "partner:apply:start"}],
                    [{"text": t(lang, "COMMON.back"), "callback_data": "partner"}]
                ]
                await query.edit_message_text(
                    text,
                    reply_markup=build_keyboard(keyboard),
                    parse_mode="HTML"
                )
                return
            
            keyboard = [
                [{"text": t(lang, "COMMON.back"), "callback_data": "partner"}]
            ]
            await query.edit_message_text(
                text,
                reply_markup=build_keyboard(keyboard),
                parse_mode="HTML"
            )
            return
    
    # Show questionnaire intro
    text = "🤝 <b>Стать партнёром</b>\n\n"
    text += "Партнёрская программа позволяет зарабатывать до 30% с покупок ваших рефералов!\n\n"
    text += "<b>Преимущества:</b>\n"
    text += "• Повышенный процент комиссии\n"
    text += "• Вывод средств на карту/СБП\n"
    text += "• Персональная поддержка\n"
    text += "• Промо-материалы\n\n"
    text += "Для подачи заявки ответьте на несколько вопросов."
    
    keyboard = [
        [{"text": "📝 Начать анкету", "callback_data": "partner:apply:start"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "partner"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_apply_start(query, user_id: int, lang: str):
    """Start partner questionnaire - Step 1: Audience size"""
    from core.database.models import UserService
    
    # Set state for questionnaire
    async with get_db() as session:
        result = await session.execute(
            select(UserService).where(
                UserService.user_id == user_id,
                UserService.service_id == "core"
            )
        )
        user_service = result.scalar_one_or_none()
        
        if not user_service:
            user_service = UserService(user_id=user_id, service_id="core")
            session.add(user_service)
        
        user_service.state = "partner_apply_audience"
        user_service.state_data = {}
    
    text = "📊 <b>Шаг 1 из 2</b>\n\n"
    text += "Какой общий размер вашей аудитории?\n\n"
    text += "Укажите примерное количество подписчиков/читателей во всех ваших соцсетях и каналах.\n\n"
    text += "<i>Например: 5000 или 50к</i>"
    
    keyboard = [
        [{"text": "❌ Отмена", "callback_data": "partner"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_apply_socials(query_or_update, user_id: int, lang: str, audience: str):
    """Step 2: Social links"""
    from core.database.models import UserService
    
    # Save audience and move to next step
    async with get_db() as session:
        result = await session.execute(
            select(UserService).where(
                UserService.user_id == user_id,
                UserService.service_id == "core"
            )
        )
        user_service = result.scalar_one_or_none()
        
        if user_service:
            state_data = user_service.state_data or {}
            state_data["audience"] = audience
            user_service.state_data = state_data
            user_service.state = "partner_apply_socials"
    
    text = "🔗 <b>Шаг 2 из 2</b>\n\n"
    text += "Укажите ссылки на ваши соцсети/каналы:\n\n"
    text += "Отправьте ссылки на ваши площадки (Telegram, Instagram, YouTube, TikTok и т.д.)\n\n"
    text += "<i>Можно несколько ссылок, каждую с новой строки</i>"
    
    keyboard = [
        [{"text": "❌ Отмена", "callback_data": "partner"}]
    ]
    
    # Check if it's a callback query or message
    if hasattr(query_or_update, 'edit_message_text'):
        await query_or_update.edit_message_text(
            text,
            reply_markup=build_keyboard(keyboard),
            parse_mode="HTML"
        )
    else:
        await query_or_update.message.reply_text(
            text,
            reply_markup=build_keyboard(keyboard),
            parse_mode="HTML"
        )


async def partner_apply_submit(update, user_id: int, lang: str, socials: str, context):
    """Submit partner application"""
    from core.database.models import Partner, User, UserService
    from datetime import datetime
    import secrets
    
    # Get questionnaire data
    async with get_db() as session:
        result = await session.execute(
            select(UserService).where(
                UserService.user_id == user_id,
                UserService.service_id == "core"
            )
        )
        user_service = result.scalar_one_or_none()
        
        state_data = user_service.state_data if user_service else {}
        audience = state_data.get("audience", "Не указано")
        
        # Clear state
        if user_service:
            user_service.state = None
            user_service.state_data = None
        
        # Get user info
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        # Check if partner exists (rejected - allow re-apply)
        result = await session.execute(
            select(Partner).where(Partner.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        
        # Format application text
        application_text = f"👥 Аудитория: {audience}\n\n🔗 Соцсети:\n{socials}"
        
        if existing:
            # Update existing rejected application
            existing.status = "pending"
            existing.application_text = application_text
            existing.applied_at = datetime.utcnow()
            existing.rejection_reason = None
            partner_id = existing.id
        else:
            # Create new application
            partner = Partner(
                user_id=user_id,
                referral_code=secrets.token_urlsafe(6).upper(),
                status="pending",
                application_text=application_text,
                applied_at=datetime.utcnow()
            )
            session.add(partner)
            await session.flush()
            partner_id = partner.id
    
    text = "✅ <b>Заявка отправлена!</b>\n\n"
    text += "Ваша заявка на партнёрство отправлена на рассмотрение.\n\n"
    text += f"<b>Ваши данные:</b>\n"
    text += f"👥 Аудитория: {audience}\n"
    text += f"🔗 Соцсети: указаны\n\n"
    text += "Мы уведомим вас о решении в ближайшее время! 🎉"
    
    keyboard = [
        [{"text": "🔙 В партнёрскую программу", "callback_data": "partner"}]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
    
    # Notify admins
    if user:
        await notify_admins_new_application(context.bot, user, partner_id, audience, socials)


async def partner_stats(query, user_id: int, lang: str):
    """Partner statistics — show in TON with RUB equivalent"""
    from core.database.models import Partner, Referral, Commission
    from core.payments.converter import currency_converter
    from datetime import datetime, timedelta
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner).where(Partner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        
        if not partner:
            await query.answer("Вы не являетесь партнёром", show_alert=True)
            return
        
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Referrals this week
        result = await session.execute(
            select(func.count(Referral.id)).where(
                Referral.partner_id == partner.id,
                Referral.created_at >= week_ago
            )
        )
        week_referrals = result.scalar() or 0
        
        # Earnings this month (from Commission model)
        result = await session.execute(
            select(func.sum(Commission.commission_amount)).where(
                Commission.referrer_id == user_id,
                Commission.created_at >= month_ago
            )
        )
        month_earnings = Decimal(str(result.scalar() or 0))
    
    # Convert GTON to TON and RUB for partner display
    balance_gton = Decimal(str(partner.balance or 0))
    earned_gton = Decimal(str(partner.total_earned or 0))
    withdrawn_gton = Decimal(str(partner.total_withdrawn or 0))
    
    # Get TON and RUB equivalents
    balance_ton = await currency_converter.gton_to_ton(balance_gton)
    earned_ton = await currency_converter.gton_to_ton(earned_gton)
    withdrawn_ton = await currency_converter.gton_to_ton(withdrawn_gton)
    month_ton = await currency_converter.gton_to_ton(month_earnings)
    
    balance_rub = await currency_converter.convert_from_gton(balance_gton, "RUB")
    earned_rub = await currency_converter.convert_from_gton(earned_gton, "RUB")
    month_rub = await currency_converter.convert_from_gton(month_earnings, "RUB")
    
    # Format: TON (~RUB)
    balance_str = f"{balance_ton:.4f} TON"
    if balance_rub:
        balance_str += f" (~{balance_rub:,.0f} ₽)"
    
    earned_str = f"{earned_ton:.4f} TON"
    if earned_rub:
        earned_str += f" (~{earned_rub:,.0f} ₽)"
    
    month_str = f"{month_ton:.4f} TON"
    if month_rub:
        month_str += f" (~{month_rub:,.0f} ₽)"
    
    text = "📊 <b>Статистика</b>\n\n"
    text += f"💰 Баланс: {balance_str}\n"
    text += f"📈 Всего заработано: {earned_str}\n"
    text += f"💸 Выведено: {withdrawn_ton:.4f} TON\n\n"
    text += f"👥 Рефералов за неделю: +{week_referrals}\n"
    text += f"💵 Заработок за месяц: {month_str}\n\n"
    text += f"📊 Комиссия: {partner.level1_percent}%"
    
    keyboard = [
        [{"text": "🔄 Обновить", "callback_data": "partner:stats"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "partner:cabinet"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_payout(query, user_id: int, lang: str):
    """Partner payout request — GTON withdrawal"""
    from core.database.models import Partner
    from core.payout import payout_service
    from core.payments.converter import currency_converter
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner).where(Partner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        
        if not partner:
            await query.answer("Вы не являетесь партнёром", show_alert=True)
            return
    
    # Get min payout in GTON
    min_payout = await payout_service.get_min_payout_gton()
    available = partner.available_balance
    
    # Get fiat equivalent
    available_fiat = await currency_converter.convert_from_gton(available, "RUB")
    min_fiat = await currency_converter.convert_from_gton(min_payout, "RUB")
    
    available_str = f"{format_gton(available)} GTON"
    if available_fiat:
        available_str += f" (~{available_fiat:,.0f} ₽)"
    
    min_str = f"{format_gton(min_payout)} GTON"
    if min_fiat:
        min_str += f" (~{min_fiat:,.0f} ₽)"
    
    text = "💸 <b>Вывод средств</b>\n\n"
    text += f"💰 Доступно: {available_str}\n"
    text += f"📊 Минимум: {min_str}\n\n"
    
    if available >= min_payout:
        text += "Выберите способ вывода:"
        keyboard = [
            [{"text": "💳 Банковская карта", "callback_data": "partner:payout:card"}],
            [{"text": "📱 СБП", "callback_data": "partner:payout:sbp"}],
            [{"text": "📜 История выводов", "callback_data": "partner:payout:history"}],
            [{"text": t(lang, "COMMON.back"), "callback_data": "partner:cabinet"}]
        ]
    else:
        need_more = min_payout - available
        need_fiat = await currency_converter.convert_from_gton(need_more, "RUB")
        need_str = f"{format_gton(need_more)} GTON"
        if need_fiat:
            need_str += f" (~{need_fiat:,.0f} ₽)"
        
        text += f"❌ Недостаточно средств.\n"
        text += f"Нужно ещё: {need_str}"
        keyboard = [
            [{"text": "📜 История выводов", "callback_data": "partner:payout:history"}],
            [{"text": t(lang, "COMMON.back"), "callback_data": "partner:cabinet"}]
        ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_payout_method(query, user_id: int, lang: str, method: str, context):
    """Select payout method and enter details"""
    from core.database.models import Partner, UserService
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner).where(Partner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        
        if not partner or partner.status != "active":
            await query.answer("Вы не являетесь партнёром", show_alert=True)
            return
        
        # Set state for input
        result = await session.execute(
            select(UserService).where(
                UserService.user_id == user_id,
                UserService.service_id == "core"
            )
        )
        user_service = result.scalar_one_or_none()
        
        if not user_service:
            user_service = UserService(user_id=user_id, service_id="core")
            session.add(user_service)
        
        user_service.state = f"partner_payout_{method}"
        user_service.state_data = {"method": method}
    
    if method == "card":
        text = "💳 <b>Вывод на карту</b>\n\n"
        text += "Введите номер карты (16 цифр):\n\n"
        text += "<i>Пример: 4276 1234 5678 9012</i>"
    else:  # sbp
        text = "📱 <b>Вывод по СБП</b>\n\n"
        text += "Введите номер телефона:\n\n"
        text += "<i>Пример: +7 900 123 45 67</i>"
    
    keyboard = [
        [{"text": t(lang, "COMMON.cancel"), "callback_data": "partner:payout"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_payout_history(query, user_id: int, lang: str):
    """Show payout history"""
    from core.database.models import Partner
    from core.payout import payout_service
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner).where(Partner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        
        if not partner:
            await query.answer("Вы не являетесь партнёром", show_alert=True)
            return
    
    payouts = await payout_service.get_partner_payouts(partner.id, limit=10)
    
    text = "📜 <b>История выводов</b>\n\n"
    
    if not payouts:
        text += "У вас пока нет заявок на вывод."
    else:
        status_icons = {
            "pending": "⏳",
            "processing": "🔄",
            "completed": "✅",
            "rejected": "❌",
            "cancelled": "🚫"
        }
        
        for p in payouts:
            icon = status_icons.get(p.status, "❓")
            amount_str = format_gton(Decimal(str(p.amount_gton)))
            date_str = p.created_at.strftime("%d.%m.%Y")
            text += f"{icon} {amount_str} GTON → {p.amount_fiat:,.0f} ₽\n"
            text += f"   {p.method.upper()} | {date_str}\n"
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": "partner:payout"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_payout_confirm(query, user_id: int, lang: str, context):
    """Confirm and create payout request"""
    from core.database.models import Partner, UserService
    from core.payout import payout_service
    from core.payments.converter import currency_converter
    
    async with get_db() as session:
        result = await session.execute(
            select(Partner).where(Partner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        
        if not partner:
            await query.answer("Вы не являетесь партнёром", show_alert=True)
            return
        
        # Get state data
        result = await session.execute(
            select(UserService).where(
                UserService.user_id == user_id,
                UserService.service_id == "core"
            )
        )
        user_service = result.scalar_one_or_none()
        
        if not user_service or not user_service.state_data:
            await query.answer("Ошибка. Попробуйте снова.", show_alert=True)
            return
        
        state_data = user_service.state_data
        method = state_data.get("method")
        details = state_data.get("details", {})
        
        # Clear state
        user_service.state = None
        user_service.state_data = None
    
    # Create payout for full available balance
    available = partner.available_balance
    
    result = await payout_service.create_payout_request(
        partner_id=partner.id,
        amount_gton=available,
        method=method,
        details=details
    )
    
    if result.success:
        fiat_str = f"{result.amount_fiat:,.0f} ₽" if result.amount_fiat else ""
        text = "✅ <b>Заявка создана!</b>\n\n"
        text += f"💰 Сумма: {format_gton(result.amount_gton)} GTON\n"
        text += f"💵 К выплате: {fiat_str}\n"
        text += f"📋 Метод: {method.upper()}\n\n"
        text += "Заявка будет обработана в течение 24 часов."
        
        # Notify admins
        await notify_admins_new_payout(context.bot, partner, result)
    else:
        text = f"❌ <b>Ошибка</b>\n\n{result.error}"
    
    keyboard = [
        [{"text": "🔙 В кабинет", "callback_data": "partner:cabinet"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def partner_payout_cancel(query, user_id: int, lang: str, payout_id: int):
    """Cancel pending payout"""
    from core.payout import payout_service
    
    if not payout_id:
        await query.answer("Заявка не найдена", show_alert=True)
        return
    
    result = await payout_service.cancel_payout(payout_id, user_id)
    
    if result.success:
        await query.answer("✅ Заявка отменена", show_alert=True)
    else:
        await query.answer(f"❌ {result.error}", show_alert=True)
    
    # Refresh history
    await partner_payout_history(query, user_id, lang)


async def notify_admins_new_payout(bot, partner, payout_result):
    """Notify admins about new payout request"""
    from core.database.models import User
    
    async with get_db() as session:
        # Get partner user
        result = await session.execute(
            select(User).where(User.id == partner.user_id)
        )
        user = result.scalar_one_or_none()
        
        # Get all admins
        result = await session.execute(
            select(User).where(User.role == "admin")
        )
        admins = result.scalars().all()
        
        username = f"@{user.telegram_username}" if user and user.telegram_username else f"#{partner.user_id}"
        
        text = f"💸 <b>Новая заявка на вывод</b>\n\n"
        text += f"👤 Партнёр: {username}\n"
        text += f"💰 Сумма: {format_gton(payout_result.amount_gton)} GTON\n"
        text += f"💵 К выплате: {payout_result.amount_fiat:,.0f} ₽\n\n"
        text += f"Рассмотреть: /admin → Партнёры → Выводы"
        
        for admin in admins:
            try:
                await bot.send_message(
                    chat_id=admin.telegram_id,
                    text=text,
                    parse_mode="HTML"
                )
            except Exception:
                pass


async def handle_payout_input(update, user_id: int, lang: str, method: str, state_data: dict):
    """Handle payout details input (card number or phone)"""
    from core.database.models import UserService, Partner
    from core.payout import payout_service
    from core.payments.converter import currency_converter
    
    input_text = update.message.text.strip()
    
    # Validate input
    if method == "card":
        # Remove spaces and validate card number
        card = input_text.replace(" ", "").replace("-", "")
        if not card.isdigit() or len(card) != 16:
            await update.message.reply_text(
                "❌ Неверный номер карты. Введите 16 цифр.",
                parse_mode="HTML"
            )
            return
        details = {"card": card, "display": f"{card[:4]} **** **** {card[-4:]}"}
    else:  # sbp
        # Clean phone number
        phone = input_text.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not phone.startswith("+"):
            phone = "+" + phone
        if len(phone) < 11:
            await update.message.reply_text(
                "❌ Неверный номер телефона.",
                parse_mode="HTML"
            )
            return
        details = {"phone": phone}
    
    # Get partner and available balance
    async with get_db() as session:
        result = await session.execute(
            select(Partner).where(Partner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        
        if not partner:
            await update.message.reply_text("❌ Вы не являетесь партнёром")
            return
        
        # Update state with details
        result = await session.execute(
            select(UserService).where(
                UserService.user_id == user_id,
                UserService.service_id == "core"
            )
        )
        user_service = result.scalar_one_or_none()
        
        if user_service:
            user_service.state_data = {"method": method, "details": details}
    
    # Show confirmation
    available = partner.available_balance
    fiat = await currency_converter.convert_from_gton(available, "RUB")
    
    available_str = f"{format_gton(available)} GTON"
    if fiat:
        available_str += f" (~{fiat:,.0f} ₽)"
    
    if method == "card":
        details_str = details.get("display", "****")
    else:
        details_str = details.get("phone", "")
    
    text = "📋 <b>Подтвердите вывод</b>\n\n"
    text += f"💰 Сумма: {available_str}\n"
    text += f"📱 Метод: {method.upper()}\n"
    text += f"📝 Реквизиты: {details_str}\n\n"
    text += "Подтвердить вывод?"
    
    keyboard = [
        [{"text": "✅ Подтвердить", "callback_data": "partner:payout:confirm"}],
        [{"text": "❌ Отмена", "callback_data": "partner:payout"}]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
