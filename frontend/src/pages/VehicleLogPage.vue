<!-- File: frontend/src/pages/VehicleLogPage.vue -->
<template>
  <q-page padding>
    <div class="text-h6 q-mb-md">Nhật ký xe</div>

    <!-- Toolbar -->
    <q-card class="q-mb-md">
      <q-card-section>
        <div class="row q-col-gutter-md items-end">
          <div class="col-12 col-sm-6 col-md-2">
            <q-select dense outlined v-model="filters.quick" :options="quickOptions" label="Khoảng nhanh" emit-value map-options clearable @clear="filters.quick = null" />
          </div>
          <div class="col-12 col-sm-6 col-md-2">
            <q-input dense outlined v-model="filters.start" mask="date" label="Từ ngày" :disable="!!filters.quick">
              <template #append><q-icon name="event" class="cursor-pointer"><q-popup-proxy cover><q-date v-model="filters.start" /></q-popup-proxy></q-icon></template>
            </q-input>
          </div>
          <div class="col-12 col-sm-6 col-md-2">
            <q-input dense outlined v-model="filters.end" mask="date" label="Đến ngày" :disable="!!filters.quick">
              <template #append><q-icon name="event" class="cursor-pointer"><q-popup-proxy cover><q-date v-model="filters.end" /></q-popup-proxy></q-icon></template>
            </q-input>
          </div>
          <div class="col-12 col-sm-6 col-md-3">
            <q-input dense outlined v-model="filters.q" label="Tìm theo biển số" clearable @clear="filters.q = ''" @keyup.enter="fetchData" />
          </div>
          <div class="col-12 col-md-3">
            <q-btn label="Xuất Excel" color="secondary" @click="exportExcel" :loading="exporting" class="full-width" />
          </div>
        </div>
      </q-card-section>
    </q-card>
    
    <!-- Loading and Error States -->
    <div v-if="loading" class="text-center q-pa-lg">
      <q-spinner-dots color="primary" size="40px" />
      <div class="q-mt-sm">Đang tải dữ liệu...</div>
    </div>
    <div v-else-if="error" class="text-center q-pa-lg">
      <q-icon name="error_outline" color="negative" size="40px" />
      <div class="q-mt-sm text-negative">{{ error }}</div>
      <q-btn label="Thử lại" color="primary" @click="fetchData" class="q-mt-md" />
    </div>

    <!-- Dashboard Content -->
    <div v-else>
      <!-- KPIs -->
      <div class="row q-col-gutter-md q-mb-md">
        <div v-for="k in kpiCards" :key="k.label" class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-h6">{{ k.value }}</div>
              <div class="text-caption text-grey">{{ k.label }}</div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Charts -->
      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-12 col-lg-8"><q-card flat bordered><q-card-section><LineChart :series="chartSeries.trend" :options="chartOptions.trend" /></q-card-section></q-card></div>
        <div class="col-12 col-lg-4"><q-card flat bordered><q-card-section><BarChart :series="chartSeries.hourly" :options="chartOptions.hourly" /></q-card-section></q-card></div>
        <div class="col-12"><q-card flat bordered><q-card-section><BarChart :series="chartSeries.topPlates" :options="chartOptions.topPlates" type="bar" /></q-card-section></q-card></div>
      </div>

      <!-- Data Table -->
      <q-table
        flat bordered
        title="Chi tiết lượt xe"
        :rows="items"
        :columns="columns"
        row-key="plate"
        v-model:pagination="pagination"
        :rows-per-page-options="[10, 25, 50, 100]"
        @request="onRequest"
      />
    </div>
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue';
import { useQuasar, date as qDate } from 'quasar';
import api from '../api';
import VueApexCharts from 'vue3-apexcharts';

// Renaming components to avoid conflicts
const BarChart = VueApexCharts;
const LineChart = VueApexCharts;

const $q = useQuasar();

const loading = ref(true);
const exporting = ref(false);
const error = ref(null);

const filters = reactive({
  quick: 'last7',
  start: '',
  end: '',
  q: ''
});

const quickOptions = [
  { label: 'Hôm nay', value: 'today' },
  { label: '7 ngày qua', value: 'last7' },
  { label: '30 ngày qua', value: 'last30' },
  { label: 'Tuần này', value: 'thisWeek' },
  { label: 'Tháng này', value: 'thisMonth' },
  { label: 'Tháng trước', value: 'prevMonth' },
];

const items = ref([]);
const pagination = ref({
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0
});

const kpiCards = ref([
  { label: 'Tổng lượt xe', value: 0 },
  { label: 'TB / ngày', value: 0 },
  { label: 'Giờ cao điểm', value: '-' },
  { label: 'Xe vào nhiều nhất', value: '-' }
]);

const chartOptions = reactive({ trend: {}, hourly: {}, topPlates: {} });
const chartSeries = reactive({ trend: [], hourly: [], topPlates: [] });

