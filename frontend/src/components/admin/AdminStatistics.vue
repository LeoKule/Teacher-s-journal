<template>
  <v-card-text class="pa-6">
    <v-row class="mb-6">
      <v-col cols="12" class="text-h6 font-weight-bold">
         Общая статистика по школе
      </v-col>
    </v-row>

    <v-row v-if="loading" class="justify-center align-center" style="min-height: 300px;">
      <v-progress-circular indeterminate color="indigo-darken-2"></v-progress-circular>
    </v-row>

    <v-row v-else-if="error" class="justify-center align-center" style="min-height: 300px;">
      <v-col cols="12" sm="8">
        <v-alert type="error" variant="tonal" class="mb-4">
          <strong>Ошибка загрузки статистики:</strong>
          <div class="mt-2">{{ error }}</div>
        </v-alert>
        <v-btn @click="loadStatistics" color="indigo-darken-2">
          <v-icon start>mdi-refresh</v-icon>
          Повторить попытку
        </v-btn>
      </v-col>
    </v-row>

    <v-row v-else class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card color="blue-lighten-4" class="rounded-lg">
          <v-card-text class="text-center py-6">
            <div class="text-h4 font-weight-bold text-blue-darken-3">{{ stats.total_teachers }}</div>
            <div class="text-body-2 text-grey-darken-2 mt-2"> Преподавателей</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card color="green-lighten-4" class="rounded-lg">
          <v-card-text class="text-center py-6">
            <div class="text-h4 font-weight-bold text-green-darken-3">{{ stats.active_teachers }}</div>
            <div class="text-body-2 text-grey-darken-2 mt-2"> Активных</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card color="purple-lighten-4" class="rounded-lg">
          <v-card-text class="text-center py-6">
            <div class="text-h4 font-weight-bold text-purple-darken-3">{{ stats.total_students }}</div>
            <div class="text-body-2 text-grey-darken-2 mt-2"> Студентов</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card color="orange-lighten-4" class="rounded-lg">
          <v-card-text class="text-center py-6">
            <div class="text-h4 font-weight-bold text-orange-darken-3">{{ stats.total_groups }}</div>
            <div class="text-body-2 text-grey-darken-2 mt-2"> Групп</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card color="indigo-lighten-4" class="rounded-lg">
          <v-card-text class="text-center py-6">
            <div class="text-h4 font-weight-bold text-indigo-darken-3">{{ stats.total_subjects }}</div>
            <div class="text-body-2 text-grey-darken-2 mt-2"> Предметов</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card color="red-lighten-4" class="rounded-lg">
          <v-card-text class="text-center py-6">
            <div class="text-h4 font-weight-bold text-red-darken-3">{{ stats.total_grades_recorded }}</div>
            <div class="text-body-2 text-grey-darken-2 mt-2"> Оценок</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card color="teal-lighten-4" class="rounded-lg">
          <v-card-text class="text-center py-6">
            <div class="text-h4 font-weight-bold text-teal-darken-3">{{ stats.average_grade || '-' }}</div>
            <div class="text-body-2 text-grey-darken-2 mt-2"> Средняя оценка</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-alert v-if="error && !loading" type="error" variant="tonal" class="mt-4">
      {{ error }}
    </v-alert>
  </v-card-text>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/axios'

const stats = ref({
  total_teachers: 0,
  total_students: 0,
  total_groups: 0,
  total_subjects: 0,
  active_teachers: 0,
  total_grades_recorded: 0,
  average_grade: null
})
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  await loadStatistics()
})

const loadStatistics = async () => {
  try {
    loading.value = true
    error.value = ''
    const response = await api.get('/admin/statistics/')
    stats.value = response.data
  } catch (err) {
    error.value = `Ошибка: ${err.response?.status || 'соединение'} - ${err.response?.data?.detail || err.message}`
    console.error('Statistics error:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
</style>
