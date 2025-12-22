# Мультиязычность FuBot

## Обзор

Система локализации позволяет:
- Поддерживать несколько языков
- Включать/отключать языки через админку
- Хранить переводы в отдельных файлах
- Сервисам иметь свои переводы

---

## Структура файлов ядра

```
core/
└── locales/
    ├── __init__.py         # Загрузчик локализаций
    ├── base.py             # Базовый класс
    ├── ru.py               # Русский (основной)
    ├── en.py               # Английский
    └── de.py               # Немецкий
```

---

## Формат файла локализации

### core/locales/ru.py

```python
"""
Русская локализация (основная)
"""

# Метаданные языка
LANGUAGE_CODE = "ru"
LANGUAGE_NAME = "Русский"
LANGUAGE_FLAG = "🇷🇺"

# ==================== ОБЩИЕ ====================

COMMON = {
    "back": "◀️ Назад",
    "cancel": "❌ Отмена",
    "confirm": "✅ Подтвердить",
    "yes": "Да",
    "no": "Нет",
    "save": "💾 Сохранить",
    "delete": "🗑 Удалить",
    "edit": "✏️ Редактировать",
    "loading": "⏳ Загрузка...",
    "error": "❌ Произошла ошибка",
    "success": "✅ Успешно!",
    "not_found": "Не найдено",
}

# ==================== ГЛАВНОЕ МЕНЮ ====================

MAIN_MENU = {
    "title": "🏠 <b>Главное меню</b>",
    "balance": "💰 Баланс: {balance} токенов",
    "top_up": "💳 Пополнить",
    "settings": "⚙️ Настройки",
    "help": "❓ Помощь",
    "partner": "🤝 Партнёрская программа",
}

# ==================== ПОПОЛНЕНИЕ ====================

TOP_UP = {
    "title": "💳 <b>Пополнение баланса</b>",
    "current_balance": "Текущий баланс: {balance} токенов",
    "rate": "Курс: 1 токен = {rate} ₽",
    "select_amount": "Выберите сумму:",
    "custom_amount": "💬 Другая сумма",
    "enter_amount": "Введите сумму в рублях:",
    "min_amount": "Минимальная сумма: {min} ₽",
    "max_amount": "Максимальная сумма: {max} ₽",
    "invalid_amount": "❌ Некорректная сумма",
    
    # Методы оплаты
    "select_method": "Выберите способ оплаты:",
    "method_card": "💳 Банковская карта",
    "method_sbp": "📱 СБП",
    "method_yoomoney": "🟡 ЮMoney",
    "method_crypto": "₿ Криптовалюта",
    
    # Результат
    "payment_created": "🔗 Ссылка на оплату создана",
    "payment_success": "✅ Оплата прошла успешно!\n\n💰 Зачислено: {tokens} токенов",
    "payment_failed": "❌ Ошибка оплаты",
    "payment_pending": "⏳ Ожидание оплаты...",
}

# ==================== НАСТРОЙКИ ====================

SETTINGS = {
    "title": "⚙️ <b>Настройки</b>",
    "language": "🌐 Язык",
    "language_current": "Текущий язык: {language}",
    "language_select": "Выберите язык:",
    "language_changed": "✅ Язык изменён на {language}",
    "notifications": "🔔 Уведомления",
    "notifications_on": "Уведомления включены",
    "notifications_off": "Уведомления отключены",
}

# ==================== ПАРТНЁРКА ====================

PARTNER = {
    "title": "🤝 <b>Партнёрская программа</b>",
    "description": "Приглашайте друзей и получайте {percent}% от их платежей!",
    
    # Статистика
    "stats_title": "📊 Ваша статистика:",
    "stats_referrals": "Рефералов: {count}",
    "stats_earned": "Заработано: {amount} ₽",
    "stats_available": "Доступно к выводу: {amount} ₽",
    
    # Ссылка
    "your_link": "🔗 Ваша ссылка:",
    "link_copied": "✅ Ссылка скопирована",
    
    # Меню
    "my_referrals": "📋 Мои рефералы",
    "withdraw": "💸 Вывести средства",
    "become_partner": "💰 Стать партнёром",
    "partner_cabinet": "🤝 Партнёрский кабинет",
    
    # Заявка
    "application_title": "📝 <b>Заявка на партнёрство</b>",
    "application_text": "Расскажите о себе и как планируете привлекать пользователей:",
    "application_sent": "✅ Заявка отправлена!\n\nМы рассмотрим её в ближайшее время.",
    "application_pending": "⏳ Ваша заявка на рассмотрении",
    
    # Вывод
    "withdraw_title": "💸 <b>Вывод средств</b>",
    "withdraw_available": "Доступно: {amount} ₽",
    "withdraw_min": "Минимальная сумма: {min} ₽",
    "withdraw_enter_amount": "Введите сумму для вывода:",
    "withdraw_select_method": "Выберите способ вывода:",
    "withdraw_enter_details": "Введите реквизиты ({method}):",
    "withdraw_confirm": "Подтвердите вывод:\n\nСумма: {amount} ₽\nМетод: {method}\nРеквизиты: {details}",
    "withdraw_success": "✅ Заявка на вывод создана!\n\nОжидайте обработки.",
    "withdraw_insufficient": "❌ Недостаточно средств",
}

# ==================== ПОМОЩЬ ====================

HELP = {
    "title": "❓ <b>Помощь</b>",
    "description": "Если у вас возникли вопросы, свяжитесь с поддержкой:",
    "support": "📩 Написать в поддержку",
    "faq": "📖 Частые вопросы",
}

# ==================== ОШИБКИ ====================

ERRORS = {
    "not_enough_balance": "❌ Недостаточно токенов!\n\nНужно: {required}\nУ вас: {balance}",
    "user_blocked": "🚫 Ваш аккаунт заблокирован.\n\nПричина: {reason}",
    "rate_limit": "⏳ Слишком много запросов. Подождите немного.",
    "maintenance": "🔧 Бот на обслуживании. Попробуйте позже.",
    "unknown_command": "❓ Неизвестная команда",
    "invalid_input": "❌ Некорректный ввод",
}

# ==================== АДМИНКА ====================

ADMIN = {
    "title": "🔧 <b>Админ-панель</b>",
    "partners": "👥 Партнёры",
    "statistics": "📊 Статистика",
    "broadcast": "📢 Рассылка",
    "settings": "⚙️ Настройки",
    "services": "📦 Сервисы",
    "users": "👤 Пользователи",
    
    # Партнёры
    "partners_list": "📋 Список партнёров",
    "partners_applications": "📝 Заявки",
    "partners_payouts": "💸 Заявки на вывод",
    
    # Статистика
    "stats_users_total": "Всего пользователей: {count}",
    "stats_users_today": "Новых сегодня: {count}",
    "stats_users_active": "Активных: {count}",
    "stats_revenue_today": "Выручка сегодня: {amount} ₽",
    "stats_revenue_month": "Выручка за месяц: {amount} ₽",
    
    # Рассылка
    "broadcast_title": "📢 <b>Рассылка</b>",
    "broadcast_enter_text": "Введите текст рассылки:",
    "broadcast_select_target": "Выберите аудиторию:",
    "broadcast_target_all": "Все пользователи",
    "broadcast_target_active": "Активные (7 дней)",
    "broadcast_confirm": "Отправить рассылку?\n\nПолучателей: {count}",
    "broadcast_started": "✅ Рассылка запущена",
    "broadcast_progress": "📤 Отправлено: {sent}/{total}",
    "broadcast_completed": "✅ Рассылка завершена\n\nДоставлено: {delivered}\nОшибок: {failed}",
    
    # Языки
    "languages_title": "🌐 <b>Управление языками</b>",
    "languages_available": "Доступные языки:",
    "language_enabled": "✅ {name} — включён",
    "language_disabled": "❌ {name} — отключён",
    "language_enable": "Включить",
    "language_disable": "Отключить",
    "language_default": "🔹 По умолчанию",
    "language_set_default": "Сделать по умолчанию",
}

# ==================== УВЕДОМЛЕНИЯ ====================

NOTIFICATIONS = {
    "low_balance": "⚠️ У вас заканчиваются токены!\n\nБаланс: {balance} токенов",
    "subscription_expiring": "⏰ Ваша подписка истекает через {days} дн.\n\nПродлите, чтобы не потерять доступ.",
    "subscription_expired": "❌ Ваша подписка истекла.\n\nПродлите для продолжения использования.",
    "payment_received": "💰 Получен платёж!\n\nСумма: {amount} ₽\nЗачислено: {tokens} токенов",
    "referral_registered": "🎉 По вашей ссылке зарегистрировался новый пользователь!",
    "referral_payment": "💰 Ваш реферал совершил платёж!\n\nВаша комиссия: {commission} ₽",
    "payout_completed": "✅ Выплата выполнена!\n\nСумма: {amount} ₽\nМетод: {method}",
    "payout_rejected": "❌ Заявка на выплату отклонена.\n\nПричина: {reason}",
}
```

