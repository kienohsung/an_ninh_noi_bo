# Backend — Security Management V2.3 (FastAPI + SQLite, Local-only)

## Thay đổi quan trọng V2.3
- **Guests/Register-Guest:** Staff chỉ xem **lịch sử khách do chính mình đăng ký** (kể cả khi xem lịch sử). `admin/manager/guard` xem được tất cả.
- **Users:** Bổ sung **tìm kiếm, sửa, xóa**.
- **Suppliers ↔ Vehicles OCR:** Tự động **đối chiếu biển số** với danh sách đã đăng ký của nhà cung cấp; nếu khớp sẽ gán `supplier_id` cho bản ghi vehicle.
- **Guard Gate:** Thêm danh sách **đã xác nhận vào** ở cuối màn hình.
- **Reports/Dashboard:** frontend ẩn Dashboard đối với `staff` và `guard`.

## Cài đặt
```bash
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
```

## Cài Tesseract (cho OCR)
- Windows: https://tesseract-ocr.github.io/ (chọn "Add to PATH")
- macOS: `brew install tesseract`
- Ubuntu/Debian: `sudo apt-get install -y tesseract-ocr`

## Chạy server
```bash
python -m uvicorn app.main:app --reload --reload-exclude ".venv" --reload-exclude "__pycache__" --host 127.0.0.1 --port 8000
# Swagger: http://127.0.0.1:8000/docs
```

## Env mẫu (`backend/.env`)
```
SECRET_KEY=change_me_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=http://127.0.0.1:5173
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
TZ=Asia/Bangkok
```

> Dữ liệu & ảnh lưu **cục bộ** trong SQLite & thư mục `uploads/`.
