"""
Payment Models

Payment and PaymentProvider models for handling payments.
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, 
    Boolean, ForeignKey, JSON, Text
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base


class PaymentProvider(Base):
    """Payment provider configuration"""
    __tablename__ = "payment_providers"
    
    # Provider ID (ton, cryptobot, yookassa)
    id: Mapped[str] = Column(String(50), primary_key=True)
    
    # Display name
    name: Mapped[str] = Column(String(100), nullable=False)
    
    # Icon emoji
    icon: Mapped[str] = Column(String(10), default="💳")
    
    # Is provider active
    is_active: Mapped[bool] = Column(Boolean, default=True, index=True)
    
    # Supported currencies
    # ["RUB", "USD", "TON"]
    currencies: Mapped[Optional[list]] = Column(JSON, default=list)
    
    # Provider configuration (API keys, etc.)
    # Stored encrypted in production
    config: Mapped[Optional[dict]] = Column(JSON, default=dict)
    
    # Provider fee percentage
    fee_percent: Mapped[Decimal] = Column(Numeric(5, 2), default=0)
    
    # Limits in provider's primary currency
    min_amount: Mapped[Optional[Decimal]] = Column(Numeric(18, 6))
    max_amount: Mapped[Optional[Decimal]] = Column(Numeric(18, 6))
    
    # Sort order in UI
    sort_order: Mapped[int] = Column(Integer, default=0)
    
    # Description for users
    description: Mapped[Optional[str]] = Column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", 
        back_populates="provider_rel"
    )
    
    def __repr__(self) -> str:
        return f"<PaymentProvider({self.id}, active={self.is_active})>"


class Payment(Base):
    """Payment record"""
    __tablename__ = "payments"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # Unique payment identifier
    uuid: Mapped[str] = Column(String(36), unique=True, nullable=False, index=True)
    
    # User who made the payment
    user_id: Mapped[int] = Column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=False, 
        index=True
    )
    
    # === Amounts ===
    
    # Final GTON amount to credit (calculated at confirmation)
    amount_gton: Mapped[Decimal] = Column(Numeric(18, 6), nullable=False)
    
    # Original amount in payment currency
    amount_original: Mapped[Decimal] = Column(Numeric(18, 6), nullable=False)
    
    # Payment currency
    currency: Mapped[str] = Column(String(10), nullable=False)
    
    # === Fee ===
    
    # Fee percentage applied
    fee_percent: Mapped[Decimal] = Column(Numeric(5, 2), default=0)
    
    # Fee amount in payment currency
    fee_amount: Mapped[Decimal] = Column(Numeric(18, 6), default=0)
    
    # === Exchange rates at confirmation ===
    
    # Rate of payment currency to USD
    # e.g., 1 USD = 103.5 RUB
    rate_currency_usd: Mapped[Optional[Decimal]] = Column(Numeric(18, 6))
    
    # Rate of TON to USD
    # e.g., 1 TON = 6.85 USD
    rate_ton_usd: Mapped[Optional[Decimal]] = Column(Numeric(18, 6))
    
    # Rate of GTON to TON (from settings)
    # e.g., 1 GTON = 1.53 TON
    rate_gton_ton: Mapped[Optional[Decimal]] = Column(Numeric(18, 6))
    
    # === Provider ===
    
    # Provider ID
    provider: Mapped[str] = Column(
        String(50), 
        ForeignKey("payment_providers.id"),
        nullable=False,
        index=True
    )
    
    # Payment ID from provider
    provider_payment_id: Mapped[Optional[str]] = Column(String(255))
    
    # Additional data from provider
    provider_data: Mapped[Optional[dict]] = Column(JSON)
    
    # === Status ===
    
    # pending, completed, expired, failed, refunded
    status: Mapped[str] = Column(String(20), default="pending", index=True)
    
    # Error message if failed
    error_message: Mapped[Optional[str]] = Column(Text)
    
    # === Timestamps ===
    
    created_at: Mapped[datetime] = Column(
        DateTime, 
        default=datetime.utcnow, 
        index=True
    )
    
    # When payment expires
    expires_at: Mapped[Optional[datetime]] = Column(DateTime, index=True)
    
    # When payment was completed
    completed_at: Mapped[Optional[datetime]] = Column(DateTime)
    
    # === References ===
    
    # Transaction created after payment
    transaction_id: Mapped[Optional[int]] = Column(
        Integer, 
        ForeignKey("transactions.id")
    )
    
    # === Relationships ===
    
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    provider_rel: Mapped["PaymentProvider"] = relationship(
        "PaymentProvider", 
        back_populates="payments"
    )
    transaction: Mapped[Optional["Transaction"]] = relationship(
        "Transaction", 
        foreign_keys=[transaction_id]
    )
    
    def __repr__(self) -> str:
        return f"<Payment({self.uuid[:8]}, {self.amount_gton} GTON, {self.status})>"
    
    @property
    def is_pending(self) -> bool:
        return self.status == "pending"
    
    @property
    def is_completed(self) -> bool:
        return self.status == "completed"
    
    @property
    def is_expired(self) -> bool:
        return self.status == "expired"
    
    @property
    def net_amount(self) -> Decimal:
        """Amount after fee deduction"""
        return self.amount_original - self.fee_amount
