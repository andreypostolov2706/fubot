# BaseService — Базовый класс сервиса

## Полный интерфейс

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime


@dataclass
class ServiceInfo:
    """Информация о сервисе"""
    id: str             # "ai_psychologist" (уникальный ID)
    name: str           # "ИИ-Психолог" (отображаемое имя)
    description: str    # Описание
    version: str        # "1.0.0"
    author: str         # Автор
    icon: str = "📦"    # Эмодзи для меню


@dataclass
class MenuItem:
    """Пункт меню"""
    text: str                          # "🧠 ИИ-Психолог"
    callback: str                      # "service:ai_psychologist:main"
    order: int = 0                     # Порядок сортировки (меньше = выше)
    row: int = None                    # Номер строки (для группировки)
    visible: bool = True               # Показывать ли
    badge: Optional[str] = None        # "NEW", "3", "⭐"


@dataclass
class Response:
    """Ответ сервиса на действие"""
    
    # === Основное ===
    text: str                              # Текст сообщения
    keyboard: Optional[list] = None        # Inline клавиатура
    parse_mode: str = "HTML"               # HTML или Markdown
    
    # === Действие ===
    action: str = "edit"
    # "edit"   - редактировать текущее сообщение
    # "send"   - отправить новое сообщение
    # "answer" - ответить на callback (toast)
    # "delete" - удалить сообщение
    
    # === Медиа ===
    media_type: Optional[str] = None       # photo, video, voice, document
    media_file_id: Optional[str] = None    # file_id из Telegram
    media_url: Optional[str] = None        # URL файла
    
    # === Alert ===
    show_alert: bool = False               # Показать alert вместо toast
    alert_text: Optional[str] = None       # Текст alert
    
    # === FSM состояние ===
    set_state: Optional[str] = None        # Установить состояние
    state_data: Optional[dict] = None      # Данные состояния
    clear_state: bool = False              # Очистить состояние
    
    # === Навигация ===
    redirect_to: Optional[str] = None      # Перенаправить на другой callback


@dataclass
class MessageDTO:
    """Входящее сообщение"""
    text: Optional[str] = None
    voice_file_id: Optional[str] = None
    voice_duration: Optional[int] = None
    photo_file_id: Optional[str] = None
    document_file_id: Optional[str] = None
    caption: Optional[str] = None


@dataclass
class CallbackContext:
    """Контекст callback"""
    message_id: int
    chat_id: int
    user_id: int


@dataclass
class MessageContext:
    """Контекст сообщения"""
    message_id: int
    chat_id: int
    user_id: int
    reply_to_message_id: Optional[int] = None


