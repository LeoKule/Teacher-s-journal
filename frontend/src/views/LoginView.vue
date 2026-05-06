<template>
  <div class="login-bg" :class="{ 'login-bg--dark': isDarkMode }">
    <v-btn
      icon
      @click="toggleTheme"
      style="position: fixed; top: 12px; left: 12px; z-index: 100;"
      variant="tonal"
      size="small"
    >
      <v-icon>{{ isDarkMode ? 'mdi-white-balance-sunny' : 'mdi-moon-waning-crescent' }}</v-icon>
    </v-btn>

    <v-container class="fill-height d-flex align-center justify-center">
      <v-card
        width="420"
        max-width="100%"
        elevation="0"
        class="pa-7 rounded-xl login-card"
        :class="{ 'login-card--dark': isDarkMode }"
      >
        <div class="text-center mb-6">
          <v-icon size="48" color="indigo-darken-2">mdi-school</v-icon>
          <h1 class="text-h5 font-weight-bold mt-3 mb-1">Журнал преподавателя</h1>
          <p class="text-body-2 text-medium-emphasis">Войдите в аккаунт</p>
        </div>

        <v-form ref="loginForm" @submit.prevent="handleLogin">
          <v-text-field
            v-model="email"
            label="Email"
            prepend-inner-icon="mdi-email-outline"
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
            class="text-none font-weight-bold"
            style="letter-spacing: 0.3px;"
          >
            Войти
          </v-btn>
        </v-form>
      </v-card>
    </v-container>
  </div>
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

  const formData = new URLSearchParams()
  formData.append('username', email.value)
  formData.append('password', password.value)

  try {
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

<style scoped>
.login-bg {
  position: fixed;
  inset: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow-y: auto;
  transition: background 0.4s ease;
}

.login-bg--dark {
  background: linear-gradient(135deg, #1e1b4b 0%, #4c1d95 50%, #831843 100%);
}

.login-card {
  background: rgba(255, 255, 255, 0.92) !important;
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.25),
    0 1px 2px rgba(0, 0, 0, 0.08);
}

.login-card--dark {
  background: rgba(30, 30, 40, 0.75) !important;
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 1px 2px rgba(0, 0, 0, 0.2);
}
</style>
