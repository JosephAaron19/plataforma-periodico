import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.DEV ? 'http://127.0.0.1:8000/api/v1' : '/api/v1');

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('amazonia_access') || localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    const activeCompanyId = localStorage.getItem('activeCompanyId');
    if (activeCompanyId) {
      config.headers['X-Company-Id'] = activeCompanyId;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('amazonia_access');
      localStorage.removeItem('amazonia_refresh');
      localStorage.removeItem('amazonia_user');
      localStorage.removeItem('activeCompanyId');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default api;
