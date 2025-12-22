"""
Migration: Recreate payouts table with new schema
WARNING: This will delete all existing payouts!
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from core.database import db_manager, get_db


async def migrate():
    await db_manager.init()
    
    async with get_db() as session:
        print("Recreating payouts table...")
        
        # Drop old table
        await session.execute(text("DROP TABLE IF EXISTS payouts"))
        print("  Dropped old payouts table")
        
        # Create new table with correct schema
        await session.execute(text("""
            CREATE TABLE payouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER NOT NULL REFERENCES partners(id) ON DELETE CASCADE,
                
                amount_gton DECIMAL(18,6) NOT NULL,
                fee_gton DECIMAL(18,6) DEFAULT 0,
                amount_fiat DECIMAL(12,2) NOT NULL,
                currency VARCHAR(3) DEFAULT 'RUB',
                gton_rate DECIMAL(12,4) NOT NULL,
                
                method VARCHAR(30) NOT NULL,
                details JSON NOT NULL,
                
                status VARCHAR(20) DEFAULT 'pending',
                
                processed_by INTEGER REFERENCES users(id),
                processed_at DATETIME,
                rejection_reason TEXT,
                
                user_comment TEXT,
                admin_comment TEXT,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """))
        print("  Created new payouts table")
        
        # Create index
        await session.execute(text("CREATE INDEX ix_payouts_partner_id ON payouts(partner_id)"))
        await session.execute(text("CREATE INDEX ix_payouts_status ON payouts(status)"))
        await session.execute(text("CREATE INDEX ix_payouts_created_at ON payouts(created_at)"))
        print("  Created indexes")
        
        print("\nMigration complete!")
    
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(migrate())
