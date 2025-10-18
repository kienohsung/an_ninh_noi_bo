// File: security_mgmt_dev/frontend/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'
import path from 'path'

export default defineConfig({
  plugins: [
    vue({ template: { transformAssetUrls } }),
    quasar() // dùng CSS build, không cần sassVariables
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') }
  },
  // Cấu hình server để chạy trên port 5174 và cho phép truy cập từ mạng LAN
  server: { host: '0.0.0.0', port: 5173 }
})
