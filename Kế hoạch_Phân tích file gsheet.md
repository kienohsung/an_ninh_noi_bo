# KẾ HOẠCH THỐNG NHẤT: TRANG “NHẬT KÝ XE” (PHIÊN BẢN NÂNG CAO)

> **Mục tiêu:** Xây dựng **dashboard hiện đại, trực quan, chuyên nghiệp** cho “Nhật ký xe” (dữ liệu Google Sheets với 3 cột **Số xe, Ngày, Giờ**), hỗ trợ **lọc thời gian/khoảng**, **tìm kiếm tương đối**, **xuất Excel sau lọc**; đồng thời vận hành bền vững với **cơ chế tự động tách dữ liệu theo tháng** (~10.000 dòng/tháng) và **lưu trữ theo năm**.

---

## 1) KIẾN TRÚC & LUỒNG DỮ LIỆU

### 1.1 Nguồn dữ liệu & quy ước

* **File live (tháng hiện tại):** `NhatKyXe_Live`

  * Sheet dữ liệu: **Trang tính1**, cột **A: Số xe**, **B: Ngày (Date)**, **C: Giờ (Time)**.
* **File archive theo năm:** `NhatKyXe_Archive_YYYY`

  * Mỗi **tháng** được lưu vào **một sheet riêng**: `ThangMM_YYYY` (ví dụ: `Thang10_2025`) để truy vấn nhanh và quản trị dễ.
* **Múi giờ:** `Asia/Ho_Chi_Minh`.

### 1.2 Tự động lưu trữ (Archiving) — **không cần server**

* **Công nghệ:** Google Apps Script + **Time-driven Trigger**.
* **Lịch chạy:** 01:00 sáng **ngày 1 mỗi tháng**.
* **Quy trình:**

  1. Lọc tất cả bản ghi **tháng trước** trong `NhatKyXe_Live/Trang tính1`.
  2. **Dán** vào `NhatKyXe_Archive_YYYY/ThangMM_YYYY` (tự **tạo sheet** nếu chưa có).
  3. **Xoá** các dòng đã dán khỏi file live.
  4. **Ghi log** (số dòng, thời gian, liên kết), **gửi email** tóm tắt (tùy chọn).
  5. **Tự tạo** file `NhatKyXe_Archive_YYYY` cho năm mới nếu thiếu.
* **Kết quả:** `NhatKyXe_Live` luôn chỉ chứa **tháng hiện tại (~10k dòng)** ⇒ thao tác nhanh, ổn định.

### 1.3 Backend trung gian (khuyến nghị)

* **Vai trò:** Làm API proxy tới Google Sheets (qua Service Account) + **xử lý/ tổng hợp** số liệu (đếm theo ngày, theo giờ, top biển số…).
* **Tính năng bổ sung:** Cache ngắn (60–120s), bảo vệ khóa (rate limit), chuẩn hóa dữ liệu (format ngày/giờ), chuẩn hóa tìm kiếm (bỏ dấu, không phân biệt hoa thường).
* **Phương án không-backend:** Dùng **Apps Script Web App** trả JSON (khi muốn tối giản). Hai phương án tương thích nhau.

---

## 2) THIẾT KẾ GIAO DIỆN DASHBOARD

### 2.1 Bố cục tổng thể (responsive, dark/light)

* **Hàng 1 – Bộ lọc & KPI**

  * **Bộ lọc nhanh:** Hôm nay, 7 ngày, 30 ngày, Tuần này, Tháng này, Tháng trước.
  * **Khoảng tùy chỉnh:** Từ ngày/Đến ngày (YYYY-MM-DD).
  * **Tìm kiếm tương đối:** theo **Số xe** (bỏ dấu/không phân biệt hoa thường).
  * **Nút Xuất Excel:** xuất **đúng phần dữ liệu đã lọc**.
  * **Thẻ KPI (3–4 thẻ):**

    * **Tổng lượt** trong khoảng (số lớn, nổi bật).
    * **Giờ cao điểm nhất** (tính theo histogram giờ).
    * **Top 1 biển số hoạt động nhiều nhất** trong khoảng.
    * (Tuỳ chọn) **Trung bình lượt/ngày**.
