import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'security_v2_3.db')

def check_nulls():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Check for NULLs in nullable=False columns of asset_log
        columns_to_check = [
            "full_name", "employee_code", "asset_description", "quantity"
        ]
        
        print("Checking for NULL values in required columns of 'asset_log'...")
        for col in columns_to_check:
            cursor.execute(f"SELECT count(*) FROM asset_log WHERE {col} IS NULL")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"⚠ WARNING: Column '{col}' has {count} NULL values!")
                # Fix it
                print(f"  -> Fixing '{col}'...")
                default_val = "''" if col != "quantity" else "1"
                cursor.execute(f"UPDATE asset_log SET {col} = {default_val} WHERE {col} IS NULL")
                print(f"  -> Fixed.")
            else:
                print(f"✓ Column '{col}' has no NULL values.")

        # Check for NULLs in users table
        print("\nChecking for NULL values in required columns of 'users'...")
        user_cols = ["username", "password_hash", "full_name", "role"]
        for col in user_cols:
            cursor.execute(f"SELECT count(*) FROM users WHERE {col} IS NULL")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"⚠ WARNING: Column '{col}' has {count} NULL values!")
                # Fix it
                print(f"  -> Fixing '{col}'...")
                cursor.execute(f"UPDATE users SET {col} = '' WHERE {col} IS NULL")
                print(f"  -> Fixed.")
            else:
                print(f"✓ Column '{col}' has no NULL values.")
                
        conn.commit()
        print("\nCheck complete.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_nulls()
