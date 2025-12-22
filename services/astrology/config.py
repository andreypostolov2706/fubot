"""
Astrology Service - Configuration
"""
import os
from decimal import Decimal
from pathlib import Path


# === Paths ===
SERVICE_DIR = Path(__file__).parent
PROMPTS_DIR = SERVICE_DIR / "prompts"
CHARTS_DIR = Path(__file__).parent.parent.parent / "data" / "charts"

# Ensure charts directory exists
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


# === DeepSeek API ===
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


# === Default Prices (GTON) ===
DEFAULT_PRICES = {
    # Анализ личности
    "price_natal_chart": Decimal("5.0"),
    "price_child_chart": Decimal("6.0"),
    "price_love_portrait": Decimal("6.0"),
    
    # Прогнозы
    "price_daily_horoscope": Decimal("0.5"),
    "price_forecast_week": Decimal("4.0"),
    "price_forecast_month": Decimal("8.0"),
    "price_forecast_3months": Decimal("15.0"),
    "price_forecast_year": Decimal("40.0"),
    
    # График событий
    "price_events_3days": Decimal("2.0"),
    "price_events_week": Decimal("4.0"),
    "price_events_month": Decimal("7.0"),
    "price_events_3months": Decimal("15.0"),
    "price_events_year": Decimal("35.0"),
    "price_events_2years": Decimal("50.0"),
    
    # Транзиты и совместимость
    "price_transits": Decimal("3.0"),
    "price_compatibility": Decimal("8.0"),
    "price_relationship_analysis": Decimal("10.0"),
    
    # Вопрос астрологу
    "price_question": Decimal("5.0"),
    
    # Подписки - ежедневный гороскоп
    "price_sub_daily_7d": Decimal("3.0"),
    "price_sub_daily_30d": Decimal("10.0"),
    "price_sub_daily_90d": Decimal("25.0"),
    
    # Подписки - еженедельный прогноз
    "price_sub_weekly_4w": Decimal("12.0"),
    "price_sub_weekly_12w": Decimal("30.0"),
    "price_sub_weekly_52w": Decimal("100.0"),
    
    # Слоты для карт
    "price_slots_5": Decimal("3.0"),
    "price_slots_10": Decimal("5.0"),
    "price_slots_20": Decimal("8.0"),
}

# === Default Limits ===
DEFAULT_LIMITS = {
    "default_max_charts": 10,
}


# === Price Keys Display Names (for admin panel) ===
PRICE_KEY_NAMES = {
    "price_natal_chart": "Астропортрет",
    "price_child_chart": "Детский гороскоп",
    "price_love_portrait": "Любовный портрет",
    "price_daily_horoscope": "Гороскоп на сегодня",
    "price_forecast_week": "Прогноз на неделю",
    "price_forecast_month": "Прогноз на месяц",
    "price_forecast_3months": "Прогноз на 3 месяца",
    "price_forecast_year": "Прогноз на год",
    "price_events_3days": "События 3 дня",
    "price_events_week": "События неделя",
    "price_events_month": "События месяц",
    "price_events_3months": "События 3 месяца",
    "price_events_year": "События год",
    "price_events_2years": "События 2 года",
    "price_transits": "Транзиты сейчас",
    "price_compatibility": "Совместимость",
    "price_relationship_analysis": "Анализ отношений",
    "price_question": "Вопрос астрологу",
    "price_sub_daily_7d": "Подписка 7 дней",
    "price_sub_daily_30d": "Подписка 30 дней",
    "price_sub_daily_90d": "Подписка 90 дней",
    "price_sub_weekly_4w": "Еженедельная 4 нед",
    "price_sub_weekly_12w": "Еженедельная 12 нед",
    "price_sub_weekly_52w": "Еженедельная 52 нед",
    "price_slots_5": "+5 слотов",
    "price_slots_10": "+10 слотов",
    "price_slots_20": "+20 слотов",
    "default_max_charts": "Лимит карт",
}


# === Relation Types ===
RELATION_TYPES = {
    "partner": "💕 Партнёр",
    "child": "👶 Ребёнок",
    "family": "👨‍👩‍👧 Родственник",
    "friend": "👫 Друг",
    "colleague": "👔 Коллега",
    "other": "❓ Другое",
}


