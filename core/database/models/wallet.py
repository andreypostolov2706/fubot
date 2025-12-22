"""
Wallet Model

Stores user GTON balance.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    UniqueConstraint, Numeric
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base

if TYPE_CHECKING:
    from .user import User


class Wallet(Base):
    """
    User wallet.
    Main currency - GTON (6 decimal places).
    """
    __tablename__ = "wallets"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    
    # === Type ===
    wallet_type: Mapped[str] = Column(String(20), nullable=False, default="main")
    # main   - main wallet (GTON)
    # bonus  - bonus GTON (expire, cannot withdraw)
    
    # === Balance (GTON with 6 decimal places) ===
    balance: Mapped[Decimal] = Column(Numeric(18, 6), default=Decimal("0"))
    
    # === Frozen (for withdrawal) ===
    frozen: Mapped[Decimal] = Column(Numeric(18, 6), default=Decimal("0"))
    
    # === Daily Limits ===
    daily_limit: Mapped[Optional[Decimal]] = Column(Numeric(18, 6), nullable=True)
    daily_spent: Mapped[Decimal] = Column(Numeric(18, 6), default=Decimal("0"))
    daily_reset_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Bonus Expiration ===
    expires_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    
    # === Relationships ===
    user: Mapped["User"] = relationship("User", back_populates="wallets")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'wallet_type', name='uq_user_wallet_type'),
    )
    
    def __repr__(self) -> str:
        return f"<Wallet(id={self.id}, user_id={self.user_id}, type={self.wallet_type}, balance={self.balance})>"
    
    @property
    def available_balance(self) -> Decimal:
        """Get available balance (excluding frozen)"""
        return max(Decimal("0"), Decimal(str(self.balance)) - Decimal(str(self.frozen)))
    
    def can_spend(self, amount: Decimal) -> bool:
        """Check if can spend amount"""
        return self.available_balance >= Decimal(str(amount))
