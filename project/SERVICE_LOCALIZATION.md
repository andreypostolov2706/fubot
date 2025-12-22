# Локализация сервиса

## Структура файлов сервиса с локализацией

```
services/
└── ai_psychologist/
    ├── service.py
    ├── config.py
    ├── database/
    │   └── ...
    ├── handlers/
    │   └── ...
    │
    ├── locales/                    # 🌐 Локализации сервиса
    │   ├── __init__.py             # Загрузчик
    │   ├── ru.py                   # Русский
    │   ├── en.py                   # Английский
    │   └── de.py                   # Немецкий
    │
    ├── keyboards.py
    ├── install.bat
    └── requirements.txt
```

---

## Формат файла локализации сервиса

### locales/ru.py

```python
"""
AI Psychologist - Русская локализация
"""

LANGUAGE_CODE = "ru"

# ==================== ГЛАВНОЕ МЕНЮ СЕРВИСА ====================

MENU = {
    "title": "🧠 <b>ИИ-Психолог</b>",
    "description": "Ваш личный психолог на базе искусственного интеллекта.\nКонфиденциально и безопасно.",
    "balance": "💰 Баланс: {balance} токенов",
    
    # Кнопки
    "start_session": "💬 Начать сеанс",
    "my_sessions": "📋 Мои сеансы",
    "settings": "⚙️ Настройки",
}

# ==================== СЕССИЯ ====================

SESSION = {
    "starting": "🧠 Начинаю сеанс...",
    "started": "🧠 <b>Сеанс начат</b>\n\nРасскажите, что вас беспокоит. Я внимательно слушаю.",
    "ended": "✅ Сеанс завершён.\n\nСпасибо за доверие. Берегите себя! 💚",
    "continue_prompt": "Продолжайте, я слушаю...",
    
    # Кнопки
    "end_session": "🔚 Завершить сеанс",
    "voice_mode": "🎤 Голосовой режим",
    "text_mode": "💬 Текстовый режим",
    
    # Статистика сессии
    "session_stats": "📊 <b>Статистика сеанса</b>\n\nСообщений: {messages}\nДлительность: {duration} мин\nПотрачено: {tokens} токенов",
}

# ==================== МОИ СЕАНСЫ ====================

SESSIONS_LIST = {
    "title": "📋 <b>Мои сеансы</b>",
    "empty": "У вас пока нет сеансов.\n\nНачните первый сеанс!",
    "item": "📅 {date} — {messages} сообщ.",
    "total": "Всего сеансов: {count}",
    
    # Детали сессии
    "session_detail": "📋 <b>Сеанс от {date}</b>\n\nСообщений: {messages}\nДлительность: {duration} мин",
    "view_summary": "📝 Краткое содержание",
    "continue_session": "▶️ Продолжить",
    "delete_session": "🗑 Удалить",
    "delete_confirm": "Удалить этот сеанс?\n\nЭто действие нельзя отменить.",
    "deleted": "✅ Сеанс удалён",
}

# ==================== НАСТРОЙКИ ====================

SETTINGS = {
    "title": "⚙️ <b>Настройки ИИ-Психолога</b>",
    
    # Режим ответа
    "response_mode": "📝 Режим ответа",
    "mode_text": "💬 Текст",
    "mode_voice": "🎤 Голос",
    "mode_both": "💬🎤 Текст + Голос",
    
    # Голос
    "voice_settings": "🎙 Настройки голоса",
    "voice_gender": "Голос: {gender}",
    "voice_female": "👩 Женский",
    "voice_male": "👨 Мужской",
    "voice_speed": "Скорость: {speed}x",
    
    # Обращение
    "use_name": "Обращение по имени",
    "use_name_on": "✅ Включено",
    "use_name_off": "❌ Отключено",
    
    # Сохранение
    "saved": "✅ Настройки сохранены",
}

# ==================== ОШИБКИ ====================

ERRORS = {
    "not_enough_tokens": "❌ Недостаточно токенов для сеанса.\n\nМинимум: {required} токенов\nУ вас: {balance} токенов",
    "session_not_found": "❌ Сеанс не найден",
    "ai_error": "😔 Произошла ошибка при обработке. Попробуйте ещё раз.",
    "voice_error": "❌ Не удалось обработать голосовое сообщение",
    "too_long": "⚠️ Сообщение слишком длинное. Максимум {max} символов.",
}

# ==================== УВЕДОМЛЕНИЯ ====================

NOTIFICATIONS = {
    "session_reminder": "🧠 Давно не виделись!\n\nКак ваши дела? Может, пора поговорить?",
    "tip_of_day": "💡 <b>Совет дня</b>\n\n{tip}",
}

# ==================== АДМИНКА СЕРВИСА ====================

ADMIN = {
    "title": "🧠 <b>ИИ-Психолог — Админ</b>",
    "stats_title": "📊 Статистика:",
    "stats_users": "Пользователей: {count}",
    "stats_sessions_today": "Сессий сегодня: {count}",
    "stats_messages_today": "Сообщений сегодня: {count}",
    "stats_revenue": "Выручка (токены): {amount}",
    
    # Меню
    "detailed_stats": "📊 Детальная статистика",
    "ai_settings": "🤖 Настройки ИИ",
    "pricing": "💰 Тарифы",
    "broadcast": "📢 Рассылка",
}
```

