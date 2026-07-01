import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1/',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    // Check if it is an admin request or user request
    const isAdmin = config.url.includes('admin/');
    const token = localStorage.getItem(isAdmin ? 'admin_access_token' : 'access_token');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isAdmin = originalRequest.url.includes('admin/');

    // Check if error is 401 Unauthorized and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshKey = isAdmin ? 'admin_refresh_token' : 'refresh_token';
      const accessKey = isAdmin ? 'admin_access_token' : 'access_token';
      const refreshToken = localStorage.getItem(refreshKey);

      if (refreshToken) {
        try {
          // Token refresh endpoint (admins and users both use the same refresh API)
          const response = await axios.post(
            `${api.defaults.baseURL}auth/token/refresh/`,
            { refresh: refreshToken }
          );

          if (response.status === 200) {
            const { access } = response.data;
            localStorage.setItem(accessKey, access);
            originalRequest.headers.Authorization = `Bearer ${access}`;
            return api(originalRequest);
          }
        } catch (refreshError) {
          // Refresh token is invalid/expired - log out user
          localStorage.removeItem(accessKey);
          localStorage.removeItem(refreshKey);
          if (isAdmin) {
            localStorage.removeItem('admin_user');
            window.location.href = '/admin/login';
          } else {
            localStorage.removeItem('user');
            window.location.href = '/login';
          }
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
