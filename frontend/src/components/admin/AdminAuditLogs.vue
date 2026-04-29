<template>
  <v-card-text class="pa-6">
    <v-row class="mb-6">
      <v-col cols="12" class="admin-section-title text-h6 font-weight-bold">
        Логи аудита
      </v-col>
    </v-row>

    <!-- Фильтры -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-select
          v-model="filterAction"
          label="Действие"
          variant="outlined"
          clearable
          :items="['create', 'update', 'delete', 'reset_password', 'block_teacher', 'promote_group']"
        ></v-select>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-select
          v-model="filterEntityType"
          label="Тип сущности"
          variant="outlined"
          clearable
          :items="['teacher', 'subject', 'group', 'lesson', 'grade_record']"
        ></v-select>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-text-field
          v-model="searchQuery"
          label="Поиск"
          variant="outlined"
          prepend-inner-icon="mdi-magnify"
          clearable
        ></v-text-field>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-row no-gutters class="gap-2">
          <v-col>
            <v-btn color="primary" block @click="loadLogs" :loading="loading">
              Обновить
            </v-btn>
          </v-col>
          <v-col>
            <v-btn color="success" variant="outlined" block prepend-icon="mdi-download" @click="exportToCsv">
              CSV
            </v-btn>
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <v-progress-linear v-if="loading" indeterminate class="mb-4"></v-progress-linear>

    <!-- Таблица логов -->
    <div v-if="!loading" class="rounded-lg overflow-hidden border">
      <v-table dense hover>
        <thead>
          <tr>
            <th class="text-left">Дата/Время</th>
            <th class="text-left">Администратор</th>
            <th class="text-left">Действие</th>
            <th class="text-left">Тип сущности</th>
            <th class="text-left">ID сущности</th>
            <th class="text-left">Описание</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in filteredLogs" :key="log.id" class="log-row">
            <td class="text-body-2">{{ formatDate(log.created_at) }}</td>
            <td class="text-body-2">
              <span v-if="log.admin_id">Admin #{{ log.admin_id }}</span>
              <span v-else class="text-medium-emphasis">Система</span>
            </td>
            <td>
              <v-chip
                :color="getActionColor(log.action)"
                variant="tonal"
                size="small"
              >
                {{ formatAction(log.action) }}
              </v-chip>
            </td>
            <td class="text-body-2">{{ formatEntityType(log.entity_type) }}</td>
            <td class="text-body-2 font-weight-bold">{{ log.entity_id || '-' }}</td>
            <td class="text-body-2">{{ log.description || '-' }}</td>
          </tr>
          <tr v-if="filteredLogs.length === 0">
            <td colspan="6" class="text-center py-4 text-medium-emphasis">
              Логи не найдены
            </td>
          </tr>
        </tbody>
      </v-table>
    </div>

    <!-- Пагинация -->
    <v-row class="mt-4">
      <v-col cols="12" class="d-flex justify-center align-center gap-2">
        <v-btn 
          :disabled="page === 1"
          @click="page--"
          icon="mdi-chevron-left"
        ></v-btn>
        <span>Страница {{ page }}</span>
        <v-btn 
          :disabled="filteredLogs.length < pageSize"
          @click="page++"
          icon="mdi-chevron-right"
        ></v-btn>
      </v-col>
    </v-row>

    <!-- Алерты -->
    <v-alert v-if="error" type="error" variant="tonal" class="mt-4" closable @click="error = ''">
      {{ error }}
    </v-alert>
  </v-card-text>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api/axios'

const logs = ref([])
const loading = ref(false)
const error = ref('')
const page = ref(1)
const pageSize = 50

const filterAction = ref('')
const filterEntityType = ref('')
const searchQuery = ref('')

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('ru-RU')
}

const formatAction = (action) => {
  const actions = {
    'create': ' Создано',
    'update': ' Обновлено',
    'delete': ' Удалено',
    'reset_password': ' Сброс пароля',
    'block_teacher': ' Блокировано',
    'unblock_teacher': ' Разблокировано',
    'promote_group': ' Перевод группы'
  }
  return actions[action] || action
}

const formatEntityType = (type) => {
  const types = {
    'teacher': ' Преподаватель',
    'subject': ' Предмет',
    'group': ' Группа',
    'lesson': ' Урок',
    'grade_record': ' Оценка'
  }
  return types[type] || type
}

const getActionColor = (action) => {
  const colors = {
    'create': 'green',
    'update': 'blue',
    'delete': 'red',
    'reset_password': 'orange',
    'block_teacher': 'red-darken-2',
    'unblock_teacher': 'green-darken-2',
    'promote_group': 'indigo'
  }
  return colors[action] || 'grey'
}

const filteredLogs = computed(() => {
  let result = logs.value

  if (filterAction.value) {
    result = result.filter(log => log.action === filterAction.value)
  }

  if (filterEntityType.value) {
    result = result.filter(log => log.entity_type === filterEntityType.value)
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(log =>
      log.description?.toLowerCase().includes(query) ||
      log.entity_id?.toString().includes(query)
    )
  }

  return result
})

const exportToCsv = () => {
  const headers = ['Дата/Время', 'Администратор', 'Действие', 'Тип сущности', 'ID сущности', 'Описание']
  const rows = filteredLogs.value.map(log => [
    formatDate(log.created_at),
    log.admin_id ? `Admin #${log.admin_id}` : 'Система',
    formatAction(log.action),
    formatEntityType(log.entity_type),
    log.entity_id || '',
    log.description || ''
  ])
  const csv = [headers, ...rows]
    .map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(','))
    .join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const loadLogs = async () => {
  try {
    loading.value = true
    const response = await api.get('/admin/audit-logs/', {
      params: {
        skip: (page.value - 1) * pageSize,
        limit: pageSize,
        action: filterAction.value,
        entity_type: filterEntityType.value
      }
    })
    logs.value = response.data
  } catch (err) {
    error.value = 'Ошибка при загрузке логов'
    console.error(err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.log-row:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.06);
}

/* Vuetify 3 v-table hardcodes rgba(0,0,0,.6) for th — overriding for dark theme */
:deep(.v-table thead th) {
  color: rgba(var(--v-theme-on-surface), var(--v-high-emphasis-opacity)) !important;
  background-color: rgb(var(--v-theme-surface-variant)) !important;
}
</style>
