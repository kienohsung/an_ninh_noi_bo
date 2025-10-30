<!-- File: frontend/src/pages/LongTermGuestsPage.vue -->
<template>
  <q-page padding>
    <q-card>
      <q-card-section class="row items-center justify-between">
        <div class="text-h6">Quản lý khách dài hạn</div>
      </q-card-section>
      <q-separator />
      <q-table
        :rows="rows"
        :columns="columns"
        row-key="id"
        flat
        :loading="loading"
      >
        <template #body-cell-is_active="props">
          <q-td :props="props">
            <q-toggle
              :model-value="props.row.is_active"
              @update:model-value="val => updateActiveStatus(props.row, val)"
              :color="props.row.is_active ? 'positive' : 'grey'"
            />
          </q-td>
        </template>
        
        <!-- BẮT ĐẦU NÂNG CẤP: Định dạng cột Ngày & Giờ dự kiến -->
        <template #body-cell-estimated_datetime="props">
            <q-td :props="props">
              <q-chip 
                v-if="props.value" 
                icon="schedule" 
                :label="quasarDate.formatDate(props.value, 'DD/MM HH:mm')" 
                dense 
                outline 
                size="sm"
                color="blue-grey" 
              />
            </q-td>
        </template>
        <!-- KẾT THÚC NÂNG CẤP -->

        <template #body-cell-actions="props">
          <q-td :props="props">
            <q-btn flat dense icon="edit" @click="openEditDialog(props.row)" />
            <q-btn flat dense icon="delete" color="negative" @click="deleteGuest(props.row)" />
          </q-td>
        </template>
      </q-table>
    </q-card>

    <!-- Edit Dialog -->
    <q-dialog v-model="showEditDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Chỉnh sửa đăng ký dài hạn</div>
        </q-card-section>
        <q-separator />
        <q-card-section>
          <q-form @submit="onUpdateSubmit" class="q-gutter-y-md">
            <q-input v-model="editForm.full_name" label="Họ tên" dense outlined required />
            <q-input v-model="editForm.id_card_number" label="CCCD" dense outlined />
            <q-input v-model="editForm.supplier_name" label="Nhà cung cấp" dense outlined />
            <q-input v-model="editForm.license_plate" label="Biển số" dense outlined />

            <!-- BẮT ĐẦU NÂNG CẤP: Thay thế input time bằng DateTime Picker -->
            <q-input 
              v-model="formattedEditEstimatedDatetime" 
              label="Ngày & Giờ dự kiến" 
              dense 
              outlined 
              readonly 
              clearable 
              @clear="editForm.estimated_datetime = null"
              hint="Tùy chọn"
            >
              <template v-slot:append>
                <q-icon name="event" class="cursor-pointer" @click="openDateTimePickerProxy">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <div class="q-pa-md" style="min-width: 300px">
                      <div class="q-gutter-md">
                        <q-date v-model="proxyDate" mask="YYYY-MM-DD" />
                        <q-time v-model="proxyTime" mask="HH:mm" format24h />
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
            <!-- KẾT THÚC NÂNG CẤP -->

            <q-input type="textarea" v-model="editForm.reason" label="Chi tiết" outlined dense />
            
            <div class="row q-col-gutter-md">
              <div class="col-6">
                <q-input dense outlined v-model="editForm.start_date_display" mask="date" label="Từ ngày">
                  <template v-slot:append>
                    <q-icon name="event" class="cursor-pointer">
                      <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                        <q-date v-model="editForm.start_date_display">
                          <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                        </q-date>
                      </q-popup-proxy>
                    </q-icon>
                  </template>
                </q-input>
              </div>
              <div class="col-6">
                <q-input dense outlined v-model="editForm.end_date_display" mask="date" label="Đến ngày">
                   <template v-slot:append>
                    <q-icon name="event" class="cursor-pointer">
                      <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                        <q-date v-model="editForm.end_date_display">
                           <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                        </q-date>
                      </q-popup-proxy>
                    </q-icon>
                  </template>
                </q-input>
              </div>
            </div>

            <div class="row justify-end q-gutter-sm q-mt-lg">
              <q-btn label="Hủy" flat v-close-popup />
              <q-btn type="submit" label="Cập nhật" color="primary" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
// BẮT ĐẦU NÂNG CẤP: Thêm 'computed'
import { ref, onMounted, reactive, computed } from 'vue';
// KẾT THÚC NÂNG CẤP
import { useQuasar, date as quasarDate } from 'quasar';
import api from '../api';

const $q = useQuasar();
const loading = ref(false);
const rows = ref([]);
const showEditDialog = ref(false);

// --- BẮT ĐẦU NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
const editForm = reactive({
  id: null,
  full_name: '',
  id_card_number: '',
  supplier_name: '',
  license_plate: '',
  reason: '',
  estimated_datetime: null, // <-- NÂNG CẤP
  start_date_display: '',
  end_date_display: ''
});
// --- KẾT THÚC NÂNG CẤP ---

// --- BẮT ĐẦU NÂNG CẤP: Logic cho DateTime Picker (Dialog Sửa) ---
const proxyDate = ref(null)
const proxyTime = ref(null)

// Computed để hiển thị ngày giờ trong DIALOG SỬA
const formattedEditEstimatedDatetime = computed(() => {
  if (!editForm.estimated_datetime) return null;
  const d = new Date(editForm.estimated_datetime);
  return quasarDate.formatDate(d, 'DD/MM/YYYY HH:mm');
});

