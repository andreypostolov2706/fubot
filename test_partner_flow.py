"""
Тестовый скрипт для проверки партнёрской программы

Сценарий:
1. 748634393 — Партнёр
2. 1629061111 — Реферал партнёра 748634393
3. 6445832036 — Реферал пользователя 1629061111
"""
import asyncio
import sys
import os
from decimal import Decimal

# Fix encoding for Windows
os.system("chcp 65001 > nul")
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, r"c:\Users\Andrey\Desktop\Program\FuBot — Базовая версия")

from sqlalchemy import select
from core.database import get_db, db_manager
from core.database.models import User, Wallet, Partner, Referral, Transaction, Commission


async def get_user_by_tg(session, tg_id: int):
    result = await session.execute(select(User).where(User.telegram_id == tg_id))
    return result.scalar_one_or_none()


async def get_wallet(session, user_id: int):
    result = await session.execute(
        select(Wallet).where(Wallet.user_id == user_id, Wallet.wallet_type == "main")
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        wallet = Wallet(user_id=user_id, wallet_type="main", balance=Decimal("0"))
        session.add(wallet)
        await session.flush()
    return wallet


async def get_partner(session, user_id: int):
    result = await session.execute(select(Partner).where(Partner.user_id == user_id))
    return result.scalar_one_or_none()


async def print_status(title: str):
    print(f"\n{'='*60}\n[STATUS] {title}\n{'='*60}")
    
    async with get_db() as session:
        # Partner
        pu = await get_user_by_tg(session, 748634393)
        if pu:
            p = await get_partner(session, pu.id)
            w = await get_wallet(session, pu.id)
            print(f"\n[PARTNER] {pu.first_name} (TG: 748634393)")
            print(f"   Wallet: {w.balance:.4f} GTON")
            if p:
                print(f"   Partner balance: {p.balance:.4f} GTON, Total earned: {p.total_earned:.4f}")
        
        # Referral 1
        r1 = await get_user_by_tg(session, 1629061111)
        if r1:
            w = await get_wallet(session, r1.id)
            ref = (await session.execute(select(Referral).where(Referral.referred_id == r1.id))).scalar_one_or_none()
            print(f"\n[REF1] {r1.first_name} (TG: 1629061111)")
            print(f"   Balance: {w.balance:.4f} GTON")
            if ref:
                print(f"   Link: Referrer={ref.referrer_id}, Partner={ref.partner_id}, Spent={ref.total_payments:.4f}")
        
        # Referral 2
        r2 = await get_user_by_tg(session, 6445832036)
        if r2:
            w = await get_wallet(session, r2.id)
            ref = (await session.execute(select(Referral).where(Referral.referred_id == r2.id))).scalar_one_or_none()
            print(f"\n[REF2] {r2.first_name} (TG: 6445832036)")
            print(f"   Balance: {w.balance:.4f} GTON")
            if ref:
                print(f"   Link: Referrer={ref.referrer_id}, Partner={ref.partner_id}, Spent={ref.total_payments:.4f}")


async def setup_links():
    print("\n[SETUP] Setting up referral links...")
    async with get_db() as session:
        pu = await get_user_by_tg(session, 748634393)
        r1 = await get_user_by_tg(session, 1629061111)
        r2 = await get_user_by_tg(session, 6445832036)
        
        if not all([pu, r1, r2]):
            print(f"   ERROR: Not all users found: Partner={pu}, Ref1={r1}, Ref2={r2}")
            return False
        
        # Partner
        p = await get_partner(session, pu.id)
        if not p:
            p = Partner(user_id=pu.id, referral_code=f"p_{pu.id}", status="active",
                       level1_percent=Decimal("20"), balance=Decimal("0"), total_earned=Decimal("0"))
            session.add(p)
            await session.flush()
            print(f"   OK: Partner created")
        
        # Ref1 -> Partner
        ref1 = (await session.execute(select(Referral).where(Referral.referred_id == r1.id))).scalar_one_or_none()
        if not ref1:
            ref1 = Referral(referrer_id=pu.id, referred_id=r1.id, partner_id=p.id, total_payments=Decimal("0"), is_active=True)
            session.add(ref1)
        else:
            ref1.referrer_id = pu.id
            ref1.partner_id = p.id
        print(f"   OK: Ref1 -> Partner")
        
        # Ref2 -> Ref1
        ref2 = (await session.execute(select(Referral).where(Referral.referred_id == r2.id))).scalar_one_or_none()
        if not ref2:
            ref2 = Referral(referrer_id=r1.id, referred_id=r2.id, partner_id=None, total_payments=Decimal("0"), is_active=True)
            session.add(ref2)
        else:
            ref2.referrer_id = r1.id
        print(f"   OK: Ref2 -> Ref1")
        
        await session.commit()
    return True


async def top_up(tg_id: int, amount: Decimal):
    print(f"\n[TOP UP] TG:{tg_id} +{amount} GTON...")
    async with get_db() as session:
        u = await get_user_by_tg(session, tg_id)
        w = await get_wallet(session, u.id)
        balance_before = w.balance
        w.balance += amount
        session.add(Transaction(user_id=u.id, wallet_id=w.id, type="credit", direction="credit",
                               amount=amount, balance_before=balance_before, balance_after=w.balance, description="Test"))
        await session.commit()
        print(f"   OK! Balance: {w.balance:.4f} GTON")


async def spend(tg_id: int, amount: Decimal):
    """Трата с начислением комиссий"""
    print(f"\n[SPEND] TG:{tg_id} -{amount} GTON...")
    
    async with get_db() as session:
        u = await get_user_by_tg(session, tg_id)
        w = await get_wallet(session, u.id)
        
        if w.balance < amount:
            print(f"   ERROR: Not enough balance!")
            return
        
        balance_before = w.balance
        w.balance -= amount
        session.add(Transaction(user_id=u.id, wallet_id=w.id, type="debit", direction="debit",
                               amount=amount, balance_before=balance_before, balance_after=w.balance, description="Test spend"))
        
        # Обновляем total_payments в Referral
        ref = (await session.execute(select(Referral).where(Referral.referred_id == u.id))).scalar_one_or_none()
        if ref:
            ref.total_payments = (ref.total_payments or Decimal("0")) + amount
            ref.is_active = True
            
            # Начисляем комиссию рефереру (обычному)
            if ref.referrer_id and not ref.partner_id:
                referrer = (await session.execute(select(User).where(User.id == ref.referrer_id))).scalar_one_or_none()
                if referrer:
                    ref_wallet = await get_wallet(session, referrer.id)
                    commission = amount * Decimal("0.20")  # 20%
                    ref_balance_before = ref_wallet.balance
                    ref_wallet.balance += commission
                    session.add(Transaction(user_id=referrer.id, wallet_id=ref_wallet.id, type="referral_commission", direction="credit",
                                           amount=commission, balance_before=ref_balance_before, balance_after=ref_wallet.balance,
                                           description=f"Commission from {u.first_name}"))
                    print(f"   -> Commission to referrer {referrer.first_name}: {commission:.4f} GTON")
            
            # Начисляем комиссию партнёру
            if ref.partner_id:
                p = (await session.execute(select(Partner).where(Partner.id == ref.partner_id))).scalar_one_or_none()
                if p:
                    commission = amount * p.level1_percent / Decimal("100")
                    p.balance += commission
                    p.total_earned += commission
                    session.add(Commission(referrer_id=p.user_id, referred_id=u.id, source_amount=amount,
                                          commission_amount=commission, commission_percent=p.level1_percent, level=1))
                    print(f"   -> Commission to PARTNER: {commission:.4f} GTON ({p.level1_percent}%)")
        
        await session.commit()
        print(f"   OK! New balance: {w.balance:.4f} GTON")


async def main():
    print("=== PARTNER PROGRAM TEST ===\n")
    
    await db_manager.init()
    
    await print_status("INITIAL STATE")
    
    if not await setup_links():
        return
    
    await print_status("AFTER SETUP")
    
    # Top up Ref1 (partner's referral)
    await top_up(1629061111, Decimal("100"))
    
    # Ref1 spends - partner gets commission
    await spend(1629061111, Decimal("50"))
    
    await print_status("AFTER REF1 SPEND (50 GTON)")
    
    # Top up Ref2 (Ref1's referral)
    await top_up(6445832036, Decimal("100"))
    
    # Ref2 spends - Ref1 gets commission (regular referrer)
    await spend(6445832036, Decimal("30"))
    
    await print_status("AFTER REF2 SPEND (30 GTON)")
    
    print("\n=== TEST COMPLETED ===")


if __name__ == "__main__":
    asyncio.run(main())
