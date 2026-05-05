<template>
  <v-card-text class="pa-0">
    <v-stepper v-model="step" flat>
      <v-stepper-header>
        <v-stepper-item :value="1" title="Назначение" :complete="step > 1" color="primary"></v-stepper-item>
        <v-divider></v-divider>
        <v-stepper-item :value="2" title="Шаблоны" :complete="step > 2" color="primary"></v-stepper-item>
        <v-divider></v-divider>
        <v-stepper-item :value="3" title="Генерация" color="primary"></v-stepper-item>
      </v-stepper-header>

      <v-stepper-window>
        <!-- Шаг 1: Выбор назначения -->
        <v-stepper-window-item :value="1">
          <div class="pa-6">
            <v-row class="mb-2">
              <v-col cols="12" md="5">
                <v-select
                  v-model="selectedTeacherId"
                  :items="teachers"
                  item-title="full_name"
                  item-value="id"
                  label="Преподаватель"
                  variant="outlined"
                  clearable
                  @update:model-value="onTeacherChange"
                ></v-select>
              </v-col>
              <v-col cols="12" md="7">
                <v-select
                  v-model="selectedAssignmentId"
                  :items="assignments"
                  :item-title="assignmentLabel"
                  item-value="id"
                  label="Назначение (предмет — группа — период)"
                  variant="outlined"
                  :disabled="!selectedTeacherId"
                  :loading="assignmentsLoading"
                  clearable
                  @update:model-value="onAssignmentChange"
                ></v-select>
              </v-col>
            </v-row>
            <div class="d-flex justify-end">
              <v-btn
                color="primary"
                :disabled="!selectedAssignmentId"
                @click="step = 2"
              >
                Далее <v-icon end>mdi-arrow-right</v-icon>
              </v-btn>
            </div>
          </div>
        </v-stepper-window-item>

        <!-- Шаг 2: Шаблоны расписания -->
        <v-stepper-window-item :value="2">
          <div class="pa-6">
            <div class="d-flex align-center justify-space-between mb-4">
              <span class="text-h6 font-weight-bold">Шаблоны расписания</span>
              <v-btn color="primary" prepend-icon="mdi-plus" size="small" @click="openAddTemplateDialog">
                Добавить слот
              </v-btn>
            </div>

            <v-progress-linear v-if="templatesLoading" indeterminate class="mb-4"></v-progress-linear>

            <div v-if="!templatesLoading">
              <div v-if="templates.length === 0" class="text-center text-medium-emphasis py-8">
                Нет шаблонов расписания. Добавьте первый слот.
              </div>
              <div v-else class="rounded-lg overflow-hidden border mb-4" style="overflow-x: auto">
                <v-table density="compact">
                  <thead>
                    <tr>
                      <th class="text-left">День недели</th>
                      <th class="text-left">№ урока</th>
                      <th class="text-left">Начало</th>
                      <th class="text-left">Конец</th>
                      <th class="text-left">Аудитория</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="t in templates" :key="t.id">
                      <td class="text-body-2">{{ DAY_NAMES[t.day_of_week] }}</td>
                      <td class="text-body-2">{{ t.lesson_number }}</td>
                      <td class="text-body-2">{{ t.start_time }}</td>
                      <td class="text-body-2">{{ t.end_time }}</td>
                      <td class="text-body-2">{{ t.classroom || '—' }}</td>
                      <td>
                        <v-btn icon size="small" variant="text" color="error" @click="confirmDeleteTemplate(t)">
                          <v-icon size="18">mdi-delete</v-icon>
                        </v-btn>
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </div>
            </div>

            <div class="d-flex justify-space-between mt-2">
              <v-btn variant="outlined" @click="step = 1">
                <v-icon start>mdi-arrow-left</v-icon> Назад
              </v-btn>
              <v-btn color="primary" @click="step = 3">
                Далее <v-icon end>mdi-arrow-right</v-icon>
              </v-btn>
            </div>
          </div>
        </v-stepper-window-item>

        <!-- Шаг 3: Генерация уроков -->
        <v-stepper-window-item :value="3">
          <div class="pa-6">
            <v-alert v-if="templates.length === 0" type="warning" variant="tonal" class="mb-4">
              Нет шаблонов расписания. Вернитесь на шаг 2 и добавьте слоты.
            </v-alert>

            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="dateFrom"
                  label="Дата с"
                  type="date"
                  variant="outlined"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="dateTo"
                  label="Дата по"
                  type="date"
                  variant="outlined"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row class="mb-2">
              <v-col cols="12" class="d-flex flex-wrap" style="gap: 16px">
                <v-btn
                  color="secondary"
                  :loading="previewLoading"
                  :disabled="!dateFrom || !dateTo || templates.length === 0"
                  @click="previewLessons"
                >
                  <v-icon start>mdi-eye</v-icon>
                  Предпросмотр
                </v-btn>
                <v-btn
                  color="primary"
                  :loading="generateLoading"
                  :disabled="!dateFrom || !dateTo || templates.length === 0"
                  @click="generateLessons"
                >
                  <v-icon start>mdi-calendar-plus</v-icon>
                  Создать пары
                </v-btn>
              </v-col>
            </v-row>

            <div v-if="previewResult" class="mb-4">
              <v-alert type="info" variant="tonal" class="mb-3">
                Будет создано уроков: <strong>{{ previewResult.would_generate_count }}</strong>
                <span v-if="previewResult.skipped_count > 0">
                  , пропущено (уже существуют): <strong>{{ previewResult.skipped_count }}</strong>
                </span>
              </v-alert>
              <div v-if="previewResult.lessons.length > 0" class="rounded-lg overflow-hidden border" style="overflow-x: auto">
                <v-table density="compact">
                  <thead>
                    <tr>
                      <th class="text-left">#</th>
                      <th class="text-left">Дата</th>
                      <th class="text-left">День</th>
                      <th class="text-left">Предмет</th>
                      <th class="text-left">Группа</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(lesson, idx) in previewResult.lessons" :key="idx">
                      <td class="text-medium-emphasis text-body-2">{{ idx + 1 }}</td>
                      <td class="text-body-2">{{ formatDate(lesson.lesson_date) }}</td>
                      <td class="text-body-2">{{ formatDayOfWeek(lesson.lesson_date) }}</td>
                      <td class="text-body-2">{{ lesson.subject_name }}</td>
                      <td class="text-body-2">{{ lesson.group_name }}</td>
                    </tr>
                  </tbody>
                </v-table>
              </div>
            </div>

            <div class="d-flex justify-start mt-4">
              <v-btn variant="outlined" @click="step = 2">
                <v-icon start>mdi-arrow-left</v-icon> Назад
              </v-btn>
            </div>
          </div>
        </v-stepper-window-item>
      </v-stepper-window>
    </v-stepper>

    <!-- Алерты -->
    <div class="px-6 pb-4">
      <v-alert v-if="success" type="success" variant="tonal" class="mt-2" closable @click:close="success = ''">
        {{ success }}
      </v-alert>
      <v-alert v-if="error" type="error" variant="tonal" class="mt-2" closable @click:close="error = ''">
        {{ error }}
      </v-alert>
    </div>

    <!-- Диалог добавления шаблона -->
    <v-dialog v-model="showTemplateDialog" width="440">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold">Добавить слот расписания</v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <v-select
            v-model="templateForm.day_of_week"
            :items="DAY_OPTIONS"
            item-title="label"
            item-value="value"
            label="День недели"
            variant="outlined"
            class="mb-4"
          ></v-select>
          <v-select
            v-model="templateForm.lesson_number"
            :items="[1, 2, 3, 4, 5, 6, 7, 8]"
            label="Номер урока"
            variant="outlined"
            class="mb-4"
          ></v-select>
          <v-text-field
            v-model="templateForm.start_time"
            label="Начало"
            type="time"
            variant="outlined"
            class="mb-4"
          ></v-text-field>
          <v-text-field
            v-model="templateForm.end_time"
            label="Конец"
            type="time"
            variant="outlined"
            class="mb-4"
          ></v-text-field>
          <v-text-field
            v-model="templateForm.classroom"
            label="Аудитория (необязательно)"
            variant="outlined"
            :error-messages="templateError"
          ></v-text-field>
        </v-card-text>
        <v-card-actions class="pa-4 justify-end gap-2">
          <v-btn variant="outlined" @click="showTemplateDialog = false">Отмена</v-btn>
          <v-btn
            color="primary"
            :loading="templateSaveLoading"
            :disabled="!templateForm.day_of_week || !templateForm.lesson_number || !templateForm.start_time || !templateForm.end_time"
            @click="saveTemplate"
          >
            Сохранить
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог успешной генерации -->
    <v-dialog v-model="showSuccessDialog" width="380" persistent>
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold text-center">Расписание создано!</v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6 text-center">
          <v-icon color="success" size="56" class="mb-4">mdi-check-circle</v-icon>
          <p class="text-body-1">{{ successMessage }}</p>
        </v-card-text>
        <v-card-actions class="pa-4 justify-center">
          <v-btn color="primary" size="large" @click="resetAll">Отлично!</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог подтверждения удаления шаблона -->
    <v-dialog v-model="showDeleteTemplateDialog" width="400">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold">Удалить шаблон?</v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <p>
            <strong>{{ DAY_NAMES[deletingTemplate?.day_of_week] }}</strong>,
            урок {{ deletingTemplate?.lesson_number }},
            {{ deletingTemplate?.start_time }}–{{ deletingTemplate?.end_time }}
          </p>
          <p class="text-body-2 text-medium-emphasis mt-2">Уже созданные уроки не удаляются.</p>
        </v-card-text>
        <v-card-actions class="pa-4 justify-end gap-2">
          <v-btn variant="outlined" @click="showDeleteTemplateDialog = false">Отмена</v-btn>
          <v-btn color="error" :loading="deleteTemplateLoading" @click="deleteTemplate">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card-text>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/axios'

