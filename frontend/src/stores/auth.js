// File: security_mgmt_dev/frontend/src/stores/auth.js
import { defineStore } from 'pinia'
import api from '../api'

export const useAuthStore = defineStore('auth', {
  // CẬP NHẬT: Thêm refreshToken vào state và đọc từ localStorage
  state: () => ({ 
    user: null, 
    token: localStorage.getItem('token') || null,
    refreshToken: localStorage.getItem('refreshToken') || null,
  }),
  getters: { isAuthenticated: (state) => !!state.token },
  actions: {
    async bootstrap () {
      if (!this.token) return
      try {
        const me = await api.get('/me')
        this.user = me.data
      } catch (e) { 
        // Lỗi ở đây có thể do token hết hạn, interceptor sẽ xử lý
        // Nếu interceptor không xử lý được (refresh token cũng hết hạn), nó sẽ tự redirect
        console.error("Bootstrap failed, interceptor should handle this.", e)
      }
    },
    // CẬP NHẬT: Lưu cả 2 token sau khi đăng nhập
    async login (username, password) {
      const res = await api.post('/token', new URLSearchParams({ username, password }))
      this.token = res.data.access_token
      this.refreshToken = res.data.refresh_token
      localStorage.setItem('token', this.token)
      localStorage.setItem('refreshToken', this.refreshToken)
      
      // Cập nhật header mặc định cho các request sau này
      api.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;
      
      const me = await api.get('/me')
      this.user = me.data
    },
    // CẬP NHẬT: Xóa cả 2 token khi đăng xuất
    logout () { 
      this.user = null; 
      this.token = null; 
      this.refreshToken = null; 
      localStorage.removeItem('token') 
      localStorage.removeItem('refreshToken')
      delete api.defaults.headers.common['Authorization'];
    }
  }
})
