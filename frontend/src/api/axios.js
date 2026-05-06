import axios from 'axios'
import { clearAuthData, getCsrfToken } from './authStorage'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const UNSAFE_METHODS = new Set(['post', 'put', 'patch', 'delete'])

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  if (UNSAFE_METHODS.has((config.method || '').toLowerCase())) {
    const csrf = getCsrfToken()
    if (csrf) {
      config.headers['X-CSRF-Token'] = csrf
    }
  }
  return config
})

// Refresh singleton: один параллельный refresh-запрос на всё приложение
let refreshPromise = null

const performRefresh = () => {
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${BASE_URL}/refresh`, {}, { withCredentials: true })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status

    if (status === 401 && originalRequest && !originalRequest._isRetry) {
      originalRequest._isRetry = true

      try {
        await performRefresh()
        return api(originalRequest)
      } catch (e) {
        clearAuthData()
        window.location.href = '/'
      }
    }
    return Promise.reject(error)
  }
)

export default api
