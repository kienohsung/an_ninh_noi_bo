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
export async function drainQueue(flushFn) {
  const all = await db.queue.toArray();
  for (const item of all) {
    try {
      await flushFn(item);
      await db.queue.delete(item.id);
    } catch (e) {
      // stop on first failure to retry later
      break;
    }
  }
}
export default db;