* **Hàng 2 – Biểu đồ chính (ưu tiên trực quan, sinh động):**

  * **Area Trend (Xu hướng theo ngày)** + **MA7** (đường trung bình 7 ngày)
  * **Heatmap Ngày × Giờ** (điểm nóng theo ngày/giờ)
  * **Horizontal Bar – Top 10 biển số**
* **Hàng 3 – Bảng dữ liệu chi tiết:**

  * Cột: **Số xe | Ngày | Giờ**; **phân trang / cuộn vô hạn**; **sortable**; **quick-search**.

### 2.2 Phong cách & UX chuyên nghiệp

* **Tối giản & sạch sẽ:** chú trọng khoảng trắng, bỏ đường lưới dư thừa.
* **Màu sắc có chủ đích:** bảng màu thống nhất; gradient nhẹ; tương thích **dark mode**.
* **Tương tác mượt:** hover tinh tế, **tooltip giàu thông tin**, **crosshair** cho biểu đồ tuyến tính, chuyển cảnh mềm.
* **Typography:** KPI/giá trị chính đậm (600–700), nhãn phụ mảnh và nhạt.

---

## 3) HỆ BIỂU ĐỒ (TẬP TRUNG TRỰC QUAN, HIỆN ĐẠI)

> **Thư viện ưu tiên:** **ApexCharts** (tương tác phong phú, cấu hình gradient/animation tốt).
> **Thay thế:** ECharts (siêu linh hoạt) hoặc Chart.js (cơ bản, cần tuỳ chỉnh nhiều hơn cho “độ sang”).

### 3.1 Area Trend (xu hướng theo ngày) — **must-have**

* **Dữ liệu:** ngày (x), số lượt (y).
* **Hiệu ứng:** area gradient nhạt; line sắc nét; **MA7** bật/tắt; **crosshair + tooltip** hiển thị 2 series (raw & MA7).
* **Giá trị:** nắm xu hướng, biến động, chu kỳ.

### 3.2 Heatmap Ngày × Giờ (ma trận) — **must-have**

* **Trục:** X = 24 giờ (00–23), Y = ngày (YYYY-MM-DD).
* **Màu:** gradient từ nhạt → nóng (thấp → cao); bo góc nhẹ.
* **Tooltip:** “Thứ/Ngày, Giờ — X lượt”.
* **Giá trị:** nhìn “điểm nóng” rõ hơn mọi biểu đồ cột.

### 3.3 Horizontal Bar – Top 10 biển số — **must-have**

* **Trục:** Y = biển số (text), X = lượt (số).
* **Hiệu ứng:** thanh bo góc, **gradient theo chiều ngang**, hiển thị **giá trị cuối thanh**.
* **Giá trị:** nhận diện phương tiện/đối tác nổi bật.

### 3.4 Hourly Distribution (line/area theo giờ)

* **Trục:** 00–23; tổng lượt theo từng giờ (gộp theo filter).
* **Giá trị:** xác định giờ cao điểm trong ngày.

### 3.5 Calendar Heatmap (toàn năm) — **nâng cao**

* **Bố cục:** lưới 365 ô như “GitHub contributions”, màu theo lượt/ngày.
* **Giá trị:** bức tranh năm; phát hiện ngày bất thường.
* **Gợi ý:** đặt ở tab “Tổng quan năm” để không làm nặng trang chính.

### 3.6 KPI Sparkline (mini-charts trong card)

* **Dạng:** line/area siêu nhỏ, không trục/nhãn.
* **Dữ liệu:** 7–30 ngày gần nhất của KPI tương ứng.
* **Giá trị:** tăng tính “chuyên nghiệp”, đọc xu hướng trong nháy mắt.