class BaseService(ABC):
    """
    Базовый класс для всех сервисов.
    
    Каждый сервис должен наследовать этот класс и реализовать
    абстрактные методы.
    """
    
    def __init__(self, core_api: "CoreAPI"):
        """
        Инициализация сервиса.
        
        Args:
            core_api: Интерфейс ядра для взаимодействия
        """
        self.core = core_api
        self._db = None
    
    # ==================== ОБЯЗАТЕЛЬНЫЕ СВОЙСТВА ====================
    
    @property
    @abstractmethod
    def info(self) -> ServiceInfo:
        """
        Информация о сервисе.
        
        Returns:
            ServiceInfo с id, name, description, version, author, icon
        """
        pass
    
    @property
    def permissions(self) -> list[str]:
        """
        Требуемые разрешения.
        
        Returns:
            Список разрешений: ["balance:read", "balance:deduct", ...]
        """
        return ["balance:read", "balance:deduct"]
    
    @property
    def features(self) -> dict:
        """
        Возможности сервиса.
        
        Returns:
            {
                "subscriptions": False,    # Поддержка подписок
                "broadcasts": False,       # Может делать рассылки
                "partner_menu": False,     # Меню для партнёров
                "voice_messages": False,   # Обработка голоса
            }
        """
        return {}
    
    # ==================== УСТАНОВКА ====================
    
    @abstractmethod
    async def install(self) -> bool:
        """
        Установка сервиса.
        
        Здесь нужно:
        - Создать таблицы в своей БД
        - Инициализировать данные
        
        Returns:
            True если успешно
        """
        pass
    
    @abstractmethod
    async def uninstall(self) -> bool:
        """
        Удаление сервиса.
        
        Здесь нужно:
        - Удалить таблицы
        - Очистить данные
        
        Returns:
            True если успешно
        """
        pass
    
    async def upgrade(self, from_version: str) -> bool:
        """
        Обновление сервиса.
        
        Args:
            from_version: Предыдущая версия
        
        Returns:
            True если успешно
        """
        return True
    
    # ==================== МЕНЮ ====================
    
    @abstractmethod
    def get_user_menu_items(
        self, 
        user_id: int, 
        user_data: "UserServiceDTO"
    ) -> list[MenuItem]:
        """
        Пункты меню для пользователя.
        
        Args:
            user_id: ID пользователя
            user_data: Данные пользователя в сервисе (роль, подписка, настройки)
        
        Returns:
            Список MenuItem для отображения в главном меню
        """
        pass
    
    @abstractmethod
    def get_admin_menu_items(self) -> list[MenuItem]:
        """
        Пункты админ-меню сервиса.
        
        Returns:
            Список MenuItem для админ-панели
        """
        pass
    
    def get_partner_menu_items(self, partner_id: int) -> list[MenuItem]:
        """
        Пункты меню для партнёра (опционально).
        
        Args:
            partner_id: ID партнёра
        
        Returns:
            Список MenuItem
        """
        return []
    
    # ==================== ОБРАБОТКА ====================
    
    @abstractmethod
    async def handle_callback(
        self, 
        user_id: int, 
        action: str, 
        params: dict,
        context: CallbackContext
    ) -> Response:
        """
        Обработка callback от пользователя.
        
        Callback data формат: "service:{service_id}:{action}:{param1}:{param2}"
        Ядро парсит и передаёт:
        - action: первая часть после service_id
        - params: {"param1": "value1", "param2": "value2"} или {"id": "123"}
        
        Args:
            user_id: ID пользователя
            action: Действие ("main", "start", "settings", etc.)
            params: Параметры из callback_data
            context: Контекст (message_id, chat_id)
        
        Returns:
            Response с текстом, клавиатурой и действием
        """
        pass
    
    @abstractmethod
    async def handle_message(
        self,
        user_id: int,
        message: MessageDTO,
        context: MessageContext
    ) -> Response:
        """
        Обработка сообщения от пользователя.
        
        Вызывается когда:
        - Пользователь в состоянии сервиса (FSM)
        - Или сервис активен для пользователя
        
        Args:
            user_id: ID пользователя
            message: Сообщение (текст, голос, фото, документ)
            context: Контекст
        
        Returns:
            Response
        """
        pass
    
    # ==================== ХУКИ ОТ ЯДРА ====================
    
    async def on_user_registered(self, user_id: int, referrer_id: Optional[int]):
        """
        Новый пользователь зарегистрировался в боте.
        
        Args:
            user_id: ID нового пользователя
            referrer_id: ID того, кто пригласил (или None)
        """
        pass
    
    async def on_user_first_visit(self, user_id: int):
        """
        Пользователь впервые зашёл в сервис.
        
        Хорошее место для:
        - Приветственного сообщения
        - Начисления бонуса
        - Трекинга события
        """
        pass
    
    async def on_payment_success(
        self, 
        user_id: int, 
        amount_rub: float, 
        tokens: int
    ):
        """
        Пользователь пополнил баланс.
        
        Args:
            user_id: ID пользователя
            amount_rub: Сумма в рублях
            tokens: Количество токенов
        """
        pass
    
    async def on_subscription_activated(
        self, 
        user_id: int, 
        plan: str, 
        until: datetime
    ):
        """
        Подписка активирована.
        
        Args:
            user_id: ID пользователя
            plan: Название плана
            until: До какой даты
        """
        pass
    
    async def on_subscription_expired(self, user_id: int):
        """
        Подписка истекла.
        """
        pass
    
    async def on_daily_reset(self):
        """
        Ежедневный сброс (вызывается в 00:00).
        
        Хорошее место для:
        - Сброса дневных лимитов
        - Отправки напоминаний
        - Очистки временных данных
        """
        pass
    
    # ==================== АДМИНСКИЕ ХУКИ ====================
    
    async def on_admin_action(
        self, 
        admin_id: int, 
        action: str, 
        target_user_id: int, 
        data: dict
    ):
        """
        Админ выполнил действие над пользователем сервиса.
        
        Args:
            admin_id: ID админа
            action: Действие (block, unblock, reset, etc.)
            target_user_id: ID пользователя
            data: Дополнительные данные
        """
        pass
    
    # ==================== СТАТИСТИКА ====================
    
    async def get_user_stats(self, user_id: int) -> dict:
        """
        Статистика пользователя для отображения.
        
        Returns:
            {"sessions": 10, "messages": 150, ...}
        """
        return {}
    
    async def get_service_stats(self) -> dict:
        """
        Общая статистика сервиса для админки.
        
        Returns:
            {"total_users": 1000, "active_today": 50, ...}
        """
        return {}
    
    async def search_users(self, query: str, limit: int = 10) -> list[dict]:
        """
        Поиск пользователей сервиса.
        
        Args:
            query: Поисковый запрос
            limit: Максимум результатов
        
        Returns:
            [{"user_id": 123, "name": "...", ...}, ...]
        """
        return []
