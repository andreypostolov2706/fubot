"""
Message Handler
"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from core.database import get_db
from core.locales import t
from core.plugins.registry import service_registry
from core.plugins.base_service import MessageDTO, MessageContext
from core.plugins.core_api import CoreAPI
from core.platform.telegram.utils import (
    get_or_create_user,
    get_user_language,
    get_user_balance,
    build_keyboard
)
from core.platform.telegram.keyboards import main_menu_kb


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    telegram_user = update.effective_user
    user_id = await get_or_create_user(telegram_user.id, telegram_user)
    lang = await get_user_language(user_id)
    
    # Check if user is in any service state
    from core.database.models import UserService
    async with get_db() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(UserService).where(
                UserService.user_id == user_id,
                UserService.state.isnot(None)
            )
        )
        user_service = result.scalar_one_or_none()
    
    # Handle core states first
    if user_service and user_service.service_id == "core":
        state = user_service.state
        state_data = user_service.state_data or {}
        logger.info(f"Core state: {state}, data: {state_data}")
        
        if state == "waiting_promocode":
            from .promocode import handle_promocode_input
            await handle_promocode_input(update, user_id, lang)
            return
        
        elif state == "topup_custom_amount":
            from .topup import handle_custom_amount_message
            await handle_custom_amount_message(update, context)
            return
        
        # Admin states
        elif state == "admin_user_search":
            from core.platform.telegram.admin.users import handle_user_search
            await handle_user_search(update, user_id, lang)
            return
        
        elif state == "admin_balance_add":
            from core.platform.telegram.admin.users import handle_balance_input
            target_user_id = state_data.get("target_user_id")
            if target_user_id:
                await handle_balance_input(update, context, user_id, lang, "add", target_user_id)
            return
        
        elif state == "admin_balance_subtract":
            from core.platform.telegram.admin.users import handle_balance_input
            target_user_id = state_data.get("target_user_id")
            if target_user_id:
                await handle_balance_input(update, context, user_id, lang, "subtract", target_user_id)
            return
        
        elif state == "admin_send_message":
            from core.platform.telegram.admin.users import handle_send_message
            target_user_id = state_data.get("target_user_id")
            if target_user_id:
                await handle_send_message(update, context, user_id, lang, target_user_id)
            return
        
        elif state == "admin_moderation_search":
            from core.platform.telegram.admin.moderation import handle_moderation_search
            await handle_moderation_search(update, context, user_id, lang)
            return
        
        elif state == "admin_broadcast_text":
            from core.platform.telegram.admin.broadcast import handle_broadcast_text
            await handle_broadcast_text(update, context, user_id, lang)
            return
        
        elif state == "admin_broadcast_button":
            from core.platform.telegram.admin.broadcast import handle_broadcast_button
            broadcast_id = state_data.get("broadcast_id")
            if broadcast_id:
                await handle_broadcast_button(update, context, user_id, lang, broadcast_id)
            return
        
        elif state == "admin_broadcast_media":
            from core.platform.telegram.admin.broadcast import handle_broadcast_media
            broadcast_id = state_data.get("broadcast_id")
            if broadcast_id:
                await handle_broadcast_media(update, context, user_id, lang, broadcast_id)
            return
        
        elif state == "admin_broadcast_schedule":
            from core.platform.telegram.admin.broadcast import handle_broadcast_schedule
            broadcast_id = state_data.get("broadcast_id")
            if broadcast_id:
                await handle_broadcast_schedule(update, context, user_id, lang, broadcast_id)
            return
        
        elif state == "admin_trigger_name":
            from core.platform.telegram.admin.broadcast import handle_trigger_name
            trigger_type = state_data.get("trigger_type")
            if trigger_type:
                await handle_trigger_name(update, context, user_id, lang, trigger_type)
            return
        
        elif state == "admin_trigger_text":
            from core.platform.telegram.admin.broadcast import handle_trigger_text
            trigger_type = state_data.get("trigger_type")
            name = state_data.get("name")
            if trigger_type and name:
                await handle_trigger_text(update, context, user_id, lang, trigger_type, name)
            return
        
        # Trigger edit handlers
        elif state == "admin_trigger_edit_text":
            from core.platform.telegram.admin.broadcast import handle_trigger_edit_text
            trigger_id = state_data.get("trigger_id")
            if trigger_id:
                await handle_trigger_edit_text(update, context, user_id, lang, trigger_id)
            return
        
        elif state == "admin_trigger_edit_media":
            from core.platform.telegram.admin.broadcast import handle_trigger_edit_media
            trigger_id = state_data.get("trigger_id")
            if trigger_id:
                await handle_trigger_edit_media(update, context, user_id, lang, trigger_id)
            return
        
        elif state == "admin_trigger_edit_button":
            from core.platform.telegram.admin.broadcast import handle_trigger_edit_button
            trigger_id = state_data.get("trigger_id")
            if trigger_id:
                await handle_trigger_edit_button(update, context, user_id, lang, trigger_id)
            return
        
        elif state == "admin_trigger_edit_cond":
            from core.platform.telegram.admin.broadcast import handle_trigger_edit_cond
            trigger_id = state_data.get("trigger_id")
            param = state_data.get("param")
            if trigger_id and param:
                await handle_trigger_edit_cond(update, context, user_id, lang, trigger_id, param)
            return
        
        elif state == "admin_trigger_edit_behavior":
            from core.platform.telegram.admin.broadcast import handle_trigger_edit_behavior
            trigger_id = state_data.get("trigger_id")
            param = state_data.get("param")
            if trigger_id and param:
                await handle_trigger_edit_behavior(update, context, user_id, lang, trigger_id, param)
            return
        
        elif state == "admin_settings_edit":
            from core.platform.telegram.admin.settings import handle_settings_edit
            category = state_data.get("category")
            key = state_data.get("key")
            if category and key:
                await handle_settings_edit(update, context, user_id, lang, category, key)
            return
        
        # Promocode handlers
        elif state == "admin_promo_custom_code":
            from core.platform.telegram.admin.promocodes import handle_promo_custom_code
            promo_id = state_data.get("promo_id")
            if promo_id:
                await handle_promo_custom_code(update, context, user_id, lang, promo_id)
            return
        
        elif state == "admin_promo_bind_user":
            from core.platform.telegram.admin.promocodes import handle_promo_bind_user
            promo_id = state_data.get("promo_id")
            if promo_id:
                await handle_promo_bind_user(update, context, user_id, lang, promo_id)
            return
        
        elif state == "admin_promo_bind_partner":
            from core.platform.telegram.admin.promocodes import handle_promo_bind_partner
            promo_id = state_data.get("promo_id")
            if promo_id:
                await handle_promo_bind_partner(update, context, user_id, lang, promo_id)
            return
        
        # Partner payout states
        elif state == "partner_payout_card":
            from .partner import handle_payout_input
            await handle_payout_input(update, user_id, lang, "card", state_data)
            return
        
        elif state == "partner_payout_sbp":
            from .partner import handle_payout_input
            await handle_payout_input(update, user_id, lang, "sbp", state_data)
            return
        
        # Partner application questionnaire
        elif state == "partner_apply_audience":
            from .partner import partner_apply_socials
            audience = update.message.text.strip()
            await partner_apply_socials(update, user_id, lang, audience)
            return
        
        elif state == "partner_apply_socials":
            from .partner import partner_apply_submit
            socials = update.message.text.strip()
            await partner_apply_submit(update, user_id, lang, socials, context)
            return
        
        # Admin: custom partner percent
        elif state == "admin_partner_custom_percent":
            from core.platform.telegram.admin.partners import handle_partner_custom_percent
            partner_id = state_data.get("partner_id") if state_data else None
            if partner_id:
                await handle_partner_custom_percent(update, context, user_id, lang, partner_id)
            return
        
        # Stars: custom amount
        elif state == "stars_custom_amount":
            from .topup import handle_stars_custom_input
            await handle_stars_custom_input(update, context, user_id, lang)
            return
        
        # Admin: service config edit
        elif state == "admin_service_config_edit":
            from core.platform.telegram.admin.services import handle_service_config_input
            service_id = state_data.get("service_id")
            key = state_data.get("key")
            if service_id and key:
                await handle_service_config_input(update, context, user_id, lang, service_id, key)
            return
        
        # Admin: service price edit
        elif state == "admin_service_price_edit":
            from core.platform.telegram.admin.services import handle_service_price_input
            service_id = state_data.get("service_id")
            price_key = state_data.get("price_key")
            if service_id and price_key:
                await handle_service_price_input(update, context, user_id, lang, service_id, price_key)
            return
        
        # Global settings input
        elif state and state.startswith("global_settings:waiting:"):
            from .global_settings import handle_global_settings_input
            text = update.message.text.strip() if update.message.text else ""
            handled = await handle_global_settings_input(update, user_id, state, text)
            if handled:
                return
    
    if user_service and user_service.state:
        # Route to service
        logger.info(f"Routing message to service: {user_service.service_id}, state: {user_service.state}")
        service = service_registry.get(user_service.service_id)
        if service:
            # Собираем данные о сообщении
            photo_file_id = None
            if update.message.photo:
                # Берём самое большое фото (последнее в списке)
                photo_file_id = update.message.photo[-1].file_id
            
            msg = MessageDTO(
                text=update.message.text,
                photo_file_id=photo_file_id,
                caption=update.message.caption,
            )
            ctx = MessageContext(
                message_id=update.message.message_id,
                chat_id=update.message.chat_id,
                user_id=user_id
            )
            
            try:
                response = await service.handle_message(user_id, msg, ctx)
                logger.info(f"Service response: action={response.action}, text_len={len(response.text) if response.text else 0}")
                
                # Skip if action is ignore or text is empty
                if response.action == "ignore" or not response.text:
                    return
                
                keyboard = None
                if response.keyboard:
                    keyboard = build_keyboard(response.keyboard)
                
                # Send media if specified
                if response.media_path:
                    from pathlib import Path
                    media_file = Path(response.media_path)
                    if media_file.exists():
                        with open(media_file, 'rb') as f:
                            if response.media_type == "photo" or media_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                                await update.message.reply_photo(
                                    photo=f,
                                    caption=response.text,
                                    reply_markup=keyboard,
                                    parse_mode=response.parse_mode
                                )
                            else:
                                await update.message.reply_document(
                                    document=f,
                                    caption=response.text,
                                    reply_markup=keyboard,
                                    parse_mode=response.parse_mode
                                )
                    else:
                        logger.error(f"Media file not found: {response.media_path}")
                        await update.message.reply_text(
                            response.text,
                            reply_markup=keyboard,
                            parse_mode=response.parse_mode
                        )
                else:
                    await update.message.reply_text(
                        response.text,
                        reply_markup=keyboard,
                        parse_mode=response.parse_mode
                    )
                
                # Handle state
                if response.clear_state:
                    api = CoreAPI(user_service.service_id)
                    await api.clear_user_state(user_id)
                elif response.set_state:
                    api = CoreAPI(user_service.service_id)
                    await api.set_user_state(user_id, response.set_state, response.state_data)
                    
            except Exception as e:
                logger.error(f"Error handling service message: {e}")
            
            return
    
    # Default: show main menu
    lang = await get_user_language(user_id)
    balance = await get_user_balance(user_id)
    
    text = t(lang, "MAIN_MENU.title") + "\n\n"
    text += t(lang, "MAIN_MENU.balance", balance=balance)
    
    keyboard = await main_menu_kb(user_id, lang)
    
    await update.message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
