# Frontend — Security Management V2.3 (Vue 3 + Quasar + Pinia)

## Thay đổi V2.3
- Ẩn Dashboard đối với `staff` và `guard` (route + menu).
- Register-Guest: lịch sử chỉ hiện **khách do chính nhân viên đang đăng nhập đăng ký**.
- Users: thêm **sửa, xóa, tìm kiếm**.
- Vehicles OCR: thêm nút **Bắt đầu nhận diện** (chọn file trước, nhấn nút để chạy OCR), hiển thị **Supplier match**.
- Guard Gate: thêm danh sách **đã xác nhận vào** ở cuối trang.

## Cài đặt & chạy
```bash
cd frontend
npm install
npm run dev
# http://127.0.0.1:5173
```
# test github