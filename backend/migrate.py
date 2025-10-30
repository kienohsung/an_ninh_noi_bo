import sqlite3
import os

# Đường dẫn đến file CSDL (đảm bảo file này nằm trong thư mục 'backend')
# Lấy tên file từ file migrate.py cũ bạn gửi
DB_FILE = os.path.join(os.path.dirname(__file__), 'security_v2_3.db')
if not os.path.exists(DB_FILE):
    print(f"LỖI: Không tìm thấy file CSDL tại '{DB_FILE}'.")
    print("Vui lòng kiểm tra lại tên file CSDL trong script 'migrate_v2.py'.")
    exit(1)

def migrate_database_v2():
    conn = None
    try:
        # 1. Kết nối đến CSDL
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"Đã kết nối thành công đến {DB_FILE}")

        # === Xử lý bảng 'guests' ===

        # 2. Thêm cột mới 'estimated_datetime' cho 'guests'
        try:
            print("Đang thêm cột 'estimated_datetime' (kiểu DATETIME) vào bảng 'guests'...")
            cursor.execute("ALTER TABLE guests ADD COLUMN estimated_datetime DATETIME")
            print("...Thành công!")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("...Cột 'estimated_datetime' trong 'guests' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # 3. Xóa cột cũ 'estimated_time' khỏi 'guests' (nếu tồn tại)
        try:
            print("Đang xóa cột cũ 'estimated_time' khỏi bảng 'guests'...")
            # Lưu ý: Cú pháp DROP COLUMN yêu cầu SQLite 3.35.0+
            # Chúng ta sẽ chạy lệnh này, nếu thất bại (do phiên bản SQLite cũ)
            # cũng không sao, cột đó sẽ không được dùng nữa.
            cursor.execute("ALTER TABLE guests DROP COLUMN estimated_time")
            print("...Xóa thành công!")
        except sqlite3.OperationalError as e:
            if "no such column" in str(e) or "can't drop" in str(e):
                print("...Cột 'estimated_time' trong 'guests' không tồn tại hoặc không thể xóa (bỏ qua).")
            else:
                # Báo lỗi nhưng vẫn tiếp tục
                print(f"...Lỗi khi xóa cột 'estimated_time' (guests): {e}. Cân nhắc xóa thủ công nếu cần.")


        # === Xử lý bảng 'long_term_guests' ===

        # 4. Thêm cột mới 'estimated_datetime' cho 'long_term_guests'
        try:
            print("Đang thêm cột 'estimated_datetime' (kiểu DATETIME) vào bảng 'long_term_guests'...")
            cursor.execute("ALTER TABLE long_term_guests ADD COLUMN estimated_datetime DATETIME")
            print("...Thành công!")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("...Cột 'estimated_datetime' trong 'long_term_guests' đã tồn tại. Bỏ qua.")
            else:
                raise e

        # 5. Xóa cột cũ 'estimated_time' khỏi 'long_term_guests' (nếu tồn tại)
        try:
            print("Đang xóa cột cũ 'estimated_time' khỏi bảng 'long_term_guests'...")
            cursor.execute("ALTER TABLE long_term_guests DROP COLUMN estimated_time")
            print("...Xóa thành công!")
        except sqlite3.OperationalError as e:
            if "no such column" in str(e) or "can't drop" in str(e):
                print("...Cột 'estimated_time' trong 'long_term_guests' không tồn tại hoặc không thể xóa (bỏ qua).")
            else:
                print(f"...Lỗi khi xóa cột 'estimated_time' (long_term_guests): {e}. Cân nhắc xóa thủ công nếu cần.")


        # 6. Lưu thay đổi và đóng kết nối
        conn.commit()
        print("\nDi trú v2 (DateTime) đã hoàn tất. Đã lưu (commit) thay đổi.")

    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình di trú v2: {e}")
        if conn:
            conn.rollback() # Hoàn tác nếu có lỗi
            print("Đã hoàn tác (rollback) thay đổi.")
    finally:
        if conn:
            conn.close()
            print("Đã đóng kết nối CSDL.")

if __name__ == "__main__":
    print("Bắt đầu quá trình di trú CSDL v2 (Nâng cấp lên DateTime)...")
    migrate_database_v2()
