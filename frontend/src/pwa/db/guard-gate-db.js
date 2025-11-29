// File: frontend/src/pwa/db/guard-gate-db.js
import Dexie from "dexie";
const db = new Dexie('guardGateDB');
db.version(1).stores({
  snapshots: '&key, data, cachedAt',
  queue: '++id, type, payload, createdAt'
});
export async function saveGuestsSnapshot(userId, data) {
  const key = `guests:list:${userId}`;
  await db.snapshots.put({ key, data, cachedAt: new Date().toISOString() });
}
export async function getGuestsSnapshot(userId) {
  const key = `guests:list:${userId}`;
  return db.snapshots.get(key);
}
export async function enqueueConfirm(guestId) {
  await db.queue.add({ type: 'confirmIn', payload: { guestId }, createdAt: Date.now() });
}
// === CHECKLIST 4.5 (Phần 1): Thêm hàm xếp hàng cho Tài sản ===
export async function enqueueAssetCheckOut(assetId) {
  await db.queue.add({ 
    type: 'ASSET_CHECKOUT', // Giống trong kế hoạch
    payload: { assetId }, 
    createdAt: Date.now() 
  });
}

export async function enqueueAssetReturn(assetId) {
  await db.queue.add({ 
    type: 'ASSET_RETURN', // Giống trong kế hoạch
    payload: { assetId }, 
    createdAt: Date.now() 
  });
}
// === KẾT THÚC CHECKLIST 4.5 (Phần 1) ===

// === CHECKLIST 4.5 (Phần 2): Cập nhật drainQueue để xử lý Tài sản ===
export async function drainQueue(flushFn) {
  // Sửa: Dùng orderBy('createdAt') để đảm bảo thứ tự
  const all = await db.queue.orderBy('createdAt').toArray(); 
  
  for (const item of all) {
    try {
      // flushFn (sẽ được định nghĩa trong GuardGate.vue) 
      // sẽ gọi đúng API dựa trên item.type
      await flushFn(item);
      
      // Chỉ xóa khỏi hàng đợi nếu flushFn thành công
      await db.queue.delete(item.id);
    } catch (e) {
      // stop on first failure to retry later
      // Sửa: Thêm log lỗi
      console.error('PWA drainQueue failed for item:', item, e);
      break; 
    }
  }
}
