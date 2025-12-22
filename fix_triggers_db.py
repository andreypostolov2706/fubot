"""Fix broadcast_triggers table - create with all columns"""
import sqlite3

conn = sqlite3.connect('data/core.db')
cursor = conn.cursor()

# Drop and recreate broadcast_triggers table
cursor.execute("DROP TABLE IF EXISTS broadcast_triggers")
print("Dropped old broadcast_triggers table")

# Create broadcast_triggers table
cursor.execute("""
CREATE TABLE broadcast_triggers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    conditions JSON DEFAULT '{}',
    send_start_hour INTEGER DEFAULT 9,
    send_end_hour INTEGER DEFAULT 21,
    delay_minutes INTEGER DEFAULT 0,
    repeat_interval_days INTEGER DEFAULT 0,
    max_sends_per_user INTEGER DEFAULT 1,
    cooldown_hours INTEGER DEFAULT 24,
    text TEXT NOT NULL,
    parse_mode VARCHAR(10) DEFAULT 'HTML',
    media_type VARCHAR(20),
    media_file_id VARCHAR(255),
    buttons JSON,
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_clicked INTEGER DEFAULT 0,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_run_at DATETIME,
    FOREIGN KEY (created_by) REFERENCES users(id)
)
""")
print("Created broadcast_triggers table")

# Create trigger_send_logs table
cursor.execute("""
CREATE TABLE IF NOT EXISTS trigger_send_logs (
    id INTEGER PRIMARY KEY,
    trigger_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    send_count INTEGER DEFAULT 1,
    first_sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trigger_id) REFERENCES broadcast_triggers(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
""")
print("Created trigger_send_logs table")

conn.commit()
conn.close()
print("Done!")
