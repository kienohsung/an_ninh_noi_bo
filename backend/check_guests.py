import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'security_v2_3.db')

def check_guests():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(guests)")
        columns = cursor.fetchall()
        print("\nColumns in 'guests' table:")
        for col in columns:
            print(col)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_guests()
