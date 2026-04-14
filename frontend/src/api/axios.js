import axios from 'axios';
import { clearAuthData, getAccessToken, updateStoredAccessToken } from './authStorage';

const api = axios.create({
    baseURL: 'http://localhost:8000', 
    withCredentials: true // ОЧЕНЬ ВАЖНО! Разрешает отправку кук на сервер
});

// Добавляем токен к каждому запросу
api.interceptors.request.use(config => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Перехватываем ошибки от сервера
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status

    // Если ошибка 401 (Не авторизован) и мы еще не пробовали обновить токен
    if (status === 401 && originalRequest && !originalRequest._isRetry) {
      originalRequest._isRetry = true;

      try {
        // Пробуем получить новый access_token (кук с refresh отправится автоматически)
        const response = await axios.post('http://localhost:8000/refresh', {}, { withCredentials: true });
        
        // Сохраняем новый токен
        updateStoredAccessToken(response.data.access_token);
        
        // Повторяем оригинальный запрос с новым токеном
        originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
        return api(originalRequest);
      } catch (e) {
        // Если refresh тоже протух, выкидываем на страницу логина
        clearAuthData();
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
)

export default api;
