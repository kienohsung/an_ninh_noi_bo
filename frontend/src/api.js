// File: security_mgmt_dev/frontend/src/api.js
import axios from 'axios'

const backendHost = window.location.hostname;

const backendPort = window.location.port === '5174' ? '8001' : '8000';

const backendUrl = `http://${backendHost}:${backendPort}`;

console.log('Connecting to backend at:', backendUrl); 

const api = axios.create({ baseURL: backendUrl });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})


// === CẢI TIẾN LỚN: LOGIC TỰ ĐỘNG LÀM MỚI TOKEN ===
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  response => response,
  async (error) => {
    const originalRequest = error.config;

    // Chỉ xử lý lỗi 401 và không phải là yêu cầu thử lại
    if (error.response?.status === 401 && !originalRequest._retry) {
      
      if (isRefreshing) {
        // Nếu đang có một yêu cầu làm mới token khác chạy, đưa yêu cầu này vào hàng đợi
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        // Không có refresh token, không thể làm mới, buộc đăng xuất
        localStorage.removeItem('token');
        window.location.href = '/login';
        return Promise.reject(error);
      }
      
      try {
        const { data } = await api.post('/token/refresh', { refresh_token: refreshToken });
        
        // Cập nhật token mới vào localStorage
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('refreshToken', data.refresh_token);
        
        // Cập nhật header mặc định và header cho yêu cầu hiện tại
        api.defaults.headers.common['Authorization'] = 'Bearer ' + data.access_token;
        originalRequest.headers['Authorization'] = 'Bearer ' + data.access_token;
        
        // Thực thi lại các yêu cầu đã thất bại trong hàng đợi
        processQueue(null, data.access_token);
        
        // Thực thi lại yêu cầu ban đầu
        return api(originalRequest);

      } catch (refreshError) {
        // Nếu làm mới token thất bại (ví dụ: refresh token cũng hết hạn)
        processQueue(refreshError, null);
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Đối với các lỗi khác, trả về lỗi như bình thường
    return Promise.reject(error);
  }
);
// =======================================================


export default api

