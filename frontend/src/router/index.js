import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import JournalView from '../views/JournalView.vue'
import AdminView from '../views/AdminView.vue'
import { clearAuthData, getUserRole, hasUsableSession } from '../api/authStorage'

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
  },
  {
    path: '/admin',
    name: 'Admin',
    component: AdminView,
    meta: { requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Защита маршрута: проверяем токен в обоих хранилищах
router.beforeEach((to, from, next) => {
  // Ищем токен в обоих местах
  const userRole = getUserRole()
  const isAuthenticated = hasUsableSession()
  if (!isAuthenticated) {
    clearAuthData()
  }
  if (to.name !== 'Login' && !isAuthenticated) {
    next({ name: 'Login' })
  } else if (to.meta.requiresAdmin && userRole !== 'admin') {
    // Если маршрут требует админа, а пользователь не админ
    next({ name: 'Journal' })
  } else if (to.name === 'Login' && isAuthenticated) {
    // Если пользователь аутентифицирован и попытается перейти на логин,
    // перенаправляем на нужную страницу в зависимости от роли
    if (userRole === 'admin') {
      next({ name: 'Admin' })
    } else {
      next({ name: 'Journal' })
    }
  } else {
    next()
  }
})
export default router