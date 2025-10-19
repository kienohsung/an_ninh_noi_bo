<!-- File: frontend/src/pages/VehicleLogPage.vue -->
<template>
  <q-page padding>
    <div class="q-gutter-y-md">

      <!-- Toolbar Lọc -->
      <q-card>
        <q-card-section>
          <div class="row q-col-gutter-md items-center">
            <q-select
              v-model="filters.quick"
              :options="quickRangeOptions"
              label="Khoảng nhanh"
              dense outlined
              emit-value map-options
              class="col-12 col-sm-6 col-md-2"
              @update:model-value="applyQuickRange"
            />
            <q-input
              v-model="filters.start"
              label="Từ ngày"
              dense outlined
              type="date"
              class="col-6 col-sm-3 col-md-2"
              :disable="!!filters.quick"
            />
            <q-input
              v-model="filters.end"
              label="Đến ngày"
              dense outlined
              type="date"
              class="col-6 col-sm-3 col-md-2"
              :disable="!!filters.quick"
            />
            <q-input
              v-model="filters.q"
              label="Tìm số xe"
              dense outlined
              class="col-12 col-md-3"
              clearable
              @keyup.enter="fetchData"
            >
              <template #append><q-icon name="search" /></template>
            </q-input>
            <div class="col-12 col-md-3">
              <q-btn
                label="Xuất Excel"
                icon="download"
                color="positive"
                @click="exportExcel"
                class="full-width"
              />
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- CẢI TIẾN: Vùng hiển thị lỗi hoặc loading -->
      <q-card v-if="loading || error">
        <q-card-section class="text-center">
          <div v-if="loading">
            <q-spinner-dots color="primary" size="40px" />
            <div class="q-mt-sm text-grey-8">Đang tải dữ liệu...</div>
          </div>
          <div v-if="error" class="text-negative">
            <q-icon name="error" size="32px" />
            <div class="text-h6 q-mt-sm">Không thể tải dữ liệu</div>
            <div class="q-mt-xs text-grey-8">{{ error }}</div>
            <q-btn
              label="Thử lại"
              color="primary"
              class="q-mt-md"
              @click="fetchData"
              unelevated
            />
          </div>
        </q-card-section>
      </q-card>

      <!-- Vùng hiển thị dữ liệu (chỉ hiện khi không có lỗi và không loading) -->
      <div v-else class="q-gutter-y-md">
        <!-- KPIs -->
        <div class="row q-col-gutter-md">
          <div v-for="k in kpiCards" :key="k.label" class="col-6 col-sm-3">
            <q-card>
              <q-card-section>
                <div class="text-h6">{{ kpi[k.key] || '-' }}</div>
                <div class="text-caption text-grey-7">{{ k.label }}</div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <!-- Biểu đồ -->
        <div class="row q-col-gutter-md">
          <div class="col-12 col-lg-8">
            <q-card>
              <q-card-section>
                <div class="text-subtitle1">Xu hướng theo ngày</div>
                <apexchart type="area" height="300" :options="chartTrend.options" :series="chartTrend.series" />
              </q-card-section>
            </q-card>
          </div>
          <div class="col-12 col-lg-4">
            <q-card>
              <q-card-section>
                <div class="text-subtitle1">Phân bố theo giờ</div>
                <apexchart type="bar" height="300" :options="chartHour.options" :series="chartHour.series" />
              </q-card-section>
            </q-card>
          </div>
        </div>
        
        <q-card>
          <q-card-section>
            <div class="text-subtitle1">Top 10 xe hoạt động nhiều</div>
            <apexchart type="bar" height="350" :options="chartTop.options" :series="chartTop.series" />
          </q-card-section>
        </q-card>

        <!-- Bảng dữ liệu -->
        <q-table
          title="Chi tiết nhật ký"
          :rows="items"
          :columns="columns"
          row-key="plate"
          v-model:pagination="pagination"
          :rows-per-page-options="[10, 20, 50, 100]"
          @request="handleTableRequest"
          :loading="loading"
          flat bordered
        />
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { useQuasar, date as qDate } from 'quasar';
import api from '../api';
import VueApexCharts from 'vue3-apexcharts';

const $q = useQuasar();

// --- State ---
const loading = ref(true);
const error = ref(null);

const filters = reactive({
  quick: 'last7',
  start: '',
  end: '',
  q: '',
});

const items = ref([]);
const kpi = ref({ totalInRange: 0, peakHour: null, topPlate: null, avgPerDay: 0 });
const pagination = ref({
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0
});

const kpiCards = [
  { key: 'totalInRange', label: 'Tổng lượt' },
  { key: 'avgPerDay', label: 'Trung bình/ngày' },
  { key: 'peakHour', label: 'Giờ cao điểm' },
  { key: 'topPlate', label: 'Xe nhiều nhất' }
];

const quickRangeOptions = [
  { label: 'Hôm nay', value: 'today' },
  { label: '7 ngày qua', value: 'last7' },
  { label: '30 ngày qua', value: 'last30' },
  { label: 'Tháng này', value: 'thisMonth' },
  { label: 'Tháng trước', value: 'prevMonth' },
  { label: '(Tùy chọn)', value: '' }
];

const columns = [
  { name: 'plate', label: 'Số xe', field: 'plate', align: 'left', sortable: true },
  { name: 'date', label: 'Ngày', field: 'date', align: 'left', sortable: true },
  { name: 'time', label: 'Giờ', field: 'time', align: 'left', sortable: true },
];

