# Промокоды

## Обзор

Система промокодов позволяет:
- Начислять бонусные **GTON**
- Давать бесплатную подписку
- Ограничивать по количеству активаций
- Устанавливать срок действия

---

## Таблица `promocodes`

```python
class PromoCode(Base):
    __tablename__ = "promocodes"
    
    id = Column(Integer, primary_key=True)
    
    # === Код ===
    code = Column(String(50), unique=True, nullable=False, index=True)
    # Код в верхнем регистре: "WELCOME50", "NEWYEAR2024"
    
    # === Описание ===
    name = Column(String(255))           # Название для админки
    description = Column(Text)           # Описание
    
    # === Тип награды ===
    reward_type = Column(String(30), nullable=False)
    # gton         - бонусные GTON
    # subscription - бесплатная подписка
    # discount     - скидка на пополнение (%)
    
    # === Значение награды ===
    reward_value = Column(Numeric(18, 6), nullable=False)
    # Для gton: количество GTON (Decimal)
    # Для subscription: количество дней
    # Для discount: процент скидки
    
    # === Для подписки ===
    subscription_service_id = Column(String(100))  # Для какого сервиса
    subscription_plan = Column(String(50))         # Какой план
    
    # === Лимиты ===
    max_activations = Column(Integer)              # Всего активаций (null = безлимит)
    max_per_user = Column(Integer, default=1)      # Активаций на пользователя
    current_activations = Column(Integer, default=0)
    
    # === Условия ===
    min_deposit = Column(Integer)                  # Мин. сумма пополнения (для discount)
    only_new_users = Column(Boolean, default=False)  # Только для новых
    only_first_deposit = Column(Boolean, default=False)  # Только первый платёж
    
    # === Период действия ===
    starts_at = Column(DateTime)                   # Начало действия
    expires_at = Column(DateTime)                  # Окончание действия
    
    # === Статус ===
    is_active = Column(Boolean, default=True, index=True)
    
    # === Создание ===
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

## Таблица `promocode_activations`

```python
class PromoCodeActivation(Base):
    """История активаций промокодов"""
    __tablename__ = "promocode_activations"
    
    id = Column(Integer, primary_key=True)
    
    promocode_id = Column(Integer, ForeignKey("promocodes.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # === Награда ===
    reward_type = Column(String(30), nullable=False)  # gton, subscription, discount
    reward_value = Column(Numeric(18, 6), nullable=False)  # GTON или дни/процент
    
    # === Связи ===
    transaction_id = Column(Integer, ForeignKey("transactions.id"))  # Если токены
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))  # Если подписка
    
    # === Timestamp ===
    activated_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        # Уникальность: пользователь + промокод (если max_per_user=1)
        Index('idx_promo_user', 'promocode_id', 'user_id'),
    )
```

---

## Core API для промокодов

```python
async def validate_promocode(
    self, 
    code: str, 
    user_id: int
) -> PromoCodeValidationResult:
    """
    Проверить промокод.
    
    Returns:
        PromoCodeValidationResult:
            - valid: bool
            - error: str (если невалидный)
            - reward_type: str
            - reward_value: int
            - description: str
    """

async def activate_promocode(
    self, 
    code: str, 
    user_id: int
) -> PromoCodeActivationResult:
    """
    Активировать промокод.
    
    Returns:
        PromoCodeActivationResult:
            - success: bool
            - error: str
            - reward_type: str
            - reward_value: int
            - new_balance: int (если токены)
            - subscription_until: datetime (если подписка)
    """

async def get_user_promocode_history(
    self, 
    user_id: int
) -> list[PromoCodeActivationDTO]:
    """
    История активаций промокодов пользователя.
    """
```

---

## Примеры промокодов

### 1. Бонусные токены

```python
PromoCode(
    code="WELCOME100",
    name="Приветственный бонус",
    reward_type="tokens",
    reward_value=100,
    only_new_users=True,
    max_per_user=1
)
```

### 2. Бесплатная подписка

```python
PromoCode(
    code="TRIAL7",
    name="7 дней Premium бесплатно",
    reward_type="subscription",
    reward_value=7,  # дней
    subscription_service_id="ai_psychologist",
    subscription_plan="premium",
    only_new_users=True,
    max_per_user=1
)
```

### 3. Скидка на пополнение

```python
PromoCode(
    code="SALE20",
    name="Скидка 20% на пополнение",
    reward_type="discount",
    reward_value=20,  # процентов
    min_deposit=500,
    expires_at=datetime(2024, 12, 31)
)
```

### 4. Ограниченный промокод

```python
PromoCode(
    code="FIRST100",
    name="Для первых 100 пользователей",
    reward_type="tokens",
    reward_value=500,
    max_activations=100,
    max_per_user=1
)
```

---

## Меню пользователя

```
💳 Пополнение баланса

Текущий баланс: 50 токенов

┌─────────────────────────┐
│ 100 ₽ → 100 токенов     │
├─────────────────────────┤
│ 500 ₽ → 500 токенов     │
├─────────────────────────┤
│ 🎁 Ввести промокод      │  ← Новая кнопка
├─────────────────────────┤
│ ◀️ Назад                │
└─────────────────────────┘
```

При нажатии "Ввести промокод":

```
🎁 Введите промокод:
```

После ввода (успех):

```
✅ Промокод активирован!

🎁 Вам начислено: 100 токенов
💰 Новый баланс: 150 токенов
```

После ввода (ошибка):

```
❌ Промокод недействителен

Возможные причины:
• Промокод не существует
• Срок действия истёк
• Вы уже использовали этот промокод
• Промокод только для новых пользователей
```

---

## Админка

```
🎁 Промокоды

Активных: 5
Всего активаций: 1,234

┌─────────────────────────┐
│ ➕ Создать промокод     │
├─────────────────────────┤
│ 📋 Список промокодов    │
├─────────────────────────┤
│ 📊 Статистика           │
├─────────────────────────┤
│ ◀️ Назад                │
└─────────────────────────┘
```

Создание промокода:

```
➕ Создание промокода

Шаг 1: Введите код (латиница, цифры):

> SUMMER2024

Шаг 2: Выберите тип награды:

┌─────────────────────────┐
│ 🪙 Бонусные токены      │
├─────────────────────────┤
│ ⭐ Подписка             │
├─────────────────────────┤
│ 💸 Скидка на пополнение │
└─────────────────────────┘
```

---

## Локализация

```python
# core/locales/ru.py

PROMOCODE = {
    "enter_code": "🎁 Введите промокод:",
    "activated": "✅ Промокод активирован!",
    "reward_tokens": "🎁 Вам начислено: {amount} токенов",
    "reward_subscription": "⭐ Вам активирована подписка {plan} на {days} дней",
    "reward_discount": "💸 Скидка {percent}% применена",
    "new_balance": "💰 Новый баланс: {balance} токенов",
    
    # Ошибки
    "invalid": "❌ Промокод недействителен",
    "expired": "❌ Срок действия промокода истёк",
    "already_used": "❌ Вы уже использовали этот промокод",
    "limit_reached": "❌ Лимит активаций промокода исчерпан",
    "new_users_only": "❌ Промокод только для новых пользователей",
    "first_deposit_only": "❌ Промокод только для первого пополнения",
}
```
