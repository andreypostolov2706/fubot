"""
Daily Bonus Handler — Ежедневный бонус GTON
"""
from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes
from datetime import date, datetime

from core.locales import t
from core.database import get_db
from core.platform.telegram.utils import (
    get_or_create_user, 
    get_user_language,
    get_user_balance_with_fiat,
    format_gton,
    build_keyboard
)
from core.payments.converter import currency_converter


# Default rewards by day (GTON)
DEFAULT_REWARDS = [
    Decimal("0.1"),   # День 1
    Decimal("0.2"),   # День 2
    Decimal("0.3"),   # День 3
    Decimal("0.5"),   # День 4
    Decimal("0.7"),   # День 5
    Decimal("1.0"),   # День 6
    Decimal("2.0"),   # День 7 (максимум)
]


async def daily_bonus_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle daily_bonus callback"""
    query = update.callback_query
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    lang = await get_user_language(user_id)
    
    # Check sub-action
    data = query.data
    if ":" in data:
        action = data.split(":")[1]
        if action == "claim":
            await claim_bonus(query, user_id, lang)
            return
    
    await query.answer()
    await show_bonus_menu(query, user_id, lang)


async def show_bonus_menu(query, user_id: int, lang: str):
    """Show daily bonus menu"""
    from core.database.models import DailyBonus
    from sqlalchemy import select
    
    async with get_db() as session:
        result = await session.execute(
            select(DailyBonus).where(DailyBonus.user_id == user_id)
        )
        bonus = result.scalar_one_or_none()
    
    today = date.today()
    streak = 0
    can_claim = True
    day_number = 1
    
    if bonus:
        streak = bonus.current_streak
        
        if bonus.last_claim_date:
            days_diff = (today - bonus.last_claim_date).days
            
            if days_diff == 0:
                # Already claimed today
                can_claim = False
            elif days_diff == 1:
                # Continue streak
                day_number = (streak % 7) + 1
            else:
                # Streak lost
                streak = 0
                day_number = 1
    
    reward = DEFAULT_REWARDS[day_number - 1]
    reward_str = format_gton(reward)
    
    text = t(lang, "DAILY_BONUS.title") + "\n\n"
    text += t(lang, "DAILY_BONUS.streak", days=streak) + "\n"
    text += t(lang, "DAILY_BONUS.day_of", current=day_number, total=7) + "\n"
    text += t(lang, "DAILY_BONUS.reward", gton=reward_str)
    
    if not can_claim:
        text += "\n\n" + t(lang, "DAILY_BONUS.already_claimed")
        text += "\n" + t(lang, "DAILY_BONUS.dont_miss")
    
    keyboard = []
    if can_claim:
        keyboard.append([{
            "text": t(lang, "DAILY_BONUS.claim"), 
            "callback_data": "daily_bonus:claim"
        }])
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "main_menu"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def claim_bonus(query, user_id: int, lang: str):
    """Claim daily bonus"""
    from core.database.models import DailyBonus, DailyBonusHistory, Wallet, Transaction
    from sqlalchemy import select
    
    today = date.today()
    
    async with get_db() as session:
        # Get or create bonus record
        result = await session.execute(
            select(DailyBonus).where(DailyBonus.user_id == user_id)
        )
        bonus = result.scalar_one_or_none()
        
        if not bonus:
            bonus = DailyBonus(user_id=user_id)
            session.add(bonus)
            await session.flush()
        
        # Check if already claimed
        if bonus.last_claim_date == today:
            await query.answer(
                t(lang, "DAILY_BONUS.already_claimed"), 
                show_alert=True
            )
            return
        
        # Calculate streak and reward
        if bonus.last_claim_date:
            days_diff = (today - bonus.last_claim_date).days
            if days_diff == 1:
                bonus.current_streak += 1
            else:
                bonus.current_streak = 1
        else:
            bonus.current_streak = 1
        
        day_number = ((bonus.current_streak - 1) % 7) + 1
        reward = DEFAULT_REWARDS[day_number - 1]
        
        # Update bonus record
        bonus.last_claim_date = today
        bonus.last_claim_at = datetime.utcnow()
        bonus.total_claims += 1
        bonus.total_tokens = float(Decimal(str(bonus.total_tokens or 0)) + reward)
        
        if bonus.current_streak > bonus.max_streak:
            bonus.max_streak = bonus.current_streak
        
        # Add GTON to wallet
        result = await session.execute(
            select(Wallet).where(
                Wallet.user_id == user_id,
                Wallet.wallet_type == "main"
            )
        )
        wallet = result.scalar_one_or_none()
        
        if wallet:
            balance_before = Decimal(str(wallet.balance))
            wallet.balance = balance_before + reward
            
            # Create transaction
            transaction = Transaction(
                user_id=user_id,
                wallet_id=wallet.id,
                type="credit",
                amount=reward,
                direction="credit",
                balance_before=balance_before,
                balance_after=wallet.balance,
                source="bonus",
                action="daily_bonus",
                description=f"Ежедневный бонус (день {day_number})",
                status="completed",
                completed_at=datetime.utcnow()
            )
            session.add(transaction)
            await session.flush()
            
            # Create history
            history = DailyBonusHistory(
                user_id=user_id,
                daily_bonus_id=bonus.id,
                day_number=day_number,
                tokens=float(reward),
                streak=bonus.current_streak,
                transaction_id=transaction.id
            )
            session.add(history)
            
            new_balance = wallet.balance
        else:
            new_balance = reward
    
    # Get fiat equivalent for display
    fiat_balance = None
    try:
        fiat_balance = await currency_converter.convert_from_gton(
            Decimal(str(new_balance)), "RUB"
        )
    except:
        pass
    
    # Format for display
    reward_str = format_gton(reward)
    balance_str = format_gton(Decimal(str(new_balance)))
    fiat_str = f"{fiat_balance:,.0f}".replace(",", " ") if fiat_balance else "—"
    
    # Show success
    text = t(lang, "DAILY_BONUS.claimed_title") + "\n\n"
    text += t(lang, "DAILY_BONUS.claimed_gton", gton=reward_str) + "\n"
    text += t(lang, "DAILY_BONUS.new_balance", balance=balance_str, fiat=fiat_str) + "\n"
    text += t(lang, "DAILY_BONUS.new_streak", days=bonus.current_streak)
    
    if day_number == 7:
        text += "\n\n" + t(lang, "DAILY_BONUS.day7_congrats")
    else:
        next_reward = DEFAULT_REWARDS[day_number]
        next_reward_str = format_gton(next_reward)
        text += "\n\n" + t(lang, "DAILY_BONUS.next_reward", gton=next_reward_str)
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": "main_menu"}]
    ]
    
    await query.answer(f"🎁 +{reward_str} GTON!")
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