### locales/en.py

```python
"""
AI Psychologist - English localization
"""

LANGUAGE_CODE = "en"

MENU = {
    "title": "🧠 <b>AI Psychologist</b>",
    "description": "Your personal AI-powered psychologist.\nConfidential and secure.",
    "balance": "💰 Balance: {balance} tokens",
    "start_session": "💬 Start Session",
    "my_sessions": "📋 My Sessions",
    "settings": "⚙️ Settings",
}

SESSION = {
    "starting": "🧠 Starting session...",
    "started": "🧠 <b>Session Started</b>\n\nTell me what's on your mind. I'm listening.",
    "ended": "✅ Session ended.\n\nThank you for your trust. Take care! 💚",
    "continue_prompt": "Please continue, I'm listening...",
    "end_session": "🔚 End Session",
    "voice_mode": "🎤 Voice Mode",
    "text_mode": "💬 Text Mode",
    "session_stats": "📊 <b>Session Stats</b>\n\nMessages: {messages}\nDuration: {duration} min\nSpent: {tokens} tokens",
}

SESSIONS_LIST = {
    "title": "📋 <b>My Sessions</b>",
    "empty": "You don't have any sessions yet.\n\nStart your first session!",
    "item": "📅 {date} — {messages} msgs",
    "total": "Total sessions: {count}",
    "session_detail": "📋 <b>Session from {date}</b>\n\nMessages: {messages}\nDuration: {duration} min",
    "view_summary": "📝 Summary",
    "continue_session": "▶️ Continue",
    "delete_session": "🗑 Delete",
    "delete_confirm": "Delete this session?\n\nThis action cannot be undone.",
    "deleted": "✅ Session deleted",
}

SETTINGS = {
    "title": "⚙️ <b>AI Psychologist Settings</b>",
    "response_mode": "📝 Response Mode",
    "mode_text": "💬 Text",
    "mode_voice": "🎤 Voice",
    "mode_both": "💬🎤 Text + Voice",
    "voice_settings": "🎙 Voice Settings",
    "voice_gender": "Voice: {gender}",
    "voice_female": "👩 Female",
    "voice_male": "👨 Male",
    "voice_speed": "Speed: {speed}x",
    "use_name": "Use my name",
    "use_name_on": "✅ Enabled",
    "use_name_off": "❌ Disabled",
    "saved": "✅ Settings saved",
}

ERRORS = {
    "not_enough_tokens": "❌ Not enough tokens for session.\n\nMinimum: {required} tokens\nYou have: {balance} tokens",
    "session_not_found": "❌ Session not found",
    "ai_error": "😔 An error occurred. Please try again.",
    "voice_error": "❌ Failed to process voice message",
    "too_long": "⚠️ Message too long. Maximum {max} characters.",
}

NOTIFICATIONS = {
    "session_reminder": "🧠 Long time no see!\n\nHow are you doing? Maybe it's time to talk?",
    "tip_of_day": "💡 <b>Tip of the Day</b>\n\n{tip}",
}

ADMIN = {
    "title": "🧠 <b>AI Psychologist — Admin</b>",
    "stats_title": "📊 Statistics:",
    "stats_users": "Users: {count}",
    "stats_sessions_today": "Sessions today: {count}",
    "stats_messages_today": "Messages today: {count}",
    "stats_revenue": "Revenue (tokens): {amount}",
    "detailed_stats": "📊 Detailed Stats",
    "ai_settings": "🤖 AI Settings",
    "pricing": "💰 Pricing",
    "broadcast": "📢 Broadcast",
}
```

---

## Загрузчик локализаций сервиса

### locales/__init__.py

