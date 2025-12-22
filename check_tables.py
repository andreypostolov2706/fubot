import sqlite3
conn = sqlite3.connect('data/fubot.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print([r[0] for r in c.fetchall()])
conn.close()
