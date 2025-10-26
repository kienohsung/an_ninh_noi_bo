# TỔNG HỢP CUỘC THẢO LUẬN VÀ CẬP NHẬT KẾ HOẠCH DỰ ÁN

Đây là bản tổng hợp các vấn đề đã được thảo luận, lý do và giải pháp đã được thống nhất cho dự án phân tích và tổng hợp khuyến nghị chứng khoán từ Gmail, tập trung vào việc tích hợp Google Cloud API.

---

## 1. Tích hợp Xử lý Nội dung File & Bất đồng bộ

| Hạng mục | Lý do | Giải pháp Đã thống nhất |
| :--- | :--- | :--- |
| **Xử lý File Bất đồng bộ (GC API)** | Quá trình gọi Google Cloud API (Document AI) để trích xuất text là tác vụ tốn thời gian, dễ gây treo luồng đồng bộ email chính. | Tích hợp cơ chế **Hàng đợi Tác vụ nhẹ** bằng **APScheduler**. Thêm bảng `ocr_jobs` để quản lý trạng thái xử lý file (PENDING/DONE/FAILED). |
| **Kiểm soát Chi phí/Upload File** | Tránh phát sinh chi phí và thời gian không cần thiết do tự động upload tất cả các file đính kèm lên Google Cloud Storage. | Chỉ tải lên Google Cloud những file được người dùng **chọn thủ công** thông qua giao diện UI. Bảng `files` sẽ có trường `is_uploaded_to_gc` để tránh upload trùng lặp. |
| **Lựa chọn GC API** | Cần một công cụ mạnh mẽ để xử lý các tài liệu phức tạp, đa trang như báo cáo phân tích PDF/DOCX. | Sử dụng **Google Cloud Document AI** (Document Text Extractor/Form Parser) thay vì tự xây dựng hay dùng Vision API. |
| **Lưu trữ Kết quả Text thô** | Cần một kho lưu trữ kết quả text thô từ OCR để tránh phải gọi lại GC API và làm cơ sở cho tìm kiếm toàn văn. | Tạo bảng **`file_ocr_results`** để lưu `full_text_content` trích xuất từ GC API. Giới hạn độ dài sẽ được cài đặt trong quá trình sử dụng. |

---

## 2. Chất lượng & Toàn vẹn Dữ liệu (DB & Extractor)

| Hạng mục | Lý do | Giải pháp Đã thống nhất |
| :--- | :--- | :--- |
| **Trích xuất Text Email** | Việc chỉ dùng regex/từ khoá để trích xuất `action`, `target_price` từ text email rất dễ bị lỗi do sự khác biệt về định dạng. | **Cân nhắc sử dụng thư viện NLP/mô hình nhỏ** cho việc trích xuất các trường quan trọng, kết hợp với cơ chế **Human-in-the-Loop** để người dùng sửa lỗi trích xuất. |
| **Chuẩn hóa Mã CP (Ticker)** | Đảm bảo tính nhất quán và toàn vẹn tham chiếu của các mã CP được trích xuất (tránh lỗi chính tả, trùng lặp). | Bảng **`tickers`** sẽ được thiết lập với trường `ticker` là **UNIQUE NOT NULL**. Mọi mã CP trích xuất phải được **chuẩn hóa/tham chiếu (lookup)** với bảng này trước khi lưu vào bảng `recommendations`. |
| **Tìm kiếm Toàn văn (FTS5)** | Tăng cường khả năng tìm kiếm nội dung sâu bên trong báo cáo, không chỉ giới hạn ở tiêu đề email. | **Mở rộng FTS5** (`reports_fts`) để bao gồm `subject` **VÀ** trường `full_text_content` (kết quả text thô từ GC API). |

---

## 3. Bảo mật & Vận hành (Cá nhân)

| Hạng mục | Lý do | Giải pháp Đã thống nhất |
| :--- | :--- | :--- |
| **Bảo mật OAuth Token** | Token truy cập Gmail (Refresh Token) là khóa nhạy cảm, cần được bảo vệ dù dự án chỉ dùng cá nhân. | Không lưu trữ plaintext. Sử dụng **mã hóa cục bộ** (ví dụ: `cryptography`) hoặc **OS-level keyring** (ví dụ: thư viện `keyring`) để lưu trữ Refresh Token. |
| **Tương thích Mở File** | Đảm bảo người dùng có thể mở file báo cáo (chủ yếu là PDF) trên các hệ điều hành khác nhau. | Sử dụng các lệnh mở file chuẩn (`xdg-open` / `start` / `open`) tùy thuộc vào OS, với ưu tiên sử dụng chức năng **open-with** của hệ thống nếu file không phải PDF. |
| **Quản lý Lỗi** | Cần một cơ chế chủ động thông báo khi hệ thống gặp lỗi nghiêm trọng (ví dụ: mất kết nối DB, lỗi GC API, lỗi APScheduler). | Thiết lập cơ chế **cảnh báo tối thiểu** (ví dụ: gửi email thông báo) khi quá trình đồng bộ hoặc xử lý OCR thất bại liên tục (ví dụ: 3 lần liên tiếp). |