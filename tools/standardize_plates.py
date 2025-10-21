# -*- coding: utf-8 -*-
"""
Module Name: standardize_plates.py
Description: Một công cụ độc lập để quét cơ sở dữ liệu SQLite và
             chuẩn hóa lại định dạng của các biển số xe.
Author: Đối tác lập trình AI
Date: 21/10/2025
"""

import sqlite3
import re
import os
import sys

# --- CẤU HÌNH ---
# Xác định đường dẫn tương đối đến file database từ vị trí của script này.
# Script này nằm trong /tools, database nằm trong /backend
DB_FILENAME = "security_v2_3.db"
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', DB_FILENAME)

# Danh sách các bảng và cột cần được chuẩn hóa
# Cấu trúc: ('tên_bảng', 'tên_cột_biển_số', 'tên_cột_id')
TABLES_TO_PROCESS = [
    ('guests', 'license_plate', 'id'),
    ('long_term_guests', 'license_plate', 'id'),
    ('supplier_plates', 'plate', 'id')
]

# --- HÀM LÕI ---

def format_license_plate(plate_string: str) -> str:
    """
    Hàm này nhận vào một chuỗi biển số và trả về chuỗi đã được chuẩn hóa
    theo định dạng *-XXX.XX.

    Ví dụ:
    - '29H16088' -> '29H-160.88'
    - '29a-160.25' -> '29A-160.25'
    - '51F 12345' -> '51F-123.45'
    - '30A1234' -> '30A1234' (Không đủ 5 số cuối, giữ nguyên)
    """
    if not plate_string or not isinstance(plate_string, str):
        return plate_string

    # 1. Dọn dẹp và viết hoa chuỗi đầu vào
    # Loại bỏ tất cả dấu chấm, gạch ngang, khoảng trắng
    cleaned_plate = plate_string.upper().replace('.', '').replace('-', '').replace(' ', '')

    # 2. Sử dụng biểu thức chính quy (regex) để tìm kiếm mẫu:
    # Mẫu bao gồm một phần tiền tố (có thể là số và chữ) và một hậu tố là 5 chữ số ở cuối.
    # (.*?)   : Nhóm 1, bắt bất kỳ ký tự nào (phần tiền tố)
    # (\d{5}) : Nhóm 2, bắt chính xác 5 chữ số
    # $       : Đảm bảo 5 chữ số này nằm ở cuối chuỗi
    match = re.match(r'^(.*?)(\d{5})$', cleaned_plate)

    if match:
        prefix = match.group(1)
        five_digits = match.group(2)
        
        # 3. Áp dụng định dạng chuẩn: *-xxx.xx
        formatted_suffix = f"{five_digits[:3]}.{five_digits[3:]}"
        
        return f"{prefix}-{formatted_suffix}"
    
    # 4. Nếu chuỗi không khớp với mẫu (ví dụ: không có 5 số ở cuối),
    # trả về chuỗi đã được dọn dẹp và viết hoa.
    return cleaned_plate

def standardize_all_plates():
    """
    Hàm chính để kết nối CSDL, duyệt qua các bảng và cập nhật biển số.
    """
    print(f"--- BẮT ĐẦU QUÁ TRÌNH CHUẨN HÓA BIỂN SỐ XE ---")
    
    # Kiểm tra xem file database có tồn tại không
    if not os.path.exists(DB_PATH):
        print(f"\n[LỖI] Không tìm thấy file cơ sở dữ liệu tại: {os.path.abspath(DB_PATH)}")
        print("Vui lòng đảm bảo bạn đang chạy script này từ thư mục 'tools' của dự án.")
        sys.exit(1)
        
    print(f"Đã kết nối tới cơ sở dữ liệu: {os.path.abspath(DB_PATH)}")

    conn = None
    total_updated_count = 0
    try:
        # Mở kết nối đến database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Lặp qua từng bảng đã được cấu hình
        for table_name, column_name, id_column in TABLES_TO_PROCESS:
            print(f"\n[ĐANG XỬ LÝ] Bảng '{table_name}', cột '{column_name}'...")
            
            cursor.execute(f"SELECT {id_column}, {column_name} FROM {table_name}")
            rows = cursor.fetchall()

            updated_in_table = 0
            for row_id, old_plate in rows:
                if not old_plate:
                    continue

                new_plate = format_license_plate(old_plate)

                # Chỉ cập nhật nếu có sự thay đổi
                if new_plate != old_plate:
                    print(f"  - Cập nhật ID {row_id}: '{old_plate}' -> '{new_plate}'")
                    cursor.execute(f"UPDATE {table_name} SET {column_name} = ? WHERE {id_column} = ?", (new_plate, row_id))
                    updated_in_table += 1
            
            if updated_in_table > 0:
                print(f"[THÀNH CÔNG] Đã cập nhật {updated_in_table} bản ghi trong bảng '{table_name}'.")
                total_updated_count += updated_in_table
            else:
                print(f"[INFO] Không có bản ghi nào cần cập nhật trong bảng '{table_name}'.")

        # Lưu tất cả các thay đổi vào database
        if total_updated_count > 0:
            conn.commit()
            print(f"\n--- HOÀN TẤT ---")
            print(f"Đã lưu tất cả thay đổi. Tổng cộng {total_updated_count} biển số đã được chuẩn hóa.")
        else:
            print(f"\n--- HOÀN TẤT ---")
            print("Toàn bộ dữ liệu biển số đã ở định dạng chuẩn.")

    except sqlite3.Error as e:
        print(f"\n[LỖI DATABASE] Đã xảy ra lỗi: {e}")
        if conn:
            conn.rollback() # Hoàn tác các thay đổi nếu có lỗi
    except Exception as e:
        print(f"\n[LỖI KHÔNG XÁC ĐỊNH] Đã xảy ra lỗi: {e}")
    finally:
        if conn:
            conn.close() # Luôn đóng kết nối
            print("\nĐã đóng kết nối cơ sở dữ liệu.")

# --- ĐIỂM KHỞI CHẠY SCRIPT ---
if __name__ == "__main__":
    print("===================================================================")
    print(" CÔNG CỤ CHUẨN HÓA BIỂN SỐ XE - AN NINH NỘI BỘ")
    print("===================================================================")
    print("\nCẢNH BÁO QUAN TRỌNG:")
    print("1. Tác vụ này sẽ THAY ĐỔI TRỰC TIẾP dữ liệu trong database.")
    print("2. Vui lòng SAO LƯU (BACKUP) file 'backend/security_v2_3.db' trước khi tiếp tục.")
    print("===================================================================")
    
    # Yêu cầu người dùng xác nhận trước khi chạy
    while True:
        choice = input("\nBạn đã sao lưu database và sẵn sàng tiếp tục? (yes/no): ").lower().strip()
        if choice == 'yes':
            standardize_all_plates()
            break
        elif choice == 'no':
            print("Đã hủy tác vụ. Vui lòng sao lưu database trước khi chạy lại.")
            break
        else:
            print("Vui lòng nhập 'yes' hoặc 'no'.")
