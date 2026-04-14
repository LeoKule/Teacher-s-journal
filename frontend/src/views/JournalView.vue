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
      v-else
      type="info"
      variant="tonal"
      class="mt-5"
    >
      Пожалуйста, выберите курс, группу и предмет для отображения журнала.
    </v-alert>

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
            :items="GRADE_OPTIONS"
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/axios'

// ===== КОНСТАНТЫ =====
const GRADE_OPTIONS = [2, 3, 4, 5, 'Н']
const GRADE_CONFIG = {
  'Н': { color: 'grey-darken-3', label: 'Отсутствие' },
  2: { color: 'red-darken-1', label: 'Неудовлетворительно' },
  3: { color: 'orange-darken-2', label: 'Удовлетворительно' },
  4: { color: 'green-darken-1', label: 'Хорошо' },
  5: { color: 'green-darken-1', label: 'Отлично' }
}

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

// ===== ПРОВЕРКА АВТОРИЗАЦИИ =====
onMounted(() => {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  if (!token) {
    router.push('/')
  }
})

// ===== ОПТИМИЗАЦИЯ ПОИСКА ОЦЕНОК =====
const gradesMap = computed(() => {
  const map = new Map()
  grades.value.forEach(g => {
    map.set(`${g.student_id}-${g.lesson_id}`, g)
  })
  return map
})

// Функция переключения
const toggleTheme = () => {
  const isDark = theme.global.current.value.dark
  theme.global.name.value = isDark ? 'light' : 'dark'
}

const onCourseChange = async () => {
  selectedGroup.value = null
  selectedSubject.value = null
  groups.value = []
  subjects.value = []
  
  if (!selectedCourse.value) return
  
  loadingGroups.value = true
  try {
    const res = await api.get(`/groups/by-course/${selectedCourse.value}`)
    groups.value = res.data
  } catch (err) {
    handleApiError(err, "Ошибка загрузки групп")
  } finally {
    loadingGroups.value = false
  }
}

const onGroupChange = async () => {
  selectedSubject.value = null
  subjects.value = []
  
  if (!selectedGroup.value) return
  
  loadingSubjects.value = true
  try {
    // Исправлен путь: добавляем /by-group/
    const res = await api.get(`/subjects/by-group/${selectedGroup.value}`)
    subjects.value = res.data
  } catch (err) {
    handleApiError(err, "Ошибка загрузки предметов")
  } finally {
    loadingSubjects.value = false
  }
}

const loadJournal = async () => {
  if (!selectedGroup.value || !selectedSubject.value) return
  
  loading.value = true
  
  await new Promise(resolve => setTimeout(resolve, 1000));
  try {
    const [lRes, sRes, gRes] = await Promise.all([
      api.get(`/lessons/?group_id=${selectedGroup.value}&subject_id=${selectedSubject.value}`),
      api.get(`/students/?group_id=${selectedGroup.value}`),
      api.get(`/grade-records/?group_id=${selectedGroup.value}&subject_id=${selectedSubject.value}`)
    ])

    lessons.value = lRes.data.sort((a, b) => new Date(a.lesson_date) - new Date(b.lesson_date))
    students.value = sRes.data
    grades.value = gRes.data
  } catch (err) {
    handleApiError(err, "Не удалось загрузить журнал")
  } finally {
    loading.value = false
  }
}

const getGradeRecord = (studentId, lessonId) => {
  return gradesMap.value.get(`${studentId}-${lessonId}`) || null
}

const getGrade = (studentId, lessonId) => getGradeRecord(studentId, lessonId)?.grade_value || null
const getComment = (studentId, lessonId) => getGradeRecord(studentId, lessonId)?.comment || null

const getGradeColor = (val) => {
  if (!val) return 'blue-lighten-2'
  return GRADE_CONFIG[val]?.color || 'blue-lighten-2'
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
  // Валидация перед сохранением
  if (!newGradeValue.value) {
    showMsg('Пожалуйста, выберите оценку', 'warning')
    return
  }

  saving.value = true
  try {
    const payload = {
      lesson_id: selectedLesson.value.id,
      student_id: selectedStudent.value.id,
      grade_value: newGradeValue.value,
      comment: newComment.value
    }
    
    // Используем upsert для создания или обновления
    const response = await api.put('/grade-records/upsert/', payload)
    const savedRecord = response.data
    
    const key = `${selectedStudent.value.id}-${selectedLesson.value.id}`
    const existingGrade = gradesMap.value.get(key)
    
    if (existingGrade) {
      // Обновляем существующий рекорд
      const index = grades.value.findIndex(g => g === existingGrade)
      if (index >= 0) {
        grades.value[index] = savedRecord
      }
    } else {
      // Добавляем новый рекорд
      grades.value.push(savedRecord)
    }
    
    showMsg("Оценка успешно сохранена")
    dialog.value = false
  } catch (err) {
    handleApiError(err, "Не удалось сохранить оценку");
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
  localStorage.removeItem('user_role')
  localStorage.removeItem('user_id')
  localStorage.removeItem('full_name')
  sessionStorage.removeItem('access_token')
  sessionStorage.removeItem('user_role')
  sessionStorage.removeItem('user_id')
  sessionStorage.removeItem('full_name')
  
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

// Умный обработчик ошибок API
const handleApiError = (err, defaultMessage = "Произошла ошибка") => {
  console.error("Детали ошибки:", err);

  if (err.response) {
    // Если это ошибка валидации данных от FastAPI (422)
    if (err.response.status === 422) {
      const details = err.response.data.detail;
      if (Array.isArray(details)) {
        // Собираем все ошибки в одну строку
        const errorMessages = details.map(d => {
          const field = d.loc[d.loc.length - 1]; // Берем название поля (последний элемент в loc)
          return `Поле "${field}": ${d.msg}`;
        }).join('\n');
        
        showMsg(`Ошибка заполнения:\n${errorMessages}`, 'error');
        return;
      }
    }
    
    // Обработка других ошибок (400, 401, 404), если бэкенд прислал строку в detail
    if (err.response.data && err.response.data.detail && typeof err.response.data.detail === 'string') {
      showMsg(err.response.data.detail, 'error');
      return;
    }
  }

  // Если сервер вообще не ответил или ошибка неизвестна
  showMsg(defaultMessage, 'error');
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