"""
Telegram Stars Payment Provider

Провайдер для оплаты через Telegram Stars (XTR).
Stars — внутренняя валюта Telegram для цифровых товаров.

Процесс:
1. sendInvoice(currency="XTR") — отправить счёт
2. pre_checkout_query — подтвердить заказ
3. successful_payment — начислить GTON
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from loguru import logger


@dataclass
class StarsInvoice:
    """Invoice data for Stars payment"""
    invoice_id: str
    user_id: int
    stars_amount: int
    gton_amount: Decimal
    created_at: datetime


@dataclass
class StarsPaymentResult:
    """Result of Stars payment"""
    success: bool
    gton_amount: Optional[Decimal] = None
    transaction_id: Optional[int] = None
    error: Optional[str] = None


class StarsProvider:
    """
    Telegram Stars payment provider.
    
    Usage:
        provider = StarsProvider()
        
        # Get conversion rate
        rate = await provider.get_stars_to_gton_rate()
        
        # Calculate GTON for stars
        gton = await provider.stars_to_gton(100)  # 100 stars → X GTON
        
        # Process successful payment
        result = await provider.process_payment(user_id, stars_amount, charge_id)
    """
    
    # Default rate: 1 Star = 1.5 RUB (примерный курс)
    DEFAULT_STARS_RUB_RATE = Decimal("1.5")
    
    # Limits
    DEFAULT_MIN_STARS = 10
    DEFAULT_MAX_STARS = 10000
    
    async def get_stars_to_rub_rate(self) -> Decimal:
        """
        Get current Stars to RUB conversion rate.
        
        Returns:
            Rate: 1 Star = X RUB
        """
        from core.settings import settings
        
        rate = await settings.get_decimal(
            "payments.stars_rub_rate", 
            self.DEFAULT_STARS_RUB_RATE
        )
        return rate
    
    async def get_stars_to_gton_rate(self) -> Decimal:
        """
        Get current Stars to GTON conversion rate.
        Calculated: Stars → RUB → GTON
        
        Returns:
            Rate: 1 Star = X GTON
        """
        from core.payments.converter import currency_converter
        
        # 1 Star = X RUB
        stars_rub = await self.get_stars_to_rub_rate()
        
        # Get GTON rates (1 GTON = X RUB)
        try:
            gton_rates = await currency_converter.get_gton_rates()
            gton_rub = gton_rates.get("RUB", Decimal("100"))
        except:
            gton_rub = Decimal("100")  # fallback
        
        # 1 Star = stars_rub RUB
        # 1 GTON = gton_rub RUB
        # 1 Star = stars_rub / gton_rub GTON
        if gton_rub > 0:
            rate = stars_rub / gton_rub
        else:
            rate = Decimal("0.01")
        
        return rate.quantize(Decimal("0.000001"))
    
    async def get_limits(self) -> tuple[int, int]:
        """
        Get min/max Stars limits.
        
        Returns:
            (min_stars, max_stars)
        """
        from core.settings import settings
        
        min_stars = await settings.get_int(
            "payments.stars_min_amount", 
            self.DEFAULT_MIN_STARS
        )
        max_stars = await settings.get_int(
            "payments.stars_max_amount", 
            self.DEFAULT_MAX_STARS
        )
        return min_stars, max_stars
    
    async def is_enabled(self) -> bool:
        """Check if Stars payments are enabled"""
        from core.settings import settings
        return await settings.get_bool("payments.stars_enabled", True)
    
    async def stars_to_gton(self, stars_amount: int) -> Decimal:
        """
        Convert Stars to GTON.
        
        Args:
            stars_amount: Amount in Stars
            
        Returns:
            Amount in GTON
        """
        rate = await self.get_stars_to_gton_rate()
        gton = Decimal(str(stars_amount)) * rate
        return gton.quantize(Decimal("0.000001"))
    
    async def gton_to_stars(self, gton_amount: Decimal) -> int:
        """
        Convert GTON to Stars.
        
        Args:
            gton_amount: Amount in GTON
            
        Returns:
            Amount in Stars (rounded up)
        """
        rate = await self.get_stars_to_gton_rate()
        if rate <= 0:
            return 0
        stars = gton_amount / rate
        return int(stars.quantize(Decimal("1")))
    
    async def validate_amount(self, stars_amount: int) -> tuple[bool, Optional[str]]:
        """
        Validate Stars amount.
        
        Args:
            stars_amount: Amount to validate
            
        Returns:
            (is_valid, error_message)
        """
        min_stars, max_stars = await self.get_limits()
        
        if stars_amount < min_stars:
            return False, f"Минимум {min_stars} Stars"
        
        if stars_amount > max_stars:
            return False, f"Максимум {max_stars} Stars"
        
        return True, None
    
    async def create_invoice_data(
        self, 
        user_id: int, 
        stars_amount: int
    ) -> Optional[StarsInvoice]:
        """
        Create invoice data for Stars payment.
        
        Args:
            user_id: User ID
            stars_amount: Amount in Stars
            
        Returns:
            StarsInvoice or None if validation fails
        """
        # Validate
        is_valid, error = await self.validate_amount(stars_amount)
        if not is_valid:
            logger.warning(f"Invalid Stars amount {stars_amount}: {error}")
            return None
        
        # Calculate GTON
        gton_amount = await self.stars_to_gton(stars_amount)
        
        # Create invoice
        invoice = StarsInvoice(
            invoice_id=str(uuid4()),
            user_id=user_id,
            stars_amount=stars_amount,
            gton_amount=gton_amount,
            created_at=datetime.utcnow()
        )
        
        logger.info(
            f"Stars invoice created: user={user_id}, "
            f"stars={stars_amount}, gton={gton_amount}"
        )
        
        return invoice
    
    async def process_payment(
        self,
        user_id: int,
        stars_amount: int,
        telegram_charge_id: str,
        provider_charge_id: str = ""
    ) -> StarsPaymentResult:
        """
        Process successful Stars payment.
        
        Called after receiving successful_payment from Telegram.
        
        Args:
            user_id: User ID
            stars_amount: Amount paid in Stars
            telegram_charge_id: Telegram's payment charge ID
            provider_charge_id: Provider's charge ID (empty for Stars)
            
        Returns:
            StarsPaymentResult
        """
        from core.database import get_db
        from core.database.models import Wallet, Transaction, Payment
        from sqlalchemy import select
        
        try:
            # Calculate GTON
            gton_amount = await self.stars_to_gton(stars_amount)
            rate = await self.get_stars_to_gton_rate()
            
            async with get_db() as session:
                # Get or create wallet
                result = await session.execute(
                    select(Wallet).where(
                        Wallet.user_id == user_id,
                        Wallet.wallet_type == "main"
                    ).with_for_update()
                )
                wallet = result.scalar_one_or_none()
                
                if not wallet:
                    wallet = Wallet(
                        user_id=user_id,
                        wallet_type="main",
                        balance=Decimal("0")
                    )
                    session.add(wallet)
                    await session.flush()
                
                # Update balance
                balance_before = Decimal(str(wallet.balance))
                wallet.balance = balance_before + gton_amount
                
                # Create payment record
                payment = Payment(
                    uuid=str(uuid4()),
                    user_id=user_id,
                    amount_gton=gton_amount,
                    amount_original=Decimal(str(stars_amount)),
                    currency="XTR",
                    provider="stars",
                    provider_payment_id=telegram_charge_id,
                    provider_data={
                        "telegram_charge_id": telegram_charge_id,
                        "provider_charge_id": provider_charge_id,
                        "stars_amount": stars_amount,
                        "rate": str(rate)
                    },
                    status="completed",
                    completed_at=datetime.utcnow()
                )
                session.add(payment)
                await session.flush()
                
                # Create transaction
                transaction = Transaction(
                    user_id=user_id,
                    wallet_id=wallet.id,
                    type="credit",
                    amount=gton_amount,
                    direction="credit",
                    balance_before=balance_before,
                    balance_after=wallet.balance,
                    source="payment",
                    action="stars_topup",
                    reference_id=payment.uuid,
                    description=f"Пополнение {stars_amount} Stars → {gton_amount} GTON",
                    status="completed",
                    completed_at=datetime.utcnow()
                )
                session.add(transaction)
                await session.flush()
                
                transaction_id = transaction.id
            
            logger.info(
                f"Stars payment processed: user={user_id}, "
                f"stars={stars_amount}, gton={gton_amount}, "
                f"charge_id={telegram_charge_id}"
            )
            
            return StarsPaymentResult(
                success=True,
                gton_amount=gton_amount,
                transaction_id=transaction_id
            )
            
        except Exception as e:
            logger.error(f"Failed to process Stars payment: {e}")
            return StarsPaymentResult(
                success=False,
                error=str(e)
            )
    
    async def refund_payment(
        self,
        user_id: int,
        telegram_charge_id: str
    ) -> bool:
        """
        Refund Stars payment.
        
        Args:
            user_id: Telegram user ID
            telegram_charge_id: Original payment charge ID
            
        Returns:
            True if refund initiated
        """
        # Note: Actual refund is done via bot.refund_star_payment()
        # This method just logs the intent
        logger.info(
            f"Stars refund requested: user={user_id}, "
            f"charge_id={telegram_charge_id}"
        )
        return True


# Global instance
stars_provider = StarsProvider()
