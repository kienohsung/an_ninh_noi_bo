// File: frontend/src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Quasar, Dialog, Notify, Loading } from 'quasar'
import quasarLang from 'quasar/lang/vi'

// Import icon libraries
import '@quasar/extras/material-icons/material-icons.css'
// Import Quasar css
import 'quasar/dist/quasar.css'

// Import ApexCharts
import VueApexCharts from "vue3-apexcharts";

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

app.use(createPinia())
app.use(Quasar, {
  plugins: { Dialog, Notify, Loading },
  lang: quasarLang,
})

// --- SỬA LỖI: Chỉ đăng ký ApexCharts một lần duy nhất tại đây ---
app.use(VueApexCharts);

app.use(router)

const auth = useAuthStore()
// Bootstrap authentication
auth.bootstrap().then(() => {
  app.mount('#app')
})