const columns = [
  { name: 'plate', label: 'Biển số', field: 'plate', align: 'left', sortable: true },
  { name: 'date', label: 'Ngày', field: 'date', align: 'left', sortable: true, format: val => qDate.formatDate(val, 'DD/MM/YYYY') },
  { name: 'time', label: 'Giờ', field: 'time', align: 'left', sortable: true },
];

function updateChartData(chartData) {
  // Trend Chart
  chartOptions.trend = {
    chart: { type: 'area', height: 350, toolbar: { show: false } },
    xaxis: { type: 'datetime', categories: chartData.daily.labels },
    stroke: { curve: 'smooth' },
    dataLabels: { enabled: false },
    title: { text: 'Xu hướng lượt xe theo ngày', align: 'left' }
  };
  chartSeries.trend = [{ name: 'Số lượt', data: chartData.daily.series }];

  // Hourly Chart
  chartOptions.hourly = {
    chart: { type: 'bar', height: 350, toolbar: { show: false } },
    plotOptions: { bar: { columnWidth: '50%' } },
    xaxis: { categories: chartData.hours.labels, title: { text: 'Giờ trong ngày' } },
    dataLabels: { enabled: false },
    title: { text: 'Phân bố lượt xe theo giờ', align: 'left' }
  };
  chartSeries.hourly = [{ name: 'Số lượt', data: chartData.hours.series }];

  // Top Plates Chart
  chartOptions.topPlates = {
    chart: { type: 'bar', height: 400, toolbar: { show: false } },
    plotOptions: { bar: { horizontal: true } },
    xaxis: { categories: chartData.top10.labels },
    dataLabels: { enabled: true, textAnchor: 'start', style: { colors: ['#000'] }, offsetX: 0 },
    title: { text: 'Top 10 xe vào nhiều nhất', align: 'left' }
  };
  chartSeries.topPlates = [{ name: 'Số lượt', data: chartData.top10.series }];
}


async function fetchData(paginationReq) {
  loading.value = true;
  error.value = null;

  const page = paginationReq?.page || pagination.value.page;
  const rowsPerPage = paginationReq?.rowsPerPage || pagination.value.rowsPerPage;
  
  const params = new URLSearchParams({
    page,
    pageSize: rowsPerPage
  });
  if (filters.quick) params.set('quick', filters.quick);
  if (filters.start && !filters.quick) params.set('start', qDate.formatDate(qDate.extractDate(filters.start, 'YYYY/MM/DD'), 'YYYY-MM-DD'));
  if (filters.end && !filters.quick) params.set('end', qDate.formatDate(qDate.extractDate(filters.end, 'YYYY/MM/DD'), 'YYYY-MM-DD'));
  if (filters.q) params.set('q', filters.q);

  try {
    const { data } = await api.get('/vehicle-log', { params });
    
    items.value = data.items;
    pagination.value.rowsNumber = data.total;
    pagination.value.page = data.page;
    pagination.value.rowsPerPage = data.pageSize;
    
    // (SỬA LỖI) Chỉ cập nhật chart và kpi nếu có dữ liệu
    if (data.kpi && data.chart) {
      kpiCards.value = [
        { label: 'Tổng lượt xe', value: data.kpi.totalInRange },
        { label: 'TB / ngày', value: data.kpi.avgPerDay },
        { label: 'Giờ cao điểm', value: data.kpi.peakHour || '-' },
        { label: 'Xe vào nhiều nhất', value: data.kpi.topPlate || '-' }
      ];
      updateChartData(data.chart);
    } else {
      // Reset to empty state if no chart data
      updateChartData({ daily: {}, hours: {}, top10: {} });
    }

  } catch (err) {
    console.error("Fetch data failed:", err);
    error.value = "Không thể tải dữ liệu. Vui lòng kiểm tra log backend hoặc cấu hình Google Sheet.";
  } finally {
    loading.value = false;
  }
}

function onRequest(props) {
  fetchData(props.pagination);
}

async function exportExcel() {
  exporting.value = true;
  const params = new URLSearchParams();
  if (filters.quick) params.set('quick', filters.quick);
  if (filters.start && !filters.quick) params.set('start', qDate.formatDate(qDate.extractDate(filters.start, 'YYYY/MM/DD'), 'YYYY-MM-DD'));
  if (filters.end && !filters.quick) params.set('end', qDate.formatDate(qDate.extractDate(filters.end, 'YYYY/MM/DD'), 'YYYY-MM-DD'));
  if (filters.q) params.set('q', filters.q);

  try {
    const response = await api.get('/vehicle-log/export', { params, responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `nhat_ky_xe_${Date.now()}.xlsx`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (err) {
    $q.notify({ type: 'negative', message: 'Xuất file thất bại.' });
  } finally {
    exporting.value = false;
  }
}

watch(filters, () => {
  // Use a debounce to avoid rapid firing
  setTimeout(() => {
    fetchData({ page: 1, rowsPerPage: pagination.value.rowsPerPage });
  }, 300);
}, { deep: true });

onMounted(() => {
  fetchData();
});
</script>

