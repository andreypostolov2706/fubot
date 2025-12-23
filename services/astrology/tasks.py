"""
Astrology Service - Background Tasks
"""
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, and_
from loguru import logger

from core.database import get_db

from .models import UserAstrologyProfile, DailyHoroscopeLog
from .config import SUBSCRIPTION_PLANS, DEFAULT_PRICES
from .calculator import ChartData
from .interpreter import interpreter


async def send_daily_horoscopes(bot, core_api):
    """
    Отправка ежедневных гороскопов подписчикам.
    Вызывается каждую минуту.
    Поддерживает триальный период (4 бесплатных дня) и платную отправку.
    """
    import pytz
    
    logger.info("Daily horoscope task running...")
    
    async with get_db() as session:
        # Находим пользователей с включенным ежедневным гороскопом
        result = await session.execute(
            select(UserAstrologyProfile).where(
                and_(
                    UserAstrologyProfile.daily_horoscope_enabled == True,
                    UserAstrologyProfile.subscription_send_time != None,
                )
            )
        )
        profiles = list(result.scalars().all())
        logger.info(f"Found {len(profiles)} users with daily horoscope enabled")
    
    for profile in profiles:
        try:
            # Проверяем время отправки (с точностью до минуты)
            send_time = profile.subscription_send_time
            if not send_time:
                continue
            
            # Получаем текущее время в часовом поясе пользователя
            user_tz = profile.subscription_tz or "UTC"
            try:
                tz = pytz.timezone(user_tz)
            except:
                tz = pytz.UTC
            
            now_user_tz = datetime.now(tz)
            current_time = now_user_tz.time()
            today = now_user_tz.date()
            
            # Отладка: логируем проверку времени
            logger.debug(f"Daily horoscope check: user={profile.user_id}, tz={user_tz}, "
                        f"current={current_time.strftime('%H:%M')}, "
                        f"target={send_time.strftime('%H:%M')}, "
                        f"match={send_time.hour == current_time.hour and send_time.minute == current_time.minute}")
            
            # Проверяем, совпадает ли час и минута
            if send_time.hour != current_time.hour or send_time.minute != current_time.minute:
                continue
            
            # Проверяем, не отправляли ли уже сегодня
            async with get_db() as session:
                existing = await session.execute(
                    select(DailyHoroscopeLog).where(
                        and_(
                            DailyHoroscopeLog.user_id == profile.user_id,
                            DailyHoroscopeLog.send_date == today,
                            DailyHoroscopeLog.status == "sent",
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    continue
            
            # Проверяем триал или баланс
            is_trial = profile.trial_days_left > 0
            
            if not is_trial:
                # Платная отправка - проверяем баланс
                config = await core_api.get_service_config("astrology")
                prices = config.get("prices", {})
                price = Decimal(str(prices.get("daily_horoscope", 2)))
                balance = await core_api.get_balance(profile.user_id)
                
                if balance < price:
                    # Недостаточно средств - уведомляем
                    await _notify_insufficient_balance(bot, profile, price, balance)
                    continue
            
            # Генерируем гороскоп
            chart_data = ChartData.from_dict(profile.chart_data or {})
            today_str = today.strftime("%d.%m.%Y")
            
            try:
                interpretation, tokens = await interpreter.interpret_daily(chart_data, today_str)
                
                # Рендерим в HTML
                from .renderer import renderer
                from .config import get_sign_name, get_sign_emoji
                
                html_path = renderer.render_daily(
                    content=interpretation,
                    sun_sign=get_sign_name(chart_data.sun_sign),
                    sun_emoji=get_sign_emoji(chart_data.sun_sign),
                    user_id=profile.user_id,
                    person_name=profile.name
                )
                
                # Получаем пользователя
                from core.database.models import User
                async with get_db() as session:
                    user_result = await session.execute(
                        select(User).where(User.id == profile.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                
                if user and user.telegram_id:
                    # Списываем средства если не триал
                    if not is_trial:
                        await core_api.deduct_balance(profile.user_id, price, "Ежедневный гороскоп")
                    
                    # Отправляем HTML документ
                    if html_path:
                        await bot.send_document(
                            chat_id=user.telegram_id,
                            document=open(html_path, 'rb'),
                            caption=f"☀️ <b>Ваш гороскоп на {today_str}</b>",
                            parse_mode="HTML"
                        )
                    else:
                        # Fallback на текст если HTML не создался
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=f"☀️ <b>Ваш гороскоп на {today_str}</b>\n\n{interpretation}",
                            parse_mode="HTML"
                        )
                    
                    # Уменьшаем счетчик триала
                    if is_trial:
                        async with get_db() as session:
                            result = await session.execute(
                                select(UserAstrologyProfile).where(UserAstrologyProfile.id == profile.id)
                            )
                            prof = result.scalar_one_or_none()
                            if prof:
                                prof.trial_days_left -= 1
                                await session.commit()
                                
                                # Уведомляем об окончании триала
                                if prof.trial_days_left == 0:
                                    await _notify_trial_ended(bot, prof, price)
                
                # Логируем успех
                async with get_db() as session:
                    log = DailyHoroscopeLog(
                        user_id=profile.user_id,
                        profile_id=profile.id,
                        send_date=today,
                        scheduled_time=send_time,
                        scheduled_tz=profile.subscription_tz or "UTC",
                        status="sent",
                        sent_at=datetime.now(),
                        horoscope_text=interpretation,
                    )
                    session.add(log)
                    await session.commit()
                
                logger.info(f"Daily horoscope sent to user {profile.user_id}")
                
            except Exception as e:
                # Логируем ошибку
                async with get_db() as session:
                    log = DailyHoroscopeLog(
                        user_id=profile.user_id,
                        profile_id=profile.id,
                        send_date=today,
                        scheduled_time=send_time,
                        scheduled_tz=profile.subscription_tz or "UTC",
                        status="failed",
                        error=str(e),
                    )
                    session.add(log)
                    await session.commit()
                
                logger.error(f"Failed to send daily horoscope to user {profile.user_id}: {e}")
                
        except Exception as e:
            logger.exception(f"Error processing daily horoscope for user {profile.user_id}: {e}")


async def check_subscription_renewals(bot, core_api):
    """
    Автопродление подписок.
    Вызывается каждый час.
    """
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    
    async with get_db() as session:
        # Находим подписки, которые заканчиваются сегодня
        result = await session.execute(
            select(UserAstrologyProfile).where(
                and_(
                    UserAstrologyProfile.subscription_until != None,
                    UserAstrologyProfile.subscription_until <= tomorrow,
                    UserAstrologyProfile.subscription_until > now,
                    UserAstrologyProfile.subscription_auto_renew == True,
                )
            )
        )
        profiles = list(result.scalars().all())
    
    for profile in profiles:
        try:
            plan = profile.subscription_plan
            if not plan or plan not in SUBSCRIPTION_PLANS:
                continue
            
            plan_data = SUBSCRIPTION_PLANS[plan]
            price_key = plan_data["price_key"]
            
            # Получаем цену
            config = await core_api.get_service_config("astrology")
            prices = config.get("prices", {})
            key = price_key.replace("price_", "")
            price = Decimal(str(prices.get(key, DEFAULT_PRICES.get(price_key, 0))))
            
            # Проверяем баланс
            balance = await core_api.get_balance(profile.user_id)
            
            if balance >= price:
                # Списываем и продлеваем
                await core_api.deduct_balance(profile.user_id, price, f"Автопродление подписки: {plan}")
                
                async with get_db() as session:
                    result = await session.execute(
                        select(UserAstrologyProfile).where(UserAstrologyProfile.id == profile.id)
                    )
                    prof = result.scalar_one_or_none()
                    if prof:
                        prof.subscription_until = prof.subscription_until + timedelta(days=plan_data["days"])
                        prof.subscription_notified = False
                        await session.commit()
                
                # Уведомляем пользователя
                from core.database.models import User
                async with get_db() as session:
                    user_result = await session.execute(
                        select(User).where(User.id == profile.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                
                if user and user.telegram_id:
                    new_until = (profile.subscription_until + timedelta(days=plan_data["days"])).strftime("%d.%m.%Y")
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=f"✅ Подписка продлена!\n\nСписано: {price} GTON\nНовый период: до {new_until}",
                        parse_mode="HTML"
                    )
                
                logger.info(f"Subscription renewed for user {profile.user_id}")
                
            else:
                # Недостаточно средств - уведомляем
                if not profile.subscription_notified:
                    from core.database.models import User
                    async with get_db() as session:
                        user_result = await session.execute(
                            select(User).where(User.id == profile.user_id)
                        )
                        user = user_result.scalar_one_or_none()
                    
                    if user and user.telegram_id:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=f"⚠️ Не удалось продлить подписку\n\nНа балансе недостаточно средств.\nНужно: {price} GTON\nБаланс: {balance} GTON\n\nПополните баланс, чтобы продолжить получать ежедневные гороскопы.",
                            parse_mode="HTML"
                        )
                    
                    # Отмечаем, что уведомили
                    async with get_db() as session:
                        result = await session.execute(
                            select(UserAstrologyProfile).where(UserAstrologyProfile.id == profile.id)
                        )
                        prof = result.scalar_one_or_none()
                        if prof:
                            prof.subscription_notified = True
                            await session.commit()
                    
                    logger.info(f"Subscription renewal failed for user {profile.user_id} - insufficient balance")
                    
        except Exception as e:
            logger.exception(f"Error processing subscription renewal for user {profile.user_id}: {e}")


async def send_expiration_reminders(bot, core_api):
    """
    Уведомления об окончании подписки (за день).
    Вызывается раз в день.
    """
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    day_after = now + timedelta(days=2)
    
    async with get_db() as session:
        # Находим подписки, которые заканчиваются завтра
        result = await session.execute(
            select(UserAstrologyProfile).where(
                and_(
                    UserAstrologyProfile.subscription_until != None,
                    UserAstrologyProfile.subscription_until > tomorrow,
                    UserAstrologyProfile.subscription_until <= day_after,
                    UserAstrologyProfile.subscription_notified == False,
                )
            )
        )
        profiles = list(result.scalars().all())
    
    for profile in profiles:
        try:
            plan = profile.subscription_plan
            if not plan or plan not in SUBSCRIPTION_PLANS:
                continue
            
            plan_data = SUBSCRIPTION_PLANS[plan]
            price_key = plan_data["price_key"]
            
            # Получаем цену
            config = await core_api.get_service_config("astrology")
            prices = config.get("prices", {})
            key = price_key.replace("price_", "")
            price = Decimal(str(prices.get(key, DEFAULT_PRICES.get(price_key, 0))))
            
            # Проверяем баланс
            balance = await core_api.get_balance(profile.user_id)
            has_balance = balance >= price
            
            from core.database.models import User
            async with get_db() as session:
                user_result = await session.execute(
                    select(User).where(User.id == profile.user_id)
                )
                user = user_result.scalar_one_or_none()
            
            if user and user.telegram_id:
                status = "✅" if has_balance else "⚠️ Недостаточно"
                auto_text = "Подписка будет продлена автоматически." if profile.subscription_auto_renew else ""
                
                text = f"🔮 Напоминание\n\n"
                text += f"Ваша подписка на ежедневный гороскоп заканчивается завтра.\n\n"
                text += f"Баланс: {balance} GTON {status}\n"
                text += auto_text
                
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    parse_mode="HTML"
                )
            
            # Отмечаем, что уведомили
            async with get_db() as session:
                result = await session.execute(
                    select(UserAstrologyProfile).where(UserAstrologyProfile.id == profile.id)
                )
                prof = result.scalar_one_or_none()
                if prof:
                    prof.subscription_notified = True
                    await session.commit()
            
            logger.info(f"Expiration reminder sent to user {profile.user_id}")
            
        except Exception as e:
            logger.exception(f"Error sending expiration reminder to user {profile.user_id}: {e}")


async def _notify_trial_ended(bot, profile: UserAstrologyProfile, daily_price: Decimal):
    """Уведомление об окончании триального периода"""
    try:
        from core.database.models import User
        from core.database import get_db
        
        async with get_db() as session:
            user_result = await session.execute(
                select(User).where(User.id == profile.user_id)
            )
            user = user_result.scalar_one_or_none()
        
        if user and user.telegram_id:
            text = f"🎁 <b>Пробный период закончен!</b>\n\n"
            text += f"Вы получили 4 бесплатных гороскопа.\n"
            text += f"Теперь ежедневный гороскоп стоит {daily_price} GTON.\n\n"
            text += f"Подписка активна и продолжит работать автоматически."
            
            await bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                parse_mode="HTML"
            )
            
            logger.info(f"Trial ended notification sent to user {profile.user_id}")
    except Exception as e:
        logger.error(f"Failed to send trial ended notification to user {profile.user_id}: {e}")


async def _notify_insufficient_balance(bot, profile: UserAstrologyProfile, price: Decimal, balance: Decimal):
    """Уведомление о недостатке средств для ежедневного гороскопа"""
    try:
        from core.database.models import User
        from core.database import get_db
        
        async with get_db() as session:
            user_result = await session.execute(
                select(User).where(User.id == profile.user_id)
            )
            user = user_result.scalar_one_or_none()
        
        if user and user.telegram_id:
            text = f"⚠️ <b>Недостаточно средств для гороскопа</b>\n\n"
            text += f"Сегодняшний гороскоп не отправлен.\n"
            text += f"Нужно: {price} GTON\n"
            text += f"Баланс: {balance} GTON\n\n"
            text += f"Пополните баланс, чтобы продолжить получать гороскопы."
            
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Пополнить баланс", callback_data="top_up")],
                [InlineKeyboardButton("❌ Отключить подписку", callback_data="service:astrology:daily_toggle")],
            ])
            
            await bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            logger.info(f"Insufficient balance notification sent to user {profile.user_id}")
    except Exception as e:
        logger.error(f"Failed to send insufficient balance notification to user {profile.user_id}: {e}")
