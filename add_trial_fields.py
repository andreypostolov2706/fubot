"""
Migration: Add trial fields to astrology_profiles table
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "bot.db"


def add_trial_fields():
    """Add trial_days_left and trial_started_at columns to astrology_profiles"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(astrology_profiles)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add trial_days_left if not exists
        if "trial_days_left" not in columns:
            print("Adding trial_days_left column...")
            cursor.execute("""
                ALTER TABLE astrology_profiles 
                ADD COLUMN trial_days_left INTEGER DEFAULT 4
            """)
            print("✓ trial_days_left column added")
        else:
            print("✓ trial_days_left column already exists")
        
        # Add trial_started_at if not exists
        if "trial_started_at" not in columns:
            print("Adding trial_started_at column...")
            cursor.execute("""
                ALTER TABLE astrology_profiles 
                ADD COLUMN trial_started_at DATETIME
            """)
            print("✓ trial_started_at column added")
        else:
            print("✓ trial_started_at column already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    print("Starting migration: add trial fields to astrology_profiles\n")
    add_trial_fields()
