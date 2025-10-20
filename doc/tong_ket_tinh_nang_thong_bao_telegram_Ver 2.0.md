# 🛰️ Tổng Kết Tính Năng: Thông Báo Tự Động Qua Telegram

**Dự án:** Ứng dụng An Ninh Nội Bộ  
**Thời gian:** Tháng 10, 2025  
**Mục tiêu:** Cung cấp thông tin cập nhật, theo thời gian thực về tình hình khách ra vào cho đội ngũ an ninh thông qua một kênh Telegram chuyên dụng, đảm bảo thông tin luôn gọn gàng và chỉ hiển thị trạng thái mới nhất.

---

## 1. Mô tả & Luồng Hoạt động

Tính năng này tự động gửi một tin nhắn **tổng hợp** đến một nhóm chat Telegram mỗi khi có sự thay đổi trong **danh sách khách chờ vào**.  
Để tránh làm nhiễu thông tin, hệ thống được thiết kế để **xóa tin nhắn cũ và thay thế bằng một tin nhắn mới duy nhất**, đảm bảo nhóm chat chỉ hiển thị **danh sách chờ cập nhật nhất**.

### 🔁 Luồng hoạt động chi tiết

**Kích hoạt (Trigger):**  
Tác vụ được kích hoạt mỗi khi có một trong các sự kiện sau xảy ra:
- Một hoặc nhiều khách mới được đăng ký (`create_guest`, `create_guests_bulk`).
- Một khách được xác nhận vào (`confirm-in`).

**Xử lý nền (Background Task):**  
Ngay khi sự kiện kích hoạt, hệ thống đưa tác vụ gửi thông báo vào hàng đợi xử lý nền (`BackgroundTasks` của FastAPI), giúp API phản hồi ngay cho người dùng mà không bị trễ.

**Xóa tin nhắn cũ:**  
- Hệ thống đọc ID của tin nhắn trước từ file `telegram_last_message_id.txt`.  
- Nếu tìm thấy ID, hệ thống gửi yêu cầu `deleteMessage` tới Telegram API để xóa tin cũ.

**Tổng hợp dữ liệu mới:**  
- Truy vấn cơ sở dữ liệu để lấy toàn bộ khách có trạng thái `pending` (chờ vào).

**Tạo và gửi tin nhắn mới:**  
- Định dạng dữ liệu thành một tin nhắn duy nhất, rõ ràng theo mẫu thống nhất.  
- Gửi tin nhắn tổng hợp mới qua Telegram API (`sendMessage`).

**Lưu trạng thái:**  
- Nếu gửi thành công, ID tin nhắn mới được ghi đè vào file `telegram_last_message_id.txt` cho lần cập nhật kế tiếp.

---

## 2. Quá trình Phát triển & Các Cải tiến

Tính năng đã trải qua nhiều giai đoạn cải tiến:

| Phiên bản | Mô tả | Nhược điểm / Cải tiến |
|------------|--------|----------------------|
| **V1 – Tin nhắn riêng lẻ** | Gửi tin cho từng sự kiện (đăng ký, xác nhận). | Spam nhóm chat, khó theo dõi. |
| **V2 – Tổng hợp danh sách chờ** | Gửi tin duy nhất chứa toàn bộ danh sách chờ. | Giảm spam, nhưng vẫn tạo nhiều tin liên tiếp. |
| **V3 – Xóa & Thay thế (hiện tại)** | Dùng `deleteMessage` để thay thế tin cũ. | Giữ 1 tin duy nhất – gọn gàng, rõ ràng. |

**Cải tiến định dạng tin nhắn:**  
Hiển thị gọn thông tin: Họ tên, CCCD, BKS, Nhà cung cấp, người đăng ký, thời gian.  
Cập nhật tự động và có dấu thời gian để dễ theo dõi.

---

## 3. Các Vấn đề Kỹ thuật & Cách Khắc Phục

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|--------------|-----------|
| `AssertionError` khi khởi động server | Khai báo `BackgroundTasks` sai (dùng `Depends`). | Chỉ cần dùng type hint `bg: BackgroundTasks`. |
| `ModuleNotFoundError` | Import tương đối sai (`from .database`). | Sửa thành `from ..database`. |
| Không xóa được tin nhắn | 1. Bot không có quyền admin. 2. Thiếu logging. | 1. Cấp quyền **Administrator** và “Can delete messages”. 2. Thêm logging chi tiết để theo dõi Telegram API. |

---

## 4. Hướng Dẫn Cài Đặt & Vận Hành

### ⚙️ Cấu hình `.env`
```bash
NOTIFY_TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=<token từ BotFather>
TELEGRAM_CHAT_ID=-100xxxxxxxxxx
```

### 🧾 Quyền của Bot trong nhóm
- Bắt buộc là **Administrator**.  
- Phải bật quyền **“Xóa tin nhắn” (Can delete messages)**.

### 🗂️ File `telegram_last_message_id.txt`
- Tự động tạo trong thư mục `backend/` khi gửi tin đầu tiên.  
- Không cần tạo thủ công.

---

## 5. Kết Quả

- Hệ thống thông báo gọn gàng, hiệu quả, không gây phiền nhiễu.  
- Nhóm Telegram luôn hiển thị **1 tin duy nhất**, phản ánh **danh sách CHỜ VÀO mới nhất**.  
- Đội ngũ an ninh dễ dàng nắm bắt thông tin và phản hồi nhanh chóng.

---