### core/locales/en.py

```python
"""
English localization
"""

LANGUAGE_CODE = "en"
LANGUAGE_NAME = "English"
LANGUAGE_FLAG = "🇬🇧"

COMMON = {
    "back": "◀️ Back",
    "cancel": "❌ Cancel",
    "confirm": "✅ Confirm",
    "yes": "Yes",
    "no": "No",
    "save": "💾 Save",
    "delete": "🗑 Delete",
    "edit": "✏️ Edit",
    "loading": "⏳ Loading...",
    "error": "❌ An error occurred",
    "success": "✅ Success!",
    "not_found": "Not found",
}

MAIN_MENU = {
    "title": "🏠 <b>Main Menu</b>",
    "balance": "💰 Balance: {balance} tokens",
    "top_up": "💳 Top Up",
    "settings": "⚙️ Settings",
    "help": "❓ Help",
    "partner": "🤝 Partner Program",
}

TOP_UP = {
    "title": "💳 <b>Top Up Balance</b>",
    "current_balance": "Current balance: {balance} tokens",
    "rate": "Rate: 1 token = {rate} ₽",
    "select_amount": "Select amount:",
    "custom_amount": "💬 Custom amount",
    "enter_amount": "Enter amount in rubles:",
    "min_amount": "Minimum amount: {min} ₽",
    "max_amount": "Maximum amount: {max} ₽",
    "invalid_amount": "❌ Invalid amount",
    "select_method": "Select payment method:",
    "method_card": "💳 Bank Card",
    "method_sbp": "📱 SBP",
    "method_yoomoney": "🟡 YooMoney",
    "method_crypto": "₿ Cryptocurrency",
    "payment_created": "🔗 Payment link created",
    "payment_success": "✅ Payment successful!\n\n💰 Credited: {tokens} tokens",
    "payment_failed": "❌ Payment failed",
    "payment_pending": "⏳ Waiting for payment...",
}

SETTINGS = {
    "title": "⚙️ <b>Settings</b>",
    "language": "🌐 Language",
    "language_current": "Current language: {language}",
    "language_select": "Select language:",
    "language_changed": "✅ Language changed to {language}",
    "notifications": "🔔 Notifications",
    "notifications_on": "Notifications enabled",
    "notifications_off": "Notifications disabled",
}

PARTNER = {
    "title": "🤝 <b>Partner Program</b>",
    "description": "Invite friends and get {percent}% of their payments!",
    "stats_title": "📊 Your statistics:",
    "stats_referrals": "Referrals: {count}",
    "stats_earned": "Earned: {amount} ₽",
    "stats_available": "Available for withdrawal: {amount} ₽",
    "your_link": "🔗 Your link:",
    "link_copied": "✅ Link copied",
    "my_referrals": "📋 My Referrals",
    "withdraw": "💸 Withdraw",
    "become_partner": "💰 Become a Partner",
    "partner_cabinet": "🤝 Partner Dashboard",
    "application_title": "📝 <b>Partnership Application</b>",
    "application_text": "Tell us about yourself and how you plan to attract users:",
    "application_sent": "✅ Application sent!\n\nWe will review it shortly.",
    "application_pending": "⏳ Your application is under review",
    "withdraw_title": "💸 <b>Withdrawal</b>",
    "withdraw_available": "Available: {amount} ₽",
    "withdraw_min": "Minimum amount: {min} ₽",
    "withdraw_enter_amount": "Enter withdrawal amount:",
    "withdraw_select_method": "Select withdrawal method:",
    "withdraw_enter_details": "Enter details ({method}):",
    "withdraw_confirm": "Confirm withdrawal:\n\nAmount: {amount} ₽\nMethod: {method}\nDetails: {details}",
    "withdraw_success": "✅ Withdrawal request created!\n\nPlease wait for processing.",
    "withdraw_insufficient": "❌ Insufficient funds",
}

HELP = {
    "title": "❓ <b>Help</b>",
    "description": "If you have questions, contact support:",
    "support": "📩 Contact Support",
    "faq": "📖 FAQ",
}

ERRORS = {
    "not_enough_balance": "❌ Not enough tokens!\n\nRequired: {required}\nYou have: {balance}",
    "user_blocked": "🚫 Your account is blocked.\n\nReason: {reason}",
    "rate_limit": "⏳ Too many requests. Please wait.",
    "maintenance": "🔧 Bot is under maintenance. Try again later.",
    "unknown_command": "❓ Unknown command",
    "invalid_input": "❌ Invalid input",
}

# ... остальные секции аналогично
```

