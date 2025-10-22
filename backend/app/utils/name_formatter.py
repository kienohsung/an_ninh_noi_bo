# File: backend/app/utils/name_formatter.py
"""
Module tiện ích chứa hàm chuẩn hóa Họ Tên sang dạng Title Case.
"""

def format_full_name(name: str) -> str:
    """
    Chuẩn hóa tên sang dạng Title Case (Viết hoa chữ cái đầu mỗi từ).
    
    Ví dụ: 
    - "nguyễn văn a" -> "Nguyễn Văn A"
    - "NGUYỄN VĂN B" -> "Nguyễn Văn B"
    - "trần thị c" -> "Trần Thị C"
    """
    if not name or not isinstance(name, str):
        return ""
        
    # .strip() để xóa khoảng trắng thừa ở đầu/cuối
    # .title() để chuyển sang dạng Title Case
    return name.strip().title()
