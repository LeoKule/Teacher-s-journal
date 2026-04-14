<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card width="400" elevation="8" class="pa-5 rounded-lg">
      <v-card-title class="text-h5 text-center font-weight-bold mb-4">
        Вход в журнал
      </v-card-title>

      <v-form @submit.prevent="handleLogin">
        <v-text-field
          v-model="email"
          label="Email"
          prepend-inner-icon="mdi-email-outline"
          variant="outlined"
          class="mb-2"
        ></v-text-field>

        <v-text-field
          v-model="password"
          label="Пароль"
          type="password"
          prepend-inner-icon="mdi-lock-outline"
          variant="outlined"
          class="mb-4"
        ></v-text-field>

        <v-checkbox
          v-model="rememberMe"
          label="Запомнить меня"
          color="indigo-darken-2"
          density="compact"
          hide-details
          class="mb-4"
        ></v-checkbox>

        <v-alert v-if="error" type="error" variant="tonal" class="mb-4" density="compact">
          {{ error }}
        </v-alert>

        <v-btn 
          type="submit" 
          color="indigo-darken-2" 
          block 
          size="large"
          :loading="loading"
        >
          Войти
        </v-btn>
      </v-form>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted} from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/axios' 
import { getUserRole, hasUsableSession, storeAuthData } from '../api/authStorage'

const rememberMe = ref(true)
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const router = useRouter()

// АВТОМАТИЧЕСКИЙ ВХОД
onMounted(() => {
  // Проверяем, есть ли уже сохраненный токен
  if (hasUsableSession()) {
    // Получаем роль пользователя
    const userRole = getUserRole()
    // Если токен найден, перенаправляем в зависимости от роли
    if (userRole === 'admin') {
      router.push('/admin')
    } else {
      router.push('/journal')
    }
  }
})

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  
  // Собираем данные в формате Form Data, как того требует FastAPI OAuth2
  const formData = new URLSearchParams()
  formData.append('username', email.value)
  formData.append('password', password.value)

  try {
    // Отправляем запрос на наш бэкенд
    const response = await api.post('/token', formData)
    const { access_token, user_role, user_id, full_name, email: userEmail } = response.data

    // ЛОГИКА "ЗАПОМНИТЬ МЕНЯ"
    storeAuthData(response.data, rememberMe.value)
    const storage = { setItem: () => {} }
    const otherStorage = { removeItem: () => {} }

    // Сохраняем токен и информацию о пользователе
    storage.setItem('access_token', access_token)
    storage.setItem('user_role', user_role)
    storage.setItem('user_id', user_id)
    storage.setItem('full_name', full_name)
    storage.setItem('email', userEmail)

    // Чистим противоположное хранилище
    otherStorage.removeItem('access_token')
    otherStorage.removeItem('user_role')
    otherStorage.removeItem('user_id')
    otherStorage.removeItem('full_name')
    otherStorage.removeItem('email')
    
    // Перенаправляем в зависимости от роли пользователя
    if (user_role === 'admin') {
      router.push('/admin')
    } else {
      router.push('/journal')
    }
  } catch (err) {
    if (err.response && err.response.status === 401) {
      error.value = 'Неверный email или пароль.'
    } else {
      error.value = 'Ошибка соединения с сервером.'
    }
  } finally {
    loading.value = false
  }
}
</script>