---

## 4) BẢNG DỮ LIỆU & TƯƠNG TÁC

* **Cột:** Số xe | Ngày | Giờ.
* **Sắp xếp:** mặc định “mới → cũ”, có thể thay đổi.
* **Phân trang / cuộn vô hạn:** 50–100 dòng/lần tải để mượt.
* **Tìm kiếm tương đối:** normalize bỏ dấu + lowercase; debounce 300–400ms.
* **Xuất Excel (sau lọc):** tải đúng dataset đang xem (khớp bộ lọc/tìm kiếm), tên file theo ngày.

---

## 5) API HỢP NHẤT (BACKEND ⇄ SHEETS)

> Có thể thay bằng **Web App Apps Script** nếu muốn tối giản. Bên dưới là hợp đồng API (dù triển khai ở backend hay Apps Script).

### 5.1 Endpoint dữ liệu & phân tích

`GET /vehicle-log`

* **Query:**

  * `quick` = `today|last7|last30|thisWeek|thisMonth|prevMonth`
  * `start`, `end` = `YYYY-MM-DD` (ưu tiên nếu có, bỏ qua quick)
  * `q` = chuỗi tìm theo **Số xe** (tương đối)
  * `page`, `pageSize` (mặc định 1 & 50)
* **Response:**

  ```json
  {
    "total": 1234,
    "page": 1,
    "pageSize": 50,
    "items": [
      {"plate":"51F-123.45","date":"2025-10-18","time":"08:15"},
      ...
    ],
    "chart": {
      "daily":   {"labels":["2025-10-01",...],"series":[100,...]},
      "hours":   {"labels":["00","01",...],"series":[12,34,...]},
      "heatmap": {"rows":["2025-10-01",...],"cols":["00","01",...],"matrix":[[0,1,...],...]},
      "top10":   {"labels":["51F-123.45",...],"series":[25,...]}
    },
    "kpi": {
      "totalInRange": 1234,
      "peakHour": "17",
      "topPlate": "51F-123.45",
      "avgPerDay": 412
    }
  }
  ```

### 5.2 Endpoint xuất Excel

`GET /vehicle-log/export`

* **Query:** giống `/vehicle-log` (bộ lọc giống hệt).
* **Response:** file `.xlsx` gồm sheet `NhatKyXe` với cột **Số xe | Ngày | Giờ**.

> **Lưu ý hiệu năng:**
>
> * **Ưu tiên đọc `NhatKyXe_Live`** cho khoảng tháng hiện tại.
> * **Khi filter vượt qua tháng hiện tại**, chỉ đọc **các sheet/tháng cần thiết** từ `NhatKyXe_Archive_YYYY` (không merge toàn bộ).
> * **Cache**: kết quả tổng hợp theo tham số (60–120s) để mượt với 10k dòng/tháng.

---

## 6) KẾ HOẠCH TỰ ĐỘNG TÁCH DỮ LIỆU (CHI TIẾT)

### 6.1 Thực thi

* **Apps Script “Archive Job”** (độc lập với API đọc):

  * Trigger **time-driven**: lúc **01:00** ngày **1** mỗi tháng.
  * **Bước 1:** Xác định **tháng trước**; lọc theo cột **Ngày**.
  * **Bước 2:** Dán vào `NhatKyXe_Archive_YYYY/ThangMM_YYYY`.
  * **Bước 3:** Xoá phần đã dán trong `NhatKyXe_Live`.
  * **Bước 4:** Ghi **log** (sheet “Lịch sử lưu trữ”) & (tùy chọn) **gửi email**.
  * **Bước 5:** Nếu `NhatKyXe_Archive_YYYY` chưa tồn tại ⇒ **tự tạo**.

### 6.2 An toàn & kiểm soát

