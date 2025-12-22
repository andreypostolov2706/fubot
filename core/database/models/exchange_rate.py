"""
Exchange Rate Model

Stores cached exchange rates from external APIs.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, UniqueConstraint
)
from sqlalchemy.orm import Mapped

from core.database.base import Base


class ExchangeRate(Base):
    """Exchange rate cache"""
    __tablename__ = "exchange_rates"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # Currency pair
    # Example: base=USD, quote=RUB means 1 USD = rate RUB
    base_currency: Mapped[str] = Column(String(10), nullable=False, index=True)
    quote_currency: Mapped[str] = Column(String(10), nullable=False, index=True)
    
    # Rate with 6 decimal precision
    # 1 base_currency = rate quote_currency
    rate: Mapped[Decimal] = Column(Numeric(18, 6), nullable=False)
    
    # Source of the rate
    # exchangerate, coingecko, admin
    source: Mapped[str] = Column(String(50), nullable=False, default="api")
    
    # Timestamps
    updated_at: Mapped[datetime] = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        index=True
    )
    
    __table_args__ = (
        UniqueConstraint(
            'base_currency', 
            'quote_currency', 
            name='uq_exchange_rate_pair'
        ),
    )
    
    def __repr__(self) -> str:
        return f"<ExchangeRate({self.base_currency}/{self.quote_currency}={self.rate})>"
