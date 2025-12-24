"""
Astrology Service - Telegram Keyboards
"""
from typing import List, Optional
from decimal import Decimal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .texts import t
from .config import (
    RELATION_TYPES,
    FORECAST_PERIODS,
    EVENTS_PERIODS,
    LIFE_SPHERES,
    SUBSCRIPTION_PLANS,
    get_sign_emoji,
)


def build_keyboard(buttons: List[List[dict]]) -> InlineKeyboardMarkup:
    """
    Построить клавиатуру из списка кнопок.
    
    Args:
        buttons: [[{"text": "...", "callback_data": "..."}], ...]
    """
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for btn in row:
            keyboard_row.append(InlineKeyboardButton(
                text=btn["text"],
                callback_data=btn.get("callback_data"),
                url=btn.get("url"),
            ))
        keyboard.append(keyboard_row)
    return InlineKeyboardMarkup(keyboard)


# === Префикс для callback_data ===
PREFIX = "service:astrology"


def cb(action: str, *args) -> str:
    """Создать callback_data"""
    parts = [PREFIX, action] + [str(a) for a in args if a is not None]
    return ":".join(parts)


# === Главное меню ===

def main_menu_keyboard(
    prices: dict,
    has_profile: bool = True,
) -> InlineKeyboardMarkup:
    """Главное меню сервиса"""
    if not has_profile:
        return build_keyboard([
            [{"text": t("onboarding_start"), "callback_data": cb("onboard", "start")}],
            [{"text": t("btn_back"), "callback_data": "services"}],
        ])
    
    buttons = [
        # Анализ личности
        [{"text": f"{t('btn_natal_chart')} — {prices.get('natal_chart', 5)} GTON", "callback_data": cb("natal")}],
        [{"text": f"{t('btn_child_chart')} — {prices.get('child_chart', 6)} GTON", "callback_data": cb("child")}],
        [{"text": f"{t('btn_love_horoscope')} — {prices.get('love_portrait', 6)} GTON", "callback_data": cb("love")}],
        [{"text": f"❓ Задать вопрос Люцине — {prices.get('question', 5)} GTON", "callback_data": cb("question")}],
        
        # Прогнозы
        [{"text": f"{t('btn_daily_horoscope')} — {prices.get('daily_horoscope', 0.5)} GTON", "callback_data": cb("daily")}],
        [{"text": f"{t('btn_forecast')} — от {prices.get('forecast_week', 4)} GTON", "callback_data": cb("forecast")}],
        [{"text": f"{t('btn_events')} — от {prices.get('events_3days', 2)} GTON", "callback_data": cb("events")}],
        [{"text": f"{t('btn_transits')} — {prices.get('transits', 3)} GTON", "callback_data": cb("transits")}],
        
        # Отношения
        [{"text": f"{t('btn_compatibility')} — {prices.get('compatibility', 8)} GTON", "callback_data": cb("compat")}],
        
        # Управление
        [{"text": t("btn_my_charts"), "callback_data": cb("charts")}],
        [{"text": t("btn_history"), "callback_data": cb("history")}],
        [{"text": t("btn_subscriptions"), "callback_data": cb("subs")}],
        [{"text": t("btn_settings"), "callback_data": cb("settings")}],
        
        # Назад
        [{"text": t("btn_back"), "callback_data": "services"}],
    ]
    
    return build_keyboard(buttons)


# === Онбординг ===

def onboarding_welcome_keyboard() -> InlineKeyboardMarkup:
    """Приветствие онбординга"""
    return build_keyboard([
        [{"text": t("onboarding_start"), "callback_data": cb("onboard", "name")}],
        [{"text": t("btn_back"), "callback_data": "services"}],
    ])


def onboarding_time_unknown_keyboard() -> InlineKeyboardMarkup:
    """Время неизвестно"""
    return build_keyboard([
        [{"text": t("step_time_unknown"), "callback_data": cb("onboard", "time_unknown")}],
    ])


def onboarding_time_warning_keyboard() -> InlineKeyboardMarkup:
    """Предупреждение о времени"""
    return build_keyboard([
        [{"text": t("step_time_use_noon"), "callback_data": cb("onboard", "time_noon")}],
        [{"text": t("step_time_enter"), "callback_data": cb("onboard", "time_enter")}],
    ])


