"""Add Platega provider to database"""
import sqlite3

conn = sqlite3.connect('data/core.db')

conn.execute("""
    INSERT OR REPLACE INTO payment_providers 
    (id, name, icon, is_active, currencies, config, fee_percent, min_amount, max_amount, sort_order, description) 
    VALUES 
    ('platega', 'СБП (Platega)', '🏦', 1, '["RUB"]', '{}', 0, 50, 100000, 2, 'Оплата через СБП')
""")

conn.commit()
print("✅ Platega provider added!")

# Verify
cursor = conn.execute('SELECT id, name, is_active FROM payment_providers')
print("Providers:", list(cursor))

conn.close()
