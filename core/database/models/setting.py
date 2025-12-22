"""
Setting Model
"""
from datetime import datetime
from typing import Optional, Any
import json

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, Boolean
)
from sqlalchemy.orm import Mapped

from core.database.base import Base


class Setting(Base):
    """Global settings"""
    __tablename__ = "settings"
    
    key: Mapped[str] = Column(String(100), primary_key=True)
    
    # === Value ===
    value: Mapped[str] = Column(Text, nullable=False)
    value_type: Mapped[str] = Column(String(20), default="string")
    # string, int, float, bool, json
    
    # === Description ===
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # === Category ===
    category: Mapped[Optional[str]] = Column(String(50), index=True, nullable=True)
    # general, payments, referral, notifications, limits, localization
    
    # === Editability ===
    is_editable: Mapped[bool] = Column(Boolean, default=True)
    
    # === Change Info ===
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    updated_by: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<Setting(key={self.key}, value={self.value})>"
    
    def get_typed_value(self) -> Any:
        """Get value with proper type"""
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        elif self.value_type == "json":
            return json.loads(self.value)
        return self.value
    
    @classmethod
    def from_typed_value(cls, key: str, value: Any, **kwargs) -> "Setting":
        """Create setting from typed value"""
        if isinstance(value, bool):
            value_type = "bool"
            str_value = "true" if value else "false"
        elif isinstance(value, int):
            value_type = "int"
            str_value = str(value)
        elif isinstance(value, float):
            value_type = "float"
            str_value = str(value)
        elif isinstance(value, (dict, list)):
            value_type = "json"
            str_value = json.dumps(value)
        else:
            value_type = "string"
            str_value = str(value)
        
        return cls(key=key, value=str_value, value_type=value_type, **kwargs)