const DAY_NAMES = { 1: 'Понедельник', 2: 'Вторник', 3: 'Среда', 4: 'Четверг', 5: 'Пятница', 6: 'Суббота', 7: 'Воскресенье' }
const DAY_OPTIONS = [
  { value: 1, label: 'Понедельник' },
  { value: 2, label: 'Вторник' },
  { value: 3, label: 'Среда' },
  { value: 4, label: 'Четверг' },
  { value: 5, label: 'Пятница' },
  { value: 6, label: 'Суббота' },
]

const step = ref(1)

const teachers = ref([])
const selectedTeacherId = ref(null)
const assignments = ref([])
const assignmentsLoading = ref(false)
const selectedAssignmentId = ref(null)
const selectedAssignment = ref(null)

const templates = ref([])
const templatesLoading = ref(false)

const dateFrom = ref('')
const dateTo = ref('')
const previewResult = ref(null)
const previewLoading = ref(false)
const generateLoading = ref(false)

const showTemplateDialog = ref(false)
const templateSaveLoading = ref(false)
const templateError = ref('')
const templateForm = ref({ day_of_week: null, lesson_number: null, start_time: '', end_time: '', classroom: '' })

const showDeleteTemplateDialog = ref(false)
const deleteTemplateLoading = ref(false)
const deletingTemplate = ref(null)