def onboarding_city_confirm_keyboard(city_index: int = 0) -> InlineKeyboardMarkup:
    """Подтверждение города"""
    return build_keyboard([
        [{"text": t("step_city_confirm"), "callback_data": cb("onboard", "city_confirm", city_index)}],
        [{"text": t("step_city_retry"), "callback_data": cb("onboard", "city_retry")}],
    ])


def onboarding_city_select_keyboard(cities: List[dict]) -> InlineKeyboardMarkup:
    """Выбор из нескольких городов"""
    buttons = []
    for i, city in enumerate(cities[:5]):
        buttons.append([{"text": city.get("city", ""), "callback_data": cb("onboard", "city_select", i)}])
    buttons.append([{"text": t("step_city_retry"), "callback_data": cb("onboard", "city_retry")}])
    return build_keyboard(buttons)


def onboarding_confirm_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение данных"""
    return build_keyboard([
        [{"text": t("confirm_save"), "callback_data": cb("onboard", "save")}],
        [{"text": t("confirm_edit"), "callback_data": cb("onboard", "edit")}],
    ])


def onboarding_time_selection_keyboard() -> InlineKeyboardMarkup:
    """Выбор времени для ежедневного гороскопа"""
    return build_keyboard([
        [{"text": "🌅 07:00", "callback_data": cb("onboard", "time_select", "07:00")}],
        [{"text": "☀️ 09:00", "callback_data": cb("onboard", "time_select", "09:00")}],
        [{"text": "🌤 12:00", "callback_data": cb("onboard", "time_select", "12:00")}],
        [{"text": "🌆 18:00", "callback_data": cb("onboard", "time_select", "18:00")}],
        [{"text": "🌙 21:00", "callback_data": cb("onboard", "time_select", "21:00")}],
        [{"text": "⏰ Другое время", "callback_data": cb("onboard", "time_custom")}],
        [{"text": "⏭ Пропустить", "callback_data": cb("onboard", "time_skip")}],
    ])


def onboarding_complete_keyboard() -> InlineKeyboardMarkup:
    """Профиль создан"""
    return build_keyboard([
        [{"text": t("profile_created_go"), "callback_data": cb("menu")}],
    ])


# === Натальная карта ===

def natal_confirm_keyboard(price: Decimal, balance: Decimal) -> InlineKeyboardMarkup:
    """Подтверждение генерации натальной карты"""
    can_afford = balance >= price
    buttons = []
    
    if can_afford:
        buttons.append([{"text": t("natal_generate"), "callback_data": cb("natal", "generate")}])
    else:
        buttons.append([{"text": "💳 Пополнить баланс", "callback_data": "balance:topup"}])
    
    buttons.append([{"text": t("btn_back"), "callback_data": cb("menu")}])
    return build_keyboard(buttons)


# === Детский гороскоп ===

def child_select_keyboard(children: List[dict]) -> InlineKeyboardMarkup:
    """Выбор ребёнка"""
    buttons = []
    
    for child in children:
        sign_emoji = get_sign_emoji(child.get("sun_sign", ""))
        text = f"👶 {child['name']} ({sign_emoji})"
        buttons.append([{"text": text, "callback_data": cb("child", "select", child["id"])}])
    
    buttons.append([{"text": t("child_add"), "callback_data": cb("charts", "add", "child")}])
    buttons.append([{"text": t("btn_back"), "callback_data": cb("menu")}])
    
    return build_keyboard(buttons)


def child_confirm_keyboard(chart_id: int, price: Decimal, balance: Decimal) -> InlineKeyboardMarkup:
    """Подтверждение детского гороскопа"""
    can_afford = balance >= price
    buttons = []
    
    if can_afford:
        buttons.append([{"text": t("child_generate"), "callback_data": cb("child", "generate", chart_id)}])
    else:
        buttons.append([{"text": "💳 Пополнить баланс", "callback_data": "balance:topup"}])
    
    buttons.append([{"text": t("btn_back"), "callback_data": cb("child")}])
    return build_keyboard(buttons)


# === Любовный гороскоп ===

def love_menu_keyboard(prices: dict) -> InlineKeyboardMarkup:
    """Меню любовного гороскопа"""
    return build_keyboard([
        [{"text": f"{t('love_portrait')} — {prices.get('love_portrait', 6)} GTON", "callback_data": cb("love", "portrait")}],
        [{"text": f"{t('love_compatibility')} — {prices.get('compatibility', 8)} GTON", "callback_data": cb("compat")}],
        [{"text": f"{t('love_relationship')} — {prices.get('relationship_analysis', 10)} GTON", "callback_data": cb("love", "relationship")}],
        [{"text": t("btn_back"), "callback_data": cb("menu")}],
    ])


# === Прогноз ===

def forecast_period_keyboard(prices: dict) -> InlineKeyboardMarkup:
    """Выбор периода прогноза"""
    buttons = []
    
    for key, data in FORECAST_PERIODS.items():
        price = prices.get(data["price_key"].replace("price_", ""), 0)
        buttons.append([{"text": f"{data['name']} — {price} GTON", "callback_data": cb("forecast", "period", key)}])
    
    buttons.append([{"text": t("btn_back"), "callback_data": cb("menu")}])
    return build_keyboard(buttons)


def forecast_spheres_keyboard(selected: List[str], period: str, price: Decimal) -> InlineKeyboardMarkup:
    """Выбор сфер жизни"""
    buttons = []
    
    for key, name in LIFE_SPHERES.items():
        check = "✅" if key in selected else "  "
        buttons.append([{"text": f"{check} {name}", "callback_data": cb("forecast", "sphere", period, key)}])
    
    buttons.append([{"text": f"{t('forecast_generate')} — {price} GTON", "callback_data": cb("forecast", "generate", period)}])
    buttons.append([{"text": t("btn_back"), "callback_data": cb("forecast")}])
    
    return build_keyboard(buttons)


# === График событий ===

def events_period_keyboard(prices: dict) -> InlineKeyboardMarkup:
    """Выбор периода графика событий"""
    buttons = []
    
    for key, data in EVENTS_PERIODS.items():
        price = prices.get(data["price_key"].replace("price_", ""), 0)
        buttons.append([{"text": f"{data['name']} — {price} GTON", "callback_data": cb("events", "period", key)}])
    
    buttons.append([{"text": t("btn_back"), "callback_data": cb("menu")}])
    return build_keyboard(buttons)


# === Совместимость ===

def compat_first_keyboard(my_chart: dict, saved_charts: List[dict]) -> InlineKeyboardMarkup:
    """Выбор первой карты для совместимости"""
    buttons = []
    
    # Моя карта
    sign_emoji = get_sign_emoji(my_chart.get("sun_sign", ""))
    buttons.append([{"text": f"⭐ Моя карта ({my_chart['name']} {sign_emoji})", "callback_data": cb("compat", "first", "me")}])
    
    # Сохранённые карты
    for chart in saved_charts:
        sign_emoji = get_sign_emoji(chart.get("sun_sign", ""))
        relation = RELATION_TYPES.get(chart.get("relation", ""), "")
        buttons.append([{"text": f"👤 {chart['name']} {sign_emoji} — {relation}", "callback_data": cb("compat", "first", chart["id"])}])
    
    buttons.append([{"text": t("btn_back"), "callback_data": cb("menu")}])
    return build_keyboard(buttons)


def compat_second_keyboard(first_id: str, saved_charts: List[dict], my_chart: Optional[dict] = None) -> InlineKeyboardMarkup:
    """Выбор второй карты для совместимости"""
    buttons = []
    
    # Моя карта (если первая не моя)
    if first_id != "me" and my_chart:
        sign_emoji = get_sign_emoji(my_chart.get("sun_sign", ""))
        buttons.append([{"text": f"⭐ Моя карта ({my_chart['name']} {sign_emoji})", "callback_data": cb("compat", "second", first_id, "me")}])
    
    # Сохранённые карты (кроме первой)
    for chart in saved_charts:
        if str(chart["id"]) == str(first_id):
            continue
        sign_emoji = get_sign_emoji(chart.get("sun_sign", ""))
        relation = RELATION_TYPES.get(chart.get("relation", ""), "")
        buttons.append([{"text": f"👤 {chart['name']} {sign_emoji} — {relation}", "callback_data": cb("compat", "second", first_id, chart["id"])}])
    
    buttons.append([{"text": t("compat_add_new"), "callback_data": cb("charts", "add")}])
    buttons.append([{"text": t("btn_back"), "callback_data": cb("compat")}])
    
    return build_keyboard(buttons)


def compat_confirm_keyboard(first_id: str, second_id: str, price: Decimal, balance: Decimal) -> InlineKeyboardMarkup:
    """Подтверждение совместимости"""
    can_afford = balance >= price
    buttons = []
    
    if can_afford:
        buttons.append([{"text": t("compat_generate"), "callback_data": cb("compat", "generate", first_id, second_id)}])
    else:
        buttons.append([{"text": "💳 Пополнить баланс", "callback_data": "balance:topup"}])
    
    buttons.append([{"text": t("btn_back"), "callback_data": cb("compat", "first", first_id)}])
    return build_keyboard(buttons)


# === Мои карты ===

def charts_list_keyboard(charts: List[dict], used: int, max_slots: int) -> InlineKeyboardMarkup:
    """Список сохранённых карт"""
    buttons = []
    
    for chart in charts:
        sign_emoji = get_sign_emoji(chart.get("sun_sign", ""))
        relation = RELATION_TYPES.get(chart.get("relation", ""), "")
        buttons.append([{"text": f"👤 {chart['name']} {sign_emoji} — {relation}", "callback_data": cb("charts", "view", chart["id"])}])
    
    if used < max_slots:
        buttons.append([{"text": t("charts_add"), "callback_data": cb("charts", "add")}])
    
    buttons.append([{"text": t("charts_buy_slots"), "callback_data": cb("charts", "slots")}])
    buttons.append([{"text": t("btn_back"), "callback_data": cb("menu")}])
    
    return build_keyboard(buttons)


def chart_view_keyboard(chart_id: int) -> InlineKeyboardMarkup:
    """Просмотр карты"""
    return build_keyboard([
        [{"text": "🌟 Астропортрет", "callback_data": cb("natal", "chart", chart_id)}],
        [{"text": "💑 Совместимость", "callback_data": cb("compat", "first", chart_id)}],
        [{"text": "🗑 Удалить", "callback_data": cb("charts", "delete", chart_id)}],
        [{"text": t("btn_back"), "callback_data": cb("charts")}],
    ])


def add_chart_relation_keyboard() -> InlineKeyboardMarkup:
    """Выбор типа отношений"""
    buttons = []
    
    for key, name in RELATION_TYPES.items():
        buttons.append([{"text": name, "callback_data": cb("charts", "add_relation", key)}])
    
    buttons.append([{"text": t("btn_back"), "callback_data": cb("charts")}])
    return build_keyboard(buttons)


def slots_keyboard(prices: dict) -> InlineKeyboardMarkup:
    """Покупка слотов"""
    return build_keyboard([
        [{"text": f"+5 слотов — {prices.get('slots_5', 3)} GTON", "callback_data": cb("charts", "buy_slots", 5)}],
        [{"text": f"+10 слотов — {prices.get('slots_10', 5)} GTON", "callback_data": cb("charts", "buy_slots", 10)}],
        [{"text": f"+20 слотов — {prices.get('slots_20', 8)} GTON", "callback_data": cb("charts", "buy_slots", 20)}],
        [{"text": t("btn_back"), "callback_data": cb("charts")}],
    ])


# === Подписки ===

def subscriptions_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню подписок"""
    return build_keyboard([
        [{"text": t("sub_daily"), "callback_data": cb("subs", "daily")}],
        [{"text": t("sub_weekly"), "callback_data": cb("subs", "weekly")}],
        [{"text": t("sub_my"), "callback_data": cb("subs", "my")}],
        [{"text": t("btn_back"), "callback_data": cb("menu")}],
    ])


