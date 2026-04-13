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

const rememberMe = ref(true)
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const router = useRouter()

// АВТОМАТИЧЕСКИЙ ВХОД
onMounted(() => {
  // Проверяем, есть ли уже сохраненный токен
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  if (token) {
    // Если токен найден, сразу переходим к журналу
    router.push('/journal')
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
    const token = response.data.access_token

    // ЛОГИКА "ЗАПОМНИТЬ МЕНЯ"
    if (rememberMe.value) {
      // Сохраняем "навсегда" и чистим временное
      localStorage.setItem('access_token', token)
      sessionStorage.removeItem('access_token')
    } else {
      // Сохраняем временно и чистим "постоянное"
      sessionStorage.setItem('access_token', token)
      localStorage.removeItem('access_token')
    }
    
    // Автоматически перенаправляем пользователя на страницу журнала
    router.push('/journal')
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