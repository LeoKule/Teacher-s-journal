<template>
  <v-container>
    <div class="d-flex justify-space-between align-center mb-5 mt-5">
      <h1 class="text-h4 font-weight-bold">Журнал преподавателя</h1>
      
      <div class="d-flex align-center gap-4">
        <v-btn icon variant="text" @click="toggleTheme">
          <v-icon>{{ theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
        </v-btn>

        <v-btn 
        icon 
        variant="text" 
        color="success" 
        @click="exportToExcel" 
        title="Экспорт в Excel"
        class="mr-2"
      >
          <v-icon>mdi-file-excel</v-icon>
        </v-btn>

        <v-btn color="error" variant="tonal" @click="logout" prepend-icon="mdi-logout">
          Выйти
        </v-btn>
      </div>
    </div>

    <v-card class="pa-4 mb-6 rounded-lg" elevation="1">
      <v-row>
        <v-col cols="12" md="4">
          <v-select
            v-model="selectedCourse"
            :items="[1, 2, 3, 4]"
            label="Курс"
            variant="outlined"
            density="comfortable"
            hide-details
            @update:model-value="onCourseChange"
          ></v-select>
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="selectedGroup"
            :items="groups"
            item-title="group_name"
            item-value="id"
            label="Группа"
            :disabled="!selectedCourse"
            :loading="loadingGroups"
            variant="outlined"
            density="comfortable"
            hide-details
            @update:model-value="onGroupChange"
          ></v-select>
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="selectedSubject"
            :items="subjects"
            item-title="name"
            item-value="id"
            label="Предмет"
            :disabled="!selectedGroup"
            :loading="loadingSubjects"
            variant="outlined"
            density="comfortable"
            hide-details
            @update:model-value="loadJournal"
          ></v-select>
        </v-col>
      </v-row>
    </v-card>

    <v-skeleton-loader
      v-if="loading"
      class="pa-0 mb-6 rounded-lg border"
      elevation="1"
      type="table-thead, table-tbody"
    ></v-skeleton-loader>

    <v-card 
      v-else-if="selectedSubject" 
      elevation="1" 
      class="rounded-lg overflow-hidden mb-6"
    >
      <v-table hover class="journal-table">
        <thead>
          <tr class="bg-surface-variant">
            <th class="sticky-column font-weight-medium bg-surface">Студент</th>
            <th v-for="lesson in lessons" :key="lesson.id" class="text-center font-weight-bold bg-surface">
              {{ formatDate(lesson.lesson_date) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="student in students" :key="student.id">
            <td class="sticky-column font-weight-medium bg-surface">
              {{ student.full_name }}
            </td>
            <td v-for="lesson in lessons" :key="lesson.id" class="text-center">
              <v-btn 
                variant="text" 
                density="comfortable" 
                :color="getGradeColor(getGrade(student.id, lesson.id))"
                class="font-weight-bold grade-btn"
                min-width="40"
                min-height="40"
                @click="openEditDialog(student, lesson)"
              >
                {{ getGrade(student.id, lesson.id) || '—' }}
                <v-icon v-if="getComment(student.id, lesson.id)" size="x-small" class="ml-1">
                  mdi-comment-text-outline
                </v-icon>
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <v-alert
      v-else-if="!selectedSubject && !loading"
      type="info"
      variant="tonal"
      class="mt-5"
    >
      Пожалуйста, выберите курс, группу и предмет для отображения журнала.
    </v-alert>

    <div v-if="loading && selectedSubject" class="text-center mt-10">
      <v-progress-circular indeterminate color="indigo" size="64"></v-progress-circular>
    </div>

    <v-dialog v-model="dialog" max-width="450px">
      <v-card class="rounded-xl pa-2">
        <v-card-title class="text-h5 text-center pt-4">Оценка и отзыв</v-card-title>
        
        <v-card-text>
          <div class="mb-5 text-center grey--text">
            <v-chip color="indigo" variant="outlined" size="small" class="mr-2">
              {{ selectedStudent?.full_name }}
            </v-chip>
            <v-chip color="grey" variant="outlined" size="small">
              {{ formatDate(selectedLesson?.lesson_date) }}
            </v-chip>
          </div>
          
          <v-select
            v-model="newGradeValue"
            :items="[2, 3, 4, 5, 'Н']"
            label="Выберите оценку или 'Н'"
            variant="outlined"
            prepend-inner-icon="mdi-star"
            class="mb-2"
          ></v-select>

          <v-textarea
            v-model="newComment"
            label="Комментарий (необязательно)"
            variant="outlined"
            rows="3"
            prepend-inner-icon="mdi-message-draw"
            counter
            maxlength="100"
          ></v-textarea>
        </v-card-text>

        <v-card-actions class="pb-4 px-4">
          <v-btn color="grey-darken-1" variant="text" @click="dialog = false">Отмена</v-btn>
          <v-spacer></v-spacer>
          <v-btn 
            color="indigo-darken-2" 
            variant="elevated" 
            min-width="120"
            :loading="saving" 
            @click="saveGrade"
          >
            Сохранить
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000" rounded="pill">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Закрыть</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import * as XLSX from 'xlsx'
import { useTheme } from 'vuetify'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/axios'

const router = useRouter()

const theme = useTheme()

const selectedCourse = ref(null)
const selectedGroup = ref(null)
const selectedSubject = ref(null)

const groups = ref([])
const subjects = ref([])
const lessons = ref([])
const students = ref([])
const grades = ref([])

const loading = ref(false)
const loadingGroups = ref(false)
const loadingSubjects = ref(false)
const saving = ref(false)

const dialog = ref(false)
const selectedStudent = ref(null)
const selectedLesson = ref(null)
const newGradeValue = ref(null)
const newComment = ref('')

const snackbar = ref({ show: false, text: '', color: 'success' })
const showMsg = (text, color = 'success') => {
  snackbar.value = { show: true, text, color }
}

// Функция переключения
const toggleTheme = () => {
  const isDark = theme.global.current.value.dark
  // Используем актуальный способ смены
  theme.global.name.value = isDark ? 'light' : 'dark'
}

const onCourseChange = async (course) => {
  selectedGroup.value = null
  selectedSubject.value = null
  groups.value = []
  if (!course) return
  
  loadingGroups.value = true
  try {
    const res = await api.get(`/groups/by-course/${course}`)
    groups.value = res.data
  } catch (err) {
    showMsg("Ошибка загрузки групп", "error")
  } finally {
    loadingGroups.value = false
  }
}

const onGroupChange = async (groupId) => {
  selectedSubject.value = null
  subjects.value = []
  if (!groupId) return

  loadingSubjects.value = true
  try {
    const res = await api.get(`/subjects/by-group/${groupId}`)
    subjects.value = res.data
  } catch (err) {
    showMsg("Ошибка загрузки предметов", "error")
  } finally {
    loadingSubjects.value = false
  }
}

const loadJournal = async () => {
  if (!selectedGroup.value || !selectedSubject.value) return
  
  loading.value = true
  try {
    const [lRes, sRes, gRes] = await Promise.all([
      api.get(`/lessons/?group_id=${selectedGroup.value}&subject_id=${selectedSubject.value}`),
      api.get(`/students/?group_id=${selectedGroup.value}`),
      api.get('/grade-records/')
    ])

    lessons.value = lRes.data.sort((a, b) => new Date(a.lesson_date) - new Date(b.lesson_date))
    students.value = sRes.data
    grades.value = gRes.data
  } catch (err) {
    showMsg("Ошибка при загрузке журнала", "error")
  } finally {
    loading.value = false
  }
}

const getGradeRecord = (studentId, lessonId) => {
  return grades.value.find(g => g.student_id === studentId && g.lesson_id === lessonId)
}

const getGrade = (studentId, lessonId) => getGradeRecord(studentId, lessonId)?.grade_value || null
const getComment = (studentId, lessonId) => getGradeRecord(studentId, lessonId)?.comment || null

const getGradeColor = (val) => {
  if (val === 'Н') return 'grey-darken-3'
  if (!val) return 'blue-lighten-2'
  const n = Number(val)
  if (n >= 4) return 'green-darken-1'
  if (n === 3) return 'orange-darken-2'
  return 'red-darken-1'
}

const openEditDialog = (student, lesson) => {
  selectedStudent.value = student
  selectedLesson.value = lesson
  const record = getGradeRecord(student.id, lesson.id)
  newGradeValue.value = record?.grade_value || null
  newComment.value = record?.comment || ''
  dialog.value = true
}

const saveGrade = async () => {
  saving.value = true
  try {
    const payload = {
      student_id: Number(selectedStudent.value.id),
      lesson_id: Number(selectedLesson.value.id),
      grade_value: newGradeValue.value ? String(newGradeValue.value) : "", 
      comment: newComment.value || ""
    }

    await api.put('/grade-records/upsert/', payload)
    await loadJournal() 
    showMsg("Оценка успешно сохранена")
    dialog.value = false
  } catch (err) {
    console.error(err)
    showMsg("Ошибка сохранения", "error")
  } finally {
    saving.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '??'
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
}

const logout = () => {
  // Чистим оба хранилища
  localStorage.removeItem('access_token')
  sessionStorage.removeItem('access_token')
  
  router.push('/')
}

const exportToExcel = () => {
  // 1. Создаем заголовки (Студент + даты уроков)
  const headers = ['Студент', ...lessons.value.map(l => formatDate(l.lesson_date))]
  
  // 2. Собираем данные: Имя студента + его оценки
  const rows = students.value.map(student => {
    const studentGrades = lessons.value.map(lesson => {
      return getGrade(student.id, lesson.id) || '' // Оценка или пусто, если её нет
    })
    return [student.full_name, ...studentGrades]
  })

  // 3. Формируем таблицу для Excel
  const worksheet = XLSX.utils.aoa_to_sheet([headers, ...rows])
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, "Успеваемость")

  // 4. Генерируем название файла с текущей датой и скачиваем
  const dateStr = new Date().toLocaleDateString('ru-RU').replace(/\./g, '-')
  XLSX.writeFile(workbook, `Journal_${selectedGroup.value}_${dateStr}.xlsx`)
}

</script>

<style scoped>
.journal-table {
  background: transparent !important;
}

.sticky-column {
  position: sticky;
  left: 0;
  z-index: 2;
  min-width: 220px;
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)) !important;
}

thead th.sticky-column {
  z-index: 3;
  background-color: rgb(var(--v-theme-surface)) !important;
}

.journal-table :deep(table) {
  background-color: transparent !important;
}

.journal-table :deep(td:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05) !important;
}

.grade-btn {
  font-size: 1.05rem;
  transition: all 0.2s;
}

.grade-btn:hover {
  transform: scale(1.2); 
}

.sticky-column::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(to right, rgba(0,0,0,0.05), transparent);
  pointer-events: none;
}
</style>