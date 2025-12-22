# Настройки FuBot

## Обзор

Настройки хранятся в таблице `settings` и редактируются через админ-панель.

---

## Категории настроек

| Категория | Описание |
|-----------|----------|
| `general` | Общие настройки бота |
| `tokens` | Токены и курсы |
| `referral` | Партнёрская программа |
| `payments` | Платежи |
| `limits` | Лимиты |
| `notifications` | Уведомления |
| `analytics` | Аналитика |

---

## Все настройки

### General (Общие)

| Ключ | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `general.bot_name` | string | "FuBot" | Название бота |
| `general.support_username` | string | "@support" | Username поддержки |
| `general.support_url` | string | "" | URL поддержки |
| `general.default_language` | string | "ru" | Язык по умолчанию |
| `general.timezone` | string | "Europe/Moscow" | Часовой пояс |
| `general.maintenance_mode` | bool | false | Режим обслуживания |
| `general.maintenance_message` | string | "Бот на обслуживании" | Сообщение при обслуживании |

### Tokens (Токены)

| Ключ | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `tokens.rate_rub` | float | 1.0 | Курс: 1 токен = X рублей |
| `tokens.min_purchase` | int | 100 | Минимальная покупка (токенов) |
| `tokens.max_purchase` | int | 100000 | Максимальная покупка (токенов) |
| `tokens.bonus_percent` | int | 0 | Бонус при пополнении (%) |
| `tokens.bonus_min_amount` | int | 500 | Мин. сумма для бонуса |
| `tokens.welcome_bonus` | int | 0 | Бонус при регистрации |

### Referral (Партнёрка)

| Ключ | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `referral.enabled` | bool | true | Партнёрка включена |
| `referral.default_level1` | float | 20.0 | Комиссия 1 уровня (%) |
| `referral.level2_enabled` | bool | false | 2-й уровень включён |
| `referral.default_level2` | float | 5.0 | Комиссия 2 уровня (%) |
| `referral.level3_enabled` | bool | false | 3-й уровень включён |
| `referral.default_level3` | float | 2.0 | Комиссия 3 уровня (%) |
| `referral.min_payout` | int | 500 | Минимальная сумма вывода (руб) |
| `referral.payout_fee_percent` | float | 0 | Комиссия за вывод (%) |
| `referral.payout_fee_fixed` | int | 0 | Фикс. комиссия за вывод (руб) |
| `referral.registration_bonus` | int | 0 | Бонус рефералу при регистрации |
| `referral.first_payment_bonus` | int | 0 | Бонус за первый платёж реферала |
| `referral.auto_approve_partners` | bool | false | Авто-одобрение партнёров |

### Payments (Платежи)

| Ключ | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `payments.yookassa_enabled` | bool | true | YooKassa включена |
| `payments.yookassa_shop_id` | string | "" | Shop ID |
| `payments.yookassa_secret` | string | "" | Secret Key |
| `payments.crypto_enabled` | bool | false | Крипто включена |
| `payments.sbp_enabled` | bool | false | СБП включён |
| `payments.card_enabled` | bool | true | Карты включены |

### Limits (Лимиты)

| Ключ | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `limits.daily_messages` | int | 0 | Лимит сообщений в день (0 = нет) |
| `limits.daily_tokens` | int | 0 | Лимит токенов в день (0 = нет) |
| `limits.rate_limit_messages` | int | 10 | Сообщений в минуту |
| `limits.rate_limit_callbacks` | int | 30 | Callbacks в минуту |

### Notifications (Уведомления)

| Ключ | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `notifications.low_balance_threshold` | int | 10 | Порог низкого баланса |
| `notifications.low_balance_enabled` | bool | true | Уведомлять о низком балансе |
| `notifications.subscription_remind_days` | int | 3 | За сколько дней напоминать |
| `notifications.welcome_message` | string | "..." | Приветственное сообщение |
| `notifications.payment_success` | string | "..." | Сообщение об успешной оплате |

### Analytics (Аналитика)

| Ключ | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `analytics.enabled` | bool | true | Аналитика включена |
| `analytics.retention_days` | int | 90 | Хранить события N дней |
| `analytics.daily_report` | bool | true | Дневной отчёт |
| `analytics.report_chat_id` | int | 0 | Куда отправлять отчёт |

### Localization (Локализация)

