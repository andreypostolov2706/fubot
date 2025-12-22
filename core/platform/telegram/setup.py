"""
Telegram Setup - Register all handlers
"""
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)
from loguru import logger

from .handlers import start_command, help_command, message_handler
from .handlers.payments import handle_pre_checkout, handle_successful_payment
from .router import callback_router


def setup_handlers(application: Application):
    """Setup all handlers"""
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Payment handlers (Telegram Stars)
    application.add_handler(PreCheckoutQueryHandler(handle_pre_checkout))
    application.add_handler(MessageHandler(
        filters.SUCCESSFUL_PAYMENT,
        handle_successful_payment
    ))
    
    # Callback handler (single router)
    application.add_handler(CallbackQueryHandler(callback_router))
    
    # Message handler (text)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_handler
    ))
    
    # Message handler (media - photo, video, animation, document)
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.ANIMATION | filters.Document.ALL,
        message_handler
    ))
    
    logger.info("Telegram handlers setup complete")
