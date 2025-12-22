"""
Event Model (Analytics)
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    JSON, Index
)
from sqlalchemy.orm import Mapped

from core.database.base import Base


class Event(Base):
    """Analytics events"""
    __tablename__ = "events"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # === User ===
    user_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), 
        index=True, nullable=True
    )
    
    # === Event ===
    category: Mapped[str] = Column(String(50), nullable=False, index=True)
    # user, payment, service, referral, subscription
    
    action: Mapped[str] = Column(String(100), nullable=False, index=True)
    # user:registered, payment:completed, service:ai:message_sent
    
    # === Source ===
    service_id: Mapped[Optional[str]] = Column(String(100), index=True, nullable=True)
    
    # === Data ===
    label: Mapped[Optional[str]] = Column(String(255), nullable=True)
    value: Mapped[Optional[int]] = Column(Integer, nullable=True)
    properties: Mapped[Optional[dict]] = Column(JSON, nullable=True)
    
    # === Session ===
    session_id: Mapped[Optional[str]] = Column(String(100), index=True, nullable=True)
    
    # === Context ===
    platform: Mapped[Optional[str]] = Column(String(20), nullable=True)
    # telegram, discord, web
    
    # === Timestamp ===
    created_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    __table_args__ = (
        Index('idx_events_category_action', 'category', 'action'),
        Index('idx_events_user_date', 'user_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Event(id={self.id}, category={self.category}, action={self.action})>"
