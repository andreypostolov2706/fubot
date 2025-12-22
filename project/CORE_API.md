# Core API — Интерфейс ядра для сервисов

## Обзор

`CoreAPI` — это интерфейс, через который сервисы взаимодействуют с ядром.
Сервис получает экземпляр `CoreAPI` при инициализации и использует его для всех операций.

```python
class MyService(BaseService):
    def __init__(self, core_api: CoreAPI):
        self.core = core_api
    
    async def do_something(self, user_id: int):
        # Используем Core API
        balance = await self.core.get_balance(user_id)
        await self.core.deduct_balance(user_id, 10, reason="action")
```

---

## Полный API

### Пользователи

```python
async def get_user(self, telegram_id: int) -> Optional[UserDTO]:
    """
    Получить пользователя по telegram_id.
    
    Returns:
        UserDTO или None если не найден
    """

async def get_user_by_id(self, user_id: int) -> Optional[UserDTO]:
    """
    Получить пользователя по внутреннему ID.
    """

async def update_user(self, user_id: int, **fields) -> bool:
    """
    Обновить данные пользователя.
    
    Args:
        user_id: ID пользователя
        **fields: Поля для обновления (first_name, language, etc.)
    
    Returns:
        True если успешно
    """

async def get_user_metadata(self, user_id: int, key: str) -> Any:
    """
    Получить метаданные пользователя.
    Метаданные хранятся в JSON поле.
    """

async def set_user_metadata(self, user_id: int, key: str, value: Any):
    """
    Установить метаданные пользователя.
    """
```

### Баланс (GTON)

> ⚠️ **Важно:** Внутренняя валюта — GTON (6 знаков после запятой).
> Все суммы передаются как `Decimal`, не `int`.

```python
from decimal import Decimal

async def get_balance(self, user_id: int, wallet_type: str = "main") -> Decimal:
    """
    Получить баланс пользователя в GTON.
    
    Args:
        user_id: ID пользователя
        wallet_type: "main" или "bonus"
    
    Returns:
        Баланс в GTON (Decimal с 6 знаками)
    """

async def get_all_balances(self, user_id: int) -> dict[str, Decimal]:
    """
    Получить все балансы пользователя.
    
    Returns:
        {"main": Decimal("100.5"), "bonus": Decimal("50.0")}
    """

async def get_balance_with_fiat(self, user_id: int, fiat: str = "RUB") -> tuple[Decimal, Optional[Decimal]]:
    """
    Получить баланс GTON с фиатным эквивалентом.
    
    Returns:
        (gton_balance, fiat_equivalent) — например (Decimal("10.5"), Decimal("1085.50"))
    """

async def deduct_balance(
    self, 
    user_id: int, 
    amount: Decimal, 
    reason: str = "",
    action: str = "",
    data: dict = None
) -> TransactionResult:
    """
    Списать GTON с баланса.
    
    Args:
        user_id: ID пользователя
        amount: Сумма в GTON (Decimal)
        reason: Описание (для истории)
        action: Действие сервиса (chat_message, voice, etc.)
        data: Дополнительные данные
    
    Returns:
        TransactionResult:
            - success: bool
            - transaction_id: int (если успешно)
            - new_balance: Decimal
            - error: str (если неуспешно)
    
    Пример:
        result = await self.core.deduct_balance(
            user_id, 
            Decimal("0.5"),  # 0.5 GTON
            reason="Сообщение AI",
            action="chat_message"
        )
    """

async def add_balance(
    self,
    user_id: int,
    amount: Decimal,
    wallet_type: str = "main",
    source: str = "",
    reason: str = ""
) -> TransactionResult:
    """
    Начислить GTON на баланс.
    
    Args:
        user_id: ID пользователя
        amount: Сумма в GTON (Decimal)
        wallet_type: "main" или "bonus"
        source: Источник (refund, bonus, admin, payment)
        reason: Описание
    
    Пример:
        await self.core.add_balance(
            user_id,
            Decimal("5.0"),  # 5 GTON
            source="bonus",
            reason="Бонус за регистрацию"
        )
    """

async def transfer_balance(
    self,
    user_id: int,
    from_wallet: str,
    to_wallet: str,
    amount: Decimal
) -> TransactionResult:
    """
    Перевод между кошельками пользователя.
    """

# ==================== КОНВЕРТАЦИЯ ВАЛЮТ ====================

async def convert_to_gton(self, amount: Decimal, currency: str) -> Optional[Decimal]:
    """
    Конвертировать любую валюту в GTON.
    
    Args:
        amount: Сумма в исходной валюте
        currency: Код валюты (RUB, USD, EUR, TON)
        
    Returns:
        Сумма в GTON или None при ошибке
    
    Цепочка конвертации: ANY → USD → TON → GTON
    """

async def convert_from_gton(self, gton_amount: Decimal, currency: str) -> Optional[Decimal]:
    """
    Конвертировать GTON в любую валюту.
    
    Args:
        gton_amount: Сумма в GTON
        currency: Целевая валюта
        
    Returns:
        Сумма в целевой валюте или None при ошибке
    """

async def get_gton_rates(self) -> dict[str, Decimal]:
    """
    Получить текущие курсы GTON.
    
    Returns:
        {"TON": Decimal("1.53"), "USD": Decimal("10.5"), "RUB": Decimal("1085.0")}
    """

async def format_gton(self, amount: Decimal, with_fiat: bool = True, fiat: str = "RUB") -> str:
    """
    Форматировать сумму GTON для отображения.
    
    Returns:
        "10.5 GTON (~1,085 ₽)" или "10.5 GTON"
    """

# ==================== РЕФЕРАЛЬНЫЕ КОМИССИИ ====================

# Комиссии начисляются АВТОМАТИЧЕСКИ при вызове deduct_balance()
# Не нужно вызывать отдельно — система сама:
# 1. Находит реферера пользователя
# 2. Рассчитывает комиссию (10% для обычных, 20% для партнёров)
# 3. Начисляет комиссию на баланс реферера
# 4. Сохраняет в историю (таблица commissions)

# Настройки комиссий (Settings):
# - referral.commission_enabled: true/false
# - referral.level1_percent: 10 (для обычных рефереров)
# - referral.partner_level1_percent: 20 (дефолт для партнёров)
# - Partner.level1_percent: индивидуальный % партнёра

async def freeze_balance(self, user_id: int, amount: int) -> bool:
    """
    Заморозить средства (для вывода).
    Замороженные средства нельзя потратить.
    """

async def unfreeze_balance(self, user_id: int, amount: int) -> bool:
    """
    Разморозить средства.
    """

async def check_daily_limit(self, user_id: int, amount: int) -> bool:
    """
    Проверить, не превышен ли дневной лимит.
    
    Returns:
        True если лимит не превышен (можно списать)
    """
```

