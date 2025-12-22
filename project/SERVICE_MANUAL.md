# 📘 Методичка по созданию сервисов FuBot

## Что такое сервис?

**Сервис** — это подключаемый модуль, который расширяет функционал бота. Сервис имеет:
- Свою кнопку в главном меню
- Свою базу данных (опционально)
- Доступ к балансу пользователя через CoreAPI

**Примеры сервисов:**
- 🧠 ИИ-Психолог — чат с GPT
- 🎮 Игры — казино, слоты
- 📚 Курсы — обучающие материалы
- 🛒 Магазин — продажа цифровых товаров

---

## Архитектура взаимодействия

```
┌─────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │                    ЯДРО (core/)                  │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │    │
│  │  │ Баланс   │  │ Партнёры │  │ Пользователи │   │    │
│  │  │  GTON    │  │ Рефералы │  │   Настройки  │   │    │
│  │  └────┬─────┘  └──────────┘  └──────────────┘   │    │
│  │       │                                          │    │
│  │       ▼                                          │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │              CoreAPI                      │   │    │
│  │  │  • get_balance()    • set_user_state()   │   │    │
│  │  │  • deduct_balance() • track_event()      │   │    │
│  │  │  • add_balance()    • format_gton()      │   │    │
│  │  └────────────────┬─────────────────────────┘   │    │
│  └───────────────────┼─────────────────────────────┘    │
│                      │                                   │
│  ┌───────────────────▼─────────────────────────────┐    │
│  │              СЕРВИСЫ (services/)                 │    │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────┐   │    │
│  │  │ИИ-Психолог │  │   Игры     │  │  Курсы   │   │    │
│  │  │  своя БД   │  │  своя БД   │  │ своя БД  │   │    │
│  │  └────────────┘  └────────────┘  └──────────┘   │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Быстрый старт: Минимальный сервис

### 1. Создайте структуру папок

```
services/
└── my_service/
    ├── __init__.py          # Пустой файл
    ├── service.py           # Главный класс
    └── requirements.txt     # Зависимости (может быть пустым)
```

### 2. Создайте service.py

```python
"""
My Service — Минимальный пример сервиса
"""
from decimal import Decimal
from core.plugins.base_service import (
    BaseService, ServiceInfo, MenuItem, Response,
    UserServiceDTO, CallbackContext, MessageContext, MessageDTO
)
from core.plugins.core_api import CoreAPI


class MyService(BaseService):
    """Минимальный сервис"""
    
    @property
    def info(self) -> ServiceInfo:
        return ServiceInfo(
            id="my_service",           # Уникальный ID (латиница, snake_case)
            name="Мой Сервис",         # Название для отображения
            description="Описание",    # Краткое описание
            version="1.0.0",
            author="Автор",
            icon="🎮"                  # Эмодзи для меню
        )
    
    async def install(self) -> bool:
        """Вызывается при установке сервиса"""
        return True
    
    async def uninstall(self) -> bool:
        """Вызывается при удалении сервиса"""
        return True
    
    def get_user_menu_items(self, user_id: int, user_data: UserServiceDTO) -> list[MenuItem]:
        """Кнопка в главном меню"""
        return [
            MenuItem(
                text=f"{self.info.icon} {self.info.name}",
                callback=f"service:{self.info.id}:main",
                order=100  # Порядок сортировки (меньше = выше)
            )
        ]
    
    def get_admin_menu_items(self) -> list[MenuItem]:
        """Кнопка в админ-панели"""
        return []
    
    async def handle_callback(
        self, 
        user_id: int, 
        action: str, 
        params: dict,
        context: CallbackContext
    ) -> Response:
        """
        Обработка нажатия кнопки.
        
        Callback "service:my_service:main" → action="main", params={}
        Callback "service:my_service:play:123" → action="play", params={"id": "123"}
        """
        if action == "main":
            return await self._show_main(user_id)
        
        return Response(text="❌ Неизвестное действие")
    
    async def handle_message(
        self,
        user_id: int,
        message: MessageDTO,
        context: MessageContext
    ) -> Response:
        """Обработка текстового сообщения (когда пользователь в состоянии сервиса)"""
        return Response(text="Используйте кнопки меню")
    
    # === Приватные методы ===
    
    async def _show_main(self, user_id: int) -> Response:
        """Главный экран сервиса"""
        # Получаем баланс с фиатным эквивалентом
        balance = await self.core.get_balance(user_id)
        balance_str = await self.core.format_gton(balance, with_fiat=True)
        
        text = f"""
{self.info.icon} <b>{self.info.name}</b>

💰 Ваш баланс: {balance_str}

Добро пожаловать в сервис!
"""
        
        keyboard = [
            [{"text": "🎯 Действие", "callback_data": f"service:{self.info.id}:action"}],
            [{"text": "◀️ Назад", "callback_data": "main_menu"}]
        ]
        
        return Response(text=text, keyboard=keyboard)
