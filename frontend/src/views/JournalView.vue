<template>
  <v-container fluid class="px-3">
    <div class="d-flex flex-wrap justify-space-between align-center mb-4 mt-4 gap-2">
      <h1 class="text-h5 text-sm-h4 font-weight-bold">Журнал преподавателя</h1>

      <div class="d-flex align-center" style="gap: 6px;">
        <v-tooltip :text="theme.global.current.value.dark ? 'Светлая тема' : 'Тёмная тема'" location="bottom" :content-class="headerTooltipClass">
          <template #activator="{ props }">
            <v-btn v-bind="props" icon variant="text" @click="toggleTheme">
              <v-icon>{{ theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
            </v-btn>
          </template>
        </v-tooltip>

        <v-tooltip text="Экспорт в Excel" location="bottom" :content-class="headerTooltipClass">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon
              variant="text"
              color="success"
              @click="exportToExcel"
              :disabled="!selectedSubject || lessons.length === 0"
            >
              <v-icon>mdi-file-excel</v-icon>
            </v-btn>
          </template>
        </v-tooltip>

        <v-menu v-model="notifMenu" :close-on-content-click="false" width="420">
          <template #activator="{ props }">
            <v-tooltip text="Уведомления" location="bottom" :content-class="headerTooltipClass">
              <template #activator="{ props: tooltipProps }">
                <v-btn v-bind="{ ...props, ...tooltipProps }" icon variant="text">
                  <v-badge :content="unreadCount" :model-value="unreadCount > 0" color="error">
                    <v-icon>mdi-bell</v-icon>
                  </v-badge>
                </v-btn>
              </template>
            </v-tooltip>
          </template>
          <v-card elevation="4" rounded="lg">
            <v-card-title class="d-flex align-center justify-space-between pa-4 pb-2">
              <span class="text-body-1 font-weight-bold">Уведомления</span>
              <v-btn v-if="unreadCount > 0" size="small" variant="text" color="primary" @click="markAllRead">
                Прочитать все
              </v-btn>
            </v-card-title>

            <div class="px-3 pb-2">
              <v-chip-group v-model="filterType" mandatory selected-class="bg-primary text-white">
                <v-chip value="all" size="small" variant="outlined">Все</v-chip>
                <v-chip value="announcement" size="small" variant="outlined">Объявления</v-chip>
                <v-chip value="reminder" size="small" variant="outlined">Напоминания</v-chip>
                <v-chip value="completion" size="small" variant="outlined">Завершено</v-chip>
                <v-chip value="technical" size="small" variant="outlined">Техн.</v-chip>
                <v-chip value="other" size="small" variant="outlined">Прочее</v-chip>
              </v-chip-group>
            </div>
            <v-divider></v-divider>

            <div v-if="!notifications.length" class="text-center py-8">
              <v-icon size="48" color="grey-lighten-1">mdi-bell-off-outline</v-icon>
              <div class="text-medium-emphasis text-body-2 mt-2">Уведомлений нет</div>
            </div>

            <div v-else-if="groupedVisible.length === 0" class="text-center py-8">
              <v-icon size="48" color="grey-lighten-1">mdi-filter-off-outline</v-icon>
              <div class="text-medium-emphasis text-body-2 mt-2">Нет уведомлений по фильтру</div>
            </div>

            <div v-else style="max-height: 500px; overflow-y: auto">
              <template v-for="group in groupedVisible" :key="group.label">
                <v-list-subheader class="text-caption font-weight-bold pl-4">
                  {{ group.label }}
                </v-list-subheader>
                <v-card
                  v-for="n in group.items"
                  :key="n.id"
                  flat
                  class="mx-3 mb-2 pa-3"
                  :class="{ 'notif-unread': isUnread(n) }"
                  variant="tonal"
                >
                  <div class="d-flex align-start">
                    <v-avatar :color="typeMeta(n.notification_type).color" size="36" class="mr-3 flex-shrink-0">
                      <v-icon color="white" size="20">{{ typeMeta(n.notification_type).icon }}</v-icon>
                    </v-avatar>
                    <div class="flex-grow-1" style="min-width: 0">
                      <div class="d-flex align-center justify-space-between">
                        <div class="text-body-2 font-weight-bold text-truncate">{{ n.title }}</div>
                        <v-btn
                          v-if="isUnread(n)"
                          icon
                          size="x-small"
                          variant="text"
                          title="Отметить прочитано"
                          @click="markOneRead(n)"
                        >
                          <v-icon size="14">mdi-close</v-icon>
                        </v-btn>
                      </div>
                      <div class="text-body-2 text-medium-emphasis" style="white-space: pre-wrap; word-break: break-word">
                        {{ n.message }}
                      </div>
                      <div class="text-caption text-medium-emphasis mt-1">
                        {{ formatRelativeTime(n.created_at) }}
                      </div>
                    </div>
                  </div>
                </v-card>
              </template>
            </div>
          </v-card>
        </v-menu>

        <v-btn color="error" variant="tonal" @click="logout" prepend-icon="mdi-logout">
          Выйти
        </v-btn>
      </div>
    </div>

    <v-card v-if="!isMobile" class="pa-4 mb-6 rounded-lg" elevation="1">
      <v-row>
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="selectedCourse"
            :items="[1, 2, 3, 4]"
            label="Курс"
            prepend-inner-icon="mdi-school-outline"
            density="comfortable"
            hide-details
            @update:model-value="onCourseChange"
          ></v-select>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="selectedGroup"
            :items="groups"
            item-title="group_name"
            item-value="id"
            label="Группа"
            prepend-inner-icon="mdi-account-group-outline"
            :disabled="!selectedCourse"
            :loading="loadingGroups"
            density="comfortable"
            hide-details
            @update:model-value="onGroupChange"
          ></v-select>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="selectedPeriod"
            :items="periods"
            item-title="name"
            item-value="id"
            label="Семестр"
            prepend-inner-icon="mdi-calendar-month-outline"
            :disabled="!selectedGroup"
            density="comfortable"
            hide-details
            clearable
            @update:model-value="onPeriodChange"
          ></v-select>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="selectedSubject"
            :items="subjects"
            item-title="name"
            item-value="id"
            label="Предмет"
            prepend-inner-icon="mdi-book-open-variant"
            :disabled="!selectedGroup"
            :loading="loadingSubjects"
            density="comfortable"
            hide-details
            @update:model-value="loadJournal"
          ></v-select>
        </v-col>
      </v-row>
    </v-card>

    <!-- Мобильные фильтры: свёрнутая карточка с summary -->
    <v-card v-else class="mb-4 rounded-lg" elevation="1">
      <v-list-item
        :title="filtersSummary"
        :subtitle="filtersExpanded ? 'Тап чтобы свернуть' : 'Тап чтобы изменить'"
        @click="filtersExpanded = !filtersExpanded"
      >
        <template #prepend>
          <v-icon color="primary">mdi-filter-variant</v-icon>
        </template>
        <template #append>
          <v-icon>{{ filtersExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
        </template>
      </v-list-item>
      <v-expand-transition>
        <div v-show="filtersExpanded" class="pa-3 pt-0">
          <v-select
            v-model="selectedCourse"
            :items="[1, 2, 3, 4]"
            label="Курс"
            prepend-inner-icon="mdi-school-outline"
            density="comfortable"
            variant="outlined"
            hide-details
            class="mb-3"
            @update:model-value="onCourseChange"
          ></v-select>
          <v-select
            v-model="selectedGroup"
            :items="groups"
            item-title="group_name"
            item-value="id"
            label="Группа"
            prepend-inner-icon="mdi-account-group-outline"
            :disabled="!selectedCourse"
            :loading="loadingGroups"
            density="comfortable"
            variant="outlined"
            hide-details
            class="mb-3"
            @update:model-value="onGroupChange"
          ></v-select>
          <v-select
            v-model="selectedPeriod"
            :items="periods"
            item-title="name"
            item-value="id"
            label="Семестр"
            prepend-inner-icon="mdi-calendar-month-outline"
            :disabled="!selectedGroup"
            density="comfortable"
            variant="outlined"
            hide-details
            clearable
            class="mb-3"
            @update:model-value="onPeriodChange"
          ></v-select>
          <v-select
            v-model="selectedSubject"
            :items="subjects"
            item-title="name"
            item-value="id"
            label="Предмет"
            prepend-inner-icon="mdi-book-open-variant"
            :disabled="!selectedGroup"
            :loading="loadingSubjects"
            density="comfortable"
            variant="outlined"
            hide-details
            @update:model-value="loadJournal"
          ></v-select>
        </div>
      </v-expand-transition>
    </v-card>

    <v-skeleton-loader
      v-if="loading"
      class="pa-0 mb-6 rounded-lg border"
      elevation="1"
      type="table-thead, table-tbody"
    ></v-skeleton-loader>

    <v-card
      v-else-if="selectedSubject && !isMobile"
      elevation="1"
      class="rounded-lg mb-6"
    >
      <div class="journal-scroll" @wheel="onJournalWheel">
        <v-table hover class="journal-table">
          <thead>
            <tr>
              <th class="sticky-column sticky-header num-col text-center">№</th>
              <th class="sticky-column sticky-column--name sticky-header">Студент</th>
              <th
                v-for="lesson in lessons"
                :key="lesson.id"
                class="text-center sticky-header date-col"
              >
                <div class="text-body-2 font-weight-bold">{{ formatDate(lesson.lesson_date) }}</div>
                <div class="text-caption text-medium-emphasis">{{ formatDayOfWeek(lesson.lesson_date) }}</div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(student, idx) in students" :key="student.id" class="journal-row">
              <td class="sticky-column num-col text-center text-medium-emphasis">{{ idx + 1 }}</td>
              <td class="sticky-column sticky-column--name font-weight-medium">
                {{ student.full_name }}
              </td>
              <td v-for="lesson in lessons" :key="lesson.id" class="text-center grade-cell">
                <v-btn
                  :variant="getGrade(student.id, lesson.id) ? 'flat' : 'text'"
                  density="compact"
                  :color="getGradeColor(getGrade(student.id, lesson.id))"
                  class="font-weight-bold grade-btn"
                  size="small"
                  min-width="34"
                  min-height="30"
                  rounded="md"
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
      </div>
    </v-card>

    <!-- Мобильный режим: лента дат + список студентов -->
    <template v-else-if="selectedSubject && isMobile">
      <div v-if="!lessons.length" class="text-center pa-8 text-medium-emphasis">
        <v-icon size="48" color="grey-lighten-1">mdi-calendar-blank-outline</v-icon>
        <div class="mt-3">У этого предмета пока нет уроков</div>
      </div>

      <template v-else>
        <!-- Горизонтальная лента дат -->
        <div ref="dateStripRef" class="date-strip mb-3">
          <button
            v-for="lesson in lessons"
            :key="lesson.id"
            type="button"
            class="date-chip"
            :class="{ 'date-chip--active': selectedLessonMobile?.id === lesson.id }"
            @click="selectedLessonMobile = lesson"
          >
            <div class="date-chip__day">{{ formatDate(lesson.lesson_date) }}</div>
            <div class="date-chip__weekday">{{ formatDayOfWeek(lesson.lesson_date) }}</div>
          </button>
        </div>

        <!-- Список студентов с оценками за выбранный день -->
        <div v-if="selectedLessonMobile" class="d-flex flex-column mb-6" style="gap: 6px">
          <v-card
            v-for="(student, idx) in students"
            :key="student.id"
            variant="outlined"
            class="student-row"
            @click="openEditDialog(student, selectedLessonMobile)"
          >
            <div class="d-flex align-center pa-3" style="gap: 12px">
              <span class="text-caption text-medium-emphasis" style="min-width: 22px; text-align: right">
                {{ idx + 1 }}
              </span>
              <span class="flex-grow-1 text-body-2 font-weight-medium" style="min-width: 0">
                {{ student.full_name }}
              </span>
              <v-icon
                v-if="getComment(student.id, selectedLessonMobile.id)"
                size="16"
                color="primary"
              >mdi-comment-text</v-icon>
              <div
                v-if="getGrade(student.id, selectedLessonMobile.id)"
                class="grade-badge"
                :class="`bg-${getGradeColor(getGrade(student.id, selectedLessonMobile.id))}`"
              >
                {{ getGrade(student.id, selectedLessonMobile.id) }}
              </div>
              <v-icon v-else color="grey-lighten-1" size="28">mdi-plus-circle-outline</v-icon>
            </div>
          </v-card>
        </div>
      </template>
    </template>

    <v-card
      v-else
      class="text-center pa-10 mt-5 rounded-lg empty-state"
      elevation="0"
    >
      <v-icon size="72" color="primary" class="mb-4 empty-icon">mdi-notebook-outline</v-icon>
      <div class="text-h6 font-weight-bold mb-2">Журнал не выбран</div>
      <div class="text-body-2 text-medium-emphasis">
        Выберите курс, группу, семестр и предмет — таблица появится автоматически.
      </div>
    </v-card>

    <!-- Десктоп: обычный модальный диалог -->
    <v-dialog v-if="!isMobile" v-model="dialog" max-width="450px">
      <v-card class="rounded-xl pa-2">
        <v-card-title class="text-h5 text-center pt-4">Оценка и отзыв</v-card-title>

        <v-card-text>
          <div class="mb-5 text-center text-medium-emphasis">
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
          <v-btn
            v-if="selectedGradeId"
            color="error"
            variant="text"
            :loading="deleting"
            @click="deleteGrade"
          >
            <v-icon start>mdi-delete</v-icon>
            Удалить
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" @click="dialog = false">Отмена</v-btn>
          <v-btn
            color="primary"
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

    <!-- Мобила: bottom sheet с большими кнопками -->
    <v-bottom-sheet v-else v-model="dialog" inset>
      <v-card class="rounded-t-xl mobile-grade-sheet">
        <v-card-title class="pa-4 pb-1 text-body-1 font-weight-bold">
          {{ selectedStudent?.full_name }}
        </v-card-title>
        <v-card-subtitle class="px-4 pb-3 text-body-2">
          {{ formatDate(selectedLesson?.lesson_date) }} · {{ formatDayOfWeek(selectedLesson?.lesson_date) }}
        </v-card-subtitle>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <div class="d-flex justify-space-between mb-4" style="gap: 8px">
            <v-btn
              v-for="opt in GRADE_OPTIONS"
              :key="opt"
              :color="getGradeColor(opt)"
              :variant="newGradeValue === opt ? 'flat' : 'tonal'"
              size="large"
              height="56"
              class="flex-grow-1 grade-pick-btn"
              @click="newGradeValue = opt"
            >
              {{ opt }}
            </v-btn>
          </div>
          <v-textarea
            v-model="newComment"
            label="Комментарий (необязательно)"
            variant="outlined"
            rows="2"
            counter
            maxlength="100"
            density="compact"
            hide-details="auto"
          ></v-textarea>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-btn
            v-if="selectedGradeId"
            color="error"
            variant="text"
            :loading="deleting"
            prepend-icon="mdi-delete"
            @click="deleteGrade"
          >
            Удалить
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="dialog = false">Отмена</v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            :loading="saving"
            :disabled="!newGradeValue"
            @click="saveGrade"
          >
            Сохранить
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-bottom-sheet>

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
import { useTheme, useDisplay } from 'vuetify'
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/axios'
import { clearAuthData } from '../api/authStorage'

// ===== КОНСТАНТЫ =====
const GRADE_OPTIONS = [2, 3, 4, 5, 'Н']
const GRADE_CONFIG = {
  'Н': { color: 'grey', label: 'Отсутствие' },
  2: { color: 'error', label: 'Неудовлетворительно' },
  3: { color: 'warning', label: 'Удовлетворительно' },
  4: { color: 'success', label: 'Хорошо' },
  5: { color: 'success', label: 'Отлично' }
}

const router = useRouter()

const theme = useTheme()
const display = useDisplay()
const isMobile = computed(() => display.mdAndDown.value)

// Инвертированный tooltip: на светлой теме — тёмный, на тёмной — светлый
const headerTooltipClass = computed(() =>
  theme.global.current.value.dark
    ? 'bg-grey-lighten-4 text-grey-darken-4 font-weight-medium'
    : 'bg-grey-darken-4 text-white font-weight-medium'
)

const selectedCourse = ref(null)
const selectedGroup = ref(null)
const selectedPeriod = ref(null)
const selectedSubject = ref(null)

const groups = ref([])
const periods = ref([])
const subjects = ref([])
const lessons = ref([])
const students = ref([])
const grades = ref([])

const loading = ref(false)
const loadingGroups = ref(false)
const loadingSubjects = ref(false)
const saving = ref(false)
const deleting = ref(false)
const selectedGradeId = ref(null)

const dialog = ref(false)
const selectedStudent = ref(null)
const selectedLesson = ref(null)
const newGradeValue = ref(null)
const newComment = ref('')

// Мобильный режим
const selectedLessonMobile = ref(null)
const filtersExpanded = ref(false)
const dateStripRef = ref(null)

const filtersSummary = computed(() => {
  if (!selectedSubject.value) return 'Выберите группу и предмет'
  const parts = []
  if (selectedCourse.value) parts.push(`${selectedCourse.value} курс`)
  const g = groups.value.find(x => x.id === selectedGroup.value)
  if (g) parts.push(g.group_name)
  const p = periods.value.find(x => x.id === selectedPeriod.value)
  if (p) parts.push(p.name)
  const s = subjects.value.find(x => x.id === selectedSubject.value)
  if (s) parts.push(s.name)
  return parts.join(' · ')
})

const snackbar = ref({ show: false, text: '', color: 'success' })
const showMsg = (text, color = 'success') => {
  snackbar.value = { show: true, text, color }
}

// ===== УВЕДОМЛЕНИЯ =====
const NOTIF_TYPE_MAP = {
  announcement: { icon: 'mdi-bullhorn', color: 'orange' },
  reminder:     { icon: 'mdi-clock-alert', color: 'warning' },
  completion:   { icon: 'mdi-check-circle', color: 'success' },
  technical:    { icon: 'mdi-information', color: 'info' },
  other:        { icon: 'mdi-bell', color: 'grey' },
}
const typeMeta = (t) => NOTIF_TYPE_MAP[t] || NOTIF_TYPE_MAP.other

const notifications = ref([])
const notifMenu = ref(false)
const filterType = ref('all')

const isUnread = (n) => !n.is_read

const unreadCount = computed(() =>
  notifications.value.filter(n => isUnread(n)).length
)

const visibleNotifications = computed(() =>
  filterType.value === 'all'
    ? notifications.value
    : notifications.value.filter(n => n.notification_type === filterType.value)
)

const groupedVisible = computed(() => {
  const today = new Date(); today.setHours(0, 0, 0, 0)
  const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1)
  const weekAgo = new Date(today); weekAgo.setDate(weekAgo.getDate() - 7)

  const buckets = { today: [], yesterday: [], week: [], older: [] }
  for (const n of visibleNotifications.value) {
    const d = new Date(n.created_at)
    if (d >= today) buckets.today.push(n)
    else if (d >= yesterday) buckets.yesterday.push(n)
    else if (d >= weekAgo) buckets.week.push(n)
    else buckets.older.push(n)
  }

  const out = []
  if (buckets.today.length) out.push({ label: 'Сегодня', items: buckets.today })
  if (buckets.yesterday.length) out.push({ label: 'Вчера', items: buckets.yesterday })
  if (buckets.week.length) out.push({ label: 'На этой неделе', items: buckets.week })
  if (buckets.older.length) out.push({ label: 'Раньше', items: buckets.older })
  return out
})

const formatRelativeTime = (iso) => {
  const diffMs = Date.now() - new Date(iso).getTime()
  const min = Math.floor(diffMs / 60000)
  if (min < 1) return 'только что'
  if (min < 60) return `${min} мин назад`
  const h = Math.floor(min / 60)
  if (h < 24) return `${h} ч назад`
  return new Date(iso).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
}

const loadNotifications = async () => {
  try {
    const res = await api.get('/notifications/my')
    notifications.value = res.data
  } catch (err) {
    console.error('Не удалось загрузить уведомления:', err)
  }
}

const markOneRead = async (n) => {
  if (n.is_read) return
  // Оптимистично отмечаем в UI, потом синхронизируем с сервером
  n.is_read = true
  try {
    await api.post(`/notifications/${n.id}/read`)
  } catch (err) {
    // Откат при ошибке
    n.is_read = false
    console.error('Не удалось отметить уведомление прочитанным:', err)
  }
}

const markAllRead = async () => {
  const unread = notifications.value.filter(n => !n.is_read)
  if (!unread.length) return
  // Оптимистично
  unread.forEach(n => { n.is_read = true })
  try {
    await api.post('/notifications/mark-all-read')
  } catch (err) {
    // Откат
    unread.forEach(n => { n.is_read = false })
    console.error('Не удалось отметить все уведомления прочитанными:', err)
  }
}

// ===== ПРОВЕРКА АВТОРИЗАЦИИ =====
onMounted(() => {
  const role = localStorage.getItem('user_role') || sessionStorage.getItem('user_role')
  if (!role) {
    router.push('/')
  }
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme) {
    theme.global.name.value = savedTheme
  }
  loadNotifications()
})

// ===== ОПТИМИЗАЦИЯ ПОИСКА ОЦЕНОК =====
const gradesMap = computed(() => {
  const map = new Map()
  grades.value.forEach(g => {
    map.set(`${g.student_id}-${g.lesson_id}`, g)
  })
  return map
})

// При смене списка уроков — выбираем ближайший к сегодня (или последний прошедший)
watch(lessons, async (newLessons) => {
  if (!newLessons || !newLessons.length) {
    selectedLessonMobile.value = null
    return
  }
  const today = new Date().toISOString().slice(0, 10)
  const upcoming = newLessons.find(l => l.lesson_date >= today)
  selectedLessonMobile.value = upcoming || newLessons[newLessons.length - 1]
  await nextTick()
  const stripEl = dateStripRef.value
  if (stripEl) {
    const activeChip = stripEl.querySelector('.date-chip--active')
    if (activeChip) {
      activeChip.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
    }
  }
})

// После выбора предмета на мобиле — авто-свернуть фильтры
watch(selectedSubject, (val) => {
  if (val && isMobile.value) {
    filtersExpanded.value = false
  }
})

// Функция переключения
const toggleTheme = () => {
  const isDark = theme.global.current.value.dark
  const newTheme = isDark ? 'light' : 'dark'
  theme.global.name.value = newTheme
  localStorage.setItem('theme', newTheme)
}

const onCourseChange = async () => {
  selectedGroup.value = null
  selectedPeriod.value = null
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

const loadSubjects = async () => {
  if (!selectedGroup.value) return
  loadingSubjects.value = true
  try {
    const params = selectedPeriod.value ? { academic_period_id: selectedPeriod.value } : {}
    const res = await api.get(`/subjects/by-group/${selectedGroup.value}`, { params })
    subjects.value = res.data
  } catch (err) {
    handleApiError(err, "Ошибка загрузки предметов")
  } finally {
    loadingSubjects.value = false
  }
}

const loadPeriods = async () => {
  if (periods.value.length) return
  try {
    const res = await api.get('/academic-periods/')
    periods.value = res.data
  } catch (err) {
    console.error('Не удалось загрузить семестры:', err)
  }
}

const onGroupChange = async () => {
  selectedSubject.value = null
  subjects.value = []

  if (!selectedGroup.value) return

  await loadPeriods()
  await loadSubjects()
}

const onPeriodChange = async () => {
  selectedSubject.value = null
  subjects.value = []
  if (!selectedGroup.value) return
  await loadSubjects()
}

const loadJournal = async () => {
  if (!selectedGroup.value || !selectedSubject.value) return

  loading.value = true

  const periodParam = selectedPeriod.value ? `&academic_period_id=${selectedPeriod.value}` : ''

  try {
    const [lRes, sRes, gRes] = await Promise.all([
      api.get(`/lessons/?group_id=${selectedGroup.value}&subject_id=${selectedSubject.value}${periodParam}`),
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
  if (!val) return 'primary'
  return GRADE_CONFIG[val]?.color || 'primary'
}

const openEditDialog = (student, lesson) => {
  selectedStudent.value = student
  selectedLesson.value = lesson
  const record = getGradeRecord(student.id, lesson.id)
  newGradeValue.value = record?.grade_value || null
  newComment.value = record?.comment || ''
  selectedGradeId.value = record?.id || null
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

const deleteGrade = async () => {
  deleting.value = true
  try {
    await api.delete(`/grade-records/${selectedGradeId.value}`)
    grades.value = grades.value.filter(
      g => !(g.student_id === selectedStudent.value.id && g.lesson_id === selectedLesson.value.id)
    )
    showMsg('Оценка удалена')
    dialog.value = false
  } catch (e) {
    handleApiError(e, 'Ошибка при удалении оценки')
  } finally {
    deleting.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '??'
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
}

const formatDayOfWeek = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const days = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб']
  return days[date.getDay()]
}

// Колесо мыши над журналом: если нет горизонтальной части (обычная мышь) и есть куда скроллить вправо/влево —
// переводим вертикальный wheel в горизонтальный. Если контейнер уже на краю (scrollLeft = 0 при движении вверх,
// scrollLeft = max при движении вниз) — отдаём wheel странице, чтобы она прокручивалась естественно.
const onJournalWheel = (e) => {
  if (e.shiftKey || e.deltaX !== 0) return
  const el = e.currentTarget
  const max = el.scrollWidth - el.clientWidth
  if (max <= 0) return
  const goingRight = e.deltaY > 0
  const atRight = el.scrollLeft >= max - 1
  const atLeft = el.scrollLeft <= 0
  if ((goingRight && atRight) || (!goingRight && atLeft)) return
  e.preventDefault()
  el.scrollLeft += e.deltaY
}

const logout = () => {
  clearAuthData()
  router.push('/')
}

const exportToExcel = () => {
  const groupObj = groups.value.find(g => g.id === selectedGroup.value)
  const subjectObj = subjects.value.find(s => s.id === selectedSubject.value)
  const groupName = groupObj?.group_name || String(selectedGroup.value)
  const subjectName = subjectObj?.name || ''

  const metaRows = [
    [`Курс: ${selectedCourse.value}`],
    [`Группа: ${groupName}`],
    [`Предмет: ${subjectName}`],
    [],
  ]

  const headers = ['Студент', ...lessons.value.map(l => formatDate(l.lesson_date))]

  const rows = students.value.map(student => {
    const studentGrades = lessons.value.map(lesson => {
      const grade = getGrade(student.id, lesson.id)
      const comment = getComment(student.id, lesson.id)
      if (!grade) return ''
      return comment ? `${grade} (${comment})` : String(grade)
    })
    return [student.full_name, ...studentGrades]
  })

  const worksheet = XLSX.utils.aoa_to_sheet([...metaRows, headers, ...rows])
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, groupName.slice(0, 31))

  const dateStr = new Date().toLocaleDateString('ru-RU').replace(/\./g, '-')
  const safeName = `${groupName}_${subjectName}`.replace(/\s+/g, '_')
  XLSX.writeFile(workbook, `Журнал_${safeName}_${dateStr}.xlsx`)
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
.notif-unread {
  border-left: 3px solid rgb(var(--v-theme-primary)) !important;
}

.journal-scroll {
  overflow: auto;
  max-height: calc(100vh - 280px);
  position: relative;
}

/* Более заметные скроллбары внутри журнала */
.journal-scroll::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}
.journal-scroll::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.4);
  border-radius: 6px;
  border: 2px solid transparent;
  background-clip: padding-box;
}
.journal-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-primary), 0.7);
  background-clip: padding-box;
  border: 2px solid transparent;
}

.journal-table {
  background: transparent !important;
}

.journal-table :deep(table) {
  background-color: transparent !important;
}

/* === Sticky column (студент + №) === */
.sticky-column {
  position: sticky;
  z-index: 2;
  background-color: rgb(var(--v-theme-surface)) !important;
}

.num-col {
  left: 0;
  min-width: 50px;
  width: 50px;
}

.sticky-column--name {
  left: 50px;
  min-width: 220px;
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)) !important;
}

