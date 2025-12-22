# База данных ядра FuBot

## Схема

```
┌─────────────────────────────────────────────────────────────────┐
│                         CORE DATABASE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   users     │────▶│   wallets   │────▶│transactions │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │  partners   │────▶│  referrals  │     │   payouts   │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │  services   │────▶│user_services│     │subscriptions│       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   events    │     │ broadcasts  │     │  settings   │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │ promocodes  │     │notifications│     │daily_bonuses│       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │user_warnings│     │  user_bans  │     │moderation_log│      │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

> 📖 Дополнительные таблицы описаны в:
> - [PROMOCODES.md](./PROMOCODES.md) — промокоды
> - [NOTIFICATIONS.md](./NOTIFICATIONS.md) — уведомления и триггеры
> - [MODERATION.md](./MODERATION.md) — модерация и баны
> - [DAILY_BONUS.md](./DAILY_BONUS.md) — ежедневные бонусы

---

## Таблица `users`

Пользователи системы.

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    
    # === Платформы ===
    telegram_id = Column(BigInteger, unique=True, index=True)
    telegram_username = Column(String(255))
    # discord_id = Column(BigInteger, unique=True, index=True)  # Будущее
    # whatsapp_phone = Column(String(20), unique=True, index=True)  # Будущее
    
    # === Профиль ===
    first_name = Column(String(255))
    last_name = Column(String(255))
    language = Column(String(10), default="ru")
    timezone = Column(String(50), default="Europe/Moscow")
    
    # === Системная роль ===
    role = Column(String(20), default="user")  # user, admin, superadmin
    
    # === Реферальная система ===
    referrer_id = Column(Integer, ForeignKey("users.id"), index=True)
    referral_code = Column(String(20), unique=True, index=True)
    
    # === Статус ===
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(String(500))
    blocked_at = Column(DateTime)
    
    # === Онбординг ===
    onboarding_completed = Column(Boolean, default=False)
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime, index=True)
```

---

## Таблица `wallets`

Кошельки пользователей. Основная валюта — **GTON** (6 знаков после запятой).

```python
class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # === Тип ===
    wallet_type = Column(String(20), nullable=False, default="main")
    # main   - основной (GTON)
    # bonus  - бонусные GTON (сгорают, нельзя вывести)
    
    # === Баланс (GTON — 6 знаков после запятой) ===
    balance = Column(Numeric(18, 6), default=Decimal("0"))
    
    # === Заморозка ===
    frozen = Column(Numeric(18, 6), default=Decimal("0"))
    
    # === Лимиты ===
    daily_limit = Column(Numeric(18, 6))           # Дневной лимит трат
    daily_spent = Column(Numeric(18, 6), default=Decimal("0"))
    daily_reset_at = Column(DateTime)
    
    # === Бонусные GTON ===
    expires_at = Column(DateTime)  # Когда сгорают
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'wallet_type', name='uq_user_wallet_type'),
    )
```

> ⚠️ **GTON** — внутренняя валюта бота. Цепочка конвертации: ANY → USD → TON → GTON

---

## Таблица `transactions`

История всех операций с балансом GTON.

```python
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    
    # === Тип операции ===
    type = Column(String(10), nullable=False, index=True)
    # credit - зачисление
    # debit  - списание
    
    # === Сумма (GTON) ===
    amount = Column(Numeric(18, 6), nullable=False)
    direction = Column(String(10), nullable=False)  # "credit" или "debit"
    
    # === Баланс (GTON) ===
    balance_before = Column(Numeric(18, 6))
    balance_after = Column(Numeric(18, 6))
    
    # === Платёж (для deposit) ===
    payment_method = Column(String(30))      # ton, yookassa, crypto
    payment_id = Column(String(255))         # ID в платёжке
    payment_amount = Column(Numeric(18, 6))  # Сумма в оригинальной валюте
    payment_currency = Column(String(10))    # RUB, USD, TON
    exchange_rate = Column(Numeric(18, 8))   # Курс на момент платежа
    
    # === Сервис (для usage) ===
    service_id = Column(String(100), index=True)
    service_action = Column(String(100))
    service_data = Column(JSON)
    
    # === Реферал ===
    referral_user_id = Column(Integer, ForeignKey("users.id"))
    referral_level = Column(Integer)
    
    # === Источник и действие ===
    source = Column(String(50))   # payment, bonus, referral, admin, service
    action = Column(String(50))   # deposit, usage, refund, commission
    reference_id = Column(String(100))  # Связь с платежом/промокодом
    
    # === Описание ===
    description = Column(String(500))
    
    # === Статус ===
    status = Column(String(20), default="completed", index=True)
    # pending, completed, failed, cancelled
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
```

---

