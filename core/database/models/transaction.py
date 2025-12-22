"""
Transaction Model
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Numeric, Text, JSON
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base


class Transaction(Base):
    """Transaction history"""
    __tablename__ = "transactions"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    wallet_id: Mapped[int] = Column(
        Integer, ForeignKey("wallets.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # === Transaction Type ===
    type: Mapped[str] = Column(String(30), nullable=False, index=True)
    # credit           - balance increase
    # debit            - balance decrease
    
    # === Amount (GTON with 6 decimal places) ===
    amount: Mapped[Decimal] = Column(Numeric(18, 6), nullable=False)
    direction: Mapped[str] = Column(String(10), nullable=False)  # "credit" or "debit"
    
    # === Balance ===
    balance_before: Mapped[Optional[Decimal]] = Column(Numeric(18, 6), nullable=True)
    balance_after: Mapped[Optional[Decimal]] = Column(Numeric(18, 6), nullable=True)
    
    # === Payment Info (for deposit) ===
    payment_method: Mapped[Optional[str]] = Column(String(30), nullable=True)
    payment_id: Mapped[Optional[str]] = Column(String(255), nullable=True)
    payment_amount: Mapped[Optional[Decimal]] = Column(Numeric(10, 2), nullable=True)
    payment_currency: Mapped[Optional[str]] = Column(String(3), nullable=True)
    exchange_rate: Mapped[Optional[Decimal]] = Column(Numeric(10, 4), nullable=True)
    
    # === Service Info (for usage) ===
    service_id: Mapped[Optional[str]] = Column(String(100), index=True, nullable=True)
    service_action: Mapped[Optional[str]] = Column(String(100), nullable=True)
    service_data: Mapped[Optional[dict]] = Column(JSON, nullable=True)
    
    # === Referral Info ===
    referral_user_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    referral_level: Mapped[Optional[int]] = Column(Integer, nullable=True)
    
    # === Source and Action ===
    source: Mapped[Optional[str]] = Column(String(50), nullable=True, index=True)
    # payment, referral, bonus, admin, service, promocode, daily_bonus
    
    action: Mapped[Optional[str]] = Column(String(50), nullable=True)
    # For service: specific action name
    
    # === Reference ===
    reference_id: Mapped[Optional[int]] = Column(Integer, nullable=True)
    # ID of related entity (payment_id, promocode_id, etc.)
    
    # === Description ===
    description: Mapped[Optional[str]] = Column(String(500), nullable=True)
    
    # === Status ===
    status: Mapped[str] = Column(String(20), default="completed", index=True)
    # pending, completed, failed, cancelled
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, index=True
    )
    completed_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Relationships ===
    user = relationship("User", foreign_keys=[user_id])
    wallet = relationship("Wallet")
    referral_user = relationship("User", foreign_keys=[referral_user_id])
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, type={self.type}, amount={self.amount}, direction={self.direction})>"
