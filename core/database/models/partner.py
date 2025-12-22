"""
Partner Model
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Numeric, Text, Boolean
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base

if TYPE_CHECKING:
    from .user import User
    from .referral import Referral
    from .payout import Payout


class Partner(Base):
    """Partner program"""
    __tablename__ = "partners"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True, nullable=False, index=True
    )
    
    # === Referral Code ===
    referral_code: Mapped[str] = Column(
        String(50), unique=True, nullable=False, index=True
    )
    
    # === Commission Rates (%) ===
    level1_percent: Mapped[Decimal] = Column(Numeric(5, 2), default=20.0)
    level2_percent: Mapped[Decimal] = Column(Numeric(5, 2), default=0.0)
    level3_percent: Mapped[Decimal] = Column(Numeric(5, 2), default=0.0)
    
    # === Balance (in GTON) ===
    balance: Mapped[Decimal] = Column(Numeric(18, 6), default=0)  # Available GTON
    total_earned: Mapped[Decimal] = Column(Numeric(18, 6), default=0)  # Total earned GTON
    total_withdrawn: Mapped[Decimal] = Column(Numeric(18, 6), default=0)  # Total withdrawn GTON
    frozen_balance: Mapped[Decimal] = Column(Numeric(18, 6), default=0)  # Frozen for pending payouts
    
    # === Statistics ===
    total_referrals: Mapped[int] = Column(Integer, default=0)
    active_referrals: Mapped[int] = Column(Integer, default=0)
    
    # === Status ===
    status: Mapped[str] = Column(String(20), default="pending", index=True)
    # pending  - application pending
    # active   - active partner
    # blocked  - blocked
    
    # === Application ===
    application_text: Mapped[Optional[str]] = Column(Text, nullable=True)
    applied_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    
    # === Approval ===
    approved_by: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    
    # === Relationships ===
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="partner",
        foreign_keys=[user_id]
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User", 
        foreign_keys=[approved_by]
    )
    referrals: Mapped[List["Referral"]] = relationship(
        "Referral", 
        back_populates="partner",
        cascade="all, delete-orphan"
    )
    payouts: Mapped[List["Payout"]] = relationship(
        "Payout", 
        back_populates="partner",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Partner(id={self.id}, user_id={self.user_id}, code={self.referral_code})>"
    
    @property
    def is_active(self) -> bool:
        """Check if partner is active"""
        return self.status == "active"
    
    @property
    def available_balance(self) -> Decimal:
        """Get available balance for withdrawal (excluding frozen)"""
        return Decimal(str(self.balance)) - Decimal(str(self.frozen_balance or 0))
