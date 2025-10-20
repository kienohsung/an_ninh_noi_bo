Tuyệt vời — dưới đây là **bản kế hoạch bổ sung** cho hai hạng mục mới, viết theo đúng phong cách “đặc tả triển khai”, có thể đưa thẳng vào backlog & thực hiện theo từng PR.

# Phần mở rộng kế hoạch

**Phạm vi:**

1. **Chế độ Offline cho “Cổng bảo vệ” (PWA + Service Worker + IndexedDB)**
2. **Thông báo đa kênh (Real-time Notifications) – ưu tiên Telegram trước**

---

## 1) Chế độ Offline cho “Cổng bảo vệ”

### 1.1. Mục tiêu & tiêu chí thành công

* Trang **“Cổng bảo vệ”** vẫn hiển thị **danh sách khách** gần nhất khi **mất mạng**.
* Khi **có mạng**, dữ liệu được **đồng bộ** và **làm mới** tự động (stale-while-revalidate).
* **UX rõ ràng**: hiển thị **badge/trạng thái** “Offline” + timestamp của dữ liệu cache.

### 1.2. Kiến trúc & công nghệ

* **Quasar PWA mode** + **Service Worker** (Workbox) để intercept request.
* **IndexedDB** (qua **Dexie.js**) lưu snapshot danh sách khách + metadata.
* **Chiến lược cache**: `Stale-While-Revalidate` cho `GET /guests` + fallback offline.
* **(Tuỳ chọn) Background Sync** để flush **hàng đợi POST** nếu sau này cần tạo/sửa dữ liệu khi offline.

### 1.3. Lưu đồ hoạt động

**Online**

1. UI gọi `GET /guests`.
2. SW cho request đi qua → nhận response → **trả UI ngay** **đồng thời** ghi **cache** (IndexedDB).
3. UI render từ **network** (tức thời) → nếu network chậm, cho phép render **cache trước** rồi merge sau.

**Offline**

1. UI gọi `GET /guests`.
2. SW phát hiện offline → **không gọi network**; **đọc IndexedDB** → trả snapshot gần nhất.
3. UI hiển thị dữ liệu **offline** + badge “Offline” + thời điểm snapshot.
4. Khi online trở lại, SW tự **revalidate** và ghi đè cache → UI nhận sự kiện **“refreshed”** cập nhật.

### 1.4. Kế hoạch triển khai (Quasar)

* **Bước 1 – Bật PWA**

  * `quasar mode add pwa`
  * Kiểm tra các file sinh ra:

    * `quasar.conf.js`/`quasar.config.js` (tùy phiên bản)
    * `src-pwa/custom-service-worker.[js|ts]`
    * `src-pwa/register-service-worker.[js|ts]`

* **Bước 2 – Service Worker**

  * Trong `src-pwa/custom-service-worker.js`:

    * Đăng ký route match `GET /guests` (đúng baseURL prod/dev).
    * Áp dụng **stale-while-revalidate**:

      * **Trước**: trả cache ngay nếu có.
      * **Sau**: fetch mạng ở background; nếu thành công → cập nhật IndexedDB.
    * Fallback khi **offline** & **cache rỗng**: trả JSON rỗng có `offline=true` để UI xử lý.

* **Bước 3 – IndexedDB (Dexie)**

  * Tạo `src/pwa/db/guard-gate-db.ts`:

    * `db.guests` (key: `id` hoặc hash page key), lưu **mảng khách** + `updatedAt`.
    * `db.meta` lưu `lastSnapshotAt`/`etag` nếu muốn dùng kiểm tra thay đổi.
  * Hàm tiện ích:

    * `saveGuestsSnapshot(list, ts)`
    * `getGuestsSnapshot() -> { list, updatedAt } | null`

* **Bước 4 – UI GuardGate.vue**

  * Trạng thái:

    * `isOffline` = `!navigator.onLine` hoặc lắng sự kiện `online/offline`.
    * `fromCache` + `cachedAt` khi dữ liệu lấy từ IndexedDB.
  * Luồng tải:

    * **Lần 1**: thử **cache trước** → render tức thì.
    * **Song song**: gọi API (nếu online) → render **mạng** → update cache.
  * Hiển thị badge “Offline” (icon mây gạch) + tooltip “Dữ liệu tại …”.

* **Bước 5 – (Tuỳ chọn) Background Sync**

  * Đăng ký `sync` tag `pending-guests` cho các **POST** khi offline.
  * SW flush queue khi `sync` fire (browser online).

### 1.5. Dữ liệu & schema cache

```ts
// Dexie Schema
db.version(1).stores({
  guests: 'key',        // key: 'all' hoặc phân trang nếu cần
  meta: 'name'          // { name: 'lastSnapshotAt', value: timestamp }
});
```

### 1.6. Bảo mật & quyền truy cập

* Dữ liệu cache là **nhạy cảm**: bật **PWA scope** chỉ domain nội bộ; khuyến nghị **xóa cache khi logout**.
* Nếu có RBAC theo user: cache **theo user** (key = userId) để tránh lộ dữ liệu chéo.

### 1.7. Kiểm thử

* **Unit**: util DB (save/get), SW handlers (mock fetch).
* **Integration**: Cypress — bật devtools offline, reload trang → vẫn có danh sách.
* **UX**: hiển thị badge offline, timestamp, behavior khi online lại (toast “Đã cập nhật”).

### 1.8. Rollout & rủi ro

* Rollout theo **feature flag** `PWA_ENABLED`.
* Rủi ro: cache cũ quá lâu → hiển thị lỗi thời. Giảm thiểu bằng `maxAge` + toast cảnh báo “dữ liệu > X phút”.

---

