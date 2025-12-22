"""Fix settings with comma instead of dot"""
import sqlite3

conn = sqlite3.connect('data/core.db')

# Fix all settings with comma
fixes = [
    ('payments.fee_percent', '0.1'),
    ('payout.fee_percent', '0.2'),
    ('payments.min_deposit_gton', '0.1'),
]

for key, value in fixes:
    conn.execute('UPDATE settings SET value = ? WHERE key = ?', (value, key))
    print(f"Fixed {key} = {value}")

conn.commit()
print("\n✅ All settings fixed!")

# Verify
cursor = conn.execute('SELECT key, value FROM settings WHERE key LIKE ? OR key LIKE ?', ('%fee%', '%min_deposit%'))
print("\nCurrent values:")
for row in cursor:
    print(f"  {row[0]} = {row[1]}")

conn.close()
