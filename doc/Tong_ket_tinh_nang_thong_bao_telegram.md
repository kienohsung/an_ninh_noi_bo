# Tổng Kết Quá Trình Phát Triển Tính Năng Thông Báo Telegram

Tài liệu này ghi lại chi tiết các giai đoạn phát triển, các sự cố gặp phải và giải pháp kỹ thuật đã được áp dụng để hoàn thiện tính năng gửi thông báo tức thì qua Telegram cho hệ thống An Ninh Nội Bộ.

## Giai đoạn 1: Triển khai & Cải tiến lần đầu

### 1.1. Mục tiêu ban đầu
Ban đầu, tính năng chỉ gửi thông báo đến Telegram khi bảo vệ nhấn nút **"XÁC NHẬN VÀO"** tại trang *Cổng bảo vệ*.

### 1.2. Yêu cầu cải tiến
- **Thông báo khi có đăng ký mới:** Hệ thống cần gửi thông báo ngay khi có một khách mới được tạo, không chỉ lúc xác nhận vào.  
- **Việt hóa trạng thái:** Các trạng thái như `pending` hay `checked_in` trong tin nhắn Telegram cần được hiển thị bằng tiếng Việt có dấu để dễ hiểu hơn (ví dụ: “ĐANG CHỜ”, “ĐÃ VÀO”).

### 1.3. Thay đổi kỹ thuật
- **guests.py:** Sửa đổi các endpoint `create_guest` và `create_guests_bulk` để thêm vào một tác vụ nền (`BackgroundTasks`) sau khi tạo khách thành công. Tác vụ này sẽ gọi hàm gửi thông báo.  
- **notifications.py:** Tạo một hàm mới `format_guest_for_telegram` để định dạng nội dung tin nhắn, trong đó có logic chuyển đổi trạng thái sang tiếng Việt.  
- **guests_confirm.py:** Cập nhật để sử dụng hàm `format_guest_for_telegram`, đảm bảo tính nhất quán.

### 1.4. Lỗi phát sinh và cách khắc phục
- **Lỗi:** `AssertionError: Cannot specify 'Depends' for type <class 'fastapi.background.BackgroundTasks'>`  
- **Nguyên nhân:** Lỗi này xảy ra do việc khai báo `BackgroundTasks` trong các hàm xử lý API đã sử dụng cú pháp `bg: BackgroundTasks = Depends()`. Trong FastAPI, `BackgroundTasks` là một dependency đặc biệt và phải được khai báo trực tiếp dưới dạng `bg: BackgroundTasks`, không cần thông qua `Depends`.  
- **Khắc phục:** Đã cập nhật lại chữ ký của các hàm trong `guests.py` và `guests_confirm.py`, thay đổi cách khai báo `BackgroundTasks` cho đúng với quy chuẩn của FastAPI.  

**Code cũ (lỗi):**
```python
def create_guest(..., bg: BackgroundTasks = Depends()):
```

**Code mới (đã sửa):**
```python
def create_guest(..., bg: BackgroundTasks):  # hoặc bg: BackgroundTasks = BackgroundTasks()
```

---

## Giai đoạn 2: Tinh chỉnh luồng gửi ảnh

### 2.1. Yêu cầu cải tiến
- **Chỉ gửi ảnh khi đăng ký mới:** Hình ảnh chỉ nên được đính kèm vào thông báo khi người dùng đăng ký khách và tải ảnh lên.  
- **Không gửi ảnh khi xác nhận vào:** Khi bảo vệ nhấn “XÁC NHẬN VÀO”, hệ thống chỉ cần gửi một thông báo bằng văn bản, không cần đính kèm lại hình ảnh.

### 2.2. Thay đổi kỹ thuật
- **guests.py:**  
  - Xóa bỏ việc gửi thông báo khỏi các hàm `create_guest` và `create_guests_bulk`.  
  - Chuyển logic gửi thông báo vào `upload_guest_image`: thông báo sẽ chỉ được kích hoạt khi một tệp ảnh được tải lên thành công. Tại thời điểm này, hệ thống sẽ truy vấn lại toàn bộ thông tin của khách và gửi một thông báo duy nhất kèm tất cả các ảnh đó.  

- **guests_confirm.py:**  
  - Trong hàm `confirm_in`, thay đổi lệnh gọi từ `send_telegram_photos` thành `send_telegram_message` để chỉ gửi nội dung văn bản.

### 2.3. Hiệu quả và Lưu ý
- **Luồng hoạt động chính xác:** Ảnh chỉ được gửi một lần duy nhất tại thời điểm đăng ký, và việc xác nhận vào cổng chỉ gửi thông báo văn bản.  
- **Lưu ý về hành vi:** Nếu người dùng tải lên 3 ảnh cho một khách, hệ thống sẽ gửi 3 thông báo liên tiếp, trong đó thông báo cuối cùng sẽ là đầy đủ nhất (chứa cả 3 ảnh). Đây là sự đánh đổi để giữ cho logic xử lý đơn giản và đáp ứng nhanh yêu cầu.

---

## Tổng kết
Tính năng thông báo qua Telegram hiện đã hoạt động ổn định, đúng theo các luồng nghiệp vụ được yêu cầu, và có cơ chế xử lý lỗi rõ ràng. Mã nguồn đã được tối ưu để đảm bảo hiệu suất và tính nhất quán.
