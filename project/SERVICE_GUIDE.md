# Руководство по созданию сервиса

## Структура сервиса

```
services/
└── my_service/                 # 📦 Ваш сервис
    ├── __init__.py
    ├── service.py              # Главный класс (обязательно)
    ├── config.py               # Настройки
    │
    ├── database/               # Своя БД
    │   ├── __init__.py
    │   ├── connection.py
    │   └── models.py
    │
    ├── locales/                # 🌐 Локализации (опционально)
    │   ├── __init__.py
    │   ├── ru.py
    │   └── en.py
    │
    ├── handlers/               # Обработчики
    │   ├── __init__.py
    │   └── main.py
    │
    ├── keyboards.py            # Клавиатуры
    ├── messages.py             # Тексты (если без локализации)
    │
    ├── install.bat             # Установщик Windows
    ├── install.sh              # Установщик Linux
    ├── requirements.txt        # Зависимости
    └── README.md
```

> 📖 Подробнее о локализации сервиса: [SERVICE_LOCALIZATION.md](./SERVICE_LOCALIZATION.md)

---

## Шаг 1: Создать service.py

```python
"""
My Service - описание сервиса
"""
from dataclasses import dataclass
from typing import Optional
from core.plugins.base_service import BaseService, ServiceInfo, MenuItem, Response
from core.plugins.core_api import CoreAPI


class MyService(BaseService):
    """Главный класс сервиса"""
    
    def __init__(self, core_api: CoreAPI):
        super().__init__(core_api)
        self._init_database()
    
    # ==================== ИНФОРМАЦИЯ ====================
    
    @property
    def info(self) -> ServiceInfo:
        return ServiceInfo(
            id="my_service",
            name="Мой Сервис",
            description="Описание сервиса",
            version="1.0.0",
            author="Автор",
            icon="🎮"
        )
    
    @property
    def permissions(self) -> list[str]:
        return [
            "balance:read",
            "balance:deduct",
            "notifications:send",
            "analytics:track"
        ]
    
    @property
    def features(self) -> dict:
        return {
            "subscriptions": False,      # Поддержка подписок
            "broadcasts": True,          # Может делать рассылки
            "partner_menu": False,       # Меню для партнёров
            "voice_messages": False,     # Обработка голоса
        }
    
    # ==================== УСТАНОВКА ====================
    
    async def install(self) -> bool:
        """Установка сервиса"""
        try:
            # Создаём таблицы в своей БД
            self._create_tables()
            return True
        except Exception as e:
            print(f"Install error: {e}")
            return False
    
    async def uninstall(self) -> bool:
        """Удаление сервиса"""
        try:
            # Удаляем таблицы
            self._drop_tables()
            return True
        except Exception as e:
            print(f"Uninstall error: {e}")
            return False
    
    # ==================== МЕНЮ ====================
    
    def get_user_menu_items(self, user_id: int, user_data) -> list[MenuItem]:
        """Пункты меню для пользователя"""
        return [
            MenuItem(
                text=f"{self.info.icon} {self.info.name}",
                callback=f"service:{self.info.id}:main",
                order=10
            )
        ]
    
    def get_admin_menu_items(self) -> list[MenuItem]:
        """Пункты админ-меню"""
        return [
            MenuItem(
                text=f"{self.info.icon} {self.info.name}",
                callback=f"service:{self.info.id}:admin",
                order=10
            )
        ]
    
    # ==================== ОБРАБОТКА ====================
    
    async def handle_callback(
        self, 
        user_id: int, 
        action: str, 
        params: dict,
        context
    ) -> Response:
        """
        Обработка callback.
        
        action приходит без префикса сервиса:
        "service:my_service:main" → action = "main"
        "service:my_service:play:123" → action = "play", params = {"id": "123"}
        """
        
        if action == "main":
            return await self._show_main_menu(user_id)
        
        elif action == "play":
            return await self._handle_play(user_id, params)
        
        elif action == "admin":
            return await self._show_admin_menu(user_id)
        
        else:
            return Response(text="❌ Неизвестное действие")
    
    async def handle_message(
        self,
        user_id: int,
        message,
        context
    ) -> Response:
        """Обработка текстового сообщения"""
        
        # Получаем состояние пользователя
        state, state_data = await self.core.get_user_state(user_id)
        
        if state == "waiting_input":
            return await self._process_input(user_id, message.text, state_data)
        
        # Нет активного состояния
        return Response(
            text="Используйте меню для взаимодействия",
            keyboard=self._get_main_keyboard()
        )
    
    # ==================== ХУКИ ====================
    
    async def on_user_first_visit(self, user_id: int):
        """Пользователь впервые зашёл в сервис"""
        # Можно показать приветствие, дать бонус и т.д.
        await self.core.track_event("first_visit", user_id)
    
    async def on_payment_success(self, user_id: int, amount, currency: str):
        """Пользователь пополнил баланс"""
        pass
    
    # ==================== ПРИВАТНЫЕ МЕТОДЫ ====================
    
    async def _show_main_menu(self, user_id: int) -> Response:
        """Показать главное меню сервиса"""
        # Получаем баланс GTON с фиатным эквивалентом
        balance_str = await self.core.format_gton(
            await self.core.get_balance(user_id),
            with_fiat=True
        )
        
        text = f"""
{self.info.icon} <b>{self.info.name}</b>

💰 Ваш баланс: {balance_str}

Выберите действие:
"""
        
        keyboard = [
            [{"text": "🎮 Играть", "callback_data": f"service:{self.info.id}:play"}],
            [{"text": "📊 Статистика", "callback_data": f"service:{self.info.id}:stats"}],
            [{"text": "⚙️ Настройки", "callback_data": f"service:{self.info.id}:settings"}],
            [{"text": "◀️ Назад", "callback_data": "main_menu"}]
        ]
        
        return Response(text=text, keyboard=keyboard)
    
    async def _handle_play(self, user_id: int, params: dict) -> Response:
        """Обработка игры"""
        from decimal import Decimal
        
        cost = Decimal("0.5")  # Стоимость в GTON
        
        # Списываем GTON
        result = await self.core.deduct_balance(
            user_id=user_id,
            amount=cost,
            reason="Игра",
            action="play"
        )
        
        if not result.success:
            balance_str = await self.core.format_gton(result.new_balance or Decimal("0"))
            return Response(
                text=f"❌ Недостаточно GTON!\n\nНужно: {cost} GTON\nУ вас: {balance_str}",
                keyboard=[[{"text": "💳 Пополнить", "callback_data": "top_up"}]]
            )
        
        # Логика игры...
        won = True  # Результат
        
        # Трекаем событие
        await self.core.track_event("game_played", user_id, value=cost)
        
        if won:
            await self.core.track_event("game_won", user_id)
        
        return Response(
            text="🎉 Вы выиграли!" if won else "😔 Попробуйте ещё раз",
            keyboard=[[{"text": "🔄 Играть снова", "callback_data": f"service:{self.info.id}:play"}]]
        )
    
    # ==================== БАЗА ДАННЫХ ====================
    
    def _init_database(self):
        """Инициализация подключения к БД сервиса"""
        from .database.connection import init_db
        self._db = init_db()
    
    def _create_tables(self):
        """Создание таблиц"""
        from .database.models import Base
        from .database.connection import engine
        Base.metadata.create_all(engine)
    
    def _drop_tables(self):
        """Удаление таблиц"""
        from .database.models import Base
        from .database.connection import engine
        Base.metadata.drop_all(engine)
```

