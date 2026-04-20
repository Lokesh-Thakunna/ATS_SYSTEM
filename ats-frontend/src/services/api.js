import axios from 'axios';

const DEFAULT_API_URL = 'http://localhost:8000/api';
const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const configuredApiBaseUrl = rawApiBaseUrl && rawApiBaseUrl !== 'https://api.yourdomain.com'
  ? rawApiBaseUrl.replace(/\/+$/, '')
  : '';
const BASE_URL = configuredApiBaseUrl
  ? (configuredApiBaseUrl.endsWith('/api') ? configuredApiBaseUrl : `${configuredApiBaseUrl}/api`)
  : DEFAULT_API_URL;

if ((!import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE_URL === 'https://api.yourdomain.com') && import.meta.env.DEV) {
  console.warn('[API] VITE_API_BASE_URL not configured; using fallback', BASE_URL);
}

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach JWT ──────────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ats_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor: error normalisation ────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.code === 'ERR_CANCELED' || error.message === 'canceled') {
      return Promise.reject({
        type: 'CANCELED',
        name: 'AbortError',
        code: 'ERR_CANCELED',
        message: 'Request canceled.',
      });
    }

    if (error.code === 'ECONNABORTED') {
      return Promise.reject({
        type: 'TIMEOUT',
        message: 'Request timed out. Please try again.',
      });
    }

    if (!error.response) {
      return Promise.reject({ type: 'NETWORK', message: 'Network error. Please check your connection.' });
    }

    const { status, data } = error.response;

    if (status === 401) {
      localStorage.removeItem('ats_token');
      localStorage.removeItem('ats_user');
      window.location.href = '/login';
      return Promise.reject({ type: 'UNAUTHORIZED', message: 'Session expired. Please log in again.' });
    }

    if (status === 403) {
      return Promise.reject({ type: 'FORBIDDEN', message: "You don't have permission to perform this action." });
    }

    if (status >= 500) {
      return Promise.reject({ type: 'SERVER', message: 'Server error. Please try again later.' });
    }

    return Promise.reject({
      type: 'API',
      message: data?.detail || data?.error || data?.message || 'Something went wrong.',
      data,
      status,
    });
  }
);

export default api;
