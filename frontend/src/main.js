import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // Наш роутер

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css' 

// 1. Создаем объект Vuetify
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#1976D2',
          secondary: '#26A69A',
          accent: '#82B1FF',
          error: '#F44336',
          warning: '#FFC107',
          info: '#2196F3',
          success: '#4CAF50',
          background: '#FFFFFF',
          surface: '#F5F5F5',
          'surface-variant': '#EEEEEE'
        }
      },
      dark: {
        colors: {
          primary: '#6A8FD9',
          secondary: '#4DB8A8',
          accent: '#6AB7FF',
          error: '#EF9A9A',
          warning: '#FFB74D',
          info: '#64B5F6',
          success: '#81C784',
          background: '#121212',
          surface: '#1E1E1E',
          'surface-variant': '#2A2A2A'
        }
      }
    }
  }
})

// 2. Создаем экземпляр приложения
const app = createApp(App)

// 3. Подключаем плагины (Роутер и Vuetify)
app.use(router)
app.use(vuetify)

// 4. Монтируем в HTML
app.mount('#app')