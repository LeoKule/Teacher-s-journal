import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import JournalView from '../views/JournalView.vue'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: LoginView
  },
  {
    path: '/journal',
    name: 'Journal',
    component: JournalView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Защита маршрута: проверяем токен в обоих хранилищах
router.beforeEach((to, from, next) => {
  // Ищем токен в обоих местах
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  const isAuthenticated = !!token
  
  if (to.name !== 'Login' && !isAuthenticated) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router