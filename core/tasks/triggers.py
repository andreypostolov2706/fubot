"""
Trigger Processing Task
Автоматическая проверка и отправка триггерных рассылок
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_, or_, func

from core.database import get_db
from core.database.models import User, BroadcastTrigger, TriggerSendLog, Wallet, UserService

logger = logging.getLogger(__name__)

# Bot instance
_bot = None


def set_bot(bot):
    """Set bot instance for sending messages"""
    global _bot
    _bot = bot


async def process_triggers():
    """Main trigger processing loop - runs daily at 7:30"""
    logger.info("Trigger processor started")
    
    while True:
        try:
            now = datetime.now()
            
            # Calculate next run at 7:30
            target_time = now.replace(hour=7, minute=30, second=0, microsecond=0)
            
            # If it's already past 7:30 today, schedule for tomorrow
            if now >= target_time:
                target_time = target_time + timedelta(days=1)
            
            # Wait until target time
            wait_seconds = (target_time - now).total_seconds()
            logger.info(f"Trigger processor will run at {target_time.strftime('%Y-%m-%d %H:%M')}")
            
            await asyncio.sleep(wait_seconds)
            
            # Run triggers
            logger.info("Running trigger check...")
            await check_and_send_triggers()
            
            # Wait a bit before calculating next run
            await asyncio.sleep(60)
            
        except asyncio.CancelledError:
            logger.info("Trigger processor cancelled")
            break
        except Exception as e:
            logger.error(f"Error in trigger processor: {e}")
            # Wait 1 hour before retry on error
            await asyncio.sleep(3600)


async def check_and_send_triggers():
    """Check all active triggers and send messages"""
    if not _bot:
        logger.warning("Bot not set for trigger processor")
        return
    
    current_hour = datetime.now().hour
    
    async with get_db() as session:
        # Get active triggers within send time
        result = await session.execute(
            select(BroadcastTrigger).where(
                and_(
                    BroadcastTrigger.is_active == True,
                    BroadcastTrigger.send_start_hour <= current_hour,
                    BroadcastTrigger.send_end_hour > current_hour
                )
            )
        )
        triggers = result.scalars().all()
    
    for trigger in triggers:
        try:
            await process_single_trigger(trigger)
        except Exception as e:
            logger.error(f"Error processing trigger {trigger.id}: {e}")


async def process_single_trigger(trigger: BroadcastTrigger):
    """Process a single trigger"""
    trigger_type = trigger.trigger_type
    
    if trigger_type == "low_balance":
        await process_low_balance_trigger(trigger)
    elif trigger_type == "inactive":
        await process_inactive_trigger(trigger)
    elif trigger_type == "welcome":
        await process_welcome_trigger(trigger)
    elif trigger_type == "subscription_expiring":
        await process_subscription_expiring_trigger(trigger)
    elif trigger_type == "subscription_expired":
        await process_subscription_expired_trigger(trigger)
    # after_deposit обрабатывается событийно, не здесь


async def process_low_balance_trigger(trigger: BroadcastTrigger):
    """Process low balance trigger"""
    conditions = trigger.conditions or {}
    balance_threshold = conditions.get("balance_less_than", 100)
    
    async with get_db() as session:
        # Find users with low balance who haven't received this trigger recently
        result = await session.execute(
            select(User, Wallet.balance).join(
                Wallet, and_(Wallet.user_id == User.id, Wallet.type == "main")
            ).outerjoin(
                TriggerSendLog, and_(
                    TriggerSendLog.trigger_id == trigger.id,
                    TriggerSendLog.user_id == User.id
                )
            ).where(
                and_(
                    User.is_blocked == False,
                    User.is_active == True,
                    Wallet.balance < balance_threshold,
                    or_(
                        TriggerSendLog.id == None,
                        and_(
                            TriggerSendLog.send_count < trigger.max_sends_per_user,
                            TriggerSendLog.last_sent_at < datetime.utcnow() - timedelta(hours=trigger.cooldown_hours)
                        ) if trigger.max_sends_per_user > 0 else TriggerSendLog.last_sent_at < datetime.utcnow() - timedelta(hours=trigger.cooldown_hours)
                    )
                )
            ).limit(50)  # Process in batches
        )
        users_data = result.all()
    
    for user, balance in users_data:
        await send_trigger_message(trigger, user, {"balance": balance})


async def process_inactive_trigger(trigger: BroadcastTrigger):
    """Process inactive users trigger"""
    conditions = trigger.conditions or {}
    inactive_days = conditions.get("inactive_days", 7)
    exclude_new_days = conditions.get("exclude_new_users_days", 3)
    
    inactive_since = datetime.utcnow() - timedelta(days=inactive_days)
    not_new_since = datetime.utcnow() - timedelta(days=exclude_new_days)
    
    async with get_db() as session:
        result = await session.execute(
            select(User).outerjoin(
                TriggerSendLog, and_(
                    TriggerSendLog.trigger_id == trigger.id,
                    TriggerSendLog.user_id == User.id
                )
            ).where(
                and_(
                    User.is_blocked == False,
                    User.is_active == True,
                    User.last_activity_at < inactive_since,
                    User.created_at < not_new_since,
                    or_(
                        TriggerSendLog.id == None,
                        and_(
                            TriggerSendLog.send_count < trigger.max_sends_per_user,
                            TriggerSendLog.last_sent_at < datetime.utcnow() - timedelta(hours=trigger.cooldown_hours)
                        ) if trigger.max_sends_per_user > 0 else TriggerSendLog.last_sent_at < datetime.utcnow() - timedelta(hours=trigger.cooldown_hours)
                    )
                )
            ).limit(50)
        )
        users = result.scalars().all()
    
    for user in users:
        days = (datetime.utcnow() - user.last_activity_at).days if user.last_activity_at else inactive_days
        await send_trigger_message(trigger, user, {"days": days})


async def process_welcome_trigger(trigger: BroadcastTrigger):
    """Process welcome trigger for new users"""
    conditions = trigger.conditions or {}
    hours_after = conditions.get("hours_after_registration", 24)
    only_inactive = conditions.get("only_if_inactive", True)
    
    registered_before = datetime.utcnow() - timedelta(hours=hours_after)
    registered_after = datetime.utcnow() - timedelta(hours=hours_after + 24)  # Window of 24 hours
    
    async with get_db() as session:
        query = select(User).outerjoin(
            TriggerSendLog, and_(
                TriggerSendLog.trigger_id == trigger.id,
                TriggerSendLog.user_id == User.id
            )
        ).where(
            and_(
                User.is_blocked == False,
                User.is_active == True,
                User.created_at <= registered_before,
                User.created_at >= registered_after,
                TriggerSendLog.id == None  # Never sent before
            )
        )
        
        if only_inactive:
            # Only users who haven't been active since registration
            query = query.where(
                or_(
                    User.last_activity_at == None,
                    User.last_activity_at <= User.created_at + timedelta(hours=1)
                )
            )
        
        result = await session.execute(query.limit(50))
        users = result.scalars().all()
    
    for user in users:
        await send_trigger_message(trigger, user, {})


async def process_subscription_expiring_trigger(trigger: BroadcastTrigger):
    """Process subscription expiring trigger"""
    conditions = trigger.conditions or {}
    days_before = conditions.get("days_before_expiry", 3)
    
    expiry_start = datetime.utcnow() + timedelta(days=days_before - 1)
    expiry_end = datetime.utcnow() + timedelta(days=days_before + 1)
    
    async with get_db() as session:
        result = await session.execute(
            select(User, UserService).join(
                UserService, UserService.user_id == User.id
            ).outerjoin(
                TriggerSendLog, and_(
                    TriggerSendLog.trigger_id == trigger.id,
                    TriggerSendLog.user_id == User.id
                )
            ).where(
                and_(
                    User.is_blocked == False,
                    UserService.subscription_until != None,
                    UserService.subscription_until >= expiry_start,
                    UserService.subscription_until <= expiry_end,
                    or_(
                        TriggerSendLog.id == None,
                        TriggerSendLog.last_sent_at < datetime.utcnow() - timedelta(hours=trigger.cooldown_hours)
                    )
                )
            ).limit(50)
        )
        data = result.all()
    
    for user, service in data:
        days = (service.subscription_until - datetime.utcnow()).days
        await send_trigger_message(trigger, user, {
            "days": days,
            "subscription": service.subscription_plan or "подписка"
        })


async def process_subscription_expired_trigger(trigger: BroadcastTrigger):
    """Process subscription expired trigger"""
    conditions = trigger.conditions or {}
    hours_after = conditions.get("hours_after_expiry", 1)
    
    expired_before = datetime.utcnow() - timedelta(hours=hours_after)
    expired_after = datetime.utcnow() - timedelta(hours=hours_after + 24)
    
    async with get_db() as session:
        result = await session.execute(
            select(User, UserService).join(
                UserService, UserService.user_id == User.id
            ).outerjoin(
                TriggerSendLog, and_(
                    TriggerSendLog.trigger_id == trigger.id,
                    TriggerSendLog.user_id == User.id
                )
            ).where(
                and_(
                    User.is_blocked == False,
                    UserService.subscription_until != None,
                    UserService.subscription_until <= expired_before,
                    UserService.subscription_until >= expired_after,
                    or_(
                        TriggerSendLog.id == None,
                        and_(
                            TriggerSendLog.send_count < trigger.max_sends_per_user,
                            TriggerSendLog.last_sent_at < datetime.utcnow() - timedelta(hours=trigger.cooldown_hours)
                        ) if trigger.max_sends_per_user > 0 else TriggerSendLog.last_sent_at < datetime.utcnow() - timedelta(hours=trigger.cooldown_hours)
                    )
                )
            ).limit(50)
        )
        data = result.all()
    
    for user, service in data:
        await send_trigger_message(trigger, user, {
            "subscription": service.subscription_plan or "подписка"
        })


async def send_trigger_message(trigger: BroadcastTrigger, user: User, variables: dict = None, skip_delay: bool = False) -> bool:
    """Send trigger message to user. Returns True if successful."""
    if not _bot:
        return False
    
    variables = variables or {}
    
    # Apply delay if configured (skip for manual sends)
    if trigger.delay_minutes > 0 and not skip_delay:
        await asyncio.sleep(trigger.delay_minutes * 60)
    
    # Prepare message text with variables
    text = trigger.text
    text = text.replace("{name}", user.first_name or "")
    text = text.replace("{username}", f"@{user.telegram_username}" if user.telegram_username else "")
    
    for key, value in variables.items():
        text = text.replace(f"{{{key}}}", str(value))
    
    # Prepare buttons
    reply_markup = None
    if trigger.buttons:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        for row in trigger.buttons:
            keyboard_row = []
            for btn in row:
                if btn.get("url"):
                    keyboard_row.append(InlineKeyboardButton(text=btn["text"], url=btn["url"]))
                elif btn.get("callback_data"):
                    keyboard_row.append(InlineKeyboardButton(text=btn["text"], callback_data=btn["callback_data"]))
            if keyboard_row:
                keyboard.append(keyboard_row)
        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Send message
        if trigger.media_type and trigger.media_file_id:
            if trigger.media_type == "photo":
                await _bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=trigger.media_file_id,
                    caption=text,
                    parse_mode=trigger.parse_mode,
                    reply_markup=reply_markup
                )
            elif trigger.media_type == "video":
                await _bot.send_video(
                    chat_id=user.telegram_id,
                    video=trigger.media_file_id,
                    caption=text,
                    parse_mode=trigger.parse_mode,
                    reply_markup=reply_markup
                )
            elif trigger.media_type == "animation":
                await _bot.send_animation(
                    chat_id=user.telegram_id,
                    animation=trigger.media_file_id,
                    caption=text,
                    parse_mode=trigger.parse_mode,
                    reply_markup=reply_markup
                )
            elif trigger.media_type == "document":
                await _bot.send_document(
                    chat_id=user.telegram_id,
                    document=trigger.media_file_id,
                    caption=text,
                    parse_mode=trigger.parse_mode,
                    reply_markup=reply_markup
                )
        else:
            await _bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                parse_mode=trigger.parse_mode,
                reply_markup=reply_markup
            )
        
        # Log successful send
        await log_trigger_send(trigger.id, user.id, success=True)
        
        logger.info(f"Trigger {trigger.id} sent to user {user.id}")
        
        # Rate limiting - wait between sends
        await asyncio.sleep(0.1)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send trigger {trigger.id} to user {user.id}: {e}")
        await log_trigger_send(trigger.id, user.id, success=False)
        return False


async def log_trigger_send(trigger_id: int, user_id: int, success: bool):
    """Log trigger send to prevent spam"""
    async with get_db() as session:
        # Check if log exists
        result = await session.execute(
            select(TriggerSendLog).where(
                and_(
                    TriggerSendLog.trigger_id == trigger_id,
                    TriggerSendLog.user_id == user_id
                )
            )
        )
        log = result.scalar_one_or_none()
        
        if log:
            log.send_count += 1
            log.last_sent_at = datetime.utcnow()
        else:
            log = TriggerSendLog(
                trigger_id=trigger_id,
                user_id=user_id,
                send_count=1
            )
            session.add(log)


async def update_trigger_stats(trigger_id: int, delivered: bool):
    """Update trigger statistics"""
    async with get_db() as session:
        result = await session.execute(
            select(BroadcastTrigger).where(BroadcastTrigger.id == trigger_id)
        )
        trigger = result.scalar_one_or_none()
        
        if trigger:
            trigger.total_sent += 1
            if delivered:
                trigger.total_delivered += 1
            trigger.last_run_at = datetime.utcnow()


# === Event-based triggers ===

async def on_user_deposit(user_id: int, amount: float):
    """Called when user makes a deposit - for after_deposit trigger"""
    async with get_db() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return
        
        # Get active after_deposit triggers
        result = await session.execute(
            select(BroadcastTrigger).where(
                and_(
                    BroadcastTrigger.is_active == True,
                    BroadcastTrigger.trigger_type == "after_deposit"
                )
            )
        )
        triggers = result.scalars().all()
    
    for trigger in triggers:
        conditions = trigger.conditions or {}
        min_amount = conditions.get("min_amount", 0)
        first_only = conditions.get("first_deposit_only", False)
        
        if amount < min_amount:
            continue
        
        # Check if first deposit only
        if first_only:
            async with get_db() as session:
                result = await session.execute(
                    select(TriggerSendLog).where(
                        and_(
                            TriggerSendLog.trigger_id == trigger.id,
                            TriggerSendLog.user_id == user_id
                        )
                    )
                )
                if result.scalar_one_or_none():
                    continue  # Already sent
        
        # Send with delay
        asyncio.create_task(
            send_trigger_message(trigger, user, {"amount": amount})
        )


async def find_matching_users(trigger: BroadcastTrigger) -> list:
    """Find users matching trigger conditions (for manual send)"""
    trigger_type = trigger.trigger_type
    conditions = trigger.conditions or {}
    users = []
    
    async with get_db() as session:
        if trigger_type == "low_balance":
            balance_threshold = conditions.get("balance_less_than", 100)
            result = await session.execute(
                select(User).join(
                    Wallet, and_(Wallet.user_id == User.id, Wallet.type == "main")
                ).where(
                    and_(
                        User.is_blocked == False,
                        User.is_active == True,
                        Wallet.balance < balance_threshold
                    )
                ).limit(100)
            )
            users = result.scalars().all()
            
        elif trigger_type == "inactive":
            inactive_days = conditions.get("inactive_days", 7)
            exclude_new_days = conditions.get("exclude_new_users_days", 3)
            inactive_since = datetime.utcnow() - timedelta(days=inactive_days)
            not_new_since = datetime.utcnow() - timedelta(days=exclude_new_days)
            
            result = await session.execute(
                select(User).where(
                    and_(
                        User.is_blocked == False,
                        User.is_active == True,
                        User.last_activity_at < inactive_since,
                        User.created_at < not_new_since
                    )
                ).limit(100)
            )
            users = result.scalars().all()
            
        elif trigger_type == "welcome":
            hours_after = conditions.get("hours_after_registration", 24)
            registered_before = datetime.utcnow() - timedelta(hours=hours_after)
            
            result = await session.execute(
                select(User).where(
                    and_(
                        User.is_blocked == False,
                        User.is_active == True,
                        User.created_at <= registered_before
                    )
                ).limit(100)
            )
            users = result.scalars().all()
            
        elif trigger_type == "subscription_expiring":
            days_before = conditions.get("days_before_expiry", 3)
            expiry_start = datetime.utcnow()
            expiry_end = datetime.utcnow() + timedelta(days=days_before)
            
            result = await session.execute(
                select(User).join(
                    UserService, UserService.user_id == User.id
                ).where(
                    and_(
                        User.is_blocked == False,
                        UserService.subscription_until != None,
                        UserService.subscription_until >= expiry_start,
                        UserService.subscription_until <= expiry_end
                    )
                ).limit(100)
            )
            users = result.scalars().all()
            
        elif trigger_type == "subscription_expired":
            hours_after = conditions.get("hours_after_expiry", 1)
            expired_before = datetime.utcnow() - timedelta(hours=hours_after)
            
            result = await session.execute(
                select(User).join(
                    UserService, UserService.user_id == User.id
                ).where(
                    and_(
                        User.is_blocked == False,
                        UserService.subscription_until != None,
                        UserService.subscription_until < expired_before
                    )
                ).limit(100)
            )
            users = result.scalars().all()
            
        else:
            # Default: all active users
            result = await session.execute(
                select(User).where(
                    and_(
                        User.is_blocked == False,
                        User.is_active == True
                    )
                ).limit(100)
            )
            users = result.scalars().all()
    
    return users
