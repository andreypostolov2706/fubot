"""
Settings Manager — Единый интерфейс для работы с настройками

Особенности:
- Кэширование для уменьшения запросов к БД
- Типизированные методы (get_decimal, get_bool, get_json)
- Автоматическая инвалидация кэша при изменении
- Регистрация всех используемых настроек
"""
from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import json

from loguru import logger
from sqlalchemy import select

from core.database import get_db
from core.database.models import Setting


@dataclass
class SettingDefinition:
    """Definition of a setting"""
    key: str
    default: Any
    value_type: str  # string, decimal, bool, json, int
    description: str
    category: str
    is_editable: bool = True


@dataclass 
class CachedValue:
    """Cached setting value"""
    value: Any
    expires_at: datetime


class SettingsManager:
    """
    Centralized settings manager with caching.
    
    Usage:
        from core.settings import settings
        
        # Get values
        min_payout = await settings.get_decimal("payout.min_gton")
        is_enabled = await settings.get_bool("referral.enabled")
        
        # Set values (invalidates cache)
        await settings.set("payout.min_gton", "100")
    """
    
    # Cache TTL in seconds
    CACHE_TTL = 60
    
    def __init__(self):
        self._cache: Dict[str, CachedValue] = {}
        self._definitions: Dict[str, SettingDefinition] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """Register all known settings with defaults"""
        defaults = [
            # === Payments ===
            SettingDefinition(
                key="payments.min_deposit_gton",
                default=Decimal("1.0"),
                value_type="decimal",
                description="Минимальная сумма пополнения в GTON",
                category="payments"
            ),
            SettingDefinition(
                key="payments.max_deposit_gton",
                default=Decimal("10000"),
                value_type="decimal",
                description="Максимальная сумма пополнения в GTON",
                category="payments"
            ),
            SettingDefinition(
                key="payments.gton_ton_rate",
                default=Decimal("1.0"),
                value_type="decimal",
                description="Курс GTON к TON",
                category="payments"
            ),
            SettingDefinition(
                key="payments.fee_percent",
                default=Decimal("0"),
                value_type="decimal",
                description="Комиссия на пополнение (%)",
                category="payments"
            ),
            SettingDefinition(
                key="payments.welcome_bonus_gton",
                default=Decimal("0"),
                value_type="decimal",
                description="Приветственный бонус в GTON",
                category="payments"
            ),
            
            # === Telegram Stars ===
            SettingDefinition(
                key="payments.stars_enabled",
                default=True,
                value_type="bool",
                description="Оплата через Telegram Stars включена",
                category="payments"
            ),
            SettingDefinition(
                key="payments.stars_rub_rate",
                default=Decimal("1.5"),
                value_type="decimal",
                description="Курс: 1 Star = X RUB",
                category="payments"
            ),
            SettingDefinition(
                key="payments.stars_min_amount",
                default=10,
                value_type="int",
                description="Минимум Stars для пополнения",
                category="payments"
            ),
            SettingDefinition(
                key="payments.stars_max_amount",
                default=10000,
                value_type="int",
                description="Максимум Stars для пополнения",
                category="payments"
            ),
            
            # === Payout ===
            SettingDefinition(
                key="payout.min_gton",
                default=Decimal("5.0"),
                value_type="decimal",
                description="Минимальная сумма вывода в GTON",
                category="payout"
            ),
            SettingDefinition(
                key="payout.fee_percent",
                default=Decimal("0"),
                value_type="decimal",
                description="Комиссия на вывод (%)",
                category="payout"
            ),
            SettingDefinition(
                key="payout.methods",
                default=["card", "sbp"],
                value_type="json",
                description="Доступные методы вывода",
                category="payout"
            ),
            
            # === Referral ===
            SettingDefinition(
                key="referral.enabled",
                default=True,
                value_type="bool",
                description="Реферальная система включена",
                category="referral"
            ),
            SettingDefinition(
                key="referral.commission_enabled",
                default=True,
                value_type="bool",
                description="Начисление комиссий включено",
                category="referral"
            ),
            SettingDefinition(
                key="referral.level1_percent",
                default=Decimal("10"),
                value_type="decimal",
                description="Комиссия реферера 1 уровня (%)",
                category="referral"
            ),
            SettingDefinition(
                key="referral.partner_level1_percent",
                default=Decimal("20"),
                value_type="decimal",
                description="Комиссия партнёра 1 уровня (%)",
                category="referral"
            ),
            SettingDefinition(
                key="referral.level2_enabled",
                default=False,
                value_type="bool",
                description="2 уровень рефералов включен",
                category="referral"
            ),
            SettingDefinition(
                key="referral.level2_percent",
                default=Decimal("5"),
                value_type="decimal",
                description="Комиссия 2 уровня (%)",
                category="referral"
            ),
            
            # === Daily Bonus ===
            SettingDefinition(
                key="daily_bonus.enabled",
                default=True,
                value_type="bool",
                description="Ежедневный бонус включен",
                category="daily_bonus"
            ),
            SettingDefinition(
                key="daily_bonus.rewards",
                default=[0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 2.0],
                value_type="json",
                description="Награды по дням (GTON)",
                category="daily_bonus"
            ),
            
            # === General ===
            SettingDefinition(
                key="general.bot_name",
                default="FuBot",
                value_type="string",
                description="Название бота",
                category="general"
            ),
            SettingDefinition(
                key="general.support_username",
                default="",
                value_type="string",
                description="Username поддержки",
                category="general"
            ),
            SettingDefinition(
                key="general.default_language",
                default="ru",
                value_type="string",
                description="Язык по умолчанию",
                category="general"
            ),
        ]
        
        for d in defaults:
            self._definitions[d.key] = d
    
    def _is_expired(self, key: str) -> bool:
        """Check if cached value is expired"""
        if key not in self._cache:
            return True
        return datetime.utcnow() > self._cache[key].expires_at
    
    async def _load_from_db(self, key: str) -> Optional[str]:
        """Load setting value from database"""
        async with get_db() as session:
            result = await session.execute(
                select(Setting.value).where(Setting.key == key)
            )
            return result.scalar()
    
    def _convert_value(self, value: str, value_type: str) -> Any:
        """Convert string value to appropriate type"""
        if value is None:
            return None
        
        try:
            if value_type == "decimal":
                return Decimal(str(value))
            elif value_type == "int":
                return int(value)
            elif value_type == "bool":
                return str(value).lower() in ("true", "1", "yes", "on")
            elif value_type == "json":
                if isinstance(value, str):
                    return json.loads(value)
                return value
            else:
                return str(value)
        except Exception as e:
            logger.warning(f"Failed to convert setting {value} to {value_type}: {e}")
            return value
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get setting value with caching.
        
        Args:
            key: Setting key (e.g., "payout.min_gton")
            default: Default value if not found
            
        Returns:
            Setting value (converted to appropriate type)
        """
        # Check cache first
        if not self._is_expired(key):
            return self._cache[key].value
        
        # Load from DB
        raw_value = await self._load_from_db(key)
        
        # Get definition for type conversion
        definition = self._definitions.get(key)
        
        if raw_value is not None:
            value_type = definition.value_type if definition else "string"
            value = self._convert_value(raw_value, value_type)
        elif definition:
            value = definition.default
        else:
            value = default
        
        # Cache the value
        self._cache[key] = CachedValue(
            value=value,
            expires_at=datetime.utcnow() + timedelta(seconds=self.CACHE_TTL)
        )
        
        return value
    
    async def get_decimal(self, key: str, default: Decimal = Decimal("0")) -> Decimal:
        """Get setting as Decimal"""
        value = await self.get(key, default)
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except:
            return default
    
    async def get_int(self, key: str, default: int = 0) -> int:
        """Get setting as int"""
        value = await self.get(key, default)
        try:
            return int(value)
        except:
            return default
    
    async def get_bool(self, key: str, default: bool = False) -> bool:
        """Get setting as bool"""
        value = await self.get(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "yes", "on")
    
    async def get_json(self, key: str, default: Any = None) -> Any:
        """Get setting as JSON (list/dict)"""
        value = await self.get(key, default)
        if isinstance(value, (list, dict)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                pass
        return default if default is not None else []
    
    async def get_str(self, key: str, default: str = "") -> str:
        """Get setting as string"""
        value = await self.get(key, default)
        return str(value) if value else default
    
    async def set(self, key: str, value: Any, updated_by: int = None) -> bool:
        """
        Set setting value in database and invalidate cache.
        
        Args:
            key: Setting key
            value: New value
            updated_by: User ID who made the change
            
        Returns:
            True if successful
        """
        try:
            # Convert value to string for storage
            if isinstance(value, (list, dict)):
                str_value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, bool):
                str_value = "true" if value else "false"
            else:
                str_value = str(value)
            
            async with get_db() as session:
                result = await session.execute(
                    select(Setting).where(Setting.key == key)
                )
                setting = result.scalar_one_or_none()
                
                if setting:
                    setting.value = str_value
                    setting.updated_at = datetime.utcnow()
                    if updated_by:
                        setting.updated_by = updated_by
                else:
                    # Create new setting
                    definition = self._definitions.get(key)
                    setting = Setting(
                        key=key,
                        value=str_value,
                        value_type=definition.value_type if definition else "string",
                        description=definition.description if definition else "",
                        category=definition.category if definition else "general",
                        is_editable=True,
                        updated_by=updated_by
                    )
                    session.add(setting)
            
            # Invalidate cache
            self.invalidate(key)
            
            logger.info(f"Setting {key} updated to {str_value[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set setting {key}: {e}")
            return False
    
    def invalidate(self, key: str = None):
        """
        Invalidate cache.
        
        Args:
            key: Specific key to invalidate, or None for all
        """
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
    
    def get_definitions(self, category: str = None) -> List[SettingDefinition]:
        """Get all setting definitions, optionally filtered by category"""
        if category:
            return [d for d in self._definitions.values() if d.category == category]
        return list(self._definitions.values())
    
    def get_categories(self) -> List[str]:
        """Get all unique categories"""
        return list(set(d.category for d in self._definitions.values()))
    
    async def get_all_values(self, category: str = None) -> Dict[str, Any]:
        """Get all settings with their current values"""
        definitions = self.get_definitions(category)
        result = {}
        
        for d in definitions:
            value = await self.get(d.key, d.default)
            result[d.key] = {
                "value": value,
                "default": d.default,
                "type": d.value_type,
                "description": d.description,
                "category": d.category,
                "is_editable": d.is_editable
            }
        
        return result


# Global instance
settings = SettingsManager()
