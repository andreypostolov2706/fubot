"""
Payment Constants — Константы для платёжных провайдеров

Используются при реализации провайдеров (TON, YooKassa, CryptoBot).
"""
from decimal import Decimal
from enum import Enum
from typing import Final


# =============================================================================
# PROVIDER IDs — Идентификаторы провайдеров
# =============================================================================

class ProviderId:
    """Provider identifiers for database and config"""
    TON = "ton"                    # Native TON payments
    CRYPTOBOT = "cryptobot"        # @CryptoBot payments
    YOOKASSA = "yookassa"          # YooKassa (RUB)
    STARS = "stars"                # Telegram Stars
    MANUAL = "manual"              # Manual confirmation


# =============================================================================
# CURRENCIES — Поддерживаемые валюты
# =============================================================================

class Currency:
    """Currency codes"""
    # Crypto
    TON = "TON"
    USDT = "USDT"
    BTC = "BTC"
    ETH = "ETH"
    
    # Fiat
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    
    # Internal
    GTON = "GTON"
    
    # Telegram
    STARS = "XTR"  # Telegram Stars


# =============================================================================
# PAYMENT STATUS — Статусы платежей
# =============================================================================

class PaymentStatus(str, Enum):
    """Payment statuses"""
    PENDING = "pending"          # Ожидает оплаты
    PROCESSING = "processing"    # Обрабатывается
    COMPLETED = "completed"      # Успешно завершён
    FAILED = "failed"            # Ошибка
    EXPIRED = "expired"          # Истёк срок
    CANCELLED = "cancelled"      # Отменён пользователем
    REFUNDED = "refunded"        # Возврат


# =============================================================================
# TRANSACTION TYPES — Типы транзакций
# =============================================================================

class TransactionType:
    """Transaction types for Transaction model"""
    CREDIT = "credit"            # Пополнение баланса
    DEBIT = "debit"              # Списание с баланса


class TransactionSource:
    """Transaction sources"""
    PAYMENT = "payment"          # Платёж через провайдера
    ADMIN = "admin"              # Админ начисление/списание
    BONUS = "bonus"              # Бонус (daily, welcome)
    REFERRAL = "referral"        # Реферальная комиссия
    PROMOCODE = "promocode"      # Промокод
    REFUND = "refund"            # Возврат
    SERVICE = "service"          # Списание сервисом


class TransactionAction:
    """Transaction actions (for debit)"""
    SERVICE_USAGE = "service_usage"      # Использование сервиса
    SUBSCRIPTION = "subscription"        # Подписка
    PURCHASE = "purchase"                # Покупка
    FEE = "fee"                          # Комиссия
    WITHDRAWAL = "withdrawal"            # Вывод


# =============================================================================
# LIMITS — Лимиты
# =============================================================================

class Limits:
    """Default limits (can be overridden in Settings)"""
    # Deposit
    MIN_DEPOSIT_GTON: Final[Decimal] = Decimal("1.0")
    MAX_DEPOSIT_GTON: Final[Decimal] = Decimal("100000.0")
    
    # Payout
    MIN_PAYOUT_GTON: Final[Decimal] = Decimal("5.0")
    MAX_PAYOUT_GTON: Final[Decimal] = Decimal("10000.0")
    
    # Daily
    MAX_DAILY_DEPOSIT_GTON: Final[Decimal] = Decimal("50000.0")
    MAX_DAILY_WITHDRAWAL_GTON: Final[Decimal] = Decimal("10000.0")
    
    # Payment timeout
    PAYMENT_TIMEOUT_MINUTES: Final[int] = 30


# =============================================================================
# FEES — Комиссии
# =============================================================================

class Fees:
    """Default fee percentages"""
    GLOBAL_FEE_PERCENT: Final[Decimal] = Decimal("0")
    PAYOUT_FEE_PERCENT: Final[Decimal] = Decimal("0")
    
    # Provider-specific (примерные)
    TON_FEE_PERCENT: Final[Decimal] = Decimal("0")
    CRYPTOBOT_FEE_PERCENT: Final[Decimal] = Decimal("1")
    YOOKASSA_FEE_PERCENT: Final[Decimal] = Decimal("3.5")


# =============================================================================
# GTON RATES — Курсы GTON
# =============================================================================

class GtonRates:
    """GTON rate constants"""
    # 1 GTON = X TON (базовый курс, обновляется из Settings)
    DEFAULT_GTON_TON_RATE: Final[Decimal] = Decimal("1.53")
    
    # Precision
    GTON_PRECISION: Final[int] = 6  # Decimal(18, 6)
    FIAT_PRECISION: Final[int] = 2  # Decimal(12, 2)
    
    # Rate TTL (seconds)
    FIAT_RATES_TTL: Final[int] = 86400   # 24 hours
    CRYPTO_RATES_TTL: Final[int] = 600   # 10 minutes


# =============================================================================
# PROVIDER CONFIG KEYS — Ключи конфигурации провайдеров
# =============================================================================

class ProviderConfigKeys:
    """Config keys for payment providers (stored in PaymentProvider.config)"""
    
    # TON
    TON_WALLET_ADDRESS = "wallet_address"
    TON_API_KEY = "api_key"
    TON_TESTNET = "testnet"
    
    # CryptoBot
    CRYPTOBOT_TOKEN = "token"
    CRYPTOBOT_TESTNET = "testnet"
    
    # YooKassa
    YOOKASSA_SHOP_ID = "shop_id"
    YOOKASSA_SECRET_KEY = "secret_key"
    YOOKASSA_RETURN_URL = "return_url"
    
    # Telegram Stars
    STARS_BOT_TOKEN = "bot_token"


# =============================================================================
# WEBHOOK PATHS — Пути для вебхуков
# =============================================================================

class WebhookPaths:
    """Webhook URL paths for providers"""
    TON = "/webhooks/ton"
    CRYPTOBOT = "/webhooks/cryptobot"
    YOOKASSA = "/webhooks/yookassa"
    STARS = "/webhooks/stars"


# =============================================================================
# SETTINGS KEYS — Ключи настроек
# =============================================================================

class SettingsKeys:
    """Settings keys used in payments module"""
    # GTON rates
    GTON_TON_RATE = "payments.gton_ton_rate"
    
    # Limits
    MIN_DEPOSIT_GTON = "payments.min_deposit_gton"
    MAX_DEPOSIT_GTON = "payments.max_deposit_gton"
    
    # Fees
    FEE_PERCENT = "payments.fee_percent"
    
    # Timeouts
    PAYMENT_TIMEOUT = "payments.payment_timeout_minutes"
    
    # TTL
    FIAT_RATES_TTL = "payments.fiat_rates_ttl"
    CRYPTO_RATES_TTL = "payments.crypto_rates_ttl"
    
    # Payout
    PAYOUT_MIN_GTON = "payout.min_gton"
    PAYOUT_FEE_PERCENT = "payout.fee_percent"
    PAYOUT_METHODS = "payout.methods"


# =============================================================================
# ERROR CODES — Коды ошибок
# =============================================================================

class PaymentError:
    """Payment error codes"""
    INVALID_AMOUNT = "invalid_amount"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    PROVIDER_NOT_FOUND = "provider_not_found"
    PROVIDER_INACTIVE = "provider_inactive"
    CONVERSION_FAILED = "conversion_failed"
    PAYMENT_NOT_FOUND = "payment_not_found"
    PAYMENT_EXPIRED = "payment_expired"
    PAYMENT_ALREADY_PROCESSED = "payment_already_processed"
    WEBHOOK_INVALID = "webhook_invalid"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    PROVIDER_ERROR = "provider_error"