---

## Шаг 2: Создать database/

### database/connection.py

```python
"""Database connection for the service"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Путь к БД сервиса
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'service.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def init_db():
    """Initialize database"""
    Base.metadata.create_all(engine)
    return SessionLocal


def get_session():
    """Get database session"""
    return SessionLocal()
```

### database/models.py

```python
"""Database models for the service"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Text
from .connection import Base


class GameSession(Base):
    """Пример модели сервиса"""
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)  # ID из ядра
    
    # Данные сессии
    score = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    
    def __repr__(self):
        return f"<GameSession(id={self.id}, user_id={self.user_id})>"
```

---

## Шаг 3: Создать install.bat

```batch
@echo off
echo ========================================
echo   Installing My Service
echo ========================================

:: Проверяем что мы в папке сервиса
if not exist "service.py" (
    echo ERROR: Run this from service directory!
    pause
    exit /b 1
)

:: Устанавливаем зависимости
echo Installing dependencies...
pip install -r requirements.txt

:: Регистрируем сервис
echo Registering service...
cd ..\..
python -m core.plugins.installer install my_service

echo ========================================
echo   Installation complete!
echo   Restart the bot to apply changes.
echo ========================================
pause
```

---

## Шаг 4: Создать requirements.txt

```
# Зависимости сервиса
# (ядро уже установлено)
```

