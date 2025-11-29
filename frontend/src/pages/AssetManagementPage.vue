<!-- File path: frontend/src/pages/AssetManagementPage.vue -->
<!-- === CHECKLIST 2.5: Tạo file component AssetManagementPage.vue (copy từ LongTermGuestsPage.vue) === -->
<template>
  <q-page padding>
    <q-card>
      <q-card-section class="row items-center justify-between">
        <!-- === CHECKLIST 2.6: Cập nhật UI (Tiêu đề) === -->
        <div class="text-h6">Quản lý Lịch sử Tài sản</div>
        <!-- === CHECKLIST 2.8: Thêm nút Export Excel === -->
        <q-btn 
          label="Xuất Excel" 
          color="positive" 
          @click="exportData" 
          icon="download"
          :loading="loading"
        />
      </q-card-section>
      <q-separator />

      <!-- === CHECKLIST 2.7: Thêm Filters === -->
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

      <!-- === CHECKLIST 2.6: Cập nhật Q-Table === -->
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
        <!-- Template cho cột Trạng thái -->
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

        <!-- Template cho các cột ngày giờ -->
        <template #body-cell-created_at="props">
          <q-td :props="props">{{ formatDateTime(props.value) }}</q-td>
        </template>
        <template #body-cell-expected_return_date="props">
          <q-td :props="props">{{ formatDate(props.value) }}</q-td>
        </template>
         <template #body-cell-check_out_time="props">
          <q-td :props="props">{{ formatDateTime(props.value) }}</q-td>
        </template>
        <template #body-cell-check_in_back_time="props">
          <q-td :props="props">{{ formatDateTime(props.value) }}</q-td>
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
                <q-item-label>{{ formatDate(selectedAsset.expected_return_date) || 'Không về' }}</q-item-label>
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

  </q-page>
</template>

<script setup>
import { ref, onMounted, reactive, watch } from 'vue';
import { useQuasar, date as quasarDate } from 'quasar';
import api from '../api';
import { exportFile } from '../utils/export'; // === CHECKLIST 2.8 ===
import { useAuthStore } from '../stores/auth';

const $q = useQuasar();
const auth = useAuthStore();
const loading = ref(false);
const rows = ref([]);
const showDetailDialog = ref(false);
const selectedAsset = ref(null);
const slide = ref(0);

// === CHECKLIST 2.7: Thêm Filters ===
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

// === CHECKLIST 2.6: Cập nhật Cột ===
const columns = [
  { name: 'status', label: 'Trạng thái', field: 'status', align: 'left', sortable: true },
  { name: 'registered_by_name', label: 'Người đăng ký', field: row => row.registered_by.full_name, align: 'left' },
  { name: 'department', label: 'Bộ phận', field: 'department', align: 'left', sortable: true },
  { name: 'destination', label: 'Nơi đến', field: 'destination', align: 'left' },
  { name: 'description_reason', label: 'Mô tả', field: 'description_reason', align: 'left', style: 'max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;' },
  { name: 'quantity', label: 'SL', field: 'quantity', align: 'center', sortable: true },
  { name: 'created_at', label: 'Ngày ĐK', field: 'created_at', align: 'left', sortable: true },
  { name: 'expected_return_date', label: 'Dự kiến về', field: 'expected_return_date', align: 'left', sortable: true },
  { name: 'check_out_time', label: 'Giờ ra', field: 'check_out_time', align: 'left', sortable: true },
  { name: 'check_in_back_time', label: 'Giờ về', field: 'check_in_back_time', align: 'left', sortable: true },
  { name: 'check_out_by_name', label: 'BV xác nhận ra', field: row => row.check_out_by?.full_name, align: 'left' },
  { name: 'check_in_back_by_name', label: 'BV xác nhận về', field: row => row.check_in_back_by?.full_name, align: 'left' },
];

// === Helpers ===
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

// === CHECKLIST 2.7: Cập nhật logic loadData ===
async function loadData() {
  loading.value = true;
  try {
    const params = {
      status: filters.status || undefined,
      department: filters.department || undefined,
      start_date: filters.startDate ? quasarDate.formatDate(quasarDate.extractDate(filters.startDate, 'YYYY/MM/DD'), 'YYYY-MM-DD') : undefined,
      end_date: filters.endDate ? quasarDate.formatDate(quasarDate.extractDate(filters.endDate, 'YYYY/MM/DD'), 'YYYY-MM-DD') : undefined,
    };
    
    // Chỉ staff mới bị lọc theo user_id (logic này đã ở backend)
    // const response = await api.get('/assets', { params: auth.user?.role === 'staff' ? params : { ...params, all: true } });
    
    const response = await api.get('/assets', { params });
    rows.value = response.data;
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Không thể tải lịch sử tài sản.' });
  } finally {
    loading.value = false;
  }
}

// Open detail dialog when row is clicked
function onRowClick(evt, row) {
  selectedAsset.value = row;
  slide.value = 0;
  showDetailDialog.value = true;
}

// Get full image URL
function getImageUrl(imagePath) {
  if (!imagePath) return '';
  const apiBaseURL = api.defaults.baseURL || 'http://localhost:8000';
  return `${apiBaseURL}/uploads/${imagePath}`;
}

// === CHECKLIST 2.8: Logic Export Excel ===
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
      'Dự kiến về': formatDate(row.expected_return_date),
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

// Watch filters to reload data
watch(filters, loadData, { deep: true });

onMounted(loadData);
</script>