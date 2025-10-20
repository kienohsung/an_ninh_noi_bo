// File: frontend/public/sw.js
const CACHE_NAME = 'guardgate-cache-v1';
const API_MATCH = /\/guests(\?|$)/;
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE_NAME));
});
self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});
// Notify clients helper
async function broadcast(type, payload) {
  const clients = await self.clients.matchAll({ includeUncontrolled: true, type: 'window' });
  for (const client of clients) {
    client.postMessage({ type, payload });
  }
}
// Cache GET /guests with network-first + fallback to cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method === 'GET' && API_MATCH.test(new URL(request.url).pathname)) {
    event.respondWith((async () => {
      try {
        const net = await fetch(request);
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, net.clone());
        broadcast('GUESTS_REFRESHED', { url: request.url });
        return net;
      } catch (e) {
        const cache = await caches.open(CACHE_NAME);
        const match = await cache.match(request);
        if (match) return match;
        throw e;
      }
    })());
  }
});
// Background Sync: just ping clients to flush their queues
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-confirm') {
    event.waitUntil(broadcast('SYNC_CONFIRM', {}));
  }
});
