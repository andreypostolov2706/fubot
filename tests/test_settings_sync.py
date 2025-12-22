"""
Test Settings Synchronization

Проверяет что настройки из БД правильно применяются в коде
"""
import asyncio
import sys
from decimal import Decimal

sys.path.insert(0, ".")


async def main():
    from core.database import db_manager, get_db
    from core.database.models import Setting
    from sqlalchemy import select
    
    await db_manager.init()
    
    print("=" * 60)
    print("Settings Sync Test")
    print("=" * 60)
    
    # 1. Check payout settings in DB
    print("\n=== Payout Settings in DB ===")
    async with get_db() as session:
        result = await session.execute(
            select(Setting).where(Setting.key.like("payout.%"))
        )
        settings = result.scalars().all()
        
        for s in settings:
            print(f"  {s.key} = {s.value} ({s.value_type})")
    
    # 2. Check what payout_service reads
    print("\n=== Payout Service Reads ===")
    try:
        from core.payout import payout_service
        
        min_gton = await payout_service.get_min_payout_gton()
        print(f"  get_min_payout_gton() = {min_gton}")
        
        fee = await payout_service.get_fee_percent()
        print(f"  get_fee_percent() = {fee}")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # 3. Check partner.py uses these values
    print("\n=== Partner Handler Uses ===")
    try:
        # Read partner_payout function to see what it uses
        from core.platform.telegram.handlers import partner
        import inspect
        
        source = inspect.getsource(partner.partner_payout)
        
        # Check if it reads from payout_service
        if "payout_service" in source:
            print("  partner_payout uses payout_service: YES")
        else:
            print("  partner_payout uses payout_service: NO (PROBLEM!)")
        
        if "get_min_payout" in source:
            print("  partner_payout calls get_min_payout: YES")
        else:
            print("  partner_payout calls get_min_payout: NO (may be hardcoded!)")
            
        # Find hardcoded values
        import re
        hardcoded = re.findall(r'min_payout\s*=\s*(\d+)', source)
        if hardcoded:
            print(f"  FOUND HARDCODED min_payout = {hardcoded}")
        
        hardcoded_decimal = re.findall(r'Decimal\(["\'](\d+)["\']', source)
        if hardcoded_decimal:
            print(f"  FOUND HARDCODED Decimal values: {hardcoded_decimal}")
            
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # 4. Check referral settings
    print("\n=== Referral Settings in DB ===")
    async with get_db() as session:
        result = await session.execute(
            select(Setting).where(Setting.key.like("referral.%"))
        )
        settings = result.scalars().all()
        
        for s in settings:
            print(f"  {s.key} = {s.value} ({s.value_type})")
    
    # 5. Check commission service
    print("\n=== Commission Service ===")
    try:
        from core.referral import commission_service
        import inspect
        
        source = inspect.getsource(commission_service.process_commission)
        
        if "get_setting" in source or "Setting" in source:
            print("  process_commission reads from DB: YES")
        else:
            print("  process_commission reads from DB: NO (may be hardcoded!)")
            
        # Find hardcoded percentages
        import re
        hardcoded = re.findall(r'percent\s*=\s*Decimal\(["\'](\d+)["\']', source)
        if hardcoded:
            print(f"  FOUND HARDCODED percent = {hardcoded}")
            
    except Exception as e:
        print(f"  ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