## 2) Thông báo đa kênh (ưu tiên Telegram)

### 2.1. Mục tiêu & lợi ích

* **Mục tiêu**: gửi thông báo **tức thì** khi có sự kiện quan trọng (khách mới, VIP check-in, bị từ chối…).
* **Lợi ích**: chủ động giám sát, tăng tốc phản ứng, giảm liên lạc thủ công.

### 2.2. Kênh ưu tiên giai đoạn 1: **Telegram**

* **Lý do**: miễn phí, dễ cấu hình, ổn định, API đơn giản.
* **Luồng**:

  1. Sự kiện (VD: tạo khách mới tại `/guests`).
  2. Backend persist → `db.commit()`.
  3. Gọi `send_telegram_message(templated_msg)`.
  4. Telegram đẩy tới nhóm “An Ninh Công Ty”.

### 2.3. Thay đổi backend

* **Biến môi trường**:

  * `TELEGRAM_BOT_TOKEN=...`
  * `TELEGRAM_CHAT_ID=...`
  * (Tuỳ chọn) `NOTIFY_ENABLED=true|false`, `NOTIFY_EVENTS=guest_created,guest_vip_checkin,...`
* **Config loader**: cập nhật `app/config.py` đọc các biến trên.
* **Utils**: `app/utils/notifications.py`

  * `def send_telegram_message(text: str) -> None`
  * Dùng `requests.post('https://api.telegram.org/bot{token}/sendMessage', data={ 'chat_id': CHAT_ID, 'text': text })`
  * **Retry**: 3 lần, backoff, log lỗi.
* **Hook ở routers**:

  * `app/routers/guests.py` → tại endpoint **create_guest**:

    * Sau `db.commit()`, build message:

      ```
      Khách mới: {name} | NCC: {org} | Biển số: {plate} | Người ĐK: {staff}
      ```
    * Gọi `send_telegram_message(message)` trong **task async** (FastAPI BackgroundTasks) để không chặn response.
* **Masking/GDPR**:

  * Tôn trọng **masking** theo role/chính sách. Channel Telegram dành cho **bên liên quan** → có thể bật **full** (cấu hình).
  * Log audit: ai/endpoint nào phát thông báo.

### 2.4. Thay đổi frontend (tuỳ chọn)

* Trang cấu hình cho admin:

  * Bật/tắt thông báo, chọn sự kiện, test gửi tin nhắn.
* Snackbar “Đã gửi thông báo đến Telegram” khi tạo khách (chỉ UX, không phụ thuộc để tránh giả thành công).

### 2.5. Kiểm thử

* **Unit**: mock `requests.post`, test retry/backoff, format message.
* **Integration**: staging bot & chat riêng.
* **Security**: không log BOT_TOKEN; rotate token khi cần.

### 2.6. Mở rộng đa kênh (giai đoạn 2)

* **Web Push**: dùng Service Worker (đã có vì PWA) + VAPID.
* **Email/SMS/Slack**: trừu tượng hóa lớp `Notifier` với adapters; cấu hình per-tenant.

### 2.7. Rollout & rủi ro

* Rollout theo **feature flag** `TELEGRAM_NOTIF_ENABLED`.
* Rủi ro: spam tin nhắn khi có nhiều sự kiện → **debounce**/**rate limit** theo type & timeframe; gom nhóm sự kiện.

---

## 3) Phụ lục: Tương tác với các cải tiến sẵn có

### 3.1. Liên hệ với MA7/MA14 & Masking biển số

* **MA7/MA14**: không ảnh hưởng tới PWA/Telegram.
* **Masking**:

  * **PWA cache** lưu **giá trị plate đã mask theo role hiện hành** hoặc lưu `plate_norm` + mask ở UI (khuyến nghị: **mask ở backend trước khi trả** để thống nhất).
  * **Telegram**: tuỳ cấu hình kênh, nếu nhóm chỉ dành cho bộ phận an ninh → **cho phép full**. Ngược lại → áp dụng mask.

---

## 4) Roadmap & PR breakdown

### Sprint 1 — PWA Offline (3–4 ngày)

* PR1: **PWA skeleton** (`mode add pwa` + SW register)
* PR2: **SW + IndexedDB + Dexie** (stale-while-revalidate, get/save snapshot)
* PR3: **UI GuardGate** (offline badge, prefetch cache, revalidate online)
* PR4: **E2E test** (Cypress offline/online), docs

### Sprint 2 — Telegram Notifications (1–2 ngày)

* PR1: **config + utils** (env, notifications.py, retry)
* PR2: **hook guests.create** + BackgroundTasks + masking policy
* PR3: **admin screen** (tuỳ chọn) + docs + staging test

---

## 5) Checklist nghiệm thu

* [ ] PWA bật, cài được trên thiết bị cổng (Add to Homescreen)
* [ ] Offline reload hiển thị danh sách mới nhất + badge “Offline”
* [ ] Online back → tự refresh dữ liệu trong vòng ≤ 5s
* [ ] Telegram nhận tin **ngay** sau tạo khách (≤ 1–2s)
* [ ] Logs có request_id; không lộ token; có retry & error handling
* [ ] Tài liệu cấu hình đầy đủ (env, quyền, hướng dẫn đổi BOT_TOKEN)

---

Nếu bạn đồng ý, mình có thể soạn ngay **mẫu file**:

* `src-pwa/custom-service-worker.js` (Workbox route + stale-while-revalidate + IndexedDB bridge),
* `src/pwa/db/guard-gate-db.ts` (Dexie schema),
* `app/utils/notifications.py` + patch `app/routers/guests.py` (BackgroundTasks),
* cùng với **README** cấu hình Telegram & PWA.
