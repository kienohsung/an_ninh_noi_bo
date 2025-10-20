<!-- File: frontend/src/pages/GuardGate.vue (Updated with PWA/Offline features) -->
<template>
  <q-page padding>
    <div class="row items-center justify-between q-mb-sm q-gutter-sm">
      <div class="text-h6">Cổng bảo vệ</div>
      <div class="row items-center q-gutter-sm">
        <!-- PWA/Offline Status Badge -->
        <q-badge v-if="offline" color="orange" text-color="black">
          <q-icon name="cloud_off" class="q-mr-xs" />
          Offline
        </q-badge>
        <div v-if="cachedAt" class="text-caption text-grey-7">
          Cache: {{ new Date(cachedAt).toLocaleString('vi-VN') }}
        </div>
        
        <!-- Audio Toggle Button -->
        <q-btn 
          flat 
          round 
          @click="toggleAudio"
          :icon="audioEnabled ? 'volume_up' : 'volume_off'"
          :color="audioEnabled ? 'positive' : 'grey-7'"
        >
          <q-tooltip>{{ audioEnabled ? 'Tắt thông báo' : 'Bật thông báo âm thanh' }}</q-tooltip>
        </q-btn>
        
        <!-- Search and Actions -->
        <q-input dense outlined v-model="q" placeholder="Tìm kiếm..." style="min-width: 280px" clearable @clear="load" @keyup.enter="load">
          <template #append><q-icon name="search" class="cursor-pointer" @click="load" /></template>
        </q-input>
        <q-btn-dropdown color="primary" label="Actions">
           <q-list>
            <q-item clickable v-close-popup @click="() => fileInputRef.click()" v-if="isAdmin || isManager">
              <q-item-section avatar><q-icon name="upload_file" /></q-item-section>
              <q-item-section>Import Excel</q-item-section>
            </q-item>
            <q-item clickable v-close-popup @click="exportGuests">
              <q-item-section avatar><q-icon name="download" /></q-item-section>
              <q-item-section>Export Excel</q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
         <q-btn label="Xóa dữ liệu" color="negative" @click="clearData" v-if="isAdmin" />
        <input type="file" ref="fileInputRef" @change="handleImport" accept=".xlsx, .xls" style="display:none" />
      </div>
    </div>
    <q-separator class="q-mb-md" />

    <q-card>
      <q-card-section>
        <div class="text-subtitle1">Khách chờ vào ({{ pending.length }})</div>
      </q-card-section>
      <q-separator/>
      <q-table
        :rows="pending"
        :columns="columns"
        row-key="id"
        flat
        dense
        :pagination="{ rowsPerPage: 20 }"
      >
        <template #body-cell-actions="props">
          <q-td :props="props">
            <q-btn color="primary" icon="check_circle" label="XÁC NHẬN VÀO" @click="confirmIn(props.row)" dense/>
          </q-td>
        </template>
      </q-table>
    </q-card>

    <q-card class="q-mt-lg">
       <q-card-section>
        <div class="text-subtitle1">Đã xác nhận vào</div>
      </q-card-section>
      <q-separator/>
      <q-table
        :rows="checkedIn"
        :columns="checkedInColumns"
        row-key="id"
        flat
        dense
        :pagination="{ rowsPerPage: 10 }"
      />
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useQuasar, exportFile as qExportFile } from 'quasar' 
import api from '../api'
import { useAuthStore } from '../stores/auth'
// PWA Imports
import { getGuestsSnapshot, saveGuestsSnapshot, enqueueConfirm, drainQueue } from '../pwa/db/guard-gate-db'
import { registerServiceWorker } from '../register-sw'

const $q = useQuasar()
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')
const isManager = computed(() => auth.user?.role === 'manager')

const pending = ref([])
const checkedIn = ref([])
const q = ref('')
const fileInputRef = ref(null)
let timer = null

// --- PWA State Refs ---
const cachedAt = ref(null)
const offline = ref(false)

// --- Audio Notification Logic ---
const audioEnabled = ref(localStorage.getItem('guard_audio_enabled') === 'true');
const previousPendingCount = ref(0)
let notificationSound = null

