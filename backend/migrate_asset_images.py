import sqlite3
import os

# Đường dẫn đến file CSDL
DB_FILE = os.path.join(os.path.dirname(__file__), 'security_v2_3.db')

if not os.path.exists(DB_FILE):
    print(f"LỖI: Không tìm thấy file CSDL tại '{DB_FILE}'.")
    print("Vui lòng kiểm tra lại tên file CSDL trong script.")
    exit(1)

def migrate_add_asset_images():
    conn = None
    try:
        # 1. Kết nối đến CSDL
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"Đã kết nối thành công đến {DB_FILE}")

        # === TẠO BẢNG 'asset_images' ===
        print("\n=== BẢNG: asset_images ===")
        
        try:
            print("Đang tạo bảng 'asset_images' (nếu chưa tồn tại)...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    image_path VARCHAR(255) NOT NULL,
                    FOREIGN KEY (asset_id) REFERENCES asset_log(id) ON DELETE CASCADE
                )
            """)
            print("✓ Bảng 'asset_images' đã được tạo!")
        except Exception as e:
            print(f"⚠ Lỗi khi tạo bảng 'asset_images': {e}")
            raise e

        # === TẠO INDEX CHO HIỆU SUẤT ===
        print("\n=== TẠO INDEX ===")
        
        try:
            print("Đang tạo index 'idx_asset_images_asset_id'...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_images_asset_id ON asset_images(asset_id)")
            print("✓ Index 'idx_asset_images_asset_id' đã được tạo!")
        except Exception as e:
            print(f"⚠ Lỗi khi tạo index: {e}")

        # === LƯU THAY ĐỔI ===
        conn.commit()
        print("\n" + "="*50)
        print("✓ DI TRÚ (Add Asset Images) ĐÃ HOÀN TẤT!")
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
    print("BẮT ĐẦU DI TRÚ CSDL (Add Asset Images)")
    print("="*50)
    migrate_add_asset_images()
