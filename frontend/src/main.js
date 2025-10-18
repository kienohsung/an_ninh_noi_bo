// File: security_mgmt_dev/frontend/src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
// --- FIX: Add 'Loading' plugin from Quasar ---
import { Quasar, Dialog, Notify, Loading } from 'quasar'
import quasarLang from 'quasar/lang/vi'
import '@quasar/extras/material-icons/material-icons.css'
import 'quasar/dist/quasar.css' // dùng CSS để tránh lỗi SASS

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
app.use(createPinia())
// --- FIX: Register the 'Loading' plugin ---
app.use(Quasar, { lang: quasarLang, plugins: { Dialog, Notify, Loading } })
app.use(router)

const auth = useAuthStore()
await auth.bootstrap()

app.mount('#app')
