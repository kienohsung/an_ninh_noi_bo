<!-- File: security_mgmt_dev/frontend/src/pages/SuppliersPage.vue -->
<template>
  <q-page padding>
    <q-card>
      <q-card-section class="row items-center justify-between">
        <div class="text-subtitle1">Nhà cung cấp</div>
        <div class="row items-center q-gutter-sm">
          <q-btn label="Thêm" color="primary" @click="addSupplier"/>
          <q-btn-dropdown color="secondary" label="Actions" v-if="auth.user?.role === 'admin'">
            <q-list>
              <q-item clickable v-close-popup @click="triggerImport"><q-item-section>Import Excel</q-item-section></q-item>
              <q-item clickable v-close-popup @click="exportSuppliers"><q-item-section>Export Excel</q-item-section></q-item>
            </q-list>
          </q-btn-dropdown>
          <q-btn color="red" label="Xóa dữ liệu" @click="clearData" v-if="auth.user?.role === 'admin'" />
          <input type="file" ref="fileInput" @change="handleImport" accept=".xlsx" hidden/>
        </div>
      </q-card-section>
      <q-separator/>
      <q-card-section>
        <q-table :rows="rows" :columns="columns" row-key="id" flat>
          <template #body-cell-actions="props">
            <q-td :props="props">
              <q-btn flat icon="edit" @click="editSupplier(props.row)"/>
              <q-btn flat icon="delete" color="negative" @click="delSupplier(props.row)"/>
              <q-btn flat icon="format_list_numbered" label="Biển số" @click="managePlates(props.row)"/>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <q-dialog v-model="dlgPlates">
      <q-card style="min-width:420px">
        <q-card-section><div class="text-subtitle1">Quản lý biển số — {{ activeSupplier?.name }}</div></q-card-section>
        <q-separator/>
        <q-card-section>
          <div class="row q-col-gutter-sm q-mb-sm">
            <div class="col"><q-input v-model="newPlate" label="Thêm biển số" dense outlined/></div>
            <div class="col-auto"><q-btn color="primary" label="Thêm" @click="addPlate"/></div>
          </div>
          <q-list bordered separator>
            <q-item v-for="p in plates" :key="p.id">
              <q-item-section>{{ p.plate }}</q-item-section>
              <q-item-section side>
                <q-btn flat icon="delete" color="negative" @click="delPlate(p)"/>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
        <q-separator/>
        <q-card-actions align="right"><q-btn flat label="Đóng" v-close-popup/></q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/auth'

const rows = ref([])
const $q = useQuasar()
const auth = useAuthStore()
const fileInput = ref(null)

const columns = [
  { name: 'name', label: 'Tên NCC', field: 'name', align: 'left' },
  { name: 'actions', label: '', field: 'actions', align: 'right' }
]

const dlgPlates = ref(false)
const activeSupplier = ref(null)
const plates = ref([])
const newPlate = ref('')

async function load () {
  const res = await api.get('/suppliers')
  rows.value = res.data
}
async function addSupplier () {
  const name = prompt('Tên nhà cung cấp')
  if (name) { await api.post('/suppliers', { name }); load() }
}
async function editSupplier (row) {
  const name = prompt('Sửa tên nhà cung cấp', row.name)
  if (name) { await api.put(`/suppliers/${row.id}`, { name }); load() }
}
async function delSupplier (row) {
  if (confirm('Xóa nhà cung cấp này?')) { await api.delete(`/suppliers/${row.id}`); load() }
}
async function managePlates (row) {
  activeSupplier.value = row
  const res = await api.get(`/suppliers/${row.id}/plates`)
  plates.value = res.data; newPlate.value = ''; dlgPlates.value = true
}
async function addPlate () {
  if (!newPlate.value) return
  await api.post(`/suppliers/${activeSupplier.value.id}/plates`, { plate: newPlate.value.toUpperCase() })
  const res = await api.get(`/suppliers/${activeSupplier.value.id}/plates`)
  plates.value = res.data; newPlate.value = ''
}
async function delPlate (p) {
  await api.delete(`/suppliers/${activeSupplier.value.id}/plates/${p.id}`)
  const res = await api.get(`/suppliers/${activeSupplier.value.id}/plates`)
  plates.value = res.data
}

function triggerImport() { fileInput.value.click() }

async function handleImport(event) {
  const file = event.target.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  try {
    $q.loading.show({ message: 'Đang xử lý file...' });
    await api.post('/suppliers/import/xlsx', formData);
    $q.notify({ type: 'positive', message: 'Import thành công!' });
    load();
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Import thất bại.' });
  } finally {
    $q.loading.hide();
    event.target.value = '';
  }
}

async function exportSuppliers() {
  try {
    const response = await api.get('/suppliers/export/xlsx', { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `suppliers_${new Date().toISOString().split('T')[0]}.xlsx`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Export thất bại.' });
  }
}

function clearData() {
  $q.dialog({
    title: 'Xác nhận xóa',
    message: 'Hành động này sẽ xóa tất cả nhà cung cấp và biển số liên quan. Vui lòng nhập mật khẩu để xác nhận:',
    prompt: { model: '', type: 'password' },
    cancel: true,
    persistent: true
  }).onOk(async (password) => {
    if (password === 'Kienhp@@123') {
      try {
        await api.post('/suppliers/clear');
        $q.notify({ type: 'positive', message: 'Đã xóa dữ liệu nhà cung cấp.' });
        load();
      } catch (error) {
        $q.notify({ type: 'negative', message: 'Xóa dữ liệu thất bại.' });
      }
    } else {
      $q.notify({ type: 'negative', message: 'Sai mật khẩu.' });
    }
  });
}

load()
</script>