def subscription_plans_keyboard(sub_type: str, prices: dict) -> InlineKeyboardMarkup:
    """Выбор тарифа подписки"""
    buttons = []
    
    if sub_type == "daily":
        buttons.append([{"text": f"7 дней — {prices.get('sub_daily_7d', 3)} GTON", "callback_data": cb("subs", "plan", "daily_7d")}])
        buttons.append([{"text": f"30 дней — {prices.get('sub_daily_30d', 10)} GTON", "callback_data": cb("subs", "plan", "daily_30d")}])
        buttons.append([{"text": f"90 дней — {prices.get('sub_daily_90d', 25)} GTON", "callback_data": cb("subs", "plan", "daily_90d")}])
    else:
        buttons.append([{"text": f"4 недели — {prices.get('sub_weekly_4w', 12)} GTON", "callback_data": cb("subs", "plan", "weekly_4w")}])
        buttons.append([{"text": f"12 недель — {prices.get('sub_weekly_12w', 30)} GTON", "callback_data": cb("subs", "plan", "weekly_12w")}])
        buttons.append([{"text": f"52 недели — {prices.get('sub_weekly_52w', 100)} GTON", "callback_data": cb("subs", "plan", "weekly_52w")}])
    
    buttons.append([{"text": t("btn_back"), "callback_data": cb("subs")}])
    return build_keyboard(buttons)


