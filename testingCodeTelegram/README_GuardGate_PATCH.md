# Apply changes in `frontend/src/pages/GuardGate.vue`
- Import: 
  ```js
  import { getGuestsSnapshot, saveGuestsSnapshot, enqueueConfirm, drainQueue } from '../pwa/db/guard-gate-db'
  import { registerServiceWorker } from '../register-sw'
  ```
- On mounted:
  ```js
  registerServiceWorker()
  // Load snapshot first
  const userId = auth.user?.id || 'anon'
  const snap = await getGuestsSnapshot(userId)
  if (snap?.data) {
    pending.value = snap.data.pending || []
    checkedIn.value = snap.data.checkedIn || []
    cachedAt.value = snap.cachedAt
    offline.value = !navigator.onLine
  }
  // Then fetch from network if online
  if (navigator.onLine) await load()
  // Listen SW messages
  navigator.serviceWorker?.addEventListener('message', async (e) => {
    const { type } = e.data || {}
    if (type === 'GUESTS_REFRESHED') {
      await load()
    }
    if (type === 'SYNC_CONFIRM') {
      await flushQueue()
    }
  })
  window.addEventListener('online', flushQueue)
  ```
- New refs:
  ```js
  const cachedAt = ref(null)
  const offline = ref(false)
  ```
- After successful `load()` from API:
  ```js
  await saveGuestsSnapshot(userId, { pending: pending.value, checkedIn: checkedIn.value })
  cachedAt.value = new Date().toISOString()
  ```
- Modify `confirmIn(row)`:
  ```js
  if (!navigator.onLine) {
    await enqueueConfirm(row.id)
    $q.notify({ type:'warning', message: 'Đã xếp hàng xác nhận. Sẽ đồng bộ khi online.'})
    try { await (await navigator.serviceWorker.ready).sync.register('sync-confirm') } catch(e){}
    return
  }
  await api.post(`/guests/${row.id}/confirm-in`)
  load()
  ```
- Add `async function flushQueue()`:
  ```js
  async function flushQueue() {
    await drainQueue(async (item) => {
      if (item.type === 'confirmIn') {
        await api.post(`/guests/${item.payload.guestId}/confirm-in`)
      }
    })
    await load()
  }
  ```
- UI badge (somewhere at page header):
  ```html
  <q-badge v-if="!navigator.onLine" color="orange" text-color="black" class="q-ml-md">Offline</q-badge>
  <div v-if="cachedAt" class="text-caption">Snapshot: {{ new Date(cachedAt).toLocaleString() }}</div>
  ```
