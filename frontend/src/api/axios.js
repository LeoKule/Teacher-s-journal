import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000', 
});

// Проверяем оба места: и постоянное, и сессионное
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;