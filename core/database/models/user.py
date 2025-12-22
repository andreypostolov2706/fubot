"""
User Model
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, 
    DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base

if TYPE_CHECKING:
    from .wallet import Wallet
    from .partner import Partner
    from .referral import Referral


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # === Platform IDs ===
    telegram_id: Mapped[Optional[int]] = Column(
        BigInteger, unique=True, index=True, nullable=True
    )
    telegram_username: Mapped[Optional[str]] = Column(String(255), nullable=True)
    
    # Future platforms
    # discord_id = Column(BigInteger, unique=True, index=True, nullable=True)
    # whatsapp_phone = Column(String(20), unique=True, index=True, nullable=True)
    
    # === Profile ===
    first_name: Mapped[Optional[str]] = Column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = Column(String(255), nullable=True)
    language: Mapped[str] = Column(String(10), default="ru")
    timezone: Mapped[str] = Column(String(50), default="Europe/Moscow")
    
    # === System Role ===
    role: Mapped[str] = Column(String(20), default="user", index=True)
    # user, admin, superadmin
    
    # === Referral System ===
    referrer_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("users.id"), index=True, nullable=True
    )
    referral_code: Mapped[Optional[str]] = Column(
        String(20), unique=True, index=True, nullable=True
    )
    
    # === Status ===
    is_active: Mapped[bool] = Column(Boolean, default=True)
    is_blocked: Mapped[bool] = Column(Boolean, default=False, index=True)
    block_type: Mapped[Optional[str]] = Column(String(20), nullable=True)
    block_reason: Mapped[Optional[str]] = Column(String(500), nullable=True)
    block_expires_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    blocked_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    blocked_by: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    
    # === Moderation ===
    warnings_count: Mapped[int] = Column(Integer, default=0)
    last_warning_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Onboarding ===
    onboarding_completed: Mapped[bool] = Column(Boolean, default=False)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    last_activity_at: Mapped[Optional[datetime]] = Column(
        DateTime, index=True, nullable=True
    )
    
    # === Relationships ===
    wallets: Mapped[List["Wallet"]] = relationship(
        "Wallet", back_populates="user", cascade="all, delete-orphan"
    )
    partner: Mapped[Optional["Partner"]] = relationship(
        "Partner", 
        back_populates="user", 
        uselist=False,
        foreign_keys="Partner.user_id"
    )
    referrals_made: Mapped[List["Referral"]] = relationship(
        "Referral",
        back_populates="referrer",
        foreign_keys="Referral.referrer_id"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, name={self.first_name})>"
    
    @property
    def display_name(self) -> str:
        """Get display name"""
        if self.first_name:
            return self.first_name
        if self.telegram_username:
            return f"@{self.telegram_username}"
        return f"User #{self.id}"
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else self.display_name
