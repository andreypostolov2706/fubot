"""
Base Service - Abstract class for all services
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .core_api import CoreAPI


@dataclass
class ServiceInfo:
    """Service information"""
    id: str             # "ai_psychologist" (unique ID)
    name: str           # "ИИ-Психолог" (display name)
    description: str    # Description
    version: str        # "1.0.0"
    author: str         # Author
    icon: str = "📦"    # Emoji for menu


@dataclass
class MenuItem:
    """Menu item"""
    text: str                          # "🧠 ИИ-Психолог"
    callback: str                      # "service:ai_psychologist:main"
    order: int = 0                     # Sort order (lower = higher)
    row: Optional[int] = None          # Row number (for grouping)
    visible: bool = True               # Show or not
    badge: Optional[str] = None        # "NEW", "3", "⭐"
    full_width: bool = False           # Full width button (single column)


@dataclass
class Response:
    """Service response to action"""
    
    # === Main ===
    text: str                              # Message text
    keyboard: Optional[list] = None        # Inline keyboard
    parse_mode: str = "HTML"               # HTML or Markdown
    
    # === Action ===
    action: str = "edit"
    # "edit"   - edit current message
    # "send"   - send new message
    # "answer" - answer callback (toast)
    # "delete" - delete message
    
    # === Media ===
    media_type: Optional[str] = None       # photo, video, voice, document
    media_file_id: Optional[str] = None    # file_id from Telegram
    media_url: Optional[str] = None        # File URL
    media_path: Optional[str] = None       # Local file path
    
    # === Alert ===
    show_alert: bool = False               # Show alert instead of toast
    alert_text: Optional[str] = None       # Alert text
    
    # === FSM State ===
    set_state: Optional[str] = None        # Set state
    state_data: Optional[dict] = None      # State data
    clear_state: bool = False              # Clear state
    
    # === Navigation ===
    redirect_to: Optional[str] = None      # Redirect to another callback
    
    # === Loading ===
    loading_text: Optional[str] = None     # Show loading message before main text (for long operations)


@dataclass
class MessageDTO:
    """Incoming message"""
    text: Optional[str] = None
    voice_file_id: Optional[str] = None
    voice_duration: Optional[int] = None
    photo_file_id: Optional[str] = None
    document_file_id: Optional[str] = None
    caption: Optional[str] = None


@dataclass
class CallbackContext:
    """Callback context"""
    message_id: int
    chat_id: int
    user_id: int


@dataclass
class MessageContext:
    """Message context"""
    message_id: int
    chat_id: int
    user_id: int
    reply_to_message_id: Optional[int] = None


@dataclass
class UserServiceDTO:
    """User data in service context"""
    role: str = "user"
    settings: dict = field(default_factory=dict)
    subscription_plan: Optional[str] = None
    subscription_until: Optional[datetime] = None
    total_spent: int = 0
    usage_count: int = 0
    first_use_at: Optional[datetime] = None
    last_use_at: Optional[datetime] = None


class BaseService(ABC):
    """
    Base class for all services.
    
    Each service must inherit this class and implement
    abstract methods.
    """
    
    def __init__(self, core_api: "CoreAPI"):
        """
        Initialize service.
        
        Args:
            core_api: Core interface for interaction
        """
        self.core = core_api
        self._db = None
    
    # ==================== REQUIRED PROPERTIES ====================
    
    @property
    @abstractmethod
    def info(self) -> ServiceInfo:
        """
        Service information.
        
        Returns:
            ServiceInfo with id, name, description, version, author, icon
        """
        pass
    
    @property
    def permissions(self) -> list[str]:
        """
        Required permissions.
        
        Returns:
            List of permissions: ["balance:read", "balance:deduct", ...]
        """
        return ["balance:read", "balance:deduct"]
    
    @property
    def features(self) -> dict:
        """
        Service features.
        
        Returns:
            {
                "subscriptions": False,    # Subscription support
                "broadcasts": False,       # Can send broadcasts
                "partner_menu": False,     # Partner menu
                "voice_messages": False,   # Voice processing
            }
        """
        return {}
    
    # ==================== INSTALLATION ====================
    
    @abstractmethod
    async def install(self) -> bool:
        """
        Install service.
        
        Here you need to:
        - Create tables in your DB
        - Initialize data
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def uninstall(self) -> bool:
        """
        Uninstall service.
        
        Here you need to:
        - Drop tables
        - Clean up data
        
        Returns:
            True if successful
        """
        pass
    
    async def upgrade(self, from_version: str) -> bool:
        """
        Upgrade service.
        
        Args:
            from_version: Previous version
        
        Returns:
            True if successful
        """
        return True
    
    # ==================== MENU ====================
    
    @abstractmethod
    def get_user_menu_items(
        self, 
        user_id: int, 
        user_data: UserServiceDTO
    ) -> list[MenuItem]:
        """
        Menu items for user.
        
        Args:
            user_id: User ID
            user_data: User data in service (role, subscription, settings)
        
        Returns:
            List of MenuItem for main menu
        """
        pass
    
    @abstractmethod
    def get_admin_menu_items(self) -> list[MenuItem]:
        """
        Admin menu items.
        
        Returns:
            List of MenuItem for admin panel
        """
        pass
    
    def get_partner_menu_items(self, partner_id: int) -> list[MenuItem]:
        """
        Partner menu items (optional).
        
        Args:
            partner_id: Partner ID
        
        Returns:
            List of MenuItem
        """
        return []
    
    # ==================== HANDLING ====================
    
    @abstractmethod
    async def handle_callback(
        self, 
        user_id: int, 
        action: str, 
        params: dict,
        context: CallbackContext
    ) -> Response:
        """
        Handle callback from user.
        
        Callback data format: "service:{service_id}:{action}:{param1}:{param2}"
        Core parses and passes:
        - action: first part after service_id
        - params: {"param1": "value1", "param2": "value2"} or {"id": "123"}
        
        Args:
            user_id: User ID
            action: Action ("main", "start", "settings", etc.)
            params: Parameters from callback_data
            context: Context (message_id, chat_id)
        
        Returns:
            Response with text, keyboard and action
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
        Handle message from user.
        
        Called when:
        - User is in service state (FSM)
        - Or service is active for user
        
        Args:
            user_id: User ID
            message: Message (text, voice, photo, document)
            context: Context
        
        Returns:
            Response
        """
        pass
    
    # ==================== HOOKS FROM CORE ====================
    
    async def on_user_registered(self, user_id: int, referrer_id: Optional[int]):
        """
        New user registered in bot.
        
        Args:
            user_id: New user ID
            referrer_id: Referrer ID (or None)
        """
        pass
    
    async def on_user_first_visit(self, user_id: int):
        """
        User first visited service.
        
        Good place for:
        - Welcome message
        - Bonus credit
        - Event tracking
        """
        pass
    
    async def on_payment_success(
        self, 
        user_id: int, 
        amount_rub: float, 
        tokens: int
    ):
        """
        User topped up balance.
        
        Args:
            user_id: User ID
            amount_rub: Amount in rubles
            tokens: Token amount
        """
        pass
    
    async def on_subscription_activated(
        self, 
        user_id: int, 
        plan: str, 
        until: datetime
    ):
        """
        Subscription activated.
        
        Args:
            user_id: User ID
            plan: Plan name
            until: Until date
        """
        pass
    
    async def on_subscription_expired(self, user_id: int):
        """
        Subscription expired.
        """
        pass
    
    async def on_daily_reset(self):
        """
        Daily reset (called at 00:00).
        
        Good place for:
        - Reset daily limits
        - Send reminders
        - Clean up temporary data
        """
        pass
    
    # ==================== ADMIN HOOKS ====================
    
    async def on_admin_action(
        self, 
        admin_id: int, 
        action: str, 
        target_user_id: int, 
        data: dict
    ):
        """
        Admin performed action on service user.
        
        Args:
            admin_id: Admin ID
            action: Action (block, unblock, reset, etc.)
            target_user_id: User ID
            data: Additional data
        """
        pass
    
    # ==================== STATISTICS ====================
    
    async def get_user_stats(self, user_id: int) -> dict:
        """
        User statistics for display.
        
        Returns:
            {"sessions": 10, "messages": 150, ...}
        """
        return {}
    
    async def get_service_stats(self) -> dict:
        """
        Overall service statistics for admin.
        
        Returns:
            {"total_users": 1000, "active_today": 50, ...}
        """
        return {}
    
    async def search_users(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search service users.
        
        Args:
            query: Search query
            limit: Max results
        
        Returns:
            [{"user_id": 123, "name": "...", ...}, ...]
        """
        return []