function toggleAudio() {
  if (!notificationSound) {
    notificationSound = new Audio('/notification.mp3');
  }
  
  audioEnabled.value = !audioEnabled.value;
  localStorage.setItem('guard_audio_enabled', audioEnabled.value);

  if (audioEnabled.value) {
    $q.notify({
      type: 'positive',
      icon: 'volume_up',
      message: 'Đã bật thông báo âm thanh.',
      position: 'top'
    });
    notificationSound.play().catch(e => console.error("Audio play failed on toggle:", e));
  } else {
    $q.notify({
      type: 'info',
      icon: 'volume_off',
      message: 'Đã tắt thông báo âm thanh.',
      position: 'top'
    });
  }
}

const columns = [
  { name: 'full_name', align: 'left', label: 'Họ tên', field: 'full_name', sortable: true },
  { name: 'id_card_number', align: 'left', label: 'CCCD', field: 'id_card_number', sortable: true },
  { name: 'supplier_name', align: 'left', label: 'Nhà cung cấp', field: 'supplier_name', sortable: true },
  { name: 'reason', align: 'left', label: 'Chi tiết', field: 'reason', sortable: true, style: 'max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;' },
  { name: 'license_plate', align: 'left', label: 'Biển số', field: 'license_plate', sortable: true },
  { name: 'registered_by_name', align: 'left', label: 'Người đăng ký', field: 'registered_by_name', sortable: true },
  { name: 'created_at', align: 'left', label: 'Ngày đăng ký', field: 'created_at', sortable: true, format: val => val ? new Date(val).toLocaleString('vi-VN') : '' },
  { name: 'check_in_time', align: 'left', label: 'Giờ vào', field: 'check_in_time', sortable: true, format: val => val ? new Date(val).toLocaleString('vi-VN') : '' },
  { name: 'actions', label: '', field: 'actions', align: 'right' }
]

const checkedInColumns = computed(() => columns.filter(col => col.name !== 'actions'))

async function load () {
  const userId = auth.user?.id || 'anon'
  try {
    const res = await api.get('/guests', { params: { q: q.value || undefined, include_all_my_history: true } })
    const rows = res.data || []
    
    const newPendingCount = rows.filter(r => r.status === 'pending').length;
    if (audioEnabled.value && notificationSound && newPendingCount > previousPendingCount.value) {
      notificationSound.play().catch(e => console.error("Audio play failed on new guest:", e));
    }
    previousPendingCount.value = newPendingCount;

    pending.value = rows.filter(r => r.status === 'pending')
    checkedIn.value = rows.filter(r => r.status === 'checked_in')

    // FIX: Convert reactive arrays to plain JS objects before saving to Dexie
    const plainPending = JSON.parse(JSON.stringify(pending.value));
    const plainCheckedIn = JSON.parse(JSON.stringify(checkedIn.value));
    await saveGuestsSnapshot(userId, { pending: plainPending, checkedIn: plainCheckedIn });

    cachedAt.value = new Date().toISOString()
    offline.value = false // We are online if this succeeds

  } catch (error) {
    if(timer) clearInterval(timer);
    // Only show notification if it's a real network error, not Dexie error
    if (error.name !== 'DexieError') {
      $q.notify({type: 'negative', message: 'Không tải được danh sách khách. Đã tạm dừng tự động làm mới.'})
    }
    console.error("Failed to load guests", error)
    offline.value = true // Assume offline on network error
  }
}

