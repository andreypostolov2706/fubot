"""
Global Settings Handler

Глобальные настройки для админа:
- Курс GTON/TON
- Курс GTON/Stars
- Маржа для всех сервисов
"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from decimal import Decimal

from core.config import config
from core.database import get_db
from core.platform.telegram.utils import (
    get_or_create_user,
    get_user_telegram_id,
    build_keyboard,
)
from core.plugins.core_api import CoreAPI


async def global_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню глобальных настроек"""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    
    # Проверка на админа
    telegram_id = await get_user_telegram_id(user_id)
    if not telegram_id or not config.is_admin(telegram_id):
        await query.edit_message_text("❌ Доступ запрещён")
        return
    
    await show_global_settings(query, user_id)


async def show_global_settings(query, user_id: int):
    """Показать глобальные настройки"""
    from core.database.models import Setting, Service
    from sqlalchemy import select
    from core.payments.converter import currency_converter
    
    async with get_db() as session:
        # Получаем текущие курсы
        gton_ton_rate = await get_setting(session, "payments.gton_ton_rate", "1.0")
        gton_stars_rate = await get_setting(session, "payments.gton_stars_rate", "100")
        
        # Получаем маржу первого сервиса (для отображения)
        result = await session.execute(
            select(Service.config).where(Service.id == "nano_banano")
        )
        service_config = result.scalar_one_or_none()
        current_margin = 0.3
        if service_config and isinstance(service_config, dict):
            current_margin = service_config.get("margin_multiplier", 0.3)
    
    # Рассчитываем курс GTON/RUB
    try:
        gton_rub = await currency_converter.convert_from_gton(Decimal("1"), "RUB")
        gton_rub_str = f"{float(gton_rub):.2f}" if gton_rub else "N/A"
    except:
        gton_rub_str = "N/A"
    
    text = """⚙️ <b>Глобальные настройки</b>

<b>💱 Курсы:</b>
• GTON/TON: <b>{gton_ton}</b> (1 GTON = {gton_ton} TON)
• GTON/Stars: <b>{gton_stars}</b> (1 GTON = {gton_stars} ⭐)
• GTON/RUB: <b>{gton_rub} ₽</b> (1 GTON = {gton_rub} ₽)

<b>💰 Маржа:</b>
• Текущая: <b>{margin}%</b> (для всех сервисов)

Выберите параметр для изменения:
""".format(
        gton_ton=gton_ton_rate,
        gton_stars=gton_stars_rate,
        gton_rub=gton_rub_str,
        margin=int(float(current_margin) * 100)
    )
    
    keyboard = [
        [{"text": "💱 Курс GTON/TON", "callback_data": "global_settings:edit:gton_ton_rate"}],
        [{"text": "⭐ Курс GTON/Stars", "callback_data": "global_settings:edit:gton_stars_rate"}],
        [{"text": "💰 Маржа для всех", "callback_data": "global_settings:edit:margin"}],
        [{"text": "◀️ Главное меню", "callback_data": "main_menu"}],
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def get_setting(session, key: str, default: str = "") -> str:
    """Получить значение настройки из БД"""
    from core.database.models import Setting
    from sqlalchemy import select
    
    result = await session.execute(
        select(Setting.value).where(Setting.key == key)
    )
    value = result.scalar_one_or_none()
    return value if value else default


async def global_settings_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора параметра для редактирования"""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    
    # Проверка на админа
    telegram_id = await get_user_telegram_id(user_id)
    if not telegram_id or not config.is_admin(telegram_id):
        await query.edit_message_text("❌ Доступ запрещён")
        return
    
    # Парсим callback
    data = query.data.split(":")
    if len(data) < 3:
        return
    
    param = data[2]  # gton_ton_rate, gton_stars_rate, margin
    
    # Сохраняем состояние
    api = CoreAPI("core")
    await api.set_user_state(user_id, f"global_settings:waiting:{param}", {})
    
    if param == "gton_ton_rate":
        text = """💱 <b>Курс GTON/TON</b>

Введите новый курс (сколько TON за 1 GTON):

Например: <code>1.5</code> означает 1 GTON = 1.5 TON
"""
    elif param == "gton_stars_rate":
        text = """⭐ <b>Курс GTON/Stars</b>

Введите новый курс (сколько Stars за 1 GTON):

Например: <code>100</code> означает 1 GTON = 100 ⭐
"""
    elif param == "margin":
        text = """💰 <b>Маржа для всех сервисов</b>

Введите новую маржу (например, 0.3 для 30%):

Это изменит маржу сразу для всех сервисов!
"""
    else:
        return
    
    keyboard = [
        [{"text": "❌ Отмена", "callback_data": "global_settings"}],
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_global_settings_input(update: Update, user_id: int, state: str, value: str) -> bool:
    """
    Обработка ввода значения глобальной настройки.
    Возвращает True если обработано, False если нет.
    """
    from core.database.models import Setting, Service
    from sqlalchemy import select, update as sql_update
    from sqlalchemy.orm.attributes import flag_modified
    
    # Парсим состояние: global_settings:waiting:param
    parts = state.split(":")
    if len(parts) < 3 or parts[0] != "global_settings":
        return False
    
    param = parts[2]
    
    # Проверка на админа
    telegram_id = await get_user_telegram_id(user_id)
    if not telegram_id or not config.is_admin(telegram_id):
        await update.message.reply_text("❌ Доступ запрещён")
        return True
    
    try:
        if param == "gton_ton_rate":
            rate = float(value)
            if rate <= 0 or rate > 1000:
                await update.message.reply_text("❌ Курс должен быть от 0.001 до 1000")
                return True
            
            await save_setting("payments.gton_ton_rate", str(rate))
            await update.message.reply_text(f"✅ Курс GTON/TON обновлён: <b>{rate}</b>", parse_mode="HTML")
            
        elif param == "gton_stars_rate":
            rate = float(value)
            if rate <= 0 or rate > 10000:
                await update.message.reply_text("❌ Курс должен быть от 0.1 до 10000")
                return True
            
            await save_setting("payments.gton_stars_rate", str(rate))
            await update.message.reply_text(f"✅ Курс GTON/Stars обновлён: <b>{rate}</b>", parse_mode="HTML")
            
        elif param == "margin":
            margin = float(value)
            if margin < 0 or margin > 100:
                await update.message.reply_text("❌ Маржа должна быть от 0 до 100 (например, 3 для 300%)")
                return True
            
            # Обновляем маржу для всех сервисов
            await update_all_services_margin(margin)
            await update.message.reply_text(
                f"✅ Маржа обновлена для всех сервисов: <b>{int(margin * 100)}%</b>",
                parse_mode="HTML"
            )
        else:
            return False
            
    except ValueError:
        await update.message.reply_text("❌ Введите корректное число")
        return True
    
    # Очищаем состояние
    api = CoreAPI("core")
    await api.clear_user_state(user_id)
    
    # Показываем кнопку возврата
    keyboard = [
        [{"text": "◀️ К настройкам", "callback_data": "global_settings"}],
        [{"text": "🏠 Главное меню", "callback_data": "main_menu"}],
    ]
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=build_keyboard(keyboard)
    )
    
    return True


async def save_setting(key: str, value: str):
    """Сохранить настройку в БД"""
    from core.database.models import Setting
    from sqlalchemy import select
    
    async with get_db() as session:
        result = await session.execute(
            select(Setting).where(Setting.key == key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value, value_type="float")
            session.add(setting)
        
        await session.commit()


async def update_all_services_margin(margin: float):
    """Обновить маржу для всех сервисов"""
    from core.database.models import Service
    from sqlalchemy import select
    from sqlalchemy.orm.attributes import flag_modified
    
    async with get_db() as session:
        result = await session.execute(select(Service))
        services = result.scalars().all()
        
        for service in services:
            if service.config:
                service.config["margin_multiplier"] = margin
                flag_modified(service, "config")
            else:
                service.config = {"margin_multiplier": margin}
        
        await session.commit()
