"""
Exchange Rates Background Task

Updates exchange rates periodically.
"""
import asyncio
from datetime import datetime
from loguru import logger


async def update_rates_task():
    """
    Background task to update exchange rates.
    
    - Fiat rates: once per day
    - Crypto rates: every 10 minutes
    """
    from core.payments.rates import rates_manager
    from core.database import get_db
    from core.database.models import Setting
    from sqlalchemy import select
    
    logger.info("Exchange rates updater started")
    
    last_fiat_update = None
    last_crypto_update = None
    
    while True:
        try:
            now = datetime.utcnow()
            
            # Get TTLs from settings
            async with get_db() as session:
                fiat_ttl_result = await session.execute(
                    select(Setting).where(Setting.key == "payments.fiat_rates_ttl")
                )
                fiat_setting = fiat_ttl_result.scalar_one_or_none()
                fiat_ttl = int(fiat_setting.value) if fiat_setting else 86400
                
                crypto_ttl_result = await session.execute(
                    select(Setting).where(Setting.key == "payments.crypto_rates_ttl")
                )
                crypto_setting = crypto_ttl_result.scalar_one_or_none()
                crypto_ttl = int(crypto_setting.value) if crypto_setting else 600
            
            # Update fiat rates (daily)
            if last_fiat_update is None or (now - last_fiat_update).total_seconds() >= fiat_ttl:
                try:
                    await rates_manager._update_fiat_rates()
                    last_fiat_update = now
                    logger.info("Fiat exchange rates updated")
                except Exception as e:
                    logger.error(f"Failed to update fiat rates: {e}")
            
            # Update crypto rates (every 10 minutes)
            if last_crypto_update is None or (now - last_crypto_update).total_seconds() >= crypto_ttl:
                try:
                    await rates_manager._update_crypto_rates()
                    last_crypto_update = now
                    logger.info("Crypto exchange rates updated")
                except Exception as e:
                    logger.error(f"Failed to update crypto rates: {e}")
            
        except Exception as e:
            logger.error(f"Error in rates update task: {e}")
        
        # Check every minute
        await asyncio.sleep(60)


async def init_rates():
    """
    Initialize exchange rates on startup.
    Called once during application startup.
    """
    from core.payments.rates import rates_manager
    
    logger.info("Initializing exchange rates...")
    
    try:
        success = await rates_manager.update_all_rates()
        if success:
            logger.info("Exchange rates initialized successfully")
        else:
            logger.warning("Some exchange rates failed to initialize")
    except Exception as e:
        logger.error(f"Failed to initialize exchange rates: {e}")
