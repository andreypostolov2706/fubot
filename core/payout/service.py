"""
Payout Service — Сервис вывода средств

Обрабатывает заявки партнёров на вывод GTON в фиат.
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional, Tuple
from dataclasses import dataclass

from loguru import logger
from sqlalchemy import select

from core.database import get_db
from core.database.models import Partner, Payout, User, Setting
from core.payments.converter import currency_converter


@dataclass
class PayoutResult:
    """Result of payout operation"""
    success: bool
    payout_id: Optional[int] = None
    error: Optional[str] = None
    amount_gton: Optional[Decimal] = None
    amount_fiat: Optional[Decimal] = None


class PayoutService:
    """Service for handling partner payouts"""
    
    # Fee percentage for withdrawals
    DEFAULT_FEE_PERCENT = Decimal("0")  # 0% fee by default
    
    async def get_min_payout_gton(self) -> Decimal:
        """Get minimum payout amount in GTON"""
        from core.settings import settings
        return await settings.get_decimal("payout.min_gton", Decimal("5.0"))
    
    async def get_fee_percent(self) -> Decimal:
        """Get withdrawal fee percentage"""
        from core.settings import settings
        return await settings.get_decimal("payout.fee_percent", self.DEFAULT_FEE_PERCENT)
    
    async def create_payout_request(
        self,
        partner_id: int,
        amount_gton: Decimal,
        method: str,
        details: dict,
        currency: str = "RUB"
    ) -> PayoutResult:
        """
        Create a new payout request.
        
        Args:
            partner_id: Partner ID
            amount_gton: Amount in GTON to withdraw
            method: Payout method (card, sbp, crypto)
            details: Method details (card number, etc.)
            currency: Target fiat currency
            
        Returns:
            PayoutResult with status and details
        """
        try:
            # Validate amount
            min_payout = await self.get_min_payout_gton()
            if amount_gton < min_payout:
                return PayoutResult(
                    success=False,
                    error=f"Минимальная сумма вывода: {min_payout} GTON"
                )
            
            async with get_db() as session:
                # Get partner
                result = await session.execute(
                    select(Partner).where(Partner.id == partner_id)
                )
                partner = result.scalar_one_or_none()
                
                if not partner:
                    return PayoutResult(success=False, error="Партнёр не найден")
                
                if partner.status != "active":
                    return PayoutResult(success=False, error="Партнёр не активен")
                
                # Check available balance
                available = partner.available_balance
                if amount_gton > available:
                    return PayoutResult(
                        success=False,
                        error=f"Недостаточно средств. Доступно: {available} GTON"
                    )
                
                # Calculate fee
                fee_percent = await self.get_fee_percent()
                fee_gton = (amount_gton * fee_percent / 100).quantize(Decimal("0.000001"))
                
                # Get current GTON rate
                gton_rate = await currency_converter.convert_from_gton(Decimal("1"), currency)
                if not gton_rate:
                    return PayoutResult(success=False, error="Не удалось получить курс")
                
                # Calculate fiat amount
                net_gton = amount_gton - fee_gton
                amount_fiat = (net_gton * gton_rate).quantize(Decimal("0.01"))
                
                # Freeze the amount
                partner.frozen_balance = Decimal(str(partner.frozen_balance or 0)) + amount_gton
                
                # Create payout request
                payout = Payout(
                    partner_id=partner_id,
                    amount_gton=amount_gton,
                    fee_gton=fee_gton,
                    amount_fiat=amount_fiat,
                    currency=currency,
                    gton_rate=gton_rate,
                    method=method,
                    details=details,
                    status="pending",
                    created_at=datetime.utcnow()
                )
                session.add(payout)
                await session.flush()
                
                payout_id = payout.id
            
            logger.info(
                f"Payout request created: partner={partner_id}, "
                f"amount={amount_gton} GTON (~{amount_fiat} {currency}), "
                f"method={method}, id={payout_id}"
            )
            
            return PayoutResult(
                success=True,
                payout_id=payout_id,
                amount_gton=amount_gton,
                amount_fiat=amount_fiat
            )
            
        except Exception as e:
            logger.error(f"Error creating payout request: {e}")
            return PayoutResult(success=False, error=str(e))
    
    async def approve_payout(
        self,
        payout_id: int,
        admin_id: int,
        comment: Optional[str] = None
    ) -> PayoutResult:
        """
        Approve and process a payout request.
        
        Args:
            payout_id: Payout request ID
            admin_id: Admin user ID who approves
            comment: Optional admin comment
        """
        try:
            async with get_db() as session:
                # Get payout
                result = await session.execute(
                    select(Payout).where(Payout.id == payout_id)
                )
                payout = result.scalar_one_or_none()
                
                if not payout:
                    return PayoutResult(success=False, error="Заявка не найдена")
                
                if payout.status != "pending":
                    return PayoutResult(success=False, error=f"Заявка уже обработана: {payout.status}")
                
                # Get partner
                result = await session.execute(
                    select(Partner).where(Partner.id == payout.partner_id)
                )
                partner = result.scalar_one_or_none()
                
                if not partner:
                    return PayoutResult(success=False, error="Партнёр не найден")
                
                # Deduct from balance and frozen
                amount = Decimal(str(payout.amount_gton))
                partner.balance = Decimal(str(partner.balance)) - amount
                partner.frozen_balance = Decimal(str(partner.frozen_balance or 0)) - amount
                partner.total_withdrawn = Decimal(str(partner.total_withdrawn or 0)) + amount
                
                # Update payout status
                payout.status = "completed"
                payout.processed_by = admin_id
                payout.processed_at = datetime.utcnow()
                if comment:
                    payout.admin_comment = comment
            
            logger.info(
                f"Payout approved: id={payout_id}, partner={payout.partner_id}, "
                f"amount={payout.amount_gton} GTON, admin={admin_id}"
            )
            
            return PayoutResult(
                success=True,
                payout_id=payout_id,
                amount_gton=payout.amount_gton,
                amount_fiat=payout.amount_fiat
            )
            
        except Exception as e:
            logger.error(f"Error approving payout: {e}")
            return PayoutResult(success=False, error=str(e))
    
    async def reject_payout(
        self,
        payout_id: int,
        admin_id: int,
        reason: str
    ) -> PayoutResult:
        """
        Reject a payout request and unfreeze funds.
        
        Args:
            payout_id: Payout request ID
            admin_id: Admin user ID who rejects
            reason: Rejection reason
        """
        try:
            async with get_db() as session:
                # Get payout
                result = await session.execute(
                    select(Payout).where(Payout.id == payout_id)
                )
                payout = result.scalar_one_or_none()
                
                if not payout:
                    return PayoutResult(success=False, error="Заявка не найдена")
                
                if payout.status != "pending":
                    return PayoutResult(success=False, error=f"Заявка уже обработана: {payout.status}")
                
                # Get partner and unfreeze
                result = await session.execute(
                    select(Partner).where(Partner.id == payout.partner_id)
                )
                partner = result.scalar_one_or_none()
                
                if partner:
                    amount = Decimal(str(payout.amount_gton))
                    partner.frozen_balance = Decimal(str(partner.frozen_balance or 0)) - amount
                
                # Update payout status
                payout.status = "rejected"
                payout.processed_by = admin_id
                payout.processed_at = datetime.utcnow()
                payout.rejection_reason = reason
            
            logger.info(
                f"Payout rejected: id={payout_id}, partner={payout.partner_id}, "
                f"reason={reason}, admin={admin_id}"
            )
            
            return PayoutResult(
                success=True,
                payout_id=payout_id,
                amount_gton=payout.amount_gton
            )
            
        except Exception as e:
            logger.error(f"Error rejecting payout: {e}")
            return PayoutResult(success=False, error=str(e))
    
    async def cancel_payout(self, payout_id: int, user_id: int) -> PayoutResult:
        """
        Cancel a pending payout request by the partner.
        
        Args:
            payout_id: Payout request ID
            user_id: User ID (partner's user)
        """
        try:
            async with get_db() as session:
                # Get payout with partner check
                result = await session.execute(
                    select(Payout, Partner).join(
                        Partner, Payout.partner_id == Partner.id
                    ).where(
                        Payout.id == payout_id,
                        Partner.user_id == user_id
                    )
                )
                row = result.one_or_none()
                
                if not row:
                    return PayoutResult(success=False, error="Заявка не найдена")
                
                payout, partner = row
                
                if payout.status != "pending":
                    return PayoutResult(success=False, error="Заявку нельзя отменить")
                
                # Unfreeze amount
                amount = Decimal(str(payout.amount_gton))
                partner.frozen_balance = Decimal(str(partner.frozen_balance or 0)) - amount
                
                # Update status
                payout.status = "cancelled"
                payout.updated_at = datetime.utcnow()
            
            logger.info(f"Payout cancelled by user: id={payout_id}, user={user_id}")
            
            return PayoutResult(success=True, payout_id=payout_id)
            
        except Exception as e:
            logger.error(f"Error cancelling payout: {e}")
            return PayoutResult(success=False, error=str(e))
    
    async def get_pending_payouts(self, limit: int = 50) -> list:
        """Get all pending payout requests"""
        async with get_db() as session:
            result = await session.execute(
                select(Payout, Partner, User).join(
                    Partner, Payout.partner_id == Partner.id
                ).join(
                    User, Partner.user_id == User.id
                ).where(
                    Payout.status == "pending"
                ).order_by(Payout.created_at).limit(limit)
            )
            return result.all()
    
    async def get_partner_payouts(self, partner_id: int, limit: int = 20) -> list:
        """Get partner's payout history"""
        async with get_db() as session:
            result = await session.execute(
                select(Payout).where(
                    Payout.partner_id == partner_id
                ).order_by(Payout.created_at.desc()).limit(limit)
            )
            return result.scalars().all()


# Global instance
payout_service = PayoutService()
