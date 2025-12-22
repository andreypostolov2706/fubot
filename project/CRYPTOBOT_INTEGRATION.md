# CryptoBot Integration

## Обзор

CryptoBot — платёжный бот в Telegram для приёма криптовалютных платежей.

**Поддерживаемые валюты:** TON, USDT, BTC, ETH, LTC, BNB, TRX, USDC

## Настройка

### 1. Получение API токена

1. Откройте [@CryptoBot](https://t.me/CryptoBot) в Telegram
2. Напишите `/pay`
3. Нажмите **"Create App"** или **"Crypto Pay"**
4. Создайте новое приложение
5. Скопируйте **API Token**

### 2. Добавление в .env

```env
CRYPTOBOT_API_TOKEN=12345:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CRYPTOBOT_TESTNET=false
```

Для тестирования используйте [@CryptoTestnetBot](https://t.me/CryptoTestnetBot):
```env
CRYPTOBOT_API_TOKEN=your_testnet_token
CRYPTOBOT_TESTNET=true
```

### 3. Инициализация провайдера в БД

```bash
python tests/init_cryptobot.py
```

## Архитектура

```
core/payments/
├── providers/
│   ├── base.py          # BasePaymentProvider (абстрактный)
│   ├── cryptobot.py     # CryptoBotProvider
│   └── manager.py       # ProviderManager
├── service.py           # PaymentService
└── converter.py         # CurrencyConverter
```

## Использование

### Создание платежа

```python
from core.payments.service import payment_service

result = await payment_service.create_payment(
    user_id=123,
    amount_gton=Decimal("10"),  # Сколько GTON получит пользователь
    provider="cryptobot",
    currency="TON"  # или USDT, BTC, etc.
)

if result.success:
    print(f"Payment URL: {result.payment_url}")
    print(f"UUID: {result.payment_uuid}")
```

### Проверка статуса

```python
from core.payments.providers.manager import provider_manager
from core.payments.providers.base import PaymentStatus

provider = provider_manager.get_provider("cryptobot")
status = await provider.check_payment(provider_payment_id)

if status == PaymentStatus.COMPLETED:
    # Платёж завершён
    pass
```

### Webhook (опционально)

CryptoBot может отправлять webhook при изменении статуса платежа.

```python
from core.payments.providers.cryptobot import cryptobot_provider

result = await cryptobot_provider.handle_webhook(
    data=webhook_data,
    headers=request.headers
)

if result.success and result.status == PaymentStatus.COMPLETED:
    await payment_service.confirm_payment(
        payment_uuid=result.payment_uuid,
        provider_payment_id=result.provider_payment_id
    )
```

## Telegram UI

### Меню пополнения

```
💳 Пополнение баланса

💰 Баланс: 10.50 GTON (~1 050 ₽)
💱 Курс: 1 GTON ≈ 100 ₽

Выберите способ оплаты:

[🤖 CryptoBot (TON, USDT)]
[🎟 Ввести промокод]
[← Назад]
```

### Выбор суммы

```
🤖 Пополнение через CryptoBot

💰 Баланс: 10.50 GTON
💎 Валюта: TON

Выберите сумму пополнения:

• 1 TON → ~0.65 GTON
• 3 TON → ~1.96 GTON
• 5 TON → ~3.27 GTON

[1 TON] [3 TON] [5 TON]
[10 TON] [25 TON] [50 TON]

[💎 TON] [💵 USDT]
[← Назад]
```

### Платёж создан

```
✅ Платёж создан!

💎 Сумма: 5 TON
💰 Получите: ~3.27 GTON

Нажмите кнопку ниже для оплаты через @CryptoBot:

[💳 Оплатить 5 TON]  ← URL кнопка
[🔄 Проверить оплату]
[← Назад]
```

## API Reference

### CryptoBotProvider

| Метод | Описание |
|-------|----------|
| `create_payment()` | Создать инвойс |
| `check_payment()` | Проверить статус |
| `handle_webhook()` | Обработать webhook |
| `get_me()` | Информация о боте |
| `get_balance()` | Баланс бота |
| `get_exchange_rates()` | Курсы валют |

### PaymentStatus

| Статус | Описание |
|--------|----------|
| `PENDING` | Ожидает оплаты |
| `COMPLETED` | Оплачен |
| `EXPIRED` | Истёк |
| `FAILED` | Ошибка |

## Файлы

| Файл | Описание |
|------|----------|
| `core/payments/providers/cryptobot.py` | Провайдер CryptoBot |
| `core/payments/providers/manager.py` | Менеджер провайдеров |
| `core/platform/telegram/handlers/topup.py` | UI пополнения |
| `tests/init_cryptobot.py` | Инициализация в БД |
| `tests/test_cryptobot_api.py` | Тест API |

## Troubleshooting

### UNAUTHORIZED (401)

Токен недействителен. Получите новый у @CryptoBot.

### Provider not configured

Токен не установлен в .env или провайдер не добавлен в БД.

```bash
# Проверить .env
echo $CRYPTOBOT_API_TOKEN

# Добавить в БД
python tests/init_cryptobot.py
```

### Conversion failed

Не удалось конвертировать валюту. Проверьте курсы:

```python
from core.payments.rates import rates_manager
rates = await rates_manager.get_all_rates()
print(rates)
```

---

*Документ создан: 10.12.2024*
