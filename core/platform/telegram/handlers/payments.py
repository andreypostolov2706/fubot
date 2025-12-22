"""
Payment Handlers — Обработчики платежей Telegram

Обрабатывает:
- pre_checkout_query — подтверждение заказа перед оплатой
- successful_payment — успешная оплата (начисление GTON)
"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from core.locales import t
from core.platform.telegram.utils import (
    get_or_create_user,
    get_user_language,
    format_gton,
    build_keyboard
)


async def handle_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle pre-checkout query from Telegram.
    
    Called when user clicks "Pay" button.
    Must respond within 10 seconds.
    """
    query = update.pre_checkout_query
    
    try:
        # Parse payload
        payload = query.invoice_payload
        
        # Validate payload format
        if not payload.startswith("stars_topup:"):
            await query.answer(ok=False, error_message="Invalid payment")
            return
        
        parts = payload.split(":")
        if len(parts) != 3:
            await query.answer(ok=False, error_message="Invalid payment format")
            return
        
        _, user_id_str, stars_str = parts
        user_id = int(user_id_str)
        stars_amount = int(stars_str)
        
        # Verify user
        if query.from_user.id != user_id:
            # Get actual user_id from telegram_id
            actual_user_id = await get_or_create_user(query.from_user.id, query.from_user)
            if actual_user_id != user_id:
                logger.warning(
                    f"Pre-checkout user mismatch: payload={user_id}, actual={actual_user_id}"
                )
                # Still allow - user might have different internal ID
        
        # Validate amount
        from core.payments.providers.stars import stars_provider
        
        is_valid, error = await stars_provider.validate_amount(stars_amount)
        if not is_valid:
            await query.answer(ok=False, error_message=error)
            return
        
        # All good - approve
        await query.answer(ok=True)
        
        logger.info(
            f"Pre-checkout approved: user={query.from_user.id}, "
            f"stars={stars_amount}, currency={query.currency}"
        )
        
    except Exception as e:
        logger.error(f"Pre-checkout error: {e}")
        await query.answer(ok=False, error_message="Payment error. Please try again.")


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle successful payment from Telegram.
    
    Called after user completes payment.
    Credits GTON to user's balance.
    """
    message = update.message
    payment = message.successful_payment
    
    try:
        # Get user
        telegram_user = update.effective_user
        user_id = await get_or_create_user(telegram_user.id, telegram_user)
        lang = await get_user_language(user_id)
        
        # Parse payload
        payload = payment.invoice_payload
        
        if not payload.startswith("stars_topup:"):
            logger.error(f"Unknown payment payload: {payload}")
            await message.reply_text("❌ Ошибка обработки платежа")
            return
        
        parts = payload.split(":")
        if len(parts) != 3:
            logger.error(f"Invalid payload format: {payload}")
            await message.reply_text("❌ Ошибка обработки платежа")
            return
        
        _, _, stars_str = parts
        stars_amount = int(stars_str)
        
        # Get charge IDs
        telegram_charge_id = payment.telegram_payment_charge_id
        provider_charge_id = payment.provider_payment_charge_id or ""
        
        # Process payment
        from core.payments.providers.stars import stars_provider
        
        result = await stars_provider.process_payment(
            user_id=user_id,
            stars_amount=stars_amount,
            telegram_charge_id=telegram_charge_id,
            provider_charge_id=provider_charge_id
        )
        
        if result.success:
            # Success message
            text = "✅ <b>Оплата успешна!</b>\n\n"
            text += f"⭐ Оплачено: {stars_amount} Stars\n"
            text += f"💰 Начислено: {format_gton(result.gton_amount)} GTON\n\n"
            text += "Спасибо за пополнение!"
            
            keyboard = [
                [{"text": "💰 Мой баланс", "callback_data": "main_menu"}],
                [{"text": "⭐ Пополнить ещё", "callback_data": "top_up:stars"}]
            ]
            
            await message.reply_text(
                text,
                reply_markup=build_keyboard(keyboard),
                parse_mode="HTML"
            )
            
            logger.info(
                f"Stars payment success: user={user_id}, "
                f"stars={stars_amount}, gton={result.gton_amount}, "
                f"charge_id={telegram_charge_id}"
            )
            
        else:
            # Error
            await message.reply_text(
                f"❌ Ошибка начисления: {result.error}\n\n"
                "Обратитесь в поддержку с ID платежа:\n"
                f"<code>{telegram_charge_id}</code>",
                parse_mode="HTML"
            )
            
            logger.error(
                f"Stars payment failed: user={user_id}, "
                f"stars={stars_amount}, error={result.error}"
            )
            
    except Exception as e:
        logger.error(f"Successful payment handler error: {e}")
        await message.reply_text(
            "❌ Произошла ошибка при обработке платежа.\n"
            "Обратитесь в поддержку."
        )