```

### 3. Зарегистрируйте сервис

В файле `services/__init__.py` добавьте:

```python
from .my_service.service import MyService
```

---

## CoreAPI — Все доступные методы

### 💰 Работа с балансом

```python
from decimal import Decimal

# Получить баланс (GTON)
balance = await self.core.get_balance(user_id)
# → Decimal("125.500000")

# Получить баланс с фиатом
gton, rub = await self.core.get_balance_with_fiat(user_id, "RUB")
# → (Decimal("125.5"), Decimal("12550.0"))

# Форматировать для отображения
text = await self.core.format_gton(balance, with_fiat=True)
# → "125.5 GTON (~12,550 ₽)"

# Списать GTON
result = await self.core.deduct_balance(
    user_id=user_id,
    amount=Decimal("0.5"),      # Сумма в GTON
    reason="Отправка сообщения", # Описание для истории
    action="chat_message"        # Тип действия
)

if result.success:
    print(f"Списано! Новый баланс: {result.new_balance}")
else:
    print(f"Ошибка: {result.error}")
    # Возможные ошибки:
    # - "Insufficient balance" — недостаточно средств
    # - "Wallet not found" — кошелёк не найден
    # - "Invalid amount" — некорректная сумма

# Начислить GTON (например, возврат)
result = await self.core.add_balance(
    user_id=user_id,
    amount=Decimal("1.0"),
    source="refund",
    reason="Возврат за ошибку"
)
```

### 🔄 Конвертация валют

```python
from decimal import Decimal

# RUB → GTON
gton = await self.core.convert_to_gton(Decimal("100"), "RUB")
# → Decimal("1.0")

# GTON → RUB
rub = await self.core.convert_from_gton(Decimal("1.0"), "RUB")
# → Decimal("100.0")

# Текущие курсы
rates = await self.core.get_gton_rates()
# → {"TON": Decimal("1.53"), "USD": Decimal("10.0"), "RUB": Decimal("1000.0")}
```

### 📝 FSM — Состояния пользователя

```python
# Установить состояние
await self.core.set_user_state(
    user_id=user_id,
    state="waiting_message",
    data={"session_id": 123, "step": 1}
)

# Получить состояние
state, data = await self.core.get_user_state(user_id)
# state = "waiting_message"
# data = {"session_id": 123, "step": 1}

# Очистить состояние
await self.core.clear_user_state(user_id)
```

**Использование в Response:**

```python
# Установить состояние через Response
return Response(
    text="Введите ваше сообщение:",
    set_state="waiting_input",
    state_data={"context": "greeting"}
)

# Очистить состояние через Response
return Response(
    text="Готово!",
    clear_state=True
)
```

### 👤 Информация о пользователе

```python
# Получить пользователя
user = await self.core.get_user(telegram_id=123456789)
# user.id, user.first_name, user.language, user.role

# Получить язык
lang = await self.core.get_user_language(user_id)
# → "ru" или "en"

# Получить локализованный текст
text = await self.core.get_text(user_id, "SECTION.key", name="Иван")
```

### ⚙️ Настройки пользователя в сервисе

```python
# Сохранить настройки
await self.core.set_user_service_settings(user_id, {
    "voice_enabled": True,
    "model": "gpt-4",
    "temperature": 0.7
})

# Получить настройки
settings = await self.core.get_user_service_settings(user_id)
voice = settings.get("voice_enabled", False)
```

### 📊 Аналитика

```python
# Трекать событие
await self.core.track_event(
    event_name="message_sent",     # Название события
    user_id=user_id,               # ID пользователя
    value=5,                       # Числовое значение (опционально)
    properties={                   # Дополнительные данные (опционально)
        "mode": "voice",
        "model": "gpt-4"
    }
)

