"""
Promocode Handler — Промокоды с наградами в GTON
"""
from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

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


async def promocode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle promocode callback"""
    query = update.callback_query
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    lang = await get_user_language(user_id)
    
    data = query.data
    if ":" in data:
        action = data.split(":")[1]
        if action == "cancel":
            # Clear state and go back
            await clear_promocode_state(user_id)
            await query.answer()
            # Redirect to top_up
            from .topup import topup_callback
            await topup_callback(update, context)
            return
    
    await query.answer()
    
    # Set state for promocode input
    await set_promocode_state(user_id)
    
    text = t(lang, "PROMOCODE.enter_code")
    
    keyboard = [
        [{"text": t(lang, "COMMON.cancel"), "callback_data": "promocode:cancel"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def set_promocode_state(user_id: int):
    """Set user state to waiting for promocode"""
    from core.database.models import UserService
    
    async with get_db() as session:
        from sqlalchemy import select
        
        # Use special "core" service for core states
        result = await session.execute(
            select(UserService).where(
                UserService.user_id == user_id,
                UserService.service_id == "core"
            )
        )
        user_service = result.scalar_one_or_none()
        
        if not user_service:
            user_service = UserService(
                user_id=user_id,
                service_id="core"
            )
            session.add(user_service)
        
        user_service.state = "waiting_promocode"
        user_service.state_data = {}


async def clear_promocode_state(user_id: int):
    """Clear promocode state"""
    from core.database.models import UserService
    
    async with get_db() as session:
        from sqlalchemy import select
        
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


async def handle_promocode_input(update: Update, user_id: int, lang: str):
    """Handle promocode text input"""
    code = update.message.text.strip().upper()
    
    # Validate and activate
    result = await activate_promocode(user_id, code)
    
    if result["success"]:
        text = t(lang, "PROMOCODE.activated") + "\n\n"
        
        if result["reward_type"] == "gton":
            gton_str = format_gton(result["reward_value"])
            balance_str = format_gton(result["new_balance"])
            # Get fiat equivalent
            fiat = await currency_converter.convert_from_gton(result["reward_value"], "RUB")
            fiat_str = f"{fiat:,.0f}".replace(",", " ") if fiat else "—"
            fiat_balance = await currency_converter.convert_from_gton(result["new_balance"], "RUB")
            fiat_balance_str = f"{fiat_balance:,.0f}".replace(",", " ") if fiat_balance else "—"
            
            text += t(lang, "PROMOCODE.reward_gton", amount=gton_str, fiat=fiat_str) + "\n"
            text += t(lang, "PROMOCODE.new_balance", balance=balance_str, fiat=fiat_balance_str)
        elif result["reward_type"] == "subscription":
            text += t(lang, "PROMOCODE.reward_subscription", 
                     plan=result.get("plan", "Premium"),
                     days=result["reward_value"])
        elif result["reward_type"] == "discount":
            text += t(lang, "PROMOCODE.reward_discount", percent=result["reward_value"])
    else:
        error_key = f"PROMOCODE.{result['error']}"
        text = t(lang, error_key) if t(lang, error_key) != error_key else t(lang, "PROMOCODE.invalid")
    
    # Clear state
    await clear_promocode_state(user_id)
    
    keyboard = [
        [{"text": t(lang, "COMMON.back"), "callback_data": "main_menu"}]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def activate_promocode(user_id: int, code: str) -> dict:
    """Validate and activate promocode"""
    from core.database.models import PromoCode, PromoCodeActivation, Wallet, Transaction, User
    from sqlalchemy import select, func
    
    async with get_db() as session:
        # Find promocode
        result = await session.execute(
            select(PromoCode).where(
                PromoCode.code == code,
                PromoCode.is_active == True
            )
        )
        promo = result.scalar_one_or_none()
        
        if not promo:
            return {"success": False, "error": "invalid"}
        
        # Check expiration
        if promo.expires_at and promo.expires_at < datetime.utcnow():
            return {"success": False, "error": "expired"}
        
        # Check start date
        if promo.starts_at and promo.starts_at > datetime.utcnow():
            return {"success": False, "error": "invalid"}
        
        # Check max activations
        if promo.max_activations and promo.current_activations >= promo.max_activations:
            return {"success": False, "error": "limit_reached"}
        
        # Check user activations
        result = await session.execute(
            select(func.count(PromoCodeActivation.id)).where(
                PromoCodeActivation.promocode_id == promo.id,
                PromoCodeActivation.user_id == user_id
            )
        )
        user_activations = result.scalar() or 0
        
        if promo.max_per_user and user_activations >= promo.max_per_user:
            return {"success": False, "error": "already_used"}
        
        # Check new users only
        if promo.only_new_users:
            result = await session.execute(
                select(User.created_at).where(User.id == user_id)
            )
            created_at = result.scalar()
            # New user = registered less than 24 hours ago
            from datetime import timedelta
            if created_at and (datetime.utcnow() - created_at) > timedelta(hours=24):
                return {"success": False, "error": "new_users_only"}
        
        # Activate based on reward type
        transaction_id = None
        new_balance = Decimal("0")
        reward_value = Decimal(str(promo.reward_value))
        
        if promo.reward_type == "gton":
            # Add GTON to wallet
            result = await session.execute(
                select(Wallet).where(
                    Wallet.user_id == user_id,
                    Wallet.wallet_type == "bonus"
                )
            )
            wallet = result.scalar_one_or_none()
            
            if not wallet:
                # Try main wallet
                result = await session.execute(
                    select(Wallet).where(
                        Wallet.user_id == user_id,
                        Wallet.wallet_type == "main"
                    )
                )
                wallet = result.scalar_one_or_none()
            
            if wallet:
                balance_before = Decimal(str(wallet.balance))
                wallet.balance = balance_before + reward_value
                new_balance = Decimal(str(wallet.balance))
                
                # Create transaction
                transaction = Transaction(
                    user_id=user_id,
                    wallet_id=wallet.id,
                    type="credit",
                    amount=reward_value,
                    direction="credit",
                    balance_before=balance_before,
                    balance_after=wallet.balance,
                    source="promocode",
                    action="activate",
                    reference_id=code,
                    description=f"Промокод {code}",
                    status="completed",
                    completed_at=datetime.utcnow()
                )
                session.add(transaction)
                await session.flush()
                transaction_id = transaction.id
        
        # Create activation record
        activation = PromoCodeActivation(
            promocode_id=promo.id,
            user_id=user_id,
            reward_type=promo.reward_type,
            reward_value=promo.reward_value,
            transaction_id=transaction_id
        )
        session.add(activation)
        
        # Update promocode counter
        promo.current_activations += 1
        
        # If promocode is bound to a partner, create referral
        if promo.partner_id:
            from core.database.models import Referral, Partner
            
            # Get partner and their user_id
            result = await session.execute(
                select(Partner).where(Partner.id == promo.partner_id)
            )
            partner = result.scalar_one_or_none()
            
            if partner and partner.user_id != user_id:  # Can't be referral of yourself
                # Check if user is not already a referral of this partner
                result = await session.execute(
                    select(Referral).where(
                        Referral.referred_id == user_id,
                        Referral.referrer_id == partner.user_id
                    )
                )
                existing_referral = result.scalar_one_or_none()
                
                if not existing_referral:
                    # Create referral
                    referral = Referral(
                        referrer_id=partner.user_id,
                        referred_id=user_id,
                        partner_id=partner.id,
                        level=1
                    )
                    session.add(referral)
                    
                    # Update partner stats
                    partner.total_referrals = (partner.total_referrals or 0) + 1
        
        return {
            "success": True,
            "reward_type": promo.reward_type,
            "reward_value": promo.reward_value,
            "new_balance": new_balance
        }
