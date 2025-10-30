% an_ninh_noi_bo — Giới thiệu Dự án
% Nguyễn Trung Kiên (tác giả tài liệu / kỹ sư)
% Phiên bản: V2.3

---
# Giới thiệu chung
**an_ninh_noi_bo** — Hệ thống quản lý an ninh nội bộ
Mục tiêu: quản lý đăng ký khách, xác nhận vào cổng, báo cáo, và chức năng OCR/AI hỗ trợ trích xuất dữ liệu từ CCCD/CMND.  


Notes: Tóm tắt ngắn, dùng làm slide mở đầu.

---
# Các thay đổi quan trọng (V2.3)
- Chỉnh quyền truy cập: staff chỉ xem lịch sử do mình đăng ký; admin/manager/guard xem tất cả.  
- Users: thêm tìm kiếm, sửa, xóa.  
- OCR/Vehicle: tự động đối chiếu biển số với supplier list, gán `supplier_id`.  
- Guard Gate: hiển thị danh sách đã xác nhận.  
- Dashboard: ẩn cho staff & guard.  
**Nguồn:** backend/README.md (V2.3) :contentReference[oaicite:1]{index=1}

Notes: Liệt kê highlight kỹ thuật.

---
# Mục tiêu chức năng chính
1. Quản lý khách (đăng ký, xác nhận, lịch sử).  
2. Tự động trích xuất thông tin CCCD/ID (OCR + AI).  
3. Thông báo realtime (Telegram) cho trạng thái chờ và logging.  
4. Dashboard & báo cáo (bao gồm trang "Nhật ký xe" dùng Google Sheets cho dữ liệu xe vào/ra).  
**Nguồn:** doc/Project diary.md (nhật ký & kế hoạch) :contentReference[oaicite:2]{index=2}

Notes: Slide mục tiêu hệ thống.

---
# Kiến trúc tổng quan (Microservices / 3 thành phần chính)
Kiến trúc gồm **3 thành phần chính** (mô tả tổng quan):
- **Frontend (Client)** — giao diện người dùng (ví dụ trang "Đăng ký khách"), cho phép tải ảnh, gọi API backend.  
- **Backend (API Gateway)** — cổng API an toàn; không xử lý AI trực tiếp, chuyển yêu cầu an toàn tới service chuyên dụng.  
- **Service chuyên dụng** (ví dụ: ID Card Extractor Service / OCR, Service xử lý Gemini/Gemini-proxy) — xử lý OCR/AI, trả về kết quả trích xuất.  
**Nguồn:** doc/Project diary.md (mô tả kiến trúc & luồng ảnh → backend → service) :contentReference[oaicite:3]{index=3}

Notes: Kèm sơ đồ microservices (chèn ảnh vào slide, xem phần hình ảnh).

---
# Luồng xử lý trích xuất CCCD (từ Frontend → Backend → ID-Extractor)
1. Người dùng chọn/đăng ảnh trên trang "Đăng ký khách".  
2. Frontend gửi ảnh tới **Backend Gateway**. Backend không xử lý AI trực tiếp.  
3. Backend gọi endpoint (ví dụ `/gemini/extract-cccd-info`) và **chuyển tiếp** ảnh tới **ID Card Extractor Service** (URL cấu hình trong `.env`, ví dụ `http://127.0.0.1:5009/extract`).  
4. Kết quả trích xuất trả về frontend hoặc được lưu vào DB.  
**Nguồn:** doc/Project diary.md (mô tả upload + endpoint `/gemini/extract-cccd-info`) :contentReference[oaicite:4]{index=4}

Notes: Show code snippet (ví dụ hàm gọi POST) nếu cần.

---
# Tích hợp Telegram — Thiết kế thông báo
- **Hai kênh Telegram**:
  - Kênh Chính (Main): hiển thị danh sách chờ (luôn chỉ 1 tin duy nhất, được cập nhật).  
  - Kênh Lưu trữ (Archive): lưu toàn bộ lịch sử hành động (tin mới, không xóa).  