### Транзакции

```python
async def get_transactions(
    self,
    user_id: int,
    wallet_type: str = None,
    type: str = None,
    limit: int = 50,
    offset: int = 0
) -> list[TransactionDTO]:
    """
    Получить историю транзакций.
    
    Args:
        user_id: ID пользователя
        wallet_type: Фильтр по кошельку
        type: Фильтр по типу (deposit, usage, etc.)
        limit: Лимит записей
        offset: Смещение
    """

async def get_transaction(self, transaction_id: int) -> Optional[TransactionDTO]:
    """
    Получить транзакцию по ID.
    """
```

### Рефералы

```python
async def get_referrer(self, user_id: int) -> Optional[int]:
    """
    Получить ID того, кто пригласил пользователя.
    
    Returns:
        user_id реферера или None
    """

async def get_referrals(
    self, 
    user_id: int, 
    level: int = 1,
    limit: int = 50
) -> list[ReferralDTO]:
    """
    Получить рефералов пользователя.
    
    Args:
        user_id: ID пользователя
        level: Уровень (1 = прямые, 2 = рефералы рефералов)
    """

async def add_referral_commission(
    self,
    referrer_id: int,
    amount: Decimal,
    from_user_id: int,
    source: str = ""
) -> bool:
    """
    Начислить реферальную комиссию.
    Обычно вызывается автоматически при deduct_balance.
    """
```

### Сервис-Пользователь

