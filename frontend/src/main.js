// File: frontend/src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Quasar, Dialog, Notify, Loading } from 'quasar'
import quasarLang from 'quasar/lang/vi'
import '@quasar/extras/material-icons/material-icons.css'
import 'quasar/dist/quasar.css'

// --- (BƯỚC 1) IMPORT APEXCHARTS ---
import VueApexCharts from "vue3-apexcharts";

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
app.use(createPinia())
app.use(Quasar, { lang: quasarLang, plugins: { Dialog, Notify, Loading } })

// --- (BƯỚC 2) ĐĂNG KÝ APEXCHARTS VỚI ỨNG DỤNG VUE ---
app.use(VueApexCharts)
// Đăng ký component với tên 'apexchart' để có thể dùng trong các file .vue
app.component('apexchart', VueApexCharts)

app.use(router)

const auth = useAuthStore()
await auth.bootstrap()

app.mount('#app')
