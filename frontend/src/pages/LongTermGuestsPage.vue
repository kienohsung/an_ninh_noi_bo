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
import { ref, onMounted, reactive } from 'vue';
import { useQuasar, date as quasarDate } from 'quasar'; // Sửa tên import
import api from '../api';

const $q = useQuasar();
const loading = ref(false);
const rows = ref([]);
const showEditDialog = ref(false);
const editForm = reactive({
  id: null,
  full_name: '',
  id_card_number: '',
  supplier_name: '',
  license_plate: '',
  reason: '',
  start_date_display: '',
  end_date_display: ''
});

const columns = [
  { name: 'full_name', label: 'Họ tên', field: 'full_name', align: 'left', sortable: true },
  { name: 'id_card_number', label: 'CCCD', field: 'id_card_number', align: 'left' },
  { name: 'supplier_name', label: 'Nhà cung cấp', field: 'supplier_name', align: 'left' },
  { name: 'license_plate', label: 'Biển số', field: 'license_plate', align: 'left' },
  { name: 'start_date', label: 'Từ ngày', field: 'start_date', format: val => quasarDate.formatDate(val, 'DD/MM/YYYY'), align: 'left', sortable: true },
  { name: 'end_date', label: 'Đến ngày', field: 'end_date', format: val => quasarDate.formatDate(val, 'DD/MM/YYYY'), align: 'left', sortable: true },
  { name: 'registered_by_name', label: 'Người đăng ký', field: 'registered_by_name', align: 'left' },
  { name: 'is_active', label: 'Hoạt động', field: 'is_active', align: 'center' },
  { name: 'actions', label: '', field: 'actions', align: 'right' }
];

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
    await api.put(`/long-term-guests/${row.id}`, { is_active: isActive });
    $q.notify({ type: 'positive', message: `Đã ${isActive ? 'kích hoạt' : 'hủy'} đăng ký.` });
    loadData();
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Cập nhật trạng thái thất bại.' });
  }
}

function openEditDialog(row) {
  Object.assign(editForm, row);
  // CẢI TIẾN: Chuẩn hoá format ngày để hiển thị
  editForm.start_date_display = quasarDate.formatDate(row.start_date, 'YYYY/MM/DD');
  editForm.end_date_display = quasarDate.formatDate(row.end_date, 'YYYY/MM/DD');
  showEditDialog.value = true;
}

async function onUpdateSubmit() {
  try {
    // CẢI TIẾN: Chuẩn hoá parse/format ngày khi submit
    const startDate = quasarDate.extractDate(editForm.start_date_display, 'YYYY/MM/DD');
    const endDate = quasarDate.extractDate(editForm.end_date_display, 'YYYY/MM/DD');
    
    const payload = {
      full_name: editForm.full_name,
      id_card_number: editForm.id_card_number,
      supplier_name: editForm.supplier_name,
      license_plate: editForm.license_plate,
      reason: editForm.reason,
      start_date: quasarDate.formatDate(startDate, 'YYYY-MM-DD'),
      end_date: quasarDate.formatDate(endDate, 'YYYY-MM-DD')
    };

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

