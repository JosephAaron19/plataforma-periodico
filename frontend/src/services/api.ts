import axios from 'axios';

// Get base URL from env or fallback to local backend port
const API_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.DEV ? 'http://127.0.0.1:8000/api/v1' : '/api/v1');

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to inject JWT token and active company header if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    const activeCompanyId = localStorage.getItem('activeCompanyId');
    if (activeCompanyId) {
      // Custom header to tell the backend which company is currently active
      config.headers['X-Company-Id'] = activeCompanyId;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor to handle global errors (e.g., 401 Unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // If token expired or invalid, we clear storage and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('activeCompanyId');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
