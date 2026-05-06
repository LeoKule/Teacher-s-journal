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
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Guards смотрят на UI-метаданные в storage. Реальная авторизация — httpOnly cookie на бэке:
// если пользователь подделает user_role и попадёт на /admin, бэк всё равно вернёт 401/403.
router.beforeEach((to, from, next) => {
  const userRole = getUserRole()
  const isAuthenticated = hasUsableSession()
  if (!isAuthenticated) {
    clearAuthData()
  }
  if (to.name !== 'Login' && !isAuthenticated) {
    next({ name: 'Login' })
  } else if (to.meta.requiresAdmin && userRole !== 'admin') {
    next({ name: 'Journal' })
  } else if (to.name === 'Login' && isAuthenticated) {
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