## Таблица `partners`

Партнёрская программа. Баланс хранится в GTON.

```python
class Partner(Base):
    __tablename__ = "partners"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # === Реферальный код ===
    referral_code = Column(String(50), unique=True, nullable=False, index=True)
    
    # === Комиссии (%) ===
    level1_percent = Column(Numeric(5, 2), default=20.0)  # Прямые
    level2_percent = Column(Numeric(5, 2), default=0.0)   # 2-й уровень
    level3_percent = Column(Numeric(5, 2), default=0.0)   # 3-й уровень
    
    # === Баланс (GTON) ===
    balance = Column(Numeric(18, 6), default=0)           # Доступный баланс
    total_earned = Column(Numeric(18, 6), default=0)      # Всего заработано
    total_withdrawn = Column(Numeric(18, 6), default=0)   # Всего выведено
    frozen_balance = Column(Numeric(18, 6), default=0)    # Заморожено для вывода
    
    # === Статистика ===
    total_referrals = Column(Integer, default=0)
    active_referrals = Column(Integer, default=0)
    
    # === Статус ===
    status = Column(String(20), default="pending", index=True)
    # pending, active, blocked
    
    # === Заявка ===
    application_text = Column(Text)
    applied_at = Column(DateTime, default=datetime.utcnow)
    
    # === Одобрение ===
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

## Таблица `referrals`

Связи реферер → реферал.

```python
class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True)
    
    # === Связи ===
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), index=True)
    
    # === Уровень ===
    level = Column(Integer, default=1)  # 1, 2, 3
    
    # === Статистика ===
    total_payments = Column(Numeric(12, 2), default=0)
    total_commission = Column(Numeric(12, 2), default=0)
    
    # === Статус ===
    is_active = Column(Boolean, default=True)
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    first_payment_at = Column(DateTime)
    last_payment_at = Column(DateTime)
    
    __table_args__ = (
        UniqueConstraint('referrer_id', 'referred_id', name='uq_referral_pair'),
    )
```

---

## Таблица `commissions`

История реферальных комиссий. Создаётся автоматически при `deduct_balance`.

```python
class Commission(Base):
    __tablename__ = "commissions"
    
    id = Column(Integer, primary_key=True)
    
    # === Участники ===
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referral_id = Column(Integer, ForeignKey("referrals.id"), index=True)
    
    # === Суммы (GTON) ===
    source_amount = Column(Numeric(18, 6), nullable=False)      # Списано у реферала
    commission_amount = Column(Numeric(18, 6), nullable=False)  # Начислено рефереру
    commission_percent = Column(Numeric(5, 2), nullable=False)  # Процент
    
    # === Уровень ===
    level = Column(Integer, default=1)  # 1 = прямой реферер
    
    # === Источник ===
    service_id = Column(String(100))
    action = Column(String(100))
    
    # === Связи с транзакциями ===
    source_transaction_id = Column(Integer, ForeignKey("transactions.id"))
    commission_transaction_id = Column(Integer, ForeignKey("transactions.id"))
    
    # === Timestamp ===
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
```

---

## Таблица `payouts`

Заявки на вывод средств. Суммы в GTON + фиат эквивалент.

```python
class Payout(Base):
    __tablename__ = "payouts"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, index=True)
    
    # === Сумма (GTON) ===
    amount_gton = Column(Numeric(18, 6), nullable=False)  # Запрошено GTON
    fee_gton = Column(Numeric(18, 6), default=0)          # Комиссия GTON
    
    # === Фиат эквивалент (на момент заявки) ===
    amount_fiat = Column(Numeric(12, 2), nullable=False)  # Сумма в RUB
    currency = Column(String(3), default="RUB")           # Валюта
    gton_rate = Column(Numeric(12, 4), nullable=False)    # Курс GTON/RUB
    
    # === Метод ===
    method = Column(String(30), nullable=False)  # card, sbp, crypto
    details = Column(JSON, nullable=False)       # {"card": "4276...", "bank": "Sber"}
    
    # === Статус ===
    status = Column(String(20), default="pending", index=True)
    # pending, processing, completed, rejected, cancelled
    
    # === Обработка ===
    processed_by = Column(Integer, ForeignKey("users.id"))
    processed_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # === Комментарии ===
    user_comment = Column(Text)
    admin_comment = Column(Text)
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

## Таблица `services`

Реестр установленных сервисов.

