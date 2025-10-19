/**
 * Archive Job: xoay vòng dữ liệu theo tháng cho "Nhật ký xe"
 * - Nguồn: NhatKyXe_Live / sheet "Trang tính1" (A: Số xe, B: Ngày, C: Giờ)
 * - Đích: NhatKyXe_Archive_YYYY / sheet "ThangMM_YYYY"
 * - Lịch gợi ý: Time-driven trigger, 01:00 sáng ngày 1 mỗi tháng
 */

const CONFIG = {
  LIVE_SHEET_ID: 'PUT_LIVE_SHEET_ID_HERE',
  ARCHIVE_MAP: {
    '2024': 'PUT_ARCHIVE_2024_ID_HERE',
    '2025': 'PUT_ARCHIVE_2025_ID_HERE'
  },
  LIVE_SHEET_NAME: 'Trang tính1',
  HEADER_ROWS: 1,
  DATE_COL: 2, // "Ngày" ở cột B (1-based)
  DRY_RUN: false, // true: chạy thử, không xoá/ghi; false: thực thi
  SEND_EMAIL: false,
  REPORT_EMAIL: 'you@example.com'
};

function runArchiveJob() {
  const tz = Session.getScriptTimeZone();
  const now = new Date();
  const firstOfThisMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const lastMonthDate = new Date(firstOfThisMonth - 1);
  const year = lastMonthDate.getFullYear();
  const month = lastMonthDate.getMonth(); // 0-11
  const sheetNameTarget = `Thang${String(month+1).padStart(2,'0')}_${year}`;

  const live = SpreadsheetApp.openById(CONFIG.LIVE_SHEET_ID);
  const shLive = live.getSheetByName(CONFIG.LIVE_SHEET_NAME);
  if (!shLive) throw new Error('Không tìm thấy sheet live');

  const values = shLive.getDataRange().getValues();
  if (!values || values.length <= CONFIG.HEADER_ROWS) {
    Logger.log('Không có dữ liệu trong file live.');
    return;
  }
  const header = values[0];
  const rows = values.slice(CONFIG.HEADER_ROWS);

  // Lọc tháng trước theo cột Ngày (B)
  const startOfLastMonth = new Date(year, month, 1);
  const endOfLastMonth = new Date(year, month+1, 0);
  const lastMonthRows = rows.filter(r => {
    const d = r[CONFIG.DATE_COL - 1];
    const dt = (d instanceof Date) ? d : new Date(d);
    if (!(dt instanceof Date) || isNaN(dt)) return false;
    const dOnly = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
    return dOnly >= startOfLastMonth && dOnly <= endOfLastMonth;
  });

  Logger.log(`Tháng trước: ${sheetNameTarget}, số dòng: ${lastMonthRows.length}`);

  if (lastMonthRows.length === 0) return;

  // Mở file archive theo năm
  const archiveId = CONFIG.ARCHIVE_MAP[String(year)];
  if (!archiveId) throw new Error('Chưa cấu hình ARCHIVE_MAP cho năm ' + year);
  const archive = SpreadsheetApp.openById(archiveId);
  let shTarget = archive.getSheetByName(sheetNameTarget);
  if (!shTarget && !CONFIG.DRY_RUN) {
    shTarget = archive.insertSheet(sheetNameTarget);
    shTarget.getRange(1, 1, 1, header.length).setValues([header]);
  }

  // Ghi dữ liệu sang archive
  if (!CONFIG.DRY_RUN) {
    const startRow = shTarget.getLastRow() + 1;
    shTarget.getRange(startRow, 1, lastMonthRows.length, header.length).setValues(lastMonthRows);
  }

  // Xoá dữ liệu cũ ở live
  if (!CONFIG.DRY_RUN) {
    // Xây danh sách các dòng (index trong sheet) cần xóa
    const toDelete = [];
    for (let i = 0; i < rows.length; i++) {
      const d = rows[i][CONFIG.DATE_COL - 1];
      const dt = (d instanceof Date) ? d : new Date(d);
      if ((dt instanceof Date) && !isNaN(dt)) {
        const dOnly = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
        if (dOnly >= startOfLastMonth && dOnly <= endOfLastMonth) {
          toDelete.push(CONFIG.HEADER_ROWS + i + 1); // chuyển về index trong sheet
        }
      }
    }
    // Xóa từ dưới lên để không lệch chỉ số
    toDelete.sort((a,b)=>b-a).forEach(r => shLive.deleteRow(r));
  }

  // Gửi báo cáo
  const msg = `Đã lưu trữ tháng ${String(month+1).padStart(2,'0')}/${year}
Số dòng: ${lastMonthRows.length}
Sheet đích: ${sheetNameTarget}`;
  Logger.log(msg);
  if (CONFIG.SEND_EMAIL && !CONFIG.DRY_RUN) {
    MailApp.sendEmail(CONFIG.REPORT_EMAIL, '[Nhật ký xe] Báo cáo lưu trữ tháng', msg);
  }
}
