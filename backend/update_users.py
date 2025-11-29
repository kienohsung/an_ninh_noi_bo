import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'security_v2_3.db')

def update_user_departments():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        print("Đang cập nhật bộ phận cho users...")
        
        # Cập nhật department từ full_name (nếu có dạng "BỘ PHẬN - TÊN")
        cursor.execute("""
            UPDATE users 
            SET department = TRIM(SUBSTR(full_name, 1, INSTR(full_name, '-') - 1))
            WHERE full_name LIKE '%-%' AND (department = '' OR department IS NULL)
        """)
        
        updated = cursor.rowcount
        conn.commit()
        
        print(f"✓ Đã cập nhật {updated} user(s).")
        
        # Hiển thị kết quả
        print("\n=== Danh sách Users ===")
        cursor.execute("SELECT id, username, full_name, department, role FROM users")
        for row in cursor.fetchall():
            print(f"ID: {row[0]} | User: {row[1]} | Name: {row[2]} | Dept: {row[3] or 'N/A'} | Role: {row[4]}")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_user_departments()