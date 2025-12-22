"""
Test GTON rates and conversion
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import db_manager
from core.payments.converter import currency_converter
from core.payments.rates import rates_manager


async def test_rates():
    await db_manager.init()
    
    print("=" * 60)
    print("GTON CONVERSION TEST")
    print("=" * 60)
    print()
    
    # Get all rates
    rates = await rates_manager.get_all_rates()
    print("Current rates from DB:")
    for k, v in rates.items():
        print(f"  {k}: {v}")
    print()
    
    # Calculate 1 GTON in various currencies
    gton_rates = await currency_converter.get_gton_rates()
    print("1 GTON equals:")
    for currency, rate in gton_rates.items():
        print(f"  {rate} {currency}")
    print()
    
    # Conversion chain explanation
    gton_ton = rates.get("GTON_TON", Decimal("1.53"))
    ton_usd = rates.get("TON_USD", Decimal("0"))
    usd_rub = rates.get("USD_RUB", Decimal("0"))
    
    print("Conversion chain:")
    print(f"  1 GTON = {gton_ton} TON (from settings)")
    print(f"  1 TON = {ton_usd} USD (from CoinGecko)")
    print(f"  1 USD = {usd_rub} RUB (from ExchangeRate API)")
    print()
    
    gton_rub = gton_ton * ton_usd * usd_rub
    print(f"  => 1 GTON = {gton_ton} * {ton_usd} * {usd_rub} = {gton_rub:.2f} RUB")
    print()
    
    # Test conversion: 1000 RUB -> GTON
    print("-" * 60)
    result = await currency_converter.convert_to_gton(Decimal("1000"), "RUB")
    if result.success:
        print(f"1000 RUB -> {result.gton_amount} GTON")
        print(f"  Step 1: 1000 RUB / {result.rate_currency_usd} = {result.usd_amount} USD")
        print(f"  Step 2: {result.usd_amount} USD / {result.rate_ton_usd} = {result.ton_amount} TON")
        print(f"  Step 3: {result.ton_amount} TON / {result.rate_gton_ton} = {result.gton_amount} GTON")
    else:
        print(f"Error: {result.error}")
    print()
    
    # Test conversion: 10 GTON -> RUB
    print("-" * 60)
    rub = await currency_converter.convert_from_gton(Decimal("10"), "RUB")
    print(f"10 GTON -> {rub} RUB")
    print()
    
    # Format with fiat
    print("-" * 60)
    formatted = await currency_converter.format_gton_with_fiat(Decimal("10.5"), "RUB")
    print(f"Formatted balance: {formatted}")
    print()
    
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(test_rates())
