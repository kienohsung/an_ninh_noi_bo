<!-- File: security_mgmt_dev/frontend/src/pages/DashboardPage.vue -->
<template>
  <q-page padding>
    <!-- BỘ LỌC THỜI GIAN -->
    <q-card class="q-mb-md">
      <q-card-section>
        <div class="row items-center q-col-gutter-md">
          <div class="col-auto">
            <q-btn-group push>
              <q-btn label="1 tuần" @click="setRange('last7days')" :color="filters.range === 'last7days' ? 'primary' : 'white'" :text-color="filters.range === 'last7days' ? 'white' : 'black'"/>
              <q-btn label="1 tháng" @click="setRange('last1month')" :color="filters.range === 'last1month' ? 'primary' : 'white'" :text-color="filters.range === 'last1month' ? 'white' : 'black'"/>
              <q-btn label="3 tháng" @click="setRange('last3months')" :color="filters.range === 'last3months' ? 'primary' : 'white'" :text-color="filters.range === 'last3months' ? 'white' : 'black'"/>
              <q-btn label="Tất cả" @click="setRange('all')" :color="filters.range === 'all' ? 'primary' : 'white'" :text-color="filters.range === 'all' ? 'white' : 'black'"/>
            </q-btn-group>
          </div>
          <div class="col-12 col-sm-3">
            <q-input dense outlined v-model="filters.start" mask="date" label="Từ ngày">
              <template v-slot:append>
                <q-icon name="event" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date v-model="filters.start" @update:model-value="filters.range = ''">
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup label="Đóng" color="primary" flat />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>
          <div class="col-12 col-sm-3">
             <q-input dense outlined v-model="filters.end" mask="date" label="Đến ngày">
              <template v-slot:append>
                <q-icon name="event" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date v-model="filters.end" @update:model-value="filters.range = ''">
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup label="Đóng" color="primary" flat />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>
        </div>
      </q-card-section>
    </q-card>

    <div class="row q-col-gutter-md">
      <div class="col-12 col-lg-8">
        <q-card>
          <q-card-section>
             <div class="text-subtitle1">Lượt khách vào theo ngày</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <BarChart :labels="guestsDaily.labels" :series="guestsDaily.series" title="Số khách"/>
          </q-card-section>
        </q-card>
      </div>
       <div class="col-12 col-md-6 col-lg-4">
        <q-card>
          <q-card-section>
             <div class="text-subtitle1">Lượt khách theo người đăng ký</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <PieChart :labels="guestsByUser.labels" :series="guestsByUser.series"/>
          </q-card-section>
        </q-card>
      </div>
      <div class="col-12 col-md-6 col-lg-4">
        <q-card>
          <q-card-section>
            <div class="text-subtitle1">Lượt khách theo nhà cung cấp</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <PieChart :labels="guestsBySupplier.labels" :series="guestsBySupplier.series"/>
          </q-card-section>
        </q-card>
      </div>
       <div class="col-12 col-lg-8">
        <q-card>
          <q-card-section>
            <div class="text-subtitle1">Top 10 xe vào nhiều nhất</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <BarChart :labels="guestsByPlate.labels" :series="guestsByPlate.series" title="Số lượt"/>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { reactive, onMounted, watch } from 'vue';
import { date } from 'quasar'; // Import Quasar date utility
import api from '../api';
import BarChart from '../components/charts/BarChart.vue';
import PieChart from '../components/charts/PieChart.vue';

const guestsDaily = reactive({ labels: [], series: [] });
const guestsByUser = reactive({ labels: [], series: [] });
const guestsBySupplier = reactive({ labels: [], series: [] });
const guestsByPlate = reactive({ labels: [], series: [] });

const filters = reactive({
  start: '',
  end: '',
  range: 'last7days', // default
});

// Format date to YYYY/MM/DD for q-date component
const formatDateForInput = (d) => date.formatDate(d, 'YYYY/MM/DD');

// Function to set quick date ranges
function setRange(period) {
  filters.range = period;
  const today = new Date();
  
  if (period === 'last7days') {
    const startDate = date.subtractFromDate(today, { days: 6 });
    filters.start = formatDateForInput(startDate);
    filters.end = formatDateForInput(today);
  } else if (period === 'last1month') {
    const startDate = date.subtractFromDate(today, { months: 1 });
    filters.start = formatDateForInput(startDate);
    filters.end = formatDateForInput(today);
  } else if (period === 'last3months') {
    const startDate = date.subtractFromDate(today, { months: 3 });
    filters.start = formatDateForInput(startDate);
    filters.end = formatDateForInput(today);
  } else if (period === 'all') {
    // Setting to empty will clear the filters and fetch all data
    filters.start = '';
    filters.end = '';
  }
}

async function load() {
  const params = {};
  if (filters.start) {
    // Đảm bảo gửi đi mốc thời gian bắt đầu của ngày (00:00:00)
    const startDate = new Date(filters.start);
    startDate.setHours(0, 0, 0, 0);
    params.start = startDate.toISOString();
  }
  if (filters.end) {
    // Đảm bảo gửi đi mốc thời gian kết thúc của ngày (23:59:59)
    const endDate = new Date(filters.end);
    endDate.setHours(23, 59, 59, 999);
    params.end = endDate.toISOString();
  }
  
  try {
    const [daily, byUser, bySupplier, byPlate] = await Promise.all([
      api.get('/reports/guests_daily', { params }),
      api.get('/reports/guests_by_user', { params }),
      api.get('/reports/guests_by_supplier', { params }),
      api.get('/reports/guests_by_plate', { params })
    ]);
    
    guestsDaily.labels = daily.data.labels;
    guestsDaily.series = daily.data.series;
    guestsByUser.labels = byUser.data.labels;
    guestsByUser.series = byUser.data.series;
    guestsBySupplier.labels = bySupplier.data.labels;
    guestsBySupplier.series = bySupplier.data.series;
    guestsByPlate.labels = byPlate.data.labels;
    guestsByPlate.series = byPlate.data.series;
  } catch (error) {
    console.error("Failed to load dashboard data:", error);
  }
}

// Watch for filter changes to reload data
watch(filters, load, { deep: true, immediate: false }); 

onMounted(() => {
  setRange('last7days'); // This will trigger the watch and load initial data
});
</script>
