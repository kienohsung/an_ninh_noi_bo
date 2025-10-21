<!-- File: frontend/src/pages/GuardGate.vue (Updated with PWA/Offline features) -->
<template>
  <q-page class="q-pa-md bg-grey-2">
    <!-- Header -->
    <div class="row items-center justify-between q-mb-md">
      <div class="col-auto">
        <div class="text-h5 text-bold">Cổng Bảo Vệ</div>
        <div class="text-caption text-grey-7">Quản lý khách chờ và đã vào cổng</div>
      </div>
      <div class="col-auto row items-center q-gutter-sm">
        <q-input dense outlined v-model="q" placeholder="Tìm kiếm..." style="min-width: 250px" clearable @clear="load" @keyup.enter="load">
          <template #append><q-icon name="search" /></template>
        </q-input>
        <q-btn 
          flat 
          round 
          @click="toggleAudio"
          :icon="audioEnabled ? 'volume_up' : 'volume_off'"
          :color="audioEnabled ? 'positive' : 'grey-8'"
        >
          <q-tooltip>{{ audioEnabled ? 'Tắt âm báo' : 'Bật âm báo khách mới' }}</q-tooltip>
        </q-btn>
        <q-badge v-if="offline" color="orange" text-color="black" class="q-pa-sm">
          <q-icon name="cloud_off" class="q-mr-xs" />
          Offline
          <q-tooltip>Đang ở chế độ ngoại tuyến. Dữ liệu có thể đã cũ.</q-tooltip>
        </q-badge>
      </div>
    </div>

    <!-- Bảng: Khách đang chờ vào -->
    <q-card class="q-mb-lg">
       <q-card-section class="bg-primary text-white">
        <div class="text-subtitle1 text-bold">Khách Chờ Vào ({{ pending.length }})</div>
      </q-card-section>
      <q-separator />
      <q-table
        :rows="pending"
        :columns="pendingColumns"
        row-key="id"
        flat
        :pagination="{ rowsPerPage: 20 }"
        :loading="loading"
      >
        <template #body-cell-actions="props">
          <q-td :props="props">
            <q-btn color="positive" icon="login" label="Xác nhận vào" @click="confirmIn(props.row)" dense/>
          </q-td>
        </template>
        <template #no-data>
            <div class="full-width row flex-center text-positive q-gutter-sm q-pa-md">
                <q-icon size="2em" name="check_circle" />
                <span>Không có khách nào đang chờ.</span>
            </div>
        </template>
      </q-table>
    </q-card>

    <!-- Bảng: Khách đã vào trong ngày -->
     <q-card>
       <q-card-section class="bg-blue-grey-8 text-white">
        <div class="text-subtitle1 text-bold">Khách Đã Vào</div>
      </q-card-section>
      <q-separator />
      <q-table
        :rows="checkedIn"
        :columns="checkedInColumns"
        row-key="id"
        flat
        :pagination="{ rowsPerPage: 10 }"
        :loading="loading"
      />
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useQuasar } from 'quasar' 
import api from '../api'
import { useAuthStore } from '../stores/auth'
// PWA Imports (giữ nguyên)
import { getGuestsSnapshot, saveGuestsSnapshot, enqueueConfirm, drainQueue } from '../pwa/db/guard-gate-db'
import { registerServiceWorker } from '../register-sw'

const $q = useQuasar()
const auth = useAuthStore()
const loading = ref(false)

const pending = ref([])
const checkedIn = ref([])
const q = ref('')
let timer = null

// --- PWA State Refs (giữ nguyên) ---
const cachedAt = ref(null)
const offline = ref(false)

// --- Audio Notification Logic (giữ nguyên) ---
const audioEnabled = ref(localStorage.getItem('guard_audio_enabled') === 'true');
const previousPendingCount = ref(0)
let notificationSound = null

function toggleAudio() {
  if (!notificationSound) {
    notificationSound = new Audio('/notification.mp3');
  }
  
  audioEnabled.value = !audioEnabled.value;
  localStorage.setItem('guard_audio_enabled', audioEnabled.value);

  const message = audioEnabled.value ? 'Đã bật thông báo âm thanh.' : 'Đã tắt thông báo âm thanh.';
  const icon = audioEnabled.value ? 'volume_up' : 'volume_off';

  $q.notify({ type: 'info', icon, message, position: 'top' });

  if (audioEnabled.value) {
    notificationSound.play().catch(e => console.error("Audio play failed on toggle:", e));
  }
}

