"""
Astrology Service - Chart Calculator (Kerykeion wrapper)
"""
import asyncio
from dataclasses import dataclass, field
from datetime import date, time, datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from loguru import logger

from .config import CHARTS_DIR, ZODIAC_SIGNS, get_sign_name, get_sign_emoji


@dataclass
class ChartData:
    """Данные натальной карты"""
    # Основные знаки
    sun_sign: str           # "Ari", "Tau", etc.
    moon_sign: str
    ascendant_sign: str
    
    # Позиции планет
    planets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # {"Sun": {"sign": "Ari", "degree": 15.5, "house": 1}, ...}
    
    # Дома
    houses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # {"1": {"sign": "Leo", "degree": 10.2}, ...}
    
    # Аспекты
    aspects: List[Dict[str, Any]] = field(default_factory=list)
    # [{"planet1": "Sun", "planet2": "Moon", "aspect": "trine", "orb": 2.5}, ...]
    
    # Путь к SVG
    svg_path: Optional[str] = None
    
    # AI-контекст для LLM
    ai_context: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Конвертация в словарь для JSON"""
        return {
            "sun_sign": self.sun_sign,
            "moon_sign": self.moon_sign,
            "ascendant_sign": self.ascendant_sign,
            "planets": self.planets,
            "houses": self.houses,
            "aspects": self.aspects,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChartData":
        """Создание из словаря"""
        return cls(
            sun_sign=data.get("sun_sign", ""),
            moon_sign=data.get("moon_sign", ""),
            ascendant_sign=data.get("ascendant_sign", ""),
            planets=data.get("planets", {}),
            houses=data.get("houses", {}),
            aspects=data.get("aspects", []),
        )


class ChartCalculator:
    """Калькулятор натальных карт на базе Kerykeion"""
    
    def __init__(self):
        self._kerykeion_available = False
        self._check_kerykeion()
    
    def _check_kerykeion(self):
        """Проверка доступности Kerykeion"""
        try:
            from kerykeion import AstrologicalSubjectFactory
            self._kerykeion_available = True
            logger.info("Kerykeion library available")
        except ImportError:
            logger.warning("Kerykeion library not installed. Chart calculations will be limited.")
            self._kerykeion_available = False
    
    async def calculate_natal_chart(
        self,
        name: str,
        birth_date: date,
        birth_time: time,
        lat: float,
        lng: float,
        tz_str: str,
    ) -> ChartData:
        """
        Рассчитать натальную карту.
        
        Args:
            name: Имя человека
            birth_date: Дата рождения
            birth_time: Время рождения
            lat: Широта
            lng: Долгота
            tz_str: Часовой пояс
            
        Returns:
            ChartData с рассчитанными данными
        """
        if not self._kerykeion_available:
            return self._mock_chart_data()
        
        try:
            # Выполняем расчёт в отдельном потоке (Kerykeion синхронный)
            loop = asyncio.get_event_loop()
            chart_data = await loop.run_in_executor(
                None,
                lambda: self._calculate_sync(
                    name, birth_date, birth_time, lat, lng, tz_str
                )
            )
            return chart_data
            
        except Exception as e:
            logger.exception(f"Error calculating natal chart: {e}")
            return self._mock_chart_data()
    
    def _calculate_sync(
        self,
        name: str,
        birth_date: date,
        birth_time: time,
        lat: float,
        lng: float,
        tz_str: str,
    ) -> ChartData:
        """Синхронный расчёт карты"""
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion import to_context
        
        # Создаём субъект
        subject = AstrologicalSubjectFactory.from_birth_data(
            name=name,
            year=birth_date.year,
            month=birth_date.month,
            day=birth_date.day,
            hour=birth_time.hour,
            minute=birth_time.minute,
            lng=lng,
            lat=lat,
            tz_str=tz_str,
            online=False,
        )
        
        # Извлекаем данные планет
        planets = {}
        planet_attrs = [
            "sun", "moon", "mercury", "venus", "mars",
            "jupiter", "saturn", "uranus", "neptune", "pluto",
            "mean_node", "true_node", "chiron"
        ]
        
        for attr in planet_attrs:
            if hasattr(subject, attr):
                planet = getattr(subject, attr)
                if planet:
                    planets[planet.name] = {
                        "sign": planet.sign,
                        "degree": round(planet.position, 2),
                        "abs_pos": round(planet.abs_pos, 2),
                        "house": planet.house if hasattr(planet, "house") else None,
                        "retrograde": planet.retrograde if hasattr(planet, "retrograde") else False,
                    }
        
        # Извлекаем данные домов
        houses = {}
        for i in range(1, 13):
            house_attr = f"{'first' if i == 1 else 'second' if i == 2 else 'third' if i == 3 else 'fourth' if i == 4 else 'fifth' if i == 5 else 'sixth' if i == 6 else 'seventh' if i == 7 else 'eighth' if i == 8 else 'ninth' if i == 9 else 'tenth' if i == 10 else 'eleventh' if i == 11 else 'twelfth'}_house"
            if hasattr(subject, house_attr):
                house = getattr(subject, house_attr)
                if house:
                    houses[str(i)] = {
                        "sign": house.sign,
                        "degree": round(house.position, 2),
                    }
        
        # Генерируем AI-контекст
        ai_context = to_context(subject)
        
        return ChartData(
            sun_sign=subject.sun.sign if subject.sun else "",
            moon_sign=subject.moon.sign if subject.moon else "",
            ascendant_sign=subject.first_house.sign if subject.first_house else "",
            planets=planets,
            houses=houses,
            aspects=[],  # TODO: добавить аспекты
            ai_context=ai_context,
        )
    
    async def generate_svg(
        self,
        name: str,
        birth_date: date,
        birth_time: time,
        lat: float,
        lng: float,
        tz_str: str,
        user_id: int,
        chart_type: str = "natal",
        chart_id: Optional[int] = None,
    ) -> Optional[str]:
        """
        Сгенерировать SVG-изображение карты.
        
        Args:
            name: Имя человека
            birth_date: Дата рождения
            birth_time: Время рождения
            lat: Широта
            lng: Долгота
            tz_str: Часовой пояс
            user_id: ID пользователя
            chart_type: Тип карты (natal, synastry)
            chart_id: ID карты (для сохранённых карт)
            
        Returns:
            Путь к SVG файлу или None
        """
        if not self._kerykeion_available:
            return None
        
        try:
            # Создаём директорию пользователя
            user_dir = CHARTS_DIR / f"user_{user_id}"
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # Определяем имя файла
            if chart_id:
                filename = f"chart_{chart_id}"
            else:
                filename = chart_type
            
            # Выполняем генерацию в отдельном потоке
            loop = asyncio.get_event_loop()
            svg_path = await loop.run_in_executor(
                None,
                lambda: self._generate_svg_sync(
                    name, birth_date, birth_time, lat, lng, tz_str,
                    user_dir, filename
                )
            )
            return svg_path
            
        except Exception as e:
            logger.exception(f"Error generating SVG: {e}")
            return None
    
    def _generate_svg_sync(
        self,
        name: str,
        birth_date: date,
        birth_time: time,
        lat: float,
        lng: float,
        tz_str: str,
        output_dir: Path,
        filename: str,
    ) -> Optional[str]:
        """Синхронная генерация SVG"""
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.chart_data_factory import ChartDataFactory
        from kerykeion.charts.chart_drawer import ChartDrawer
        
        # Создаём субъект
        subject = AstrologicalSubjectFactory.from_birth_data(
            name=name,
            year=birth_date.year,
            month=birth_date.month,
            day=birth_date.day,
            hour=birth_time.hour,
            minute=birth_time.minute,
            lng=lng,
            lat=lat,
            tz_str=tz_str,
            online=False,
        )
        
        # Создаём данные карты
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        
        # Рисуем карту
        chart_drawer = ChartDrawer(chart_data=chart_data)
        chart_drawer.save_svg(output_path=output_dir, filename=filename)
        
        svg_path = output_dir / f"{filename}.svg"
        return str(svg_path) if svg_path.exists() else None
    
    async def calculate_synastry(
        self,
        person1_data: dict,
        person2_data: dict,
    ) -> Dict[str, Any]:
        """
        Рассчитать синастрию (совместимость).
        
        Args:
            person1_data: Данные первого человека
            person2_data: Данные второго человека
            
        Returns:
            Данные синастрии
        """
        if not self._kerykeion_available:
            return {"aspects": [], "compatibility_score": 75}
        
        # TODO: реализовать расчёт синастрии
        return {"aspects": [], "compatibility_score": 75}
    
    async def calculate_transits(
        self,
        natal_chart: ChartData,
        transit_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Рассчитать транзиты.
        
        Args:
            natal_chart: Натальная карта
            transit_date: Дата для транзитов (по умолчанию сейчас)
            
        Returns:
            Список транзитов
        """
        if not self._kerykeion_available:
            return []
        
        # TODO: реализовать расчёт транзитов
        return []
    
    def _mock_chart_data(self) -> ChartData:
        """Заглушка для тестирования без Kerykeion"""
        return ChartData(
            sun_sign="Pis",
            moon_sign="Leo",
            ascendant_sign="Can",
            planets={
                "Sun": {"sign": "Pis", "degree": 15.5, "house": "10"},
                "Moon": {"sign": "Leo", "degree": 22.3, "house": "2"},
                "Mercury": {"sign": "Pis", "degree": 5.1, "house": "10"},
                "Venus": {"sign": "Ari", "degree": 10.8, "house": "11"},
                "Mars": {"sign": "Gem", "degree": 18.2, "house": "12"},
            },
            houses={
                "1": {"sign": "Can", "degree": 10.0},
                "2": {"sign": "Leo", "degree": 5.0},
                "3": {"sign": "Vir", "degree": 3.0},
            },
            aspects=[],
            ai_context="Mock chart data for testing",
        )
    
    def format_chart_summary(self, chart: ChartData) -> str:
        """
        Форматировать краткую сводку карты.
        
        Returns:
            Строка вида "♓ Рыбы • Луна ♌ Лев • Асц ♋ Рак"
        """
        sun = f"{get_sign_emoji(chart.sun_sign)} {get_sign_name(chart.sun_sign)}"
        moon = f"Луна {get_sign_emoji(chart.moon_sign)} {get_sign_name(chart.moon_sign)}"
        asc = f"Асц {get_sign_emoji(chart.ascendant_sign)} {get_sign_name(chart.ascendant_sign)}"
        return f"{sun} • {moon} • {asc}"


# Глобальный экземпляр
chart_calculator = ChartCalculator()
