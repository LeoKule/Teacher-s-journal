import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000', 
    withCredentials: true // ОЧЕНЬ ВАЖНО! Разрешает отправку кук на сервер
});

// Добавляем токен к каждому запросу
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
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

    // Если ошибка 401 (Не авторизован) и мы еще не пробовали обновить токен
    if (error.response.status === 401 && !originalRequest._isRetry) {
      originalRequest._isRetry = true;

      try {
        // Пробуем получить новый access_token (кука с refresh отправится автоматически)
        const response = await axios.post('http://localhost:8000/refresh', {}, { withCredentials: true });
        
        // Сохраняем новый токен
        localStorage.setItem('access_token', response.data.access_token);
        
        // Повторяем оригинальный запрос с новым токеном
        originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
        return api(originalRequest);
      } catch (e) {
        // Если refresh тоже протух, выкидываем на страницу логина
        localStorage.removeItem('access_token');
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
)

export default api;