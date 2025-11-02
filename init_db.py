import sqlite3
conn = sqlite3.connect("fitness_app.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    plan TEXT DEFAULT 'free',
    expiry TEXT,
    payment_id TEXT
)
""")
conn.commit()
conn.close()
print("✅ Database created successfully!")
