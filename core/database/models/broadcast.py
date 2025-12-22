"""
Broadcast Model
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, JSON, Boolean, Float
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base


class Broadcast(Base):
    """Broadcasts (system and service)"""
    __tablename__ = "broadcasts"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # === Source ===
    source: Mapped[str] = Column(String(20), default="admin")
    # admin, service, trigger
    service_id: Mapped[Optional[str]] = Column(
        String(100), ForeignKey("services.id", ondelete="SET NULL"), 
        nullable=True
    )
    trigger_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("broadcast_triggers.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # === Content ===
    name: Mapped[Optional[str]] = Column(String(100), nullable=True)
    text: Mapped[str] = Column(Text, nullable=False)
    parse_mode: Mapped[str] = Column(String(10), default="HTML")
    
    # === Media ===
    media_type: Mapped[Optional[str]] = Column(String(20), nullable=True)
    # photo, video, document, voice, animation
    media_file_id: Mapped[Optional[str]] = Column(String(255), nullable=True)
    
    # === Buttons ===
    buttons: Mapped[Optional[list]] = Column(JSON, nullable=True)
    # [[{"text": "...", "url": "..."}], [{"text": "...", "callback_data": "..."}]]
    
    # === Target ===
    target: Mapped[str] = Column(String(50), default="all")
    # all, active_7d, active_30d, with_balance, with_subscription, new_week, inactive_30d
    filters: Mapped[Optional[dict]] = Column(JSON, nullable=True)
    
    # === A/B Testing ===
    is_ab_test: Mapped[bool] = Column(Boolean, default=False)
    ab_variant: Mapped[Optional[str]] = Column(String(1), nullable=True)  # A or B
    ab_parent_id: Mapped[Optional[int]] = Column(Integer, ForeignKey("broadcasts.id"), nullable=True)
    ab_split_percent: Mapped[int] = Column(Integer, default=50)  # % for variant A
    
    # === Scheduling ===
    scheduled_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Status ===
    status: Mapped[str] = Column(String(20), default="draft", index=True)
    # draft, scheduled, sending, paused, completed, cancelled
    
    # === Progress ===
    total_recipients: Mapped[int] = Column(Integer, default=0)
    sent_count: Mapped[int] = Column(Integer, default=0)
    delivered_count: Mapped[int] = Column(Integer, default=0)
    failed_count: Mapped[int] = Column(Integer, default=0)
    
    # === Speed ===
    send_rate: Mapped[int] = Column(Integer, default=25)
    # Messages per second (Telegram limit ~30/sec)
    
    # === Timestamps ===
    created_by: Mapped[int] = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Relationships ===
    creator = relationship("User", foreign_keys=[created_by])
    service = relationship("Service")
    trigger = relationship("BroadcastTrigger", back_populates="broadcasts")
    ab_parent = relationship("Broadcast", remote_side=[id])
    
    def __repr__(self) -> str:
        return f"<Broadcast(id={self.id}, status={self.status}, target={self.target})>"
    
    @property
    def progress_percent(self) -> float:
        """Get progress percentage"""
        if self.total_recipients == 0:
            return 0
        return (self.sent_count / self.total_recipients) * 100


class BroadcastTrigger(Base):
    """Automatic broadcast triggers"""
    __tablename__ = "broadcast_triggers"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # === Basic ===
    name: Mapped[str] = Column(String(100), nullable=False)
    trigger_type: Mapped[str] = Column(String(50), nullable=False)
    # low_balance, subscription_expiring, subscription_expired, 
    # inactive, welcome, after_deposit
    
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    # === Conditions (JSON) ===
    conditions: Mapped[dict] = Column(JSON, default={})
    # Структура зависит от типа триггера:
    # low_balance: {"balance_less_than": 100, "check_interval_hours": 24}
    # subscription_expiring: {"days_before_expiry": 3, "subscription_types": ["premium"]}
    # subscription_expired: {"hours_after_expiry": 1, "repeat_after_days": 7}
    # inactive: {"inactive_days": 7, "exclude_new_users_days": 3}
    # welcome: {"hours_after_registration": 24, "only_if_inactive": true}
    # after_deposit: {"min_amount": 0, "delay_minutes": 5, "first_deposit_only": false}
    
    # === Timing ===
    send_start_hour: Mapped[int] = Column(Integer, default=9)  # Начало отправки (час)
    send_end_hour: Mapped[int] = Column(Integer, default=21)   # Конец отправки (час)
    delay_minutes: Mapped[int] = Column(Integer, default=0)    # Задержка перед отправкой
    
    # === Frequency ===
    repeat_interval_days: Mapped[int] = Column(Integer, default=0)
    # 0 = one-time, >0 = repeat every N days
    max_sends_per_user: Mapped[int] = Column(Integer, default=1)
    # 0 = unlimited
    cooldown_hours: Mapped[int] = Column(Integer, default=24)
    # Минимум часов между отправками одному пользователю
    
    # === Content ===
    text: Mapped[str] = Column(Text, nullable=False)
    parse_mode: Mapped[str] = Column(String(10), default="HTML")
    media_type: Mapped[Optional[str]] = Column(String(20), nullable=True)
    media_file_id: Mapped[Optional[str]] = Column(String(255), nullable=True)
    buttons: Mapped[Optional[list]] = Column(JSON, nullable=True)
    
    # === Stats ===
    total_sent: Mapped[int] = Column(Integer, default=0)
    total_delivered: Mapped[int] = Column(Integer, default=0)
    total_clicked: Mapped[int] = Column(Integer, default=0)
    
    # === Timestamps ===
    created_by: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Relationships ===
    creator = relationship("User")
    broadcasts = relationship("Broadcast", back_populates="trigger")
    
    def __repr__(self) -> str:
        return f"<BroadcastTrigger(id={self.id}, type={self.trigger_type}, active={self.is_active})>"


class BroadcastRecipient(Base):
    """Track broadcast recipients for deduplication and analytics"""
    __tablename__ = "broadcast_recipients"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    broadcast_id: Mapped[int] = Column(Integer, ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # === Status ===
    status: Mapped[str] = Column(String(20), default="pending")
    # pending, sent, delivered, failed, clicked
    
    # === Tracking ===
    sent_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    clicked_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = Column(String(255), nullable=True)
    
    # === A/B ===
    ab_variant: Mapped[Optional[str]] = Column(String(1), nullable=True)


class TriggerSendLog(Base):
    """Track trigger sends per user to prevent spam"""
    __tablename__ = "trigger_send_logs"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    trigger_id: Mapped[int] = Column(Integer, ForeignKey("broadcast_triggers.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    send_count: Mapped[int] = Column(Integer, default=1)
    first_sent_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    last_sent_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
