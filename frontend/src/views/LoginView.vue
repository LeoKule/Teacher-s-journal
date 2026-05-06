<template>
  <v-btn
    icon
    @click="toggleTheme"
    style="position: fixed; top: 12px; left: 12px; z-index: 100;"
    variant="text"
  >
    <v-icon>{{ isDarkMode ? 'mdi-white-balance-sunny' : 'mdi-moon-waning-crescent' }}</v-icon>
  </v-btn>

  <v-container class="fill-height d-flex align-center justify-center">
    <v-card width="400" max-width="100%" elevation="8" class="pa-5 rounded-lg">
      <v-card-title class="text-h5 text-center font-weight-bold mb-4">
        Вход в журнал
      </v-card-title>

      <v-form ref="loginForm" @submit.prevent="handleLogin">
        <v-text-field
          v-model="email"
          label="Email"
          prepend-inner-icon="mdi-email-outline"
          variant="outlined"
          class="mb-2"
          :rules="emailRules"
        ></v-text-field>

        <v-text-field
          v-model="password"
          label="Пароль"
          :type="showPassword ? 'text' : 'password'"
          prepend-inner-icon="mdi-lock-outline"
          :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showPassword = !showPassword"
          variant="outlined"
          class="mb-4"
          :rules="passwordRules"
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
          :disabled="!email || !password"
        >
          Войти
        </v-btn>
      </v-form>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import api from '../api/axios'
import { getUserRole, hasUsableSession, storeAuthData } from '../api/authStorage'

const theme = useTheme()
const isDarkMode = ref(false)

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  const newTheme = isDarkMode.value ? 'dark' : 'light'
  theme.global.name.value = newTheme
  localStorage.setItem('theme', newTheme)
}

const showPassword = ref(false)
const rememberMe = ref(true)
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const loginForm = ref(null)
const router = useRouter()

const emailRules = [
  v => !!v || 'Введите email',
  v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Некорректный формат email',
]
const passwordRules = [
  v => !!v || 'Введите пароль',
  v => v.length >= 8 || 'Минимум 8 символов',
]

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDarkMode.value = true
    theme.global.name.value = 'dark'
  }

  if (hasUsableSession()) {
    const userRole = getUserRole()
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
    // Бэк ставит httpOnly cookies (access, refresh, csrf). В теле — только метаданные.
    const response = await api.post('/token', formData)
    const { user_role } = response.data

    storeAuthData(response.data, rememberMe.value)

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
