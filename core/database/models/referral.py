"""
Referral Model
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey, 
    Numeric, Boolean, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base

if TYPE_CHECKING:
    from .user import User
    from .partner import Partner


class Referral(Base):
    """Referral relationship: referrer -> referred"""
    __tablename__ = "referrals"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # === Relationships ===
    referrer_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    referred_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    partner_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("partners.id", ondelete="SET NULL"), 
        index=True, nullable=True
    )
    
    # === Level ===
    level: Mapped[int] = Column(Integer, default=1)
    # 1 = direct referral
    # 2 = referral of referral
    # 3 = third level
    
    # === Statistics ===
    total_payments: Mapped[Decimal] = Column(Numeric(12, 2), default=0)
    total_commission: Mapped[Decimal] = Column(Numeric(12, 2), default=0)
    
    # === Status ===
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, index=True
    )
    first_payment_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    last_payment_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Relationships ===
    referrer: Mapped["User"] = relationship(
        "User", 
        back_populates="referrals_made",
        foreign_keys=[referrer_id]
    )
    referred: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[referred_id]
    )
    partner: Mapped[Optional["Partner"]] = relationship(
        "Partner", 
        back_populates="referrals"
    )
    
    __table_args__ = (
        UniqueConstraint('referrer_id', 'referred_id', name='uq_referral_pair'),
        Index('idx_referral_referrer_level', 'referrer_id', 'level'),
    )
    
    def __repr__(self) -> str:
        return f"<Referral(id={self.id}, referrer={self.referrer_id}, referred={self.referred_id}, level={self.level})>"