---

## Загрузчик локализаций

### core/locales/__init__.py

```python
"""
Система локализации FuBot
"""
from typing import Dict, Any, Optional
from importlib import import_module
import os

# Доступные языки
AVAILABLE_LANGUAGES = {
    "ru": "core.locales.ru",
    "en": "core.locales.en",
    "de": "core.locales.de",
}

# Кэш загруженных локализаций
_locales_cache: Dict[str, Any] = {}


def load_locale(lang_code: str) -> Any:
    """Загрузить модуль локализации"""
    if lang_code in _locales_cache:
        return _locales_cache[lang_code]
    
    if lang_code not in AVAILABLE_LANGUAGES:
        lang_code = "ru"  # Fallback
    
    module = import_module(AVAILABLE_LANGUAGES[lang_code])
    _locales_cache[lang_code] = module
    return module


def get_text(
    lang_code: str, 
    section: str, 
    key: str, 
    **kwargs
) -> str:
    """
    Получить локализованный текст.
    
    Args:
        lang_code: Код языка (ru, en, de)
        section: Секция (MAIN_MENU, TOP_UP, etc.)
        key: Ключ в секции
        **kwargs: Параметры для форматирования
    
    Returns:
        Локализованный текст
    
    Example:
        get_text("ru", "MAIN_MENU", "balance", balance=100)
        # "💰 Баланс: 100 токенов"
    """
    locale = load_locale(lang_code)
    
    # Получаем секцию
    section_dict = getattr(locale, section, None)
    if section_dict is None:
        # Fallback на русский
        locale = load_locale("ru")
        section_dict = getattr(locale, section, {})
    
    # Получаем текст
    text = section_dict.get(key, f"[{section}.{key}]")
    
    # Форматируем
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text


def t(lang: str, path: str, **kwargs) -> str:
    """
    Короткий алиас для get_text.
    
    Args:
        lang: Код языка
        path: Путь в формате "SECTION.key"
        **kwargs: Параметры
    
    Example:
        t("ru", "MAIN_MENU.balance", balance=100)
    """
    parts = path.split(".", 1)
    if len(parts) != 2:
        return f"[{path}]"
    
    return get_text(lang, parts[0], parts[1], **kwargs)


def get_language_info(lang_code: str) -> dict:
    """Получить информацию о языке"""
    locale = load_locale(lang_code)
    return {
        "code": getattr(locale, "LANGUAGE_CODE", lang_code),
        "name": getattr(locale, "LANGUAGE_NAME", lang_code),
        "flag": getattr(locale, "LANGUAGE_FLAG", "🏳️"),
    }


def get_available_languages() -> list[dict]:
    """Получить список доступных языков"""
    return [get_language_info(code) for code in AVAILABLE_LANGUAGES.keys()]
```

