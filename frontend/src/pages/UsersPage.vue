<!-- File: security_mgmt_dev/frontend/src/pages/UsersPage.vue -->
<template>
  <q-page padding>
    <q-card>
      <q-card-section class="row items-center justify-between">
        <div class="text-subtitle1">Người dùng</div>
        <div class="row items-center q-gutter-sm">
          <q-input dense outlined v-model="q" @update:model-value="load" placeholder="Tìm kiếm..." style="width: 280px">
            <template #append><q-icon name="search"/></template>
          </q-input>
          <!-- Sửa: Nút Thêm và Xóa -->
          <q-btn label="Thêm" color="primary" @click="openAddUserDialog" v-if="isAdmin"/>
          <q-btn-dropdown color="secondary" label="Actions" v-if="isAdmin">
            <q-list>
              <q-item clickable v-close-popup @click="() => importRef.click()">
                <q-item-section avatar><q-icon name="upload_file"/></q-item-section>
                <q-item-section>Import Excel</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="exportUsers">
                <q-item-section avatar><q-icon name="download"/></q-item-section>
                <q-item-section>Export Excel</q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
          <q-btn label="Xóa dữ liệu" color="negative" @click="clearData" v-if="isAdmin"/>
          <input type="file" ref="importRef" @change="handleImport" accept=".xlsx" hidden/>
        </div>
      </q-card-section>
      <q-separator/>
      <q-card-section>
        <q-table :rows="rows" :columns="columns" row-key="id" flat>
          <template #body-cell-actions="props">
            <q-td :props="props">
              <!-- Sửa: Nút Sửa -->
              <q-btn flat icon="edit" @click="openEditUserDialog(props.row)" :disable="!isAdmin"/>
              <q-btn flat icon="delete" color="negative" @click="delUser(props.row)" :disable="!isAdmin"/>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Dialog mới cho việc Thêm/Sửa User -->
    <q-dialog v-model="dlgUser">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">{{ editMode ? 'Chỉnh sửa người dùng' : 'Thêm người dùng mới' }}</div>
        </q-card-section>
        <q-separator/>
        <q-card-section>
          <q-form @submit="saveUser" class="q-gutter-md">
            <q-input v-model="activeUser.username" label="Mã NV (Username)" dense outlined required
                     :rules="[val => !!val || 'Bắt buộc']" :readonly="editMode"/>
            <q-input v-model="activeUser.full_name" label="Họ tên" dense outlined required
                     :rules="[val => !!val || 'Bắt buộc']"/>
            <q-input v-model="activeUser.password" :label="editMode ? 'Mật khẩu mới (để trống nếu không đổi)' : 'Mật khẩu'"
                     type="password" dense outlined :required="!editMode"
                     :rules="[val => !editMode ? !!val : true || 'Bắt buộc']"/>
            <q-select v-model="activeUser.role" :options="['admin', 'manager', 'guard', 'staff']"
                      label="Vai trò" dense outlined required :rules="[val => !!val || 'Bắt buộc']"/>
            <div class="q-pt-md">
              <q-btn type="submit" label="Lưu" color="primary"/>
              <q-btn flat label="Hủy" v-close-popup class="q-ml-sm"/>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useQuasar, exportFile as qExportFile } from 'quasar'
import api from '../api'
import { useAuthStore } from '../stores/auth'


const $q = useQuasar()
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')

const rows = ref([])
const q = ref('')
const importRef = ref(null)

// --- State mới cho Dialog ---
const dlgUser = ref(false)
const editMode = ref(false)
const activeUser = reactive({
  id: null,
  username: '',
  full_name: '',
  password: '',
  role: 'staff'
})

const columns = [
  { name: 'username', label: 'Mã NV', field: 'username', align: 'left', sortable: true },
  { name: 'full_name', label: 'Họ tên', field: 'full_name', align: 'left', sortable: true },
  { name: 'role', label: 'Vai trò', field: 'role', align: 'left', sortable: true },
  { name: 'actions', label: '', field: 'actions' }
]

