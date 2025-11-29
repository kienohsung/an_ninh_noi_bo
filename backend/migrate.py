import sqlite3
import os

# Đường dẫn đến file CSDL (đảm bảo file này nằm trong thư mục 'backend')
# *** CHỈNH SỬA TÊN FILE NÀY NẾU CẦN ***
DB_FILE = os.path.join(os.path.dirname(__file__), 'security_v2_3.db')

if not os.path.exists(DB_FILE):
    print(f"LỖI: Không tìm thấy file CSDL tại '{DB_FILE}'.")
    print("Vui lòng kiểm tra lại tên file CSDL trong script 'migrate.py'.")
    exit(1)

def migrate_database_v3_fix():
    conn = None
    try:
        # 1. Kết nối đến CSDL
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"Đã kết nối thành công đến {DB_FILE}")

        # === XỬ LÝ BẢNG 'guests' ===
        print("\n=== BẢNG: guests ===")
        
        try:
            print("Đang thêm cột 'estimated_datetime' (DATETIME) vào bảng 'guests'...")
            cursor.execute("ALTER TABLE guests ADD COLUMN estimated_datetime DATETIME")
            print("✓ Thành công!")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'estimated_datetime' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # === XỬ LÝ BẢNG 'long_term_guests' ===
        print("\n=== BẢNG: long_term_guests ===")
        
        try:
            print("Đang thêm cột 'estimated_datetime' (DATETIME) vào bảng 'long_term_guests'...")
            cursor.execute("ALTER TABLE long_term_guests ADD COLUMN estimated_datetime DATETIME")
            print("✓ Thành công!")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'estimated_datetime' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # === XỬ LÝ BẢNG 'users' - THÊM CỘT 'department' ===
        print("\n=== BẢNG: users ===")
        
        try:
            print("Đang thêm cột 'department' (VARCHAR(64)) vào bảng 'users'...")
            cursor.execute("ALTER TABLE users ADD COLUMN department VARCHAR(64) DEFAULT ''")
            print("✓ Thành công!")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'department' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # === XỬ LÝ BẢNG 'asset_log' ===
        print("\n=== BẢNG: asset_log ===")
        
        # 1. TẠO BẢNG (NẾU CHƯA TỒN TẠI)
        try:
            print("Đang tạo bảng 'asset_log' (nếu chưa tồn tại)...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    registered_by_user_id INTEGER,
                    department VARCHAR(128) DEFAULT '',
                    description_reason TEXT DEFAULT '',
                    quantity INTEGER NOT NULL DEFAULT 1,
                    expected_return_date DATE,
                    status VARCHAR(16) DEFAULT 'pending_out',
                    check_out_time DATETIME,
                    check_out_by_user_id INTEGER,
                    check_in_back_time DATETIME,
                    check_in_back_by_user_id INTEGER,
                    created_at DATETIME,
                    FOREIGN KEY (registered_by_user_id) REFERENCES users(id),
                    FOREIGN KEY (check_out_by_user_id) REFERENCES users(id),
                    FOREIGN KEY (check_in_back_by_user_id) REFERENCES users(id)
                )
            """)
            print("✓ Lệnh CREATE IF NOT EXISTS đã chạy.")
        except Exception as e:
            print(f"⚠ Lỗi khi tạo bảng 'asset_log': {e}")
            # Tiếp tục chạy để thử ALTER
            pass

        # 2. THÊM CỘT 'destination' (ĐÂY LÀ PHẦN SỬA LỖI QUAN TRỌNG)
        try:
            print("Đang thêm cột 'destination' (VARCHAR(255)) vào bảng 'asset_log'...")
            cursor.execute("ALTER TABLE asset_log ADD COLUMN destination VARCHAR(255) DEFAULT ''")
            print("✓ Thành công! Đã thêm cột 'destination'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'destination' đã tồn tại. Bỏ qua.")
            else:
                print(f"⚠ Lỗi khi thêm cột 'destination': {e}. Có thể bảng chưa tồn tại?")
                raise e # Ném lỗi nếu đây là lỗi nghiêm trọng khác

        # 3. THÊM CÁC CỘT CÒN LẠI (ĐỂ CHẮC CHẮN)
        
        # Cột: description_reason
        try:
            print("Đang thêm cột 'description_reason' (TEXT) vào bảng 'asset_log'...")
            cursor.execute("ALTER TABLE asset_log ADD COLUMN description_reason TEXT DEFAULT ''")
            print("✓ Thành công! Đã thêm cột 'description_reason'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'description_reason' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # Cột: quantity
        try:
            print("Đang thêm cột 'quantity' (INTEGER) vào bảng 'asset_log'...")
            cursor.execute("ALTER TABLE asset_log ADD COLUMN quantity INTEGER NOT NULL DEFAULT 1")
            print("✓ Thành công! Đã thêm cột 'quantity'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'quantity' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # Cột: expected_return_date
        try:
            print("Đang thêm cột 'expected_return_date' (DATE) vào bảng 'asset_log'...")
            cursor.execute("ALTER TABLE asset_log ADD COLUMN expected_return_date DATE")
            print("✓ Thành công! Đã thêm cột 'expected_return_date'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'expected_return_date' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # Cột: status
        try:
            print("Đang thêm cột 'status' (VARCHAR(16)) vào bảng 'asset_log'...")
            cursor.execute("ALTER TABLE asset_log ADD COLUMN status VARCHAR(16) DEFAULT 'pending_out'")
            print("✓ Thành công! Đã thêm cột 'status'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'status' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # Cột: check_out_time
        try:
            print("Đang thêm cột 'check_out_time' (DATETIME) vào bảng 'asset_log'...")
            cursor.execute("ALTER TABLE asset_log ADD COLUMN check_out_time DATETIME")
            print("✓ Thành công! Đã thêm cột 'check_out_time'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'check_out_time' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # Cột: check_out_by_user_id
        try:
            print("Đang thêm cột 'check_out_by_user_id' (INTEGER) vào bảng 'asset_log'...")
            cursor.execute("ALTER TABLE asset_log ADD COLUMN check_out_by_user_id INTEGER")
            print("✓ Thành công! Đã thêm cột 'check_out_by_user_id'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'check_out_by_user_id' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # Cột: check_in_back_time
        try:
            print("Đang thêm cột 'check_in_back_time' (DATETIME) vào bảng 'asset_log'...")
            cursor.execute("ALTER TABLE asset_log ADD COLUMN check_in_back_time DATETIME")
            print("✓ Thành công! Đã thêm cột 'check_in_back_time'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'check_in_back_time' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # Cột: check_in_back_by_user_id
        try:
            print("Đang thêm cột 'check_in_back_by_user_id' (INTEGER) vào bảng 'asset_log'...")
            cursor.execute("ALTER TABLE asset_log ADD COLUMN check_in_back_by_user_id INTEGER")
            print("✓ Thành công! Đã thêm cột 'check_in_back_by_user_id'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'check_in_back_by_user_id' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # Cột: created_at
        try:
            print("Đang thêm cột 'created_at' (DATETIME) vào bảng 'asset_log'...")
            cursor.execute("ALTER TABLE asset_log ADD COLUMN created_at DATETIME")
            print("✓ Thành công! Đã thêm cột 'created_at'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'created_at' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # === TẠO INDEX CHO HIỆU SUẤT ===
        print("\n=== TẠO INDEX ===")
        
        indexes = [
            ("idx_asset_log_status", "CREATE INDEX IF NOT EXISTS idx_asset_log_status ON asset_log(status)"),
            ("idx_asset_log_destination", "CREATE INDEX IF NOT EXISTS idx_asset_log_destination ON asset_log(destination)"), # Thêm index cho cột mới
            ("idx_asset_log_department", "CREATE INDEX IF NOT EXISTS idx_asset_log_department ON asset_log(department)"),
            ("idx_asset_log_created_at", "CREATE INDEX IF NOT EXISTS idx_asset_log_created_at ON asset_log(created_at)")
        ]
        
        for idx_name, idx_sql in indexes:
            try:
                print(f"Đang tạo index '{idx_name}'...")
                cursor.execute(idx_sql)
                print(f"✓ Index '{idx_name}' đã được tạo!")
            except Exception as e:
                print(f"⚠ Lỗi khi tạo index '{idx_name}': {e}")

        # === LƯU THAY ĐỔI ===
        conn.commit()
        print("\n" + "="*50)
        print("✓ DI TRÚ v3 (Fix Asset Management) ĐÃ HOÀN TẤT!")
        print("="*50)

    except Exception as e:
        print(f"\n❌ ĐÃ XẢY RA LỖI NGHIÊM TRỌNG: {e}")
        if conn:
            conn.rollback()
            print("↩ Đã hoàn tác (rollback) thay đổi.")
    finally:
        if conn:
            conn.close()
            print("\n🔒 Đã đóng kết nối CSDL.")

if __name__ == "__main__":
    print("="*50)
    print("BẮT ĐẦU DI TRÚ CSDL v3 (Fix Asset Management)")
    print("="*50)
    migrate_database_v3_fix()