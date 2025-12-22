"""
Notification Models
"""
from datetime import datetime, time
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, JSON, Boolean, Time
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base


class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    
    # === Type ===
    type: Mapped[str] = Column(String(30), nullable=False, index=True)
    # push      - messenger
    # email     - email
    # internal  - internal inbox
    
    # === Category ===
    category: Mapped[str] = Column(String(50), nullable=False, index=True)
    # system, payment, subscription, balance, referral, promo, reminder, service
    
    # === Content ===
    title: Mapped[Optional[str]] = Column(String(255), nullable=True)
    text: Mapped[str] = Column(Text, nullable=False)
    
    # === Action ===
    action_type: Mapped[Optional[str]] = Column(String(30), nullable=True)
    # callback, url, deeplink
    action_data: Mapped[Optional[str]] = Column(String(500), nullable=True)
    action_text: Mapped[Optional[str]] = Column(String(100), nullable=True)
    
    # === Scheduling ===
    scheduled_at: Mapped[Optional[datetime]] = Column(DateTime, index=True, nullable=True)
    
    # === Status ===
    status: Mapped[str] = Column(String(20), default="pending", index=True)
    # pending, sent, delivered, read, failed, cancelled
    
    # === Result ===
    sent_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    error: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # === Source ===
    source: Mapped[str] = Column(String(30), default="system")
    # system, service, trigger
    service_id: Mapped[Optional[str]] = Column(String(100), nullable=True)
    trigger_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("notification_triggers.id"), nullable=True
    )
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    
    # === Relationships ===
    user = relationship("User")
    trigger = relationship("NotificationTrigger")
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, status={self.status})>"


class NotificationTrigger(Base):
    """Automatic notification triggers"""
    __tablename__ = "notification_triggers"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # === Name ===
    name: Mapped[str] = Column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # === Trigger Type ===
    trigger_type: Mapped[str] = Column(String(50), nullable=False)
    # low_balance, zero_balance, subscription_expiring, subscription_expired,
    # inactive_days, first_payment, registration, referral_registered,
    # referral_payment, daily_bonus_available
    
    # === Conditions ===
    conditions: Mapped[dict] = Column(JSON, default=dict)
    # {"threshold": 10, "days_before": 3, "inactive_days": 7}
    
    # === Notification Template ===
    notification_type: Mapped[str] = Column(String(30), default="push")
    # push, email, both
    title_template: Mapped[Optional[str]] = Column(String(255), nullable=True)
    text_template: Mapped[str] = Column(Text, nullable=False)
    # Supports variables: {user_name}, {balance}, {days}, {amount}
    
    action_type: Mapped[Optional[str]] = Column(String(30), nullable=True)
    action_data: Mapped[Optional[str]] = Column(String(500), nullable=True)
    action_text: Mapped[Optional[str]] = Column(String(100), nullable=True)
    
    # === Limits ===
    cooldown_hours: Mapped[int] = Column(Integer, default=24)
    max_per_user: Mapped[Optional[int]] = Column(Integer, nullable=True)
    
    # === Status ===
    is_active: Mapped[bool] = Column(Boolean, default=True, index=True)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<NotificationTrigger(id={self.id}, name={self.name}, type={self.trigger_type})>"


class UserNotificationSettings(Base):
    """User notification settings"""
    __tablename__ = "user_notification_settings"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True, nullable=False
    )
    
    # === Email ===
    email: Mapped[Optional[str]] = Column(String(255), nullable=True)
    email_verified: Mapped[bool] = Column(Boolean, default=False)
    email_verification_code: Mapped[Optional[str]] = Column(String(50), nullable=True)
    email_verification_expires: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Channels ===
    push_enabled: Mapped[bool] = Column(Boolean, default=True)
    email_enabled: Mapped[bool] = Column(Boolean, default=False)
    
    # === Categories ===
    receive_system: Mapped[bool] = Column(Boolean, default=True)
    receive_payment: Mapped[bool] = Column(Boolean, default=True)
    receive_subscription: Mapped[bool] = Column(Boolean, default=True)
    receive_balance: Mapped[bool] = Column(Boolean, default=True)
    receive_referral: Mapped[bool] = Column(Boolean, default=True)
    receive_promo: Mapped[bool] = Column(Boolean, default=True)
    receive_reminder: Mapped[bool] = Column(Boolean, default=True)
    receive_service: Mapped[bool] = Column(Boolean, default=True)
    
    # === Quiet Hours ===
    quiet_hours_enabled: Mapped[bool] = Column(Boolean, default=False)
    quiet_hours_start: Mapped[Optional[time]] = Column(Time, nullable=True)
    quiet_hours_end: Mapped[Optional[time]] = Column(Time, nullable=True)
    
    # === Timestamps ===
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    
    # === Relationships ===
    user = relationship("User")
    
    def __repr__(self) -> str:
        return f"<UserNotificationSettings(user_id={self.user_id})>"
