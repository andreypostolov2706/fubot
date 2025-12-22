"""
Core API - Interface for services to interact with core
"""
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass

from loguru import logger

from core.database import get_db
from core.locales import t


@dataclass
class TransactionResult:
    """Transaction result"""
    success: bool
    transaction_id: Optional[int] = None
    new_balance: Optional[Decimal] = None
    error: Optional[str] = None


@dataclass
class UserDTO:
    """User data transfer object"""
    id: int
    telegram_id: Optional[int]
    telegram_username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    language: str
    role: str
    is_active: bool
    is_blocked: bool
    created_at: datetime
    last_activity_at: Optional[datetime]


@dataclass
class SubscriptionDTO:
    """Subscription data transfer object"""
    is_active: bool
    plan: Optional[str]
    expires_at: Optional[datetime]
    auto_renew: bool
    days_left: int


class CoreAPI:
    """
    Core API for services.
    
    Services use this interface for all operations with core.
    """
    
    def __init__(self, service_id: str):
        """
        Initialize Core API for service.
        
        Args:
            service_id: Service ID
        """
        self.service_id = service_id
    
    # ==================== USERS ====================
    
    async def get_user(self, telegram_id: int) -> Optional[UserDTO]:
        """
        Get user by telegram_id.
        
        Returns:
            UserDTO or None if not found
        """
        from core.database.models import User
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            return UserDTO(
                id=user.id,
                telegram_id=user.telegram_id,
                telegram_username=user.telegram_username,
                first_name=user.first_name,
                last_name=user.last_name,
                language=user.language,
                role=user.role,
                is_active=user.is_active,
                is_blocked=user.is_blocked,
                created_at=user.created_at,
                last_activity_at=user.last_activity_at
            )
    
    async def get_user_by_id(self, user_id: int) -> Optional[UserDTO]:
        """Get user by internal ID."""
        from core.database.models import User
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            return UserDTO(
                id=user.id,
                telegram_id=user.telegram_id,
                telegram_username=user.telegram_username,
                first_name=user.first_name,
                last_name=user.last_name,
                language=user.language,
                role=user.role,
                is_active=user.is_active,
                is_blocked=user.is_blocked,
                created_at=user.created_at,
                last_activity_at=user.last_activity_at
            )
    
    async def get_user_language(self, user_id: int) -> str:
        """Get user language."""
        user = await self.get_user_by_id(user_id)
        return user.language if user else "ru"
    
    async def get_text(self, user_id: int, path: str, **kwargs) -> str:
        """
        Get localized text for user.
        
        Args:
            user_id: User ID
            path: Path "SECTION.key"
            **kwargs: Format parameters
        
        Returns:
            Localized text
        """
        lang = await self.get_user_language(user_id)
        return t(lang, path, **kwargs)
    
    # ==================== BALANCE ====================
    
    async def get_balance(self, user_id: int, wallet_type: str = "main") -> Decimal:
        """
        Get user balance in GTON.
        
        Args:
            user_id: User ID
            wallet_type: "main" or "bonus"
        
        Returns:
            Balance in GTON (Decimal with 6 decimal places)
        """
        from core.database.models import Wallet
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Wallet).where(
                    Wallet.user_id == user_id,
                    Wallet.wallet_type == wallet_type
                )
            )
            wallet = result.scalar_one_or_none()
            
            return Decimal(str(wallet.balance)) if wallet else Decimal("0")
    
    async def get_all_balances(self, user_id: int) -> dict[str, Decimal]:
        """
        Get all user balances.
        
        Returns:
            {"main": Decimal("100.5"), "bonus": Decimal("50.0")}
        """
        from core.database.models import Wallet
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Wallet).where(Wallet.user_id == user_id)
            )
            wallets = result.scalars().all()
            
            return {w.wallet_type: Decimal(str(w.balance)) for w in wallets}
    
    async def get_balance_with_fiat(self, user_id: int, fiat: str = "RUB") -> tuple[Decimal, Optional[Decimal]]:
        """
        Get user GTON balance with fiat equivalent.
        
        Returns:
            (gton_balance, fiat_equivalent)
        """
        from core.payments.converter import currency_converter
        
        gton = await self.get_balance(user_id)
        fiat_amount = await currency_converter.convert_from_gton(gton, fiat)
        return gton, fiat_amount
    
    async def deduct_balance(
        self, 
        user_id: int, 
        amount: Decimal, 
        reason: str = "",
        action: str = "",
        data: dict = None
    ) -> TransactionResult:
        """
        Deduct GTON from balance.
        
        Args:
            user_id: User ID
            amount: Amount in GTON (Decimal)
            reason: Description (for history)
            action: Service action (chat_message, voice, etc.)
            data: Additional data
        
        Returns:
            TransactionResult
        """
        from core.database.models import Wallet, Transaction
        
        amount = Decimal(str(amount))
        
        if amount <= 0:
            return TransactionResult(success=False, error="Invalid amount")
        
        async with get_db() as session:
            from sqlalchemy import select
            
            # Get main wallet
            result = await session.execute(
                select(Wallet).where(
                    Wallet.user_id == user_id,
                    Wallet.wallet_type == "main"
                ).with_for_update()
            )
            wallet = result.scalar_one_or_none()
            
            if not wallet:
                return TransactionResult(
                    success=False, 
                    error="Wallet not found",
                    new_balance=Decimal("0")
                )
            
            if wallet.available_balance < amount:
                return TransactionResult(
                    success=False,
                    error="Insufficient balance",
                    new_balance=Decimal(str(wallet.balance))
                )
            
            # Deduct
            balance_before = Decimal(str(wallet.balance))
            wallet.balance = balance_before - amount
            
            # Create transaction
            transaction = Transaction(
                user_id=user_id,
                wallet_id=wallet.id,
                type="debit",
                amount=amount,
                direction="debit",
                balance_before=balance_before,
                balance_after=wallet.balance,
                service_id=self.service_id,
                service_action=action,
                service_data=data,
                source=self.service_id,
                action=action,
                description=reason,
                status="completed",
                completed_at=datetime.utcnow()
            )
            session.add(transaction)
            await session.flush()
            
            logger.info(
                f"GTON deducted: user={user_id}, amount={amount}, "
                f"service={self.service_id}, action={action}"
            )
        
        # Process referral commission (outside transaction to avoid locks)
        try:
            from core.referral import commission_service
            await commission_service.process_commission(
                user_id=user_id,
                amount=amount,
                service_id=self.service_id,
                action=action,
                transaction_id=transaction.id
            )
        except Exception as e:
            logger.warning(f"Failed to process referral commission: {e}")
        
        return TransactionResult(
            success=True,
            transaction_id=transaction.id,
            new_balance=Decimal(str(wallet.balance))
        )
    
    async def add_balance(
        self,
        user_id: int,
        amount: Decimal,
        wallet_type: str = "main",
        source: str = "",
        reason: str = ""
    ) -> TransactionResult:
        """
        Add GTON to balance.
        
        Args:
            user_id: User ID
            amount: Amount in GTON (Decimal)
            wallet_type: "main" or "bonus"
            source: Source (refund, bonus, admin, payment)
            reason: Description
        """
        from core.database.models import Wallet, Transaction
        
        amount = Decimal(str(amount))
        
        if amount <= 0:
            return TransactionResult(success=False, error="Invalid amount")
        
        async with get_db() as session:
            from sqlalchemy import select
            
            # Get or create wallet
            result = await session.execute(
                select(Wallet).where(
                    Wallet.user_id == user_id,
                    Wallet.wallet_type == wallet_type
                ).with_for_update()
            )
            wallet = result.scalar_one_or_none()
            
            if not wallet:
                wallet = Wallet(
                    user_id=user_id, 
                    wallet_type=wallet_type, 
                    balance=Decimal("0")
                )
                session.add(wallet)
                await session.flush()
            
            # Add
            balance_before = Decimal(str(wallet.balance))
            wallet.balance = balance_before + amount
            
            # Create transaction
            transaction = Transaction(
                user_id=user_id,
                wallet_id=wallet.id,
                type="credit",
                amount=amount,
                direction="credit",
                balance_before=balance_before,
                balance_after=wallet.balance,
                service_id=self.service_id,
                source=source or self.service_id,
                description=reason,
                status="completed",
                completed_at=datetime.utcnow()
            )
            session.add(transaction)
            await session.flush()
            
            logger.info(
                f"GTON added: user={user_id}, amount={amount}, "
                f"source={source}, service={self.service_id}"
            )
            
            return TransactionResult(
                success=True,
                transaction_id=transaction.id,
                new_balance=Decimal(str(wallet.balance))
            )
    
    # ==================== USER SERVICE ====================
    
    async def get_user_service_data(self, user_id: int):
        """
        Get user data for current service.
        
        Returns:
            UserServiceDTO
        """
        from core.database.models import UserService
        from core.plugins.base_service import UserServiceDTO
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(UserService).where(
                    UserService.user_id == user_id,
                    UserService.service_id == self.service_id
                )
            )
            us = result.scalar_one_or_none()
            
            if not us:
                return UserServiceDTO()
            
            return UserServiceDTO(
                role=us.role,
                settings=us.settings or {},
                subscription_plan=us.subscription_plan,
                subscription_until=us.subscription_until,
                total_spent=us.total_spent,
                usage_count=us.usage_count,
                first_use_at=us.first_use_at,
                last_use_at=us.last_use_at
            )
    
    async def get_user_service_settings(self, user_id: int) -> dict:
        """Get user settings for service."""
        data = await self.get_user_service_data(user_id)
        return data.settings
    
    async def set_user_service_settings(self, user_id: int, settings: dict):
        """Save user settings for service."""
        from core.database.models import UserService
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(UserService).where(
                    UserService.user_id == user_id,
                    UserService.service_id == self.service_id
                )
            )
            us = result.scalar_one_or_none()
            
            if not us:
                us = UserService(
                    user_id=user_id,
                    service_id=self.service_id,
                    settings=settings
                )
                session.add(us)
            else:
                us.settings = {**(us.settings or {}), **settings}
    
    # ==================== FSM STATE ====================
    
    async def set_user_state(self, user_id: int, state: str, data: dict = None):
        """
        Set user state (FSM).
        
        Example:
            await self.core.set_user_state(user_id, "waiting_message", {
                "session_id": 123
            })
        """
        from core.database.models import UserService
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(UserService).where(
                    UserService.user_id == user_id,
                    UserService.service_id == self.service_id
                )
            )
            us = result.scalar_one_or_none()
            
            if not us:
                us = UserService(
                    user_id=user_id,
                    service_id=self.service_id,
                    state=state,
                    state_data=data,
                    state_updated_at=datetime.utcnow()
                )
                session.add(us)
            else:
                us.state = state
                us.state_data = data
                us.state_updated_at = datetime.utcnow()
    
    async def get_user_state(self, user_id: int) -> tuple[Optional[str], Optional[dict]]:
        """
        Get user state.
        
        Returns:
            (state_name, state_data)
        """
        from core.database.models import UserService
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(UserService).where(
                    UserService.user_id == user_id,
                    UserService.service_id == self.service_id
                )
            )
            us = result.scalar_one_or_none()
            
            if not us:
                return None, None
            
            return us.state, us.state_data
    
    async def clear_user_state(self, user_id: int):
        """Clear user state."""
        await self.set_user_state(user_id, None, None)
    
    # ==================== SUBSCRIPTION ====================
    
    async def check_subscription(self, user_id: int) -> SubscriptionDTO:
        """
        Check user subscription.
        
        Returns:
            SubscriptionDTO
        """
        from core.database.models import UserService
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(UserService).where(
                    UserService.user_id == user_id,
                    UserService.service_id == self.service_id
                )
            )
            us = result.scalar_one_or_none()
            
            if not us or not us.subscription_until:
                return SubscriptionDTO(
                    is_active=False,
                    plan=None,
                    expires_at=None,
                    auto_renew=False,
                    days_left=0
                )
            
            is_active = us.subscription_until > datetime.utcnow()
            days_left = 0
            if is_active:
                delta = us.subscription_until - datetime.utcnow()
                days_left = delta.days
            
            return SubscriptionDTO(
                is_active=is_active,
                plan=us.subscription_plan,
                expires_at=us.subscription_until,
                auto_renew=us.subscription_auto_renew,
                days_left=days_left
            )
    
    # ==================== ANALYTICS ====================
    
    async def track_event(
        self,
        event_name: str,
        user_id: int = None,
        label: str = None,
        value: int = None,
        properties: dict = None
    ):
        """
        Track event for analytics.
        
        Args:
            event_name: Event name (session_started, message_sent)
            user_id: User ID
            label: Additional label
            value: Numeric value
            properties: Arbitrary data
        
        Note:
            Event automatically gets service prefix:
            "message_sent" → "service:ai_psychologist:message_sent"
        """
        from core.database.models import Event
        
        async with get_db() as session:
            event = Event(
                user_id=user_id,
                category="service",
                action=f"service:{self.service_id}:{event_name}",
                service_id=self.service_id,
                label=label,
                value=value,
                properties=properties,
                platform="telegram"
            )
            session.add(event)
        
        logger.debug(
            f"Event tracked: {event_name}, user={user_id}, "
            f"value={value}, service={self.service_id}"
        )
    
    # ==================== SETTINGS ====================
    
    async def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get global setting.
        
        Args:
            key: Setting key (tokens.rate_rub, referral.enabled)
            default: Default value
        """
        from core.database.models import Setting
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Setting).where(Setting.key == key)
            )
            setting = result.scalar_one_or_none()
            
            if not setting:
                return default
            
            return setting.get_typed_value()
    
    async def get_service_config(self) -> dict:
        """Get current service configuration."""
        from core.database.models import Service
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Service).where(Service.id == self.service_id)
            )
            service = result.scalar_one_or_none()
            
            return service.config if service else {}
    
    async def update_service_config(self, config: dict):
        """Update service configuration."""
        from core.database.models import Service
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Service).where(Service.id == self.service_id)
            )
            service = result.scalar_one_or_none()
            
            if service:
                service.config = {**(service.config or {}), **config}
    
    # ==================== CURRENCY CONVERSION ====================
    
    async def convert_to_gton(self, amount: Decimal, currency: str) -> Optional[Decimal]:
        """
        Convert any currency to GTON.
        
        Args:
            amount: Amount in source currency
            currency: Currency code (RUB, USD, EUR, TON)
            
        Returns:
            Amount in GTON, or None on error
        """
        from core.payments.converter import currency_converter
        
        result = await currency_converter.convert_to_gton(Decimal(str(amount)), currency)
        return result.gton_amount if result.success else None
    
    async def convert_from_gton(self, gton_amount: Decimal, currency: str) -> Optional[Decimal]:
        """
        Convert GTON to any currency.
        
        Args:
            gton_amount: Amount in GTON
            currency: Target currency code
            
        Returns:
            Amount in target currency, or None on error
        """
        from core.payments.converter import currency_converter
        
        return await currency_converter.convert_from_gton(Decimal(str(gton_amount)), currency)
    
    async def get_gton_rates(self) -> dict[str, Decimal]:
        """
        Get current GTON rates in various currencies.
        
        Returns:
            {"TON": Decimal, "USD": Decimal, "RUB": Decimal}
        """
        from core.payments.converter import currency_converter
        
        return await currency_converter.get_gton_rates()
    
    async def format_gton(self, amount: Decimal, with_fiat: bool = True, fiat: str = "RUB") -> str:
        """
        Format GTON amount for display.
        
        Args:
            amount: Amount in GTON
            with_fiat: Include fiat equivalent
            fiat: Fiat currency for equivalent
            
        Returns:
            Formatted string like "10.5 GTON (~1,085 ₽)"
        """
        from core.payments.converter import currency_converter
        
        if with_fiat:
            return await currency_converter.format_gton_with_fiat(Decimal(str(amount)), fiat)
        
        gton_str = f"{amount:.6f}".rstrip('0').rstrip('.')
        return f"{gton_str} GTON"
    
    # ==================== MESSAGING ====================
    
    async def send_message(
        self, 
        user_id: int, 
        text: str, 
        keyboard: list = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Send message to user.
        
        Args:
            user_id: Telegram user ID
            text: Message text
            keyboard: Optional inline keyboard
            parse_mode: Parse mode (HTML or Markdown)
            
        Returns:
            True if sent successfully
        """
        try:
            from core.platform.telegram.bot import get_bot
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            
            bot = get_bot()
            if not bot:
                logger.error("Bot not initialized")
                return False
            
            reply_markup = None
            if keyboard:
                buttons = []
                for row in keyboard:
                    btn_row = []
                    for btn in row:
                        btn_row.append(InlineKeyboardButton(
                            text=btn.get("text", ""),
                            callback_data=btn.get("callback_data")
                        ))
                    buttons.append(btn_row)
                reply_markup = InlineKeyboardMarkup(buttons)
            
            await bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to {user_id}: {e}")
            return False
