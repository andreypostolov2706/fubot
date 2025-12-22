import sqlite3

conn = sqlite3.connect('data/core.db')
c = conn.cursor()

c.execute('''INSERT INTO broadcast_triggers 
    (name, trigger_type, is_active, conditions, text, created_by) 
    VALUES (?, ?, ?, ?, ?, ?)''', 
    ('Низкий баланс', 'low_balance', 0, 
     '{"balance_less_than": 100}', 
     'Привет, {name}! Твой баланс: {balance} руб. Пополни баланс, чтобы продолжить!', 
     1))

conn.commit()
print('Trigger added')
