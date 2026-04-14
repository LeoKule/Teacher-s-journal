<template>
  <v-app-bar color="indigo-darken-2" dark class="mb-4">
    <v-toolbar-title class="ml-4">
       Панель администратора
    </v-toolbar-title>
    <v-spacer></v-spacer>
    <v-chip class="mr-4" variant="outlined" label>
      {{ currentUser.full_name }}
    </v-chip>
    <v-btn icon @click="handleLogout">
      <v-icon>mdi-logout</v-icon>
      <v-tooltip activator="parent">Выход</v-tooltip>
    </v-btn>
  </v-app-bar>

  <v-container class="py-4">
    <v-row>
      <v-col cols="12">
        <v-card elevation="2" class="rounded-lg">
          <v-tabs v-model="activeTab" color="indigo-darken-2">
            <!-- Вкладка: Статистика -->
            <v-tab value="statistics">
              <v-icon start>mdi-chart-bar</v-icon>
              Статистика
            </v-tab>

            <!-- Вкладка: Управление преподавателями -->
            <v-tab value="teachers">
              <v-icon start>mdi-account-multiple</v-icon>
              Преподаватели
            </v-tab>

            <!-- Вкладка: Логи аудита -->
            <v-tab value="audit">
              <v-icon start>mdi-clipboard-list</v-icon>
              Логи аудита
            </v-tab>

            <!-- Вкладка: Управление группами -->
            <v-tab value="groups">
              <v-icon start>mdi-folder-multiple</v-icon>
              Группы
            </v-tab>

          </v-tabs>

          <v-window v-model="activeTab">
              <!-- СОДЕРЖИМОЕ: Статистика -->
              <v-window-item value="statistics">
                <AdminStatistics />
              </v-window-item>

              <!-- СОДЕРЖИМОЕ: Преподаватели -->
              <v-window-item value="teachers">
                <AdminTeachers />
              </v-window-item>

              <!-- СОДЕРЖИМОЕ: Логи аудита -->
              <v-window-item value="audit">
                <AdminAuditLogs />
              </v-window-item>

              <!-- СОДЕРЖИМОЕ: Группы -->
              <v-window-item value="groups">
                <AdminGroups />
              </v-window-item>
            </v-window>
          
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/axios'
import AdminStatistics from '../components/admin/AdminStatistics.vue'
import AdminTeachers from '../components/admin/AdminTeachers.vue'
import AdminAuditLogs from '../components/admin/AdminAuditLogs.vue'
import AdminGroups from '../components/admin/AdminGroups.vue'
import { clearAuthData } from '../api/authStorage'

const router = useRouter()
const activeTab = ref('statistics')
const currentUser = ref({
  full_name: '',
  email: '',
  role: ''
})

onMounted(() => {
  // Получаем информацию администратора из localStorage (она была сохранена при логине)
  const fullName = localStorage.getItem('full_name') || sessionStorage.getItem('full_name')
  const email = localStorage.getItem('email') || sessionStorage.getItem('email')
  
  if (fullName) {
    currentUser.value = {
      full_name: fullName,
      email: email || 'admin@school.com',
      role: 'admin'
    }
  } else {
    // Если данных нет, редиректим на логин
    router.push('/')
  }
})

const handleLogout = () => {
  clearAuthData()
  router.push('/')
}
</script>

<style scoped>
</style>
