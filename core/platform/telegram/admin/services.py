"""
Admin Services Management
"""
import json
from sqlalchemy import select

from core.locales import t
from core.database import get_db
from core.platform.telegram.utils import build_keyboard


async def admin_services(query, lang: str, action: str = None, params: str = None):
    """Admin services handler"""
    if action == "view" and params:
        await view_service(query, lang, params)
    elif action == "config" and params:
        await view_service_config(query, lang, params)
    elif action == "edit_config" and params:
        # params format: service_id:key
        parts = params.split(":", 1)
        if len(parts) == 2:
            await edit_config_key(query, lang, parts[0], parts[1])
    elif action == "prices" and params:
        # params может быть "service_id" или "service_id:submenu"
        parts = params.split(":", 1)
        service_id = parts[0]
        submenu = parts[1] if len(parts) > 1 else None
        await view_service_prices(query, lang, service_id, submenu)
    elif action == "edit_price" and params:
        # params format: service_id:price_key
        parts = params.split(":", 1)
        if len(parts) == 2:
            await edit_price_key(query, lang, parts[0], parts[1])
    elif action == "stats" and params:
        await view_service_stats(query, lang, params)
    elif action == "disable" and params:
        await toggle_service(query, lang, params, False)
    elif action == "enable" and params:
        await toggle_service(query, lang, params, True)
    else:
        await services_list(query, lang)


