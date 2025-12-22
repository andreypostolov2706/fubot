# Ежедневный бонус

## Обзор

Система ежедневных бонусов для повышения retention:
- Бонус в **GTON** за вход каждый день
- Серия дней (streak) с увеличением награды
- Потеря серии при пропуске

---

## Таблица `daily_bonuses`

```python
class DailyBonus(Base):
    """Ежедневные бонусы пользователей"""
    __tablename__ = "daily_bonuses"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # === Серия ===
    current_streak = Column(Integer, default=0)    # Текущая серия дней
    max_streak = Column(Integer, default=0)        # Максимальная серия
    
    # === Последний бонус ===
    last_claim_date = Column(Date, index=True)     # Дата последнего получения
    last_claim_at = Column(DateTime)               # Время последнего получения
    
    # === Статистика ===
    total_claims = Column(Integer, default=0)      # Всего получений
    total_tokens = Column(Numeric(18, 6), default=Decimal("0"))  # Всего GTON
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

## Таблица `daily_bonus_history`

```python
class DailyBonusHistory(Base):
    """История получения ежедневных бонусов"""
    __tablename__ = "daily_bonus_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # === Бонус ===
    day_number = Column(Integer, nullable=False)   # День серии (1-7)
    tokens = Column(Numeric(18, 6), nullable=False)  # Полученные GTON
    streak = Column(Integer, nullable=False)       # Серия на момент получения
    
    # === Связь ===
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    
    # === Timestamp ===
    claimed_at = Column(DateTime, default=datetime.utcnow, index=True)
```

---

## Настройки

```python
# settings
"daily_bonus.enabled": True
"daily_bonus.reset_hour": 0                    # Час сброса (0 = полночь)
"daily_bonus.timezone": "Europe/Moscow"        # Часовой пояс для сброса

# Награды по дням (GTON)
"daily_bonus.rewards": '[0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 2.0]'
# День 1: 0.1 GTON
# День 2: 0.2 GTON
# День 3: 0.3 GTON
# День 4: 0.5 GTON
# День 5: 0.7 GTON
# День 6: 1.0 GTON
# День 7: 2.0 GTON (потом цикл повторяется)

"daily_bonus.streak_multiplier": 1.0           # Множитель за серию (1.0 = нет)
"daily_bonus.max_streak_bonus": 100            # Макс. бонус за серию
```

---

## Логика работы

```python
async def check_daily_bonus(user_id: int) -> DailyBonusStatus:
    """
    Проверить статус ежедневного бонуса.
    
    Returns:
        DailyBonusStatus:
            - available: bool          # Можно ли забрать
            - current_streak: int      # Текущая серия
            - next_reward: int         # Следующая награда
            - day_number: int          # Какой день (1-7)
            - time_until_next: timedelta  # До следующего бонуса
            - streak_will_reset: bool  # Серия сбросится если не забрать
    """
    
    bonus = await get_user_daily_bonus(user_id)
    today = get_today_date()  # С учётом timezone
    
    if bonus.last_claim_date is None:
        # Первый раз
        return DailyBonusStatus(
            available=True,
            current_streak=0,
            next_reward=REWARDS[0],
            day_number=1
        )
    
    days_diff = (today - bonus.last_claim_date).days
    
    if days_diff == 0:
        # Уже забрал сегодня
        return DailyBonusStatus(
            available=False,
            current_streak=bonus.current_streak,
            time_until_next=get_time_until_reset()
        )
    
    if days_diff == 1:
        # Вчера забирал — серия продолжается
        next_day = (bonus.current_streak % 7) + 1
        return DailyBonusStatus(
            available=True,
            current_streak=bonus.current_streak,
            next_reward=REWARDS[next_day - 1],
            day_number=next_day
        )
    
    # Пропустил — серия сбрасывается
    return DailyBonusStatus(
        available=True,
        current_streak=0,  # Сброс
        next_reward=REWARDS[0],
        day_number=1,
        streak_will_reset=True
    )


async def claim_daily_bonus(user_id: int) -> ClaimResult:
    """
    Забрать ежедневный бонус.
    
    Returns:
        ClaimResult:
            - success: bool
            - tokens: int
            - new_streak: int
            - day_number: int
            - new_balance: int
    """
```

---

## Core API

```python
async def get_daily_bonus_status(self, user_id: int) -> DailyBonusStatus:
    """Получить статус ежедневного бонуса."""

async def claim_daily_bonus(self, user_id: int) -> ClaimResult:
    """Забрать ежедневный бонус."""