async function confirmIn (row) {
  // Offline handling
  if (!navigator.onLine) {
    await enqueueConfirm(row.id)
    $q.notify({ type:'warning', message: 'Đã xếp hàng xác nhận. Sẽ đồng bộ khi online.'})

    // UX IMPROVEMENT: Optimistic UI Update
    const index = pending.value.findIndex(p => p.id === row.id);
    if (index > -1) {
        const [confirmedGuest] = pending.value.splice(index, 1);
        confirmedGuest.status_display = 'Chờ đồng bộ'; // temporary status
        checkedIn.value.unshift(confirmedGuest); // Add to top of checkedIn list
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
    load()
  } catch(error) {
     $q.notify({type: 'negative', message: 'Xác nhận thất bại.'})
  }
}

// --- New PWA Function ---
async function flushQueue() {
  await drainQueue(async (item) => {
    if (item.type === 'confirmIn') {
      await api.post(`/guests/${item.payload.guestId}/confirm-in`)
    }
  })
  // After flushing, reload data from network
  await load()
}

// --- Existing Functions (handleImport, exportGuests, clearData) are unchanged ---
async function handleImport(event) {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)
  $q.loading.show({ message: 'Đang xử lý file...' })
  try {
    await api.post('/guests/import/xlsx', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    $q.notify({ type: 'positive', message: 'Import thành công!' })
    load()
  } catch (error) {
    const detail = error.response?.data?.detail || 'Import thất bại. Vui lòng kiểm tra file.'
    $q.notify({ type: 'negative', message: detail })
  } finally {
    $q.loading.hide()
    event.target.value = ''
  }
}

async function exportGuests() {
  try {
    $q.loading.show({ message: 'Đang tạo file...' });
    const response = await api.get('/guests/export/xlsx', { responseType: 'blob' });
    const filename = `guests_export_${new Date().toISOString().slice(0, 10)}.xlsx`;
    
    const status = qExportFile(filename, response.data, {
      mimeType: response.headers['content-type']
    });

    if (status !== true) {
      $q.notify({
        type: 'negative',
        message: 'Trình duyệt đã chặn việc tải file.'
      });
    }
  } catch (error) {
    console.error("Export failed:", error);
    $q.notify({ type: 'negative', message: 'Export thất bại.' });
  } finally {
    $q.loading.hide();
  }
}

function clearData() {
  $q.dialog({
    title: 'Xác nhận xóa TOÀN BỘ DỮ LIỆU',
    message: 'Hành động này không thể hoàn tác. Vui lòng nhập mật khẩu để xác nhận:',
    prompt: {
      model: '',
      type: 'password'
    },
    cancel: true,
    persistent: true
  }).onOk(async (password) => {
    if (password === 'Kienhp@@123') {
      try {
        await api.post('/guests/clear')
        $q.notify({ type: 'positive', message: 'Đã xóa toàn bộ dữ liệu khách.' })
        load()
      } catch (error) {
        $q.notify({ type: 'negative', message: 'Xóa dữ liệu thất bại.' })
      }
    } else {
      $q.notify({ type: 'negative', message: 'Sai mật khẩu.' })
    }
  })
}


onMounted(async () => {
  // Initialize audio object
  notificationSound = new Audio('/notification.mp3');
  if (audioEnabled.value) {
    $q.notify({
      type: 'info',
      icon: 'volume_up',
      message: 'Thông báo âm thanh đang được bật.',
      position: 'top',
      timeout: 2500
    });
  }
  
  // --- PWA Initialization Logic ---
  registerServiceWorker()
  
  // 1. Load snapshot from local DB first for instant UI
  const userId = auth.user?.id || 'anon'
  const snap = await getGuestsSnapshot(userId)
  if (snap?.data) {
    pending.value = snap.data.pending || []
    checkedIn.value = snap.data.checkedIn || []
    cachedAt.value = snap.cachedAt
    offline.value = !navigator.onLine
  }
  
  // 2. Then fetch fresh data from network if online
  if (navigator.onLine) {
    await load()
  }
  previousPendingCount.value = pending.value.length;
  
  // 3. Listen for messages from Service Worker (for cache updates, background sync)
  navigator.serviceWorker?.addEventListener('message', async (e) => {
    const { type } = e.data || {}
    if (type === 'GUESTS_REFRESHED') {
      await load() // SW informs that network data is fresh, reload UI
    }
    if (type === 'SYNC_CONFIRM') {
      await flushQueue() // SW informs that a background sync is triggered
    }
  })
  
  // 4. Listen for browser coming back online to flush the queue
  window.addEventListener('online', flushQueue)

  // Start polling timer
  timer = setInterval(load, 5000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  // Clean up event listeners if needed, though Vue handles most of it.
  window.removeEventListener('online', flushQueue);
})
</script>

