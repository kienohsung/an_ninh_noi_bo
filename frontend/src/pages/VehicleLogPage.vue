<!-- File: frontend/src/pages/VehicleLogPage.vue -->
<template>
  <q-page padding>
    <div class="text-h6 q-mb-md">Nhật ký xe</div>

    <!-- Toolbar Filters -->
    <q-card class="q-mb-md">
      <q-card-section>
        <div class="row q-col-gutter-md items-end">
          <div class="col-12 col-sm-6 col-md-2">
            <q-select
              v-model="filters.quick"
              :options="quickRangeOptions"
              label="Khoảng nhanh"
              dense
              outlined
              emit-value
              map-options
            />
          </div>
          <div class="col-12 col-sm-6 col-md-2">
            <q-input
              v-model="filters.start"
              label="Từ ngày"
              dense
              outlined
              type="date"
              :disable="!!filters.quick"
              stack-label
            />
          </div>
          <div class="col-12 col-sm-6 col-md-2">
            <q-input
              v-model="filters.end"
              label="Đến ngày"
              dense
              outlined
              type="date"
              :disable="!!filters.quick"
              stack-label
            />
          </div>
          <div class="col-12 col-sm-6 col-md-3">
            <q-input
              v-model="filters.q"
              label="Tìm số xe"
              dense
              outlined
              clearable
              @keyup.enter="refreshTable"
            >
              <template v-slot:append>
                <q-icon name="search" />
              </template>
            </q-input>
          </div>
          <div class="col-12 col-md-3">
            <q-btn
              label="Xuất Excel"
              color="positive"
              @click="exportExcel"
              class="full-width"
              icon="download"
              :loading="isExporting"
            />
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- Error State -->
    <q-banner v-if="error" inline-actions class="text-white bg-red q-mb-md">
      <template v-slot:avatar>
        <q-icon name="error" color="white" />
      </template>
      <b>Không thể tải dữ liệu</b>
      <p class="q-mt-xs text-caption">{{ error }}</p>
      <template v-slot:action>
        <q-btn flat color="white" label="Thử lại" @click="refreshTable" />
      </template>
    </q-banner>

    <!-- Dashboard Content -->
    <div v-if="!error">
      <!-- KPIs -->
      <div class="row q-col-gutter-md q-mb-md">
        <div v-for="kpi in kpiCards" :key="kpi.label" class="col-12 col-sm-6 col-md-3">
          <q-card>
            <q-card-section>
              <div class="text-caption text-grey">{{ kpi.label }}</div>
              <div class="text-h6 text-weight-bold">{{ kpi.value }}</div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Charts -->
      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-12 col-lg-8">
          <q-card>
            <q-card-section>
              <div class="text-subtitle1">Xu hướng theo ngày</div>
              <apexchart type="area" height="300" :options="trendChart.options" :series="trendChart.series"></apexchart>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-lg-4">
          <q-card>
            <q-card-section>
              <div class="text-subtitle1">Phân bố theo giờ</div>
              <apexchart type="bar" height="300" :options="hourChart.options" :series="hourChart.series"></apexchart>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12">
           <q-card>
            <q-card-section>
              <div class="text-subtitle1">Top 10 xe hoạt động nhiều nhất</div>
              <apexchart type="bar" height="350" :options="topPlateChart.options" :series="topPlateChart.series"></apexchart>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Data Table with Server-Side Pagination -->
      <q-card>
        <q-table
          title="Bảng dữ liệu chi tiết"
          :rows="items"
          :columns="columns"
          row-key="plate"
          v-model:pagination="pagination"
          :loading="isLoading"
          :rows-per-page-options="[10, 20, 50, 100]"
          @request="onRequest"
          binary-state-sort
          flat
        />
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue';
import { useQuasar, date as qDate } from 'quasar';
import api from '../api';

const $q = useQuasar();

// --- State ---
const isLoading = ref(false);
const isExporting = ref(false);
const error = ref(null);

const filters = reactive({
  quick: 'thisMonth',
  start: '',
  end: '',
  q: '',
});

const items = ref([]);
const kpiData = ref({});

const pagination = ref({
  sortBy: 'date',
  descending: true,
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0
});

const quickRangeOptions = [
  { label: 'Hôm nay', value: 'today' },
  { label: '7 ngày qua', value: 'last7' },
  { label: '30 ngày qua', value: 'last30' },
  { label: 'Tuần này', value: 'thisWeek' },
  { label: 'Tháng này', value: 'thisMonth' },
  { label: 'Tháng trước', value: 'prevMonth' },
  { label: 'Tất cả', value: 'all' },
  { label: 'Tùy chọn...', value: '' },
];

// Chart data holders
const trendChart = reactive({ series: [], options: {} });
const hourChart = reactive({ series: [], options: {} });
const topPlateChart = reactive({ series: [], options: {} });

// --- Computed Properties for Display ---
const kpiCards = computed(() => [
  { label: 'Tổng lượt trong khoảng', value: kpiData.value.totalInRange || 0 },
  { label: 'Trung bình/ngày', value: kpiData.value.avgPerDay || 0 },
  { label: 'Giờ cao điểm', value: kpiData.value.peakHour ? `${kpiData.value.peakHour}:00` : '-' },
  { label: 'Xe hoạt động nhiều nhất', value: kpiData.value.topPlate || '-' },
]);

