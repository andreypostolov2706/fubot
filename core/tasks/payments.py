"""
Payment Checker - Background task for automatic payment verification
"""
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from loguru import logger

from core.database import get_db
from core.database.models import Payment, User
from core.payments.service import payment_service
from core.payments.providers.manager import provider_manager
from core.payments.providers.base import PaymentStatus
from core.payments.converter import currency_converter
from sqlalchemy import select

# Bot instance for sending notifications
_bot = None


def set_bot(bot):
    """Set bot instance for notifications"""
    global _bot
    _bot = bot


async def send_payment_notification(user_id: int, gton_amount: Decimal):
    """Send notification to user about successful payment"""
    global _bot
    
    if not _bot:
        logger.warning("Bot not set, cannot send payment notification")
        return
    
    try:
        # Get user's telegram_id
        async with get_db() as session:
            result = await session.execute(
                select(User.telegram_id).where(User.id == user_id)
            )
            telegram_id = result.scalar_one_or_none()
        
        if not telegram_id:
            logger.warning(f"Telegram ID not found for user {user_id}")
            return
        
        # Get fiat equivalent
        fiat_amount = await currency_converter.convert_from_gton(gton_amount, "RUB")
        
        # Format message
        gton_str = f"{gton_amount:.2f}" if gton_amount >= 1 else f"{gton_amount:.4f}"
        
        if fiat_amount:
            fiat_str = f"{fiat_amount:,.0f}".replace(",", " ")
            text = (
                f"✅ <b>Платёж получен!</b>\n\n"
                f"💰 Зачислено: <b>{gton_str} GTON</b> (~{fiat_str} ₽)\n\n"
                f"Спасибо за пополнение! 🎉"
            )
        else:
            text = (
                f"✅ <b>Платёж получен!</b>\n\n"
                f"💰 Зачислено: <b>{gton_str} GTON</b>\n\n"
                f"Спасибо за пополнение! 🎉"
            )
        
        # Send notification
        await _bot.send_message(
            chat_id=telegram_id,
            text=text,
            parse_mode="HTML"
        )
        
        logger.info(f"Payment notification sent to user {user_id} (telegram: {telegram_id})")
        
    except Exception as e:
        logger.error(f"Failed to send payment notification to user {user_id}: {e}")


async def check_pending_payments():
    """Check all pending payments and confirm paid ones"""
    try:
        async with get_db() as session:
            # Get pending payments (not too new to avoid race conditions)
            result = await session.execute(
                select(Payment)
                .where(Payment.status == "pending")
                .order_by(Payment.created_at.asc())
                .limit(20)
            )
            payments = result.scalars().all()
        
        if not payments:
            return
        
        logger.debug(f"Checking {len(payments)} pending payments...")
        
        for payment in payments:
            try:
                # Get provider
                provider = provider_manager.get_provider(payment.provider)
                if not provider or not payment.provider_payment_id:
                    continue
                
                # Check status with provider
                status = await provider.check_payment(payment.provider_payment_id)
                
                if status == PaymentStatus.COMPLETED:
                    logger.info(f"Payment {payment.uuid} is paid, confirming...")
                    
                    # Save user_id and amount before confirmation
                    user_id = payment.user_id
                    
                    # Confirm and credit balance
                    success = await payment_service.confirm_payment(
                        payment_uuid=payment.uuid,
                        provider_payment_id=payment.provider_payment_id
                    )
                    
                    if success:
                        # Get updated payment to get actual GTON amount
                        async with get_db() as session:
                            result = await session.execute(
                                select(Payment).where(Payment.uuid == payment.uuid)
                            )
                            updated_payment = result.scalar_one_or_none()
                            gton_amount = Decimal(str(updated_payment.amount_gton)) if updated_payment else payment.amount_gton
                        
                        logger.info(f"✅ Payment {payment.uuid} confirmed, {gton_amount} GTON credited")
                        
                        # Send notification to user
                        await send_payment_notification(user_id, gton_amount)
                    else:
                        logger.error(f"❌ Failed to confirm payment {payment.uuid}")
                
                elif status == PaymentStatus.EXPIRED:
                    # Mark as expired
                    async with get_db() as session:
                        result = await session.execute(
                            select(Payment).where(Payment.uuid == payment.uuid)
                        )
                        p = result.scalar_one_or_none()
                        if p and p.status == "pending":
                            p.status = "expired"
                            logger.info(f"Payment {payment.uuid} marked as expired")
                
                # Small delay between checks
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error checking payment {payment.uuid}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in check_pending_payments: {e}")


async def payment_checker_task():
    """Background task - checks payments every 15 seconds"""
    logger.info("Payment checker task started")
    
    # Wait a bit before first check
    await asyncio.sleep(10)
    
    while True:
        try:
            await check_pending_payments()
            await asyncio.sleep(15)  # Check every 15 seconds
            
        except asyncio.CancelledError:
            logger.info("Payment checker task stopped")
            break
        except Exception as e:
            logger.error(f"Error in payment checker: {e}")
            await asyncio.sleep(30)
