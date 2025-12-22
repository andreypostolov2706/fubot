"""
Service Handler - Routes callbacks to services
"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from core.plugins.registry import service_registry
from core.plugins.base_service import CallbackContext
from core.plugins.core_api import CoreAPI
from core.platform.telegram.utils import (
    get_or_create_user,
    build_keyboard
)


async def service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle service callbacks"""
    query = update.callback_query
    logger.info(f"Service callback received: {query.data}")
    
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    
    # Parse callback: service:{service_id}:{action}:{params}
    parts = query.data.split(":")
    if len(parts) < 3:
        await query.answer("Invalid callback", show_alert=True)
        return
    
    service_id = parts[1]
    action = parts[2]
    params = {}
    
    # Парсим все дополнительные параметры
    if len(parts) > 3:
        params["id"] = parts[3]
        params["0"] = parts[3]
    if len(parts) > 4:
        params["1"] = parts[4]
    if len(parts) > 5:
        params["2"] = parts[5]
    
    # Get service
    service = service_registry.get(service_id)
    if not service:
        await query.answer("Service not found", show_alert=True)
        return
    
    await query.answer()
    
    # Build context
    ctx = CallbackContext(
        message_id=query.message.message_id,
        chat_id=query.message.chat_id,
        user_id=user_id
    )
    
    # Handle callback
    try:
        # Show loading if specified
        if hasattr(service, 'get_loading_text'):
            loading = service.get_loading_text(action, params)
            if loading:
                await query.edit_message_text(loading, parse_mode="HTML")
        
        response = await service.handle_callback(user_id, action, params, ctx)
        
        # Process response
        keyboard = None
        if response.keyboard:
            keyboard = build_keyboard(response.keyboard)
        
        # Split long messages (Telegram limit is 4096 chars)
        MAX_LENGTH = 4000
        text = response.text or ""
        logger.info(f"Sending response: action={response.action}, text_len={len(text)}")
        
        if response.action == "edit":
            if len(text) > MAX_LENGTH:
                logger.info(f"Splitting message into parts (>{MAX_LENGTH} chars)")
                # Send first part as edit, rest as new messages
                parts = [text[i:i+MAX_LENGTH] for i in range(0, len(text), MAX_LENGTH)]
                await query.edit_message_text(
                    parts[0],
                    parse_mode=response.parse_mode
                )
                for part in parts[1:-1]:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=part,
                        parse_mode=response.parse_mode
                    )
                # Last part with keyboard
                if len(parts) > 1:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=parts[-1],
                        reply_markup=keyboard,
                        parse_mode=response.parse_mode
                    )
            else:
                await query.edit_message_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode=response.parse_mode
                )
        elif response.action == "send":
            if len(text) > MAX_LENGTH:
                parts = [text[i:i+MAX_LENGTH] for i in range(0, len(text), MAX_LENGTH)]
                for part in parts[:-1]:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=part,
                        parse_mode=response.parse_mode
                    )
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=parts[-1],
                    reply_markup=keyboard,
                    parse_mode=response.parse_mode
                )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=response.parse_mode
                )
        elif response.action == "answer":
            await query.answer(response.text, show_alert=response.show_alert)
        
        # Send media if specified
        if response.media_path:
            from pathlib import Path
            media_file = Path(response.media_path)
            if media_file.exists():
                with open(media_file, 'rb') as f:
                    if response.media_type == "photo" or media_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                        await context.bot.send_photo(
                            chat_id=query.message.chat_id,
                            photo=f,
                            caption=response.media_url  # Use media_url as caption if needed
                        )
                    else:
                        await context.bot.send_document(
                            chat_id=query.message.chat_id,
                            document=f,
                            caption=response.media_url
                        )
        
        # Handle state
        if response.set_state:
            api = CoreAPI(service_id)
            await api.set_user_state(user_id, response.set_state, response.state_data)
        elif response.clear_state:
            api = CoreAPI(service_id)
            await api.clear_user_state(user_id)
        
        # Handle redirect
        if response.redirect_to:
            if response.redirect_to == "main_menu":
                from .start import main_menu_callback
                await main_menu_callback(update, context)
            else:
                # Для других redirect создаём новый контекст
                from .router import callback_router
                # Сохраняем оригинальные данные и вызываем роутер с новыми
                original_data = query.data
                try:
                    # Используем object.__setattr__ для обхода ограничения
                    object.__setattr__(query, '_data', response.redirect_to)
                    await callback_router(update, context)
                finally:
                    object.__setattr__(query, '_data', original_data)
            
    except Exception as e:
        logger.error(f"Error handling service callback: {e}")
        await query.answer("Error occurred", show_alert=True)
