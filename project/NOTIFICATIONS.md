# Расширенные уведомления

## Обзор

Система уведомлений включает:
- Push-уведомления (отложенные)
- Email уведомления
- Триггерные уведомления (автоматические)
- Напоминания о неактивности

---

## Таблица `notifications`

```python
class Notification(Base):
    """Уведомления пользователям"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # === Тип ===
    type = Column(String(30), nullable=False, index=True)
    # push      - в мессенджер
    # email     - на почту
    # internal  - внутреннее (inbox)
    
    # === Категория ===
    category = Column(String(50), nullable=False, index=True)
    # system        - системные
    # payment       - платежи
    # subscription  - подписки
    # balance       - баланс
    # referral      - рефералы
    # promo         - промо/маркетинг
    # reminder      - напоминания
    # service       - от сервисов
    
    # === Контент ===
    title = Column(String(255))
    text = Column(Text, nullable=False)
    
    # === Действие ===
    action_type = Column(String(30))     # callback, url, deeplink
    action_data = Column(String(500))    # callback_data или URL
    action_text = Column(String(100))    # Текст кнопки
    
    # === Планирование ===
    scheduled_at = Column(DateTime, index=True)  # Когда отправить
    
    # === Статус ===
    status = Column(String(20), default="pending", index=True)
    # pending   - ожидает отправки
    # sent      - отправлено
    # delivered - доставлено
    # read      - прочитано
    # failed    - ошибка
    # cancelled - отменено
    
    # === Результат ===
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    error = Column(Text)
    
    # === Источник ===
    source = Column(String(30), default="system")  # system, service, trigger
    service_id = Column(String(100))               # Если от сервиса
    trigger_id = Column(Integer, ForeignKey("notification_triggers.id"))
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## Таблица `notification_triggers`

```python
class NotificationTrigger(Base):
    """Триггеры для автоматических уведомлений"""
    __tablename__ = "notification_triggers"
    
    id = Column(Integer, primary_key=True)
    
    # === Название ===
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # === Тип триггера ===
    trigger_type = Column(String(50), nullable=False)
    # low_balance           - баланс ниже порога
    # zero_balance          - баланс = 0
    # subscription_expiring - подписка истекает через N дней
    # subscription_expired  - подписка истекла
    # inactive_days         - неактивен N дней
    # first_payment         - первый платёж
    # registration          - регистрация
    # referral_registered   - реферал зарегистрировался
    # referral_payment      - реферал сделал платёж
    # daily_bonus_available - доступен ежедневный бонус
    
    # === Условия ===
    conditions = Column(JSON, default={})
    # {
    #   "threshold": 10,        # для low_balance
    #   "days_before": 3,       # для subscription_expiring
    #   "inactive_days": 7,     # для inactive_days
    # }
    
    # === Шаблон уведомления ===
    notification_type = Column(String(30), default="push")  # push, email, both
    title_template = Column(String(255))
    text_template = Column(Text, nullable=False)
    # Поддерживает переменные: {user_name}, {balance}, {days}, {amount}
    
    action_type = Column(String(30))
    action_data = Column(String(500))
    action_text = Column(String(100))
    
    # === Ограничения ===
    cooldown_hours = Column(Integer, default=24)  # Не чаще чем раз в N часов
    max_per_user = Column(Integer)                # Максимум раз на пользователя
    
    # === Статус ===
    is_active = Column(Boolean, default=True, index=True)
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

## Таблица `user_notification_settings`

