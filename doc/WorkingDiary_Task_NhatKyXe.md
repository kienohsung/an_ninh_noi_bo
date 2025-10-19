# Nhật ký Phát triển: Chức năng "Nhật ký xe"

**Dự án:** Ứng dụng An Ninh Nội Bộ  
**Thời gian:** Tháng 10, 2025  
**Người thực hiện:** mrKienIT & Đối tác Lập trình (AI)  
**Mục tiêu:** Xây dựng một dashboard phân tích dữ liệu xe ra vào, kết nối trực tiếp với file Google Sheet, tích hợp vào hệ thống "An Ninh Nội Bộ" hiện có.

---

## Giai đoạn 1: Lên kế hoạch và Thiết kế Kiến trúc

Quá trình bắt đầu khi có yêu cầu xây dựng một trang báo cáo trực quan từ file Google Sheet "nhật ký xe".

### 1.1. Yêu cầu ban đầu

- Hiển thị dữ liệu từ Google Sheet.  
- Cung cấp các biểu đồ, bảng biểu để phân tích.  
- Giải quyết lo ngại về việc file Google Sheet sẽ ngày càng lớn.

### 1.2. Thảo luận và chốt Kiến trúc

Ban đầu, chúng tôi xem xét các phương án như nhúng trực tiếp Google Data Studio. Tuy nhiên, để tích hợp sâu và tùy biến giao diện, chúng tôi đã quyết định xây dựng một trang mới ngay trong ứng dụng hiện có.

**Kiến trúc được lựa chọn:**

#### Backend (FastAPI)

- Xác thực và kết nối an toàn với Google Sheets API.  
- Nhận yêu cầu từ Frontend (bộ lọc, tìm kiếm).  
- Đọc dữ liệu từ file Google Sheet (cả file chính và file lưu trữ).  
- Xử lý, tổng hợp, và tính toán toàn bộ dữ liệu cho biểu đồ và KPI.  
- Trả về dữ liệu đã được xử lý dưới dạng JSON cho Frontend.

#### Frontend (Vue/Quasar)

- Hiển thị các bộ lọc.  
- Gửi yêu cầu lên Backend.  
- Nhận dữ liệu JSON đã được xử lý sẵn và render ra các biểu đồ, bảng biểu.

**Lý do chọn kiến trúc này:**

- **Bảo mật:** Khóa API và file credentials.json được giữ an toàn ở phía backend, không bị lộ ra trình duyệt.  
- **Hiệu suất:** Giảm tải cho trình duyệt của người dùng.  
- **Khả năng mở rộng:** Dễ dàng thay đổi nguồn dữ liệu trong tương lai.

### 1.3. Giải pháp cho dữ liệu lớn

- Sử dụng Google Apps Script tự động tách dữ liệu hàng tháng.  
- File chính luôn nhẹ, chỉ chứa dữ liệu tháng hiện tại.

---

## Giai đoạn 2: Tích hợp và Gỡ lỗi (Debugging)

### 2.1. Lỗi Khởi động Backend

- **Triệu chứng:** ImportError, ModuleNotFoundError, AttributeError.  
- **Nguyên nhân:** Thiếu `__init__.py`, tên thư mục BACKEND viết hoa, lỗi import và tên biến cấu hình.  
- **Giải pháp:**  
  - Thêm file `__init__.py`.  
  - Đổi tên thư mục `backend`.  
  - Sửa cách import và thống nhất tên biến.

### 2.2. Lỗi Giao diện Trang trắng

- **Triệu chứng:** `[Vue Router warn]: No match found...`, `[plugin:vite:vue] template required`.  
- **Nguyên nhân:** File `MainLayout.vue` bị hỏng, thiếu route `/vehicle-log`.  
- **Giải pháp:** Khôi phục layout gốc, bổ sung route mới.

### 2.3. Lỗi Kết nối Dữ liệu

- **Triệu chứng:** `FATAL: Credentials file not found...`, `503 Service Unavailable`.  
- **Nguyên nhân:** Thiếu `credentials.json`, frontend chưa xử lý lỗi.  
- **Giải pháp:** Thêm hướng dẫn tạo tài khoản dịch vụ, thêm xử lý lỗi (try...catch, banner thông báo).

### 2.4. Lỗi Phân trang và Biểu đồ

- **Triệu chứng:** `422 Unprocessable Entity`, biểu đồ Top 10 xe không hiện nhãn.  
- **Nguyên nhân:** Phân trang xung đột, sai định dạng dữ liệu ApexCharts.  
- **Giải pháp:** Phân trang phía server, chỉnh hàm `updateChartData()`.

---

## Giai đoạn 3: Hoàn thiện và Tinh chỉnh

- Bộ lọc mặc định: “Tháng này”.  
- Bổ sung tùy chọn “Tất cả”.

---

## Kết luận

Chức năng **"Nhật ký xe"** đã được triển khai và tích hợp thành công.  
Quá trình phát triển thể hiện rõ **tính thực tiễn, khả năng gỡ lỗi có hệ thống và kiến trúc vững chắc**.
