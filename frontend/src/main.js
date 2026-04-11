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
})

// 2. Создаем экземпляр приложения
const app = createApp(App)

// 3. Подключаем плагины (Роутер и Vuetify)
app.use(router)
app.use(vuetify)

// 4. Монтируем в HTML
app.mount('#app')