| Ключ | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `localization.default_language` | string | "ru" | Язык по умолчанию |
| `localization.enabled_languages` | json | ["ru"] | Включённые языки |
| `localization.show_on_registration` | bool | false | Показывать выбор при регистрации |
| `localization.show_in_settings` | bool | true | Показывать в настройках |

---

## Работа с настройками

### Получение настройки

```python
# В ядре
from core.services.settings_service import get_setting

rate = get_setting("tokens.rate_rub", default=1.0)
enabled = get_setting("referral.enabled", default=True)
```

### В сервисе

```python
# Через Core API
rate = await self.core.get_setting("tokens.rate_rub", default=1.0)
```

### Изменение настройки (админ)

```python
from core.services.settings_service import set_setting

set_setting("tokens.rate_rub", 1.5, updated_by=admin_id)
```

---

## Настройки сервиса

Каждый сервис имеет свою конфигурацию в таблице `services.config`:

```python
# Получить конфиг сервиса
config = await self.core.get_service_config()
# {"model": "gpt-4", "max_tokens": 1000}

# Обновить конфиг
await self.core.update_service_config({
    "model": "gpt-4-turbo",
    "max_tokens": 2000
})
```

### Пример конфига AI Psychologist

```json
{
    "model": "gpt-4",
    "max_tokens": 1000,
    "temperature": 0.7,
    "system_prompt": "Ты психолог...",
    "voice_enabled": true,
    "voice_model": "tts-1",
    "voice_default_gender": "female",
    "session_timeout_minutes": 30,
    "summary_every_n_messages": 5,
    "cost_per_1k_input": 5,
    "cost_per_1k_output": 15,
    "cost_voice_per_second": 0.5
}
```

---

## Админ-панель настроек

```
⚙️ Настройки

Выберите категорию:

┌─────────────────────────┐
│ 🤖 Общие                │
├─────────────────────────┤
│ 🪙 Токены               │
├─────────────────────────┤
│ 🤝 Партнёрка            │
├─────────────────────────┤
│ 💳 Платежи              │
├─────────────────────────┤
│ 🚫 Лимиты               │
├─────────────────────────┤
│ 🔔 Уведомления          │
├─────────────────────────┤
│ 📊 Аналитика            │
├─────────────────────────┤
│ ◀️ Назад                │
└─────────────────────────┘
```

При выборе категории:

```
🪙 Настройки токенов

• Курс: 1 токен = 1.0 ₽
• Мин. покупка: 100 токенов
• Макс. покупка: 100,000 токенов
• Бонус при пополнении: 0%
• Бонус при регистрации: 0 токенов

┌─────────────────────────┐
│ ✏️ Курс токена          │
├─────────────────────────┤
│ ✏️ Мин. покупка         │
├─────────────────────────┤
│ ✏️ Бонус при пополнении │
├─────────────────────────┤
│ ◀️ Назад                │
└─────────────────────────┘
```

---

## Переменные окружения (.env)

Секретные настройки хранятся в `.env`:

```env
# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC...

# Database
DATABASE_URL=sqlite:///data/core.db

# Payments
YOOKASSA_SHOP_ID=123456
YOOKASSA_SECRET_KEY=test_xxx

# OpenAI (для сервисов)
OPENAI_API_KEY=sk-xxx

# Admin
ADMIN_IDS=123456789,987654321

# Debug
DEBUG=false
LOG_LEVEL=INFO
```

### Загрузка в коде

```python
# core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/core.db")
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

---

## Валидация настроек

```python
# core/services/settings_service.py

SETTINGS_SCHEMA = {
    "tokens.rate_rub": {
        "type": "float",
        "min": 0.01,
        "max": 1000,
        "description": "Курс токена в рублях"
    },
    "referral.default_level1": {
        "type": "float",
        "min": 0,
        "max": 100,
        "description": "Комиссия 1 уровня (%)"
    },
    # ...
}

def validate_setting(key: str, value: Any) -> bool:
    schema = SETTINGS_SCHEMA.get(key)
    if not schema:
        return True  # Нет схемы = любое значение
    
    if schema["type"] == "float":
        if not isinstance(value, (int, float)):
            return False
        if "min" in schema and value < schema["min"]:
            return False
        if "max" in schema and value > schema["max"]:
            return False
    
    return True
```
