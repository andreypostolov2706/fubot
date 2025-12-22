"""
Telegram Bot Setup
"""
import asyncio
from telegram.ext import Application
from loguru import logger

from core.config import config
from .setup import setup_handlers


class TelegramBot:
    """Telegram bot wrapper"""
    
    def __init__(self):
        self.application: Application = None
        self._ban_check_task = None
    
    async def init(self):
        """Initialize bot"""
        self.application = (
            Application.builder()
            .token(config.TELEGRAM_BOT_TOKEN)
            .concurrent_updates(8)
            .build()
        )
        
        # Setup handlers
        setup_handlers(self.application)
        
        logger.info("Telegram bot initialized")
    
    async def start(self):
        """Start bot polling"""
        logger.info("Starting Telegram bot...")
        
        # Initialize application
        await self.application.initialize()
        await self.application.start()
        
        # Set bot instance for notifications
        from core.platform.telegram.admin.moderation import set_bot as set_moderation_bot
        from core.platform.telegram.admin.partners import set_bot as set_partners_bot
        from core.platform.telegram.admin.broadcast import set_bot as set_broadcast_bot
        set_moderation_bot(self.application.bot)
        set_partners_bot(self.application.bot)
        set_broadcast_bot(self.application.bot)
        
        # Start periodic ban check task
        self._ban_check_task = asyncio.create_task(self._check_expired_bans_loop())
        
        # Start polling
        await self.application.updater.start_polling(
            drop_pending_updates=True
        )
        
        logger.info("Telegram bot started")
    
    async def _check_expired_bans_loop(self):
        """Periodically check and unban users with expired bans"""
        from core.platform.telegram.admin.moderation import check_expired_bans
        
        while True:
            try:
                unbanned_count = await check_expired_bans()
                if unbanned_count > 0:
                    logger.info(f"Auto-unbanned {unbanned_count} users with expired bans")
            except Exception as e:
                logger.error(f"Error checking expired bans: {e}")
            
            # Check every hour
            await asyncio.sleep(3600)
    
    async def stop(self):
        """Stop bot"""
        logger.info("Stopping Telegram bot...")
        
        # Cancel ban check task
        if self._ban_check_task:
            self._ban_check_task.cancel()
            try:
                await self._ban_check_task
            except asyncio.CancelledError:
                pass
        
        if self.application.updater.running:
            await self.application.updater.stop()
        
        await self.application.stop()
        await self.application.shutdown()
        
        logger.info("Telegram bot stopped")


# Global instance
telegram_bot = TelegramBot()