const success = ref('')
const error = ref('')
const showSuccessDialog = ref(false)
const successMessage = ref('')

const assignmentLabel = (a) => `${a.subject.name} — ${a.group.group_name} (${a.academic_period.name})`

onMounted(async () => {
  try {
    const res = await api.get('/admin/teachers/')
    teachers.value = res.data.filter(t => t.is_active)
  } catch (err) {
    console.error(err)
  }
})

const onTeacherChange = async () => {
  selectedAssignmentId.value = null
  selectedAssignment.value = null
  assignments.value = []
  templates.value = []
  previewResult.value = null
  if (!selectedTeacherId.value) return
  assignmentsLoading.value = true
  try {
    const res = await api.get('/admin/assignments/', { params: { teacher_id: selectedTeacherId.value } })
    assignments.value = res.data
  } catch (err) {
    console.error(err)
  } finally {
    assignmentsLoading.value = false
  }
}

const onAssignmentChange = async () => {
  templates.value = []
  previewResult.value = null
  selectedAssignment.value = assignments.value.find(a => a.id === selectedAssignmentId.value) || null
  if (!selectedAssignmentId.value) return
  await loadTemplates()
}

const loadTemplates = async () => {
  templatesLoading.value = true
  try {
    const res = await api.get('/admin/schedule-templates/', { params: { teaching_assignment_id: selectedAssignmentId.value } })
    templates.value = res.data
  } catch (err) {
    console.error(err)
  } finally {
    templatesLoading.value = false
  }
}

