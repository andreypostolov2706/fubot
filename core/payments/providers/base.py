"""
Base Payment Provider

Abstract class for all payment providers.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum


class PaymentStatus(Enum):
    """Payment status from provider"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"


@dataclass
class ProviderPaymentResult:
    """Result of creating payment at provider"""
    success: bool
    payment_url: Optional[str] = None
    provider_payment_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None
    raw_response: Optional[dict] = None


@dataclass
class WebhookResult:
    """Result of processing webhook"""
    success: bool
    payment_uuid: Optional[str] = None
    status: Optional[PaymentStatus] = None
    provider_payment_id: Optional[str] = None
    error: Optional[str] = None


class BasePaymentProvider(ABC):
    """
    Abstract base class for payment providers.
    
    To implement a new provider:
    1. Create a new file in providers/ (e.g., ton.py)
    2. Inherit from BasePaymentProvider
    3. Implement all abstract methods
    4. Register provider in database (payment_providers table)
    
    Example:
        class TonProvider(BasePaymentProvider):
            @property
            def id(self) -> str:
                return "ton"
            
            @property
            def name(self) -> str:
                return "TON Wallet"
            
            @property
            def currencies(self) -> List[str]:
                return ["TON"]
            
            async def create_payment(...) -> ProviderPaymentResult:
                # Implementation
                pass
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize provider with config.
        
        Args:
            config: Provider configuration (API keys, etc.)
        """
        self.config = config or {}
    
    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique provider ID.
        Must match ID in payment_providers table.
        
        Example: "ton", "cryptobot", "yookassa"
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Display name for UI.
        
        Example: "TON Wallet", "CryptoBot", "ЮKassa"
        """
        pass
    
    @property
    @abstractmethod
    def currencies(self) -> List[str]:
        """
        List of supported currencies.
        
        Example: ["TON"], ["RUB", "USD"], ["USDT", "BTC"]
        """
        pass
    
    @property
    def icon(self) -> str:
        """
        Emoji icon for UI.
        
        Example: "💎", "🤖", "💳"
        """
        return "💳"
    
    @abstractmethod
    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        user_id: int,
        payment_uuid: str,
        description: str = None,
        **kwargs
    ) -> ProviderPaymentResult:
        """
        Create payment at provider.
        
        Args:
            amount: Amount in provider's currency
            currency: Currency code
            user_id: Internal user ID
            payment_uuid: Internal payment UUID
            description: Payment description
            **kwargs: Additional provider-specific params
            
        Returns:
            ProviderPaymentResult with payment URL
        """
        pass
    
    @abstractmethod
    async def check_payment(
        self,
        provider_payment_id: str
    ) -> PaymentStatus:
        """
        Check payment status at provider.
        
        Args:
            provider_payment_id: Payment ID from provider
            
        Returns:
            Current payment status
        """
        pass
    
    async def handle_webhook(
        self,
        data: dict,
        headers: dict = None
    ) -> WebhookResult:
        """
        Handle webhook from provider.
        
        Override this method if provider supports webhooks.
        
        Args:
            data: Webhook payload
            headers: HTTP headers (for signature verification)
            
        Returns:
            WebhookResult with payment info
        """
        return WebhookResult(
            success=False,
            error="Webhooks not implemented for this provider"
        )
    
    async def cancel_payment(
        self,
        provider_payment_id: str
    ) -> bool:
        """
        Cancel pending payment.
        
        Override if provider supports cancellation.
        
        Args:
            provider_payment_id: Payment ID from provider
            
        Returns:
            True if cancelled successfully
        """
        return False
    
    async def refund_payment(
        self,
        provider_payment_id: str,
        amount: Decimal = None
    ) -> bool:
        """
        Refund completed payment.
        
        Override if provider supports refunds.
        
        Args:
            provider_payment_id: Payment ID from provider
            amount: Refund amount (full refund if None)
            
        Returns:
            True if refunded successfully
        """
        return False
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """
        Validate provider configuration.
        
        Override to add config validation.
        
        Returns:
            (is_valid, error_message)
        """
        return True, None
