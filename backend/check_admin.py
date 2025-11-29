import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'security_v2_3.db')

def check_admin():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE username='admin'")
        user = cursor.fetchone()
        if user:
            print("User 'admin' exists.")
            print(f"Data: {user}")
        else:
            print("User 'admin' DOES NOT exist.")
            
        # Also check table info
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\nColumns in 'users' table:")
        for col in columns:
            print(col)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_admin()