---

## Использование в ядре

### В хендлерах

```python
from core.locales import t, get_text

async def show_main_menu(user_id: int, lang: str = "ru"):
    balance = await get_balance(user_id)
    
    text = t(lang, "MAIN_MENU.title") + "\n\n"
    text += t(lang, "MAIN_MENU.balance", balance=balance)
    
    keyboard = [
        [{"text": t(lang, "MAIN_MENU.top_up"), "callback_data": "top_up"}],
        [{"text": t(lang, "MAIN_MENU.settings"), "callback_data": "settings"}],
        [{"text": t(lang, "MAIN_MENU.help"), "callback_data": "help"}],
        [{"text": t(lang, "MAIN_MENU.partner"), "callback_data": "partner"}],
    ]
    
    return text, keyboard
```

### В сервисах (через CoreAPI)

```python
class CoreAPI:
    async def get_text(
        self, 
        user_id: int, 
        path: str, 
        **kwargs
    ) -> str:
        """
        Получить локализованный текст для пользователя.
        
        Args:
            user_id: ID пользователя
            path: Путь "SECTION.key"
            **kwargs: Параметры
        """
        user = await self.get_user_by_id(user_id)
        lang = user.language if user else "ru"
        return t(lang, path, **kwargs)
    
    async def get_user_language(self, user_id: int) -> str:
        """Получить язык пользователя"""
        user = await self.get_user_by_id(user_id)
        return user.language if user else "ru"
```

