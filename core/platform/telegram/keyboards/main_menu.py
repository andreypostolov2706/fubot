"""
Main Menu Keyboard
"""
from core.locales import t
from core.config import config
from core.plugins.registry import service_registry
from core.plugins.base_service import MenuItem, UserServiceDTO
from core.platform.telegram.utils import build_keyboard, get_user_telegram_id
from loguru import logger


async def get_daily_horoscope_status(user_id: int) -> bool:
    """Получить статус подписки на ежедневный гороскоп"""
    try:
        from core.database import get_db
        from sqlalchemy import select
        
        async with get_db() as session:
            from services.astrology.models import UserAstrologyProfile
            result = await session.execute(
                select(UserAstrologyProfile.daily_horoscope_enabled)
                .where(UserAstrologyProfile.user_id == user_id)
            )
            row = result.scalar_one_or_none()
            return row if row is not None else False
    except Exception as e:
        logger.error(f"Error getting daily horoscope status: {e}")
        return False


async def main_menu_kb(user_id: int, lang: str = "ru"):
    """
    Build main menu keyboard.
    
    Порядок:
    1. Популярные услуги астрологии (order=5-8)
    2. Nano Banano (order=10)
    3. Veo (order=20)
    4. Пополнить (order=100)
    5. Партнёрская программа (order=200)
    6. Помощь (order=400)
    
    Кнопки в 2 ряда.
    """
    # Получаем статус подписки на ежедневный гороскоп
    daily_enabled = await get_daily_horoscope_status(user_id)
    daily_icon = "✅" if daily_enabled else "⬜"
    
    # Base menu items (без промокода — он есть в пополнении)
    menu_items: list[MenuItem] = [
        # Популярные услуги астрологии - быстрый доступ
        MenuItem(
            text="🌟 Натальная карта",
            callback="service:astrology:natal",
            order=5
        ),
        MenuItem(
            text="💑 Совместимость",
            callback="service:astrology:compat",
            order=6
        ),
        MenuItem(
            text="☀️ Гороскоп на сегодня",
            callback="service:astrology:daily",
            order=7
        ),
        MenuItem(
            text="👶 Детский гороскоп",
            callback="service:astrology:child",
            order=8
        ),
        MenuItem(
            text=f"{daily_icon} Гороскоп на день",
            callback="service:astrology:daily_toggle",
            order=9
        ),
        # Основные пункты меню
        MenuItem(
            text=t(lang, "MAIN_MENU.top_up"), 
            callback="top_up", 
            order=100
        ),
        MenuItem(
            text=t(lang, "MAIN_MENU.partner"), 
            callback="partner", 
            order=200
        ),
        MenuItem(
            text=t(lang, "MAIN_MENU.help"), 
            callback="help", 
            order=400
        ),
    ]
    
    # Add service menu items
    for service in service_registry.get_active():
        try:
            user_data = UserServiceDTO()  # TODO: load from DB
            service_items = service.get_user_menu_items(user_id, user_data)
            menu_items.extend(service_items)
        except Exception as e:
            logger.error(f"Error getting menu items from {service.info.id}: {e}")
    
    # Sort by order
    menu_items.sort(key=lambda x: x.order)
    
    # Build keyboard in 2 columns
    keyboard = []
    row = []
    for item in menu_items:
        if item.visible:
            btn_text = item.text
            if item.badge:
                btn_text += f" {item.badge}"
            row.append({"text": btn_text, "callback_data": item.callback})
            
            if len(row) == 2:
                keyboard.append(row)
                row = []
    
    # Add remaining button if odd number
    if row:
        keyboard.append(row)
    
    # Add admin buttons if admin
    telegram_id = await get_user_telegram_id(user_id)
    if telegram_id and config.is_admin(telegram_id):
        keyboard.append([
            {"text": "⚙️ Глобальные настройки", "callback_data": "global_settings"},
            {"text": "🔧 Админ-панель", "callback_data": "admin"},
        ])
    
    return build_keyboard(keyboard)
