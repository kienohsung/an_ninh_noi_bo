# Checklist Tích Hợp Tính Năng Mới (Telegram & PWA)

Đây là danh sách các bước cần thực hiện để tích hợp thành công chức năng thông báo qua Telegram và chế độ hoạt động offline (PWA) cho trang "Cổng bảo vệ".

---

## Giai đoạn 1: Cài đặt Telegram Bot

**Mục tiêu:** Lấy `BOT_TOKEN` và `CHAT_ID` để cấu hình cho backend.

- [ ] **Bước 1.1: Tạo Bot mới**  
  - [ ] Mở ứng dụng Telegram, tìm và bắt đầu cuộc trò chuyện với `@BotFather`.  
  - [ ] Gửi lệnh `/newbot` và làm theo hướng dẫn để đặt tên và username cho bot.  
  - [ ] Lưu lại `BOT_TOKEN` mà BotFather cung cấp.

- [ ] **Bước 1.2: Lấy Chat ID**  
  - [ ] Tạo một group chat mới trên Telegram và thêm bot bạn vừa tạo vào làm thành viên.  
  - [ ] Gửi một tin nhắn bất kỳ vào group đó.  
  - [ ] Mở trình duyệt và truy cập vào đường link sau (thay `<YOUR_TOKEN>` bằng token bạn đã lưu):  
    `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`  
  - [ ] Trong kết quả JSON trả về, tìm đến mục `chat -> id`. Lưu lại giá trị id này (nó thường là một số âm). Đây chính là `CHAT_ID` của bạn.

---

## Giai đoạn 2: Cập nhật Backend

**Mục tiêu:** Tích hợp mã nguồn xử lý và gửi thông báo vào hệ thống backend hiện tại.

- [ ] **Bước 2.1: Cập nhật `requirements.txt`**  
  - [ ] Mở file `backend/requirements.txt`.  
  - [ ] Thêm dòng sau để cài đặt thư viện requests, cần thiết cho việc gửi thông báo:  
    ```
    requests>=2.31.0
    ```  
  - [ ] Chạy lại `pip install -r requirements.txt` trong môi trường ảo của bạn.

- [ ] **Bước 2.2: Sao chép các file mới**  
  - [ ] Chép file `testingCodeTelegram/backend/app/utils/notifications.py` vào thư mục `backend/app/utils/` trong dự án của bạn.  
  - [ ] Chép file `testingCodeTelegram/backend/app/routers/admin_telegram.py` vào thư mục `backend/app/routers/`.  
  - [ ] Chép file `testingCodeTelegram/backend/app/routers/guests_confirm.py` vào thư mục `backend/app/routers/`.

- [ ] **Bước 2.3: Cập nhật file `backend/app/main.py`**  
  - [ ] Mở file `main.py`.  
  - [ ] Thêm các dòng import sau cùng với các router khác:  
    ```python
    from .routers import guests_confirm, admin_telegram
    ```  
  - [ ] Thêm các dòng đăng ký router sau, giữ nguyên các router hiện có:  
    ```python
    app.include_router(guests_confirm.router)
    app.include_router(admin_telegram.router)
    ```

- [ ] **Bước 2.4: Cập nhật file môi trường `.env`**  
  - [ ] Mở file `.env` trong thư mục backend.  
  - [ ] Thêm vào 3 dòng sau, thay thế bằng thông tin bạn đã lấy ở Giai đoạn 1:  
    ```
    NOTIFY_TELEGRAM_ENABLED=true
    TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
    TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE
    ```

- [ ] **Bước 2.5: Khởi động lại và Kiểm tra Backend**  
  - [ ] Khởi động lại server backend.  
  - [ ] Truy cập vào địa chỉ API (ví dụ: `http://127.0.0.1:8000/docs`) và gọi thử endpoint `GET /admin/telegram/test`.  
  - [ ] **Xác nhận:** Bạn nhận được tin nhắn `"Test: hệ thống đã kết nối Telegram thành công"` trong group Telegram.