const openAddTemplateDialog = () => {
  templateForm.value = { day_of_week: null, lesson_number: null, start_time: '', end_time: '', classroom: '' }
  templateError.value = ''
  showTemplateDialog.value = true
}

const saveTemplate = async () => {
  templateError.value = ''
  templateSaveLoading.value = true
  try {
    await api.post('/admin/schedule-templates/', {
      teaching_assignment_id: selectedAssignmentId.value,
      day_of_week: templateForm.value.day_of_week,
      lesson_number: templateForm.value.lesson_number,
      start_time: templateForm.value.start_time,
      end_time: templateForm.value.end_time,
      classroom: templateForm.value.classroom || null,
    })
    showTemplateDialog.value = false
    success.value = 'Шаблон добавлен'
    await loadTemplates()
  } catch (err) {
    templateError.value = err.response?.data?.detail || 'Ошибка при сохранении'
  } finally {
    templateSaveLoading.value = false
  }
}

const confirmDeleteTemplate = (template) => {
  deletingTemplate.value = template
  showDeleteTemplateDialog.value = true
}

const deleteTemplate = async () => {
  deleteTemplateLoading.value = true
  try {
    await api.delete(`/admin/schedule-templates/${deletingTemplate.value.id}`)
    templates.value = templates.value.filter(t => t.id !== deletingTemplate.value.id)
    showDeleteTemplateDialog.value = false
    success.value = 'Шаблон удалён'
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при удалении'
    showDeleteTemplateDialog.value = false
  } finally {
    deleteTemplateLoading.value = false
  }
}

const previewLessons = async () => {
  previewResult.value = null
  previewLoading.value = true
  error.value = ''
  try {
    const res = await api.post('/admin/lessons/generate/preview/', {
      academic_period_id: selectedAssignment.value.academic_period.id,
      teaching_assignment_id: selectedAssignmentId.value,
      date_from: dateFrom.value,
      date_to: dateTo.value,
    })
    previewResult.value = res.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка предпросмотра'
  } finally {
    previewLoading.value = false
  }
}

const generateLessons = async () => {
  generateLoading.value = true
  error.value = ''
  try {
    const res = await api.post('/admin/lessons/generate/', {
      academic_period_id: selectedAssignment.value.academic_period.id,
      teaching_assignment_id: selectedAssignmentId.value,
      date_from: dateFrom.value,
      date_to: dateTo.value,
    })
    const skipped = res.data.skipped_count > 0 ? `, пропущено: ${res.data.skipped_count}` : ''
    successMessage.value = `Создано ${res.data.generated_count} пар${skipped}`
    showSuccessDialog.value = true
    previewResult.value = null
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при генерации'
  } finally {
    generateLoading.value = false
  }
}

const resetAll = () => {
  step.value = 1
  selectedTeacherId.value = null
  selectedAssignmentId.value = null
  selectedAssignment.value = null
  assignments.value = []
  templates.value = []
  dateFrom.value = ''
  dateTo.value = ''
  previewResult.value = null
  successMessage.value = ''
  showSuccessDialog.value = false
  success.value = ''
  error.value = ''
}

const formatDate = (d) => {
  if (!d) return ''
  return new Date(d + 'T00:00:00').toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const formatDayOfWeek = (d) => {
  if (!d) return ''
  const day = new Date(d + 'T00:00:00').getDay()
  const map = { 0: 'Вс', 1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб' }
  return map[day]
}
</script>