---

## Настройки языков в БД

### Таблица settings

```python
# Включённые языки (JSON массив)
"localization.enabled_languages": '["ru", "en"]'

# Язык по умолчанию
"localization.default_language": "ru"

# Показывать выбор языка при регистрации
"localization.show_on_registration": "true"
```

### Админка: Управление языками

```
🌐 Управление языками

Доступные языки:

✅ 🇷🇺 Русский — включён (по умолчанию)
✅ 🇬🇧 English — включён
❌ 🇩🇪 Deutsch — отключён

┌─────────────────────────┐
│ 🇷🇺 Русский             │
├─────────────────────────┤
│ 🇬🇧 English             │
├─────────────────────────┤
│ 🇩🇪 Deutsch             │
├─────────────────────────┤
│ ◀️ Назад                │
└─────────────────────────┘
```

При нажатии на язык:

```
🇬🇧 English

Статус: ✅ Включён

┌─────────────────────────┐
│ ❌ Отключить            │
├─────────────────────────┤
│ ⭐ Сделать по умолчанию │
├─────────────────────────┤
│ ◀️ Назад                │
└─────────────────────────┘
```

---

## Выбор языка пользователем

### При регистрации (если включено)

```
🌐 Выберите язык / Select language:

┌─────────────────────────┐
│ 🇷🇺 Русский             │
├─────────────────────────┤
│ 🇬🇧 English             │
└─────────────────────────┘
```

### В настройках

```
⚙️ Настройки

🌐 Текущий язык: Русский

┌─────────────────────────┐
│ 🌐 Изменить язык        │
├─────────────────────────┤
│ 🔔 Уведомления          │
├─────────────────────────┤
│ ◀️ Назад                │
└─────────────────────────┘
```

---

## Добавление нового языка

1. Создать файл `core/locales/{code}.py`
2. Скопировать структуру из `ru.py`
3. Перевести все тексты
4. Добавить в `AVAILABLE_LANGUAGES` в `__init__.py`
5. Включить через админку

```python
# core/locales/de.py
LANGUAGE_CODE = "de"
LANGUAGE_NAME = "Deutsch"
LANGUAGE_FLAG = "🇩🇪"

COMMON = {
    "back": "◀️ Zurück",
    "cancel": "❌ Abbrechen",
    # ...
}
```