```python
class Service(Base):
    __tablename__ = "services"
    
    id = Column(String(100), primary_key=True)  # "ai_psychologist"
    
    # === Информация ===
    name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(20))
    author = Column(String(255))
    icon = Column(String(10))  # Эмодзи
    
    # === Пути ===
    install_path = Column(String(500))
    
    # === Статус ===
    status = Column(String(20), default="active", index=True)
    # active, disabled, error, maintenance
    
    # === Конфигурация ===
    config = Column(JSON, default={})
    
    # === Возможности ===
    features = Column(JSON, default={})
    # {
    #   "subscriptions": true,
    #   "broadcasts": true,
    #   "partner_menu": false,
    #   "voice_messages": true
    # }
    
    # === Права ===
    permissions = Column(JSON, default=[])
    
    # === Порядок в меню ===
    menu_order = Column(Integer, default=0)
    
    # === Timestamps ===
    installed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # === Ошибки ===
    last_error = Column(Text)
    last_error_at = Column(DateTime)
    error_count = Column(Integer, default=0)
```

---

## Таблица `user_services`

Данные пользователя в контексте сервиса.

```python
class UserService(Base):
    __tablename__ = "user_services"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_id = Column(String(100), ForeignKey("services.id"), nullable=False, index=True)
    
    # === Роль в сервисе ===
    role = Column(String(30), default="user")  # user, vip, moderator, admin
    
    # === Подписка ===
    subscription_plan = Column(String(50))
    subscription_until = Column(DateTime)
    subscription_auto_renew = Column(Boolean, default=False)
    
    # === Настройки ===
    settings = Column(JSON, default={})
    
    # === FSM состояние ===
    state = Column(String(100))
    state_data = Column(JSON)
    state_updated_at = Column(DateTime)
    
    # === Статистика ===
    total_spent = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    
    # === Статус ===
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    
    # === Timestamps ===
    first_use_at = Column(DateTime, default=datetime.utcnow)
    last_use_at = Column(DateTime)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'service_id', name='uq_user_service'),
    )
```

---

## Таблица `subscriptions`

История подписок.

```python
class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_id = Column(String(100), ForeignKey("services.id"), nullable=False, index=True)
    
    # === План ===
    plan = Column(String(50), nullable=False)
    
    # === Период ===
    started_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # === Оплата ===
    price = Column(Integer, nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    
    # === Статус ===
    status = Column(String(20), default="active", index=True)
    # active, expired, cancelled, refunded
    
    # === Автопродление ===
    auto_renew = Column(Boolean, default=False)
    renewal_reminded = Column(Boolean, default=False)
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow)
    cancelled_at = Column(DateTime)
```

---

## Таблица `events`

Аналитика.

```python
class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True)
    
    # === Пользователь ===
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # === Событие ===
    category = Column(String(50), nullable=False, index=True)
    # user, payment, service, referral, subscription
    
    action = Column(String(100), nullable=False, index=True)
    # user:registered, payment:completed, service:ai:message_sent
    
    # === Источник ===
    service_id = Column(String(100), index=True)
    
    # === Данные ===
    label = Column(String(255))
    value = Column(Integer)
    properties = Column(JSON)
    
    # === Сессия ===
    session_id = Column(String(100), index=True)
    
    # === Контекст ===
    platform = Column(String(20))
    
    # === Timestamp ===
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
```

---

## Таблица `broadcasts`

Рассылки.

```python
class Broadcast(Base):
    __tablename__ = "broadcasts"
    
    id = Column(Integer, primary_key=True)
    
    # === Источник ===
    source = Column(String(20), default="admin")  # admin, service
    service_id = Column(String(100), ForeignKey("services.id"))
    
    # === Контент ===
    text = Column(Text, nullable=False)
    parse_mode = Column(String(10), default="HTML")
    
    # === Медиа ===
    media_type = Column(String(20))
    media_file_id = Column(String(255))
    
    # === Кнопки ===
    buttons = Column(JSON)
    
    # === Аудитория ===
    target = Column(String(50), default="all")
    filters = Column(JSON)
    
    # === Планирование ===
    scheduled_at = Column(DateTime)
    
    # === Статус ===
    status = Column(String(20), default="draft", index=True)
    # draft, scheduled, sending, paused, completed, cancelled
    
    # === Прогресс ===
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    # === Скорость ===
    send_rate = Column(Integer, default=30)
    
    # === Timestamps ===
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
```

---

## Таблица `settings`

Глобальные настройки.

```python
class Setting(Base):
    __tablename__ = "settings"
    
    key = Column(String(100), primary_key=True)
    
    # === Значение ===
    value = Column(Text, nullable=False)
    value_type = Column(String(20), default="string")
    # string, int, float, bool, json
    
    # === Описание ===
    description = Column(Text)
    
    # === Категория ===
    category = Column(String(50), index=True)
    # general, payments, referral, notifications, limits
    
    # === Редактируемость ===
    is_editable = Column(Boolean, default=True)
    
    # === Изменение ===
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"))
```