// --- ĐỊNH NGHĨA CỘT MỚI ---
const baseColumns = [
  { name: 'full_name', align: 'left', label: 'Họ tên', field: 'full_name', sortable: true },
  { name: 'id_card_number', align: 'left', label: 'CCCD', field: 'id_card_number', sortable: true },
  { name: 'supplier_name', align: 'left', label: 'Nhà cung cấp', field: 'supplier_name', sortable: true },
  { name: 'reason', align: 'left', label: 'Chi tiết', field: 'reason', sortable: true, style: 'max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;' },
  { name: 'license_plate', align: 'left', label: 'Biển số', field: 'license_plate', sortable: true },
  { name: 'registered_by_name', align: 'left', label: 'Người đăng ký', field: 'registered_by_name', sortable: true },
  { name: 'created_at', align: 'left', label: 'Ngày đăng ký', field: 'created_at', sortable: true, format: val => val ? new Date(val).toLocaleString('vi-VN') : '' },
];

const pendingColumns = [
  // Cột "actions" được đưa lên đầu tiên
  { name: 'actions', label: 'Hành động', field: 'actions', align: 'left' },
  ...baseColumns
];

const checkedInColumns = [
    ...baseColumns,
    // Thêm cột giờ vào cho bảng đã check-in
    { name: 'check_in_time', align: 'left', label: 'Giờ vào', field: 'check_in_time', sortable: true, format: val => val ? new Date(val).toLocaleString('vi-VN') : '' },
];


async function load () {
  loading.value = true;
  const userId = auth.user?.id || 'anon'
  try {
    const res = await api.get('/guests', { params: { q: q.value || undefined, status: 'pending,checked_in' } })
    const rows = res.data || []
    
    const newPendingCount = rows.filter(r => r.status === 'pending').length;
    if (audioEnabled.value && notificationSound && newPendingCount > previousPendingCount.value) {
      notificationSound.play().catch(e => console.error("Audio play failed on new guest:", e));
    }
    previousPendingCount.value = newPendingCount;

    pending.value = rows.filter(r => r.status === 'pending')
    checkedIn.value = rows.filter(r => r.status === 'checked_in')

    // Lưu cache PWA (giữ nguyên)
    const plainPending = JSON.parse(JSON.stringify(pending.value));
    const plainCheckedIn = JSON.parse(JSON.stringify(checkedIn.value));
    await saveGuestsSnapshot(userId, { pending: plainPending, checkedIn: plainCheckedIn });

    cachedAt.value = new Date().toISOString()
    offline.value = false

  } catch (error) {
    if (error.name !== 'DexieError') {
      $q.notify({type: 'negative', message: 'Không tải được danh sách khách.'})
    }
    console.error("Failed to load guests", error)
    offline.value = true
  } finally {
    loading.value = false;
  }
}

async function confirmIn (row) {
  // Offline handling (giữ nguyên)
  if (!navigator.onLine) {
    await enqueueConfirm(row.id)
    $q.notify({ type:'warning', message: 'Đã xếp hàng xác nhận. Sẽ đồng bộ khi online.'})
    const index = pending.value.findIndex(p => p.id === row.id);
    if (index > -1) {
        const [confirmedGuest] = pending.value.splice(index, 1);
        checkedIn.value.unshift(confirmedGuest);
    }
    try { 
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('sync-confirm') 
    } catch(e){
      console.error('Background Sync registration failed:', e);
    }
    return
  }
  
  // Online handling
  try {
    await api.post(`/guests/${row.id}/confirm-in`)
    $q.notify({type: 'positive', message: `${row.full_name} đã được xác nhận vào.`})
    load() // Tải lại dữ liệu sau khi xác nhận
  } catch(error) {
     $q.notify({type: 'negative', message: 'Xác nhận thất bại.'})
  }
}

// --- PWA Function (giữ nguyên) ---
async function flushQueue() {
  await drainQueue(async (item) => {
    if (item.type === 'confirmIn') {
      await api.post(`/guests/${item.payload.guestId}/confirm-in`)
    }
  })
  await load()
}

// --- Lifecycle hooks (giữ nguyên) ---
onMounted(async () => {
  notificationSound = new Audio('/notification.mp3');
  
  registerServiceWorker()
  
  const userId = auth.user?.id || 'anon'
  const snap = await getGuestsSnapshot(userId)
  if (snap?.data) {
    pending.value = snap.data.pending || []
    checkedIn.value = snap.data.checkedIn || []
    cachedAt.value = snap.cachedAt
    offline.value = !navigator.onLine
  }
  
  if (navigator.onLine) {
    await load()
  }
  previousPendingCount.value = pending.value.length;
  
  navigator.serviceWorker?.addEventListener('message', async (e) => {
    const { type } = e.data || {}
    if (type === 'GUESTS_REFRESHED' || type === 'SYNC_CONFIRM') {
      await flushQueue()
    }
  })
  
  window.addEventListener('online', flushQueue)

  timer = setInterval(load, 15000) // Tăng thời gian polling lên 15 giây
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  window.removeEventListener('online', flushQueue);
})
</script>

<style lang="scss" scoped>
// Thêm một chút style để giao diện thoáng hơn
.q-page {
  max-width: 1400px;
  margin: 0 auto;
}
</style>



