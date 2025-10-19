# Gói triển khai "Nhật ký xe" (Phiên bản nâng cao)

Gói này bao gồm:
- **apps_script/**: Script tự động **tách dữ liệu theo tháng** từ Google Sheets (Archive Job).
- **backend/**: Dịch vụ **FastAPI** làm API trung gian đọc Google Sheets (file live + archive) và trả JSON + endpoint **xuất Excel**.
- **frontend/**: Trang dashboard **hiển thị biểu đồ + bảng**, gọi API backend.

> Mặc định dữ liệu gồm **3 cột**: **Số xe (A)**, **Ngày (B - Date)**, **Giờ (C - Time)**.  
> Múi giờ: `Asia/Ho_Chi_Minh`.

---

## 1) Apps Script (Archive Job) — tự động xoay vòng dữ liệu theo tháng

**Mục tiêu**: Giữ file live (tháng hiện tại) nhẹ (~10k dòng), dữ liệu cũ chuyển sang file archive theo **năm**.  
**Cách dùng**: Xem `apps_script/README.md` và `apps_script/archive_job.gs`.

---

## 2) Backend (FastAPI) — API đọc Sheets + xuất Excel

### 2.1. Cài đặt
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2.2. Biến môi trường
Tạo file `.env` ở thư mục `backend/` hoặc export môi trường trước khi chạy:
```
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
LIVE_SHEET_ID=<ID file NhatKyXe_Live>
ARCHIVE_SHEETS={"2024":"<ID_Archive_2024>", "2025":"<ID_Archive_2025>"}
SHEET_NAME=Trang tính1
TIMEZONE=Asia/Ho_Chi_Minh
ALLOW_ORIGINS=*
PORT=8000
```

> Đặt file `credentials.json` (Service Account) trong thư mục `backend/` hoặc trỏ đường dẫn tuyệt đối.

### 2.3. Chạy
```bash
uvicorn app.main:app --reload --port 8000
```

### 2.4. API chính
- `GET /vehicle-log` — trả JSON (lọc nhanh/khoảng, tìm tương đối theo biển số, phân trang, kèm **chart + KPI**).
- `GET /vehicle-log/export` — xuất **Excel** theo đúng bộ lọc đang áp dụng.

---

## 3) Frontend (dashboard HTML độc lập)

- Mở file: `frontend/vehicle_log_dashboard.html` (nhúng Vue + ApexCharts + SheetJS từ CDN).
- Sửa biến `API_BASE` (URL backend) trong file HTML trước khi mở:
  ```html
  const API_BASE = "http://localhost:8000";
  ```

---

## 4) Tích hợp vào hệ thống hiện có

- Backend: Copy `app/routers/vehicle_log.py` + `app/services/gsheets_reader.py` + `app/config.py` vào dự án, thêm `include_router`.
- Frontend: Di chuyển nội dung HTML/JS vào trang Vue/Quasar của bạn; thay ApexCharts theo component framework nếu muốn.

---

## 5) Ghi chú

- Khi filter vượt tháng hiện tại, backend chỉ đọc **những sheet/tháng cần thiết** từ file archive theo **năm** để tăng tốc.
- Heatmap Ngày × Giờ, Area Trend + MA7, Top 10 biển số, Hourly distribution được trả sẵn từ API để frontend render dễ dàng.
