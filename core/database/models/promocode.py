"""
PromoCode Models
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, Boolean, Index
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base


class PromoCode(Base):
    """Promocodes"""
    __tablename__ = "promocodes"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # === Code ===
    code: Mapped[str] = Column(String(50), unique=True, nullable=False, index=True)
    # Uppercase: "WELCOME50", "NEWYEAR2024"
    
    # === Description ===
    name: Mapped[Optional[str]] = Column(String(255), nullable=True)
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # === Reward Type ===
    reward_type: Mapped[str] = Column(String(30), nullable=False)
    # tokens       - bonus tokens
    # subscription - free subscription
    # discount     - deposit discount (%)
    
    # === Reward Value ===
    reward_value: Mapped[int] = Column(Integer, nullable=False)
    # For tokens: amount
    # For subscription: days
    # For discount: percent
    
    # === For Subscription ===
    subscription_service_id: Mapped[Optional[str]] = Column(String(100), nullable=True)
    subscription_plan: Mapped[Optional[str]] = Column(String(50), nullable=True)
    
    # === Limits ===
    max_activations: Mapped[Optional[int]] = Column(Integer, nullable=True)
    max_per_user: Mapped[int] = Column(Integer, default=1)
    current_activations: Mapped[int] = Column(Integer, default=0)
    
    # === Conditions ===
    min_deposit: Mapped[Optional[int]] = Column(Integer, nullable=True)
    min_balance: Mapped[Optional[int]] = Column(Integer, nullable=True)
    only_new_users: Mapped[bool] = Column(Boolean, default=False)
    only_first_deposit: Mapped[bool] = Column(Boolean, default=False)
    
    # === User Binding ===
    bound_user_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    # If set, only this user can activate
    
    # === Partner Binding ===
    partner_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("partners.id"), nullable=True
    )
    # If set, users who activate become referrals of this partner
    
    # === Validity Period ===
    starts_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Status ===
    is_active: Mapped[bool] = Column(Boolean, default=True, index=True)
    
    # === Creation ===
    created_by: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    
    # === Relationships ===
    creator = relationship("User", foreign_keys=[created_by])
    bound_user = relationship("User", foreign_keys=[bound_user_id])
    partner = relationship("Partner", foreign_keys=[partner_id])
    activations = relationship(
        "PromoCodeActivation", 
        back_populates="promocode",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<PromoCode(id={self.id}, code={self.code}, type={self.reward_type})>"
    
    @property
    def is_valid(self) -> bool:
        """Check if promocode is valid"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        
        if self.starts_at and now < self.starts_at:
            return False
        
        if self.expires_at and now > self.expires_at:
            return False
        
        if self.max_activations and self.current_activations >= self.max_activations:
            return False
        
        return True


class PromoCodeActivation(Base):
    """Promocode activation history"""
    __tablename__ = "promocode_activations"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    promocode_id: Mapped[int] = Column(
        Integer, ForeignKey("promocodes.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    
    # === Reward ===
    reward_type: Mapped[str] = Column(String(30), nullable=False)
    reward_value: Mapped[int] = Column(Integer, nullable=False)
    
    # === Relations ===
    transaction_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("transactions.id"), nullable=True
    )
    subscription_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("subscriptions.id"), nullable=True
    )
    
    # === Timestamp ===
    activated_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    # === Relationships ===
    promocode: Mapped["PromoCode"] = relationship(
        "PromoCode", back_populates="activations"
    )
    user = relationship("User")
    transaction = relationship("Transaction")
    subscription = relationship("Subscription")
    
    __table_args__ = (
        Index('idx_promo_user', 'promocode_id', 'user_id'),
    )
    
    def __repr__(self) -> str:
        return f"<PromoCodeActivation(id={self.id}, promocode_id={self.promocode_id}, user_id={self.user_id})>"
