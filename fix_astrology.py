import sqlite3

conn = sqlite3.connect('data/core.db')
c = conn.cursor()

# Сбросить статус астрологии на active
c.execute("UPDATE services SET status = 'active', last_error = NULL, error_count = 0 WHERE id = 'astrology'")
conn.commit()

# Проверить
c.execute("SELECT id, name, status FROM services WHERE id = 'astrology'")
row = c.fetchone()
print(f"Service: {row[0]} - {row[1]} [{row[2]}]")

conn.close()
print("Done!")