async def get_daily_bonus_history(
    self, 
    user_id: int, 
    limit: int = 30
) -> list[DailyBonusHistoryDTO]:
    """История получения бонусов."""
```

---

## Меню пользователя

### Бонус доступен

```
🎁 Ежедневный бонус

🔥 Серия: 5 дней

День 6 из 7
Награда: 1.0 GTON

┌─────────────────────────┐
│ 🎁 Забрать бонус        │
├─────────────────────────┤
│ 📊 История              │
├─────────────────────────┤
│ ◀️ Назад                │
└─────────────────────────┘
```

### После получения

```
✅ Бонус получен!

🎁 +1.0 GTON
💰 Баланс: 5.8 GTON (~600 ₽)

🔥 Серия: 6 дней
📅 Завтра: 2.0 GTON (день 7!)

┌─────────────────────────┐
│ ◀️ В меню               │
└─────────────────────────┘
```

### Бонус уже получен

```
🎁 Ежедневный бонус

✅ Сегодня уже получен

🔥 Серия: 6 дней
⏰ Следующий через: 5ч 23м

📅 Завтра: 2.0 GTON (день 7!)

💡 Не пропускай дни, чтобы 
   не потерять серию!

┌─────────────────────────┐
│ 📊 История              │
├─────────────────────────┤
│ ◀️ Назад                │
└─────────────────────────┘
```

### Серия сброшена

```
🎁 Ежедневный бонус

😔 Серия прервана!

Вы пропустили день и серия 
сбросилась. Начинаем заново!

День 1 из 7
Награда: 0.1 GTON

┌─────────────────────────┐
│ 🎁 Забрать бонус        │
├─────────────────────────┤
│ ◀️ Назад                │
└─────────────────────────┘
```

---

## Визуализация серии

```
🎁 Ежедневный бонус

Ваш прогресс:

  1    2    3    4    5    6    7
 [✅] [✅] [✅] [✅] [✅] [🎁] [ ]
 0.1  0.2  0.3  0.5  0.7  1.0  2.0

🔥 Серия: 5 дней
📅 Сегодня: День 6 — 1.0 GTON

┌─────────────────────────┐
│ 🎁 Забрать бонус        │
└─────────────────────────┘
```

Альтернативный вариант (компактный):

```
🎁 Ежедневный бонус

День: ①②③④⑤⑥⑦
      ✓ ✓ ✓ ✓ ✓ 🎁 ·

🔥 Серия: 5 дней | Награда: 1.0 GTON

┌─────────────────────────┐
│ 🎁 Забрать              │
└─────────────────────────┘
```

---

## Интеграция в главное меню

```
🏠 Главное меню

💰 Баланс: 4.8 GTON (~500 ₽)
🎁 Бонус готов!              ← Индикатор

┌─────────────────────────┐
│ 🎁 Забрать бонус (1.0 GTON)│  ← Быстрая кнопка
├─────────────────────────┤
│ 🧠 ИИ-Психолог          │
├─────────────────────────┤
│ 💳 Пополнить            │
├─────────────────────────┤
│ ...                     │
└─────────────────────────┘
```

---

## Уведомления

### Напоминание (если включено)

```
🎁 Ежедневный бонус ждёт!

Не забудь забрать свой бонус сегодня.

🔥 Твоя серия: 5 дней
🎁 Награда: 1.0 GTON

Не пропусти, чтобы не потерять серию!

[🎁 Забрать]
```

### Серия под угрозой (вечером)

```
⚠️ Серия под угрозой!

Ты ещё не забрал бонус сегодня.
До сброса: 2 часа

🔥 Серия: 5 дней
🎁 Награда: 30 токенов

[🎁 Забрать сейчас]
```

---

## Локализация

```python
# core/locales/ru.py

