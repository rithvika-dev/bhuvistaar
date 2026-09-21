import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach Bearer token automatically
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('bhuvistaar_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor for centralized error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response ? error.response.status : null;

    if (status === 401) {
      // Clear invalid token & user session
      localStorage.removeItem('bhuvistaar_token');
      localStorage.removeItem('bhuvistaar_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }

    let errorMessage = 'An unexpected error occurred.';
    if (error.response && error.response.data) {
      if (typeof error.response.data.detail === 'string') {
        errorMessage = error.response.data.detail;
      } else if (Array.isArray(error.response.data.detail)) {
        errorMessage = error.response.data.detail
          .map((err) => `${err.loc.join('.')}: ${err.msg}`)
          .join(', ');
      } else if (error.response.data.message) {
        errorMessage = error.response.data.message;
      }
    } else if (error.message) {
      errorMessage = error.message;
    }

    error.friendlyMessage = errorMessage;
    return Promise.reject(error);
  }
);

export default apiClient;