```python
class UserNotificationSettings(Base):
    """Настройки уведомлений пользователя"""
    __tablename__ = "user_notification_settings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # === Email ===
    email = Column(String(255))
    email_verified = Column(Boolean, default=False)
    email_verification_code = Column(String(50))
    email_verification_expires = Column(DateTime)
    
    # === Каналы ===
    push_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=False)
    
    # === Категории (что получать) ===
    receive_system = Column(Boolean, default=True)
    receive_payment = Column(Boolean, default=True)
    receive_subscription = Column(Boolean, default=True)
    receive_balance = Column(Boolean, default=True)
    receive_referral = Column(Boolean, default=True)
    receive_promo = Column(Boolean, default=True)      # Маркетинг
    receive_reminder = Column(Boolean, default=True)   # Напоминания
    receive_service = Column(Boolean, default=True)    # От сервисов
    
    # === Тихие часы ===
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(Time)   # 23:00
    quiet_hours_end = Column(Time)     # 08:00
    
    # === Timestamps ===
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

## Стандартные триггеры

```python
DEFAULT_TRIGGERS = [
    # === Баланс ===
    {
        "name": "low_balance",
        "trigger_type": "low_balance",
        "conditions": {"threshold": 10},
        "title_template": "⚠️ Низкий баланс",
        "text_template": "У вас осталось {balance} токенов. Пополните баланс, чтобы продолжить пользоваться сервисами.",
        "action_type": "callback",
        "action_data": "top_up",
        "action_text": "💳 Пополнить",
        "cooldown_hours": 72,
    },
    {
        "name": "zero_balance",
        "trigger_type": "zero_balance",
        "title_template": "💰 Баланс исчерпан",
        "text_template": "Ваш баланс: 0 токенов. Пополните, чтобы продолжить.",
        "action_type": "callback",
        "action_data": "top_up",
        "action_text": "💳 Пополнить",
        "cooldown_hours": 24,
    },
    
    # === Подписки ===
    {
        "name": "subscription_expiring_3d",
        "trigger_type": "subscription_expiring",
        "conditions": {"days_before": 3},
        "title_template": "⏰ Подписка истекает",
        "text_template": "Ваша подписка истекает через {days} дн. Продлите, чтобы не потерять доступ.",
        "action_type": "callback",
        "action_data": "subscription_renew",
        "action_text": "🔄 Продлить",
        "cooldown_hours": 24,
    },
    {
        "name": "subscription_expired",
        "trigger_type": "subscription_expired",
        "title_template": "❌ Подписка истекла",
        "text_template": "Ваша подписка закончилась. Продлите для продолжения использования.",
        "action_type": "callback",
        "action_data": "subscription_renew",
        "action_text": "🔄 Продлить",
        "cooldown_hours": 48,
    },
    
    # === Неактивность ===
    {
        "name": "inactive_3d",
        "trigger_type": "inactive_days",
        "conditions": {"inactive_days": 3},
        "title_template": "👋 Мы скучаем!",
        "text_template": "Вы не заходили уже 3 дня. Возвращайтесь!",
        "cooldown_hours": 72,
        "max_per_user": 1,
    },
    {
        "name": "inactive_7d",
        "trigger_type": "inactive_days",
        "conditions": {"inactive_days": 7},
        "title_template": "🎁 Бонус за возвращение",
        "text_template": "Вы давно не заходили. Вернитесь и получите бонус!",
        "action_type": "callback",
        "action_data": "claim_return_bonus",
        "action_text": "🎁 Получить бонус",
        "cooldown_hours": 168,  # 7 дней
        "max_per_user": 3,
    },
    
    # === Рефералы ===
    {
        "name": "referral_registered",
        "trigger_type": "referral_registered",
        "title_template": "🎉 Новый реферал!",
        "text_template": "По вашей ссылке зарегистрировался новый пользователь!",
    },
    {
        "name": "referral_payment",
        "trigger_type": "referral_payment",
        "title_template": "💰 Реферальный доход",
        "text_template": "Ваш реферал совершил платёж! Ваша комиссия: {amount} ₽",
    },
    
    # === Ежедневный бонус ===
    {
        "name": "daily_bonus_reminder",
        "trigger_type": "daily_bonus_available",
        "title_template": "🎁 Ежедневный бонус",
        "text_template": "Ваш ежедневный бонус готов к получению!",
        "action_type": "callback",
        "action_data": "daily_bonus",
        "action_text": "🎁 Забрать",
        "cooldown_hours": 20,
    },
]
```

---

## Core API для уведомлений

```python
async def send_notification(
    self,
    user_id: int,
    text: str,
    title: str = None,
    category: str = "system",
    notification_type: str = "push",
    action_type: str = None,
    action_data: str = None,
    action_text: str = None,
    scheduled_at: datetime = None
) -> int:
    """
    Отправить уведомление пользователю.
    
    Args:
        user_id: ID пользователя
        text: Текст уведомления
        title: Заголовок
        category: Категория (system, payment, promo, etc.)
        notification_type: Тип (push, email, both)
        action_*: Кнопка действия
        scheduled_at: Когда отправить (None = сразу)
    
    Returns:
        notification_id
    """