DAILY_BONUS = {
    "title": "\ud83c\udf81 <b>\u0415\u0436\u0435\u0434\u043d\u0435\u0432\u043d\u044b\u0439 \u0431\u043e\u043d\u0443\u0441</b>",
    
    # \u0421\u0442\u0430\u0442\u0443\u0441
    "streak": "\ud83d\udd25 \u0421\u0435\u0440\u0438\u044f: {days} \u0434\u043d\u0435\u0439",
    "day_of": "\u0414\u0435\u043d\u044c {current} \u0438\u0437 {total}",
    "reward": "\u041d\u0430\u0433\u0440\u0430\u0434\u0430: {gton} GTON",
    "next_reward": "\u0417\u0430\u0432\u0442\u0440\u0430: {gton} GTON",
    "next_in": "\u23f0 \u0421\u043b\u0435\u0434\u0443\u044e\u0447\u0438\u0439 \u0447\u0435\u0440\u0435\u0437: {time}",
    
    # \u0414\u0435\u0439\u0441\u0442\u0432\u0438\u044f
    "claim": "\ud83c\udf81 \u0417\u0430\u0431\u0440\u0430\u0442\u044c \u0431\u043e\u043d\u0443\u0441",
    "claim_short": "\ud83c\udf81 \u0417\u0430\u0431\u0440\u0430\u0442\u044c",
    "history": "\ud83d\udcca \u0418\u0441\u0442\u043e\u0440\u0438\u044f",
    
    # \u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442
    "claimed_title": "\u2705 \u0411\u043e\u043d\u0443\u0441 \u043f\u043e\u043b\u0443\u0447\u0435\u043d!",
    "claimed_gton": "\ud83c\udf81 +{gton} GTON",
    "new_balance": "\ud83d\udcb0 \u0411\u0430\u043b\u0430\u043d\u0441: {balance} GTON (~{fiat} \u20bd)",
    "new_streak": "\ud83d\udd25 \u0421\u0435\u0440\u0438\u044f: {days} \u0434\u043d\u0435\u0439",
    
    # \u0423\u0436\u0435 \u043f\u043e\u043b\u0443\u0447\u0435\u043d
    "already_claimed": "\u2705 \u0421\u0435\u0433\u043e\u0434\u043d\u044f \u0443\u0436\u0435 \u043f\u043e\u043b\u0443\u0447\u0435\u043d",
    "dont_miss": "\ud83d\udca1 \u041d\u0435 \u043f\u0440\u043e\u043f\u0443\u0441\u043a\u0430\u0439 \u0434\u043d\u0438, \u0447\u0442\u043e\u0431\u044b \u043d\u0435 \u043f\u043e\u0442\u0435\u0440\u044f\u0442\u044c \u0441\u0435\u0440\u0438\u044e!",
    
    # \u0421\u0431\u0440\u043e\u0441 \u0441\u0435\u0440\u0438\u0438
    "streak_lost_title": "\ud83d\ude14 \u0421\u0435\u0440\u0438\u044f \u043f\u0440\u0435\u0440\u0432\u0430\u043d\u0430!",
    "streak_lost_text": "\u0412\u044b \u043f\u0440\u043e\u043f\u0443\u0441\u0442\u0438\u043b\u0438 \u0434\u0435\u043d\u044c \u0438 \u0441\u0435\u0440\u0438\u044f \u0441\u0431\u0440\u043e\u0441\u0438\u043b\u0430\u0441\u044c. \u041d\u0430\u0447\u0438\u043d\u0430\u0435\u043c \u0437\u0430\u043d\u043e\u0432\u043e!",
    
    # \u0414\u0435\u043d\u044c 7
    "day7_tomorrow": "\ud83d\udcc5 \u0417\u0430\u0432\u0442\u0440\u0430: {gton} GTON (\u0434\u0435\u043d\u044c 7!)",
    "day7_congrats": "\ud83c\udf89 \u041f\u043e\u0437\u0434\u0440\u0430\u0432\u043b\u044f\u0435\u043c! \u041c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f \u043d\u0430\u0433\u0440\u0430\u0434\u0430!",
    
    # \u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u044f
    "notify_available": "\ud83c\udf81 \u0415\u0436\u0435\u0434\u043d\u0435\u0432\u043d\u044b\u0439 \u0431\u043e\u043d\u0443\u0441 \u0436\u0434\u0451\u0442!",
    "notify_reminder": "\u041d\u0435 \u0437\u0430\u0431\u0443\u0434\u044c \u0437\u0430\u0431\u0440\u0430\u0442\u044c \u0441\u0432\u043e\u0439 \u0431\u043e\u043d\u0443\u0441 \u0441\u0435\u0433\u043e\u0434\u043d\u044f.",
    "notify_warning": "\u26a0\ufe0f \u0421\u0435\u0440\u0438\u044f \u043f\u043e\u0434 \u0443\u0433\u0440\u043e\u0437\u043e\u0439!",
    "notify_time_left": "\u0414\u043e \u0441\u0431\u0440\u043e\u0441\u0430: {time}",
}
```

---

## Callback data

```
daily_bonus              - Меню ежедневного бонуса
daily_bonus:claim        - Забрать бонус
daily_bonus:history      - История
```

---

## Аналитика

```python
# События
"daily_bonus:claimed"        # value = tokens
"daily_bonus:streak_lost"    # value = lost_streak
"daily_bonus:streak_7"       # Достиг 7 дней
"daily_bonus:streak_30"      # Достиг 30 дней
```