# === Reading Types ===
READING_TYPES = {
    "natal": "Астропортрет",
    "child": "Детский гороскоп",
    "love": "Любовный гороскоп",
    "daily": "Гороскоп на сегодня",
    "forecast": "Астропрогноз",
    "events": "График событий",
    "transit": "Транзиты",
    "compatibility": "Совместимость",
    "relationship": "Анализ отношений",
    "question": "Вопрос астрологу",
}


# === Subscription Plans ===
SUBSCRIPTION_PLANS = {
    "daily_7d": {"days": 7, "price_key": "price_sub_daily_7d", "type": "daily"},
    "daily_30d": {"days": 30, "price_key": "price_sub_daily_30d", "type": "daily"},
    "daily_90d": {"days": 90, "price_key": "price_sub_daily_90d", "type": "daily"},
    "weekly_4w": {"days": 28, "price_key": "price_sub_weekly_4w", "type": "weekly"},
    "weekly_12w": {"days": 84, "price_key": "price_sub_weekly_12w", "type": "weekly"},
    "weekly_52w": {"days": 364, "price_key": "price_sub_weekly_52w", "type": "weekly"},
}


# === Forecast Periods ===
FORECAST_PERIODS = {
    "week": {"days": 7, "price_key": "price_forecast_week", "name": "Неделя"},
    "month": {"days": 30, "price_key": "price_forecast_month", "name": "Месяц"},
    "3months": {"days": 90, "price_key": "price_forecast_3months", "name": "3 месяца"},
    "year": {"days": 365, "price_key": "price_forecast_year", "name": "Год"},
}


# === Events Periods ===
EVENTS_PERIODS = {
    "3days": {"days": 3, "price_key": "price_events_3days", "name": "3 дня"},
    "week": {"days": 7, "price_key": "price_events_week", "name": "Неделя"},
    "month": {"days": 30, "price_key": "price_events_month", "name": "Месяц"},
    "3months": {"days": 90, "price_key": "price_events_3months", "name": "3 месяца"},
    "year": {"days": 365, "price_key": "price_events_year", "name": "Год"},
    "2years": {"days": 730, "price_key": "price_events_2years", "name": "2 года"},
}


# === Life Spheres for Forecast ===
LIFE_SPHERES = {
    "general": "🎯 Общий прогноз",
    "career": "💼 Работа и карьера",
    "finance": "💰 Финансы",
    "love": "💕 Отношения",
    "health": "🏥 Здоровье",
    "education": "🎓 Обучение",
}


# === Zodiac Signs ===
ZODIAC_SIGNS = {
    "Ari": {"name": "Овен", "emoji": "♈"},
    "Tau": {"name": "Телец", "emoji": "♉"},
    "Gem": {"name": "Близнецы", "emoji": "♊"},
    "Can": {"name": "Рак", "emoji": "♋"},
    "Leo": {"name": "Лев", "emoji": "♌"},
    "Vir": {"name": "Дева", "emoji": "♍"},
    "Lib": {"name": "Весы", "emoji": "♎"},
    "Sco": {"name": "Скорпион", "emoji": "♏"},
    "Sag": {"name": "Стрелец", "emoji": "♐"},
    "Cap": {"name": "Козерог", "emoji": "♑"},
    "Aqu": {"name": "Водолей", "emoji": "♒"},
    "Pis": {"name": "Рыбы", "emoji": "♓"},
}


def get_sign_display(sign_code: str) -> str:
    """Get display name with emoji for zodiac sign"""
    sign = ZODIAC_SIGNS.get(sign_code, {})
    return f"{sign.get('emoji', '')} {sign.get('name', sign_code)}"


def get_sign_emoji(sign_code: str) -> str:
    """Get emoji for zodiac sign"""
    return ZODIAC_SIGNS.get(sign_code, {}).get("emoji", "")


def get_sign_name(sign_code: str) -> str:
    """Get Russian name for zodiac sign"""
    return ZODIAC_SIGNS.get(sign_code, {}).get("name", sign_code)