def subscription_time_keyboard(plan: str) -> InlineKeyboardMarkup:
    """Выбор времени отправки"""
    return build_keyboard([
        [{"text": t("sub_time_morning"), "callback_data": cb("subs", "time", plan, "07:00")}],
        [{"text": t("sub_time_day"), "callback_data": cb("subs", "time", plan, "09:00")}],
        [{"text": t("sub_time_evening"), "callback_data": cb("subs", "time", plan, "21:00")}],
        [{"text": t("sub_time_custom"), "callback_data": cb("subs", "time_custom", plan)}],
        [{"text": t("btn_back"), "callback_data": cb("subs", "daily" if "daily" in plan else "weekly")}],
    ])


def subscription_success_keyboard() -> InlineKeyboardMarkup:
    """Подписка оформлена"""
    return build_keyboard([
        [{"text": t("sub_go_menu"), "callback_data": cb("menu")}],
    ])


def subscription_expiring_keyboard(has_balance: bool) -> InlineKeyboardMarkup:
    """Уведомление об окончании подписки"""
    buttons = []
    
    if has_balance:
        buttons.append([{"text": t("sub_renew_now"), "callback_data": cb("subs", "renew")}])
    else:
        buttons.append([{"text": t("sub_topup"), "callback_data": "balance:topup"}])
    
    buttons.append([{"text": t("sub_cancel_auto"), "callback_data": cb("subs", "cancel_auto")}])
    
    return build_keyboard(buttons)


