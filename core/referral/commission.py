"""
Referral Commission Service

Начисление комиссий партнёрам при списании GTON у рефералов.

Логика:
1. При deduct_balance проверяем, есть ли у пользователя реферер
2. Если есть — начисляем комиссию рефереру (level 1)
3. Если реферер — партнёр, начисляем ему повышенную комиссию
4. Обновляем статистику в Referral и Partner
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

from loguru import logger

from core.database import get_db


@dataclass
class CommissionResult:
    """Результат начисления комиссии"""
    success: bool
    commissions: List[dict] = None  # [{user_id, amount, level, is_partner}]
    error: Optional[str] = None


class ReferralCommissionService:
    """Сервис начисления реферальных комиссий"""
    
    # Дефолтные проценты комиссии
    DEFAULT_LEVEL1_PERCENT = Decimal("10")  # 10% для обычных рефереров
    DEFAULT_PARTNER_LEVEL1_PERCENT = Decimal("20")  # 20% для партнёров
    
    async def get_commission_settings(self) -> dict:
        """Получить настройки комиссий из Settings Manager (с кэшированием)"""
        from core.settings import settings as settings_manager
        
        return {
            "enabled": await settings_manager.get_bool("referral.commission_enabled", True),
            "level1_percent": await settings_manager.get_decimal(
                "referral.level1_percent", 
                self.DEFAULT_LEVEL1_PERCENT
            ),
            "partner_level1_percent": await settings_manager.get_decimal(
                "referral.partner_level1_percent", 
                self.DEFAULT_PARTNER_LEVEL1_PERCENT
            ),
        }
    
    async def process_commission(
        self,
        user_id: int,
        amount: Decimal,
        service_id: str = "",
        action: str = "",
        transaction_id: Optional[int] = None
    ) -> CommissionResult:
        """
        Обработать комиссию при списании GTON.
        
        Args:
            user_id: ID пользователя, у которого списали GTON
            amount: Сумма списания в GTON
            service_id: ID сервиса
            action: Действие
            transaction_id: ID транзакции списания
            
        Returns:
            CommissionResult с информацией о начисленных комиссиях
        """
        from core.database.models import Referral, Partner, Transaction, Wallet
        from sqlalchemy import select
        
        settings = await self.get_commission_settings()
        
        if not settings["enabled"]:
            return CommissionResult(success=True, commissions=[])
        
        commissions = []
        
        try:
            async with get_db() as session:
                # Найти реферальную связь (кто привёл этого пользователя)
                result = await session.execute(
                    select(Referral).where(
                        Referral.referred_id == user_id,
                        Referral.is_active == True
                    )
                )
                referral = result.scalar_one_or_none()
                
                if not referral:
                    # Пользователь не реферал — комиссий нет
                    return CommissionResult(success=True, commissions=[])
                
                referrer_id = referral.referrer_id
                partner_id = referral.partner_id
                
                # Определить процент комиссии
                if partner_id:
                    # Есть партнёр — проверить его настройки
                    result = await session.execute(
                        select(Partner).where(
                            Partner.id == partner_id,
                            Partner.status == "active"
                        )
                    )
                    partner = result.scalar_one_or_none()
                    
                    if partner:
                        # Использовать процент партнёра
                        commission_percent = Decimal(str(partner.level1_percent))
                        is_partner = True
                    else:
                        # Партнёр неактивен — использовать дефолт
                        commission_percent = settings["level1_percent"]
                        is_partner = False
                        partner = None
                else:
                    # Обычный реферер
                    commission_percent = settings["level1_percent"]
                    is_partner = False
                    partner = None
                
                # Рассчитать комиссию
                commission_amount = (amount * commission_percent / Decimal("100")).quantize(
                    Decimal("0.000001")
                )
                
                if commission_amount <= 0:
                    return CommissionResult(success=True, commissions=[])
                
                # Начислить комиссию
                # Для партнёра — на Partner.balance (можно вывести)
                # Для обычного реферера — на Wallet (можно потратить)
                
                if partner:
                    # === ПАРТНЁР: начисляем на Partner.balance ===
                    balance_before = Decimal(str(partner.balance or 0))
                    partner.balance = balance_before + commission_amount
                    partner.total_earned = Decimal(str(partner.total_earned or 0)) + commission_amount
                    
                    # Создать транзакцию для истории (без привязки к wallet)
                    commission_tx = Transaction(
                        user_id=referrer_id,
                        wallet_id=None,  # Нет привязки к кошельку
                        type="partner_commission",
                        amount=commission_amount,
                        direction="credit",
                        balance_before=balance_before,
                        balance_after=partner.balance,
                        source="referral",
                        action="partner_commission",
                        reference_id=str(transaction_id) if transaction_id else None,
                        description=f"Партнёрская комиссия {commission_percent}% от {amount} GTON",
                        status="completed",
                        completed_at=datetime.utcnow()
                    )
                    session.add(commission_tx)
                else:
                    # === ОБЫЧНЫЙ РЕФЕРЕР: начисляем на Wallet ===
                    result = await session.execute(
                        select(Wallet).where(
                            Wallet.user_id == referrer_id,
                            Wallet.wallet_type == "main"
                        ).with_for_update()
                    )
                    referrer_wallet = result.scalar_one_or_none()
                    
                    if not referrer_wallet:
                        referrer_wallet = Wallet(
                            user_id=referrer_id,
                            wallet_type="main",
                            balance=Decimal("0")
                        )
                        session.add(referrer_wallet)
                        await session.flush()
                    
                    # Начислить на баланс
                    balance_before = Decimal(str(referrer_wallet.balance))
                    referrer_wallet.balance = balance_before + commission_amount
                    
                    # Создать транзакцию комиссии
                    commission_tx = Transaction(
                        user_id=referrer_id,
                        wallet_id=referrer_wallet.id,
                        type="referral_commission",
                        amount=commission_amount,
                        direction="credit",
                        balance_before=balance_before,
                        balance_after=referrer_wallet.balance,
                        source="referral",
                        action="commission",
                        reference_id=str(transaction_id) if transaction_id else None,
                        description=f"Реферальная комиссия {commission_percent}% от {amount} GTON",
                        status="completed",
                        completed_at=datetime.utcnow()
                    )
                    session.add(commission_tx)
                
                # Обновить статистику реферала
                referral.total_payments = Decimal(str(referral.total_payments or 0)) + amount
                referral.total_commission = Decimal(str(referral.total_commission or 0)) + commission_amount
                referral.last_payment_at = datetime.utcnow()
                if not referral.first_payment_at:
                    referral.first_payment_at = datetime.utcnow()
                
                await session.flush()
                
                # Сохранить в историю комиссий
                from core.database.models import Commission
                commission_record = Commission(
                    referrer_id=referrer_id,
                    referred_id=user_id,
                    referral_id=referral.id,
                    source_amount=amount,
                    commission_amount=commission_amount,
                    commission_percent=commission_percent,
                    level=1,
                    service_id=service_id,
                    action=action,
                    source_transaction_id=transaction_id,
                    commission_transaction_id=commission_tx.id
                )
                session.add(commission_record)
                await session.flush()
                
                commissions.append({
                    "user_id": referrer_id,
                    "amount": commission_amount,
                    "percent": commission_percent,
                    "level": 1,
                    "is_partner": is_partner,
                    "transaction_id": commission_tx.id,
                    "commission_id": commission_record.id
                })
                
                logger.info(
                    f"Referral commission: referrer={referrer_id}, "
                    f"amount={commission_amount} GTON ({commission_percent}%), "
                    f"from user={user_id}, partner={is_partner}"
                )
                
                # Send notification to referrer
                try:
                    from core.referral.notifications import notify_commission_earned
                    await notify_commission_earned(
                        referrer_id=referrer_id,
                        commission_amount=commission_amount,
                        commission_percent=commission_percent,
                        referred_user_id=user_id,
                        is_partner=is_partner
                    )
                except Exception as e:
                    logger.error(f"Failed to send commission notification: {e}")
                
                return CommissionResult(success=True, commissions=commissions)
                
        except Exception as e:
            logger.error(f"Failed to process referral commission: {e}")
            return CommissionResult(success=False, error=str(e))


# Singleton instance
commission_service = ReferralCommissionService()
