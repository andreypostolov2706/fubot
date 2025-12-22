"""
Commission Model — История реферальных комиссий
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey, 
    Numeric, String, Index
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base

if TYPE_CHECKING:
    from .user import User
    from .referral import Referral
    from .transaction import Transaction


class Commission(Base):
    """Referral commission history"""
    __tablename__ = "commissions"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # === Участники ===
    referrer_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    referred_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    referral_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("referrals.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    
    # === Суммы ===
    source_amount: Mapped[Decimal] = Column(
        Numeric(18, 6), nullable=False
    )  # Сумма списания у реферала (GTON)
    
    commission_amount: Mapped[Decimal] = Column(
        Numeric(18, 6), nullable=False
    )  # Сумма комиссии (GTON)
    
    commission_percent: Mapped[Decimal] = Column(
        Numeric(5, 2), nullable=False
    )  # Процент комиссии
    
    # === Уровень ===
    level: Mapped[int] = Column(Integer, default=1)
    # 1 = прямой реферер
    # 2 = партнёр (второй уровень)
    
    # === Источник ===
    service_id: Mapped[Optional[str]] = Column(String(100), nullable=True)
    action: Mapped[Optional[str]] = Column(String(100), nullable=True)
    
    # === Связи с транзакциями ===
    source_transaction_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True
    )  # Транзакция списания
    
    commission_transaction_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True
    )  # Транзакция начисления комиссии
    
    # === Timestamp ===
    created_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    # === Relationships ===
    referrer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[referrer_id]
    )
    referred: Mapped["User"] = relationship(
        "User",
        foreign_keys=[referred_id]
    )
    referral: Mapped[Optional["Referral"]] = relationship(
        "Referral"
    )
    source_transaction: Mapped[Optional["Transaction"]] = relationship(
        "Transaction",
        foreign_keys=[source_transaction_id]
    )
    commission_transaction: Mapped[Optional["Transaction"]] = relationship(
        "Transaction",
        foreign_keys=[commission_transaction_id]
    )
    
    __table_args__ = (
        Index('idx_commission_referrer_date', 'referrer_id', 'created_at'),
        Index('idx_commission_referred_date', 'referred_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Commission(id={self.id}, referrer={self.referrer_id}, "
            f"amount={self.commission_amount}, level={self.level})>"
        )