```python
"""
Локализация сервиса AI Psychologist
"""
from typing import Dict, Any
from importlib import import_module

# Доступные языки сервиса
AVAILABLE_LANGUAGES = {
    "ru": ".ru",
    "en": ".en",
    "de": ".de",
}

_cache: Dict[str, Any] = {}


def load_locale(lang_code: str):
    """Загрузить локализацию"""
    if lang_code in _cache:
        return _cache[lang_code]
    
    if lang_code not in AVAILABLE_LANGUAGES:
        lang_code = "ru"
    
    module = import_module(
        AVAILABLE_LANGUAGES[lang_code], 
        package=__package__
    )
    _cache[lang_code] = module
    return module


def t(lang: str, path: str, **kwargs) -> str:
    """
    Получить локализованный текст.
    
    Args:
        lang: Код языка
        path: Путь "SECTION.key"
        **kwargs: Параметры для форматирования
    
    Example:
        t("ru", "MENU.title")
        t("en", "SESSION.session_stats", messages=10, duration=15, tokens=50)
    """
    parts = path.split(".", 1)
    if len(parts) != 2:
        return f"[{path}]"
    
    section, key = parts
    locale = load_locale(lang)
    
    # Получаем секцию
    section_dict = getattr(locale, section, None)
    if section_dict is None:
        # Fallback на русский
        locale = load_locale("ru")
        section_dict = getattr(locale, section, {})
    
    # Получаем текст
    text = section_dict.get(key, f"[{path}]")
    
    # Форматируем
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text
```

---

## Использование в сервисе

### service.py

```python
from .locales import t

class AIPsychologistService(BaseService):
    
    async def handle_callback(self, user_id, action, params, context) -> Response:
        # Получаем язык пользователя через Core API
        lang = await self.core.get_user_language(user_id)
        
        if action == "main":
            return await self._show_main(user_id, lang)
        elif action == "start":
            return await self._start_session(user_id, lang)
        # ...
    
    async def _show_main(self, user_id: int, lang: str) -> Response:
        balance = await self.core.get_balance(user_id)
        
        text = t(lang, "MENU.title") + "\n\n"
        text += t(lang, "MENU.description") + "\n\n"
        text += t(lang, "MENU.balance", balance=balance)
        
        keyboard = [
            [{"text": t(lang, "MENU.start_session"), 
              "callback_data": f"service:{self.info.id}:start"}],
            [{"text": t(lang, "MENU.my_sessions"), 
              "callback_data": f"service:{self.info.id}:sessions"}],
            [{"text": t(lang, "MENU.settings"), 
              "callback_data": f"service:{self.info.id}:settings"}],
            [{"text": await self.core.get_text(user_id, "COMMON.back"), 
              "callback_data": "main_menu"}],
        ]
        
        return Response(text=text, keyboard=keyboard)
    
    async def _start_session(self, user_id: int, lang: str) -> Response:
        balance = await self.core.get_balance(user_id)
        min_tokens = 10
        
        if balance < min_tokens:
            return Response(
                text=t(lang, "ERRORS.not_enough_tokens", 
                       required=min_tokens, balance=balance),
                keyboard=[[{
                    "text": await self.core.get_text(user_id, "MAIN_MENU.top_up"),
                    "callback_data": "top_up"
                }]]
            )
        
        # Начинаем сессию...
        return Response(
            text=t(lang, "SESSION.started"),
            set_state="in_session",
            keyboard=[[{
                "text": t(lang, "SESSION.end_session"),
                "callback_data": f"service:{self.info.id}:end"
            }]]
        )
```

---

## Комбинирование с локализацией ядра

Сервис может использовать тексты из ядра через `CoreAPI`:

```python
# Текст из ядра (общие кнопки)
back_text = await self.core.get_text(user_id, "COMMON.back")
cancel_text = await self.core.get_text(user_id, "COMMON.cancel")

# Текст из сервиса
title = t(lang, "MENU.title")
```

---

## Чеклист локализации сервиса

- [ ] Создать папку `locales/` в сервисе
- [ ] Создать `locales/__init__.py` с функцией `t()`
- [ ] Создать `locales/ru.py` (основной язык)
- [ ] Создать `locales/en.py` (английский)
- [ ] Создать другие языки по необходимости
- [ ] Использовать `t(lang, "SECTION.key")` везде вместо хардкода
- [ ] Для общих кнопок использовать `self.core.get_text()`
- [ ] Получать язык через `await self.core.get_user_language(user_id)`

---

## Структура секций (рекомендация)

| Секция | Описание |
|--------|----------|
| `MENU` | Главное меню сервиса |
| `SESSION` | Тексты сессии/игры/процесса |
| `SETTINGS` | Настройки сервиса |
| `ERRORS` | Сообщения об ошибках |
| `NOTIFICATIONS` | Уведомления |
| `ADMIN` | Админка сервиса |

Можно добавлять свои секции по необходимости.