async def services_list(query, lang: str):
    """Show services list"""
    from core.database.models import Service
    
    async with get_db() as session:
        result = await session.execute(select(Service))
        services = result.scalars().all()
    
    text = t(lang, "ADMIN.services_title") + "\n\n"
    
    keyboard = []
    
    if not services:
        text += t(lang, "ADMIN.services_empty") + "\n\n"
        text += t(lang, "ADMIN.services_install_hint")
    else:
        for service in services:
            status = "✅" if service.status == "active" else "❌"
            text += f"{status} <b>{service.name}</b> v{service.version}\n"
            text += f"   ID: <code>{service.id}</code>\n\n"
            
            # Кнопка для каждого сервиса
            keyboard.append([{
                "text": f"{service.icon or '📦'} {service.name}",
                "callback_data": f"admin:services:view:{service.id}"
            }])
    
    keyboard.append([{"text": t(lang, "ADMIN.services_refresh"), "callback_data": "admin:services"}])
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def view_service(query, lang: str, service_id: str):
    """View service details"""
    from core.database.models import Service
    
    async with get_db() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
    
    if not service:
        await query.answer(t(lang, "ADMIN.services_not_found"), show_alert=True)
        return
    
    status = t(lang, "ADMIN.services_active") if service.status == "active" else t(lang, "ADMIN.services_disabled")
    author = service.author or t(lang, "ADMIN.services_author_unknown")
    
    text = f"📦 <b>{service.name}</b>\n\n"
    text += f"ID: <code>{service.id}</code>\n"
    text += t(lang, "ADMIN.services_version", version=service.version) + "\n"
    text += t(lang, "ADMIN.services_author", author=author) + "\n"
    text += t(lang, "ADMIN.services_status", status=status) + "\n"
    if service.installed_at:
        text += t(lang, "ADMIN.services_installed", date=service.installed_at.strftime('%d.%m.%Y %H:%M')) + "\n"
    
    if service.description:
        text += f"\n📝 {service.description}"
    
    keyboard = []
    
    # Специальные кнопки для астрологии
    if service_id == "astrology":
        keyboard.append([{
            "text": "💰 Прайс-лист",
            "callback_data": f"admin:services:prices:{service_id}"
        }])
        keyboard.append([{
            "text": "📊 Статистика",
            "callback_data": f"admin:services:stats:{service_id}"
        }])
    
    # Кнопка настроек конфига
    keyboard.append([{
        "text": "⚙️ Настройки",
        "callback_data": f"admin:services:config:{service_id}"
    }])
    
    if service.status == "active":
        keyboard.append([{
            "text": t(lang, "ADMIN.services_disable"), 
            "callback_data": f"admin:services:disable:{service_id}"
        }])
    else:
        keyboard.append([{
            "text": t(lang, "ADMIN.services_enable"), 
            "callback_data": f"admin:services:enable:{service_id}"
        }])
    
    keyboard.append([{"text": t(lang, "COMMON.back"), "callback_data": "admin:services"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
)


CONFIG_KEY_NAMES = {
    "fal_api_key": "🔑 API ключ fal.ai",
    "margin_multiplier": "💰 Маржа",
    "prices": "💵 Цены",
    "gallery_channel_id": "📢 ID канала галереи",
    "gallery_enabled": "🖼 Публикация в галерею",
    "referral_bonus_enabled": "👥 Реферальный бонус",
    "referral_bonus_percent": "📊 Процент рефералу",
}


async def view_service_config(query, lang: str, service_id: str):
    """View and edit service config"""
    from core.database.models import Service
    
    async with get_db() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
    
    if not service:
        await query.answer("Сервис не найден", show_alert=True)
        return
    
    config = service.config or {}
    
    text = f"⚙️ <b>Настройки {service.name}</b>\n\n"
    
    # Отображаем конфиг
    for key, value in config.items():
        key_name = CONFIG_KEY_NAMES.get(key, key)
        
        if key == "fal_api_key":
            display_value = value[:10] + "..." if value else "❌ Не задан"
        elif key == "prices":
            display_value = f"{len(value)} позиций"
        elif key == "margin_multiplier":
            display_value = f"{int(value * 100)}%" if value else "0%"
        elif isinstance(value, bool):
            display_value = "✅ Да" if value else "❌ Нет"
        elif isinstance(value, (int, float)):
            display_value = str(value)
        else:
            display_value = str(value) if value else "—"
        
        text += f"• <b>{key_name}</b>: {display_value}\n"
    
    keyboard = []
    
    # Кнопки для редактирования основных настроек
    editable_keys = ["fal_api_key", "margin_multiplier", "gallery_channel_id", "gallery_enabled"]
    
    for key in editable_keys:
        if key in config:
            key_name = CONFIG_KEY_NAMES.get(key, key)
            keyboard.append([{
                "text": f"✏️ {key_name}",
                "callback_data": f"admin:services:edit_config:{service_id}:{key}"
            }])
    
    keyboard.append([{"text": "◀️ Назад", "callback_data": f"admin:services:view:{service_id}"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def edit_config_key(query, lang: str, service_id: str, key: str):
    """Start editing a config key"""
    from core.database.models import Service
    from core.plugins.core_api import CoreAPI
    
    async with get_db() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
    
    if not service:
        await query.answer("Сервис не найден", show_alert=True)
        return
    
    config = service.config or {}
    current_value = config.get(key, "")
    
    # Для boolean - сразу переключаем
    if key == "gallery_enabled":
        new_value = not config.get(key, False)
        config[key] = new_value
        
        async with get_db() as session:
            result = await session.execute(
                select(Service).where(Service.id == service_id)
            )
            service = result.scalar_one_or_none()
            if service:
                service.config = config
                await session.commit()
        
        await query.answer(f"{'✅ Включено' if new_value else '❌ Выключено'}")
        await view_service_config(query, lang, service_id)
        return
    
    # Для остальных - запрашиваем ввод
    key_name = CONFIG_KEY_NAMES.get(key, key)
    text = f"✏️ <b>{key_name}</b>\n\n"
    
    if key == "fal_api_key":
        text += "Введите API ключ fal.ai:\n\n"
        text += f"Текущий: <code>{current_value[:20]}...</code>" if current_value else "Текущий: ❌ не задан"
    elif key == "margin_multiplier":
        current_percent = f"{int(float(current_value) * 100)}%" if current_value else "0%"
        text += "Введите маржу (например, 0.3 для 30%):\n\n"
        text += f"Текущая: <b>{current_percent}</b>"
    elif key == "gallery_channel_id":
        text += "Введите ID канала для галереи:\n"
        text += "<i>Формат: -1001234567890 или @channel_name</i>\n\n"
        text += f"Текущий: <code>{current_value}</code>" if current_value else "Текущий: ❌ не задан"
    
    # Сохраняем состояние для ввода
    api = CoreAPI("core")
    user_id = query.from_user.id
    
    # Получаем внутренний user_id
    from core.platform.telegram.utils import get_or_create_user
    internal_user_id = await get_or_create_user(user_id, query.from_user)
    
    await api.set_user_state(internal_user_id, "admin_service_config_edit", {
        "service_id": service_id,
        "key": key,
    })
    
    keyboard = [
        [{"text": "❌ Отмена", "callback_data": f"admin:services:config:{service_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def toggle_service(query, lang: str, service_id: str, enable: bool):
    """Enable or disable a service"""
    from core.database.models import Service
    
    async with get_db() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
        
        if service:
            service.status = "active" if enable else "disabled"
            await session.commit()
    
    status = "включен" if enable else "выключен"
    await query.answer(f"Сервис {status}")
    await view_service(query, lang, service_id)


async def handle_service_config_input(update, context, user_id: int, lang: str, service_id: str, key: str):
    """Handle text input for service config editing"""
    from core.database.models import Service
    from core.plugins.core_api import CoreAPI
    
    value = update.message.text.strip()
    
    async with get_db() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
        
        if not service:
            await update.message.reply_text("❌ Сервис не найден")
            return
        
        config = service.config or {}
        
        # Валидация и преобразование значения
        if key == "margin_multiplier":
            try:
                value = float(value)
                if value < 0 or value > 100:
                    await update.message.reply_text("❌ Маржа должна быть от 0 до 100 (например, 3 для 300%)")
                    return
            except ValueError:
                await update.message.reply_text("❌ Введите число (например, 0.3)")
                return
        elif key == "gallery_channel_id":
            # Может быть числом или @username
            if value.startswith("@"):
                pass  # OK
            else:
                try:
                    value = int(value)
                except ValueError:
                    await update.message.reply_text("❌ Введите ID канала (число) или @username")
                    return
        
        # Обновляем конфиг
        config[key] = value
        service.config = config
        
        # Помечаем JSON-поле как изменённое
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(service, "config")
        
        await session.commit()
    
    # Очищаем состояние
    api = CoreAPI("core")
    await api.clear_user_state(user_id)
    
    await update.message.reply_text(
        f"✅ Настройка <b>{key}</b> обновлена!",
        parse_mode="HTML"
    )
    
    # Показываем конфиг сервиса
    # Создаём фейковый query для вызова view_service_config
    # Это не идеально, но работает
    keyboard = [
        [{"text": "◀️ К настройкам", "callback_data": f"admin:services:config:{service_id}"}]
    ]
    
    await update.message.reply_text(
        "Нажмите кнопку для возврата к настройкам:",
        reply_markup=build_keyboard(keyboard)
    )


# === Astrology Price Management ===

ASTROLOGY_PRICE_NAMES = {
    "natal": "🌟 Натальная карта",
    "child": "👶 Детский гороскоп",
    "love": "💕 Любовный портрет",
    "daily": "☀️ Гороскоп на сегодня",
    "transits": "🔮 Транзиты",
    "compatibility": "💑 Совместимость",
    "question": "❓ Задать вопрос",
}

# Подменю для астропрогноза
ASTROLOGY_FORECAST_PRICES = {
    "forecast_week": "📅 Неделя",
    "forecast_month": "📅 Месяц",
    "forecast_3months": "📅 3 месяца",
    "forecast_year": "📅 Год",
}

# Подменю для графика событий
ASTROLOGY_EVENTS_PRICES = {
    "events_3days": "📊 3 дня",
    "events_week": "📊 Неделя",
    "events_month": "📊 Месяц",
}


async def get_gton_to_rub_rate() -> float:
    """Получить курс GTON к рублю"""
    from core.payments.converter import currency_converter
    
    try:
        gton_rates = await currency_converter.get_gton_rates()
        rub_rate = gton_rates.get("RUB")
        if rub_rate:
            return float(rub_rate)
    except Exception as e:
        from loguru import logger
        logger.error(f"Error getting GTON rate: {e}")
    
    return 100.0  # Fallback: 1 GTON ≈ 100 RUB


async def view_service_prices(query, lang: str, service_id: str, submenu: str = None):
    """View and edit service prices (for astrology)"""
    from core.database.models import Service
    
    async with get_db() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
    
    if not service:
        await query.answer("Сервис не найден", show_alert=True)
        return
    
    config = service.config or {}
    prices = config.get("prices", {})
    
    # Получаем курс GTON к рублю
    gton_rub_rate = await get_gton_to_rub_rate()
    
    # Подменю для астропрогноза
    if submenu == "forecast":
        text = f"📅 <b>Астропрогноз — цены по периодам</b>\n\n"
        text += f"<i>Курс: 1 GTON ≈ {gton_rub_rate:.2f} ₽</i>\n\n"
        
        keyboard = []
        for key, name in ASTROLOGY_FORECAST_PRICES.items():
            gton_price = prices.get(key, 0)
            rub_price = gton_price * gton_rub_rate
            gton_str = format_gton_price(gton_price)
            text += f"{name}: <b>{gton_str} GTON</b> (~{rub_price:.0f} ₽)\n"
            keyboard.append([{
                "text": f"✏️ {name}",
                "callback_data": f"admin:services:edit_price:{service_id}:{key}"
            }])
        
        keyboard.append([{"text": "◀️ Назад", "callback_data": f"admin:services:prices:{service_id}"}])
        
        await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")
        return
    
    # Подменю для графика событий
    if submenu == "events":
        text = f"📊 <b>График событий — цены по периодам</b>\n\n"
        text += f"<i>Курс: 1 GTON ≈ {gton_rub_rate:.2f} ₽</i>\n\n"
        
        keyboard = []
        for key, name in ASTROLOGY_EVENTS_PRICES.items():
            gton_price = prices.get(key, 0)
            rub_price = gton_price * gton_rub_rate
            gton_str = format_gton_price(gton_price)
            text += f"{name}: <b>{gton_str} GTON</b> (~{rub_price:.0f} ₽)\n"
            keyboard.append([{
                "text": f"✏️ {name}",
                "callback_data": f"admin:services:edit_price:{service_id}:{key}"
            }])
        
        keyboard.append([{"text": "◀️ Назад", "callback_data": f"admin:services:prices:{service_id}"}])
        
        await query.edit_message_text(text, reply_markup=build_keyboard(keyboard), parse_mode="HTML")
        return
    
    # Основной прайс-лист
    text = f"💰 <b>Прайс-лист {service.name}</b>\n\n"
    text += f"<i>Курс: 1 GTON ≈ {gton_rub_rate:.2f} ₽</i>\n\n"
    
    keyboard = []
    
    for key, name in ASTROLOGY_PRICE_NAMES.items():
        gton_price = prices.get(key, 0)
        rub_price = gton_price * gton_rub_rate
        gton_str = format_gton_price(gton_price)
        text += f"{name}: <b>{gton_str} GTON</b> (~{rub_price:.0f} ₽)\n"
        
        keyboard.append([{
            "text": f"✏️ {name}",
            "callback_data": f"admin:services:edit_price:{service_id}:{key}"
        }])
    
    # Кнопки подменю
    keyboard.append([{
        "text": "📅 Астропрогноз (периоды)",
        "callback_data": f"admin:services:prices:{service_id}:forecast"
    }])
    keyboard.append([{
        "text": "📊 График событий (периоды)",
        "callback_data": f"admin:services:prices:{service_id}:events"
    }])
    
    keyboard.append([{"text": "◀️ Назад", "callback_data": f"admin:services:view:{service_id}"}])
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


def format_gton_price(gton_price) -> str:
    """Форматирует цену GTON"""
    if isinstance(gton_price, float) and gton_price != int(gton_price):
        return f"{gton_price:.4f}"
    else:
        return str(int(gton_price) if isinstance(gton_price, float) else gton_price)


async def edit_price_key(query, lang: str, service_id: str, price_key: str):
    """Start editing a price key"""
    from core.database.models import Service
    from core.plugins.core_api import CoreAPI
    
    async with get_db() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
    
    if not service:
        await query.answer("Сервис не найден", show_alert=True)
        return
    
    config = service.config or {}
    prices = config.get("prices", {})
    current_gton = prices.get(price_key, 0)
    
    # Получаем курс
    gton_rub_rate = await get_gton_to_rub_rate()
    current_rub = current_gton * gton_rub_rate
    
    price_name = ASTROLOGY_PRICE_NAMES.get(price_key, price_key)
    
    # Форматируем GTON
    if isinstance(current_gton, float) and current_gton != int(current_gton):
        gton_str = f"{current_gton:.4f}"
    else:
        gton_str = str(int(current_gton) if isinstance(current_gton, float) else current_gton)
    
    text = f"✏️ <b>{price_name}</b>\n\n"
    text += f"Текущая цена: <b>{gton_str} GTON</b> (~{current_rub:.0f} ₽)\n\n"
    text += f"<i>Курс: 1 GTON ≈ {gton_rub_rate:.2f} ₽</i>\n\n"
    text += "Введите новую цену <b>в рублях</b>:\n"
    text += "<i>(будет автоматически конвертирована в GTON)</i>"
    
    # Сохраняем состояние для ввода
    api = CoreAPI("core")
    user_id = query.from_user.id
    
    # Получаем внутренний user_id
    from core.platform.telegram.utils import get_or_create_user
    internal_user_id = await get_or_create_user(user_id, query.from_user)
    
    await api.set_user_state(internal_user_id, "admin_service_price_edit", {
        "service_id": service_id,
        "price_key": price_key,
    })
    
    keyboard = [
        [{"text": "❌ Отмена", "callback_data": f"admin:services:prices:{service_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )


async def handle_service_price_input(update, context, user_id: int, lang: str, service_id: str, price_key: str):
    """Handle text input for price editing"""
    from core.database.models import Service
    from core.plugins.core_api import CoreAPI
    from sqlalchemy.orm.attributes import flag_modified
    
    value = update.message.text.strip()
    
    # Парсим цену в рублях
    try:
        rub_price = float(value.replace(",", ".").replace(" ", ""))
        if rub_price < 0:
            await update.message.reply_text("❌ Цена не может быть отрицательной")
            return
    except ValueError:
        await update.message.reply_text("❌ Введите число (например, 100 или 150.50)")
        return
    
    # Конвертируем в GTON (4 знака после запятой)
    gton_rub_rate = await get_gton_to_rub_rate()
    gton_price = round(rub_price / gton_rub_rate, 4)
    
    async with get_db() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
        
        if not service:
            await update.message.reply_text("❌ Сервис не найден")
            return
        
        config = service.config or {}
        prices = config.get("prices", {})
        prices[price_key] = gton_price
        config["prices"] = prices
        service.config = config
        
        flag_modified(service, "config")
        await session.commit()
    
    # Очищаем состояние
    api = CoreAPI("core")
    await api.clear_user_state(user_id)
    
    # Определяем название и подменю для возврата
    price_name = ASTROLOGY_PRICE_NAMES.get(price_key)
    back_callback = f"admin:services:prices:{service_id}"
    
    if not price_name:
        price_name = ASTROLOGY_FORECAST_PRICES.get(price_key)
        if price_name:
            back_callback = f"admin:services:prices:{service_id}:forecast"
    
    if not price_name:
        price_name = ASTROLOGY_EVENTS_PRICES.get(price_key)
        if price_name:
            back_callback = f"admin:services:prices:{service_id}:events"
    
    if not price_name:
        price_name = price_key
    
    await update.message.reply_text(
        f"✅ Цена <b>{price_name}</b> обновлена!\n\n"
        f"Новая цена: <b>{gton_price:.4f} GTON</b> (~{rub_price:.0f} ₽)",
        parse_mode="HTML"
    )
    
    keyboard = [
        [{"text": "◀️ К прайс-листу", "callback_data": back_callback}]
    ]
    
    await update.message.reply_text(
        "Нажмите кнопку для возврата:",
        reply_markup=build_keyboard(keyboard)
    )


async def view_service_stats(query, lang: str, service_id: str):
    """View service statistics (for astrology)"""
    from core.database.models import Service
    from services.astrology.models import AstrologyReading
    from sqlalchemy import func
    
    async with get_db() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
    
    if not service:
        await query.answer("Сервис не найден", show_alert=True)
        return
    
    # Получаем курс для конвертации
    gton_rub_rate = await get_gton_to_rub_rate()
    
    text = f"📊 <b>Статистика {service.name}</b>\n\n"
    
    async with get_db() as session:
        # Статистика по типам чтений
        result = await session.execute(
            select(
                AstrologyReading.reading_type,
                func.count(AstrologyReading.id).label("count"),
                func.sum(AstrologyReading.gton_cost).label("total_gton")
            )
            .group_by(AstrologyReading.reading_type)
        )
        stats = result.all()
        
        total_count = 0
        total_gton = 0
        
        for reading_type, count, gton_sum in stats:
            gton_sum = gton_sum or 0
            rub_sum = gton_sum * gton_rub_rate
            
            type_name = ASTROLOGY_PRICE_NAMES.get(reading_type, reading_type or "Другое")
            text += f"{type_name}\n"
            text += f"   Использований: <b>{count}</b>\n"
            text += f"   Доход: <b>{gton_sum} GTON</b> (~{rub_sum:.0f} ₽)\n\n"
            
            total_count += count
            total_gton += gton_sum
        
        total_rub = total_gton * gton_rub_rate
        
        text += f"━━━━━━━━━━━━━━━━━━━━\n"
        text += f"📈 <b>Всего использований:</b> {total_count}\n"
        text += f"💰 <b>Общий доход:</b> {total_gton} GTON (~{total_rub:.0f} ₽)"
    
    keyboard = [
        [{"text": "◀️ Назад", "callback_data": f"admin:services:view:{service_id}"}]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
