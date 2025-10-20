# GuardGate PWA + Offline + Background Sync

This patch adds:
- Service Worker (`public/sw.js`)
- Dexie-based cache & queue (`src/pwa/db/guard-gate-db.js`)
- SW registration (`src/register-sw.js`)
- GuardGate.vue integration (see patch instructions: `README_GuardGate_PATCH.md`)

## Dev/Prod
- Dev: http://192.168.223.176:5174
- Prod: http://192.168.223.176:5173

## Notes
- Background Sync may not be supported in all browsers; the page also flushes when `online` event fires.
- CORS is kept as current (5173/5174).
