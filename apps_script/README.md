# Apps Script Archive Job

## Mục tiêu
- Vào **01:00 sáng ngày 1 hàng tháng**, script sẽ:
  1. Lọc tất cả dữ liệu **tháng trước** từ `NhatKyXe_Live/Trang tính1`.
  2. Ghi dữ liệu đó vào `NhatKyXe_Archive_YYYY/ThangMM_YYYY` (tạo sheet nếu chưa có).
  3. **Xoá** dữ liệu đã sao chép khỏi file live.
  4. Ghi **log** và **(tuỳ chọn)** gửi email tóm tắt.

## Hướng dẫn triển khai
1. Mở **Apps Script** (Extensions → Apps Script) từ file `NhatKyXe_Live` hoặc tạo project riêng.
2. Dán file `archive_job.gs` vào.
3. Cập nhật **CONFIG** (ID file live, map archive theo năm, tên sheet).
4. Tạo **Trigger**: Time-driven → Month timer → On the 1st → 01:00.
5. Lần đầu chạy nên bật **DRY_RUN = true** để kiểm tra số dòng/sheet đích.
6. Sau khi xác nhận → đặt **DRY_RUN = false**.

## Lưu ý
- Bảo đảm cột **Ngày** là Date thật (không phải text).
- Giữ nguyên header 1 dòng ở cả file live và archive.
- Có thể bật gửi email báo cáo sau khi chạy xong.