# === Общие ===

def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад в меню"""
    return build_keyboard([
        [{"text": t("btn_back"), "callback_data": cb("menu")}],
    ])


def confirm_action_keyboard(action: str, item_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Подтверждение действия"""
    return build_keyboard([
        [{"text": "✅ Да", "callback_data": cb(action, "confirm", item_id)}],
        [{"text": "❌ Нет", "callback_data": cb(action, "cancel")}],
    ])


# === LIST versions (для Response) ===

def main_menu_keyboard_list(prices: dict, has_profile: bool = True) -> List[List[dict]]:
    """Главное меню сервиса (список)"""
    if not has_profile:
        return [
            [{"text": t("onboarding_start"), "callback_data": cb("onboard", "start")}],
            [{"text": t("btn_back"), "callback_data": "main_menu"}],
        ]
    
    return [
        [{"text": f"{t('btn_natal_chart')} — {prices.get('natal_chart', 5)} GTON", "callback_data": cb("natal")}],
        [{"text": f"{t('btn_child_chart')} — {prices.get('child_chart', 6)} GTON", "callback_data": cb("child")}],
        [{"text": f"{t('btn_love_horoscope')} — {prices.get('love_portrait', 6)} GTON", "callback_data": cb("love")}],
        [{"text": f"❓ Задать вопрос Люцине — {prices.get('question', 5)} GTON", "callback_data": cb("question")}],
        [{"text": f"{t('btn_daily_horoscope')} — {prices.get('daily_horoscope', 0.5)} GTON", "callback_data": cb("daily")}],
        [{"text": f"{t('btn_forecast')} — от {prices.get('forecast_week', 4)} GTON", "callback_data": cb("forecast")}],
        [{"text": f"{t('btn_events')} — от {prices.get('events_3days', 2)} GTON", "callback_data": cb("events")}],
        [{"text": f"{t('btn_transits')} — {prices.get('transits', 3)} GTON", "callback_data": cb("transits")}],
        [{"text": f"{t('btn_compatibility')} — {prices.get('compatibility', 8)} GTON", "callback_data": cb("compat")}],
        [{"text": t("btn_back"), "callback_data": "main_menu"}],
    ]


