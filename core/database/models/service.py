"""
Service Models
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, JSON, Boolean, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base

if TYPE_CHECKING:
    from .user import User


class Service(Base):
    """Installed services registry"""
    __tablename__ = "services"
    
    id: Mapped[str] = Column(String(100), primary_key=True)
    # e.g., "ai_psychologist"
    
    # === Info ===
    name: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    version: Mapped[Optional[str]] = Column(String(20), nullable=True)
    author: Mapped[Optional[str]] = Column(String(255), nullable=True)
    icon: Mapped[Optional[str]] = Column(String(10), nullable=True)  # Emoji
    
    # === Paths ===
    install_path: Mapped[Optional[str]] = Column(String(500), nullable=True)
    
    # === Status ===
    status: Mapped[str] = Column(String(20), default="active", index=True)
    # active, disabled, error, maintenance
    
    # === Configuration ===
    config: Mapped[dict] = Column(JSON, default=dict)
    
    # === Features ===
    features: Mapped[dict] = Column(JSON, default=dict)
    # {
    #   "subscriptions": true,
    #   "broadcasts": true,
    #   "partner_menu": false,
    #   "voice_messages": true
    # }
    
    # === Permissions ===
    permissions: Mapped[list] = Column(JSON, default=list)
    
    # === Menu Order ===
    menu_order: Mapped[int] = Column(Integer, default=0)
    
    # === Timestamps ===
    installed_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    
    # === Errors ===
    last_error: Mapped[Optional[str]] = Column(Text, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    error_count: Mapped[int] = Column(Integer, default=0)
    
    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name={self.name}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if service is active"""
        return self.status == "active"


class UserService(Base):
    """User data in service context"""
    __tablename__ = "user_services"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    service_id: Mapped[str] = Column(
        String(100), ForeignKey("services.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    
    # === Role in Service ===
    role: Mapped[str] = Column(String(30), default="user")
    # user, vip, moderator, admin
    
    # === Subscription ===
    subscription_plan: Mapped[Optional[str]] = Column(String(50), nullable=True)
    subscription_until: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    subscription_auto_renew: Mapped[bool] = Column(Boolean, default=False)
    
    # === User Settings ===
    settings: Mapped[dict] = Column(JSON, default=dict)
    
    # === FSM State ===
    state: Mapped[Optional[str]] = Column(String(100), nullable=True)
    state_data: Mapped[Optional[dict]] = Column(JSON, nullable=True)
    state_updated_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Statistics ===
    total_spent: Mapped[int] = Column(Integer, default=0)
    usage_count: Mapped[int] = Column(Integer, default=0)
    
    # === Status ===
    is_active: Mapped[bool] = Column(Boolean, default=True)
    is_blocked: Mapped[bool] = Column(Boolean, default=False)
    
    # === Timestamps ===
    first_use_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    last_use_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Relationships ===
    user: Mapped["User"] = relationship("User")
    service: Mapped["Service"] = relationship("Service")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'service_id', name='uq_user_service'),
    )
    
    def __repr__(self) -> str:
        return f"<UserService(user_id={self.user_id}, service_id={self.service_id})>"