* **Dry-run** lần đầu (chạy thử không xoá) để xác nhận số dòng/đích.
* **Sao lưu nhanh** trước khi xoá (`makeCopy`).
* **Ngưỡng cảnh báo:** nếu số dòng tháng trước **< 3.000** hoặc **> 20.000**, gửi email cảnh báo.
* **Bảng điều khiển vận hành:** thống kê số dòng mỗi tháng, thời gian chạy, thời lượng.

---

## 7) TRIỂN KHAI & THỜI GIAN DỰ KIẾN

### Giai đoạn A — Chuẩn bị (0.5–1 ngày)

* Chuẩn hóa cột; tạo file live & archive năm hiện tại; cấp quyền SA/Script.

### Giai đoạn B — Archive Job (1–1.5 ngày)

* Viết Script; trigger lịch; log + email; kiểm thử dry-run & bản sao dự phòng.

### Giai đoạn C — API dữ liệu (0.5–1 ngày)

* Đọc Sheets (live + các sheet tháng trong archive theo filter); tổng hợp biểu đồ; cache.

### Giai đoạn D — Giao diện (1.5–2 ngày)

* Bộ lọc/KPI; hệ biểu đồ (Area+MA7, Heatmap ngày×giờ, Hourly line, Top10 bar); bảng; export.

### Giai đoạn E — Kiểm thử & bàn giao (0.5–1 ngày)

* Hiệu năng với dữ liệu mẫu ≥ 30.000 dòng; kiểm thử edge cases; tài liệu sử dụng & vận hành.

*(Tổng: 4–6 ngày, tùy mức tinh chỉnh UI và hiệu ứng biểu đồ.)*

---

## 8) RỦI RO & GIẢM THIỂU

| Rủi ro                                          | Ứng phó                                                                                                |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Định dạng “Ngày/Giờ” không phải Date/Time chuẩn | Bước normalize định dạng trước khi tổng hợp; cảnh báo khi phát hiện text “ngày/giờ”                    |
| Archive năm mới chưa có                         | Script **tự tạo** file năm/sheet tháng                                                                 |
| Hiệu năng khi filter dài hạn (nhiều tháng)      | Chỉ đọc chính xác **những sheet/tháng** cần thiết; **cache** kết quả 60–120s; downsample series khi vẽ |
| Giới hạn API/Quota                              | Cache; batch đọc; tối ưu số lần gọi; tránh gọi lại khi tham số không đổi                               |
| Bảo mật Web App/API                             | Giới hạn “Anyone in domain” hoặc xác thực token; ẩn khoá; rate limit ở backend                         |

---

## 9) TIÊU CHÍ HOÀN THÀNH (ACCEPTANCE)

* **Archive Job** chạy tự động mỗi tháng; log & (tùy chọn) email báo cáo; file live chỉ chứa **tháng hiện tại**.
* **Dashboard**:

  * Lọc nhanh & khoảng hoạt động đúng; tìm tương đối chính xác.
  * **Biểu đồ trực quan, sinh động**:

    * Area Trend + MA7 (crosshair + tooltip)
    * Heatmap Ngày × Giờ (gradient đẹp, tooltip giàu thông tin)
    * Top 10 biển số (horizontal bar bo góc + giá trị cuối thanh)
    * Phân bố theo giờ (line/area)
  * KPI nổi bật + sparkline mini.
  * **Export Excel** đúng **dataset sau lọc**.
* Thời gian tải **< 2s** cho phạm vi 7–30 ngày; ổn định với **~10k dòng/tháng**.

---

## 10) TUỲ CHỌN MỞ RỘNG

* **Calendar Heatmap cả năm** (tab “Tổng quan năm”).
* **Bookmark bộ lọc** (deep-link query params).
* **Cảnh báo bất thường** (so với baseline 30 ngày).
* **Looker Studio** tích hợp cho cấp quản lý.
* **Internationalization** (vi/eng), **Accessibility** (WCAG lite).

---