// Hàm mở popup và khởi tạo giá trị
function openDateTimePickerProxy() {
  let d;
  if (editForm.estimated_datetime) {
    // Nếu đã có giá trị, dùng giá trị đó
    d = new Date(editForm.estimated_datetime);
  } else {
    // Nếu không có, đề xuất thời gian hiện tại + làm tròn 30 phút
    d = new Date();
    const minutes = d.getMinutes();
    if (minutes < 30) {
      d.setMinutes(30);
    } else {
      d.setMinutes(0);
      d.setHours(d.getHours() + 1);
    }
    d.setSeconds(0);
    d.setMilliseconds(0);
  }
  
  // Set giá trị cho q-date và q-time
  proxyDate.value = quasarDate.formatDate(d, 'YYYY-MM-DD');
  proxyTime.value = quasarDate.formatDate(d, 'HH:mm');
}

// Hàm lưu giá trị từ popup về form
function setEstimatedDatetime() {
  if (proxyDate.value && proxyTime.value) {
    // Kết hợp lại thành chuỗi ISO
    editForm.estimated_datetime = `${proxyDate.value}T${proxyTime.value}:00`;
  }
}
// --- KẾT THÚC NÂNG CẤP ---


// --- BẮT ĐẦU NÂNG CẤP: Thêm cột Ngày & Giờ dự kiến vào bảng ---
const columns = [
  { name: 'full_name', label: 'Họ tên', field: 'full_name', align: 'left', sortable: true },
  { name: 'id_card_number', label: 'CCCD', field: 'id_card_number', align: 'left' },
  { name: 'supplier_name', label: 'Nhà cung cấp', field: 'supplier_name', align: 'left' },
  { name: 'license_plate', label: 'Biển số', field: 'license_plate', align: 'left' },
  
  // --- NÂNG CẤP ---
  { name: 'estimated_datetime', label: 'Ngày & Giờ dự kiến', field: 'estimated_datetime', align: 'left', sortable: true },
  // --- KẾT THÚC NÂNG CẤP ---
  
  { name: 'start_date', label: 'Từ ngày', field: 'start_date', format: val => quasarDate.formatDate(val, 'DD/MM/YYYY'), align: 'left', sortable: true },
  { name: 'end_date', label: 'Đến ngày', field: 'end_date', format: val => quasarDate.formatDate(val, 'DD/MM/YYYY'), align: 'left', sortable: true },
  { name: 'registered_by_name', label: 'Người đăng ký', field: 'registered_by_name', align: 'left' },
  { name: 'is_active', label: 'Hoạt động', field: 'is_active', align: 'center' },
  { name: 'actions', label: '', field: 'actions', align: 'right' }
];
// --- KẾT THÚC NÂNG CẤP ---

async function loadData() {
  loading.value = true;
  try {
    const response = await api.get('/long-term-guests');
    rows.value = response.data;
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Không thể tải danh sách khách dài hạn.' });
  } finally {
    loading.value = false;
  }
}

async function updateActiveStatus(row, isActive) {
  try {
    // Gửi chỉ 1 trường is_active để cập nhật
    await api.put(`/long-term-guests/${row.id}`, { is_active: isActive });
    $q.notify({ type: 'positive', message: `Đã ${isActive ? 'kích hoạt' : 'hủy'} đăng ký.` });
    
    // Tối ưu: Cập nhật row tại local thay vì gọi lại API
    const index = rows.value.findIndex(r => r.id === row.id);
    if (index > -1) {
      rows.value[index].is_active = isActive;
    }
    // loadData(); // Có thể bỏ nếu chỉ cập nhật 1 trường
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Cập nhật trạng thái thất bại.' });
  }
}

function openEditDialog(row) {
  // Đảm bảo sao chép sâu
  Object.assign(editForm, JSON.parse(JSON.stringify(row)));
  
  // Chuẩn hoá format ngày để hiển thị
  editForm.start_date_display = quasarDate.formatDate(row.start_date, 'YYYY/MM/DD');
  editForm.end_date_display = quasarDate.formatDate(row.end_date, 'YYYY/MM/DD');
  
  // editForm.estimated_datetime đã được gán từ row
  
  showEditDialog.value = true;
}

async function onUpdateSubmit() {
  try {
    const startDate = quasarDate.extractDate(editForm.start_date_display, 'YYYY/MM/DD');
    const endDate = quasarDate.extractDate(editForm.end_date_display, 'YYYY/MM/DD');
    
    // --- BẮT ĐẦU NÂNG CẤP: Thêm estimated_datetime vào payload ---
    const payload = {
      full_name: editForm.full_name,
      id_card_number: editForm.id_card_number,
      supplier_name: editForm.supplier_name,
      license_plate: editForm.license_plate,
      reason: editForm.reason,
      estimated_datetime: editForm.estimated_datetime || null, // <-- NÂNG CẤP
      start_date: quasarDate.formatDate(startDate, 'YYYY-MM-DD'),
      end_date: quasarDate.formatDate(endDate, 'YYYY-MM-DD')
    };
    // --- KẾT THÚC NÂNG CẤP ---

    await api.put(`/long-term-guests/${editForm.id}`, payload);
    $q.notify({ type: 'positive', message: 'Cập nhật thành công.' });
    showEditDialog.value = false;
    loadData();
  } catch (error) {
    $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Cập nhật thất bại.' });
  }
}

function deleteGuest(row) {
  $q.dialog({
    title: 'Xác nhận xóa',
    message: `Bạn có chắc muốn xóa vĩnh viễn đăng ký dài hạn cho khách "${row.full_name}"?`,
    cancel: true,
    persistent: true,
    color: 'negative'
  }).onOk(async () => {
    try {
      await api.delete(`/long-term-guests/${row.id}`);
      $q.notify({ type: 'positive', message: 'Đã xóa thành công.' });
      loadData();
    } catch (error) {
      $q.notify({ type: 'negative', message: 'Xóa thất bại.' });
    }
  });
}

onMounted(loadData);
</script>
