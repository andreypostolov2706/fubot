"""
Astrology Service - Geocoder (Nominatim/OpenStreetMap)
"""
import asyncio
from dataclasses import dataclass
from typing import Optional, List
from functools import lru_cache

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from timezonefinder import TimezoneFinder

from loguru import logger


@dataclass
class GeoLocation:
    """Результат геокодинга"""
    city: str               # Полное название (Москва, Россия)
    lat: float              # Широта
    lng: float              # Долгота
    tz: str                 # Часовой пояс (Europe/Moscow)
    display_name: str       # Полный адрес
    country: str            # Страна
    country_code: str       # Код страны (RU)


class Geocoder:
    """Геокодер на базе Nominatim (OpenStreetMap)"""
    
    def __init__(self):
        self._geolocator = Nominatim(
            user_agent="fubot_astrology/1.0",
            timeout=10
        )
        self._tz_finder = TimezoneFinder()
        self._cache: dict[str, List[GeoLocation]] = {}
    
    async def search(self, query: str, limit: int = 5) -> List[GeoLocation]:
        """
        Поиск города по названию.
        
        Args:
            query: Название города (например, "Москва")
            limit: Максимум результатов
            
        Returns:
            Список найденных локаций
        """
        # Проверяем кэш
        cache_key = query.lower().strip()
        if cache_key in self._cache:
            return self._cache[cache_key][:limit]
        
        try:
            # Выполняем поиск в отдельном потоке (geopy синхронный)
            loop = asyncio.get_event_loop()
            locations = await loop.run_in_executor(
                None,
                lambda: self._geolocator.geocode(
                    query,
                    exactly_one=False,
                    limit=limit,
                    language="ru",
                    addressdetails=True
                )
            )
            
            if not locations:
                return []
            
            results = []
            for loc in locations:
                # Определяем часовой пояс по координатам
                tz = self._tz_finder.timezone_at(lat=loc.latitude, lng=loc.longitude)
                if not tz:
                    tz = "UTC"
                
                # Извлекаем данные адреса
                address = loc.raw.get("address", {})
                city = (
                    address.get("city") or 
                    address.get("town") or 
                    address.get("village") or
                    address.get("municipality") or
                    address.get("state") or
                    query
                )
                country = address.get("country", "")
                country_code = address.get("country_code", "").upper()
                
                # Формируем отображаемое название
                display_parts = [city]
                if address.get("state") and address.get("state") != city:
                    display_parts.append(address.get("state"))
                if country:
                    display_parts.append(country)
                display_name = ", ".join(display_parts)
                
                results.append(GeoLocation(
                    city=display_name,
                    lat=loc.latitude,
                    lng=loc.longitude,
                    tz=tz,
                    display_name=loc.address,
                    country=country,
                    country_code=country_code
                ))
            
            # Кэшируем результат
            self._cache[cache_key] = results
            
            return results[:limit]
            
        except GeocoderTimedOut:
            logger.warning(f"Geocoder timeout for query: {query}")
            return []
        except GeocoderServiceError as e:
            logger.error(f"Geocoder service error: {e}")
            return []
        except Exception as e:
            logger.exception(f"Geocoder error for query '{query}': {e}")
            return []
    
    async def search_one(self, query: str) -> Optional[GeoLocation]:
        """
        Поиск одного города.
        
        Returns:
            Первый найденный результат или None
        """
        results = await self.search(query, limit=1)
        return results[0] if results else None
    
    def get_timezone(self, lat: float, lng: float) -> str:
        """
        Определить часовой пояс по координатам.
        
        Args:
            lat: Широта
            lng: Долгота
            
        Returns:
            Название часового пояса (например, "Europe/Moscow")
        """
        tz = self._tz_finder.timezone_at(lat=lat, lng=lng)
        return tz or "UTC"
    
    def clear_cache(self):
        """Очистить кэш"""
        self._cache.clear()


# Глобальный экземпляр
geocoder = Geocoder()