---

## Response — формат ответа

```python
@dataclass
class Response:
    """Ответ сервиса"""
    
    # Основное
    text: str                              # Текст сообщения
    keyboard: Optional[list] = None        # Inline клавиатура
    parse_mode: str = "HTML"               # HTML или Markdown
    
    # Действие
    action: str = "edit"                   # edit, send, answer, delete
    # edit   - редактировать текущее сообщение
    # send   - отправить новое сообщение
    # answer - ответить на callback (toast)
    # delete - удалить сообщение
    
    # Медиа
    media_type: Optional[str] = None       # photo, video, voice, document
    media_file_id: Optional[str] = None
    media_url: Optional[str] = None
    
    # Alert (для callback)
    show_alert: bool = False
    alert_text: Optional[str] = None
    
    # FSM состояние
    set_state: Optional[str] = None        # Установить состояние
    state_data: Optional[dict] = None      # Данные состояния
    clear_state: bool = False              # Очистить состояние
    
    # Навигация
    redirect_to: Optional[str] = None      # Перенаправить на callback
```

---

## Примеры использования

### Списание GTON

```python
from decimal import Decimal

result = await self.core.deduct_balance(
    user_id=user_id,
    amount=Decimal("0.5"),  # 0.5 GTON
    reason="Отправка сообщения",
    action="chat_message"
)

if not result.success:
    return Response(text=f"Недостаточно GTON: {result.error}")
```

### Работа с состоянием (FSM)

```python
# Установить состояние
return Response(
    text="Введите ваше сообщение:",
    set_state="waiting_message",
    state_data={"session_id": 123}
)

# В handle_message
state, data = await self.core.get_user_state(user_id)
if state == "waiting_message":
    session_id = data.get("session_id")
    # Обработка...
    return Response(
        text="Сообщение получено!",
        clear_state=True
    )
```

### Настройки пользователя

```python
# Сохранить
await self.core.set_user_service_settings(user_id, {
    "voice_enabled": True,
    "theme": "dark"
})

# Получить
settings = await self.core.get_user_service_settings(user_id)
voice_enabled = settings.get("voice_enabled", False)
```

### Аналитика

```python
# Трекать событие
await self.core.track_event(
    "message_sent",
    user_id=user_id,
    value=tokens_spent,
    properties={"mode": "voice"}
)
```

### Подписки

```python
from decimal import Decimal

# Проверить подписку
sub = await self.core.check_subscription(user_id)

if not sub.is_active:
    return Response(
        text="Требуется подписка!",
        keyboard=[[{"text": "Оформить", "callback_data": f"service:{self.info.id}:subscribe"}]]
    )

# Активировать подписку
await self.core.activate_subscription(
    user_id=user_id,
    plan="premium",
    days=30,
    price=Decimal("5.0")  # GTON
)
```

---

## Чеклист создания сервиса

- [ ] Создать папку `services/my_service/`
- [ ] Создать `service.py` с классом, наследующим `BaseService`
- [ ] Реализовать `info`, `permissions`, `features`
- [ ] Реализовать `install()` и `uninstall()`
- [ ] Реализовать `get_user_menu_items()` и `get_admin_menu_items()`
- [ ] Реализовать `handle_callback()` и `handle_message()`
- [ ] Создать `database/` с моделями (если нужна своя БД)
- [ ] Создать `locales/` с переводами (если нужна мультиязычность)
- [ ] Создать `install.bat` и `install.sh`
- [ ] Создать `requirements.txt`
- [ ] Создать `README.md` с описанием
- [ ] Протестировать установку и работу
