"""
Admin Users Management — Управление пользователями

Балансы отображаются в GTON + RUB эквивалент.
"""
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import select, desc, func, or_

from core.locales import t
from core.database import get_db
from core.platform.telegram.utils import build_keyboard, format_gton
from core.payments.converter import currency_converter


# Filter definitions
FILTERS = ["all", "active", "today", "with_balance", "blocked"]
USERS_PER_PAGE = 15


async def notify_user(bot, user_telegram_id: int, text: str):
    """Send notification to user"""
    try:
        await bot.send_message(
            chat_id=user_telegram_id,
            text=text,
            parse_mode="HTML"
        )
        return True
    except Exception:
        return False


async def admin_users(query, lang: str, action: str = None, params: str = None):
    """Admin users handler"""
    if action == "view" and params:
        await view_user(query, lang, int(params))
    elif action == "search":
        await search_users_menu(query, lang)
    elif action == "filter" and params:
        # params format: filter_type or filter_type_page
        parts = params.split("_") if "_" in params and params.split("_")[-1].isdigit() else [params]
        filter_type = "_".join(parts[:-1]) if len(parts) > 1 and parts[-1].isdigit() else params
        page = int(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 0
        await users_list(query, lang, filter_type, page)
    elif action == "page" and params:
        # params format: filter_page
        parts = params.rsplit("_", 1)
        filter_type = parts[0] if len(parts) > 1 else "all"
        page = int(parts[1]) if len(parts) > 1 else 0
        await users_list(query, lang, filter_type, page)
    elif action == "balance" and params:
        await user_balance_menu(query, lang, int(params))
    elif action == "balance_add" and params:
        await user_balance_action(query, lang, int(params), "add")
    elif action == "balance_sub" and params:
        await user_balance_action(query, lang, int(params), "subtract")
    elif action == "transactions" and params:
        await user_transactions(query, lang, int(params))
    elif action == "message" and params:
        await user_message_menu(query, lang, int(params))
    else:
        await users_list(query, lang)


async def users_list(query, lang: str, filter_type: str = "all", page: int = 0):
    """Show users list with filters and pagination"""
    from core.database.models import User, Wallet
    
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    
    async with get_db() as session:
        # Base query
        base_query = select(User)
        count_query = select(func.count(User.id))
        
        # Apply filter
        if filter_type == "active":
            base_query = base_query.where(User.last_activity_at >= week_ago)
            count_query = count_query.where(User.last_activity_at >= week_ago)
        elif filter_type == "today":
            base_query = base_query.where(User.created_at >= today)
            count_query = count_query.where(User.created_at >= today)
        elif filter_type == "with_balance":
            base_query = base_query.join(Wallet).where(Wallet.balance > 0)
            count_query = select(func.count(func.distinct(User.id))).select_from(User).join(Wallet).where(Wallet.balance > 0)
        elif filter_type == "blocked":
            base_query = base_query.where(User.is_blocked == True)
            count_query = count_query.where(User.is_blocked == True)
        
        # Get filtered count for pagination
        result = await session.execute(count_query)
        filtered_count = result.scalar() or 0
        
        # Calculate pages
        total_pages = max(1, (filtered_count + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
        page = max(0, min(page, total_pages - 1))
        offset = page * USERS_PER_PAGE
        
        # Get users for current page
        result = await session.execute(
            base_query.order_by(desc(User.created_at)).offset(offset).limit(USERS_PER_PAGE)
        )
        users = result.scalars().all()
        
        # Global stats
        result = await session.execute(select(func.count(User.id)))
        total_users = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(User.id)).where(User.last_activity_at >= week_ago)
        )
        active_users = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(User.id)).where(User.created_at >= today)
        )
        new_users = result.scalar() or 0
    
    text = t(lang, "ADMIN.users_title") + "\n\n"
    text += t(lang, "ADMIN.users_total", count=f"{total_users:,}") + " | "
    text += t(lang, "ADMIN.users_active", count=active_users) + " | "
    text += t(lang, "ADMIN.users_new", count=new_users) + "\n\n"
    
    # Show page info
    if total_pages > 1:
        text += t(lang, "ADMIN.page_info", current=page + 1, total=total_pages) + "\n\n"
    
    for user in users:
        status = "🚫" if user.is_blocked else "✅"
        name = user.display_name
        username = f"@{user.telegram_username}" if user.telegram_username else "-"
        text += f"{status} <code>{user.id}</code> | {username} | {name} | <code>{user.telegram_id}</code>\n"
    
    if not users:
        text += t(lang, "ADMIN.users_search_not_found") + "\n"
    
    # Filter buttons
    filter_buttons = []
    for f in FILTERS:
        label = t(lang, f"ADMIN.filter_{f}")
        if f == filter_type:
            label = f"• {label} •"
        filter_buttons.append({"text": label, "callback_data": f"admin:users:filter:{f}"})
    
    keyboard = [
        filter_buttons[:3],
        filter_buttons[3:],
    ]
    
    # Pagination buttons
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append({"text": t(lang, "ADMIN.page_prev"), "callback_data": f"admin:users:page:{filter_type}_{page - 1}"})
        if page < total_pages - 1:
            pagination.append({"text": t(lang, "ADMIN.page_next"), "callback_data": f"admin:users:page:{filter_type}_{page + 1}"})
        if pagination:
            keyboard.append(pagination)
    
    keyboard.append([{"text": t(lang, "ADMIN.users_search"), "callback_data": "admin:users:search"}])
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def view_user(query, lang: str, user_id: int):
    """View user details"""
    from core.database.models import User, Wallet, Transaction, Referral
    
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await query.answer(t(lang, "ADMIN.users_search_not_found"), show_alert=True)
            return
        
        # Main balance (GTON)
        result = await session.execute(
            select(Wallet.balance).where(
                Wallet.user_id == user_id,
                Wallet.wallet_type == "main"
            )
        )
        main_balance = Decimal(str(result.scalar() or 0))
        
        # Bonus balance (GTON)
        result = await session.execute(
            select(Wallet.balance).where(
                Wallet.user_id == user_id,
                Wallet.wallet_type == "bonus"
            )
        )
        bonus_balance = Decimal(str(result.scalar() or 0))
        
        # Total spent (GTON)
        result = await session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.type == "debit"
            )
        )
        total_spent = Decimal(str(result.scalar() or 0))
        
        # Transactions count
        result = await session.execute(
            select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        )
        tx_count = result.scalar() or 0
        
        # Deposits
        result = await session.execute(
            select(
                func.count(Transaction.id),
                func.sum(Transaction.amount)
            ).where(
                Transaction.user_id == user_id,
                Transaction.type == "deposit",
                Transaction.status == "completed"
            )
        )
        deposit_row = result.one()
        deposit_count = deposit_row[0] or 0
        deposit_sum = Decimal(str(deposit_row[1] or 0))
        
        # Referrer
        referrer = None
        if user.referrer_id:
            result = await session.execute(
                select(User).where(User.id == user.referrer_id)
            )
            referrer = result.scalar_one_or_none()
        
        # Referrals count
        result = await session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
        )
        referrals_count = result.scalar() or 0
    
    # Get fiat equivalents
    main_fiat = await currency_converter.convert_from_gton(main_balance, "RUB")
    bonus_fiat = await currency_converter.convert_from_gton(bonus_balance, "RUB")
    spent_fiat = await currency_converter.convert_from_gton(total_spent, "RUB")
    deposit_fiat = await currency_converter.convert_from_gton(deposit_sum, "RUB")
    
    # Format for display
    main_str = f"{format_gton(main_balance)} GTON"
    if main_fiat:
        main_str += f" (~{main_fiat:,.0f} ₽)"
    
    bonus_str = f"{format_gton(bonus_balance)} GTON"
    if bonus_fiat:
        bonus_str += f" (~{bonus_fiat:,.0f} ₽)"
    
    spent_str = f"{format_gton(total_spent)} GTON"
    deposit_str = f"{format_gton(deposit_sum)} GTON"
    
    # Build text
    text = t(lang, "ADMIN.user_card_title", id=user.id) + "\n\n"
    
    # Telegram info
    if user.telegram_username:
        text += t(lang, "ADMIN.user_telegram", username=user.telegram_username) + "\n"
    else:
        text += t(lang, "ADMIN.user_telegram_no") + "\n"
    
    text += t(lang, "ADMIN.user_name", name=user.display_name) + "\n"
    text += t(lang, "ADMIN.user_language", language=user.language.upper()) + "\n"
    text += t(lang, "ADMIN.user_registered", date=user.created_at.strftime("%d.%m.%Y")) + "\n"
    
    # Last activity
    if user.last_activity_at:
        now = datetime.utcnow()
        diff = now - user.last_activity_at
        if diff.total_seconds() < 60:
            activity_text = t(lang, "ADMIN.time_just_now")
        elif diff.total_seconds() < 3600:
            activity_text = t(lang, "ADMIN.time_min_ago", min=int(diff.total_seconds() // 60))
        elif diff.total_seconds() < 86400:
            activity_text = t(lang, "ADMIN.time_hours_ago", hours=int(diff.total_seconds() // 3600))
        else:
            activity_text = user.last_activity_at.strftime("%d.%m.%Y")
        text += t(lang, "ADMIN.user_last_activity", time=activity_text) + "\n"
    
    # Status
    if user.is_blocked:
        text += t(lang, "ADMIN.user_status_blocked") + "\n"
    else:
        text += t(lang, "ADMIN.user_status_active") + "\n"
    
    text += "\n"
    
    # Balance (GTON)
    text += t(lang, "ADMIN.user_balance_title") + "\n"
    text += f"├── 💰 Основной: {main_str}\n"
    text += f"└── 🎁 Бонусный: {bonus_str}\n\n"
    
    # Stats
    text += t(lang, "ADMIN.user_stats_title") + "\n"
    text += f"├── 📉 Потрачено: {spent_str}\n"
    text += f"├── 📊 Транзакций: {tx_count}\n"
    text += f"└── 💳 Пополнений: {deposit_count} ({deposit_str})\n\n"
    
    # Referral
    if referrer:
        text += t(lang, "ADMIN.user_referrer", name=referrer.display_name, id=referrer.id) + "\n"
    else:
        text += t(lang, "ADMIN.user_referrer_none") + "\n"
    text += t(lang, "ADMIN.user_referrals_count", count=referrals_count) + "\n"
    
    # Keyboard
    keyboard = [
        [
            {"text": t(lang, "ADMIN.user_action_balance"), "callback_data": f"admin:users:balance:{user_id}"},
            {"text": t(lang, "ADMIN.user_action_message"), "callback_data": f"admin:users:message:{user_id}"}
        ],
        [{"text": t(lang, "ADMIN.user_action_moderation"), "callback_data": f"admin:moderation:user:{user_id}"}],
        [{"text": t(lang, "ADMIN.user_action_transactions"), "callback_data": f"admin:users:transactions:{user_id}"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:users"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def search_users_menu(query, lang: str):
    """Search users prompt"""
    from core.database.models import UserService
    
    # Set state for search
    admin_telegram_id = query.from_user.id
    async with get_db() as session:
        from core.database.models import User
        result = await session.execute(
            select(User.id).where(User.telegram_id == admin_telegram_id)
        )
        admin_id = result.scalar()
        
        if admin_id:
            result = await session.execute(
                select(UserService).where(
                    UserService.user_id == admin_id,
                    UserService.service_id == "core"
                )
            )
            user_service = result.scalar_one_or_none()
            
            if not user_service:
                user_service = UserService(user_id=admin_id, service_id="core")
                session.add(user_service)
            
            user_service.state = "admin_user_search"
            user_service.state_data = {}
    
    text = t(lang, "ADMIN.users_search_title") + "\n\n"
    text += t(lang, "ADMIN.users_search_prompt")
    
    keyboard = [
        [{"text": t(lang, "COMMON.cancel"), "callback_data": "admin:users"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_user_search(update, user_id: int, lang: str):
    """Handle user search input"""
    from core.database.models import User, UserService
    
    search_query = update.message.text.strip()
    
    # Clear state
    async with get_db() as session:
        result = await session.execute(
            select(UserService).where(
                UserService.user_id == user_id,
                UserService.service_id == "core"
            )
        )
        user_service = result.scalar_one_or_none()
        if user_service:
            user_service.state = None
            user_service.state_data = None
    
    # Search user
    async with get_db() as session:
        found_user = None
        
        # Try by ID
        if search_query.isdigit():
            result = await session.execute(
                select(User).where(User.id == int(search_query))
            )
            found_user = result.scalar_one_or_none()
            
            # Try by telegram_id
            if not found_user:
                result = await session.execute(
                    select(User).where(User.telegram_id == int(search_query))
                )
                found_user = result.scalar_one_or_none()
        
        # Try by username
        if not found_user:
            username = search_query.lstrip("@")
            result = await session.execute(
                select(User).where(User.telegram_username.ilike(username))
            )
            found_user = result.scalar_one_or_none()
        
        # Try by name
        if not found_user:
            result = await session.execute(
                select(User).where(
                    or_(
                        User.first_name.ilike(f"%{search_query}%"),
                        User.last_name.ilike(f"%{search_query}%")
                    )
                ).limit(1)
            )
            found_user = result.scalar_one_or_none()
    
    if found_user:
        text = t(lang, "ADMIN.users_search_results") + "\n\n"
        status = "🚫" if found_user.is_blocked else "✅"
        username = f"@{found_user.telegram_username}" if found_user.telegram_username else "-"
        text += f"{status} <code>{found_user.id}</code> | {username} | {found_user.display_name}\n"
        
        keyboard = [
            [{"text": f"👤 #{found_user.id} {found_user.display_name}", "callback_data": f"admin:users:view:{found_user.id}"}],
            [{"text": t(lang, "ADMIN.users_search"), "callback_data": "admin:users:search"}],
            [{"text": t(lang, "COMMON.back"), "callback_data": "admin:users"}]
        ]
    else:
        text = t(lang, "ADMIN.users_search_not_found")
        keyboard = [
            [{"text": t(lang, "ADMIN.users_search"), "callback_data": "admin:users:search"}],
            [{"text": t(lang, "COMMON.back"), "callback_data": "admin:users"}]
        ]
    
    await update.message.reply_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def user_balance_menu(query, lang: str, user_id: int):
    """Balance change menu — GTON"""
    from core.database.models import User, Wallet
    
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await query.answer(t(lang, "ADMIN.users_search_not_found"), show_alert=True)
            return
        
        result = await session.execute(
            select(Wallet.balance).where(
                Wallet.user_id == user_id,
                Wallet.wallet_type == "main"
            )
        )
        balance = Decimal(str(result.scalar() or 0))
    
    # Get fiat equivalent
    fiat = await currency_converter.convert_from_gton(balance, "RUB")
    balance_str = f"{format_gton(balance)} GTON"
    if fiat:
        balance_str += f" (~{fiat:,.0f} ₽)"
    
    text = "💰 <b>Изменение баланса</b>\n\n"
    text += f"👤 {user.display_name} (#{user.id})\n"
    text += f"💰 Текущий баланс: {balance_str}\n\n"
    text += "Введите сумму в GTON (например: 1.5)"
    
    keyboard = [
        [
            {"text": t(lang, "ADMIN.balance_add"), "callback_data": f"admin:users:balance_add:{user_id}"},
            {"text": t(lang, "ADMIN.balance_subtract"), "callback_data": f"admin:users:balance_sub:{user_id}"}
        ],
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:users:view:{user_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def user_balance_action(query, lang: str, user_id: int, action: str):
    """Set state for balance input"""
    from core.database.models import UserService, User
    
    admin_telegram_id = query.from_user.id
    
    async with get_db() as session:
        result = await session.execute(
            select(User.id).where(User.telegram_id == admin_telegram_id)
        )
        admin_id = result.scalar()
        
        if admin_id:
            result = await session.execute(
                select(UserService).where(
                    UserService.user_id == admin_id,
                    UserService.service_id == "core"
                )
            )
            user_service = result.scalar_one_or_none()
            
            if not user_service:
                user_service = UserService(user_id=admin_id, service_id="core")
                session.add(user_service)
            
            user_service.state = f"admin_balance_{action}"
            user_service.state_data = {"target_user_id": user_id}
    
    text = t(lang, "ADMIN.balance_enter_amount")
    
    keyboard = [
        [{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:users:balance:{user_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_balance_input(update, context, admin_id: int, lang: str, action: str, target_user_id: int):
    """Handle balance amount input — GTON (Decimal)"""
    from core.database.models import User, Wallet, Transaction, UserService
    
    try:
        amount = Decimal(update.message.text.strip().replace(",", "."))
        if amount <= 0:
            raise ValueError()
    except (ValueError, Exception):
        await update.message.reply_text("❌ Введите положительное число (например: 1.5)")
        return
    
    # Clear state
    async with get_db() as session:
        result = await session.execute(
            select(UserService).where(
                UserService.user_id == admin_id,
                UserService.service_id == "core"
            )
        )
        user_service = result.scalar_one_or_none()
        if user_service:
            user_service.state = None
            user_service.state_data = None
    
    # Process balance change
    target_telegram_id = None
    target_lang = "ru"
    
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.id == target_user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await update.message.reply_text(t(lang, "ADMIN.users_search_not_found"))
            return
        
        target_telegram_id = user.telegram_id
        target_lang = user.language or "ru"
        
        result = await session.execute(
            select(Wallet).where(
                Wallet.user_id == target_user_id,
                Wallet.wallet_type == "main"
            ).with_for_update()
        )
        wallet = result.scalar_one_or_none()
        
        # Create wallet if not exists
        if not wallet:
            wallet = Wallet(
                user_id=target_user_id,
                wallet_type="main",
                balance=Decimal("0")
            )
            session.add(wallet)
            await session.flush()
        
        balance_before = Decimal(str(wallet.balance))
        
        if action == "subtract" and balance_before < amount:
            await update.message.reply_text(t(lang, "ADMIN.balance_error_insufficient"))
            return
        
        if action == "add":
            wallet.balance = balance_before + amount
            tx_type = "credit"
            tx_source = "admin"
        else:
            wallet.balance = balance_before - amount
            tx_type = "debit"
            tx_source = "admin"
        
        new_balance = Decimal(str(wallet.balance))
        
        # Create transaction
        transaction = Transaction(
            user_id=target_user_id,
            wallet_id=wallet.id,
            type=tx_type,
            amount=amount,
            direction=tx_type,
            balance_before=balance_before,
            balance_after=new_balance,
            source=tx_source,
            action="admin_balance_change",
            description=f"Admin #{admin_id}",
            status="completed",
            completed_at=datetime.utcnow()
        )
        session.add(transaction)
    
    # Format for display
    amount_str = format_gton(amount)
    new_balance_str = format_gton(new_balance)
    fiat = await currency_converter.convert_from_gton(new_balance, "RUB")
    if fiat:
        new_balance_str += f" (~{fiat:,.0f} ₽)"
    
    if action == "add":
        text = f"✅ Начислено: +{amount_str} GTON"
    else:
        text = f"✅ Списано: -{amount_str} GTON"
    
    text += f"\n💰 Новый баланс: {new_balance_str}"
    
    # Notify user
    if target_telegram_id:
        if action == "add":
            notify_text = t(target_lang, "ADMIN.notify_balance_added", amount=amount, balance=new_balance)
        else:
            notify_text = t(target_lang, "ADMIN.notify_balance_subtracted", amount=amount, balance=new_balance)
        
        await notify_user(context.bot, target_telegram_id, notify_text)
    
    keyboard = [
        [{"text": t(lang, "ADMIN.user_action_to_user"), "callback_data": f"admin:users:view:{target_user_id}"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:users"}]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def user_transactions(query, lang: str, user_id: int):
    """Show user transactions"""
    from core.database.models import Transaction
    
    async with get_db() as session:
        result = await session.execute(
            select(Transaction).where(
                Transaction.user_id == user_id
            ).order_by(desc(Transaction.created_at)).limit(15)
        )
        transactions = result.scalars().all()
    
    text = t(lang, "ADMIN.transactions_title", id=user_id) + "\n\n"
    
    if not transactions:
        text += t(lang, "ADMIN.transactions_empty")
    else:
        for tx in transactions:
            # Determine icon and sign
            if tx.direction == "credit":
                icon = "💚"
                sign = "+"
            else:
                icon = "🔴"
                sign = "-"
            
            # Source info
            source = tx.source or tx.action or tx.type
            amount_str = format_gton(Decimal(str(tx.amount)))
            
            text += f"{icon} {sign}{amount_str} GTON | {source}\n"
            text += f"   📅 {tx.created_at.strftime('%d.%m %H:%M')}\n"
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": f"admin:users:view:{user_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def user_message_menu(query, lang: str, user_id: int):
    """Send message to user menu"""
    from core.database.models import UserService, User
    
    admin_telegram_id = query.from_user.id
    
    async with get_db() as session:
        result = await session.execute(
            select(User.id).where(User.telegram_id == admin_telegram_id)
        )
        admin_id = result.scalar()
        
        if admin_id:
            result = await session.execute(
                select(UserService).where(
                    UserService.user_id == admin_id,
                    UserService.service_id == "core"
                )
            )
            user_service = result.scalar_one_or_none()
            
            if not user_service:
                user_service = UserService(user_id=admin_id, service_id="core")
                session.add(user_service)
            
            user_service.state = "admin_send_message"
            user_service.state_data = {"target_user_id": user_id}
    
    text = t(lang, "ADMIN.message_title") + "\n\n"
    text += t(lang, "ADMIN.message_enter_text")
    
    keyboard = [
        [{"text": t(lang, "COMMON.cancel"), "callback_data": f"admin:users:view:{user_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_send_message(update, context, admin_id: int, lang: str, target_user_id: int):
    """Handle sending message to user"""
    from core.database.models import User, UserService
    
    message_text = update.message.text
    
    # Clear state
    async with get_db() as session:
        result = await session.execute(
            select(UserService).where(
                UserService.user_id == admin_id,
                UserService.service_id == "core"
            )
        )
        user_service = result.scalar_one_or_none()
        if user_service:
            user_service.state = None
            user_service.state_data = None
        
        # Get target user telegram_id
        result = await session.execute(
            select(User.telegram_id).where(User.id == target_user_id)
        )
        target_telegram_id = result.scalar()
    
    if not target_telegram_id:
        await update.message.reply_text(t(lang, "ADMIN.users_search_not_found"))
        return
    
    try:
        await context.bot.send_message(
            chat_id=target_telegram_id,
            text=f"📨 <b>Сообщение от администратора:</b>\n\n{message_text}",
            parse_mode="HTML"
        )
        text = t(lang, "ADMIN.message_sent")
    except Exception as e:
        text = t(lang, "ADMIN.message_error") + f"\n{str(e)}"
    
    keyboard = [
        [{"text": f"👤 К пользователю", "callback_data": f"admin:users:view:{target_user_id}"}],
        [{"text": t(lang, "COMMON.back"), "callback_data": "admin:users"}]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
