"""
Exchange Rates Manager

Fetches and caches exchange rates from external APIs.
- Fiat rates: exchangerate-api.com (updated daily)
- Crypto rates: CoinGecko (updated every 10 minutes)
"""
from __future__ import annotations
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict
import aiohttp
from loguru import logger

from core.database import get_db


class RatesManager:
    """Manages exchange rates fetching and caching"""
    
    # API endpoints
    EXCHANGERATE_API_URL = "https://open.er-api.com/v6/latest/{base}"
    COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
    
    # Default TTLs (in seconds)
    FIAT_TTL = 86400  # 24 hours
    CRYPTO_TTL = 600  # 10 minutes
    
    def __init__(self):
        self._cache: Dict[str, dict] = {}
    
    async def get_rate(
        self, 
        base_currency: str, 
        quote_currency: str,
        use_cache: bool = True
    ) -> Optional[Decimal]:
        """
        Get exchange rate for currency pair.
        
        Args:
            base_currency: Base currency (e.g., USD)
            quote_currency: Quote currency (e.g., RUB)
            use_cache: Whether to use cached rates
            
        Returns:
            Rate as Decimal (1 base = rate quote), or None if not found
            
        Example:
            get_rate("USD", "RUB") -> 103.5 (1 USD = 103.5 RUB)
            get_rate("TON", "USD") -> 6.85 (1 TON = 6.85 USD)
        """
        base = base_currency.upper()
        quote = quote_currency.upper()
        
        # Same currency
        if base == quote:
            return Decimal("1.000000")
        
        # Stablecoins are 1:1 with USD
        stablecoins = {"USDT", "USDC", "DAI", "BUSD", "TUSD"}
        
        # USD to stablecoin or stablecoin to USD = 1:1
        if (base == "USD" and quote in stablecoins) or (base in stablecoins and quote == "USD"):
            return Decimal("1.000000")
        
        # Stablecoin to stablecoin = 1:1
        if base in stablecoins and quote in stablecoins:
            return Decimal("1.000000")
        
        # Check cache first
        if use_cache:
            cached = await self._get_cached_rate(base, quote)
            if cached is not None:
                return cached
        
        # Fetch from API
        rate = await self._fetch_rate(base, quote)
        
        if rate is not None:
            await self._save_rate(base, quote, rate)
        
        return rate
    
    async def get_all_rates(self) -> Dict[str, Decimal]:
        """
        Get all current rates needed for GTON conversion.
        
        Returns:
            {
                "USD_RUB": Decimal,
                "TON_USD": Decimal,
                "GTON_TON": Decimal,
            }
        """
        rates = {}
        
        # Fiat rate
        usd_rub = await self.get_rate("USD", "RUB")
        if usd_rub:
            rates["USD_RUB"] = usd_rub
        
        # Crypto rate
        ton_usd = await self.get_rate("TON", "USD")
        if ton_usd:
            rates["TON_USD"] = ton_usd
        
        # Internal rate (from settings)
        gton_ton = await self._get_gton_rate()
        rates["GTON_TON"] = gton_ton
        
        return rates
    
    async def update_all_rates(self) -> bool:
        """
        Force update all rates from APIs.
        Called by background task.
        
        Returns:
            True if all rates updated successfully
        """
        success = True
        
        # Update fiat rates
        try:
            await self._update_fiat_rates()
            logger.info("Fiat rates updated")
        except Exception as e:
            logger.error(f"Failed to update fiat rates: {e}")
            success = False
        
        # Update crypto rates
        try:
            await self._update_crypto_rates()
            logger.info("Crypto rates updated")
        except Exception as e:
            logger.error(f"Failed to update crypto rates: {e}")
            success = False
        
        return success
    
    async def _get_cached_rate(
        self, 
        base: str, 
        quote: str
    ) -> Optional[Decimal]:
        """Get rate from database cache"""
        from core.database.models import ExchangeRate
        from sqlalchemy import select, and_
        
        async with get_db() as session:
            result = await session.execute(
                select(ExchangeRate).where(
                    and_(
                        ExchangeRate.base_currency == base,
                        ExchangeRate.quote_currency == quote
                    )
                )
            )
            rate_record = result.scalar_one_or_none()
            
            if not rate_record:
                return None
            
            # Check TTL
            ttl = self.CRYPTO_TTL if base in ("TON", "BTC", "ETH") else self.FIAT_TTL
            
            # Get TTL from settings if available
            try:
                from core.database.models import Setting
                ttl_key = "payments.crypto_rates_ttl" if base in ("TON", "BTC", "ETH") else "payments.fiat_rates_ttl"
                ttl_result = await session.execute(
                    select(Setting).where(Setting.key == ttl_key)
                )
                ttl_setting = ttl_result.scalar_one_or_none()
                if ttl_setting:
                    ttl = int(ttl_setting.value)
            except Exception:
                pass
            
            if datetime.utcnow() - rate_record.updated_at > timedelta(seconds=ttl):
                return None  # Expired
            
            return Decimal(str(rate_record.rate))
    
    async def _save_rate(
        self, 
        base: str, 
        quote: str, 
        rate: Decimal,
        source: str = "api"
    ):
        """Save rate to database"""
        from core.database.models import ExchangeRate
        from sqlalchemy import select, and_
        
        async with get_db() as session:
            result = await session.execute(
                select(ExchangeRate).where(
                    and_(
                        ExchangeRate.base_currency == base,
                        ExchangeRate.quote_currency == quote
                    )
                )
            )
            rate_record = result.scalar_one_or_none()
            
            if rate_record:
                rate_record.rate = rate
                rate_record.source = source
                rate_record.updated_at = datetime.utcnow()
            else:
                rate_record = ExchangeRate(
                    base_currency=base,
                    quote_currency=quote,
                    rate=rate,
                    source=source
                )
                session.add(rate_record)
    
    async def _fetch_rate(
        self, 
        base: str, 
        quote: str
    ) -> Optional[Decimal]:
        """Fetch rate from appropriate API"""
        # Crypto currencies
        if base in ("TON", "BTC", "ETH"):
            return await self._fetch_crypto_rate(base, quote)
        
        # Fiat currencies
        return await self._fetch_fiat_rate(base, quote)
    
    async def _fetch_fiat_rate(
        self, 
        base: str, 
        quote: str
    ) -> Optional[Decimal]:
        """Fetch fiat rate from exchangerate-api"""
        try:
            url = self.EXCHANGERATE_API_URL.format(base=base)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"Exchangerate API error: {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    if data.get("result") != "success":
                        logger.error(f"Exchangerate API error: {data}")
                        return None
                    
                    rates = data.get("rates", {})
                    rate = rates.get(quote)
                    
                    if rate is None:
                        logger.error(f"Rate not found: {base}/{quote}")
                        return None
                    
                    return Decimal(str(rate)).quantize(
                        Decimal("0.000001"), 
                        rounding=ROUND_HALF_UP
                    )
                    
        except Exception as e:
            logger.error(f"Failed to fetch fiat rate {base}/{quote}: {e}")
            return None
    
    async def _fetch_crypto_rate(
        self, 
        base: str, 
        quote: str
    ) -> Optional[Decimal]:
        """Fetch crypto rate from CoinGecko"""
        try:
            # Map currency codes to CoinGecko IDs
            coin_ids = {
                "TON": "the-open-network",
                "BTC": "bitcoin",
                "ETH": "ethereum",
            }
            
            coin_id = coin_ids.get(base)
            if not coin_id:
                logger.error(f"Unknown crypto: {base}")
                return None
            
            params = {
                "ids": coin_id,
                "vs_currencies": quote.lower()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.COINGECKO_API_URL, 
                    params=params,
                    timeout=10
                ) as response:
                    if response.status != 200:
                        logger.error(f"CoinGecko API error: {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    rate = data.get(coin_id, {}).get(quote.lower())
                    
                    if rate is None:
                        logger.error(f"Rate not found: {base}/{quote}")
                        return None
                    
                    return Decimal(str(rate)).quantize(
                        Decimal("0.000001"), 
                        rounding=ROUND_HALF_UP
                    )
                    
        except Exception as e:
            logger.error(f"Failed to fetch crypto rate {base}/{quote}: {e}")
            return None
    
    async def _update_fiat_rates(self):
        """Update all fiat rates from USD"""
        currencies = ["RUB", "EUR", "GBP", "UAH", "KZT"]
        
        for currency in currencies:
            rate = await self._fetch_fiat_rate("USD", currency)
            if rate:
                await self._save_rate("USD", currency, rate, source="exchangerate")
    
    async def _update_crypto_rates(self):
        """Update crypto rates"""
        # TON/USD
        rate = await self._fetch_crypto_rate("TON", "USD")
        if rate:
            await self._save_rate("TON", "USD", rate, source="coingecko")
    
    async def _get_gton_rate(self) -> Decimal:
        """Get GTON/TON rate from settings"""
        from core.database.models import Setting
        from sqlalchemy import select
        
        async with get_db() as session:
            result = await session.execute(
                select(Setting).where(Setting.key == "payments.gton_ton_rate")
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                # Handle comma as decimal separator
                value = setting.value.replace(",", ".")
                return Decimal(value)
            
            return Decimal("1.530000")  # Default


# Global instance
rates_manager = RatesManager()