```

---

## Пример реализации

```python
from core.plugins.base_service import BaseService, ServiceInfo, MenuItem, Response


class DiceGameService(BaseService):
    """Игра в кости"""
    
    @property
    def info(self) -> ServiceInfo:
        return ServiceInfo(
            id="dice_game",
            name="Игра в кости",
            description="Испытай удачу!",
            version="1.0.0",
            author="FuBot",
            icon="🎲"
        )
    
    @property
    def permissions(self) -> list[str]:
        return [
            "balance:read",
            "balance:deduct",
            "balance:add",
            "analytics:track"
        ]
    
    async def install(self) -> bool:
        from .database.models import Base
        from .database.connection import engine
        Base.metadata.create_all(engine)
        return True
    
    async def uninstall(self) -> bool:
        from .database.models import Base
        from .database.connection import engine
        Base.metadata.drop_all(engine)
        return True
    
    def get_user_menu_items(self, user_id: int, user_data) -> list[MenuItem]:
        return [
            MenuItem(
                text="🎲 Игра в кости",
                callback="service:dice_game:main",
                order=20
            )
        ]
    
    def get_admin_menu_items(self) -> list[MenuItem]:
        return [
            MenuItem(
                text="🎲 Игра в кости",
                callback="service:dice_game:admin",
                order=20
            )
        ]
    
    async def handle_callback(self, user_id, action, params, context) -> Response:
        if action == "main":
            return await self._show_main(user_id)
        elif action == "play":
            return await self._play_game(user_id, params)
        elif action == "admin":
            return await self._show_admin(user_id)
        else:
            return Response(text="❌ Неизвестное действие")
    
    async def handle_message(self, user_id, message, context) -> Response:
        state, data = await self.core.get_user_state(user_id)
        
        if state == "waiting_bet":
            return await self._process_bet(user_id, message.text, data)
        
        return Response(text="Используйте кнопки меню")
    
    async def _show_main(self, user_id: int) -> Response:
        balance = await self.core.get_balance(user_id)
        stats = await self.get_user_stats(user_id)
        
        text = f"""
🎲 <b>Игра в кости</b>

💰 Баланс: {balance} токенов
🎮 Игр сыграно: {stats.get('games', 0)}
🏆 Побед: {stats.get('wins', 0)}

Выберите ставку:
"""
        keyboard = [
            [
                {"text": "10 🪙", "callback_data": "service:dice_game:play:10"},
                {"text": "50 🪙", "callback_data": "service:dice_game:play:50"},
            ],
            [
                {"text": "100 🪙", "callback_data": "service:dice_game:play:100"},
                {"text": "500 🪙", "callback_data": "service:dice_game:play:500"},
            ],
            [{"text": "◀️ Назад", "callback_data": "main_menu"}]
        ]
        
        return Response(text=text, keyboard=keyboard)
    
    async def _play_game(self, user_id: int, params: dict) -> Response:
        bet = int(params.get("id", 10))
        
        # Списываем ставку
        result = await self.core.deduct_balance(
            user_id=user_id,
            amount=bet,
            reason=f"Ставка в кости: {bet}",
            action="bet"
        )
        
        if not result.success:
            return Response(
                text=f"❌ Недостаточно токенов!\nНужно: {bet}",
                keyboard=[[{"text": "💳 Пополнить", "callback_data": "top_up"}]]
            )
        
        # Играем
        import random
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        
        won = total >= 7
        winnings = bet * 2 if won else 0
        
        if won:
            await self.core.add_balance(user_id, winnings, source="dice_win")
            await self.core.track_event("game_won", user_id, value=winnings)
            text = f"🎉 Победа!\n\n🎲 {dice1} + {dice2} = {total}\n\n💰 +{winnings} токенов"
        else:
            await self.core.track_event("game_lost", user_id, value=bet)
            text = f"😔 Не повезло...\n\n🎲 {dice1} + {dice2} = {total}\n\n💸 -{bet} токенов"
        
        keyboard = [
            [{"text": "🔄 Играть снова", "callback_data": f"service:dice_game:play:{bet}"}],
            [{"text": "◀️ В меню", "callback_data": "service:dice_game:main"}]
        ]
        
        return Response(text=text, keyboard=keyboard)
```