- Thực hiện gửi thông báo qua **FastAPI BackgroundTasks** để trả về ngay cho client mà không block.  
- Logic chính đặt ở `backend/app/utils/notifications.py`; router gọi module này.  
**Nguồn:** doc/Project diary.md — phần Tài liệu kỹ thuật Telegram (23.10.2025) :contentReference[oaicite:5]{index=5}

Notes: Đưa flowchart: Event → BackgroundTasks → notifications.py → Telegram API.

---
# Các endpoint / Router chính (ví dụ)
- `routers/guests.py` — tạo & quản lý khách.  
- `routers/guests_confirm.py` — xác nhận khách vào cổng, cập nhật trạng thái `checked_in`, dùng background tasks cho archive & notify.  
- `routers/gemini.py` — nhận request từ frontend & chuyển tiếp tới ID-Extractor.  
**Nguồn:** Kết hợp summary file `guests_confirm.py` và `gemini.py` (mô tả hành vi) :contentReference[oaicite:6]{index=6} :contentReference[oaicite:7]{index=7}

Notes: Có thể chèn trích đoạn code minh họa một hàm endpoint.

---
# Cấu hình & triển khai (Backend)
- Env mẫu (`backend/.env`) — `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `CORS_ORIGINS`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `TZ`.  
- Chạy server: `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` (Swagger: `http://127.0.0.1:8000/docs`)  
- Lưu ý: Dữ liệu & ảnh **lưu cục bộ** vào SQLite & thư mục `uploads/`.  
**Nguồn:** backend/README.md (cài đặt, env, run) :contentReference[oaicite:8]{index=8}

Notes: Slide kỹ thuật — hướng dẫn nhanh để dev chạy local.

---
# Tính năng báo cáo & Dashboard
- Dashboard cho admin/manager: visualizations, KPI.  
- Trang “Nhật ký xe”: dùng Google Sheets + Apps Script (ETL, archive theo tháng, export Excel, heatmap, top plates, filters).  
**Nguồn:** doc/Project diary.md (chi tiết "Nhật ký xe") :contentReference[oaicite:9]{index=9}

Notes: Show mockups / hình ảnh chart.

---
# Bảo mật & Quyền truy cập
- RBAC: role-based access control (admin, manager, guard, staff).  
- Việc xử lý ảnh/AI được tách ra service riêng để giảm bề mặt tấn công cho API Gateway.  
- Lưu ý: **Đổi SECRET_KEY** trước khi deploy.  
**Nguồn:** backend/README.md + docs kiến trúc. :contentReference[oaicite:10]{index=10}

Notes: Nhấn mạnh hardening trước production.

---
# Lộ trình & Cải tiến đề xuất
- Hoàn thiện UI/UX Dashboard, cải thiện caching & downsampling chart.  
- Nâng cấp ID-Extractor để hỗ trợ nhiều kiểu giấy tờ hơn, retry & queue khi overload.  
- Tích hợp CI/CD để build/publish PPT/Tài liệu tự động (xem phần automation).  
**Nguồn:** doc/Plan_caiTien.md / Project diary (chi tiết kế hoạch) :contentReference[oaicite:11]{index=11}

Notes: Bullet list roadmap ngắn.

---
# Thành viên & Liên hệ
- Tác giả / Maintainer: **Nguyễn Trung Kiên** (`@kienohsung`) — Email: *kienohsung@gmail.com*  
- Repo: `https://github.com/kienohsung/an_ninh_noi_bo`  
Notes: Cần chèn thông tin liên hệ và nơi xem mã nguồn.

---
# Demo & Hình ảnh (Slides hình ảnh)
- Sơ đồ kiến trúc (chèn file `docs/architecture.png` hoặc screenshot).  
- Ảnh mockup trang "Đăng ký khách" & "Nhật ký xe".  
Notes: Slide này để chèn các file PNG/SVG từ repo.

---
# Tài liệu tham khảo / Các file chính
- `backend/README.md` — cài đặt & thay đổi V2.3. :contentReference[oaicite:12]{index=12}  
- `doc/Project diary.md` — mô tả kiến trúc, Telegram, luồng xử lý. :contentReference[oaicite:13]{index=13}  
- `backend/app/routers/guests_confirm.py` — ví dụ router xác nhận. :contentReference[oaicite:14]{index=14}

Notes: Kèm link cụ thể tới các file ở repo.
