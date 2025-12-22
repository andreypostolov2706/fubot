"""
Currency Converter

Converts any currency to GTON and vice versa.
Chain: ANY → USD → TON → GTON
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict
from loguru import logger

from .rates import rates_manager


@dataclass
class ConversionResult:
    """Result of currency conversion"""
    success: bool
    gton_amount: Decimal = Decimal("0")
    
    # Intermediate values
    usd_amount: Decimal = Decimal("0")
    ton_amount: Decimal = Decimal("0")
    
    # Rates used
    rate_currency_usd: Optional[Decimal] = None  # e.g., 1 USD = 103.5 RUB
    rate_ton_usd: Optional[Decimal] = None       # e.g., 1 TON = 6.85 USD
    rate_gton_ton: Optional[Decimal] = None      # e.g., 1 GTON = 1.53 TON
    
    error: Optional[str] = None


class CurrencyConverter:
    """
    Converts currencies to/from GTON.
    
    Conversion chain:
    ANY → USD → TON → GTON
    
    Example:
        1000 RUB → 9.66 USD → 1.41 TON → 0.92 GTON
    """
    
    # Precision for GTON (6 decimal places)
    PRECISION = Decimal("0.000001")
    
    # Stablecoins (1:1 with USD)
    STABLECOINS = {"USDT", "USDC", "DAI", "BUSD", "TUSD"}
    
    # Crypto assets that need special handling
    CRYPTO_ASSETS = {"BTC", "ETH", "LTC", "BNB", "TRX", "DOGE", "TON"}
    
    async def convert_to_gton(
        self,
        amount: Decimal,
        currency: str,
        fee_percent: Decimal = Decimal("0")
    ) -> ConversionResult:
        """
        Convert any currency to GTON.
        
        Args:
            amount: Amount in source currency
            currency: Source currency code (RUB, USD, EUR, TON)
            fee_percent: Fee percentage to deduct (0-100)
            
        Returns:
            ConversionResult with GTON amount and rates used
        """
        currency = currency.upper()
        
        try:
            # Apply fee
            if fee_percent > 0:
                fee = amount * fee_percent / Decimal("100")
                amount = amount - fee
            
            # Get rates
            rates = await rates_manager.get_all_rates()
            
            rate_ton_usd = rates.get("TON_USD")
            rate_gton_ton = rates.get("GTON_TON")
            
            if not rate_ton_usd or not rate_gton_ton:
                return ConversionResult(
                    success=False,
                    error="Failed to get exchange rates"
                )
            
            # Step 1: Convert to USD
            if currency == "USD":
                usd_amount = amount
                rate_currency_usd = Decimal("1")
            elif currency in self.STABLECOINS:
                # Stablecoins are 1:1 with USD
                usd_amount = amount
                rate_currency_usd = Decimal("1")
            elif currency == "TON":
                # TON → USD → GTON (skip USD step)
                usd_amount = amount * rate_ton_usd
                rate_currency_usd = rate_ton_usd
            elif currency == "GTON":
                # Already GTON
                return ConversionResult(
                    success=True,
                    gton_amount=amount.quantize(self.PRECISION, ROUND_HALF_UP),
                    usd_amount=amount * rate_gton_ton * rate_ton_usd,
                    ton_amount=amount * rate_gton_ton,
                    rate_gton_ton=rate_gton_ton,
                    rate_ton_usd=rate_ton_usd
                )
            elif currency in self.CRYPTO_ASSETS:
                # Other crypto assets - get rate from DB or API
                rate_crypto_usd = await rates_manager.get_rate(currency, "USD")
                if not rate_crypto_usd:
                    # Try to use a default rate or return error
                    logger.warning(f"No rate for {currency}/USD, using fallback")
                    # Fallback rates (approximate)
                    fallback_rates = {
                        "BTC": Decimal("100000"),
                        "ETH": Decimal("3500"),
                        "LTC": Decimal("100"),
                        "BNB": Decimal("700"),
                        "TRX": Decimal("0.25"),
                        "DOGE": Decimal("0.4"),
                    }
                    rate_crypto_usd = fallback_rates.get(currency, Decimal("1"))
                usd_amount = amount * rate_crypto_usd
                rate_currency_usd = rate_crypto_usd
            else:
                # Fiat currency (RUB, EUR, etc.)
                rate_usd_currency = await rates_manager.get_rate("USD", currency)
                if not rate_usd_currency:
                    return ConversionResult(
                        success=False,
                        error=f"Failed to get USD/{currency} rate"
                    )
                # Convert: amount / rate = USD
                # e.g., 1000 RUB / 103.5 = 9.66 USD
                usd_amount = amount / rate_usd_currency
                rate_currency_usd = rate_usd_currency
            
            # Step 2: USD → TON
            # usd / ton_usd_rate = TON
            # e.g., 9.66 USD / 6.85 = 1.41 TON
            ton_amount = usd_amount / rate_ton_usd
            
            # Step 3: TON → GTON
            # ton / gton_ton_rate = GTON
            # e.g., 1.41 TON / 1.53 = 0.92 GTON
            gton_amount = ton_amount / rate_gton_ton
            
            return ConversionResult(
                success=True,
                gton_amount=gton_amount.quantize(self.PRECISION, ROUND_HALF_UP),
                usd_amount=usd_amount.quantize(self.PRECISION, ROUND_HALF_UP),
                ton_amount=ton_amount.quantize(self.PRECISION, ROUND_HALF_UP),
                rate_currency_usd=rate_currency_usd,
                rate_ton_usd=rate_ton_usd,
                rate_gton_ton=rate_gton_ton
            )
            
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return ConversionResult(
                success=False,
                error=str(e)
            )
    
    async def convert_from_gton(
        self,
        gton_amount: Decimal,
        target_currency: str
    ) -> Optional[Decimal]:
        """
        Convert GTON to target currency.
        
        Args:
            gton_amount: Amount in GTON
            target_currency: Target currency code
            
        Returns:
            Amount in target currency, or None on error
        """
        target = target_currency.upper()
        
        try:
            rates = await rates_manager.get_all_rates()
            
            rate_ton_usd = rates.get("TON_USD")
            rate_gton_ton = rates.get("GTON_TON")
            
            if not rate_ton_usd or not rate_gton_ton:
                return None
            
            # GTON → TON
            ton_amount = gton_amount * rate_gton_ton
            
            if target == "TON":
                return ton_amount.quantize(self.PRECISION, ROUND_HALF_UP)
            
            # TON → USD
            usd_amount = ton_amount * rate_ton_usd
            
            if target == "USD":
                return usd_amount.quantize(self.PRECISION, ROUND_HALF_UP)
            
            # USD → target fiat
            rate_usd_target = await rates_manager.get_rate("USD", target)
            if not rate_usd_target:
                return None
            
            target_amount = usd_amount * rate_usd_target
            return target_amount.quantize(self.PRECISION, ROUND_HALF_UP)
            
        except Exception as e:
            logger.error(f"Conversion from GTON error: {e}")
            return None
    
    async def gton_to_ton(self, gton_amount: Decimal) -> Decimal:
        """
        Convert GTON to TON.
        
        Args:
            gton_amount: Amount in GTON
            
        Returns:
            Amount in TON
        """
        try:
            rates = await rates_manager.get_all_rates()
            rate_gton_ton = rates.get("GTON_TON", Decimal("1.53"))
            
            # 1 GTON = rate_gton_ton TON
            ton_amount = gton_amount * rate_gton_ton
            return ton_amount.quantize(self.PRECISION, ROUND_HALF_UP)
        except Exception as e:
            logger.error(f"GTON to TON conversion error: {e}")
            return Decimal("0")
    
    async def get_gton_rates(self) -> Dict[str, Decimal]:
        """
        Get current GTON rates in various currencies.
        
        Returns:
            {
                "TON": Decimal,   # 1 GTON = X TON (how much TON for 1 GTON)
                "USD": Decimal,   # 1 GTON = X USD
                "RUB": Decimal,   # 1 GTON = X RUB
                "USDT": Decimal,  # 1 GTON = X USDT (same as USD)
                "BTC": Decimal,   # How much BTC for 1 GTON
                ...
            }
        """
        result = {}
        
        try:
            rates = await rates_manager.get_all_rates()
            
            rate_ton_usd = rates.get("TON_USD", Decimal("6"))
            rate_gton_ton = rates.get("GTON_TON", Decimal("1.53"))
            rate_usd_rub = rates.get("USD_RUB", Decimal("100"))
            
            # 1 GTON = X TON
            result["TON"] = rate_gton_ton
            
            # 1 GTON = X USD
            gton_usd = (rate_gton_ton * rate_ton_usd).quantize(
                self.PRECISION, ROUND_HALF_UP
            )
            result["USD"] = gton_usd
            
            # Stablecoins = USD
            result["USDT"] = gton_usd
            result["USDC"] = gton_usd
            
            # 1 GTON = X RUB
            result["RUB"] = (rate_gton_ton * rate_ton_usd * rate_usd_rub).quantize(
                self.PRECISION, ROUND_HALF_UP
            )
            
            # Other crypto - calculate based on their USD rates
            # These are approximate rates for display purposes
            crypto_usd_rates = {
                "BTC": Decimal("100000"),
                "ETH": Decimal("3500"),
                "LTC": Decimal("100"),
                "BNB": Decimal("700"),
                "TRX": Decimal("0.25"),
            }
            
            for crypto, crypto_rate in crypto_usd_rates.items():
                if crypto_rate > 0:
                    # 1 GTON = X crypto
                    # gton_usd / crypto_usd = how much crypto for 1 GTON
                    result[crypto] = (gton_usd / crypto_rate).quantize(
                        Decimal("0.00000001"), ROUND_HALF_UP
                    )
            
        except Exception as e:
            logger.error(f"Failed to get GTON rates: {e}")
        
        return result
    
    async def format_gton_with_fiat(
        self,
        gton_amount: Decimal,
        fiat_currency: str = "RUB"
    ) -> str:
        """
        Format GTON amount with fiat equivalent.
        
        Args:
            gton_amount: Amount in GTON
            fiat_currency: Fiat currency for equivalent
            
        Returns:
            Formatted string like "10.5 GTON (~1,085 ₽)"
        """
        fiat_amount = await self.convert_from_gton(gton_amount, fiat_currency)
        
        gton_str = f"{gton_amount:.6f}".rstrip('0').rstrip('.')
        
        if fiat_amount:
            if fiat_currency == "RUB":
                fiat_str = f"{fiat_amount:,.0f} ₽".replace(",", " ")
            elif fiat_currency == "USD":
                fiat_str = f"${fiat_amount:,.2f}"
            else:
                fiat_str = f"{fiat_amount:,.2f} {fiat_currency}"
            
            return f"{gton_str} GTON (~{fiat_str})"
        
        return f"{gton_str} GTON"


# Global instance
currency_converter = CurrencyConverter()
