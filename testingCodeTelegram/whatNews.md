Có gì trong .zip

Backend

backend/app/utils/notifications.py — gửi Telegram (text + nhiều ảnh).

backend/app/routers/guests_confirm.py — POST /guests/{id}/confirm-in (idempotent) + gửi Telegram với toàn bộ ảnh của bản ghi.

backend/app/routers/admin_telegram.py — GET /admin/telegram/test để test kết nối Telegram.

backend/.env.example.append — mẫu biến môi trường:

NOTIFY_TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=-1001234567890
PWA_GUARDGATE_ENABLED=true


backend/PATCH_NOTE_guests_notify.txt — hướng dẫn chèn notify sau khi tạo khách vào guests.py nếu bạn muốn bắn Telegram ngay khi tạo.

Frontend

frontend/public/sw.js — Service Worker:

cache GET /guests (network-first, fallback cache),

Background Sync tag sync-confirm (bắn sự kiện cho trang flush queue).

frontend/src/pwa/db/guard-gate-db.js — Dexie: snapshot guests:list:{userId} + hàng đợi confirmIn.

frontend/src/register-sw.js — đăng ký SW.

README_GuardGate_PATCH.md — patch chi tiết cần thêm vào src/pages/GuardGate.vue (badge Offline, snapshot-first, queue & flush).

README_PWA_GuardGate.md — tổng quan PWA/Offline.

README_Telegram_Setup.md — hướng dẫn tạo bot, lấy CHAT_ID, test.

Việc bạn cần làm (nhanh)

Backend

Add router mới vào app/main.py (hoặc nơi bạn include routers):

from app.routers import guests_confirm, admin_telegram
app.include_router(guests_confirm.router)
app.include_router(admin_telegram.router)


Cập nhật .env theo backend/.env.example.append.

(Tuỳ chọn) mở backend/app/routers/guests.py, làm theo PATCH_NOTE_guests_notify.txt để bắn Telegram ngay khi tạo khách.

Frontend

Copy public/sw.js, src/pwa/db/guard-gate-db.js, src/register-sw.js vào dự án.

Mở src/pages/GuardGate.vue và làm theo README_GuardGate_PATCH.md:

đăng ký SW,

load snapshot Dexie trước, sau đó call API,

sửa confirmIn để xếp hàng khi offline và đăng ký sync-confirm,

thêm flushQueue() lắng sự kiện từ SW và online,

hiển thị badge “Offline” + cachedAt.

Domain/CORS

Bạn đã xác nhận giữ 5173/5174 như hiện tại — không cần đổi gì.

Telegram

Thực hiện theo README_Telegram_Setup.md để lấy BOT_TOKEN và CHAT_ID.

Gọi GET /admin/telegram/test để kiểm tra.

Khi xác nhận vào: app sẽ gửi đầy đủ thông tin bản ghi + toàn bộ ảnh (nếu có).

Gợi ý merge

Bạn đã có nhánh test_Telegrame. Hãy giải nén .zip, chép file vào repo rồi commit:

feat(telegram): backend notifications + test endpoint

feat(pwa-guardgate): SW + Dexie cache + bg sync + UI hooks

docs: README PWA & Telegram setup