def onboarding_welcome_keyboard_list() -> List[List[dict]]:
    """Приветствие онбординга (список)"""
    return [
        [{"text": t("onboarding_start"), "callback_data": cb("onboard", "name")}],
        [{"text": t("btn_back"), "callback_data": "main_menu"}],
    ]


def onboarding_time_unknown_keyboard_list() -> List[List[dict]]:
    """Время неизвестно (список)"""
    return [
        [{"text": t("step_time_unknown"), "callback_data": cb("onboard", "time_unknown")}],
    ]


def onboarding_time_warning_keyboard_list() -> List[List[dict]]:
    """Предупреждение о времени (список)"""
    return [
        [{"text": t("step_time_use_noon"), "callback_data": cb("onboard", "time_noon")}],
        [{"text": t("step_time_enter"), "callback_data": cb("onboard", "time_enter")}],
    ]


def onboarding_city_confirm_keyboard_list(city_index: int = 0) -> List[List[dict]]:
    """Подтверждение города (список)"""
    return [
        [{"text": t("step_city_confirm"), "callback_data": cb("onboard", "city_confirm", city_index)}],
        [{"text": t("step_city_retry"), "callback_data": cb("onboard", "city_retry")}],
    ]


def onboarding_confirm_keyboard_list() -> List[List[dict]]:
    """Подтверждение данных (список)"""
    return [
        [{"text": t("confirm_save"), "callback_data": cb("onboard", "save")}],
        [{"text": t("confirm_edit"), "callback_data": cb("onboard", "edit")}],
    ]


def onboarding_time_selection_keyboard_list() -> List[List[dict]]:
    """Выбор времени для ежедневного гороскопа (список)"""
    return [
        [{"text": "🌅 07:00", "callback_data": cb("onboard", "time_select", "07:00")}],
        [{"text": "☀️ 09:00", "callback_data": cb("onboard", "time_select", "09:00")}],
        [{"text": "🌤 12:00", "callback_data": cb("onboard", "time_select", "12:00")}],
        [{"text": "🌆 18:00", "callback_data": cb("onboard", "time_select", "18:00")}],
        [{"text": "🌙 21:00", "callback_data": cb("onboard", "time_select", "21:00")}],
        [{"text": "⏰ Другое время", "callback_data": cb("onboard", "time_custom")}],
        [{"text": "⏭ Пропустить", "callback_data": cb("onboard", "time_skip")}],
    ]


def onboarding_complete_keyboard_list() -> List[List[dict]]:
    """Профиль создан (список)"""
    return [
        [{"text": t("profile_created_go"), "callback_data": cb("menu")}],
    ]


def back_to_menu_keyboard_list(back_to: str = None) -> List[List[dict]]:
    """
    Кнопка назад в меню (список)
    
    Args:
        back_to: Куда вернуться ("main_menu" или None для меню сервиса)
    """
    callback = back_to if back_to else cb("menu")
    return [
        [{"text": t("btn_back"), "callback_data": callback}],
    ]


def natal_confirm_keyboard_list(price, balance) -> List[List[dict]]:
    """Подтверждение генерации натальной карты (список)"""
    can_afford = balance >= price
    buttons = []
    
    if can_afford:
        buttons.append([{"text": t("natal_generate"), "callback_data": cb("natal", "generate")}])
    else:
        buttons.append([{"text": "💳 Пополнить баланс", "callback_data": "top_up"}])
    
    buttons.append([{"text": t("btn_back"), "callback_data": cb("menu")}])
    return buttons


def daily_confirm_keyboard_list(price, balance, is_free: bool = False) -> List[List[dict]]:
    """Подтверждение ежедневного гороскопа (список)"""
    buttons = []
    
    if is_free:
        buttons.append([{"text": "🎁 Получить бесплатно", "callback_data": cb("daily", "generate")}])
    elif balance >= price:
        buttons.append([{"text": f"✨ Получить за {price} GTON", "callback_data": cb("daily", "generate")}])
    else:
        buttons.append([{"text": "💳 Пополнить баланс", "callback_data": "top_up"}])
    
    buttons.append([{"text": t("btn_back"), "callback_data": cb("menu")}])
    return buttons
