"""
Astrology Service - Main Service Class
"""
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from loguru import logger

from core.plugins.base_service import (
    BaseService, ServiceInfo, MenuItem, Response, 
    CallbackContext, MessageContext, MessageDTO
)
from core.plugins.core_api import CoreAPI
from core.database import get_db

from .models import UserAstrologyProfile, SavedChart, AstrologyReading, DailyHoroscopeLog
from .config import (
    DEFAULT_PRICES, DEFAULT_LIMITS, PRICE_KEY_NAMES,
    RELATION_TYPES, READING_TYPES, SUBSCRIPTION_PLANS,
    FORECAST_PERIODS, EVENTS_PERIODS, LIFE_SPHERES,
    get_sign_display, get_sign_emoji, get_sign_name,
)
from .texts import t
from .geocoder import geocoder, GeoLocation
from .calculator import chart_calculator, ChartData
from .interpreter import interpreter
from .renderer import renderer
from . import keyboards as kb


class AstrologyService(BaseService):
    """
    Сервис персональной астрологии.
    
    Функции:
    - Натальные карты
    - Ежедневные гороскопы
    - Прогнозы на период
    - Совместимость
    - Детские гороскопы
    """
    
    @property
    def info(self) -> ServiceInfo:
        return ServiceInfo(
            id="astrology",
            name="Астрология",
            description="Персональные натальные карты и AI-интерпретации",
            version="1.0.0",
            author="FuBot",
            icon="🔮",
        )
    
    @property
    def permissions(self) -> List[str]:
        return ["balance", "user_data", "notifications"]
    
    @property
    def features(self) -> Dict[str, bool]:
        return {
            "subscriptions": True,
            "broadcasts": False,
            "partner_menu": False,
            "voice_messages": False,
        }
    
    async def install(self) -> bool:
        """Установка сервиса"""
        # Инициализируем конфиг с ценами по умолчанию
        config = await self.core.get_service_config()
        
        if "prices" not in config:
            config["prices"] = {k.replace("price_", ""): str(v) for k, v in DEFAULT_PRICES.items()}
        
        if "limits" not in config:
            config["limits"] = DEFAULT_LIMITS.copy()
        
        await self.core.update_service_config(config)
        
        logger.info("Astrology service installed")
        return True
    
    async def uninstall(self) -> bool:
        """Удаление сервиса"""
        logger.info("Astrology service uninstalled")
        return True
    
    def get_user_menu_items(self, user_id: int, user_data) -> List[MenuItem]:
        """Пункты меню для пользователя"""
        # Все пункты уже добавлены в main_menu.py
        return []
    
    def get_loading_text(self, action: str, params: dict = None) -> Optional[str]:
        """Текст загрузки для долгих операций"""
        # Показываем loading только для действий генерации
        # params содержит id/0 - первый параметр после action
        param_id = params.get("id", "") if params else ""
        
        # Для onboard:save - сохранение профиля
        if action == "onboard" and param_id == "save":
            return "⏳ Рассчитываю вашу натальную карту..."
        
        # Для генерации интерпретаций
        if param_id == "generate":
            loading_texts = {
                "natal": "⏳ Готовлю ваш астропортрет...",
                "daily": "⏳ Составляю гороскоп на сегодня...",
                "child": "⏳ Готовлю детский гороскоп...",
                "love": "⏳ Анализирую любовную сферу...",
                "forecast": "⏳ Составляю прогноз...",
                "events": "⏳ Анализирую астрособытия...",
                "transits": "⏳ Анализирую транзиты...",
                "compat": "⏳ Анализирую совместимость...",
            }
            return loading_texts.get(action)
        
        return None
    
    def get_admin_menu_items(self) -> List[MenuItem]:
        """Пункты меню для админа"""
        return []
    
    # === Helpers ===
    
    async def get_price(self, price_key: str) -> Decimal:
        """Получить цену услуги"""
        config = await self.core.get_service_config()
        prices = config.get("prices", {})
        key = price_key.replace("price_", "")
        default = DEFAULT_PRICES.get(f"price_{key}", Decimal("0"))
        return Decimal(str(prices.get(key, default)))
    
    async def get_prices_dict(self) -> Dict[str, Decimal]:
        """Получить все цены"""
        config = await self.core.get_service_config()
        prices = config.get("prices", {})
        result = {}
        for key, default in DEFAULT_PRICES.items():
            k = key.replace("price_", "")
            result[k] = Decimal(str(prices.get(k, default)))
        return result
    
    async def get_profile(self, user_id: int) -> Optional[UserAstrologyProfile]:
        """Получить профиль пользователя"""
        async with get_db() as session:
            result = await session.execute(
                select(UserAstrologyProfile)
                .where(UserAstrologyProfile.user_id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def get_saved_charts(self, user_id: int) -> List[SavedChart]:
        """Получить сохранённые карты"""
        async with get_db() as session:
            result = await session.execute(
                select(SavedChart)
                .where(SavedChart.user_id == user_id)
                .order_by(SavedChart.created_at.desc())
            )
            return list(result.scalars().all())
    
    async def get_saved_chart(self, chart_id: int) -> Optional[SavedChart]:
        """Получить сохранённую карту по ID"""
        async with get_db() as session:
            result = await session.execute(
                select(SavedChart).where(SavedChart.id == chart_id)
            )
            return result.scalar_one_or_none()
    
    async def check_referral_bonus(self, user_id: int) -> bool:
        """Проверить, пришёл ли пользователь по реферальной ссылке"""
        user = await self.core.get_user(user_id)
        return user.referrer_id is not None if user else False
    
    # === Main Handler ===
    
    async def handle_callback(
        self, 
        user_id: int, 
        action: str, 
        params: dict,
        context: CallbackContext
    ) -> Response:
        """Обработка callback"""
        # Преобразуем params dict в список для совместимости
        params_list = []
        if params.get("id"):
            params_list.append(params["id"])
        if params.get("1"):
            params_list.append(params["1"])
        if params.get("2"):
            params_list.append(params["2"])
        
        handlers = {
            "menu": self._handle_menu,
            "onboard": self._handle_onboard,
            "natal": self._handle_natal,
            "child": self._handle_child,
            "love": self._handle_love,
            "daily": self._handle_daily,
            "daily_toggle": self._handle_daily_toggle,
            "forecast": self._handle_forecast,
            "events": self._handle_events,
            "transits": self._handle_transits,
            "compat": self._handle_compat,
            "question": self._handle_question,
            "charts": self._handle_charts,
            "history": self._handle_history,
            "subs": self._handle_subs,
            "settings": self._handle_settings,
        }
        
        handler = handlers.get(action)
        if handler:
            return await handler(user_id, params_list, context)
        
        return Response(text="Неизвестное действие", action="answer")
    
    async def handle_message(
        self,
        user_id: int,
        message: MessageDTO,
        context: MessageContext
    ) -> Response:
        """Обработка текстовых сообщений"""
        state_name, state_data = await self.core.get_user_state(user_id)
        if not state_name or not state_name.startswith("astro_"):
            return Response(text="", action="ignore")
        
        state_data = state_data or {}
        text = (message.text or "").strip()
        
        # Онбординг
        if state_name == "astro_onboard_name":
            return await self._process_onboard_name(user_id, text, state_data, context)
        
        elif state_name == "astro_onboard_date":
            return await self._process_onboard_date(user_id, text, state_data, context)
        
        elif state_name == "astro_onboard_time":
            return await self._process_onboard_time(user_id, text, state_data, context)
        
        elif state_name == "astro_onboard_city":
            return await self._process_onboard_city(user_id, text, state_data, context)
        
        # Добавление карты
        elif state_name == "astro_add_chart_name":
            return await self._process_add_chart_name(user_id, text, state_data, context)
        
        elif state_name == "astro_add_chart_date":
            return await self._process_add_chart_date(user_id, text, state_data, context)
        
        elif state_name == "astro_add_chart_time":
            return await self._process_add_chart_time(user_id, text, state_data, context)
        
        elif state_name == "astro_add_chart_city":
            return await self._process_add_chart_city(user_id, text, state_data, context)
        
        # Редактирование профиля
        elif state_name == "astro_edit_name":
            return await self._process_edit_name(user_id, text, context)
        
        elif state_name == "astro_edit_date":
            return await self._process_edit_date(user_id, text, context)
        
        elif state_name == "astro_edit_time":
            return await self._process_edit_time(user_id, text, context)
        
        elif state_name == "astro_edit_city":
            return await self._process_edit_city(user_id, text, state_data, context)
        
        # Вопрос астрологу
        elif state_name == "astro_question_text":
            return await self._process_question_text(user_id, text, state_data, context)
        
        return Response(text="", action="ignore")
    
    def _require_profile_response(self) -> Response:
        """Ответ когда требуется профиль"""
        return Response(
            text="⚠️ Для использования этой функции необходимо создать профиль.\n\nВведите ваши данные рождения, чтобы получить доступ ко всем возможностям астрологии.",
            keyboard=[
                [{"text": "✨ Создать профиль", "callback_data": kb.cb("onboard", "start")}],
                [{"text": t("btn_back"), "callback_data": kb.cb("menu")}],
            ],
        )
    
    # === Menu Handler ===
    
    async def _handle_menu(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Главное меню"""
        profile = await self.get_profile(user_id)
        prices = await self.get_prices_dict()
        
        if not profile:
            # Показываем онбординг
            has_referral = await self.check_referral_bonus(user_id)
            text = t("onboarding_welcome_referral") if has_referral else t("onboarding_welcome")
            
            return Response(
                text=text,
                keyboard=kb.onboarding_welcome_keyboard_list(),
            )
        
        # Показываем главное меню
        sun_display = get_sign_display(profile.sun_sign or "")
        asc_display = get_sign_display(profile.ascendant_sign or "")
        
        text = f"{t('menu_title')}\n\n"
        text += t("menu_subtitle", sun_sign=sun_display, asc_sign=asc_display)
        
        return Response(
            text=text,
            keyboard=kb.main_menu_keyboard_list(prices, has_profile=True),
        )
    
    # === Onboarding Handlers ===
    
    async def _handle_onboard(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка онбординга"""
        if not params:
            return Response(text="Ошибка", action="answer")
        
        action = params[0]
        
        if action == "start" or action == "name":
            # Шаг 1: Имя
            await self.core.set_user_state(user_id, "astro_onboard_name", {})
            return Response(
                text=f"{t('step_name_title')}\n\n{t('step_name_text')}",
                set_state="astro_onboard_name",
            )
        
        elif action == "time_unknown":
            # Показываем предупреждение
            return Response(
                text=f"{t('step_time_warning_title')}\n\n{t('step_time_warning_text')}",
                keyboard=kb.onboarding_time_warning_keyboard_list(),
            )
        
        elif action == "time_noon":
            # Используем 12:00
            state_name, state_data = await self.core.get_user_state(user_id)
            state_data = state_data or {}
            state_data["birth_time"] = "12:00"
            state_data["time_unknown"] = True
            
            await self.core.set_user_state(user_id, "astro_onboard_city", state_data)
            return Response(
                text=f"{t('step_city_title')}\n\n{t('step_city_text')}",
                set_state="astro_onboard_city",
                state_data=state_data,
            )
        
        elif action == "time_enter":
            # Возвращаемся к вводу времени
            state_name, state_data = await self.core.get_user_state(user_id)
            state_data = state_data or {}
            
            await self.core.set_user_state(user_id, "astro_onboard_time", state_data)
            return Response(
                text=f"{t('step_time_title')}\n\n{t('step_time_text')}",
                keyboard=kb.onboarding_time_unknown_keyboard_list(),
                set_state="astro_onboard_time",
                state_data=state_data,
            )
        
        elif action == "city_confirm":
            # Подтверждение города
            city_index = int(params[1]) if len(params) > 1 else 0
            state_name, state_data = await self.core.get_user_state(user_id)
            state_data = state_data or {}
            
            cities = state_data.get("cities", [])
            if city_index < len(cities):
                city = cities[city_index]
                state_data["city"] = city["city"]
                state_data["lat"] = city["lat"]
                state_data["lng"] = city["lng"]
                state_data["tz"] = city["tz"]
            
            return await self._show_onboard_confirm(user_id, state_data)
        
        elif action == "city_select":
            # Выбор города из списка
            city_index = int(params[1]) if len(params) > 1 else 0
            state_name, state_data = await self.core.get_user_state(user_id)
            state_data = state_data or {}
            
            cities = state_data.get("cities", [])
            if city_index < len(cities):
                city = cities[city_index]
                state_data["city"] = city["city"]
                state_data["lat"] = city["lat"]
                state_data["lng"] = city["lng"]
                state_data["tz"] = city["tz"]
            
            return await self._show_onboard_confirm(user_id, state_data)
        
        elif action == "city_retry":
            # Повторный ввод города
            state_name, state_data = await self.core.get_user_state(user_id)
            state_data = state_data or {}
            
            await self.core.set_user_state(user_id, "astro_onboard_city", state_data)
            return Response(
                text=f"{t('step_city_title')}\n\n{t('step_city_text')}",
                set_state="astro_onboard_city",
                state_data=state_data,
            )
        
        elif action == "edit":
            # Редактирование - начинаем сначала
            await self.core.set_user_state(user_id, "astro_onboard_name", {})
            return Response(
                text=f"{t('step_name_title')}\n\n{t('step_name_text')}",
                set_state="astro_onboard_name",
            )
        
        elif action == "save":
            # Сохранение профиля
            return await self._save_profile(user_id)
        
        return Response(text="Неизвестное действие", action="answer")
    
    async def _show_onboard_confirm(self, user_id: int, state_data: dict) -> Response:
        """Показать подтверждение данных"""
        birth_date = state_data.get("birth_date", "")
        
        text = f"{t('confirm_title')}\n\n"
        text += t("confirm_name", name=state_data.get("name", "")) + "\n"
        text += t("confirm_date", date=birth_date) + "\n"
        text += t("confirm_time", time=state_data.get("birth_time", "")) + "\n"
        text += t("confirm_city", city=state_data.get("city", ""))
        
        await self.core.set_user_state(user_id, "astro_onboard_confirm", state_data)
        return Response(
            text=text,
            keyboard=kb.onboarding_confirm_keyboard_list(),
            set_state="astro_onboard_confirm",
            state_data=state_data,
        )
    
    async def _save_profile(self, user_id: int) -> Response:
        """Сохранить профиль"""
        state_name, state_data = await self.core.get_user_state(user_id)
        state_data = state_data or {}
        
        # Парсим данные
        name = state_data.get("name", "")
        birth_date_str = state_data.get("birth_date", "")
        birth_time_str = state_data.get("birth_time", "12:00")
        city = state_data.get("city", "")
        lat = state_data.get("lat", 0.0)
        lng = state_data.get("lng", 0.0)
        tz = state_data.get("tz", "UTC")
        time_unknown = state_data.get("time_unknown", False)
        
        # Парсим дату и время
        try:
            day, month, year = birth_date_str.split(".")
            birth_date = date(int(year), int(month), int(day))
        except:
            birth_date = date.today()
        
        try:
            hour, minute = birth_time_str.split(":")
            birth_time = time(int(hour), int(minute))
        except:
            birth_time = time(12, 0)
        
        # Рассчитываем карту
        chart_data = await chart_calculator.calculate_natal_chart(
            name=name,
            birth_date=birth_date,
            birth_time=birth_time,
            lat=lat,
            lng=lng,
            tz_str=tz,
        )
        
        # Генерируем SVG
        svg_path = await chart_calculator.generate_svg(
            name=name,
            birth_date=birth_date,
            birth_time=birth_time,
            lat=lat,
            lng=lng,
            tz_str=tz,
            user_id=user_id,
            chart_type="natal",
        )
        
        # Проверяем реферальный бонус
        has_referral = await self.check_referral_bonus(user_id)
        
        # Сохраняем в БД
        async with get_db() as session:
            profile = UserAstrologyProfile(
                user_id=user_id,
                name=name,
                birth_date=birth_date,
                birth_time=birth_time,
                birth_time_unknown=time_unknown,
                birth_city=city,
                birth_lat=lat,
                birth_lng=lng,
                birth_tz=tz,
                sun_sign=chart_data.sun_sign,
                moon_sign=chart_data.moon_sign,
                ascendant_sign=chart_data.ascendant_sign,
                chart_data=chart_data.to_dict(),
                svg_path=svg_path,
                has_referral_bonus=has_referral,
                free_horoscope_used=False,
                max_saved_charts=DEFAULT_LIMITS.get("default_max_charts", 10),
            )
            session.add(profile)
            await session.commit()
        
        # Очищаем состояние
        await self.core.clear_user_state(user_id)
        
        # Показываем результат
        text = f"{t('profile_created_title')}\n\n"
        text += f"☀️ Солнце в {get_sign_name(chart_data.sun_sign)}\n"
        text += f"🌙 Луна в {get_sign_name(chart_data.moon_sign)}\n"
        text += f"⬆️ Асцендент в {get_sign_name(chart_data.ascendant_sign)}\n\n"
        text += t("profile_created_text")
        
        return Response(
            text=text,
            keyboard=kb.onboarding_complete_keyboard_list(),
            clear_state=True,
            media_path=svg_path,
            media_type="document",
        )
    
    # === Message Processors for Onboarding ===
    
    async def _process_onboard_name(self, user_id: int, text: str, state_data: dict, context: MessageContext) -> Response:
        """Обработка ввода имени"""
        if len(text) < 2 or len(text) > 50:
            return Response(text="Введите имя от 2 до 50 символов", action="send")
        
        state_data["name"] = text
        await self.core.set_user_state(user_id, "astro_onboard_date", state_data)
        
        return Response(
            text=f"{t('step_date_title')}\n\n{t('step_date_text')}",
            action="send",
            set_state="astro_onboard_date",
            state_data=state_data,
        )
    
    async def _process_onboard_date(self, user_id: int, text: str, state_data: dict, context: MessageContext) -> Response:
        """Обработка ввода даты"""
        try:
            parts = text.replace("/", ".").replace("-", ".").split(".")
            if len(parts) != 3:
                raise ValueError()
            
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            birth_date = date(year, month, day)
            
            if birth_date > date.today():
                return Response(text="Дата не может быть в будущем", action="send")
            
            if birth_date.year < 1900:
                return Response(text="Введите год после 1900", action="send")
            
        except:
            return Response(text=t("step_date_invalid"), action="send")
        
        state_data["birth_date"] = text
        await self.core.set_user_state(user_id, "astro_onboard_time", state_data)
        
        return Response(
            text=f"{t('step_time_title')}\n\n{t('step_time_text')}",
            keyboard=kb.onboarding_time_unknown_keyboard_list(),
            action="send",
            set_state="astro_onboard_time",
            state_data=state_data,
        )
    
    async def _process_onboard_time(self, user_id: int, text: str, state_data: dict, context: MessageContext) -> Response:
        """Обработка ввода времени"""
        try:
            parts = text.replace(".", ":").replace("-", ":").split(":")
            if len(parts) != 2:
                raise ValueError()
            
            hour, minute = int(parts[0]), int(parts[1])
            
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError()
            
        except:
            return Response(text=t("step_time_invalid"), action="send")
        
        state_data["birth_time"] = f"{hour:02d}:{minute:02d}"
        state_data["time_unknown"] = False
        await self.core.set_user_state(user_id, "astro_onboard_city", state_data)
        
        return Response(
            text=f"{t('step_city_title')}\n\n{t('step_city_text')}",
            action="send",
            set_state="astro_onboard_city",
            state_data=state_data,
        )
    
    async def _process_onboard_city(self, user_id: int, text: str, state_data: dict, context: MessageContext) -> Response:
        """Обработка ввода города"""
        locations = await geocoder.search(text, limit=5)
        
        if not locations:
            return Response(text=t("step_city_not_found"), action="send")
        
        cities = [
            {"city": loc.city, "lat": loc.lat, "lng": loc.lng, "tz": loc.tz}
            for loc in locations
        ]
        state_data["cities"] = cities
        
        await self.core.set_user_state(user_id, "astro_onboard_city_select", state_data)
        
        if len(locations) == 1:
            loc = locations[0]
            return Response(
                text=t("step_city_found", city=loc.city, lat=f"{loc.lat:.4f}", lng=f"{loc.lng:.4f}", tz=loc.tz),
                keyboard=kb.onboarding_city_confirm_keyboard_list(0),
                action="send",
            )
        else:
            return Response(
                text=t("step_city_multiple"),
                keyboard=[[{"text": c["city"], "callback_data": f"service:astrology:onboard:city_select:{i}"}] for i, c in enumerate(cities[:5])] + [[{"text": t("step_city_retry"), "callback_data": "service:astrology:onboard:city_retry"}]],
                action="send",
            )
    
    # === Natal Chart Handler ===
    
    async def _handle_natal(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка натальной карты"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "view"
        
        if action == "view" or action == "":
            # Показываем выбор: для себя или для другого
            price = await self.get_price("natal_chart")
            balance = await self.core.get_balance(user_id)
            charts = await self.get_saved_charts(user_id)
            
            text = f"{t('natal_title')}\n\n"
            text += f"{t('natal_description')}\n\n"
            text += t("natal_price", price=price) + "\n"
            text += t("balance_label", balance=balance)
            
            buttons = [
                [{"text": t("natal_for_me"), "callback_data": kb.cb("natal", "me")}],
            ]
            
            # Добавляем сохранённые карты
            for c in charts[:5]:
                sign_emoji = get_sign_emoji(c.sun_sign or "")
                buttons.append([{"text": f"👤 {c.name} {sign_emoji}", "callback_data": kb.cb("natal", "chart", c.id)}])
            
            buttons.append([{"text": t("natal_for_other"), "callback_data": kb.cb("natal", "other")}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("menu")}])
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "me":
            # Подтверждение для своей карты
            price = await self.get_price("natal_chart")
            balance = await self.core.get_balance(user_id)
            
            text = f"{t('natal_title')}\n\n"
            text += f"👤 {profile.name}\n"
            text += f"☀️ {get_sign_display(profile.sun_sign)}\n\n"
            text += t("natal_price", price=price) + "\n"
            text += t("balance_label", balance=balance)
            
            return Response(
                text=text,
                keyboard=kb.natal_confirm_keyboard_list(price, balance),
            )
        
        elif action == "chart":
            # Натальная карта для сохранённой карты
            chart_id = int(params[1]) if len(params) > 1 else 0
            chart = await self.get_saved_chart(chart_id)
            
            if not chart:
                return Response(text="Карта не найдена", action="answer", show_alert=True)
            
            price = await self.get_price("natal_chart")
            balance = await self.core.get_balance(user_id)
            
            text = f"{t('natal_title')}\n\n"
            text += f"👤 {chart.name}\n"
            text += f"☀️ {get_sign_display(chart.sun_sign)}\n\n"
            text += t("natal_price", price=price) + "\n"
            text += t("balance_label", balance=balance)
            
            buttons = [
                [{"text": t("natal_generate"), "callback_data": kb.cb("natal", "generate_chart", chart_id)}],
                [{"text": t("btn_back"), "callback_data": kb.cb("natal")}],
            ]
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "other":
            # Добавить новую карту для натальной карты
            buttons = []
            for key, name in RELATION_TYPES.items():
                buttons.append([{"text": name, "callback_data": kb.cb("natal", "add", key)}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("natal")}])
            return Response(text="👤 Кто этот человек для вас?", keyboard=buttons)
        
        elif action == "add":
            # Начинаем добавление карты для натальной
            relation = params[1] if len(params) > 1 else "other"
            await self.core.set_user_state(user_id, "astro_add_chart_name", {"relation": relation, "for_natal": True})
            return Response(
                text="📝 Введите имя человека:",
                action="send",
                set_state="astro_add_chart_name",
                state_data={"relation": relation, "for_natal": True},
            )
        
        elif action == "generate":
            # Генерация для своей карты
            price = await self.get_price("natal_chart")
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(
                    text=t("insufficient_balance", need=price, balance=balance),
                    action="answer",
                    show_alert=True,
                )
            
            await self.core.deduct_balance(user_id, price, "Натальная карта")
            
            logger.info(f"Generating natal chart interpretation for user {user_id}")
            chart_data = ChartData.from_dict(profile.chart_data or {})
            logger.info(f"Chart data: sun={chart_data.sun_sign}, moon={chart_data.moon_sign}")
            interpretation, tokens = await interpreter.interpret_natal(chart_data)
            logger.info(f"Interpretation received: {len(interpretation)} chars, {tokens} tokens")
            
            # Рендерим в HTML
            html_path = renderer.render_natal(
                content=interpretation,
                sun_sign=get_sign_name(chart_data.sun_sign),
                moon_sign=get_sign_name(chart_data.moon_sign),
                asc_sign=get_sign_name(chart_data.ascendant_sign),
                user_id=user_id,
                person_name=profile.name
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    reading_type="natal",
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=False,
                    gton_cost=price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()
            
            # Отправляем HTML файл если успешно отрендерили, иначе текст
            if html_path:
                return Response(
                    text=f"🌟 Натальная карта {profile.name} готова!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            else:
                return Response(
                    text=interpretation,
                    keyboard=kb.back_to_menu_keyboard_list(),
                )
        
        elif action == "generate_chart":
            # Генерация для сохранённой карты
            chart_id = int(params[1]) if len(params) > 1 else 0
            chart = await self.get_saved_chart(chart_id)
            
            if not chart:
                return Response(text="Карта не найдена", action="answer", show_alert=True)
            
            price = await self.get_price("natal_chart")
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(
                    text=t("insufficient_balance", need=price, balance=balance),
                    action="answer",
                    show_alert=True,
                )
            
            await self.core.deduct_balance(user_id, price, f"Натальная карта ({chart.name})")
            
            logger.info(f"Generating natal chart interpretation for chart {chart_id}")
            chart_data = ChartData.from_dict(chart.chart_data or {})
            interpretation, tokens = await interpreter.interpret_natal(chart_data)
            
            # Рендерим в HTML
            html_path = renderer.render_natal(
                content=interpretation,
                sun_sign=get_sign_name(chart_data.sun_sign),
                moon_sign=get_sign_name(chart_data.moon_sign),
                asc_sign=get_sign_name(chart_data.ascendant_sign),
                user_id=user_id,
                person_name=chart.name
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    chart_id=chart_id,
                    reading_type="natal",
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=False,
                    gton_cost=price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()
            
            if html_path:
                return Response(
                    text=f"🌟 Натальная карта {chart.name} готова!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            else:
                return Response(
                    text=f"🌟 Натальная карта для {chart.name}\n\n{interpretation}",
                    keyboard=kb.back_to_menu_keyboard_list(),
                )
        
        return Response(text="Неизвестное действие", action="answer")
    
    # === Daily Horoscope Handler ===
    
    async def _handle_daily(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка ежедневного гороскопа"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "list"
        
        if action == "list" or action == "":
            # Список карт для выбора
            price = await self.get_price("daily_horoscope")
            balance = await self.core.get_balance(user_id)
            charts = await self.get_saved_charts(user_id)
            is_free = profile.has_referral_bonus and not profile.free_horoscope_used
            
            text = f"{t('daily_title')}\n\n"
            text += "Выберите, для кого составить гороскоп:\n\n"
            if is_free:
                text += "🎁 Первый гороскоп бесплатно!\n"
            else:
                text += f"💰 Стоимость: {price} GTON\n"
            text += f"💳 Баланс: {balance} GTON"
            
            buttons = [
                [{"text": f"👤 Для себя ({profile.name})", "callback_data": kb.cb("daily", "me")}],
            ]
            
            # Добавляем сохранённые карты
            for c in charts[:5]:
                sign_emoji = get_sign_emoji(c.sun_sign or "")
                buttons.append([{"text": f"👤 {c.name} {sign_emoji}", "callback_data": kb.cb("daily", "chart", c.id)}])
            
            buttons.append([{"text": "➕ Добавить карту", "callback_data": kb.cb("daily", "add")}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("menu")}])
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "me":
            # Подтверждение для своей карты
            price = await self.get_price("daily_horoscope")
            balance = await self.core.get_balance(user_id)
            is_free = profile.has_referral_bonus and not profile.free_horoscope_used
            
            text = f"{t('daily_title')}\n\n"
            text += f"👤 {profile.name}\n"
            text += f"☀️ {get_sign_display(profile.sun_sign)}\n\n"
            if is_free:
                text += "🎁 Бесплатно (реферальный бонус)\n"
            else:
                text += f"💰 Стоимость: {price} GTON\n"
            text += f"💳 Баланс: {balance} GTON"
            
            buttons = [
                [{"text": "✨ Получить гороскоп", "callback_data": kb.cb("daily", "generate")}],
                [{"text": t("btn_back"), "callback_data": kb.cb("daily")}],
            ]
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "chart":
            # Гороскоп для сохранённой карты
            chart_id = int(params[1]) if len(params) > 1 else 0
            chart = await self.get_saved_chart(chart_id)
            
            if not chart:
                return Response(text="Карта не найдена", action="answer", show_alert=True)
            
            price = await self.get_price("daily_horoscope")
            balance = await self.core.get_balance(user_id)
            
            text = f"{t('daily_title')}\n\n"
            text += f"👤 {chart.name}\n"
            text += f"☀️ {get_sign_display(chart.sun_sign)}\n\n"
            text += f"💰 Стоимость: {price} GTON\n"
            text += f"💳 Баланс: {balance} GTON"
            
            buttons = [
                [{"text": "✨ Получить гороскоп", "callback_data": kb.cb("daily", "generate_chart", chart_id)}],
                [{"text": t("btn_back"), "callback_data": kb.cb("daily")}],
            ]
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "add":
            # Добавить новую карту
            buttons = []
            for key, name in RELATION_TYPES.items():
                buttons.append([{"text": name, "callback_data": kb.cb("daily", "add_rel", key)}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("daily")}])
            return Response(text="👤 Кто этот человек для вас?", keyboard=buttons)
        
        elif action == "add_rel":
            # Начинаем добавление карты
            relation = params[1] if len(params) > 1 else "other"
            await self.core.set_user_state(user_id, "astro_add_chart_name", {"relation": relation, "return_to": "daily"})
            return Response(
                text="📝 Введите имя человека:",
                action="send",
                set_state="astro_add_chart_name",
                state_data={"relation": relation, "return_to": "daily"},
            )
        
        elif action == "generate":
            price = await self.get_price("daily_horoscope")
            balance = await self.core.get_balance(user_id)
            is_free = profile.has_referral_bonus and not profile.free_horoscope_used
            
            if not is_free and balance < price:
                return Response(
                    text=t("insufficient_balance", need=price, balance=balance),
                    action="answer",
                    show_alert=True,
                )
            
            if not is_free:
                await self.core.deduct_balance(user_id, price, "Гороскоп на сегодня")
            else:
                async with get_db() as session:
                    result = await session.execute(
                        select(UserAstrologyProfile).where(UserAstrologyProfile.user_id == user_id)
                    )
                    prof = result.scalar_one_or_none()
                    if prof:
                        prof.free_horoscope_used = True
                        await session.commit()
            
            chart_data = ChartData.from_dict(profile.chart_data or {})
            today = datetime.now().strftime("%d.%m.%Y")
            interpretation, tokens = await interpreter.interpret_daily(chart_data, today)
            
            # Рендерим в HTML
            html_path = renderer.render_daily(
                content=interpretation,
                sun_sign=get_sign_name(chart_data.sun_sign),
                sun_emoji=get_sign_emoji(chart_data.sun_sign),
                user_id=user_id,
                person_name=profile.name
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    reading_type="daily",
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=is_free,
                    gton_cost=Decimal("0") if is_free else price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()
            
            if html_path:
                return Response(
                    text=f"☀️ Гороскоп {profile.name} на сегодня готов!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            else:
                return Response(
                    text=interpretation,
                    keyboard=kb.back_to_menu_keyboard_list(),
                )
        
        elif action == "generate_chart":
            # Генерация для сохранённой карты
            chart_id = int(params[1]) if len(params) > 1 else 0
            chart = await self.get_saved_chart(chart_id)
            
            if not chart:
                return Response(text="Карта не найдена", action="answer", show_alert=True)
            
            price = await self.get_price("daily_horoscope")
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(text=t("insufficient_balance", need=price, balance=balance), action="answer", show_alert=True)
            
            await self.core.deduct_balance(user_id, price, f"Гороскоп на сегодня: {chart.name}")
            
            chart_data = ChartData.from_dict(chart.chart_data or {})
            today = datetime.now().strftime("%d.%m.%Y")
            interpretation, tokens = await interpreter.interpret_daily(chart_data, today)
            
            html_path = renderer.render_daily(
                content=interpretation,
                sun_sign=get_sign_name(chart_data.sun_sign),
                sun_emoji=get_sign_emoji(chart_data.sun_sign),
                user_id=user_id,
                person_name=chart.name
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    chart_id=chart_id,
                    reading_type="daily",
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=False,
                    gton_cost=price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()
            
            if html_path:
                return Response(
                    text=f"☀️ Гороскоп {chart.name} на сегодня готов!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            else:
                return Response(text=interpretation, keyboard=kb.back_to_menu_keyboard_list())
        
        return Response(text="Неизвестное действие", action="answer")
    
    # === Daily Toggle Handler ===
    
    async def _handle_daily_toggle(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Переключение ежедневного гороскопа ВКЛ/ВЫКЛ — просто меняет галочку и возвращает в главное меню"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        # Переключаем статус
        async with get_db() as session:
            result = await session.execute(
                select(UserAstrologyProfile).where(UserAstrologyProfile.user_id == user_id)
            )
            prof = result.scalar_one_or_none()
            if prof:
                prof.daily_horoscope_enabled = not prof.daily_horoscope_enabled
                new_status = prof.daily_horoscope_enabled
                await session.commit()
            else:
                new_status = False
        
        # Показываем короткое уведомление и возвращаем в главное меню
        status_text = "✅ Гороскоп на день включён" if new_status else "⬜ Гороскоп на день выключен"
        
        return Response(
            text=status_text,
            action="answer",  # Просто показываем всплывающее уведомление
            redirect_to="main_menu",  # И возвращаемся в главное меню
        )
    
    # === Child Horoscope Handler ===
    
    async def _handle_child(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка детского гороскопа"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "list"
        
        if action == "list" or action == "":
            charts = await self.get_saved_charts(user_id)
            children = [c for c in charts if c.relation == "child"]
            
            if not children:
                text = f"{t('child_title')}\n\n{t('child_empty')}"
                buttons = [
                    [{"text": t("child_add"), "callback_data": kb.cb("charts", "add", "child")}],
                    [{"text": t("btn_back"), "callback_data": kb.cb("menu")}],
                ]
            else:
                text = f"{t('child_title')}\n\n{t('child_select')}"
                buttons = []
                for child in children:
                    sign_emoji = get_sign_emoji(child.sun_sign or "")
                    age = self._calculate_age(child.birth_date)
                    buttons.append([{
                        "text": f"👶 {child.name} ({sign_emoji}, {age} лет)",
                        "callback_data": kb.cb("child", "select", child.id)
                    }])
                buttons.append([{"text": t("child_add"), "callback_data": kb.cb("charts", "add", "child")}])
                buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("menu")}])
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "select":
            chart_id = int(params[1]) if len(params) > 1 else 0
            chart = await self.get_saved_chart(chart_id)
            
            if not chart:
                return Response(text="Карта не найдена", action="answer", show_alert=True)
            
            price = await self.get_price("child_chart")
            balance = await self.core.get_balance(user_id)
            age = self._calculate_age(chart.birth_date)
            
            text = t("child_confirm",
                name=chart.name,
                age=age,
                date=chart.birth_date.strftime("%d.%m.%Y"),
                sun_sign=get_sign_display(chart.sun_sign or ""),
                moon_sign=get_sign_name(chart.moon_sign or "")
            )
            text += f"\n\nСтоимость: {price} GTON\nБаланс: {balance} GTON"
            
            buttons = []
            if balance >= price:
                buttons.append([{"text": t("child_generate"), "callback_data": kb.cb("child", "generate", chart_id)}])
            else:
                buttons.append([{"text": "💳 Пополнить баланс", "callback_data": "top_up"}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("child")}])
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "generate":
            chart_id = int(params[1]) if len(params) > 1 else 0
            chart = await self.get_saved_chart(chart_id)
            
            if not chart:
                return Response(text="Карта не найдена", action="answer", show_alert=True)
            
            price = await self.get_price("child_chart")
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(text=t("insufficient_balance", need=price, balance=balance), action="answer", show_alert=True)
            
            await self.core.deduct_balance(user_id, price, f"Детский гороскоп: {chart.name}")
            
            chart_data = ChartData.from_dict(chart.chart_data or {})
            interpretation, tokens = await interpreter.interpret_child(chart_data)
            
            # Рендерим в HTML
            age = self._calculate_age(chart.birth_date)
            html_path = renderer.render_child(
                content=interpretation,
                child_name=chart.name,
                child_age=age,
                sun_sign=get_sign_name(chart_data.sun_sign),
                moon_sign=get_sign_name(chart_data.moon_sign),
                user_id=user_id
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    chart_id=chart_id,
                    reading_type="child",
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=False,
                    gton_cost=price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()
            
            if html_path:
                return Response(
                    text=f"👶 Детский гороскоп {chart.name} готов!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            else:
                return Response(text=interpretation, keyboard=kb.back_to_menu_keyboard_list())
        
        return Response(text="Неизвестное действие", action="answer")
    
    def _calculate_age(self, birth_date: date) -> int:
        """Рассчитать возраст"""
        today = date.today()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    
    # === Love Horoscope Handler ===
    
    async def _handle_love(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка любовного гороскопа"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "menu"
        prices = await self.get_prices_dict()
        
        if action == "menu" or action == "":
            buttons = [
                [{"text": f"{t('love_portrait')} — {prices.get('love_portrait', 6)} GTON", "callback_data": kb.cb("love", "portrait")}],
                [{"text": f"{t('love_compatibility')} — {prices.get('compatibility', 8)} GTON", "callback_data": kb.cb("compat")}],
                [{"text": t("btn_back"), "callback_data": kb.cb("menu")}],
            ]
            return Response(text=f"{t('love_title')}\n\n{t('love_select_type')}", keyboard=buttons)
        
        elif action == "portrait":
            # Выбор карты для любовного портрета
            price = await self.get_price("love_portrait")
            balance = await self.core.get_balance(user_id)
            charts = await self.get_saved_charts(user_id)
            
            text = "💕 Любовный портрет\n\n"
            text += "Выберите, для кого составить портрет:\n\n"
            text += f"💰 Стоимость: {price} GTON\n"
            text += f"💳 Баланс: {balance} GTON"
            
            buttons = [
                [{"text": f"👤 Для себя ({profile.name})", "callback_data": kb.cb("love", "portrait_me")}],
            ]
            
            for c in charts[:5]:
                sign_emoji = get_sign_emoji(c.sun_sign or "")
                buttons.append([{"text": f"👤 {c.name} {sign_emoji}", "callback_data": kb.cb("love", "portrait_chart", c.id)}])
            
            buttons.append([{"text": "➕ Добавить карту", "callback_data": kb.cb("love", "add")}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("love")}])
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "portrait_me":
            # Генерация для своей карты
            price = await self.get_price("love_portrait")
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(text=t("insufficient_balance", need=price, balance=balance), action="answer", show_alert=True)
            
            await self.core.deduct_balance(user_id, price, "Любовный портрет")
            
            chart_data = ChartData.from_dict(profile.chart_data or {})
            interpretation, tokens = await interpreter.interpret_love(chart_data)

            html_path = renderer.render_generic(
                title=f"Любовный портрет {profile.name}",
                content=interpretation,
                user_id=user_id,
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    reading_type="love",
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=False,
                    gton_cost=price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()

            if html_path:
                return Response(
                    text=f"💕 Любовный портрет {profile.name} готов!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            return Response(text=interpretation, keyboard=kb.back_to_menu_keyboard_list())
        
        elif action == "portrait_chart":
            # Генерация для сохранённой карты
            chart_id = int(params[1]) if len(params) > 1 else 0
            chart = await self.get_saved_chart(chart_id)
            
            if not chart:
                return Response(text="Карта не найдена", action="answer", show_alert=True)
            
            price = await self.get_price("love_portrait")
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(text=t("insufficient_balance", need=price, balance=balance), action="answer", show_alert=True)
            
            await self.core.deduct_balance(user_id, price, f"Любовный портрет: {chart.name}")
            
            chart_data = ChartData.from_dict(chart.chart_data or {})
            interpretation, tokens = await interpreter.interpret_love(chart_data)

            html_path = renderer.render_generic(
                title=f"Любовный портрет {chart.name}",
                content=interpretation,
                user_id=user_id,
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    chart_id=chart_id,
                    reading_type="love",
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=False,
                    gton_cost=price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()

            if html_path:
                return Response(
                    text=f"💕 Любовный портрет {chart.name} готов!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            return Response(text=interpretation, keyboard=kb.back_to_menu_keyboard_list())
        
        elif action == "add":
            # Добавить новую карту
            buttons = []
            for key, name in RELATION_TYPES.items():
                buttons.append([{"text": name, "callback_data": kb.cb("love", "add_rel", key)}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("love", "portrait")}])
            return Response(text="👤 Кто этот человек для вас?", keyboard=buttons)
        
        elif action == "add_rel":
            relation = params[1] if len(params) > 1 else "other"
            await self.core.set_user_state(user_id, "astro_add_chart_name", {"relation": relation, "return_to": "love:portrait"})
            return Response(
                text="📝 Введите имя человека:",
                action="send",
                set_state="astro_add_chart_name",
                state_data={"relation": relation, "return_to": "love:portrait"},
            )
        
        return Response(text="Неизвестное действие", action="answer")
    
    # === Forecast Handler ===
    
    async def _handle_forecast(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка астропрогноза"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "list"
        prices = await self.get_prices_dict()
        
        if action == "list" or action == "":
            # Выбор карты
            balance = await self.core.get_balance(user_id)
            charts = await self.get_saved_charts(user_id)
            
            text = f"{t('forecast_title')}\n\n"
            text += "Выберите, для кого составить прогноз:\n\n"
            text += f"💳 Баланс: {balance} GTON"
            
            buttons = [
                [{"text": f"👤 Для себя ({profile.name})", "callback_data": kb.cb("forecast", "periods", "me")}],
            ]
            
            for c in charts[:5]:
                sign_emoji = get_sign_emoji(c.sun_sign or "")
                buttons.append([{"text": f"👤 {c.name} {sign_emoji}", "callback_data": kb.cb("forecast", "periods", c.id)}])
            
            buttons.append([{"text": "➕ Добавить карту", "callback_data": kb.cb("forecast", "add")}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("menu")}])
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "periods":
            # Выбор периода
            chart_id = params[1] if len(params) > 1 else "me"
            
            buttons = []
            for key, data in FORECAST_PERIODS.items():
                price = prices.get(data["price_key"].replace("price_", ""), 0)
                buttons.append([{"text": f"{data['name']} — {price} GTON", "callback_data": kb.cb("forecast", "generate", chart_id, key)}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("forecast")}])
            return Response(text=f"{t('forecast_title')}\n\n{t('forecast_select_period')}", keyboard=buttons)
        
        elif action == "generate":
            chart_id = params[1] if len(params) > 1 else "me"
            period = params[2] if len(params) > 2 else "week"
            period_data = FORECAST_PERIODS.get(period, FORECAST_PERIODS["week"])
            
            price = await self.get_price(period_data["price_key"])
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(text=t("insufficient_balance", need=price, balance=balance), action="answer", show_alert=True)
            
            # Получаем данные карты
            if chart_id == "me":
                chart_data = ChartData.from_dict(profile.chart_data or {})
                person_name = profile.name
                saved_chart_id = None
            else:
                chart = await self.get_saved_chart(int(chart_id))
                if not chart:
                    return Response(text="Карта не найдена", action="answer", show_alert=True)
                chart_data = ChartData.from_dict(chart.chart_data or {})
                person_name = chart.name
                saved_chart_id = chart.id
            
            await self.core.deduct_balance(user_id, price, f"Астропрогноз {person_name}: {period_data['name']}")
            
            period_text = f"{period_data['name']} ({period_data['days']} дней)"
            interpretation, tokens = await interpreter.interpret_forecast(chart_data, period_text, ["general"])

            html_path = renderer.render_generic(
                title=f"Астропрогноз {person_name}: {period_data['name']}",
                content=interpretation,
                user_id=user_id,
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    chart_id=saved_chart_id,
                    reading_type="forecast",
                    reading_subtype=period,
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=False,
                    gton_cost=price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()

            if html_path:
                return Response(
                    text=f"🔮 Астропрогноз для {person_name} готов!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            return Response(text=interpretation, keyboard=kb.back_to_menu_keyboard_list())
        
        elif action == "add":
            buttons = []
            for key, name in RELATION_TYPES.items():
                buttons.append([{"text": name, "callback_data": kb.cb("forecast", "add_rel", key)}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("forecast")}])
            return Response(text="👤 Кто этот человек для вас?", keyboard=buttons)
        
        elif action == "add_rel":
            relation = params[1] if len(params) > 1 else "other"
            await self.core.set_user_state(user_id, "astro_add_chart_name", {"relation": relation, "return_to": "forecast"})
            return Response(
                text="📝 Введите имя человека:",
                action="send",
                set_state="astro_add_chart_name",
                state_data={"relation": relation, "return_to": "forecast"},
            )
        
        return Response(text="Неизвестное действие", action="answer")
    
    # === Events Calendar Handler ===
    
    async def _handle_events(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка графика событий"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "list"
        prices = await self.get_prices_dict()
        
        if action == "list" or action == "":
            # Выбор карты
            balance = await self.core.get_balance(user_id)
            charts = await self.get_saved_charts(user_id)
            
            text = f"{t('events_title')}\n\n"
            text += "Выберите, для кого составить график:\n\n"
            text += f"💳 Баланс: {balance} GTON"
            
            buttons = [
                [{"text": f"👤 Для себя ({profile.name})", "callback_data": kb.cb("events", "periods", "me")}],
            ]
            
            for c in charts[:5]:
                sign_emoji = get_sign_emoji(c.sun_sign or "")
                buttons.append([{"text": f"👤 {c.name} {sign_emoji}", "callback_data": kb.cb("events", "periods", c.id)}])
            
            buttons.append([{"text": "➕ Добавить карту", "callback_data": kb.cb("events", "add")}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("menu")}])
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "periods":
            # Выбор периода
            chart_id = params[1] if len(params) > 1 else "me"
            
            buttons = []
            for key, data in EVENTS_PERIODS.items():
                price = prices.get(data["price_key"].replace("price_", ""), 0)
                buttons.append([{"text": f"{data['name']} — {price} GTON", "callback_data": kb.cb("events", "generate", chart_id, key)}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("events")}])
            return Response(text=f"{t('events_title')}\n\n{t('events_description')}", keyboard=buttons)
        
        elif action == "generate":
            chart_id = params[1] if len(params) > 1 else "me"
            period = params[2] if len(params) > 2 else "week"
            period_data = EVENTS_PERIODS.get(period, EVENTS_PERIODS["week"])
            price = await self.get_price(period_data["price_key"])
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(text=t("insufficient_balance", need=price, balance=balance), action="answer", show_alert=True)
            
            # Получаем данные карты
            if chart_id == "me":
                chart_data = ChartData.from_dict(profile.chart_data or {})
                person_name = profile.name
                saved_chart_id = None
            else:
                chart = await self.get_saved_chart(int(chart_id))
                if not chart:
                    return Response(text="Карта не найдена", action="answer", show_alert=True)
                chart_data = ChartData.from_dict(chart.chart_data or {})
                person_name = chart.name
                saved_chart_id = chart.id
            
            await self.core.deduct_balance(user_id, price, f"График событий {person_name}: {period_data['name']}")
            
            period_text = f"{period_data['name']} ({period_data['days']} дней)"
            interpretation, tokens = await interpreter.interpret_events(chart_data, period_text)

            html_path = renderer.render_generic(
                title=f"График событий {person_name}: {period_data['name']}",
                content=interpretation,
                user_id=user_id,
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    chart_id=saved_chart_id,
                    reading_type="events",
                    reading_subtype=period,
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=False,
                    gton_cost=price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()

            if html_path:
                return Response(
                    text=f"📅 График событий для {person_name} готов!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            return Response(text=interpretation, keyboard=kb.back_to_menu_keyboard_list())
        
        elif action == "add":
            buttons = []
            for key, name in RELATION_TYPES.items():
                buttons.append([{"text": name, "callback_data": kb.cb("events", "add_rel", key)}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("events")}])
            return Response(text="👤 Кто этот человек для вас?", keyboard=buttons)
        
        elif action == "add_rel":
            relation = params[1] if len(params) > 1 else "other"
            await self.core.set_user_state(user_id, "astro_add_chart_name", {"relation": relation, "return_to": "events"})
            return Response(
                text="📝 Введите имя человека:",
                action="send",
                set_state="astro_add_chart_name",
                state_data={"relation": relation, "return_to": "events"},
            )
        
        return Response(text="Неизвестное действие", action="answer")
    
    # === Transits Handler ===
    
    async def _handle_transits(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка транзитов"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "list"
        
        if action == "list" or action == "":
            # Выбор карты
            price = await self.get_price("transits")
            balance = await self.core.get_balance(user_id)
            charts = await self.get_saved_charts(user_id)
            
            text = f"{t('transits_title')}\n\n"
            text += "Выберите, для кого посмотреть транзиты:\n\n"
            text += f"💰 Стоимость: {price} GTON\n"
            text += f"💳 Баланс: {balance} GTON"
            
            buttons = [
                [{"text": f"👤 Для себя ({profile.name})", "callback_data": kb.cb("transits", "me")}],
            ]
            
            for c in charts[:5]:
                sign_emoji = get_sign_emoji(c.sun_sign or "")
                buttons.append([{"text": f"👤 {c.name} {sign_emoji}", "callback_data": kb.cb("transits", "chart", c.id)}])
            
            buttons.append([{"text": "➕ Добавить карту", "callback_data": kb.cb("transits", "add")}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("menu")}])
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "me":
            # Подтверждение для своей карты
            price = await self.get_price("transits")
            balance = await self.core.get_balance(user_id)
            
            text = f"{t('transits_title')}\n\n"
            text += f"👤 {profile.name}\n"
            text += f"☀️ {get_sign_display(profile.sun_sign)}\n\n"
            text += f"💰 Стоимость: {price} GTON\n"
            text += f"💳 Баланс: {balance} GTON"
            
            buttons = [
                [{"text": "✨ Получить транзиты", "callback_data": kb.cb("transits", "generate")}],
                [{"text": t("btn_back"), "callback_data": kb.cb("transits")}],
            ]
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "chart":
            # Транзиты для сохранённой карты
            chart_id = int(params[1]) if len(params) > 1 else 0
            chart = await self.get_saved_chart(chart_id)
            
            if not chart:
                return Response(text="Карта не найдена", action="answer", show_alert=True)
            
            price = await self.get_price("transits")
            balance = await self.core.get_balance(user_id)
            
            text = f"{t('transits_title')}\n\n"
            text += f"👤 {chart.name}\n"
            text += f"☀️ {get_sign_display(chart.sun_sign)}\n\n"
            text += f"💰 Стоимость: {price} GTON\n"
            text += f"💳 Баланс: {balance} GTON"
            
            buttons = [
                [{"text": "✨ Получить транзиты", "callback_data": kb.cb("transits", "generate_chart", chart_id)}],
                [{"text": t("btn_back"), "callback_data": kb.cb("transits")}],
            ]
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "generate":
            price = await self.get_price("transits")
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(text=t("insufficient_balance", need=price, balance=balance), action="answer", show_alert=True)
            
            await self.core.deduct_balance(user_id, price, "Транзиты сейчас")
            
            chart_data = ChartData.from_dict(profile.chart_data or {})
            today = datetime.now().strftime("%d.%m.%Y")
            interpretation, tokens = await interpreter.interpret_transits(chart_data, today)

            html_path = renderer.render_generic(
                title=f"Транзиты сейчас: {profile.name}",
                content=interpretation,
                user_id=user_id,
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    reading_type="transit",
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=False,
                    gton_cost=price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()

            if html_path:
                return Response(
                    text=f"✨ Транзиты для {profile.name} готовы!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            return Response(text=interpretation, keyboard=kb.back_to_menu_keyboard_list())
        
        elif action == "generate_chart":
            chart_id = int(params[1]) if len(params) > 1 else 0
            chart = await self.get_saved_chart(chart_id)
            
            if not chart:
                return Response(text="Карта не найдена", action="answer", show_alert=True)
            
            price = await self.get_price("transits")
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(text=t("insufficient_balance", need=price, balance=balance), action="answer", show_alert=True)
            
            await self.core.deduct_balance(user_id, price, f"Транзиты: {chart.name}")
            
            chart_data = ChartData.from_dict(chart.chart_data or {})
            today = datetime.now().strftime("%d.%m.%Y")
            interpretation, tokens = await interpreter.interpret_transits(chart_data, today)

            html_path = renderer.render_generic(
                title=f"Транзиты сейчас: {chart.name}",
                content=interpretation,
                user_id=user_id,
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    chart_id=chart_id,
                    reading_type="transit",
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=False,
                    gton_cost=price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()

            if html_path:
                return Response(
                    text=f"✨ Транзиты для {chart.name} готовы!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            return Response(text=interpretation, keyboard=kb.back_to_menu_keyboard_list())
        
        elif action == "add":
            buttons = []
            for key, name in RELATION_TYPES.items():
                buttons.append([{"text": name, "callback_data": kb.cb("transits", "add_rel", key)}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("transits")}])
            return Response(text="👤 Кто этот человек для вас?", keyboard=buttons)
        
        elif action == "add_rel":
            relation = params[1] if len(params) > 1 else "other"
            await self.core.set_user_state(user_id, "astro_add_chart_name", {"relation": relation, "return_to": "transits"})
            return Response(
                text="📝 Введите имя человека:",
                action="send",
                set_state="astro_add_chart_name",
                state_data={"relation": relation, "return_to": "transits"},
            )
        
        return Response(text="Неизвестное действие", action="answer")
    
    # === Compatibility Handler ===
    
    async def _handle_compat(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка совместимости"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "first"
        charts = await self.get_saved_charts(user_id)
        
        if action == "first" or action == "":
            buttons = []
            # Моя карта
            buttons.append([{"text": f"⭐ Моя карта ({profile.name})", "callback_data": kb.cb("compat", "second", "me")}])
            # Сохранённые карты
            for c in charts[:7]:
                sign_emoji = get_sign_emoji(c.sun_sign or "")
                buttons.append([{"text": f"👤 {c.name} {sign_emoji}", "callback_data": kb.cb("compat", "second", c.id)}])
            buttons.append([{"text": "➕ Добавить карту", "callback_data": kb.cb("compat", "add", "first")}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("menu")}])
            
            return Response(text=f"{t('compat_title')}\n\n{t('compat_select_first')}", keyboard=buttons)
        
        elif action == "second":
            first_id = params[1] if len(params) > 1 else "me"
            
            buttons = []
            # Моя карта (если первая не моя)
            if first_id != "me":
                buttons.append([{"text": f"⭐ Моя карта ({profile.name})", "callback_data": kb.cb("compat", "generate", first_id, "me")}])
            # Сохранённые карты (кроме первой)
            for c in charts[:7]:
                if str(c.id) == str(first_id):
                    continue
                sign_emoji = get_sign_emoji(c.sun_sign or "")
                buttons.append([{"text": f"👤 {c.name} {sign_emoji}", "callback_data": kb.cb("compat", "generate", first_id, c.id)}])
            buttons.append([{"text": "➕ Добавить карту", "callback_data": kb.cb("compat", "add", "second", first_id)}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("compat")}])
            
            return Response(text=t("compat_select_second", name="", sign=""), keyboard=buttons)
        
        elif action == "add":
            # Добавить новую карту для совместимости
            step = params[1] if len(params) > 1 else "first"  # first или second
            first_id = params[2] if len(params) > 2 else None
            
            buttons = []
            for key, name in RELATION_TYPES.items():
                if first_id:
                    buttons.append([{"text": name, "callback_data": kb.cb("compat", "add_rel", step, first_id, key)}])
                else:
                    buttons.append([{"text": name, "callback_data": kb.cb("compat", "add_rel", step, key)}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("compat") if step == "first" else kb.cb("compat", "second", first_id)}])
            return Response(text="👤 Кто этот человек для вас?", keyboard=buttons)
        
        elif action == "add_rel":
            step = params[1] if len(params) > 1 else "first"
            if step == "first":
                relation = params[2] if len(params) > 2 else "other"
                await self.core.set_user_state(user_id, "astro_add_chart_name", {"relation": relation, "return_to": "compat"})
            else:
                first_id = params[2] if len(params) > 2 else "me"
                relation = params[3] if len(params) > 3 else "other"
                await self.core.set_user_state(user_id, "astro_add_chart_name", {"relation": relation, "return_to": f"compat:second:{first_id}"})
            
            return Response(
                text="📝 Введите имя человека:",
                action="send",
                set_state="astro_add_chart_name",
            )
        
        elif action == "generate":
            first_id = params[1] if len(params) > 1 else "me"
            second_id = params[2] if len(params) > 2 else None
            
            if not second_id:
                return Response(text="Выберите вторую карту", action="answer", show_alert=True)
            
            price = await self.get_price("compatibility")
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(text=t("insufficient_balance", need=price, balance=balance), action="answer", show_alert=True)
            
            # Получаем данные карт
            if first_id == "me":
                chart1_data = ChartData.from_dict(profile.chart_data or {})
                name1 = profile.name
            else:
                chart1 = await self.get_saved_chart(int(first_id))
                chart1_data = ChartData.from_dict(chart1.chart_data or {}) if chart1 else ChartData.from_dict({})
                name1 = chart1.name if chart1 else "?"
            
            if second_id == "me":
                chart2_data = ChartData.from_dict(profile.chart_data or {})
                name2 = profile.name
            else:
                chart2 = await self.get_saved_chart(int(second_id))
                chart2_data = ChartData.from_dict(chart2.chart_data or {}) if chart2 else ChartData.from_dict({})
                name2 = chart2.name if chart2 else "?"
            
            await self.core.deduct_balance(user_id, price, f"Совместимость: {name1} + {name2}")
            
            interpretation, tokens = await interpreter.interpret_compatibility(chart1_data, chart2_data)
            
            # Рендерим в HTML
            html_path = renderer.render_compatibility(
                content=interpretation,
                person1_name=name1,
                person1_emoji=get_sign_emoji(chart1_data.sun_sign),
                person2_name=name2,
                person2_emoji=get_sign_emoji(chart2_data.sun_sign),
                user_id=user_id
            )
            
            async with get_db() as session:
                reading = AstrologyReading(
                    user_id=user_id,
                    profile_id=profile.id,
                    chart_id=int(first_id) if first_id != "me" else None,
                    second_chart_id=int(second_id) if second_id != "me" else None,
                    reading_type="compatibility",
                    interpretation=interpretation,
                    file_path=html_path,
                    is_free=False,
                    gton_cost=price,
                    tokens_used=tokens,
                )
                session.add(reading)
                await session.commit()
            
            if html_path:
                return Response(
                    text=f"💑 Совместимость {name1} и {name2} готова!",
                    keyboard=kb.back_to_menu_keyboard_list(),
                    media_path=html_path,
                    media_type="document",
                )
            else:
                return Response(text=interpretation, keyboard=kb.back_to_menu_keyboard_list())
        
        return Response(text="Неизвестное действие", action="answer")
    
    # === Question Handler ===
    
    async def _handle_question(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка вопроса астрологу"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "menu"
        
        if action == "menu" or action == "":
            # Показываем меню выбора карт
            price = await self.get_price("question")
            balance = await self.core.get_balance(user_id)
            charts = await self.get_saved_charts(user_id)
            
            text = "❓ Задать вопрос астрологу\n\n"
            text += "Выберите карты для анализа (до 3-х):\n"
            text += f"\n💰 Стоимость: {price} GTON\n💳 Баланс: {balance} GTON"
            
            # Кнопка "Моя карта" всегда первая
            buttons = [
                [{"text": f"{'✅' if False else '☐'} Моя карта ({profile.name})", "callback_data": kb.cb("question", "toggle", "me")}]
            ]
            
            # Добавляем сохранённые карты
            for chart in charts[:9]:  # Максимум 9 карт в списке
                buttons.append([{
                    "text": f"☐ {chart.name}",
                    "callback_data": kb.cb("question", "toggle", str(chart.id))
                }])
            
            buttons.append([{"text": "➡️ Продолжить", "callback_data": kb.cb("question", "select")}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("menu")}])
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "toggle":
            # Переключение выбора карты
            chart_id = params[1] if len(params) > 1 else ""
            
            # Получаем текущий выбор из state_data
            _, state_data = await self.core.get_user_state(user_id)
            selected = state_data.get("selected_charts", []) if state_data else []
            
            if chart_id in selected:
                selected.remove(chart_id)
            else:
                if len(selected) >= 3:
                    return Response(text="Максимум 3 карты!", action="answer", show_alert=True)
                selected.append(chart_id)
            
            # Сохраняем выбор
            await self.core.set_user_state(user_id, "astro_question_select", {"selected_charts": selected})
            
            # Обновляем меню
            price = await self.get_price("question")
            balance = await self.core.get_balance(user_id)
            charts = await self.get_saved_charts(user_id)
            
            text = "❓ Задать вопрос астрологу\n\n"
            text += f"Выбрано карт: {len(selected)}/3\n"
            text += f"\n💰 Стоимость: {price} GTON\n💳 Баланс: {balance} GTON"
            
            # Кнопка "Моя карта"
            is_me_selected = "me" in selected
            buttons = [
                [{"text": f"{'✅' if is_me_selected else '☐'} Моя карта ({profile.name})", "callback_data": kb.cb("question", "toggle", "me")}]
            ]
            
            # Добавляем сохранённые карты
            for chart in charts[:9]:
                is_selected = str(chart.id) in selected
                buttons.append([{
                    "text": f"{'✅' if is_selected else '☐'} {chart.name}",
                    "callback_data": kb.cb("question", "toggle", str(chart.id))
                }])
            
            buttons.append([{"text": "➡️ Продолжить", "callback_data": kb.cb("question", "select")}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("menu")}])
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "select":
            # Подтверждение выбора и переход к вводу вопроса
            _, state_data = await self.core.get_user_state(user_id)
            selected = state_data.get("selected_charts", []) if state_data else []
            
            if not selected:
                return Response(text="Выберите хотя бы одну карту!", action="answer", show_alert=True)
            
            # Проверяем баланс
            price = await self.get_price("question")
            balance = await self.core.get_balance(user_id)
            
            if balance < price:
                return Response(
                    text=t("insufficient_balance", need=price, balance=balance),
                    action="answer",
                    show_alert=True,
                )
            
            # Сохраняем состояние и просим ввести вопрос
            await self.core.set_user_state(user_id, "astro_question_text", {"selected_charts": selected})
            
            return Response(
                text="✍️ Напишите ваш вопрос астрологу:\n\n(максимум 500 символов)",
                keyboard=[[{"text": "❌ Отмена", "callback_data": kb.cb("question")}]],
                action="send",
            )
        
        return Response(text="Неизвестное действие", action="answer")
    
    async def _process_question_text(
        self, 
        user_id: int, 
        text: str, 
        state_data: dict, 
        context
    ) -> Response:
        """Обработка введённого вопроса"""
        # Проверяем длину вопроса
        if len(text) > 500:
            return Response(
                text=f"❌ Вопрос слишком длинный ({len(text)}/500 символов).\n\nСократите вопрос и отправьте снова.",
                keyboard=[[{"text": "❌ Отмена", "callback_data": kb.cb("question")}]],
            )
        
        if len(text) < 10:
            return Response(
                text="❌ Вопрос слишком короткий. Напишите более подробно.",
                keyboard=[[{"text": "❌ Отмена", "callback_data": kb.cb("question")}]],
            )
        
        selected = state_data.get("selected_charts", [])
        if not selected:
            await self.core.clear_user_state(user_id)
            return Response(text="Ошибка: карты не выбраны", keyboard=kb.back_to_menu_keyboard_list())
        
        # Проверяем баланс
        price = await self.get_price("question")
        balance = await self.core.get_balance(user_id)
        
        if balance < price:
            await self.core.clear_user_state(user_id)
            return Response(
                text=t("insufficient_balance", need=price, balance=balance),
                keyboard=kb.back_to_menu_keyboard_list(),
            )
        
        # Собираем данные карт
        profile = await self.get_profile(user_id)
        charts_data = []
        persons = []
        
        for chart_id in selected:
            if chart_id == "me":
                chart_data = ChartData.from_dict(profile.chart_data or {})
                charts_data.append(chart_data)
                persons.append({
                    "name": profile.name,
                    "emoji": get_sign_emoji(chart_data.sun_sign)
                })
            else:
                chart = await self.get_saved_chart(int(chart_id))
                if chart:
                    chart_data = ChartData.from_dict(chart.chart_data or {})
                    charts_data.append(chart_data)
                    persons.append({
                        "name": chart.name,
                        "emoji": get_sign_emoji(chart_data.sun_sign)
                    })
        
        if not charts_data:
            await self.core.clear_user_state(user_id)
            return Response(text="Ошибка: не удалось загрузить карты", keyboard=kb.back_to_menu_keyboard_list())
        
        # Отправляем сообщение о генерации
        names = [p["name"] for p in persons]
        await self.core.send_message(
            user_id, 
            f"⏳ Генерирую ответ для: {', '.join(names)}...\n\nЭто может занять до 2 минут."
        )
        
        # Списываем баланс
        await self.core.deduct_balance(user_id, price, f"Вопрос астрологу: {', '.join(names)}")
        
        # Генерируем ответ
        interpretation, tokens = await interpreter.interpret_question(
            charts=charts_data,
            names=names,
            question=text
        )
        
        # Рендерим в HTML
        html_path = renderer.render_question(
            content=interpretation,
            question_text=text,
            persons=persons,
            user_id=user_id
        )
        
        # Сохраняем в историю
        async with get_db() as session:
            reading = AstrologyReading(
                user_id=user_id,
                profile_id=profile.id,
                reading_type="question",
                reading_subtype=text[:100],  # Сохраняем начало вопроса
                interpretation=interpretation,
                file_path=html_path,
                is_free=False,
                gton_cost=price,
                tokens_used=tokens,
            )
            session.add(reading)
            await session.commit()
        
        await self.core.clear_user_state(user_id)
        
        if html_path:
            return Response(
                text=f"✨ Ответ астролога готов!",
                keyboard=kb.back_to_menu_keyboard_list(),
                media_path=html_path,
                media_type="document",
                action="send",
                clear_state=True,
            )
        else:
            return Response(
                text=interpretation,
                keyboard=kb.back_to_menu_keyboard_list(),
                action="send",
                clear_state=True,
            )
    
    # === Charts Management Handler ===
    
    async def _handle_charts(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка управления картами"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "list"
        
        if action == "list" or action == "":
            charts = await self.get_saved_charts(user_id)
            used = len(charts)
            max_slots = profile.max_saved_charts
            
            text = f"{t('charts_title')}\n\n"
            text += t("charts_slots", used=used, max=max_slots) + "\n\n"
            text += t("charts_list") if charts else t("charts_empty")
            
            buttons = []
            for c in charts:
                sign_emoji = get_sign_emoji(c.sun_sign or "")
                relation = RELATION_TYPES.get(c.relation, "")
                buttons.append([{"text": f"👤 {c.name} {sign_emoji} — {relation}", "callback_data": kb.cb("charts", "view", c.id)}])
            if used < max_slots:
                buttons.append([{"text": t("charts_add"), "callback_data": kb.cb("charts", "add")}])
            buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("menu")}])
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "view":
            chart_id = int(params[1]) if len(params) > 1 else 0
            chart = await self.get_saved_chart(chart_id)
            
            if not chart:
                return Response(text="Карта не найдена", action="answer", show_alert=True)
            
            age = self._calculate_age(chart.birth_date)
            relation = RELATION_TYPES.get(chart.relation, chart.relation)
            
            text = f"👤 <b>{chart.name}</b>\n\n"
            text += f"Отношение: {relation}\n"
            text += f"Дата рождения: {chart.birth_date.strftime('%d.%m.%Y')}\n"
            text += f"Возраст: {age} лет\n"
            text += f"Знак: {get_sign_display(chart.sun_sign or '')}\n"
            
            buttons = [
                [{"text": "💑 Совместимость", "callback_data": kb.cb("compat", "second", chart_id)}],
                [{"text": "🗑 Удалить", "callback_data": kb.cb("charts", "delete", chart_id)}],
                [{"text": t("btn_back"), "callback_data": kb.cb("charts")}],
            ]
            return Response(text=text, keyboard=buttons)
        
        elif action == "add":
            relation = params[1] if len(params) > 1 else None
            
            if not relation:
                buttons = []
                for key, name in RELATION_TYPES.items():
                    buttons.append([{"text": name, "callback_data": kb.cb("charts", "add", key)}])
                buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("charts")}])
                return Response(text=t("add_chart_relation"), keyboard=buttons)
            else:
                await self.core.set_user_state(user_id, "astro_add_chart_name", {"relation": relation})
                return Response(text="📝 Введите имя человека:", set_state="astro_add_chart_name", state_data={"relation": relation})
        
        elif action == "delete":
            chart_id = int(params[1]) if len(params) > 1 else 0
            
            async with get_db() as session:
                result = await session.execute(
                    select(SavedChart).where(SavedChart.id == chart_id, SavedChart.user_id == user_id)
                )
                chart = result.scalar_one_or_none()
                if chart:
                    await session.delete(chart)
                    await session.commit()
            
            return await self._handle_charts(user_id, ["list"], context)
        
        return Response(text="Неизвестное действие", action="answer")
    
    # === History Handler ===
    
    async def _handle_history(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка истории"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "list"
        
        # Открыть конкретный файл из истории
        if action == "open":
            reading_id = int(params[1]) if len(params) > 1 else 0
            async with get_db() as session:
                result = await session.execute(
                    select(AstrologyReading)
                    .where(AstrologyReading.id == reading_id)
                    .where(AstrologyReading.user_id == user_id)
                )
                reading = result.scalar_one_or_none()
            
            if not reading or not reading.file_path:
                return Response(text="Файл не найден", action="answer", show_alert=True)
            
            # Проверяем, существует ли файл
            import os
            if not os.path.exists(reading.file_path):
                return Response(text="Файл был удалён", action="answer", show_alert=True)
            
            type_name = READING_TYPES.get(reading.reading_type, reading.reading_type)
            return Response(
                text=f"📄 {type_name}",
                keyboard=[[{"text": t("btn_back"), "callback_data": kb.cb("history")}]],
                media_path=reading.file_path,
                media_type="document",
            )
        
        # Список истории
        async with get_db() as session:
            result = await session.execute(
                select(AstrologyReading)
                .where(AstrologyReading.user_id == user_id)
                .order_by(AstrologyReading.created_at.desc())
                .limit(20)
            )
            readings = list(result.scalars().all())
        
        if not readings:
            text = f"{t('history_title')}\n\n{t('history_empty')}"
            return Response(text=text, keyboard=kb.back_to_menu_keyboard_list())
        
        # Считаем записи с файлами
        readings_with_files = [r for r in readings if r.file_path]
        
        if readings_with_files:
            text = "📚 Ваши гороскопы\n\nНажмите на кнопку, чтобы открыть файл:"
        else:
            text = f"{t('history_title')}\n\nФайлы недоступны для старых записей."
        
        # Формируем кнопки для каждой записи с файлом
        buttons = []
        for r in readings:
            type_name = READING_TYPES.get(r.reading_type, r.reading_type)
            date_str = r.created_at.strftime("%d.%m.%Y")
            
            if r.file_path:
                # Есть файл - показываем кнопку
                buttons.append([{
                    "text": f"📄 {type_name} ({date_str})",
                    "callback_data": kb.cb("history", "open", str(r.id))
                }])
        
        buttons.append([{"text": t("btn_back"), "callback_data": kb.cb("menu")}])
        
        return Response(text=text, keyboard=buttons)
    
    # === Subscriptions Handler ===
    
    async def _handle_subs(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка подписок"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "menu"
        
        if action == "menu" or action == "":
            buttons = [
                [{"text": t("sub_daily"), "callback_data": kb.cb("subs", "daily")}],
                [{"text": t("sub_my"), "callback_data": kb.cb("subs", "my")}],
                [{"text": t("btn_back"), "callback_data": kb.cb("menu")}],
            ]
            return Response(text=t("sub_title"), keyboard=buttons)
        
        elif action == "my":
            if profile.subscription_until and profile.subscription_until > datetime.now():
                until = profile.subscription_until.strftime("%d.%m.%Y")
                send_time = profile.subscription_send_time.strftime("%H:%M") if profile.subscription_send_time else "09:00"
                text = f"📋 Ваша подписка\n\nАктивна до: {until}\nВремя отправки: {send_time}"
            else:
                text = "У вас нет активной подписки."
            
            return Response(text=text, keyboard=[[{"text": t("btn_back"), "callback_data": kb.cb("subs")}]])
        
        return Response(text="Неизвестное действие", action="answer")
    
    # === Settings Handler ===
    
    async def _handle_settings(self, user_id: int, params: List[str], context: CallbackContext) -> Response:
        """Обработка настроек"""
        profile = await self.get_profile(user_id)
        if not profile:
            return self._require_profile_response()
        
        action = params[0] if params else "view"
        
        if action == "view" or action == "":
            text = f"⚙️ Настройки\n\n"
            text += f"👤 Имя: {profile.name}\n"
            text += f"📅 Дата рождения: {profile.birth_date.strftime('%d.%m.%Y')}\n"
            text += f"⏰ Время: {profile.birth_time.strftime('%H:%M')}\n"
            text += f"🌍 Город: {profile.birth_city}\n"
            
            buttons = [
                [{"text": "✏️ Изменить имя", "callback_data": kb.cb("settings", "edit", "name")}],
                [{"text": "📅 Изменить дату", "callback_data": kb.cb("settings", "edit", "date")}],
                [{"text": "⏰ Изменить время", "callback_data": kb.cb("settings", "edit", "time")}],
                [{"text": "🌍 Изменить город", "callback_data": kb.cb("settings", "edit", "city")}],
                [{"text": "🗑 Удалить профиль", "callback_data": kb.cb("settings", "delete")}],
                [{"text": t("btn_back"), "callback_data": kb.cb("menu")}],
            ]
            
            return Response(text=text, keyboard=buttons)
        
        elif action == "edit":
            field = params[1] if len(params) > 1 else ""
            
            if field == "name":
                await self.core.set_user_state(user_id, "astro_edit_name", {})
                return Response(
                    text="✏️ Введите новое имя:",
                    action="send",
                    set_state="astro_edit_name",
                )
            elif field == "date":
                await self.core.set_user_state(user_id, "astro_edit_date", {})
                return Response(
                    text="📅 Введите новую дату рождения\n\nФормат: ДД.ММ.ГГГГ",
                    action="send",
                    set_state="astro_edit_date",
                )
            elif field == "time":
                await self.core.set_user_state(user_id, "astro_edit_time", {})
                return Response(
                    text="⏰ Введите новое время рождения\n\nФормат: ЧЧ:ММ",
                    action="send",
                    set_state="astro_edit_time",
                )
            elif field == "city":
                await self.core.set_user_state(user_id, "astro_edit_city", {})
                return Response(
                    text="🌍 Введите новый город рождения:",
                    action="send",
                    set_state="astro_edit_city",
                )
        
        elif action == "delete":
            confirm = params[1] if len(params) > 1 else ""
            
            if confirm == "yes":
                async with get_db() as session:
                    result = await session.execute(
                        select(UserAstrologyProfile).where(UserAstrologyProfile.user_id == user_id)
                    )
                    prof = result.scalar_one_or_none()
                    if prof:
                        await session.delete(prof)
                        await session.commit()
                
                return Response(
                    text="✅ Профиль удалён.\n\nВы можете создать новый профиль.",
                    keyboard=[[{"text": "🔮 Создать профиль", "callback_data": kb.cb("onboard")}]],
                )
            else:
                return Response(
                    text="⚠️ Вы уверены, что хотите удалить профиль?\n\nВсе данные будут потеряны.",
                    keyboard=[
                        [{"text": "🗑 Да, удалить", "callback_data": kb.cb("settings", "delete", "yes")}],
                        [{"text": "❌ Отмена", "callback_data": kb.cb("settings")}],
                    ],
                )
        
        return Response(text="Неизвестное действие", action="answer")
    
    # === Add Chart Message Processors ===
    
    async def _process_add_chart_name(self, user_id: int, text: str, state_data: dict, context: MessageContext) -> Response:
        """Обработка имени для новой карты"""
        if len(text) < 2 or len(text) > 50:
            return Response(text="Введите имя от 2 до 50 символов", action="send")
        
        state_data["name"] = text
        await self.core.set_user_state(user_id, "astro_add_chart_date", state_data)
        
        return Response(
            text="📅 Введите дату рождения\n\nФормат: ДД.ММ.ГГГГ\nНапример: 15.03.2010",
            action="send",
            set_state="astro_add_chart_date",
            state_data=state_data,
        )
    
    async def _process_add_chart_date(self, user_id: int, text: str, state_data: dict, context: MessageContext) -> Response:
        """Обработка даты для новой карты"""
        try:
            parts = text.replace("/", ".").replace("-", ".").split(".")
            if len(parts) != 3:
                raise ValueError()
            
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            birth_date = date(year, month, day)
            
            if birth_date > date.today():
                return Response(text="Дата не может быть в будущем", action="send")
            
            if birth_date.year < 1900:
                return Response(text="Введите год после 1900", action="send")
            
        except:
            return Response(text="❌ Неверный формат даты. Введите в формате ДД.ММ.ГГГГ", action="send")
        
        state_data["birth_date"] = text
        await self.core.set_user_state(user_id, "astro_add_chart_time", state_data)
        
        return Response(
            text="⏰ Введите время рождения\n\nФормат: ЧЧ:ММ\nНапример: 14:30",
            keyboard=kb.onboarding_time_unknown_keyboard_list(),
            action="send",
            set_state="astro_add_chart_time",
            state_data=state_data,
        )
    
    async def _process_add_chart_time(self, user_id: int, text: str, state_data: dict, context: MessageContext) -> Response:
        """Обработка времени для новой карты"""
        try:
            parts = text.replace(".", ":").replace("-", ":").split(":")
            if len(parts) != 2:
                raise ValueError()
            
            hour, minute = int(parts[0]), int(parts[1])
            
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError()
            
        except:
            return Response(text="❌ Неверный формат времени. Введите в формате ЧЧ:ММ", action="send")
        
        state_data["birth_time"] = f"{hour:02d}:{minute:02d}"
        state_data["time_unknown"] = False
        await self.core.set_user_state(user_id, "astro_add_chart_city", state_data)
        
        return Response(
            text="🌍 Введите город рождения:",
            action="send",
            set_state="astro_add_chart_city",
            state_data=state_data,
        )
    
    async def _process_add_chart_city(self, user_id: int, text: str, state_data: dict, context: MessageContext) -> Response:
        """Обработка города для новой карты"""
        locations = await geocoder.search(text, limit=5)
        
        if not locations:
            return Response(text="❌ Город не найден. Попробуйте ввести по-другому.", action="send")
        
        loc = locations[0]
        state_data["city"] = loc.city
        state_data["lat"] = loc.lat
        state_data["lng"] = loc.lng
        state_data["tz"] = loc.tz
        
        return await self._save_new_chart(user_id, state_data)
    
    async def _save_new_chart(self, user_id: int, state_data: dict) -> Response:
        """Сохранить новую карту"""
        profile = await self.get_profile(user_id)
        if not profile:
            return Response(text="❌ Сначала создайте свой профиль", action="send", clear_state=True)
        
        charts = await self.get_saved_charts(user_id)
        if len(charts) >= profile.max_saved_charts:
            await self.core.clear_user_state(user_id)
            return Response(
                text=f"❌ Достигнут лимит карт ({profile.max_saved_charts})\n\nКупите дополнительные слоты в разделе «Мои карты»",
                action="send",
                clear_state=True,
            )
        
        name = state_data.get("name", "")
        relation = state_data.get("relation", "other")
        birth_date_str = state_data.get("birth_date", "")
        birth_time_str = state_data.get("birth_time", "12:00")
        city = state_data.get("city", "")
        lat = state_data.get("lat", 0.0)
        lng = state_data.get("lng", 0.0)
        tz = state_data.get("tz", "UTC")
        time_unknown = state_data.get("time_unknown", False)
        
        try:
            day, month, year = birth_date_str.split(".")
            birth_date = date(int(year), int(month), int(day))
        except:
            birth_date = date.today()
        
        try:
            hour, minute = birth_time_str.split(":")
            birth_time = time(int(hour), int(minute))
        except:
            birth_time = time(12, 0)
        
        chart_data = await chart_calculator.calculate_natal_chart(
            name=name,
            birth_date=birth_date,
            birth_time=birth_time,
            lat=lat,
            lng=lng,
            tz_str=tz,
        )
        
        svg_path = await chart_calculator.generate_svg(
            name=name,
            birth_date=birth_date,
            birth_time=birth_time,
            lat=lat,
            lng=lng,
            tz_str=tz,
            user_id=user_id,
            chart_type="saved",
        )
        
        async with get_db() as session:
            chart = SavedChart(
                user_id=user_id,
                profile_id=profile.id,
                name=name,
                relation=relation,
                birth_date=birth_date,
                birth_time=birth_time,
                birth_time_unknown=time_unknown,
                birth_city=city,
                birth_lat=lat,
                birth_lng=lng,
                birth_tz=tz,
                sun_sign=chart_data.sun_sign,
                moon_sign=chart_data.moon_sign,
                ascendant_sign=chart_data.ascendant_sign,
                chart_data=chart_data.to_dict(),
                svg_path=svg_path,
            )
            session.add(chart)
            await session.commit()
        
        await self.core.clear_user_state(user_id)
        
        relation_name = RELATION_TYPES.get(relation, relation)
        
        text = f"✅ Карта сохранена!\n\n"
        text += f"👤 {name} ({relation_name})\n"
        text += f"☀️ {get_sign_display(chart_data.sun_sign)}\n"
        text += f"🌙 Луна в {get_sign_name(chart_data.moon_sign)}\n"
        text += f"⬆️ Асцендент в {get_sign_name(chart_data.ascendant_sign)}"
        
        return Response(
            text=text,
            keyboard=[[{"text": "👥 К моим картам", "callback_data": kb.cb("charts")}]],
            action="send",
            clear_state=True,
        )
    
    # === Profile Edit Processors ===
    
    async def _process_edit_name(self, user_id: int, text: str, context: MessageContext) -> Response:
        """Обработка изменения имени"""
        if len(text) < 2 or len(text) > 50:
            return Response(text="Введите имя от 2 до 50 символов", action="send")
        
        async with get_db() as session:
            result = await session.execute(
                select(UserAstrologyProfile).where(UserAstrologyProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if profile:
                profile.name = text
                await session.commit()
        
        await self.core.clear_user_state(user_id)
        
        return Response(
            text=f"✅ Имя изменено на: {text}",
            keyboard=[[{"text": "⚙️ Назад к настройкам", "callback_data": kb.cb("settings")}]],
            action="send",
            clear_state=True,
        )
    
    async def _process_edit_date(self, user_id: int, text: str, context: MessageContext) -> Response:
        """Обработка изменения даты рождения"""
        try:
            parts = text.replace("/", ".").replace("-", ".").split(".")
            if len(parts) != 3:
                raise ValueError()
            
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            birth_date = date(year, month, day)
            
            if birth_date > date.today():
                return Response(text="Дата не может быть в будущем", action="send")
            
            if birth_date.year < 1900:
                return Response(text="Введите год после 1900", action="send")
            
        except:
            return Response(text="❌ Неверный формат даты. Введите в формате ДД.ММ.ГГГГ", action="send")
        
        # Получаем профиль и пересчитываем карту
        profile = await self.get_profile(user_id)
        if not profile:
            return Response(text="Профиль не найден", action="send")
        
        # Пересчитываем карту
        chart_data = await chart_calculator.calculate_natal_chart(
            name=profile.name,
            birth_date=birth_date,
            birth_time=profile.birth_time,
            lat=profile.birth_lat,
            lng=profile.birth_lng,
            tz_str=profile.birth_tz,
        )
        
        async with get_db() as session:
            result = await session.execute(
                select(UserAstrologyProfile).where(UserAstrologyProfile.user_id == user_id)
            )
            prof = result.scalar_one_or_none()
            if prof:
                prof.birth_date = birth_date
                prof.sun_sign = chart_data.sun_sign
                prof.moon_sign = chart_data.moon_sign
                prof.ascendant_sign = chart_data.ascendant_sign
                prof.chart_data = chart_data.to_dict()
                await session.commit()
        
        await self.core.clear_user_state(user_id)
        
        return Response(
            text=f"✅ Дата рождения изменена!\n\n☀️ Солнце в {get_sign_name(chart_data.sun_sign)}\n🌙 Луна в {get_sign_name(chart_data.moon_sign)}\n⬆️ Асцендент в {get_sign_name(chart_data.ascendant_sign)}",
            keyboard=[[{"text": "⚙️ Назад к настройкам", "callback_data": kb.cb("settings")}]],
            action="send",
            clear_state=True,
        )
    
    async def _process_edit_time(self, user_id: int, text: str, context: MessageContext) -> Response:
        """Обработка изменения времени рождения"""
        try:
            parts = text.replace(".", ":").replace("-", ":").split(":")
            if len(parts) != 2:
                raise ValueError()
            
            hour, minute = int(parts[0]), int(parts[1])
            
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError()
            
            birth_time = time(hour, minute)
            
        except:
            return Response(text="❌ Неверный формат времени. Введите в формате ЧЧ:ММ", action="send")
        
        # Получаем профиль и пересчитываем карту
        profile = await self.get_profile(user_id)
        if not profile:
            return Response(text="Профиль не найден", action="send")
        
        # Пересчитываем карту
        chart_data = await chart_calculator.calculate_natal_chart(
            name=profile.name,
            birth_date=profile.birth_date,
            birth_time=birth_time,
            lat=profile.birth_lat,
            lng=profile.birth_lng,
            tz_str=profile.birth_tz,
        )
        
        async with get_db() as session:
            result = await session.execute(
                select(UserAstrologyProfile).where(UserAstrologyProfile.user_id == user_id)
            )
            prof = result.scalar_one_or_none()
            if prof:
                prof.birth_time = birth_time
                prof.birth_time_unknown = False
                prof.sun_sign = chart_data.sun_sign
                prof.moon_sign = chart_data.moon_sign
                prof.ascendant_sign = chart_data.ascendant_sign
                prof.chart_data = chart_data.to_dict()
                await session.commit()
        
        await self.core.clear_user_state(user_id)
        
        return Response(
            text=f"✅ Время рождения изменено!\n\n☀️ Солнце в {get_sign_name(chart_data.sun_sign)}\n🌙 Луна в {get_sign_name(chart_data.moon_sign)}\n⬆️ Асцендент в {get_sign_name(chart_data.ascendant_sign)}",
            keyboard=[[{"text": "⚙️ Назад к настройкам", "callback_data": kb.cb("settings")}]],
            action="send",
            clear_state=True,
        )
    
    async def _process_edit_city(self, user_id: int, text: str, state_data: dict, context: MessageContext) -> Response:
        """Обработка изменения города рождения"""
        # Геокодинг
        locations = await geocoder.geocode(text)
        
        if not locations:
            return Response(text=t("step_city_not_found"), action="send")
        
        if len(locations) == 1:
            loc = locations[0]
            city = loc["display_name"]
            lat = loc["lat"]
            lng = loc["lng"]
            tz = loc["timezone"]
            
            # Получаем профиль и пересчитываем карту
            profile = await self.get_profile(user_id)
            if not profile:
                return Response(text="Профиль не найден", action="send")
            
            # Пересчитываем карту
            chart_data = await chart_calculator.calculate_natal_chart(
                name=profile.name,
                birth_date=profile.birth_date,
                birth_time=profile.birth_time,
                lat=lat,
                lng=lng,
                tz_str=tz,
            )
            
            async with get_db() as session:
                result = await session.execute(
                    select(UserAstrologyProfile).where(UserAstrologyProfile.user_id == user_id)
                )
                prof = result.scalar_one_or_none()
                if prof:
                    prof.birth_city = city
                    prof.birth_lat = lat
                    prof.birth_lng = lng
                    prof.birth_tz = tz
                    prof.sun_sign = chart_data.sun_sign
                    prof.moon_sign = chart_data.moon_sign
                    prof.ascendant_sign = chart_data.ascendant_sign
                    prof.chart_data = chart_data.to_dict()
                    await session.commit()
            
            await self.core.clear_user_state(user_id)
            
            return Response(
                text=f"✅ Город изменён!\n\n🌍 {city}\n\n☀️ Солнце в {get_sign_name(chart_data.sun_sign)}\n🌙 Луна в {get_sign_name(chart_data.moon_sign)}\n⬆️ Асцендент в {get_sign_name(chart_data.ascendant_sign)}",
                keyboard=[[{"text": "⚙️ Назад к настройкам", "callback_data": kb.cb("settings")}]],
                action="send",
                clear_state=True,
            )
        
        # Несколько городов - показываем выбор
        # TODO: Добавить выбор из нескольких городов
        loc = locations[0]
        city = loc["display_name"]
        lat = loc["lat"]
        lng = loc["lng"]
        tz = loc["timezone"]
        
        profile = await self.get_profile(user_id)
        if not profile:
            return Response(text="Профиль не найден", action="send")
        
        chart_data = await chart_calculator.calculate_natal_chart(
            name=profile.name,
            birth_date=profile.birth_date,
            birth_time=profile.birth_time,
            lat=lat,
            lng=lng,
            tz_str=tz,
        )
        
        async with get_db() as session:
            result = await session.execute(
                select(UserAstrologyProfile).where(UserAstrologyProfile.user_id == user_id)
            )
            prof = result.scalar_one_or_none()
            if prof:
                prof.birth_city = city
                prof.birth_lat = lat
                prof.birth_lng = lng
                prof.birth_tz = tz
                prof.sun_sign = chart_data.sun_sign
                prof.moon_sign = chart_data.moon_sign
                prof.ascendant_sign = chart_data.ascendant_sign
                prof.chart_data = chart_data.to_dict()
                await session.commit()
        
        await self.core.clear_user_state(user_id)
        
        return Response(
            text=f"✅ Город изменён!\n\n🌍 {city}\n\n☀️ Солнце в {get_sign_name(chart_data.sun_sign)}\n🌙 Луна в {get_sign_name(chart_data.moon_sign)}\n⬆️ Асцендент в {get_sign_name(chart_data.ascendant_sign)}",
            keyboard=[[{"text": "⚙️ Назад к настройкам", "callback_data": kb.cb("settings")}]],
            action="send",
            clear_state=True,
        )
