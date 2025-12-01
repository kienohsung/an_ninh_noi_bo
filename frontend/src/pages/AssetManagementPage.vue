<template>
  <q-page padding>
    <q-card>
      <q-card-section class="row items-center justify-between">
        <div class="text-h6">Quản lý Lịch sử Tài sản</div>
        <q-btn 
          label="Xuất Excel" 
          color="positive" 
          @click="exportData" 
          icon="download"
          :loading="loading"
        />
      </q-card-section>
      <q-separator />

      <!-- Filters -->
      <q-card-section class="row q-col-gutter-md items-center">
         <div class="col-12 col-md-3">
            <q-input dense outlined v-model="filters.startDate" mask="date" label="Từ ngày">
              <template v-slot:append>
                <q-icon name="event" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date v-model="filters.startDate"><div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div></q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>
          <div class="col-12 col-md-3">
             <q-input dense outlined v-model="filters.endDate" mask="date" label="Đến ngày">
              <template v-slot:append>
                <q-icon name="event" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date v-model="filters.endDate"><div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div></q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>
         <div class="col-12 col-md-3">
          <q-select
            v-model="filters.status"
            :options="statusOptions"
            label="Trạng thái"
            dense
            outlined
            emit-value
            map-options
            clearable
          />
        </div>
        <div class="col-12 col-md-3">
          <q-input
            v-model="filters.department"
            label="Tìm theo bộ phận"
            dense
            outlined
            clearable
          />
        </div>
      </q-card-section>

      <!-- Table -->
      <q-table
        :rows="rows"
        :columns="columns"
        row-key="id"
        flat
        :loading="loading"
        :pagination="{ rowsPerPage: 15 }"
        @row-click="onRowClick"
        class="cursor-pointer"
      >
        <template #body-cell-status="props">
          <q-td :props="props">
            <q-chip 
              :color="getStatusColor(props.value)" 
              text-color="white" 
              dense
              :label="getStatusLabel(props.value)"
            />
          </q-td>
        </template>

        <template #body-cell-created_at="props">
          <q-td :props="props">{{ formatDateTime(props.value) }}</q-td>
        </template>
        <template #body-cell-estimated_datetime="props">
          <q-td :props="props">{{ formatDate(props.value) }}</q-td>
        </template>
         <template #body-cell-check_out_time="props">
          <q-td :props="props">{{ formatDateTime(props.value) }}</q-td>
        </template>
        <template #body-cell-check_in_back_time="props">
          <q-td :props="props">{{ formatDateTime(props.value) }}</q-td>
        </template>

        <template #body-cell-actions="props">
          <q-td :props="props">
            <q-btn flat dense icon="edit" color="primary" @click.stop="openEditAssetDialog(props.row)" :disable="auth.user?.role !== 'admin' && props.row.status !== 'pending_out'">
              <q-tooltip v-if="auth.user?.role === 'admin' || props.row.status === 'pending_out'">Sửa thông tin</q-tooltip>
              <q-tooltip v-else>Chỉ sửa được khi chờ ra</q-tooltip>
            </q-btn>
            <q-btn flat dense icon="delete" color="negative" @click.stop="deleteAsset(props.row.id)" :disable="auth.user?.role !== 'admin' && props.row.status !== 'pending_out'">
              <q-tooltip v-if="auth.user?.role === 'admin' || props.row.status === 'pending_out'">Xóa (Chỉ khi chưa ra cổng)</q-tooltip>
              <q-tooltip v-else>Chỉ xóa được khi chờ ra</q-tooltip>
            </q-btn>
          </q-td>
        </template>
      </q-table>
    </q-card>

    <!-- Detail Dialog -->
    <q-dialog v-model="showDetailDialog" position="right">
      <q-card style="width: 500px; max-width: 90vw;">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">Chi tiết Tài sản</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section v-if="selectedAsset" class="q-pt-none">
          <!-- Image Carousel -->
          <div v-if="selectedAsset.images && selectedAsset.images.length > 0" class="q-mb-md">
            <q-carousel
              v-model="slide"
              animated
              arrows
              navigation
              infinite
              swipeable
              height="300px"
            >
              <q-carousel-slide 
                v-for="(image, index) in selectedAsset.images" 
                :key="index"
                :name="index"
                class="q-pa-none"
              >
                <q-img 
                  :src="getImageUrl(image.image_path)" 
                  fit="contain"
                  style="height: 300px;"
                />
              </q-carousel-slide>
            </q-carousel>
          </div>
          <div v-else class="q-mb-md text-center text-grey-6">
            Không có hình ảnh
          </div>

          <!-- Asset Details -->
          <q-list dense>
            <q-item>
              <q-item-section>
                <q-item-label caption>Trạng thái</q-item-label>
                <q-item-label>
                  <q-chip 
                    :color="getStatusColor(selectedAsset.status)" 
                    text-color="white" 
                    dense
                  >
                    {{ getStatusLabel(selectedAsset.status) }}
                  </q-chip>
                </q-item-label>
              </q-item-section>
            </q-item>

            <q-separator spaced />

            <q-item>
              <q-item-section>
                <q-item-label caption>Người đăng ký</q-item-label>
                <q-item-label>{{ selectedAsset.registered_by.full_name }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section>
                <q-item-label caption>Bộ phận</q-item-label>
                <q-item-label>{{ selectedAsset.department }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section>
                <q-item-label caption>Nơi đến</q-item-label>
                <q-item-label>{{ selectedAsset.destination }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section>
                <q-item-label caption>Mô tả tài sản & lý do</q-item-label>
                <q-item-label class="text-pre-wrap">{{ selectedAsset.description_reason }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section>
                <q-item-label caption>Số lượng</q-item-label>
                <q-item-label>{{ selectedAsset.quantity }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-separator spaced />

            <q-item>
              <q-item-section>
                <q-item-label caption>Ngày đăng ký</q-item-label>
                <q-item-label>{{ formatDateTime(selectedAsset.created_at) }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section>
                <q-item-label caption>Dự kiến về</q-item-label>
                <q-item-label>{{ formatDate(selectedAsset.estimated_datetime) || 'Không về' }}</q-item-label>
              </q-item-section>
            </q-item>

            <template v-if="selectedAsset.check_out_time">
              <q-separator spaced />
              <q-item>
                <q-item-section>
                  <q-item-label caption>Giờ ra</q-item-label>
                  <q-item-label>{{ formatDateTime(selectedAsset.check_out_time) }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item v-if="selectedAsset.check_out_by">
                <q-item-section>
                  <q-item-label caption>BV xác nhận ra</q-item-label>
                  <q-item-label>{{ selectedAsset.check_out_by.full_name }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>

            <template v-if="selectedAsset.check_in_back_time">
              <q-separator spaced />
              <q-item>
                <q-item-section>
                  <q-item-label caption>Giờ về</q-item-label>
                  <q-item-label>{{ formatDateTime(selectedAsset.check_in_back_time) }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item v-if="selectedAsset.check_in_back_by">
                <q-item-section>
                  <q-item-label caption>BV xác nhận về</q-item-label>
                  <q-item-label>{{ selectedAsset.check_in_back_by.full_name }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-list>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Edit Dialog -->
    <q-dialog v-model="showEditAssetDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Cập nhật tài sản</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="submitEditAsset" class="q-gutter-md">
            <q-input v-model="editAssetForm.destination" label="Nơi đến" outlined dense required />
            <q-input v-model.number="editAssetForm.quantity" label="Số lượng" type="number" outlined dense required />
            
            <q-input 
                v-model="formattedEditAssetDatetime" 
                label="Ngày dự kiến *" 
                dense 
                outlined 
                readonly 
                required
                :rules="[val => !!val || 'Vui lòng chọn ngày dự kiến']"
              >
                <template v-slot:append>
                  <q-icon name="event" class="cursor-pointer" @click="openDateTimePickerProxy">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <div class="q-pa-md" style="min-width: 300px">
                        <div class="q-gutter-md">
                          <q-date v-model="proxyDate" mask="YYYY-MM-DD" />
                        </div>
                        <div class="row items-center justify-end q-mt-md q-gutter-sm">
                          <q-btn v-close-popup label="Bỏ qua" color="primary" flat />
                          <q-btn v-close-popup label="OK" color="primary" @click="setEstimatedDatetime" />
                        </div>
                      </div>
                    </q-popup-proxy>
                  </q-icon>
                </template>
            </q-input>

            <q-input v-model="editAssetForm.description_reason" label="Mô tả / Lý do" type="textarea" outlined dense required />
            
            <div class="row justify-end q-gutter-sm">
              <q-btn label="Hủy" flat v-close-popup />
              <q-btn label="Cập nhật" type="submit" color="primary" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, reactive, watch, computed } from 'vue';
import { useQuasar, date as quasarDate } from 'quasar';
import api from '../api';
import { exportFile } from '../utils/export';
import { useAuthStore } from '../stores/auth';

const $q = useQuasar();
const auth = useAuthStore();
const loading = ref(false);
const rows = ref([]);
const showDetailDialog = ref(false);
const selectedAsset = ref(null);
const slide = ref(0);

// Filters
const filters = reactive({
  status: null,
  department: '',
  startDate: null,
  endDate: null,
});

const statusOptions = [
  { label: 'Chờ ra', value: 'pending_out' },
  { label: 'Đã ra (chờ về)', value: 'checked_out' },
  { label: 'Đã hoàn trả', value: 'returned' }
];

// Columns
const columns = [
  { name: 'status', label: 'Trạng thái', field: 'status', align: 'left', sortable: true },
  { name: 'registered_by_name', label: 'Người đăng ký', field: row => row.registered_by.full_name, align: 'left' },
  { name: 'department', label: 'Bộ phận', field: 'department', align: 'left', sortable: true },
  { name: 'destination', label: 'Nơi đến', field: 'destination', align: 'left' },
  { name: 'description_reason', label: 'Mô tả', field: 'description_reason', align: 'left', style: 'max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;' },
  { name: 'quantity', label: 'SL', field: 'quantity', align: 'center', sortable: true },
  { name: 'created_at', label: 'Ngày ĐK', field: 'created_at', align: 'left', sortable: true },
  { name: 'estimated_datetime', label: 'Ngày dự kiến', field: 'estimated_datetime', align: 'left', sortable: true, format: val => formatDate(val) },
  { name: 'check_out_time', label: 'Giờ ra', field: 'check_out_time', align: 'left', sortable: true },
  { name: 'check_in_back_time', label: 'Giờ về', field: 'check_in_back_time', align: 'left', sortable: true },
  { name: 'check_out_by_name', label: 'BV xác nhận ra', field: row => row.check_out_by?.full_name, align: 'left' },
  { name: 'check_in_back_by_name', label: 'BV xác nhận về', field: row => row.check_in_back_by?.full_name, align: 'left' },
  { name: 'actions', label: 'Thao tác', field: 'actions', align: 'center' }
];

// Helpers
function getStatusColor(status) {
  if (status === 'pending_out') return 'warning';
  if (status === 'checked_out') return 'info';
  if (status === 'returned') return 'positive';
  return 'grey';
}
function getStatusLabel(status) {
  const option = statusOptions.find(opt => opt.value === status);
  return option ? option.label : status;
}
function formatDateTime(val) {
  if (!val) return '';
  return quasarDate.formatDate(val, 'YYYY/MM/DD HH:mm');
}
function formatDate(val) {
  if (!val) return '';
  return quasarDate.formatDate(val, 'YYYY/MM/DD');
}

// Load Data
async function loadData() {
  loading.value = true;
  try {
    const params = {
      status: filters.status || undefined,
      department: filters.department || undefined,
      start_date: filters.startDate ? quasarDate.formatDate(quasarDate.extractDate(filters.startDate, 'YYYY/MM/DD'), 'YYYY-MM-DD') : undefined,
      end_date: filters.endDate ? quasarDate.formatDate(quasarDate.extractDate(filters.endDate, 'YYYY/MM/DD'), 'YYYY-MM-DD') : undefined,
    };
    
    const response = await api.get('/assets', { params });
    rows.value = response.data;
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Không thể tải lịch sử tài sản.' });
  } finally {
    loading.value = false;
  }
}

// Row Click
function onRowClick(evt, row) {
  selectedAsset.value = row;
  slide.value = 0;
  showDetailDialog.value = true;
}

// Image URL
function getImageUrl(imagePath) {
  if (!imagePath) return '';
  const apiBaseURL = api.defaults.baseURL || 'http://localhost:8000';
  return `${apiBaseURL}/uploads/${imagePath}`;
}

// Export
function exportData() {
  loading.value = true;
  try {
    const dataToExport = rows.value.map(row => ({
      'Trạng thái': getStatusLabel(row.status),
      'Người đăng ký': row.registered_by.full_name,
      'Bộ phận': row.department,
      'Nơi đến': row.destination,
      'Mô tả': row.description_reason,
      'Số lượng': row.quantity,
      'Ngày ĐK': formatDateTime(row.created_at),
      'Dự kiến về': formatDate(row.estimated_datetime),
      'Giờ ra': formatDateTime(row.check_out_time),
      'BV xác nhận ra': row.check_out_by?.full_name || '',
      'Giờ về': formatDateTime(row.check_in_back_time),
      'BV xác nhận về': row.check_in_back_by?.full_name || '',
    }));
    
    const columnsToExport = [
      'Trạng thái', 'Người đăng ký', 'Bộ phận', 'Nơi đến', 'Mô tả', 'Số lượng', 
      'Ngày ĐK', 'Dự kiến về', 'Giờ ra', 'BV xác nhận ra', 'Giờ về', 'BV xác nhận về'
    ];

    exportFile('LichSuTaiSan.xlsx', dataToExport, columnsToExport);
  } catch (error) {
     $q.notify({ type: 'negative', message: 'Lỗi khi tạo file Excel.' });
  } finally {
    loading.value = false;
  }
}

// Watch filters
watch(filters, loadData, { deep: true });

// Edit/Delete Logic
async function deleteAsset(id) {
  $q.dialog({
    title: 'Xác nhận',
    message: 'Bạn có chắc chắn muốn xóa tài sản này?',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/assets/${id}`)
      $q.notify({ type: 'positive', message: 'Đã xóa tài sản.' })
      loadData()
    } catch (error) {
       $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Xóa thất bại.' })
    }
  })
}

const showEditAssetDialog = ref(false)
const editAssetForm = reactive({
  id: null,
  destination: '',
  quantity: 1,
  description_reason: '',
  estimated_datetime: null
})
const proxyDate = ref(null)

const formattedEditAssetDatetime = computed(() => {
  if (!editAssetForm.estimated_datetime) return null
  return quasarDate.formatDate(new Date(editAssetForm.estimated_datetime), 'DD/MM/YYYY')
})

function openEditAssetDialog(row) {
  editAssetForm.id = row.id
  editAssetForm.destination = row.destination
  editAssetForm.quantity = row.quantity
  editAssetForm.description_reason = row.description_reason
  editAssetForm.estimated_datetime = row.estimated_datetime 
  showEditAssetDialog.value = true
}

function openDateTimePickerProxy() {
  let d
  if (editAssetForm.estimated_datetime) {
    d = new Date(editAssetForm.estimated_datetime)
  } else {
    d = new Date()
  }
  proxyDate.value = quasarDate.formatDate(d, 'YYYY-MM-DD')
}

function setEstimatedDatetime() {
  if (proxyDate.value) {
    editAssetForm.estimated_datetime = `${proxyDate.value}T00:00:00`
  }
}

async function submitEditAsset() {
  try {
    const payload = { 
        destination: editAssetForm.destination,
        quantity: editAssetForm.quantity,
        description_reason: editAssetForm.description_reason,
        estimated_datetime: editAssetForm.estimated_datetime
    }
    
    await api.put(`/assets/${editAssetForm.id}`, payload)
    $q.notify({ type: 'positive', message: 'Cập nhật tài sản thành công!' })
    showEditAssetDialog.value = false
    loadData()
  } catch (error) {
    console.error('Update asset failed:', error)
    $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Cập nhật thất bại.' })
  }
}

onMounted(loadData);
</script>