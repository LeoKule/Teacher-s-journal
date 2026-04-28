<template>
  <v-container class="pa-4">
    <h2 class="admin-section-title font-weight-bold mb-4">Аналитика по группе</h2>

    <v-row class="mb-4">
      <v-col cols="12" md="4">
        <v-select
          v-model="selectedGroupId"
          :items="groups"
          item-title="group_name"
          item-value="id"
          label="Выберите группу"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          @update:model-value="loadAnalytics"
        ></v-select>
      </v-col>
    </v-row>

    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-4"></v-progress-linear>

    <v-alert v-if="!selectedGroupId && !loading" type="info" variant="tonal" class="mb-4">
      Выберите группу для просмотра аналитики
    </v-alert>

    <template v-if="analytics && !loading">
      <!-- Сводка -->
      <v-row class="mb-4">
        <v-col cols="6" sm="3">
          <v-card class="text-center pa-3" color="indigo" variant="tonal" elevation="0" rounded="lg">
            <div class="text-h4 font-weight-bold">{{ analytics.total_students }}</div>
            <div class="text-caption text-medium-emphasis">Студентов</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card class="text-center pa-3" color="green" variant="tonal" elevation="0" rounded="lg">
            <div class="text-h4 font-weight-bold">{{ analytics.total_lessons }}</div>
            <div class="text-caption text-medium-emphasis">Занятий</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card class="text-center pa-3" color="amber" variant="tonal" elevation="0" rounded="lg">
            <div class="text-h4 font-weight-bold">
              {{ analytics.overall_avg_grade ?? '—' }}
            </div>
            <div class="text-caption text-medium-emphasis">Средний балл</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card class="text-center pa-3" color="blue" variant="tonal" elevation="0" rounded="lg">
            <div class="text-h4 font-weight-bold">
              {{ analytics.overall_attendance_rate }}%
            </div>
            <div class="text-caption text-medium-emphasis">Посещаемость</div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Графики -->
      <v-row class="mb-4">
        <!-- Средняя оценка по предметам -->
        <v-col cols="12" md="7">
          <v-card elevation="1" rounded="lg" class="pa-4">
            <div class="font-weight-medium mb-3">Средний балл по предметам</div>
            <Bar v-if="subjectChartData" :key="chartKey" :data="subjectChartData" :options="barOptions" style="max-height: 260px;" />
            <v-alert v-else type="info" variant="tonal" density="compact">Нет данных об оценках</v-alert>
          </v-card>
        </v-col>

        <!-- Распределение оценок -->
        <v-col cols="12" md="5">
          <v-card elevation="1" rounded="lg" class="pa-4">
            <div class="font-weight-medium mb-3">Распределение оценок</div>
            <Doughnut v-if="gradeDistChartData" :key="chartKey" :data="gradeDistChartData" :options="doughnutOptions" style="max-height: 260px;" />
            <v-alert v-else type="info" variant="tonal" density="compact">Нет данных об оценках</v-alert>
          </v-card>
        </v-col>
      </v-row>

      <!-- Таблица студентов -->
      <v-card elevation="1" rounded="lg">
        <v-card-title class="pa-4 pb-2 font-weight-medium">Статистика по студентам</v-card-title>
        <v-table density="compact" hover>
          <thead>
            <tr>
              <th>Студент</th>
              <th class="text-center">Средний балл</th>
              <th class="text-center">Посещаемость</th>
              <th class="text-center">2</th>
              <th class="text-center">3</th>
              <th class="text-center">4</th>
              <th class="text-center">5</th>
              <th class="text-center">Н</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in analytics.students" :key="s.student_id">
              <td>{{ s.student_name }}</td>
              <td class="text-center">
                <v-chip :color="gradeColor(s.avg_grade)" size="small" variant="tonal">
                  {{ s.avg_grade ?? '—' }}
                </v-chip>
              </td>
              <td class="text-center">{{ s.attendance_rate }}%</td>
              <td class="text-center text-error">{{ s.grade_distribution['2'] || 0 }}</td>
              <td class="text-center text-warning">{{ s.grade_distribution['3'] || 0 }}</td>
              <td class="text-center text-success">{{ s.grade_distribution['4'] || 0 }}</td>
              <td class="text-center text-success">{{ s.grade_distribution['5'] || 0 }}</td>
              <td class="text-center text-disabled">{{ s.grade_distribution['Н'] || 0 }}</td>
            </tr>
          </tbody>
        </v-table>
        <v-alert v-if="!analytics.students.length" type="info" variant="tonal" density="compact" class="ma-3">
          В группе нет студентов
        </v-alert>
      </v-card>
    </template>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useTheme } from 'vuetify'
import { Bar, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title, Tooltip, Legend,
  BarElement, CategoryScale, LinearScale,
  ArcElement,
} from 'chart.js'
import api from '../../api/axios'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement)

const theme = useTheme()
const groups = ref([])
const selectedGroupId = ref(null)
const analytics = ref(null)
const loading = ref(false)
const chartKey = ref(0)
watch(theme.current, () => { chartKey.value++ })

onMounted(async () => {
  try {
    const res = await api.get('/analytics/groups')
    groups.value = res.data
  } catch (e) {
    console.error('Ошибка загрузки групп', e)
  }
})

const loadAnalytics = async () => {
  if (!selectedGroupId.value) {
    analytics.value = null
    return
  }
  loading.value = true
  try {
    const res = await api.get(`/analytics/group/${selectedGroupId.value}`)
    analytics.value = res.data
  } catch (e) {
    console.error('Ошибка загрузки аналитики', e)
  } finally {
    loading.value = false
  }
}

const subjectChartData = computed(() => {
  if (!analytics.value?.subjects?.length) return null
  const subjects = analytics.value.subjects.filter(s => s.avg_grade !== null)
  if (!subjects.length) return null
  return {
    labels: subjects.map(s => s.subject_name),
    datasets: [{
      label: 'Средний балл',
      data: subjects.map(s => s.avg_grade),
      backgroundColor: theme.current.value.colors.primary,
      borderRadius: 6,
    }],
  }
})

const gradeDistChartData = computed(() => {
  if (!analytics.value?.subjects?.length) return null
  const total = { '2': 0, '3': 0, '4': 0, '5': 0, 'Н': 0 }
  for (const s of analytics.value.subjects) {
    for (const [k, v] of Object.entries(s.grade_distribution)) {
      total[k] = (total[k] || 0) + v
    }
  }
  const hasData = Object.values(total).some(v => v > 0)
  if (!hasData) return null
  return {
    labels: ['2', '3', '4', '5', 'Н'],
    datasets: [{
      data: ['2', '3', '4', '5', 'Н'].map(k => total[k]),
      backgroundColor: ['#ef5350', '#ffa726', '#66bb6a', '#26a69a', '#bdbdbd'],
      borderWidth: 0,
    }],
  }
})

const barOptions = {
  responsive: true,
  plugins: { legend: { display: false } },
  scales: { y: { min: 1, max: 5, ticks: { stepSize: 1 } } },
}

const doughnutOptions = {
  responsive: true,
  plugins: { legend: { position: 'bottom' } },
}

const gradeColor = (avg) => {
  if (avg === null || avg === undefined) return 'grey'
  if (avg >= 4.5) return 'green'
  if (avg >= 3.5) return 'light-green'
  if (avg >= 2.5) return 'orange'
  return 'red'
}
</script>
