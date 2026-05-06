import sqlite3
import os

try:
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'flaskdb.sqlite'))
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("ALTER TABLE users ADD COLUMN salario NUMERIC(10, 2) DEFAULT 0")
    conn.commit()
    print("Column 'salario' added successfully to 'users' table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column 'salario' already exists in 'users' table")
    else:
        print(f"OperationalError: {e}")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
