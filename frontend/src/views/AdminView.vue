<template>
  <v-app-bar color="primary" dark>
    <v-btn v-if="mobile" icon @click="drawerOpen = !drawerOpen">
      <v-icon>mdi-menu</v-icon>
    </v-btn>
    <v-toolbar-title class="ml-2">
      Панель администратора
    </v-toolbar-title>
    <v-spacer></v-spacer>
    <v-btn icon @click="toggleTheme" class="mr-2">
      <v-icon>{{ isDarkMode ? 'mdi-white-balance-sunny' : 'mdi-moon-waning-crescent' }}</v-icon>
    </v-btn>
    <v-chip class="mr-4" variant="outlined" label>
      {{ currentUser.full_name }}
    </v-chip>
    <v-btn icon @click="handleLogout">
      <v-icon>mdi-logout</v-icon>
    </v-btn>
  </v-app-bar>

  <v-navigation-drawer
    v-model="drawerOpen"
    :permanent="!mobile"
    width="230"
  >
    <v-list nav density="compact" class="pt-2">
      <template v-for="section in navSections" :key="section.title">
        <v-list-subheader class="text-caption font-weight-bold">{{ section.title }}</v-list-subheader>
        <v-list-item
          v-for="item in section.items"
          :key="item.key"
          :prepend-icon="item.icon"
          :title="item.label"
          :value="item.key"
          :active="activeSection === item.key"
          color="primary"
          rounded="lg"
          @click="navigate(item.key)"
        ></v-list-item>
      </template>
    </v-list>
  </v-navigation-drawer>

  <v-main :style="!mobile ? { paddingRight: '230px' } : {}">
    <v-container fluid class="py-4">
      <v-card elevation="2" class="rounded-lg overflow-hidden">
        <component :is="currentComponent" />
      </v-card>
    </v-container>
  </v-main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme, useDisplay } from 'vuetify'
import AdminStatistics from '../components/admin/AdminStatistics.vue'
import AdminTeachers from '../components/admin/AdminTeachers.vue'
import AdminAuditLogs from '../components/admin/AdminAuditLogs.vue'
import AdminGroups from '../components/admin/AdminGroups.vue'
import AdminStudentImport from '../components/admin/AdminStudentImport.vue'
import AdminStudentRecovery from '../components/admin/AdminStudentRecovery.vue'
import AdminNotifications from '../components/admin/AdminNotifications.vue'
import AdminAnalytics from '../components/admin/AdminAnalytics.vue'
import AdminAssignments from '../components/admin/AdminAssignments.vue'
import AdminSchedule from '../components/admin/AdminSchedule.vue'
import { clearAuthData } from '../api/authStorage'

const router = useRouter()
const theme = useTheme()
const { mobile } = useDisplay()

const activeSection = ref(localStorage.getItem('admin_active_tab') || 'statistics')
const drawerOpen = ref(true)
const isDarkMode = ref(false)
const currentUser = ref({ full_name: '', email: '', role: '' })

const navSections = [
  { title: 'ОБЗОР', items: [
    { key: 'statistics', icon: 'mdi-chart-bar', label: 'Статистика' },
    { key: 'analytics', icon: 'mdi-chart-line', label: 'Аналитика' },
  ]},
  { title: 'ПОЛЬЗОВАТЕЛИ', items: [
    { key: 'teachers', icon: 'mdi-account-multiple', label: 'Преподаватели' },
    { key: 'groups', icon: 'mdi-folder-multiple', label: 'Группы' },
    { key: 'assignments', icon: 'mdi-link-variant', label: 'Назначения' },
  ]},
  { title: 'СТУДЕНТЫ', items: [
    { key: 'student-import', icon: 'mdi-file-upload', label: 'Импорт студентов' },
    { key: 'student-recovery', icon: 'mdi-restore', label: 'Восстановить студентов' },
  ]},
  { title: 'РАСПИСАНИЕ', items: [
    { key: 'schedule', icon: 'mdi-calendar-clock', label: 'Расписание' },
  ]},
  { title: 'СИСТЕМА', items: [
    { key: 'audit', icon: 'mdi-clipboard-list', label: 'Логи аудита' },
    { key: 'notifications', icon: 'mdi-bell', label: 'Уведомления' },
  ]},
]

const componentMap = {
  statistics: AdminStatistics,
  analytics: AdminAnalytics,
  teachers: AdminTeachers,
  groups: AdminGroups,
  assignments: AdminAssignments,
  'student-import': AdminStudentImport,
  'student-recovery': AdminStudentRecovery,
  schedule: AdminSchedule,
  audit: AdminAuditLogs,
  notifications: AdminNotifications,
}

const currentComponent = computed(() => componentMap[activeSection.value])

const navigate = (key) => {
  activeSection.value = key
  localStorage.setItem('admin_active_tab', key)
  if (mobile.value) drawerOpen.value = false
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDarkMode.value = true
    theme.global.name.value = 'dark'
  }

  const fullName = localStorage.getItem('full_name') || sessionStorage.getItem('full_name')
  const email = localStorage.getItem('email') || sessionStorage.getItem('email')

  if (fullName) {
    currentUser.value = { full_name: fullName, email: email || 'admin@school.com', role: 'admin' }
  } else {
    router.push('/')
  }
})

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  const newTheme = isDarkMode.value ? 'dark' : 'light'
  theme.global.name.value = newTheme
  localStorage.setItem('theme', newTheme)
}

const handleLogout = () => {
  clearAuthData()
  router.push('/')
}
</script>

<style scoped>
:deep(.admin-section-title) {
  font-size: 1.75rem !important;
  line-height: 1.35 !important;
}
</style>