async function load () {
  try {
    const res = await api.get('/users', { params: { q: q.value || undefined } })
    rows.value = res.data
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Không thể tải danh sách người dùng.' })
  }
}

// --- Logic mới cho Dialog ---
function resetActiveUser() {
  activeUser.id = null
  activeUser.username = ''
  activeUser.full_name = ''
  activeUser.password = ''
  activeUser.role = 'staff'
}

function openAddUserDialog() {
  if (!isAdmin.value) return
  resetActiveUser()
  editMode.value = false
  dlgUser.value = true
}

function openEditUserDialog(user) {
  if (!isAdmin.value) return
  resetActiveUser()
  editMode.value = true
  // Sao chép dữ liệu, mật khẩu để trống
  Object.assign(activeUser, { ...user, password: '' })
  dlgUser.value = true
}

async function saveUser() {
  if (!isAdmin.value) return

  const payload = { ...activeUser }
  // Chỉ gửi mật khẩu nếu nó được nhập
  if (!payload.password) {
    delete payload.password
  }

  try {
    if (editMode.value) {
      await api.put(`/users/${payload.id}`, payload)
      $q.notify({ type: 'positive', message: 'Cập nhật người dùng thành công.' })
    } else {
      await api.post('/users', payload)
      $q.notify({ type: 'positive', message: 'Thêm người dùng thành công.' })
    }
    dlgUser.value = false
    load()
  } catch (error) {
    const detail = error.response?.data?.detail || 'Thao tác thất bại.'
    $q.notify({ type: 'negative', message: detail })
  }
}

async function delUser (row) {
  if (!isAdmin.value) return
  $q.dialog({
    title: 'Xác nhận',
    message: `Bạn có chắc chắn muốn xóa người dùng "${row.username}" không?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/users/${row.id}`)
      $q.notify({ type: 'positive', message: 'Xóa người dùng thành công.' })
      load()
    } catch (error) {
      $q.notify({ type: 'negative', message: 'Xóa thất bại.' })
    }
  })
}

async function handleImport(event) {
  const file = event.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  $q.loading.show({ message: 'Đang xử lý file...' })
  try {
    await api.post('/users/import/xlsx', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    $q.notify({ type: 'positive', message: 'Import thành công!' })
    load()
  } catch (error) {
    const detail = error.response?.data?.detail || 'Import thất bại.'
    $q.notify({ type: 'negative', message: detail })
  } finally {
    $q.loading.hide()
    importRef.value.value = ''
  }
}

async function exportUsers() {
  try {
    $q.loading.show({ message: 'Đang tạo file...' });
    const response = await api.get('/users/export/xlsx', { responseType: 'blob' });
    const blob = new Blob([response.data], { type: response.headers['content-type'] });
    const filename = `users_export_${new Date().toISOString().slice(0, 10)}.xlsx`;

    const status = qExportFile(filename, blob, {
      mimeType: response.headers['content-type']
    });

    if (status !== true) {
      $q.notify({ type: 'negative', message: 'Trình duyệt đã chặn việc tải file.' });
    } else {
       $q.notify({ type: 'positive', message: 'Export thành công!' });
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
    title: 'XÁC NHẬN XÓA',
    message: 'Hành động này sẽ xóa TOÀN BỘ dữ liệu người dùng và không thể hoàn tác. Vui lòng nhập mật khẩu xác nhận để tiếp tục.',
    prompt: {
      model: '',
      type: 'password',
      label: 'Mật khẩu xác nhận'
    },
    cancel: true,
    persistent: true,
    color: 'negative'
  }).onOk(async (password) => {
    if (password !== 'Kienhp@@123') {
      $q.notify({ type: 'negative', message: 'Mật khẩu xác nhận không đúng.' })
      return
    }
    $q.loading.show({ message: 'Đang xóa dữ liệu...' })
    try {
      await api.post('/users/clear')
      $q.notify({ type: 'positive', message: 'Đã xóa toàn bộ dữ liệu người dùng.' })
      load()
    } catch (error) {
      $q.notify({ type: 'negative', message: 'Xóa dữ liệu thất bại.' })
    } finally {
      $q.loading.hide()
    }
  })
}

load()
</script>