async def send_bulk_notification(
    self,
    user_ids: list[int],
    text: str,
    **kwargs
) -> int:
    """
    Отправить уведомление нескольким пользователям.
    
    Returns:
        Количество созданных уведомлений
    """

async def cancel_notification(self, notification_id: int) -> bool:
    """Отменить запланированное уведомление."""

async def get_user_notifications(
    self,
    user_id: int,
    status: str = None,
    limit: int = 50
) -> list[NotificationDTO]:
    """Получить уведомления пользователя."""

async def mark_notification_read(self, notification_id: int) -> bool:
    """Отметить уведомление прочитанным."""

async def get_unread_count(self, user_id: int) -> int:
    """Количество непрочитанных уведомлений."""
```

---

## Настройки пользователя

```
🔔 Настройки уведомлений

📧 Email: не указан
   [Добавить email]

━━━━━━━━━━━━━━━━━━━━━

Получать уведомления:

✅ 💳 Платежи и баланс
✅ ⭐ Подписки
✅ 🤝 Рефералы
✅ 🎁 Акции и промо
✅ 🔔 Напоминания
✅ 📦 От сервисов

━━━━━━━━━━━━━━━━━━━━━

🌙 Тихие часы: выкл
   [Настроить]

┌─────────────────────────┐
│ ◀️ Назад                │
└─────────────────────────┘
```

---

## Админка: Триггеры

```
🔔 Триггеры уведомлений

┌─────────────────────────┐
│ ✅ Низкий баланс        │
├─────────────────────────┤
│ ✅ Подписка истекает    │
├─────────────────────────┤
│ ✅ Неактивность 3 дня   │
├─────────────────────────┤
│ ❌ Неактивность 7 дней  │
├─────────────────────────┤
│ ➕ Создать триггер      │
├─────────────────────────┤
│ ◀️ Назад                │
└─────────────────────────┘
```

---

## Локализация

```python
# core/locales/ru.py

NOTIFICATIONS = {
    "settings_title": "🔔 Настройки уведомлений",
    "email_not_set": "📧 Email: не указан",
    "email_set": "📧 Email: {email}",
    "add_email": "Добавить email",
    "change_email": "Изменить email",
    
    "receive_title": "Получать уведомления:",
    "category_payment": "💳 Платежи и баланс",
    "category_subscription": "⭐ Подписки",
    "category_referral": "🤝 Рефералы",
    "category_promo": "🎁 Акции и промо",
    "category_reminder": "🔔 Напоминания",
    "category_service": "📦 От сервисов",
    
    "quiet_hours": "🌙 Тихие часы",
    "quiet_hours_off": "выкл",
    "quiet_hours_on": "{start} - {end}",
    "configure": "Настроить",
    
    # Триггерные сообщения
    "low_balance_title": "⚠️ Низкий баланс",
    "low_balance_text": "У вас осталось {balance} токенов. Пополните баланс.",
    "subscription_expiring_title": "⏰ Подписка истекает",
    "subscription_expiring_text": "Ваша подписка истекает через {days} дн.",
    "inactive_title": "👋 Мы скучаем!",
    "inactive_text": "Вы не заходили уже {days} дней. Возвращайтесь!",
}
```
