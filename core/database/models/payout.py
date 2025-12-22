"""
Payout Model — Заявки на вывод средств

Суммы хранятся в GTON с точностью Decimal(18, 6).
При выводе конвертируются в фиат по текущему курсу.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Numeric, Text, JSON
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base

if TYPE_CHECKING:
    from .partner import Partner
    from .user import User


class Payout(Base):
    """Payout requests — заявки на вывод в GTON"""
    __tablename__ = "payouts"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    partner_id: Mapped[int] = Column(
        Integer, ForeignKey("partners.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    
    # === Amount (GTON) ===
    amount_gton: Mapped[Decimal] = Column(Numeric(18, 6), nullable=False)  # Requested GTON
    fee_gton: Mapped[Decimal] = Column(Numeric(18, 6), default=0)  # Fee in GTON
    
    # === Fiat equivalent (at request time) ===
    amount_fiat: Mapped[Decimal] = Column(Numeric(12, 2), nullable=False)  # RUB equivalent
    currency: Mapped[str] = Column(String(3), default="RUB")  # Fiat currency
    gton_rate: Mapped[Decimal] = Column(Numeric(12, 4), nullable=False)  # GTON/RUB rate at request
    
    # === Method ===
    method: Mapped[str] = Column(String(30), nullable=False)
    # card, sbp, yoomoney, crypto
    details: Mapped[dict] = Column(JSON, nullable=False)
    # {"card": "4276...", "bank": "Sber"}
    
    # === Status ===
    status: Mapped[str] = Column(String(20), default="pending", index=True)
    # pending    - waiting
    # processing - in progress
    # completed  - done
    # rejected   - rejected
    # cancelled  - cancelled by user
    
    # === Processing ===
    processed_by: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    processed_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # === Comments ===
    user_comment: Mapped[Optional[str]] = Column(Text, nullable=True)
    admin_comment: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    
    # === Relationships ===
    partner: Mapped["Partner"] = relationship("Partner", back_populates="payouts")
    processor: Mapped[Optional["User"]] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<Payout(id={self.id}, partner_id={self.partner_id}, amount={self.amount}, status={self.status})>"