# События автоматически получают префикс сервиса:
# "message_sent" → "service:my_service:message_sent"
```

### 🔔 Подписки

```python
# Проверить подписку
sub = await self.core.check_subscription(user_id)

if sub.is_active:
    print(f"План: {sub.plan}, осталось {sub.days_left} дней")
else:
    print("Подписка не активна")

# sub.is_active — активна ли
# sub.plan — название плана ("basic", "premium")
# sub.expires_at — дата окончания
# sub.days_left — дней осталось
```

---

## Response — Формат ответа

```python
from core.plugins.base_service import Response

# Простой ответ
return Response(text="Привет!")

# С клавиатурой
return Response(
    text="Выберите действие:",
    keyboard=[
        [{"text": "Кнопка 1", "callback_data": "service:my:action1"}],
        [{"text": "Кнопка 2", "callback_data": "service:my:action2"}],
        [{"text": "◀️ Назад", "callback_data": "main_menu"}]
    ]
)

# Отправить новое сообщение (вместо редактирования)
return Response(
    text="Новое сообщение",
    action="send"  # "edit" (по умолчанию), "send", "answer", "delete"
)

# Показать alert
return Response(
    text="",
    action="answer",
    show_alert=True,
    alert_text="Ошибка! Недостаточно средств."
)

# С медиа
return Response(
    text="Ваше изображение:",
    media_type="photo",
    media_file_id="AgACAgIAAxk..."  # или media_url="https://..."
)

# Установить FSM состояние
return Response(
    text="Введите сообщение:",
    set_state="waiting_input",
    state_data={"step": 1}
)

# Перенаправить на другой callback
return Response(
    text="",
    redirect_to="main_menu"
)
```

---

## Типичные сценарии

### Сценарий 1: Платное действие

```python
async def _do_action(self, user_id: int) -> Response:
    """Действие, которое стоит GTON"""
    from decimal import Decimal
    
    COST = Decimal("0.5")  # Стоимость
    
    # Списываем
    result = await self.core.deduct_balance(
        user_id=user_id,
        amount=COST,
        reason="Генерация изображения",
        action="generate_image"
    )
    
    if not result.success:
        # Недостаточно средств
        balance_str = await self.core.format_gton(
            result.new_balance or Decimal("0")
        )
        return Response(
            text=f"❌ Недостаточно GTON!\n\n"
                 f"Стоимость: {COST} GTON\n"
                 f"У вас: {balance_str}",
            keyboard=[
                [{"text": "💳 Пополнить", "callback_data": "top_up"}],
                [{"text": "◀️ Назад", "callback_data": f"service:{self.info.id}:main"}]
            ]
        )
    
    # Выполняем действие
    image_url = await self._generate_image()
    
    # Трекаем
    await self.core.track_event("image_generated", user_id, value=1)
    
    return Response(
        text="🎨 Ваше изображение готово!",
        media_type="photo",
        media_url=image_url
    )
```

### Сценарий 2: Многошаговый диалог (FSM)

```python
async def handle_callback(self, user_id, action, params, context) -> Response:
    if action == "start_dialog":
        # Шаг 1: Запрашиваем имя
        return Response(
            text="Как вас зовут?",
            set_state="waiting_name",
            state_data={"step": 1}
        )
    
    elif action == "main":
        return await self._show_main(user_id)
    
    return Response(text="❌ Неизвестное действие")

async def handle_message(self, user_id, message, context) -> Response:
    state, data = await self.core.get_user_state(user_id)
    
    if state == "waiting_name":
        name = message.text
        # Шаг 2: Запрашиваем возраст
        return Response(
            text=f"Приятно познакомиться, {name}! Сколько вам лет?",
            set_state="waiting_age",
            state_data={"name": name, "step": 2}
        )
    
    elif state == "waiting_age":
        name = data.get("name")
        age = message.text
        # Завершаем диалог
        return Response(
            text=f"Отлично! {name}, {age} лет. Данные сохранены!",
            clear_state=True,
            keyboard=[
                [{"text": "◀️ В меню", "callback_data": f"service:{self.info.id}:main"}]
            ]
        )
    
    return Response(text="Используйте кнопки меню")