```python
async def get_user_service_data(self, user_id: int) -> UserServiceDTO:
    """
    Получить данные пользователя для текущего сервиса.
    
    Returns:
        UserServiceDTO:
            - role: str
            - settings: dict
            - subscription_plan: str
            - subscription_until: datetime
            - total_spent: int
            - usage_count: int
            - first_use_at: datetime
            - last_use_at: datetime
    """

async def set_user_service_settings(self, user_id: int, settings: dict):
    """
    Сохранить настройки пользователя для сервиса.
    
    Пример:
        await self.core.set_user_service_settings(user_id, {
            "voice_enabled": True,
            "voice_gender": "female"
        })
    """

async def get_user_service_settings(self, user_id: int) -> dict:
    """
    Получить настройки пользователя для сервиса.
    """

async def set_user_state(self, user_id: int, state: str, data: dict = None):
    """
    Установить состояние пользователя (FSM).
    
    Пример:
        await self.core.set_user_state(user_id, "waiting_message", {
            "session_id": 123
        })
    """

async def get_user_state(self, user_id: int) -> tuple[str, dict]:
    """
    Получить состояние пользователя.
    
    Returns:
        (state_name, state_data)
    """

async def clear_user_state(self, user_id: int):
    """
    Очистить состояние пользователя.
    """

async def set_user_role(self, user_id: int, role: str):
    """
    Установить роль пользователя в сервисе.
    
    Args:
        role: "user", "vip", "moderator", "admin"
    """

async def check_subscription(self, user_id: int) -> SubscriptionDTO:
    """
    Проверить подписку пользователя.
    
    Returns:
        SubscriptionDTO:
            - is_active: bool
            - plan: str
            - expires_at: datetime
            - auto_renew: bool
    """

async def activate_subscription(
    self,
    user_id: int,
    plan: str,
    days: int,
    price: int
) -> bool:
    """
    Активировать подписку.
    
    Args:
        user_id: ID пользователя
        plan: Название плана
        days: Длительность в днях
        price: Цена в токенах (будет списана)
    """
```

### Уведомления

```python
async def send_notification(
    self,
    user_id: int,
    text: str,
    title: str = None,
    type: str = "info",
    action_url: str = None,
    action_text: str = None,
    schedule_at: datetime = None
) -> bool:
    """
    Отправить уведомление пользователю.
    
    Args:
        user_id: ID пользователя
        text: Текст уведомления
        title: Заголовок (опционально)
        type: "info", "warning", "success", "error"
        action_url: Deep link или callback
        action_text: Текст кнопки
        schedule_at: Когда отправить (None = сразу)
    """

async def send_message(
    self,
    user_id: int,
    text: str,
    keyboard: list = None,
    parse_mode: str = "HTML"
) -> bool:
    """
    Отправить сообщение напрямую через платформу.
    
    Args:
        user_id: ID пользователя
        text: Текст сообщения
        keyboard: Inline клавиатура
        parse_mode: "HTML" или "Markdown"
    """
```

### Аналитика

```python
async def track_event(
    self,
    event_name: str,
    user_id: int = None,
    label: str = None,
    value: int = None,
    properties: dict = None
):
    """
    Записать событие для аналитики.
    
    Args:
        event_name: Название события (session_started, message_sent)
        user_id: ID пользователя
        label: Дополнительная метка
        value: Числовое значение
        properties: Произвольные данные
    
    Примечание:
        Событие автоматически получает префикс сервиса:
        "message_sent" → "service:ai_psychologist:message_sent"
    """
```

### Настройки

```python
async def get_setting(self, key: str, default: Any = None) -> Any:
    """
    Получить глобальную настройку.
    
    Args:
        key: Ключ настройки (tokens.rate_rub, referral.enabled)
        default: Значение по умолчанию
    """

async def get_service_config(self) -> dict:
    """
    Получить конфигурацию текущего сервиса.
    """

async def update_service_config(self, config: dict):
    """
    Обновить конфигурацию сервиса.
    """
```

### Платежи

```python
async def create_payment(
    self,
    user_id: int,
    amount_rub: Decimal,
    description: str = "",
    return_url: str = None
) -> PaymentDTO:
    """
    Создать платёж.
    
    Args:
        user_id: ID пользователя
        amount_rub: Сумма в рублях
        description: Описание платежа
        return_url: URL для возврата после оплаты
    
    Returns:
        PaymentDTO:
            - payment_id: str
            - payment_url: str (ссылка на оплату)
            - amount_rub: Decimal
            - tokens_amount: int (сколько токенов получит)
    """

async def get_payment_status(self, payment_id: str) -> PaymentStatusDTO:
    """
    Проверить статус платежа.
    
    Returns:
        PaymentStatusDTO:
            - status: "pending", "completed", "failed"
            - paid_at: datetime
    """
```