const columns = [
  { name: 'plate', required: true, label: 'Số xe', align: 'left', field: 'plate', sortable: true },
  { name: 'date', label: 'Ngày', field: 'date', sortable: true, format: val => qDate.formatDate(val, 'DD/MM/YYYY') },
  { name: 'time', label: 'Giờ', field: 'time', sortable: true },
];

// --- Methods ---
async function onRequest(props) {
  const { page, rowsPerPage, sortBy, descending } = props.pagination;
  isLoading.value = true;
  error.value = null;

  const params = new URLSearchParams();
  if (filters.quick) {
    params.append('quick', filters.quick);
  } else {
    if (filters.start) params.append('start', filters.start);
    if (filters.end) params.append('end', filters.end);
  }
  if (filters.q) {
    params.append('q', filters.q);
  }
  
  params.append('page', page);
  params.append('pageSize', rowsPerPage);

  try {
    const chartParams = new URLSearchParams(params);
    chartParams.delete('page');
    chartParams.delete('pageSize');
    const chartResponse = await api.get(`/vehicle-log?${chartParams.toString()}`);
    kpiData.value = chartResponse.data.kpi || {};
    updateChartData(chartResponse.data.chart || {});

    const tableResponse = await api.get(`/vehicle-log?${params.toString()}`);
    items.value = tableResponse.data.items || [];
    
    pagination.value.page = page;
    pagination.value.rowsPerPage = rowsPerPage;
    pagination.value.sortBy = sortBy;
    pagination.value.descending = descending;
    pagination.value.rowsNumber = tableResponse.data.total || 0;

  } catch (err) {
    console.error("Lỗi khi tải dữ liệu:", err);
    error.value = err.response?.data?.detail || err.message || 'Lỗi không xác định.';
    items.value = [];
    pagination.value.rowsNumber = 0;
    kpiData.value = {};
    updateChartData({});
  } finally {
    isLoading.value = false;
  }
}

function refreshTable() {
  onRequest({ pagination: pagination.value });
}

const updateChartData = (chartData) => {
    const { daily = {}, hours = {}, top10 = {} } = chartData;

    // Trend Chart
    trendChart.series = [{ name: 'Số lượt', data: daily.series || [] }];
    trendChart.options = {
        chart: { type: 'area', height: 300, toolbar: { show: false } },
        xaxis: { categories: daily.labels || [] },
        dataLabels: { enabled: false },
        stroke: { curve: 'smooth', width: 2 },
        fill: { type: "gradient", gradient: { shadeIntensity: 1, opacityFrom: 0.7, opacityTo: 0.2, stops: [0, 90, 100] } },
    };

    // Hour Chart
    hourChart.series = [{ name: 'Số lượt', data: hours.series || [] }];
    hourChart.options = {
        chart: { type: 'bar', height: 300, toolbar: { show: false } },
        xaxis: { categories: hours.labels || [] },
        plotOptions: { bar: { borderRadius: 4, horizontal: false, } },
        dataLabels: { enabled: false }
    };

    // --- SỬA LỖI BIỂU ĐỒ TOP 10 ---
    // 1. Chuyển đổi dữ liệu sang định dạng { x: 'label', y: value } để biểu đồ hiểu đúng.
    // 2. Đảo ngược mảng để xe có số lượt cao nhất hiển thị ở trên cùng.
    const top10Data = (top10.labels || []).map((label, index) => ({
      x: label,
      y: (top10.series || [])[index] || 0
    })).reverse();

    topPlateChart.series = [{ name: 'Số lượt', data: top10Data }];
    topPlateChart.options = {
        chart: { type: 'bar', height: 350, toolbar: { show: false } },
        plotOptions: {
            bar: {
                borderRadius: 4,
                horizontal: true,
                barHeight: '70%',
            }
        },
        dataLabels: {
            enabled: true,
            textAnchor: 'start',
            style: { colors: ['#fff'] },
            offsetX: 10,
            formatter: (val) => val // Đảm bảo chỉ hiển thị số
        },
        // 3. Bỏ `xaxis.categories` vì nhãn đã nằm trong `series`.
        //    Trục X bây giờ sẽ tự động là trục số (số lượt).
        xaxis: {
           labels: {
              formatter: (val) => Math.round(val) // Làm tròn số trên trục X
           }
        },
        // 4. Trục Y sẽ tự động lấy nhãn từ thuộc tính 'x' trong dữ liệu series.
        yaxis: {
          labels: {
            show: true
          }
        }
    };
};


const exportExcel = async () => {
    isExporting.value = true;
    const params = new URLSearchParams();
    if (filters.quick) params.append('quick', filters.quick);
    else {
        if (filters.start) params.append('start', filters.start);
        if (filters.end) params.append('end', filters.end);
    }
    if (filters.q) params.append('q', filters.q);

    try {
        const response = await api.get(`/vehicle-log/export?${params.toString()}`, { responseType: 'blob' });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        const filename = `nhat_ky_xe_${qDate.formatDate(Date.now(), 'YYYY-MM-DD')}.xlsx`;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        $q.notify({ type: 'positive', message: 'Xuất file thành công!' });
    } catch (err) {
        $q.notify({ type: 'negative', message: 'Xuất file thất bại.' });
    } finally {
        isExporting.value = false;
    }
};

// --- Watchers & Lifecycle Hooks ---
watch(filters, () => {
  pagination.value.page = 1;
  refreshTable();
}, { deep: true });

onMounted(() => {
  refreshTable();
});

</script>

