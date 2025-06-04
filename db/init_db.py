import sqlite3
import os

# Always write the database to the root folder
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "grant_tracker.db")

try:
    with sqlite3.connect(DB_PATH) as conn:
        with open(os.path.join(os.path.dirname(__file__), "schema.sql"), "r") as f:
            schema = f.read()
        conn.executescript(schema)
        conn.commit()
    print("✅ Database initialized successfully.")
except Exception as e:
    print(f"❌ Initialization failed: {e}")