```

### Сценарий 3: Настройки пользователя

```python
async def _show_settings(self, user_id: int) -> Response:
    settings = await self.core.get_user_service_settings(user_id)
    
    voice = settings.get("voice_enabled", False)
    model = settings.get("model", "gpt-3.5")
    
    voice_icon = "✅" if voice else "❌"
    
    text = f"""
⚙️ <b>Настройки</b>

🎤 Голосовые сообщения: {voice_icon}
🤖 Модель: {model}
"""
    
    keyboard = [
        [{"text": f"🎤 Голос: {voice_icon}", 
          "callback_data": f"service:{self.info.id}:toggle_voice"}],
        [{"text": "🤖 Выбрать модель", 
          "callback_data": f"service:{self.info.id}:select_model"}],
        [{"text": "◀️ Назад", 
          "callback_data": f"service:{self.info.id}:main"}]
    ]
    
    return Response(text=text, keyboard=keyboard)

async def _toggle_voice(self, user_id: int) -> Response:
    settings = await self.core.get_user_service_settings(user_id)
    current = settings.get("voice_enabled", False)
    
    await self.core.set_user_service_settings(user_id, {
        "voice_enabled": not current
    })
    
    return await self._show_settings(user_id)
```

---

## Своя база данных

Если сервису нужно хранить данные (сессии, история, статистика), создайте свою БД:

### database/connection.py

```python
"""Database connection"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# БД в папке сервиса
SERVICE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(SERVICE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "service.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_session():
    return SessionLocal()


def init_db():
    Base.metadata.create_all(engine)
```

### database/models.py

```python
"""Database models"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, Boolean
from .connection import Base


class ChatSession(Base):
    """Сессия чата"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    
    title = Column(String(255))
    messages_count = Column(Integer, default=0)
    tokens_spent = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    """Сообщение в чате"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, index=True)
    
    role = Column(String(20))  # user, assistant, system
    content = Column(Text)
    tokens = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Использование в сервисе

```python
class MyService(BaseService):
    
    async def install(self) -> bool:
        from .database.connection import init_db
        init_db()
        return True
    
    async def _create_session(self, user_id: int) -> int:
        from .database.connection import get_session
        from .database.models import ChatSession
        
        with get_session() as db:
            session = ChatSession(user_id=user_id)
            db.add(session)
            db.commit()
            return session.id
    
    async def _get_user_sessions(self, user_id: int) -> list:
        from .database.connection import get_session
        from .database.models import ChatSession
        
        with get_session() as db:
            return db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).order_by(ChatSession.updated_at.desc()).all()
```

---

## Чеклист создания сервиса

### Обязательно:
- [ ] `services/my_service/__init__.py` — пустой файл
- [ ] `services/my_service/service.py` — класс сервиса
- [ ] Свойство `info` — информация о сервисе
- [ ] Метод `install()` — установка
- [ ] Метод `uninstall()` — удаление
- [ ] Метод `get_user_menu_items()` — кнопка в меню
- [ ] Метод `get_admin_menu_items()` — кнопка в админке
- [ ] Метод `handle_callback()` — обработка кнопок
- [ ] Метод `handle_message()` — обработка сообщений

### Опционально:
- [ ] `database/` — своя база данных
- [ ] `locales/` — мультиязычность
- [ ] `requirements.txt` — зависимости
- [ ] `README.md` — документация

---

## FAQ

### Как получить telegram_id пользователя?

```python
# В handle_callback и handle_message вы получаете user_id — это внутренний ID
# Чтобы получить telegram_id:
user = await self.core.get_user_by_id(user_id)
telegram_id = user.telegram_id
```

### Как отправить сообщение пользователю вне callback?

Это делается через ядро, но пока не реализовано в CoreAPI. Используйте Response с action="send".

### Как сделать подписку?

Подписки хранятся в `UserService`. Используйте `check_subscription()` для проверки.

### Как добавить свои настройки в админку?

Реализуйте `get_admin_menu_items()` и обрабатывайте в `handle_callback()` действия с префиксом `admin`.

---

*Документ создан: 17.12.2024*