// --- Chart Data & Options ---
const chartTrend = reactive({ series: [], options: { chart: { type: 'area', height: 300, toolbar: { show: false } }, dataLabels: { enabled: false }, stroke: { curve: 'smooth' }, xaxis: { type: 'datetime' } } });
const chartHour = reactive({ series: [], options: { chart: { type: 'bar', height: 300, toolbar: { show: false } }, plotOptions: { bar: { columnWidth: '80%' } }, dataLabels: { enabled: false }, xaxis: { categories: [] } } });
const chartTop = reactive({ series: [], options: { chart: { type: 'bar', height: 350 }, plotOptions: { bar: { horizontal: true } }, dataLabels: { enabled: true, formatter: val => val }, xaxis: { categories: [] } } });

// --- CẢI TIẾN: Hàm khởi tạo dữ liệu mặc định để tránh lỗi 'undefined' ---
const resetChartData = () => {
    chartTrend.series = [];
    chartHour.series = [];
    chartTop.series = [];
    chartTrend.options = { ...chartTrend.options, xaxis: { categories: [] } };
    chartHour.options = { ...chartHour.options, xaxis: { categories: [] } };
    chartTop.options = { ...chartTop.options, xaxis: { categories: [] } };
};

const updateChartData = (chartData) => {
    // Luôn kiểm tra sự tồn tại của dữ liệu trước khi gán
    if (chartData?.daily) {
        chartTrend.series = [{ name: 'Lượt', data: chartData.daily.series }];
        chartTrend.options = { ...chartTrend.options, xaxis: { categories: chartData.daily.labels } };
    }
    if (chartData?.hours) {
        chartHour.series = [{ name: 'Lượt', data: chartData.hours.series }];
        chartHour.options = { ...chartHour.options, xaxis: { categories: chartData.hours.labels } };
    }
    if (chartData?.top10) {
        chartTop.series = [{ name: 'Lượt', data: chartData.top10.series }];
        chartTop.options = { ...chartTop.options, xaxis: { categories: chartData.top10.labels } };
    }
};

// --- Methods ---
const applyQuickRange = (value) => {
  if (!value) return;
  const { start, end } = quick_range_to_dates(value);
  filters.start = start;
  filters.end = end;
};

const quick_range_to_dates = (quick) => {
  const today = new Date();
  const format = (d) => qDate.formatDate(d, 'YYYY-MM-DD');
  if (quick === 'today') return { start: format(today), end: format(today) };
  if (quick === 'last7') return { start: format(qDate.subtractFromDate(today, { days: 6 })), end: format(today) };
  if (quick === 'last30') return { start: format(qDate.subtractFromDate(today, { days: 29 })), end: format(today) };
  if (quick === 'thisMonth') return { start: format(qDate.startOfDate(today, 'month')), end: format(today) };
  if (quick === 'prevMonth') {
    const prev = qDate.subtractFromDate(today, { month: 1 });
    return { start: format(qDate.startOfDate(prev, 'month')), end: format(qDate.endOfDate(prev, 'month')) };
  }
  return { start: '', end: '' };
};

const fetchData = async () => {
  loading.value = true;
  error.value = null;
  // Reset dữ liệu biểu đồ để tránh hiển thị dữ liệu cũ khi có lỗi
  resetChartData();

  const params = new URLSearchParams({
    page: pagination.value.page,
    pageSize: pagination.value.rowsPerPage,
  });
  if (filters.quick) params.append('quick', filters.quick);
  if (!filters.quick && filters.start) params.append('start', filters.start);
  if (!filters.quick && filters.end) params.append('end', filters.end);
  if (filters.q) params.append('q', filters.q);

  try {
    const { data } = await api.get('/vehicle-log', { params });
    items.value = data.items || [];
    pagination.value.rowsNumber = data.total || 0;
    kpi.value = data.kpi || kpi.value;
    updateChartData(data.chart);
  } catch (err) {
    console.error("Lỗi khi tải dữ liệu:", err);
    // CẢI TIẾN: Gán thông báo lỗi chi tiết để hiển thị trên UI
    error.value = err.response?.data?.detail || err.message || 'Một lỗi không xác định đã xảy ra.';
    // Reset các giá trị khác
    items.value = [];
    pagination.value.rowsNumber = 0;
  } finally {
    loading.value = false;
  }
};

const handleTableRequest = (props) => {
  pagination.value.page = props.pagination.page;
  pagination.value.rowsPerPage = props.pagination.rowsPerPage;
  fetchData();
};

const exportExcel = async () => {
  const params = new URLSearchParams();
  if (filters.quick) params.append('quick', filters.quick);
  if (!filters.quick && filters.start) params.append('start', filters.start);
  if (!filters.quick && filters.end) params.append('end', filters.end);
  if (filters.q) params.append('q', filters.q);
  
  $q.loading.show({ message: 'Đang tạo file Excel...' });
  try {
    const response = await api.get('/vehicle-log/export', { params, responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    const filename = `NhatKyXe_Export_${new Date().toISOString().slice(0, 10)}.xlsx`;
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch(err) {
    $q.notify({ type: 'negative', message: 'Xuất file Excel thất bại.' });
  } finally {
    $q.loading.hide();
  }
};

watch(filters, () => {
  // Khi bộ lọc thay đổi, quay về trang 1
  pagination.value.page = 1;
  fetchData();
}, { deep: true });

onMounted(() => {
  applyQuickRange(filters.quick);
  // fetchData sẽ được gọi bởi watch ngay sau đó
});
</script>

