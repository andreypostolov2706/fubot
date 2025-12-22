import sqlite3

conn = sqlite3.connect('data/core.db')
c = conn.cursor()

c.execute("SELECT id, status, last_error FROM services WHERE id = 'astrology'")
row = c.fetchone()
print(f"ID: {row[0]}")
print(f"Status: {row[1]}")
print(f"Error: {row[2]}")

conn.close()
