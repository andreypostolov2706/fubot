"""
FuBot Payments Module

Handles currency conversion, exchange rates, and payment processing.

Key components:
- CurrencyConverter: Converts between GTON and other currencies
- RatesManager: Fetches and caches exchange rates
- PaymentService: Manages payments and GTON balance operations
- BasePaymentProvider: Abstract base for payment providers
- constants: All payment-related constants for providers
"""
from .converter import CurrencyConverter, currency_converter, ConversionResult
from .rates import RatesManager, rates_manager
from .service import PaymentService, payment_service, PaymentResult, PaymentInfo
from .providers import BasePaymentProvider, ProviderPaymentResult, PaymentStatus
from .constants import (
    ProviderId, Currency, PaymentStatus as PaymentStatusEnum,
    TransactionType, TransactionSource, TransactionAction,
    Limits, Fees, GtonRates, ProviderConfigKeys, WebhookPaths,
    SettingsKeys, PaymentError
)

__all__ = [
    # Converter
    "CurrencyConverter",
    "currency_converter",
    "ConversionResult",
    # Rates
    "RatesManager",
    "rates_manager",
    # Service
    "PaymentService",
    "payment_service",
    "PaymentResult",
    "PaymentInfo",
    # Providers
    "BasePaymentProvider",
    "ProviderPaymentResult",
    "PaymentStatus",
    # Constants
    "ProviderId",
    "Currency",
    "PaymentStatusEnum",
    "TransactionType",
    "TransactionSource",
    "TransactionAction",
    "Limits",
    "Fees",
    "GtonRates",
    "ProviderConfigKeys",
    "WebhookPaths",
    "SettingsKeys",
    "PaymentError",
]
