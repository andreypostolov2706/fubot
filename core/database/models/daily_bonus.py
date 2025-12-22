"""
Daily Bonus Models
"""
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey, Date
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base


class DailyBonus(Base):
    """User daily bonus data"""
    __tablename__ = "daily_bonuses"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True, nullable=False, index=True
    )
    
    # === Streak ===
    current_streak: Mapped[int] = Column(Integer, default=0)
    max_streak: Mapped[int] = Column(Integer, default=0)
    
    # === Last Claim ===
    last_claim_date: Mapped[Optional[date]] = Column(Date, index=True, nullable=True)
    last_claim_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Statistics ===
    total_claims: Mapped[int] = Column(Integer, default=0)
    total_tokens: Mapped[int] = Column(Integer, default=0)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    
    # === Relationships ===
    user = relationship("User")
    history = relationship(
        "DailyBonusHistory", 
        back_populates="daily_bonus",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<DailyBonus(user_id={self.user_id}, streak={self.current_streak})>"


class DailyBonusHistory(Base):
    """Daily bonus claim history"""
    __tablename__ = "daily_bonus_history"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    daily_bonus_id: Mapped[int] = Column(
        Integer, ForeignKey("daily_bonuses.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # === Bonus ===
    day_number: Mapped[int] = Column(Integer, nullable=False)
    # Day in cycle (1-7)
    tokens: Mapped[int] = Column(Integer, nullable=False)
    streak: Mapped[int] = Column(Integer, nullable=False)
    # Streak at claim time
    
    # === Relation ===
    transaction_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("transactions.id"), nullable=True
    )
    
    # === Timestamp ===
    claimed_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    # === Relationships ===
    user = relationship("User")
    daily_bonus: Mapped["DailyBonus"] = relationship(
        "DailyBonus", back_populates="history"
    )
    transaction = relationship("Transaction")
    
    def __repr__(self) -> str:
        return f"<DailyBonusHistory(id={self.id}, user_id={self.user_id}, day={self.day_number}, tokens={self.tokens})>"
