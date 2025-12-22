"""
Migration: Add missing columns to partners and payouts tables
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from core.database import db_manager, get_db


async def add_column_if_missing(session, table: str, column: str, col_type: str):
    """Add column if it doesn't exist"""
    result = await session.execute(text(f"PRAGMA table_info({table})"))
    columns = [row[1] for row in result.fetchall()]
    
    if column not in columns:
        print(f"Adding {column} to {table}...")
        await session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
        print(f"  Done!")
    else:
        print(f"  {table}.{column} already exists")


async def migrate():
    await db_manager.init()
    
    async with get_db() as session:
        print("Migrating partners table...")
        await add_column_if_missing(session, "partners", "frozen_balance", "DECIMAL(18,6) DEFAULT 0")
        
        print("\nMigrating payouts table...")
        await add_column_if_missing(session, "payouts", "amount_gton", "DECIMAL(18,6) DEFAULT 0")
        await add_column_if_missing(session, "payouts", "fee_gton", "DECIMAL(18,6) DEFAULT 0")
        await add_column_if_missing(session, "payouts", "amount_fiat", "DECIMAL(12,2) DEFAULT 0")
        await add_column_if_missing(session, "payouts", "gton_rate", "DECIMAL(18,6) DEFAULT 0")
        await add_column_if_missing(session, "payouts", "currency", "VARCHAR(10) DEFAULT 'RUB'")
        
        # Fix old 'amount' column - make it have a default value
        print("\nFixing old 'amount' column in payouts...")
        try:
            # Check if amount column exists and update it
            result = await session.execute(text("PRAGMA table_info(payouts)"))
            columns = {row[1]: row for row in result.fetchall()}
            if "amount" in columns:
                # SQLite doesn't support ALTER COLUMN, so we set a default via UPDATE
                await session.execute(text("UPDATE payouts SET amount = 0 WHERE amount IS NULL"))
                print("  Fixed null values in amount column")
        except Exception as e:
            print(f"  Note: {e}")
        
        print("\nMigration complete!")
    
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(migrate())
