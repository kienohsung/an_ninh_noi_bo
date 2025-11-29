// File: security_mgmt_dev/frontend/src/stores/auth.js
import { defineStore } from 'pinia'
import api from '../api'

export const useAuthStore = defineStore('auth', {
  // CẬP NHẬT: Thêm refreshToken vào state và đọc từ localStorage
  state: () => {
    const token = localStorage.getItem('token');
    const refreshToken = localStorage.getItem('refreshToken');

    // FIX: Validate và auto-clear invalid tokens
    // Nếu token có dạng 'null', 'undefined', hoặc rỗng → clear ngay
    const isValidToken = token && token !== 'null' && token !== 'undefined' && token.trim() !== '';
    const isValidRefreshToken = refreshToken && refreshToken !== 'null' && refreshToken !== 'undefined' && refreshToken.trim() !== '';

    // Nếu có token nhưng không hợp lệ → clear localStorage để tránh white screen
    if ((token && !isValidToken) || (refreshToken && !isValidRefreshToken)) {
      console.warn('Invalid tokens detected in localStorage, clearing...');
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
    }

    return {
      user: null,
      token: isValidToken ? token : null,
      refreshToken: isValidRefreshToken ? refreshToken : null,
    }
  },
  getters: { isAuthenticated: (state) => !!state.token },
  actions: {
    async bootstrap() {
      if (!this.token) return
      try {
        const me = await api.get('/me')
        this.user = me.data
      } catch (e) {
        // FIX: Khi token hết hạn (401), clear tokens và cho phép app mount về trang login
        console.error("Bootstrap failed - tokens may be expired", e)

        // Xóa tokens hết hạn
        this.logout()

        // Không throw error - cho phép app mount bình thường
        // Router sẽ tự động redirect về login vì !isAuthenticated
      }
    },
    // CẬP NHẬT: Lưu cả 2 token sau khi đăng nhập
    async login(username, password) {
      const res = await api.post('/token', new URLSearchParams({ username, password }))
      this.token = res.data.access_token
      this.refreshToken = res.data.refresh_token
      localStorage.setItem('token', this.token)
      localStorage.setItem('refreshToken', this.refreshToken)

      // Cập nhật header mặc định cho các request sau này
      api.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;

      try {
        const me = await api.get('/me')
        this.user = me.data
      } catch (e) {
        console.error("Login failed at /me step", e);
        this.logout();
        throw e;
      }
    },
    // CẬP NHẬT: Xóa cả 2 token khi đăng xuất
    logout() {
      this.user = null;
      this.token = null;
      this.refreshToken = null;
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      delete api.defaults.headers.common['Authorization'];
    }
  }
})
