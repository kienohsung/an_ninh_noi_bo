import sqlite3
import os

# Đường dẫn đến file CSDL
DB_FILE = os.path.join(os.path.dirname(__file__), 'security_v2_3.db')

if not os.path.exists(DB_FILE):
    print(f"LỖI: Không tìm thấy file CSDL tại '{DB_FILE}'.")
    exit(1)

def migrate_full_fix():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"Đã kết nối thành công đến {DB_FILE}")

        # === 1. BẢNG asset_images ===
        print("\n=== KIỂM TRA BẢNG: asset_images ===")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    image_path VARCHAR(255) NOT NULL,
                    FOREIGN KEY (asset_id) REFERENCES asset_log(id) ON DELETE CASCADE
                )
            """)
            print("✓ Bảng 'asset_images' đã sẵn sàng.")
            
            # Index for asset_images
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_images_asset_id ON asset_images(asset_id)")
            print("✓ Index 'idx_asset_images_asset_id' đã sẵn sàng.")
            
        except Exception as e:
            print(f"⚠ Lỗi xử lý bảng 'asset_images': {e}")

        # === 2. BẢNG asset_log ===
        print("\n=== KIỂM TRA BẢNG: asset_log ===")
        
        # Danh sách các cột cần kiểm tra/thêm
        # (Tên cột, Kiểu dữ liệu, Giá trị mặc định cho câu lệnh ADD COLUMN)
        columns_to_check = [
            ("destination", "VARCHAR(255)", "DEFAULT ''"),
            ("description_reason", "TEXT", "DEFAULT ''"),
            ("asset_description", "TEXT", "DEFAULT ''"), # Quan trọng: Model yêu cầu NOT NULL
            ("employee_code", "VARCHAR(128)", "DEFAULT ''"), # Quan trọng: Model yêu cầu NOT NULL
            ("department", "VARCHAR(128)", "DEFAULT ''"),
            ("quantity", "INTEGER", "NOT NULL DEFAULT 1"),
            ("expected_return_date", "DATE", ""),
            ("status", "VARCHAR(16)", "DEFAULT 'pending_out'"),
            ("check_out_time", "DATETIME", ""),
            ("check_out_by_user_id", "INTEGER", ""),
            ("check_in_back_time", "DATETIME", ""),
            ("check_in_back_by_user_id", "INTEGER", ""),
            ("created_at", "DATETIME", ""),
            ("full_name", "VARCHAR(128)", "DEFAULT ''"),
            ("registered_by_user_id", "INTEGER", "")
        ]

        for col_name, col_type, col_default in columns_to_check:
            try:
                # Thử thêm cột. Nếu cột đã tồn tại, SQLite sẽ báo lỗi "duplicate column name"
                sql = f"ALTER TABLE asset_log ADD COLUMN {col_name} {col_type} {col_default}"
                cursor.execute(sql)
                print(f"✓ Đã thêm cột '{col_name}'.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"✓ Cột '{col_name}' đã tồn tại.")
                else:
                    print(f"⚠ Lỗi khi thêm cột '{col_name}': {e}")

        # === 3. BẢNG users (Check department) ===
        print("\n=== KIỂM TRA BẢNG: users ===")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN department VARCHAR(64) DEFAULT ''")
            print("✓ Đã thêm cột 'department' vào bảng users.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'department' đã tồn tại trong bảng users.")
            else:
                print(f"⚠ Lỗi khi thêm cột 'department': {e}")

        # === 4. BẢNG guests (Check estimated_datetime) ===
        print("\n=== KIỂM TRA BẢNG: guests ===")
        try:
            cursor.execute("ALTER TABLE guests ADD COLUMN estimated_datetime DATETIME")
            print("✓ Đã thêm cột 'estimated_datetime' vào bảng guests.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'estimated_datetime' đã tồn tại trong bảng guests.")
            else:
                print(f"⚠ Lỗi khi thêm cột 'estimated_datetime': {e}")

        conn.commit()
        print("\n" + "="*50)
        print("✓ SỬA LỖI DATABASE HOÀN TẤT!")
        print("="*50)

    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_full_fix()
