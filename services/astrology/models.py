"""
Astrology Service - Database Models
"""
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Time,
    ForeignKey, Text, JSON, Boolean, Float, DECIMAL
)
from sqlalchemy.orm import relationship, Mapped

from core.database.base import Base


class UserAstrologyProfile(Base):
    """Профиль пользователя в сервисе астрологии"""
    __tablename__ = "astrology_profiles"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    
    # === Данные рождения ===
    name: Mapped[str] = Column(String(100), nullable=False)
    birth_date: Mapped[date] = Column(Date, nullable=False)
    birth_time: Mapped[time] = Column(Time, nullable=False)
    birth_time_unknown: Mapped[bool] = Column(Boolean, default=False)
    birth_city: Mapped[str] = Column(String(255), nullable=False)
    birth_lat: Mapped[float] = Column(Float, nullable=False)
    birth_lng: Mapped[float] = Column(Float, nullable=False)
    birth_tz: Mapped[str] = Column(String(50), nullable=False)
    
    # === Рассчитанные данные ===
    sun_sign: Mapped[Optional[str]] = Column(String(20), nullable=True)
    moon_sign: Mapped[Optional[str]] = Column(String(20), nullable=True)
    ascendant_sign: Mapped[Optional[str]] = Column(String(20), nullable=True)
    chart_data: Mapped[Optional[dict]] = Column(JSON, nullable=True)
    svg_path: Mapped[Optional[str]] = Column(String(500), nullable=True)
    
    # === Бонусы ===
    has_referral_bonus: Mapped[bool] = Column(Boolean, default=False)
    free_horoscope_used: Mapped[bool] = Column(Boolean, default=False)
    
    # === Лимиты ===
    max_saved_charts: Mapped[int] = Column(Integer, default=10)
    
    # === Подписка на ежедневный гороскоп ===
    daily_horoscope_enabled: Mapped[bool] = Column(Boolean, default=False)  # ВКЛ/ВЫКЛ ежедневный гороскоп
    subscription_type: Mapped[Optional[str]] = Column(String(20), nullable=True)
    subscription_until: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    subscription_plan: Mapped[Optional[str]] = Column(String(20), nullable=True)
    subscription_send_time: Mapped[Optional[time]] = Column(Time, nullable=True)
    subscription_tz: Mapped[Optional[str]] = Column(String(50), nullable=True)
    subscription_auto_renew: Mapped[bool] = Column(Boolean, default=True)
    subscription_notified: Mapped[bool] = Column(Boolean, default=False)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    
    # === Relationships ===
    user = relationship("User", backref="astrology_profile")
    saved_charts = relationship("SavedChart", back_populates="owner", cascade="all, delete-orphan")
    readings = relationship("AstrologyReading", back_populates="profile", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<UserAstrologyProfile(user_id={self.user_id}, name={self.name}, sun={self.sun_sign})>"


class SavedChart(Base):
    """Сохранённые карты других людей"""
    __tablename__ = "astrology_saved_charts"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    profile_id: Mapped[int] = Column(
        Integer, ForeignKey("astrology_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    
    # === Информация о человеке ===
    name: Mapped[str] = Column(String(100), nullable=False)
    relation: Mapped[str] = Column(String(20), nullable=False)
    
    # === Данные рождения ===
    birth_date: Mapped[date] = Column(Date, nullable=False)
    birth_time: Mapped[time] = Column(Time, nullable=False)
    birth_time_unknown: Mapped[bool] = Column(Boolean, default=False)
    birth_city: Mapped[str] = Column(String(255), nullable=False)
    birth_lat: Mapped[float] = Column(Float, nullable=False)
    birth_lng: Mapped[float] = Column(Float, nullable=False)
    birth_tz: Mapped[str] = Column(String(50), nullable=False)
    
    # === Рассчитанные данные ===
    sun_sign: Mapped[Optional[str]] = Column(String(20), nullable=True)
    moon_sign: Mapped[Optional[str]] = Column(String(20), nullable=True)
    ascendant_sign: Mapped[Optional[str]] = Column(String(20), nullable=True)
    chart_data: Mapped[Optional[dict]] = Column(JSON, nullable=True)
    svg_path: Mapped[Optional[str]] = Column(String(500), nullable=True)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    
    # === Relationships ===
    owner = relationship("UserAstrologyProfile", back_populates="saved_charts", foreign_keys=[profile_id])
    
    def __repr__(self) -> str:
        return f"<SavedChart(id={self.id}, name={self.name}, relation={self.relation})>"


class AstrologyReading(Base):
    """История чтений/интерпретаций"""
    __tablename__ = "astrology_readings"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    profile_id: Mapped[int] = Column(
        Integer, ForeignKey("astrology_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    chart_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("astrology_saved_charts.id", ondelete="SET NULL"),
        nullable=True
    )
    second_chart_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("astrology_saved_charts.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # === Тип чтения ===
    reading_type: Mapped[str] = Column(String(30), nullable=False)
    reading_subtype: Mapped[Optional[str]] = Column(String(30), nullable=True)
    
    # === Результат ===
    interpretation: Mapped[Optional[str]] = Column(Text, nullable=True)
    file_path: Mapped[Optional[str]] = Column(String(500), nullable=True)
    
    # === Стоимость ===
    is_free: Mapped[bool] = Column(Boolean, default=False)
    gton_cost: Mapped[Decimal] = Column(DECIMAL(18, 6), default=Decimal("0"))
    tokens_used: Mapped[int] = Column(Integer, default=0)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    
    # === Relationships ===
    profile = relationship("UserAstrologyProfile", back_populates="readings")
    
    def __repr__(self) -> str:
        return f"<AstrologyReading(id={self.id}, type={self.reading_type})>"


class DailyHoroscopeLog(Base):
    """Лог отправки ежедневных гороскопов"""
    __tablename__ = "astrology_daily_log"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    profile_id: Mapped[int] = Column(
        Integer, ForeignKey("astrology_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    
    # === Расписание ===
    send_date: Mapped[date] = Column(Date, nullable=False, index=True)
    scheduled_time: Mapped[time] = Column(Time, nullable=False)
    scheduled_tz: Mapped[str] = Column(String(50), nullable=False)
    
    # === Статус ===
    status: Mapped[str] = Column(String(20), default="pending")
    sent_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # === Контент ===
    horoscope_text: Mapped[Optional[str]] = Column(Text, nullable=True)
    error: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<DailyHoroscopeLog(id={self.id}, date={self.send_date}, status={self.status})>"
