"""
Payment Service

Main service for handling payments and GTON operations.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from uuid import uuid4
from loguru import logger

from core.database import get_db
from .converter import currency_converter, ConversionResult
from .rates import rates_manager


@dataclass
class PaymentResult:
    """Result of payment creation"""
    success: bool
    payment_uuid: Optional[str] = None
    payment_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class PaymentInfo:
    """Payment information"""
    uuid: str
    user_id: int
    amount_gton: Decimal
    amount_original: Decimal
    currency: str
    provider: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    completed_at: Optional[datetime]


class PaymentService:
    """
    Service for managing payments and GTON balance.
    """
    
    async def get_balance(self, user_id: int) -> Decimal:
        """
        Get user's GTON balance.
        
        Args:
            user_id: User ID
            
        Returns:
            GTON balance
        """
        from core.database.models import Wallet
        from sqlalchemy import select
        
        async with get_db() as session:
            result = await session.execute(
                select(Wallet).where(
                    Wallet.user_id == user_id,
                    Wallet.wallet_type == "main"
                )
            )
            wallet = result.scalar_one_or_none()
            
            if wallet:
                return Decimal(str(wallet.balance))
            
            return Decimal("0")
    
    async def get_balance_with_fiat(
        self, 
        user_id: int,
        fiat_currency: str = "RUB"
    ) -> tuple[Decimal, Optional[Decimal]]:
        """
        Get user's GTON balance with fiat equivalent.
        
        Returns:
            (gton_balance, fiat_equivalent)
        """
        gton_balance = await self.get_balance(user_id)
        fiat_equivalent = await currency_converter.convert_from_gton(
            gton_balance, 
            fiat_currency
        )
        return gton_balance, fiat_equivalent
    
    async def add_gton(
        self,
        user_id: int,
        amount: Decimal,
        source: str,
        description: str = None,
        reference_id: int = None,
        session = None
    ) -> bool:
        """
        Add GTON to user's balance.
        
        Args:
            user_id: User ID
            amount: Amount to add
            source: Source of funds (payment, referral, bonus, admin)
            description: Optional description
            reference_id: Optional reference (payment_id, etc.)
            session: Optional existing session (to avoid nested sessions)
            
        Returns:
            True if successful
        """
        from core.database.models import Wallet, Transaction
        from sqlalchemy import select
        
        if amount <= 0:
            return False
        
        async def _add_gton(session):
            # Get or create wallet
            result = await session.execute(
                select(Wallet).where(
                    Wallet.user_id == user_id,
                    Wallet.wallet_type == "main"
                )
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
            old_balance = Decimal(str(wallet.balance))
            wallet.balance = old_balance + amount
            
            # Create transaction
            transaction = Transaction(
                user_id=user_id,
                wallet_id=wallet.id,
                type="credit",
                direction="credit",
                amount=amount,
                balance_before=old_balance,
                balance_after=wallet.balance,
                source=source,
                description=description or f"GTON credit: {source}",
                reference_id=reference_id,
                status="completed"
            )
            session.add(transaction)
            
            logger.info(f"Added {amount} GTON to user {user_id}. New balance: {wallet.balance}")
            return True
        
        # Use provided session or create new one
        if session:
            return await _add_gton(session)
        else:
            async with get_db() as new_session:
                result = await _add_gton(new_session)
                return result
    
    async def deduct_gton(
        self,
        user_id: int,
        amount: Decimal,
        reason: str,
        action: str = "deduct",
        service_id: str = None
    ) -> tuple[bool, Optional[str]]:
        """
        Deduct GTON from user's balance.
        
        Args:
            user_id: User ID
            amount: Amount to deduct
            reason: Reason for deduction
            action: Action type (deduct, purchase, fee)
            service_id: Service that initiated deduction
            
        Returns:
            (success, error_message)
        """
        from core.database.models import Wallet, Transaction
        from sqlalchemy import select
        
        if amount <= 0:
            return False, "Invalid amount"
        
        async with get_db() as session:
            result = await session.execute(
                select(Wallet).where(
                    Wallet.user_id == user_id,
                    Wallet.wallet_type == "main"
                )
            )
            wallet = result.scalar_one_or_none()
            
            if not wallet:
                return False, "Wallet not found"
            
            current_balance = Decimal(str(wallet.balance))
            
            if current_balance < amount:
                return False, "Insufficient balance"
            
            # Update balance
            wallet.balance = current_balance - amount
            
            # Create transaction
            transaction = Transaction(
                user_id=user_id,
                wallet_id=wallet.id,
                type="debit",
                amount=amount,
                balance_before=current_balance,
                balance_after=wallet.balance,
                source=service_id or "core",
                action=action,
                description=reason
            )
            session.add(transaction)
            
            logger.info(f"Deducted {amount} GTON from user {user_id}. New balance: {wallet.balance}")
            
        return True, None
    
    async def create_payment(
        self,
        user_id: int,
        amount_gton: Decimal,
        provider: str,
        currency: str = None
    ) -> PaymentResult:
        """
        Create a new payment.
        
        Args:
            user_id: User ID
            amount_gton: Amount in GTON to purchase
            provider: Payment provider ID
            currency: Payment currency (provider default if not specified)
            
        Returns:
            PaymentResult with payment URL
        """
        from core.database.models import Payment, PaymentProvider, Setting
        from sqlalchemy import select
        
        async with get_db() as session:
            # Check minimum deposit
            min_result = await session.execute(
                select(Setting).where(Setting.key == "payments.min_deposit_gton")
            )
            min_setting = min_result.scalar_one_or_none()
            min_deposit = Decimal(min_setting.value) if min_setting else Decimal("1")
            
            if amount_gton < min_deposit:
                return PaymentResult(
                    success=False,
                    error=f"Minimum deposit is {min_deposit} GTON"
                )
            
            # Get provider
            provider_result = await session.execute(
                select(PaymentProvider).where(
                    PaymentProvider.id == provider,
                    PaymentProvider.is_active == True
                )
            )
            provider_record = provider_result.scalar_one_or_none()
            
            if not provider_record:
                return PaymentResult(
                    success=False,
                    error="Payment provider not found or inactive"
                )
            
            # Use provider's default currency if not specified
            if not currency:
                currencies = provider_record.currencies or []
                currency = currencies[0] if currencies else "USD"
            
            # Convert GTON to payment currency
            amount_currency = await currency_converter.convert_from_gton(
                amount_gton, 
                currency
            )
            
            if not amount_currency:
                return PaymentResult(
                    success=False,
                    error="Failed to convert currency"
                )
            
            # Apply provider fee
            fee_percent = Decimal(str(provider_record.fee_percent or 0))
            
            # Get global fee
            fee_result = await session.execute(
                select(Setting).where(Setting.key == "payments.fee_percent")
            )
            fee_setting = fee_result.scalar_one_or_none()
            if fee_setting:
                fee_percent += Decimal(fee_setting.value)
            
            fee_amount = amount_currency * fee_percent / Decimal("100")
            total_amount = amount_currency + fee_amount
            
            # Get payment timeout
            timeout_result = await session.execute(
                select(Setting).where(Setting.key == "payments.payment_timeout_minutes")
            )
            timeout_setting = timeout_result.scalar_one_or_none()
            timeout_minutes = int(timeout_setting.value) if timeout_setting else 30
            
            # Create payment record
            payment_uuid = str(uuid4())
            expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
            
            payment = Payment(
                uuid=payment_uuid,
                user_id=user_id,
                amount_gton=amount_gton,
                amount_original=total_amount,
                currency=currency,
                fee_percent=fee_percent,
                fee_amount=fee_amount,
                provider=provider,
                status="pending",
                expires_at=expires_at
            )
            session.add(payment)
            await session.flush()
            
            # Call actual payment provider
            from .providers.manager import provider_manager
            
            provider_instance = provider_manager.get_provider(provider)
            if not provider_instance:
                payment.status = "failed"
                payment.error_message = "Provider not configured"
                return PaymentResult(
                    success=False,
                    error="Payment provider not configured"
                )
            
            # Create payment at provider
            provider_result = await provider_instance.create_payment(
                amount=total_amount,
                currency=currency,
                user_id=user_id,
                payment_uuid=payment_uuid,
                description=f"Пополнение баланса: {amount_gton} GTON",
                expires_in=timeout_minutes * 60
            )
            
            if not provider_result.success:
                payment.status = "failed"
                payment.error_message = provider_result.error
                return PaymentResult(
                    success=False,
                    error=provider_result.error
                )
            
            # Update payment with provider data
            payment.provider_payment_id = provider_result.provider_payment_id
            payment.provider_data = provider_result.raw_response
            
            return PaymentResult(
                success=True,
                payment_uuid=payment_uuid,
                payment_url=provider_result.payment_url,
                expires_at=expires_at
            )
    
    async def confirm_payment(
        self,
        payment_uuid: str,
        provider_payment_id: str = None,
        provider_data: dict = None
    ) -> bool:
        """
        Confirm payment and credit GTON to user.
        Called when payment provider confirms payment.
        
        Args:
            payment_uuid: Payment UUID
            provider_payment_id: ID from payment provider
            provider_data: Additional data from provider
            
        Returns:
            True if successful
        """
        from core.database.models import Payment
        from sqlalchemy import select
        
        async with get_db() as session:
            result = await session.execute(
                select(Payment).where(Payment.uuid == payment_uuid)
            )
            payment = result.scalar_one_or_none()
            
            if not payment:
                logger.error(f"Payment not found: {payment_uuid}")
                return False
            
            if payment.status != "pending":
                logger.warning(f"Payment already processed: {payment_uuid}")
                return False
            
            # Get current rates at confirmation time
            rates = await rates_manager.get_all_rates()
            
            payment.rate_ton_usd = rates.get("TON_USD")
            payment.rate_gton_ton = rates.get("GTON_TON")
            
            # Get currency rate
            if payment.currency != "USD":
                rate = await rates_manager.get_rate("USD", payment.currency)
                payment.rate_currency_usd = rate
            else:
                payment.rate_currency_usd = Decimal("1")
            
            # Recalculate GTON amount with current rates
            net_amount = payment.amount_original - payment.fee_amount
            conversion = await currency_converter.convert_to_gton(
                net_amount,
                payment.currency
            )
            
            if not conversion.success:
                logger.error(f"Conversion failed for payment {payment_uuid}")
                payment.status = "failed"
                return False
            
            # Update payment with actual GTON amount
            payment.amount_gton = conversion.gton_amount
            payment.provider_payment_id = provider_payment_id
            payment.provider_data = provider_data
            payment.status = "completed"
            payment.completed_at = datetime.utcnow()
            
            await session.flush()
            
            # Credit GTON to user (pass session to avoid nested sessions)
            success = await self.add_gton(
                user_id=payment.user_id,
                amount=conversion.gton_amount,
                source="payment",
                description=f"Payment {payment_uuid[:8]}",
                reference_id=payment.id,
                session=session
            )
            
            if success:
                # Update transaction reference
                payment.transaction_id = payment.id  # Will be updated properly
                logger.info(f"Payment confirmed: {payment_uuid}, credited {conversion.gton_amount} GTON")
            
            return success
    
    async def get_payment(self, payment_uuid: str) -> Optional[PaymentInfo]:
        """Get payment information"""
        from core.database.models import Payment
        from sqlalchemy import select
        
        async with get_db() as session:
            result = await session.execute(
                select(Payment).where(Payment.uuid == payment_uuid)
            )
            payment = result.scalar_one_or_none()
            
            if not payment:
                return None
            
            return PaymentInfo(
                uuid=payment.uuid,
                user_id=payment.user_id,
                amount_gton=Decimal(str(payment.amount_gton)),
                amount_original=Decimal(str(payment.amount_original)),
                currency=payment.currency,
                provider=payment.provider,
                status=payment.status,
                created_at=payment.created_at,
                expires_at=payment.expires_at,
                completed_at=payment.completed_at
            )
    
    async def get_user_payments(
        self,
        user_id: int,
        status: str = None,
        limit: int = 20
    ) -> List[PaymentInfo]:
        """Get user's payment history"""
        from core.database.models import Payment
        from sqlalchemy import select
        
        async with get_db() as session:
            query = select(Payment).where(Payment.user_id == user_id)
            
            if status:
                query = query.where(Payment.status == status)
            
            query = query.order_by(Payment.created_at.desc()).limit(limit)
            
            result = await session.execute(query)
            payments = result.scalars().all()
            
            return [
                PaymentInfo(
                    uuid=p.uuid,
                    user_id=p.user_id,
                    amount_gton=Decimal(str(p.amount_gton)),
                    amount_original=Decimal(str(p.amount_original)),
                    currency=p.currency,
                    provider=p.provider,
                    status=p.status,
                    created_at=p.created_at,
                    expires_at=p.expires_at,
                    completed_at=p.completed_at
                )
                for p in payments
            ]
    
    async def expire_pending_payments(self) -> int:
        """
        Mark expired pending payments as expired.
        Called by background task.
        
        Returns:
            Number of expired payments
        """
        from core.database.models import Payment
        from sqlalchemy import select, update
        
        async with get_db() as session:
            result = await session.execute(
                update(Payment)
                .where(
                    Payment.status == "pending",
                    Payment.expires_at < datetime.utcnow()
                )
                .values(status="expired")
            )
            
            count = result.rowcount
            if count > 0:
                logger.info(f"Expired {count} pending payments")
            
            return count


# Global instance
payment_service = PaymentService()
