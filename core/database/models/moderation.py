"""
Moderation Models
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, Boolean, JSON
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base


class UserWarning(Base):
    """User warnings"""
    __tablename__ = "user_warnings"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    
    # === Reason ===
    reason: Mapped[str] = Column(String(100), nullable=False)
    # spam, abuse, fraud, terms_violation, other
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # === Issued By ===
    issued_by: Mapped[int] = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    
    # === Status ===
    is_active: Mapped[bool] = Column(Boolean, default=True)
    revoked_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    revoked_by: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    revoke_reason: Mapped[Optional[str]] = Column(String(255), nullable=True)
    
    # === Auto-ban ===
    resulted_in_ban: Mapped[bool] = Column(Boolean, default=False)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    # === Relationships ===
    user = relationship("User", foreign_keys=[user_id])
    issuer = relationship("User", foreign_keys=[issued_by])
    revoker = relationship("User", foreign_keys=[revoked_by])
    
    def __repr__(self) -> str:
        return f"<UserWarning(id={self.id}, user_id={self.user_id}, reason={self.reason})>"


class UserBan(Base):
    """User ban history"""
    __tablename__ = "user_bans"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    
    # === Type ===
    ban_type: Mapped[str] = Column(String(20), nullable=False)
    # permanent, temporary, warning
    
    # === Reason ===
    reason: Mapped[str] = Column(String(100), nullable=False)
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # === Duration (for temporary) ===
    duration_days: Mapped[Optional[int]] = Column(Integer, nullable=True)
    expires_at: Mapped[Optional[datetime]] = Column(DateTime, index=True, nullable=True)
    
    # === Banned By ===
    banned_by: Mapped[int] = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    
    # === Unban ===
    is_active: Mapped[bool] = Column(Boolean, default=True, index=True)
    unbanned_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    unbanned_by: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    unban_reason: Mapped[Optional[str]] = Column(String(255), nullable=True)
    
    # === Related Warnings ===
    warning_ids: Mapped[Optional[list]] = Column(JSON, nullable=True)
    # [1, 2, 3] - if auto-ban from warnings
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    # === Relationships ===
    user = relationship("User", foreign_keys=[user_id])
    banner = relationship("User", foreign_keys=[banned_by])
    unbanner = relationship("User", foreign_keys=[unbanned_by])
    
    def __repr__(self) -> str:
        return f"<UserBan(id={self.id}, user_id={self.user_id}, type={self.ban_type})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if temporary ban is expired"""
        if self.ban_type != "temporary":
            return False
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class ModerationLog(Base):
    """Moderation actions log"""
    __tablename__ = "moderation_log"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # === Who ===
    admin_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    target_user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    
    # === Action ===
    action: Mapped[str] = Column(String(50), nullable=False, index=True)
    # warn, warn_revoke, ban_permanent, ban_temporary, unban, note
    
    # === Details ===
    reason: Mapped[Optional[str]] = Column(String(100), nullable=True)
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    duration_days: Mapped[Optional[int]] = Column(Integer, nullable=True)
    
    # === Relations ===
    warning_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("user_warnings.id"), nullable=True
    )
    ban_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("user_bans.id"), nullable=True
    )
    
    # === Timestamp ===
    created_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    # === Relationships ===
    admin = relationship("User", foreign_keys=[admin_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    warning = relationship("UserWarning")
    ban = relationship("UserBan")
    
    def __repr__(self) -> str:
        return f"<ModerationLog(id={self.id}, action={self.action}, admin={self.admin_id}, target={self.target_user_id})>"