.sticky-column--name::after {
  content: '';
  position: absolute;
  right: -4px;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(to right, rgba(0, 0, 0, 0.08), transparent);
  pointer-events: none;
}

/* === Sticky header (даты остаются видимы при вертикальном скролле) === */
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 2;
  background-color: rgb(var(--v-theme-surface-variant)) !important;
}

thead th.sticky-column.sticky-header {
  z-index: 3;
}

.date-col {
  min-width: 64px;
  padding: 6px 4px !important;
}

/* === Zebra-полосы === */
.journal-table :deep(tbody tr.journal-row:nth-child(even) td) {
  background-color: rgba(var(--v-theme-on-surface), 0.025);
}

.journal-table :deep(tbody tr.journal-row:nth-child(even) td.sticky-column) {
  background-color: rgb(var(--v-theme-surface)) !important;
  background-image: linear-gradient(rgba(var(--v-theme-on-surface), 0.025), rgba(var(--v-theme-on-surface), 0.025));
}

/* === Hover на строке === */
.journal-table :deep(tbody tr.journal-row:hover td) {
  background-color: rgba(var(--v-theme-primary), 0.08) !important;
}

.journal-table :deep(tbody tr.journal-row:hover td.sticky-column) {
  background-color: rgb(var(--v-theme-surface)) !important;
  background-image: linear-gradient(rgba(var(--v-theme-primary), 0.08), rgba(var(--v-theme-primary), 0.08));
}

