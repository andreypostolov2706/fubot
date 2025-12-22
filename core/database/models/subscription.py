"""
Subscription Model
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base


class Subscription(Base):
    """Subscription history"""
    __tablename__ = "subscriptions"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    service_id: Mapped[str] = Column(
        String(100), ForeignKey("services.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    
    # === Plan ===
    plan: Mapped[str] = Column(String(50), nullable=False)
    # basic, premium, enterprise, etc.
    
    # === Period ===
    started_at: Mapped[datetime] = Column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = Column(DateTime, nullable=False, index=True)
    
    # === Payment ===
    price: Mapped[int] = Column(Integer, nullable=False)  # In tokens
    transaction_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("transactions.id"), nullable=True
    )
    
    # === Status ===
    status: Mapped[str] = Column(String(20), default="active", index=True)
    # active, expired, cancelled, refunded
    
    # === Auto-renewal ===
    auto_renew: Mapped[bool] = Column(Boolean, default=False)
    renewal_reminded: Mapped[bool] = Column(Boolean, default=False)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    cancelled_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Relationships ===
    user = relationship("User")
    service = relationship("Service")
    transaction = relationship("Transaction")
    
    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, service_id={self.service_id}, plan={self.plan})>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == "active" and self.expires_at > datetime.utcnow()
    
    @property
    def days_left(self) -> int:
        """Get days left until expiration"""
        if self.expires_at <= datetime.utcnow():
            return 0
        delta = self.expires_at - datetime.utcnow()
        return delta.days
