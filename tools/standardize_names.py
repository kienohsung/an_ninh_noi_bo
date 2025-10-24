# File: tools/standardize_names.py
"""
Script này dùng để chuẩn hóa cột Họ Tên trong cơ sở dữ liệu SQLite cục bộ.
Nó sẽ đổi các tên như "nguyễn VĂN a" thành "Nguyễn Văn A".
Lưu ý: Dữ liệu Nhật ký xe (vehicle_log) được quản lý trên Google Sheets và không được xử lý bởi script này.
"""
import os
import sys

# Thêm thư mục backend vào sys.path để có thể import app.models
# Điều này giả định script được chạy từ thư mục `tools/`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from sqlalchemy import create_engine, select, update, MetaData, Table, exc
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("Lỗi: Không tìm thấy thư viện SQLAlchemy.")
    print("Vui lòng cài đặt bằng lệnh: pip install SQLAlchemy")
    sys.exit(1)

# --- CẤU HÌNH ---

# Đường dẫn đến file database.
DB_FILENAME = "security_v2_3.db"
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', DB_FILENAME)

# Danh sách các bảng và cột cần chuẩn hóa TRONG DATABASE SQLITE CỤC BỘ
# Định dạng: 'tên_bảng': 'tên_cột_họ_tên'
# ĐÃ LOẠI BỎ 'vehicle_log' vì nó không nằm trong DB này.
TABLES_AND_COLUMNS = {
    'guests': 'full_name',
    'long_term_guests': 'full_name',
    'users': 'full_name',
    # 'vehicle_log': 'driver_name', # Loại bỏ dòng này
}

# --- KẾT THÚC CẤU HÌNH ---

def format_full_name(name: str) -> str:
    """
    Chuẩn hóa tên sang dạng Title Case.
    Ví dụ: "nguyễn VĂN a" -> "Nguyễn Văn A"
    """
    if not name or not isinstance(name, str):
        return ""
    # Dùng .title() để viết hoa ký tự đầu mỗi từ
    # CODE CŨ: return name.strip().title()
    # CODE MỚI: Thêm .lower() để xử lý các trường hợp chữ hoa không đồng nhất (như 'NguyễN')
    return name.strip().lower().title() # PHẦN CODE SỬA ĐỔI

def main():
    print(f"--- Công cụ Chuẩn hóa Họ Tên (Title Case) cho Database SQLite ---")

    if not os.path.exists(DB_PATH):
        print(f"Lỗi: Không tìm thấy file database tại: {DB_PATH}")
        print("Vui lòng kiểm tra lại đường dẫn DB_PATH trong script.")
        return

    print(f"Đang kết nối tới database: {DB_PATH}")

    # Xác nhận sao lưu
    confirm = input("QUAN TRỌNG: Bạn đã sao lưu (backup) file database chưa? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Vui lòng sao lưu database trước khi chạy script này. Đã hủy.")
        return

    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    session = Session()
    metadata = MetaData()

    total_updated = 0

    print("Bắt đầu quá trình chuẩn hóa...")

    try:
        with engine.connect() as connection:
            transaction = connection.begin() # Bắt đầu transaction
            try:
                for table_name, column_name in TABLES_AND_COLUMNS.items():
                    print(f"\n[Đang xử lý Bảng: {table_name}, Cột: {column_name}]")

                    table = None
                    try:
                        # Tải định nghĩa bảng từ database
                        table = Table(table_name, metadata, autoload_with=engine)
                    except exc.NoSuchTableError:
                        print(f"  LƯU Ý: Không tìm thấy bảng '{table_name}' trong database. Bỏ qua.")
                        continue # Bỏ qua và chuyển sang bảng tiếp theo

                    # Kiểm tra xem bảng có cột 'id' và cột 'tên' không
                    id_column_name = 'id' # Giả định tên cột ID là 'id'
                    if not hasattr(table.c, id_column_name):
                        print(f"  LỖI: Bảng '{table_name}' không có cột ID '{id_column_name}'. Bỏ qua bảng này.")
                        continue
                    if not hasattr(table.c, column_name):
                        print(f"  LỖI: Bảng '{table_name}' không có cột '{column_name}'. Bỏ qua bảng này.")
                        continue

                    # Lấy tất cả bản ghi
                    stmt = select(table)
                    results = connection.execute(stmt).fetchall()

                    count_table_updated = 0

                    for row in results:
                        # Lấy ID và tên một cách an toàn bằng tên cột
                        row_id = getattr(row, id_column_name)
                        current_name = getattr(row, column_name)

                        if not current_name or not isinstance(current_name, str):
                            continue

                        formatted_name = format_full_name(current_name)

                        if current_name != formatted_name:
                            # Cập nhật bản ghi
                            update_stmt = update(table).where(getattr(table.c, id_column_name) == row_id).values(
                                **{column_name: formatted_name}
                            )
                            connection.execute(update_stmt)

                            print(f"  ID {row_id}: '{current_name}' -> '{formatted_name}'")
                            count_table_updated += 1
                            total_updated += 1

                    if count_table_updated == 0:
                        print("  Không có tên nào cần cập nhật.")
                    else:
                        print(f"  Hoàn tất! Đã cập nhật {count_table_updated} bản ghi trong bảng {table_name}.")

                # Commit tất cả thay đổi nếu không có lỗi
                transaction.commit()
                print("\n--- HOÀN TẤT ---")
                if total_updated > 0:
                    print(f"Tổng cộng đã cập nhật {total_updated} bản ghi trên toàn bộ database SQLite.")
                else:
                    print("Không có bản ghi nào cần cập nhật trong database SQLite.")

            except Exception as e:
                print(f"\nĐã xảy ra lỗi trong quá trình xử lý: {e}")
                print("Đang rollback... Mọi thay đổi đã bị hủy.")
                transaction.rollback() # Rollback nếu có lỗi

    except Exception as e:
        print(f"\nĐã xảy ra lỗi kết nối hoặc transaction: {e}")
    finally:
        session.close() # Đảm bảo session được đóng

if __name__ == "__main__":
    main()
