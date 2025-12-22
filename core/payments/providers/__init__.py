"""
Payment Providers

Abstract base and implementations for payment providers.
"""
from .base import BasePaymentProvider, ProviderPaymentResult, PaymentStatus, WebhookResult
from .cryptobot import CryptoBotProvider, cryptobot_provider
from .platega import PlategalProvider, platega_provider

__all__ = [
    "BasePaymentProvider",
    "ProviderPaymentResult",
    "PaymentStatus",
    "WebhookResult",
    "CryptoBotProvider",
    "cryptobot_provider",
    "PlategalProvider",
    "platega_provider",
]
