# 📚 Документация FuBot

## Файлы документации

### Основные

| Файл | Описание |
|------|----------|
| [README.md](./README.md) | Обзор проекта, быстрый старт |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Архитектура системы, структура файлов |
| [DATABASE.md](./DATABASE.md) | Все таблицы БД ядра с полями |
| [CORE_API.md](./CORE_API.md) | API ядра для сервисов |
| [SETTINGS.md](./SETTINGS.md) | Все настройки системы |

### Сервисы

| Файл | Описание |
|------|----------|
| [BASE_SERVICE.md](./BASE_SERVICE.md) | Базовый класс сервиса |
| [SERVICE_GUIDE.md](./SERVICE_GUIDE.md) | Руководство по созданию сервиса |
| [SERVICE_LOCALIZATION.md](./SERVICE_LOCALIZATION.md) | Локализация сервисов |

### Функционал

| Файл | Описание |
|------|----------|
| [MENUS.md](./MENUS.md) | Меню и навигация |
| [LOCALIZATION.md](./LOCALIZATION.md) | Мультиязычность ядра |
| [ANALYTICS.md](./ANALYTICS.md) | Система аналитики |
| [PROMOCODES.md](./PROMOCODES.md) | Промокоды |
| [NOTIFICATIONS.md](./NOTIFICATIONS.md) | Уведомления и триггеры |
| [MODERATION.md](./MODERATION.md) | Модерация и блокировки |
| [DAILY_BONUS.md](./DAILY_BONUS.md) | Ежедневный бонус |

---

## Краткая справка

### Структура проекта

```
FuBot/
├── core/                   # Ядро (не меняется)
│   ├── database/           # БД ядра
│   ├── admin/              # Админ-панель
│   ├── partner/            # Партнёрка
│   ├── payments/           # Платежи
│   ├── platform/           # Telegram, Discord...
│   └── plugins/            # Менеджер сервисов
│
├── services/               # Подключаемые сервисы
│   └── ai_psychologist/
│
└── data/
    └── core.db
```

### Таблицы ядра

- `users` — пользователи
- `wallets` — кошельки (GTON, Decimal)
- `transactions` — история операций GTON
- `partners` — партнёры
- `referrals` — реферальные связи
- `payouts` — заявки на вывод
- `services` — реестр сервисов
- `user_services` — данные пользователя в сервисе
- `subscriptions` — подписки
- `events` — аналитика
- `broadcasts` — рассылки
- `settings` — настройки

### Главное меню (кнопки)

| # | Кнопка | Callback | Хендлер |
|---|--------|----------|---------|
| 1 | 🎁 Ежедневный бонус | `daily_bonus` | `daily_bonus.py` |
| 2 | 💳 Пополнить | `top_up` | `topup.py` |
| 3 | 🎟 Промокод | `promocode` | `promocode.py` |
| 4 | 🤝 Партнёрская программа | `partner` | `partner.py` |
| 5 | ⚙️ Настройки | `settings` | `settings.py` |
| 6 | ❓ Помощь | `help` | `help.py` |
| 7 | 🔧 Админ-панель | `admin` | `admin/` (только для админов) |

### Callback формат

```
# Ядро
main_menu, top_up, promocode, settings, partner, daily_bonus, admin

# Вложенные
partner:referrals, partner:payout, partner:payout:card, partner:payout:history
admin:users, admin:stats, admin:settings

# Сервисы
service:{service_id}:{action}:{params}
service:ai_psychologist:main
service:ai_psychologist:session:123
```

### Основные методы CoreAPI

```python
from decimal import Decimal

# Баланс (GTON)
await self.core.get_balance(user_id)  # -> Decimal
await self.core.deduct_balance(user_id, Decimal("0.5"), reason)
await self.core.add_balance(user_id, Decimal("1.0"), source)

# Конвертация
await self.core.convert_to_gton(Decimal("100"), "RUB")  # RUB -> GTON
await self.core.convert_from_gton(Decimal("1.0"), "RUB")  # GTON -> RUB
await self.core.format_gton(amount, with_fiat=True)  # "1.5 GTON (~150 ₽)"

# Состояние (FSM)
await self.core.set_user_state(user_id, state, data)
state, data = await self.core.get_user_state(user_id)
await self.core.clear_user_state(user_id)

# Настройки
await self.core.get_user_service_settings(user_id)
await self.core.set_user_service_settings(user_id, settings)

# Аналитика
await self.core.track_event(name, user_id, value, properties)

# Уведомления
await self.core.send_message(user_id, text, keyboard)
```

### Создание сервиса (чеклист)

1. ✅ Создать `services/my_service/`
2. ✅ Создать `service.py` с классом `MyService(BaseService)`
3. ✅ Реализовать `info`, `permissions`, `features`
4. ✅ Реализовать `install()`, `uninstall()`
5. ✅ Реализовать `get_user_menu_items()`, `get_admin_menu_items()`
6. ✅ Реализовать `handle_callback()`, `handle_message()`
7. ✅ Создать `database/` (если нужна своя БД)
8. ✅ Создать `install.bat`
9. ✅ Создать `requirements.txt`
10. ✅ Протестировать

---

## Статус реализации

### ✅ Ядро готово

- [x] Ядро — модели, CoreAPI, база данных
- [x] Telegram адаптер — хендлеры (start, topup, partner, daily_bonus, promocode)
- [x] GTON валюта — Decimal(18,6), конвертация, курсы
- [x] Реферальные комиссии — автоматическое начисление при deduct_balance
- [x] Админ-панель — балансы и статистика в GTON
- [x] Вывод средств — PayoutService, заморозка, фиат конвертация
- [x] Константы для провайдеров — `core/payments/constants.py`

### 📋 Отложено

- [ ] Платёжные провайдеры — TON, CryptoBot, YooKassa (база готова)
- [ ] Пример сервиса — AI Psychologist