---

## Giai đoạn 3: Cập nhật Frontend (PWA Offline Mode)

**Mục tiêu:** Kích hoạt chế độ offline cho trang "Cổng bảo vệ".

- [ ] **Bước 3.1: Sao chép các file PWA**  
  - [ ] Chép file `testingCodeTelegram/frontend/public/sw.js` vào thư mục `frontend/public/`.  
  - [ ] Tạo thư mục mới `frontend/src/pwa/db/`.  
  - [ ] Chép file `testingCodeTelegram/frontend/src/pwa/db/guard-gate-db.js` vào thư mục vừa tạo.  
  - [ ] Chép file `testingCodeTelegram/frontend/src/register-sw.js` vào thư mục `frontend/src/`.

- [ ] **Bước 3.2: Chỉnh sửa file `frontend/src/pages/GuardGate.vue`**  
  - [ ] Mở file và thực hiện các thay đổi theo hướng dẫn chi tiết trong file `README_GuardGate_PATCH.md`.  
  - [ ] Các bước chính bao gồm:  
    - [ ] Thêm các câu lệnh import cần thiết ở đầu phần `<script setup>`.  
    - [ ] **Quan trọng:** Gọi hàm đăng ký Service Worker trong `onMounted`:  
      ```javascript
      import { registerServiceWorker } from '../register-sw'

      onMounted(() => { 
        registerServiceWorker() 
        // ...các logic khác trong onMounted...
      })
      ```  
    - [ ] Thêm các `ref` mới (`cachedAt`, `offline`).  
    - [ ] Cập nhật logic trong `onMounted` để ưu tiên tải dữ liệu từ cache.  
    - [ ] Sửa đổi hàm `confirmIn` để có thể xếp hàng đợi yêu cầu khi offline.  
    - [ ] Thêm hàm `flushQueue` để xử lý hàng đợi khi có mạng trở lại.  
    - [ ] Thêm `q-badge` vào template để hiển thị trạng thái "Offline".

- [ ] **Bước 3.3: Khởi động lại và Kiểm tra Frontend (Offline Mode)**  
  - [ ] Khởi động lại server frontend.  
  - [ ] Mở trang "Cổng bảo vệ". Mở Developer Tools (F12), vào tab **Network** và chọn chế độ **Offline**.  
  - [ ] **Xác nhận:** Tải lại trang, dữ liệu khách vẫn hiển thị từ snapshot và có badge "Offline" cùng thời gian cache.  
  - [ ] Khi đang ở chế độ Offline, bấm **"XÁC NHẬN VÀO"** cho một khách.  
  - [ ] **Xác nhận:** Bạn nhận được thông báo `"Đã xếp hàng xác nhận..."`.  
  - [ ] Chuyển lại chế độ **Online** trong Developer Tools.  
  - [ ] **Xác nhận:** Yêu cầu được tự động gửi đi, danh sách khách được cập nhật, và thông báo được gửi đến Telegram (nếu có ảnh, ảnh sẽ được đính kèm).

---

## Giai đoạn 4: Hoàn tất

- [ ] **Bước 4.1 (Tùy chọn): Thông báo khi tạo khách**  
  - [ ] Nếu bạn muốn hệ thống gửi thông báo ngay khi có khách mới được đăng ký, hãy mở file `backend/app/routers/guests.py` và áp dụng các thay đổi được mô tả trong file `PATCH_NOTE_guests_notify.txt`.

- [ ] **Bước 4.2: Kiểm tra toàn bộ luồng End-to-End**  
  - [ ] Thực hiện lại các kịch bản kiểm thử ở **Bước 2.5** và **3.3** để đảm bảo toàn bộ hệ thống hoạt động đồng bộ và chính xác.

---

Sau khi bạn hoàn thành các bước trên, hệ thống sẽ được tích hợp đầy đủ hai tính năng mới.