### Локализация

```python
async def get_user_language(self, user_id: int) -> str:
    """
    Получить язык пользователя.
    
    Returns:
        Код языка: "ru", "en", "de"
    """

async def get_text(self, user_id: int, path: str, **kwargs) -> str:
    """
    Получить локализованный текст ядра для пользователя.
    
    Args:
        user_id: ID пользователя
        path: Путь "SECTION.key" (например "COMMON.back")
        **kwargs: Параметры для форматирования
    
    Returns:
        Локализованный текст
    
    Example:
        back_btn = await self.core.get_text(user_id, "COMMON.back")
        # "◀️ Назад" (для ru) или "◀️ Back" (для en)
    """

async def get_enabled_languages(self) -> list[dict]:
    """
    Получить список включённых языков.
    
    Returns:
        [{"code": "ru", "name": "Русский", "flag": "🇷🇺"}, ...]
    """
```

### Рассылки

```python
async def create_broadcast(
    self,
    text: str,
    target: str = "service_users",
    filters: dict = None,
    buttons: list = None,
    schedule_at: datetime = None
) -> int:
    """
    Создать рассылку от имени сервиса.
    
    Args:
        text: Текст рассылки
        target: "service_users" (пользователи сервиса) или фильтр
        filters: Дополнительные фильтры
        buttons: Inline кнопки
        schedule_at: Когда отправить
    
    Returns:
        broadcast_id
    
    Примечание:
        Рассылка отправляется только пользователям текущего сервиса.
    """
```

---

## DTO (Data Transfer Objects)

```python
@dataclass
class UserDTO:
    id: int
    telegram_id: int
    telegram_username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    language: str
    role: str
    is_active: bool
    is_blocked: bool
    created_at: datetime
    last_activity_at: Optional[datetime]

@dataclass
class TransactionResult:
    success: bool
    transaction_id: Optional[int] = None
    new_balance: Optional[Decimal] = None  # GTON
    error: Optional[str] = None

@dataclass
class TransactionDTO:
    id: int
    type: str  # "credit" или "debit"
    amount: Decimal  # GTON
    direction: str
    balance_after: Decimal  # GTON
    source: Optional[str]  # Источник (payment, bonus, referral, service)
    action: Optional[str]  # Действие сервиса
    description: Optional[str]
    created_at: datetime

@dataclass
class UserServiceDTO:
    role: str
    settings: dict
    subscription_plan: Optional[str]
    subscription_until: Optional[datetime]
    total_spent: Decimal  # GTON
    usage_count: int
    first_use_at: datetime
    last_use_at: Optional[datetime]

@dataclass
class SubscriptionDTO:
    is_active: bool
    plan: Optional[str]
    expires_at: Optional[datetime]
    auto_renew: bool
    days_left: int

@dataclass
class ReferralDTO:
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    level: int
    total_payments: Decimal
    total_commission: Decimal
    created_at: datetime

@dataclass
class PaymentDTO:
    payment_id: str
    payment_url: str
    amount_rub: Decimal
    tokens_amount: int

@dataclass
class PaymentStatusDTO:
    status: str  # pending, completed, failed
    paid_at: Optional[datetime]
```

---

## Права (Permissions)

Сервис должен объявить требуемые права:

```python
class MyService(BaseService):
    @property
    def permissions(self) -> list[str]:
        return [
            "balance:read",
            "balance:deduct",
            "notifications:send",
            "analytics:track"
        ]
```

Доступные права:

| Право | Описание |
|-------|----------|
| `balance:read` | Читать баланс |
| `balance:deduct` | Списывать с баланса |
| `balance:add` | Начислять на баланс |
| `users:read` | Читать данные пользователей |
| `users:write` | Изменять данные пользователей |
| `notifications:send` | Отправлять уведомления |
| `notifications:schedule` | Планировать уведомления |
| `referrals:read` | Читать реферальные данные |
| `referrals:commission` | Начислять комиссии |
| `payments:create` | Создавать платежи |
| `payments:read` | Читать историю платежей |
| `analytics:track` | Записывать события |
| `analytics:read` | Читать аналитику |
| `broadcasts:send` | Отправлять рассылки |
| `subscriptions:manage` | Управлять подписками |