.grade-cell {
  padding: 4px !important;
}

.grade-btn {
  font-size: 0.875rem;
  letter-spacing: 0;
  transition: transform 0.2s, box-shadow 0.2s;
}

.grade-btn:hover {
  transform: scale(1.08);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

:deep(.journal-table .v-table__wrapper thead th) {
  color: rgba(var(--v-theme-on-surface), var(--v-high-emphasis-opacity)) !important;
}

/* === Empty state === */
.empty-state {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.04), rgba(var(--v-theme-primary), 0.01));
  border: 1px dashed rgba(var(--v-theme-primary), 0.2);
}

.empty-icon {
  opacity: 0.6;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

/* === Мобильная лента дат === */
.date-strip {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  padding: 4px 2px 8px;
  margin: 0 -4px;
}

.date-strip::-webkit-scrollbar {
  height: 4px;
}
.date-strip::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.3);
  border-radius: 2px;
}

.date-chip {
  flex: 0 0 auto;
  min-width: 64px;
  height: 60px;
  border-radius: 12px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  cursor: pointer;
  scroll-snap-align: start;
  transition: transform 0.15s, box-shadow 0.15s, background-color 0.15s;
  font-family: inherit;
  padding: 0 10px;
}

.date-chip:active {
  transform: scale(0.95);
}

.date-chip__day {
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1;
}

.date-chip__weekday {
  font-size: 0.7rem;
  opacity: 0.7;
  text-transform: lowercase;
  line-height: 1;
}

.date-chip--active {
  background: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.35);
}

.date-chip--active .date-chip__weekday {
  opacity: 0.9;
}

/* === Карточка студента в мобильном списке === */
.student-row {
  cursor: pointer;
  transition: background-color 0.15s, transform 0.15s;
}

.student-row:active {
  transform: scale(0.99);
  background-color: rgba(var(--v-theme-primary), 0.06);
}

/* === Бейдж оценки === */
.grade-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 1rem;
  flex-shrink: 0;
}

/* === Bottom sheet с оценкой === */
.mobile-grade-sheet .grade-pick-btn {
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: 0;
  min-width: 0;
}
</style>