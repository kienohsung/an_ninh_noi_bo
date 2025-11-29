# Tài Liệu Tổng Hợp Lỗi và Giải Pháp

> **Mục đích:** Lưu trữ kinh nghiệm xử lý lỗi để tham khảo cho các cải tiến sau  
> **Cập nhật lần cuối:** 29/11/2025

---

## 📋 Mục Lục

1. [Lỗi Màn Hình Trắng (White Screen)](#1-lỗi-màn-hình-trắng-white-screen)
2. [Lỗi Upload và Hiển Thị Ảnh](#2-lỗi-upload-và-hiển-thị-ảnh)
3. [Lỗi Duplicate Note trong Device](#3-lỗi-duplicate-note-trong-device)
4. [Lỗi Database Schema Mismatch](#4-lỗi-database-schema-mismatch)
5. [Lỗi Task List Không Load](#5-lỗi-task-list-không-load)
6. [Best Practices](#6-best-practices)

---

## 1. Lỗi Màn Hình Trắng (White Screen)

### 🔴 Triệu chứng
- Màn hình trắng tinh khi truy cập ứng dụng
- Chỉ hoạt động với trình duyệt ẩn danh
- Sau một thời gian sử dụng thì bị lỗi

### 🔍 Nguyên nhân
**Sai lầm ban đầu:** Nghĩ là do Service Worker cache  
**Nguyên nhân thực sự:** Expired authentication tokens không được xử lý đúng

#### Chi tiết:
1. Token và refresh token hết hạn sau thời gian dùng
2. `auth.bootstrap()` trong `main.js` gọi `/me` → 401 Unauthorized
3. Code catch error nhưng **KHÔNG xử lý** → app stuck → white screen
4. Invalid tokens vẫn còn trong localStorage

### ✅ Giải pháp

#### File: `frontend/src/stores/auth.js`

**Fix 1: Handle expired tokens trong bootstrap()**
```javascript
async bootstrap() {
  if (!this.token) return
  try {
    const me = await api.get('/me')
    this.user = me.data
  } catch (e) {
    // ✅ Clear expired tokens
    console.error("Bootstrap failed - tokens may be expired", e)
    this.logout()  // Xóa tokens hết hạn
    // Không throw error - cho phép app mount về login
  }
}
```

**Fix 2: Auto-detect invalid tokens ngay từ state initialization**
```javascript
state: () => {
  const token = localStorage.getItem('token');
  const refreshToken = localStorage.getItem('refreshToken');
  
  // Validate tokens
  const isValidToken = token && token !== 'null' && token !== 'undefined' && token.trim() !== '';
  const isValidRefreshToken = refreshToken && refreshToken !== 'null' && refreshToken !== 'undefined' && refreshToken.trim() !== '';
  
  // Auto-clear invalid tokens
  if ((token && !isValidToken) || (refreshToken && !isValidRefreshToken)) {
    console.warn('Invalid tokens detected in localStorage, clearing...');
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
  }
  
  return {
    user: null,
    token: isValidToken ? token : null,
    refreshToken: isValidRefreshToken ? refreshToken : null,
  }
}
```

### 📝 Console Errors để nhận diện
```
GET http://IP:8001/me 401 (Unauthorized)
POST http://IP:8001/token/refresh 401 (Unauthorized)
```

### 🛠️ Cách fix khẩn cấp cho user
```javascript
// Paste vào Console (F12)
localStorage.clear(); location.reload();
```

---

## 2. Lỗi Upload và Hiển Thị Ảnh

### 🔴 Triệu chứng (28/11/2025)
- Ảnh không được upload lên Google Sheets
- Popup device maintenance không hiển thị ảnh
- Dữ liệu ảnh không được lưu vào backend

### 🔍 Nguyên nhân
- Frontend không chuyển đổi đúng ảnh sang base64
- Backend `Service_Device.js` không nhận hoặc lưu image data
- Modal popup không retrieve đúng image paths

### ✅ Giải pháp
- Verify frontend image handling và base64 conversion
- Check backend routes xử lý image upload
- Ensure modal popup đọc đúng image data từ response

---

## 3. Lỗi Duplicate Note trong Device

### 🔴 Triệu chứng (28/11/2025)
- Field 'note' bị duplicate khi edit device và thêm note mới
- Notes không được prepend đúng vào Description column
- Device Detail popup hiển thị notes bị trùng lặp

### 🔍 Nguyên nhân
- Logic prepend note không xử lý duplicate
- Description column và note column không sync đúng
- Display logic ghép notes từ nhiều nguồn không handle trùng lặp

### ✅ Giải pháp
- Fix prepend logic để kiểm tra duplicate trước khi thêm
- Sync đúng giữa Description và note columns
- Display notes với newline separation và deduplication

---

## 4. Lỗi Database Schema Mismatch

### 🔴 Triệu chứng (21-23/11/2025)
- 500 Internal Server Error khi login
- `sqlite3.IntegrityError: NOT NULL constraint failed`
- Thiếu tables hoặc columns sau khi replace database file

### 🔍 Nguyên nhân
- Database schema không khớp với application models
- Missing tables: `asset_images`
- Missing columns: `asset_description`, `employee_code`, `department`, `registered_by_user_id`

### ✅ Giải pháp
- Chạy migration scripts để sync schema
- Thêm missing tables/columns
- Verify model definitions khớp với database

### 📝 Migration pattern
```python
# Kiểm tra và thêm missing columns
if 'column_name' not in [col['name'] for col in cursor.fetchall()]:
    cursor.execute("ALTER TABLE table_name ADD COLUMN column_name TYPE")
```

---

## 5. Lỗi Task List Không Load

### 🔴 Triệu chứng (28/11/2025)
- Task list trên dashboard hiển thị blank
- Không load được dữ liệu tasks
- Data fetching process fails

### 🔍 Nguyên nhân
- Bug trong data fetching logic
- Google Sheet API connection issues
- Frontend rendering bug

### ✅ Giải pháp
- Debug data fetching chain từ Google Sheet → Backend → Frontend
- Check API credentials và permissions
- Verify rendering logic handles empty/error states

---

## 6. Best Practices

### 🎯 Authentication & Session Management

#### ✅ DO:
- **Luôn validate tokens** trước khi sử dụng
- **Auto-clear invalid data** từ localStorage
- **Handle 401 gracefully** - redirect về login, không bao giờ white screen
- **Log errors** với context đầy đủ để debug

#### ❌ DON'T:
- Để expired tokens tồn tại trong localStorage
- Catch error mà không xử lý
- Assume tokens luôn valid
- Hardcode passwords trong frontend (bảo mật yếu)

### 🎯 Error Handling Pattern

```javascript
// ✅ GOOD
try {
  const result = await apiCall()
  return result
} catch (error) {
  console.error('Descriptive error message', error)
  // Xử lý error: clear state, notify user, redirect, etc.
  handleError(error)
}

// ❌ BAD
try {
  const result = await apiCall()
  return result
} catch (error) {
  console.error(error) // Chỉ log, không xử lý
}
```

### 🎯 LocalStorage Management

```javascript
// ✅ GOOD - Validate before use
const token = localStorage.getItem('token')
const isValid = token && token !== 'null' && token !== 'undefined' && token.trim() !== ''
if (!isValid) {
  localStorage.removeItem('token')
}

// ❌ BAD - Assume data is valid
const token = localStorage.getItem('token')
if (token) {
  useToken(token) // Có thể là 'null' string!
}
```

### 🎯 Database Migrations

```python
# ✅ GOOD - Check trước khi alter
cursor.execute("PRAGMA table_info(table_name)")
columns = [col[1] for col in cursor.fetchall()]
if 'new_column' not in columns:
    cursor.execute("ALTER TABLE table_name ADD COLUMN new_column TYPE")

# ❌ BAD - Alter trực tiếp
cursor.execute("ALTER TABLE table_name ADD COLUMN new_column TYPE")
# Sẽ fail nếu column đã tồn tại
```

### 🎯 Service Worker Caching

```javascript
// ✅ GOOD - Version và cleanup
const CACHE_NAME = 'app-cache-v2'
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(names => 
      Promise.all(
        names.filter(name => name !== CACHE_NAME)
             .map(name => caches.delete(name))
      )
    )
  )
})

// ❌ BAD - Không cleanup old caches
const CACHE_NAME = 'app-cache-v1'
// Old caches tồn tại mãi mãi
```

---

## 📊 Thống Kê Lỗi

| Loại lỗi | Tần suất | Độ nghiêm trọng | Thời gian fix |
|-----------|----------|-----------------|---------------|
| Authentication/Token | Cao | 🔴 Critical | 2-3 giờ |
| Database Schema | Trung bình | 🟡 High | 1-2 giờ |
| Upload/Display | Thấp | 🟢 Medium | 1 giờ |
| UI/UX bugs | Thấp | 🟢 Low | 30 phút |

---

## 🔄 Quy Trình Debug Chuẩn

1. **Thu thập thông tin**
   - Console errors (F12 → Console)
   - Network requests (F12 → Network)
   - Backend logs
   - Reproduce steps

2. **Phân tích**
   - Xác định scope: Frontend? Backend? Database?
   - Tìm root cause, không chỉ symptoms
   - Check recent changes

3. **Giải pháp**
   - Fix nhỏ nhất có thể
   - Test thoroughly
   - Document fix trong file này

4. **Prevention**
   - Thêm validation/error handling
   - Update best practices
   - Code review

---

## 📞 Liên Hệ & Tham Khảo

- **Project Directory:** `c:\Users\mrKienIT\Desktop\python\coding\testing\an_ninh_noi_bo`
- **Backend Port:** 8001
- **Frontend Dev Port:** 5174 (dev), 5173 (prod)
- **Database:** SQLite (`security_v2_3.db`)

---

**Lưu ý:** Tài liệu này nên được cập nhật mỗi khi gặp và fix lỗi mới. Giúp team tránh lặp lại sai lầm và tiết kiệm thời gian debug!
