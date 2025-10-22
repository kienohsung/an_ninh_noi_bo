# -*- coding: utf-8 -*-
"""
Module Name: plate_formatter.py
Description: Cung cấp các hàm tiện ích để định dạng biển số xe.
Author: Đối tác lập trình AI
Date: 21/10/2025
"""
import re

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
